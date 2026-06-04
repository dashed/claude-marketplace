#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=0.1.0"]
#
# [project.optional-dependencies]
# dev = ["pytest>=7.0", "pytest-asyncio>=0.21.0"]
# ///

# ==============================================================================
# FUZZY FILE NAME SEARCH SERVER - Find files by name using fuzzy matching
# ==============================================================================
# Keywords: fuzzy search, file finder, fuzzy file name search, file discovery, fzf
# Purpose: MCP server for finding files by NAME (not content) using fuzzy matching
# What it does: Searches file names/paths - NOT file contents
# ==============================================================================
"""
Fuzzy File NAME Search Server for Model Context Protocol (MCP)
==============================================================

This server helps AI agents find files by their NAMES/PATHS using fuzzy matching.
It searches file names, NOT file contents (use grep/ripgrep for content search).

AI AGENT QUICK REFERENCE
------------------------
**What this does**: Find files by NAME using fuzzy patterns (NOT content search)
**When to use**: When you need to locate files but only know partial names
**Key capability**: Fuzzy name matching - finds "main.py" by searching "mainpy"

Tools Provided
--------------
1. **`search_files`** – Find files using patterns (regex/glob via fd)
   - Use for: Exact patterns, file extensions, regex matches
   - Example: Search "\\.py$" to find all Python files

2. **`filter_files`** – Fuzzy search through file paths (powered by fzf)
   - Use for: Finding files with partial/fuzzy names
   - Example: Filter "mainpy" finds "main.py", "main_py.txt", etc.

CRITICAL FOR AI AGENTS: NO REGEX IN FZF FILTER
----------------------------------------------
The 'filter' parameter in filter_files does NOT support regular expressions!
Use fzf's fuzzy matching syntax instead (spaces for AND, | for OR, etc).

SPACES MATTER IN FZF PATTERNS!
-----------------------------
Each space separates fuzzy patterns with AND logic:
- 'foo bar' → Files containing 'foo' AND 'bar' (2 patterns)
- 'foo/bar' → Files containing 'foo/bar' (1 pattern)
- 'temp /test$' → Files with 'temp' AND ending with '/test'
- 'foo\\ bar' → Files containing literal 'foo bar' (escaped space)

Common Use Cases for AI Agents (File Name Search)
-------------------------------------------------
- Finding config files by name: filter "config json$"
- Locating test files by name: filter "test py$" or search "test.*\\.py$"
- Finding component files: filter "button component"
- Finding files in specific dirs: filter "^src/ controller"
- Finding files with partial names: filter "usr ctrl" (finds UserController.js)

Technical Details
-----------------
* Powered by fd (fast file finder) and fzf (fuzzy finder)
* Returns results as JSON for programmatic processing
* Supports multiline content search for advanced use cases
* All errors returned as structured JSON

ADVANCED FZF FEATURES
--------------------
- Smart Case: Case-insensitive by default, case-sensitive if query has uppercase
- Latin Normalization: Accented chars normalized (café → cafe)
- Exact Boundary Match: ''word'' matches at word boundaries
- Scoring: Matches at special positions score higher

Implementation Notes
--------------------
* Uses FastMCP for automatic tool discovery
* Requires fd and fzf binaries installed on system
* Cross-platform path normalization for consistency
"""

from __future__ import annotations

import argparse
import json
import logging
import platform
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP  # high‑level helper inside the SDK

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# fzf exit codes (based on fzf source code constants)
FZF_EXIT_OK = 0  # Success with matches
FZF_EXIT_NO_MATCH = 1  # No matches found (NOT an error condition)
FZF_EXIT_ERROR = 2  # Error occurred
FZF_EXIT_BECOME = 126  # Special exit for 'become' action
FZF_EXIT_INTERRUPT = 130  # User interrupted (e.g., Ctrl+C)

# ---------------------------------------------------------------------------
# Binary discovery helpers
# ---------------------------------------------------------------------------

FD_EXECUTABLE: str | None = shutil.which("fd") or shutil.which("fdfind")
FZF_EXECUTABLE: str | None = shutil.which("fzf")

# Platform detection
IS_WINDOWS = platform.system() == "Windows"


def _normalize_path(path: str) -> str:
    """Normalize path to use forward slashes consistently across platforms."""
    # Replace backslashes with forward slashes for cross-platform consistency
    # This handles Windows paths even when running on Unix systems
    return path.replace("\\", "/")


class BinaryMissing(RuntimeError):
    """Raised when a required CLI binary is missing from PATH."""


def _require(binary: str | None, name: str) -> str:
    if not binary:
        raise BinaryMissing(
            f"Cannot find the `{name}` binary on PATH. Install it first."
        )
    return binary


def _looks_like_regex(text: str) -> bool:
    """Detect if a string looks like a regex pattern rather than fuzzy search terms."""
    import re

    # Common regex metacharacters and patterns
    regex_indicators = [
        r"\.\*",  # .* (any characters)
        r"\.\+",  # .+ (one or more)
        r"\\\w",  # \w (word character)
        r"\\\d",  # \d (digit)
        r"\\\s",  # \s (whitespace)
        r"\[.+\]",  # [abc] (character class)
        r"\(.+\)",  # (group) (capturing group)
        r"\{\d+,?\d*\}",  # {n,m} (quantifier)
        r"\\\.",  # \. (escaped dot)
    ]

    # Check if text contains regex patterns
    for pattern in regex_indicators:
        if re.search(pattern, text):
            return True

    # Check for other regex-like constructs
    if re.search(r"[^\\]\|[^\\|]", text):  # | not in fzf OR context
        return True

    return False


def _suggest_fuzzy_terms(regex_pattern: str) -> str:
    """Convert common regex patterns to fuzzy search suggestions."""
    import re

    # Remove common regex constructs to suggest fuzzy terms
    fuzzy = regex_pattern
    fuzzy = re.sub(r"\.\*", " ", fuzzy)  # .* -> space
    fuzzy = re.sub(r"\.\+", " ", fuzzy)  # .+ -> space
    fuzzy = re.sub(r"\\\w\+?", "", fuzzy)  # \w+ -> remove
    fuzzy = re.sub(r"\\\d\+?", "", fuzzy)  # \d+ -> remove
    fuzzy = re.sub(r"\\\s\+?", " ", fuzzy)  # \s+ -> space
    fuzzy = re.sub(r"[\[\]\(\)\{\}]", "", fuzzy)  # Remove brackets
    fuzzy = re.sub(r"\\\.", ".", fuzzy)  # \. -> .
    fuzzy = re.sub(r"\s+", " ", fuzzy)  # Multiple spaces -> single space
    fuzzy = fuzzy.strip()

    # If we end up with nothing useful, extract alphanumeric parts
    if not fuzzy or fuzzy.isspace():
        words = re.findall(r"\w+", regex_pattern)
        fuzzy = " ".join(words)

    return fuzzy


def _handle_fzf_error(
    exc: subprocess.CalledProcessError, warnings: list[str]
) -> dict[str, Any]:
    """Handle fzf CalledProcessError, returning appropriate result dict.

    fzf exit codes (from fzf source code):
    - 0: Success with matches (FZF_EXIT_OK)
    - 1: No matches found (FZF_EXIT_NO_MATCH) - NOT an error condition
    - 2: Error occurred (FZF_EXIT_ERROR)
    - 126: Special exit for 'become' action (FZF_EXIT_BECOME)
    - 130: User interrupted, e.g., Ctrl+C (FZF_EXIT_INTERRUPT)

    This function specifically handles the case where fzf exits with code 1,
    which indicates no matches were found but is not an error condition.
    """
    # fzf returns exit code 1 when no matches found - this is not an error
    if exc.returncode == FZF_EXIT_NO_MATCH:
        return {"matches": []}  # No matches found, return empty list

    # All other non-zero exit codes are treated as errors
    # This includes FZF_EXIT_ERROR (actual error) and FZF_EXIT_INTERRUPT (user interrupt)
    error_result: dict[str, Any] = {"error": str(exc)}
    if warnings:
        error_result["warnings"] = warnings
    return error_result


# ---------------------------------------------------------------------------
# FastMCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP("fd-fzf")

# ---------------------------------------------------------------------------
# Tool: search_files
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Search for files using patterns (powered by fd - a fast file finder).\n\n"
        "PURPOSE: Find files when you know exact patterns, extensions, or regex.\n"
        "NOT FUZZY: This uses exact pattern matching, not fuzzy search.\n\n"
        "Args:\n"
        "  pattern (str): Regex or glob pattern to match filenames. Required.\n"
        "  path    (str, optional): Directory to search in. Defaults to current dir.\n"
        "  limit   (int, optional): Maximum number of results to return. Default 0 (no limit).\n"
        "  flags   (str, optional): Extra flags for fd (e.g., '--hidden' for hidden files).\n\n"
        "Examples:\n"
        "  pattern='\\.py$' - Find all Python files\n"
        "  pattern='test_.*\\.js$' - Find JavaScript test files\n"
        "  pattern='config' - Find files with 'config' in the name\n\n"
        "Returns: { matches: string[] } or { error: string }"
    )
)
def search_files(
    pattern: str,
    path: str = ".",
    limit: int = 0,
    flags: str = "",
) -> dict[str, Any]:
    """Return every file or directory matching *pattern* according to fd."""
    if not pattern:
        return {"error": "'pattern' argument is required"}

    fd_bin = _require(FD_EXECUTABLE, "fd")
    # Ensure path is properly formatted
    search_path = str(Path(path).resolve())
    cmd: list[str] = [fd_bin]
    if isinstance(limit, int) and limit > 0:
        # Use fd's native max-results for efficiency
        cmd += ["--max-results", str(limit)]
    cmd += [*shlex.split(flags), pattern, search_path]

    logger.debug("Running fd: %s", " ".join(shlex.quote(c) for c in cmd))

    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        matches = [_normalize_path(p) for p in out.splitlines() if p]
        if isinstance(limit, int) and limit > 0:
            matches = matches[:limit]
        return {"matches": matches}
    except subprocess.CalledProcessError as exc:
        return {"error": exc.output.strip() or str(exc)}


# ---------------------------------------------------------------------------
# Tool: filter_files
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Fuzzy search for files by NAME using fzf (fuzzy finder).\n\n"
        "PURPOSE: Find files when you only know partial or approximate file names.\n"
        "FUZZY MATCHING: Searches file NAMES/PATHS, not file contents!\n\n"
        "IMPORTANT: NO REGEX SUPPORT in 'filter' - use fzf's fuzzy syntax!\n\n"
        "Args:\n"
        "  filter (str): Fuzzy search query for file names/paths. Required.\n"
        "  pattern (str, optional): Pre-filter with fd pattern (empty = all files).\n"
        "  path    (str, optional): Directory to search. Defaults to current dir.\n"
        "  first   (bool, optional): Return only the best match. Default false.\n"
        "  limit   (int, optional): Maximum number of results to return. Default 0 (no limit).\n"
        "  fd_flags  (str, optional): Extra flags for fd.\n"
        "  fzf_flags (str, optional): Extra flags for fzf.\n"
        "  multiline (bool, optional): Search file CONTENTS (not just names). Default false.\n\n"
        "Note: When both 'first' and 'limit' are set, 'first' takes precedence and returns only the best match.\n\n"
        "FUZZY FILE NAME MATCHING:\n"
        "  'mainpy' → Finds: main.py, main_py.txt, domain.py, etc.\n"
        "  'confjs' → Finds: config.js, conf.js, configure.js, etc.\n"
        "  'test spec' → Finds files with both 'test' AND 'spec' in the path\n\n"
        "fzf Query Syntax:\n"
        "  SPACES SEPARATE PATTERNS! Each space = AND condition\n"
        "  Basic: 'term1 term2' (AND), 'term1 | term2' (OR)\n"
        "  Exact: 'exact → exact match (not fuzzy)\n"
        "  Boundary: ''main.py'' → exact word boundaries\n"
        "  Position: '^src' (starts with), '.py$' (ends with)\n"
        "  Exclude: '!test' (NOT test), '!.spec$' (NOT ending in .spec)\n"
        "  Literal space: 'My\\\\ Documents' → 'My Documents'\n\n"
        "Examples for Finding Files by Name:\n"
        "  'config json$' → Config files ending in .json\n"
        "  'test !spec' → Test files but not spec files\n"
        "  '^src/ component tsx$' → React components in src/\n"
        "  'button | modal | dialog' → UI component files\n\n"
        "COMMON MISTAKES:\n"
        "  ✗ '.*\\\\.py$' → WRONG! This is regex\n"
        "  ✓ '.py$' → CORRECT! Files ending with .py\n"
        "  ✗ 'My Documents' → Matches 'My' AND 'Documents' separately\n"
        "  ✓ 'My\\\\ Documents' → Matches literal 'My Documents'\n\n"
        "Multiline Mode (Advanced):\n"
        "  When enabled, searches file CONTENTS instead of just names.\n"
        "  Useful for finding files containing specific code/text.\n\n"
        "Returns: { matches: string[] } or { error: string }"
    )
)
def filter_files(
    filter: str,
    pattern: str = "",
    path: str = ".",
    first: bool = False,
    limit: int = 0,
    fd_flags: str = "",
    fzf_flags: str = "",
    multiline: bool = False,
) -> dict[str, Any]:
    """Combine fd + fzf in headless filter mode with optional multiline support."""
    if not filter:
        return {"error": "'filter' argument is required"}

    fd_bin = _require(FD_EXECUTABLE, "fd")
    fzf_bin = _require(FZF_EXECUTABLE, "fzf")

    # Check for regex patterns and warn
    warnings = []
    if _looks_like_regex(filter):
        suggested_terms = _suggest_fuzzy_terms(filter)
        warnings.append(
            f"The 'filter' parameter contains regex-like patterns ({filter!r}). "
            f"This parameter expects fzf fuzzy search terms, not regex. "
            f"Try: {suggested_terms!r}"
        )

    # Ensure path is properly formatted
    search_path = str(Path(path).resolve())

    if multiline:
        # For multiline mode, find files first, then read contents with null separators
        fd_cmd: list[str] = [fd_bin, *shlex.split(fd_flags), pattern, search_path]

        try:
            # Get file list from fd
            fd_result = subprocess.check_output(fd_cmd, text=True)
            file_paths = [p for p in fd_result.splitlines() if p]

            # Read file contents with null separators
            multiline_input = b""
            for file_path in file_paths:
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()
                        # Add filename prefix and null separator
                        normalized_path = _normalize_path(file_path)
                        record = f"{normalized_path}:\n".encode() + content + b"\0"
                        multiline_input += record
                except OSError:
                    continue  # Skip files that can't be read

            if not multiline_input:
                result = {"matches": []}
                if warnings:
                    result["warnings"] = warnings
                return result

            # Use fzf with multiline support
            fzf_cmd: list[str] = [fzf_bin, "--filter", filter, "--read0", "--print0"]
            fzf_cmd.extend(shlex.split(fzf_flags))

            fzf_proc = subprocess.Popen(
                fzf_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
            )
            out_bytes, err_bytes = fzf_proc.communicate(multiline_input)

            # Check fzf return code and handle errors
            if fzf_proc.returncode != 0:
                # Create a CalledProcessError to pass to _handle_fzf_error
                exc = subprocess.CalledProcessError(
                    fzf_proc.returncode, fzf_cmd, output=out_bytes, stderr=err_bytes
                )
                return _handle_fzf_error(exc, warnings)

            # Parse null-separated output
            matches = []
            if out_bytes:
                for chunk in out_bytes.split(b"\0"):
                    if chunk:
                        try:
                            matches.append(chunk.decode("utf-8"))
                        except UnicodeDecodeError:
                            matches.append(chunk.decode("utf-8", errors="replace"))

        except subprocess.CalledProcessError as exc:
            return _handle_fzf_error(exc, warnings)
    else:
        # Standard mode - file paths only
        fd_cmd: list[str] = [fd_bin, *shlex.split(fd_flags), pattern, search_path]
        fzf_cmd: list[str] = [fzf_bin, "--filter", filter, *shlex.split(fzf_flags)]

        logger.debug("Pipeline: %s | %s", " ".join(fd_cmd), " ".join(fzf_cmd))

        try:
            fd_proc = subprocess.Popen(fd_cmd, stdout=subprocess.PIPE)
            out = subprocess.check_output(fzf_cmd, stdin=fd_proc.stdout, text=True)
            if fd_proc.stdout:
                fd_proc.stdout.close()
            fd_proc.wait()
            matches = [_normalize_path(p) for p in out.splitlines() if p]
        except subprocess.CalledProcessError as exc:
            return _handle_fzf_error(exc, warnings)

    if first and matches:
        matches = matches[:1]
    elif limit > 0 and matches:
        matches = matches[:limit]

    result = {"matches": matches}
    if warnings:
        result["warnings"] = warnings

    return result


# ---------------------------------------------------------------------------
# CLI helper (optional) ------------------------------------------------------
# ---------------------------------------------------------------------------


def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="fd + fzf powers, CLI mode",
        epilog="fzf query examples: 'config .json$', '^src py$ | js$', ''main.py'' !test'",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # search_files sub‑command
    p_search = sub.add_parser("search", help="fd search")
    p_search.add_argument("pattern")
    p_search.add_argument("path", nargs="?", default=".")
    p_search.add_argument("--limit", type=int, default=0, help="Maximum results")
    p_search.add_argument("--flags", default="")

    # filter_files sub‑command
    p_filter = sub.add_parser("filter", help="fd + fzf filter")
    p_filter.add_argument(
        "filter", help="fzf query (use quotes: 'config .json$ !test')"
    )
    p_filter.add_argument("pattern", nargs="?", default="")
    p_filter.add_argument("path", nargs="?", default=".")
    p_filter.add_argument("--first", action="store_true")
    p_filter.add_argument("--limit", type=int, default=0, help="Maximum results")
    p_filter.add_argument("--fd-flags", default="")
    p_filter.add_argument("--fzf-flags", default="")
    p_filter.add_argument(
        "--multiline", action="store_true", help="Enable multiline content search"
    )

    ns = parser.parse_args()

    if ns.cmd == "search":
        res = search_files(ns.pattern, ns.path, ns.limit, ns.flags)
    else:
        res = filter_files(
            ns.filter,
            ns.pattern,
            ns.path,
            ns.first,
            ns.limit,
            ns.fd_flags,
            ns.fzf_flags,
            ns.multiline,
        )

    print(json.dumps(res, indent=2))


# ---------------------------------------------------------------------------
# Entry‑point ---------------------------------------------------------------
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        _cli()
    else:
        # Ensure required binaries before exposing tools to LLMs
        _require(FD_EXECUTABLE, "fd")
        _require(FZF_EXECUTABLE, "fzf")
        mcp.run()  # defaults to stdio transport
