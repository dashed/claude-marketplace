#!/usr/bin/env python3
"""Generate Codex plugin manifests and marketplace entries from the Claude marketplace."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence, TextIO


CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")
CODEX_MARKETPLACE = Path(".agents/plugins/marketplace.json")
CODEX_PLUGIN_MANIFEST = Path(".codex-plugin/plugin.json")
CODEX_MCP_CONFIG = Path(".codex-plugin/mcp.json")
CODEX_MCP_CONFIG_MANIFEST_PATH = "./.codex-plugin/mcp.json"
DEFAULT_CATEGORY = "Productivity"
DEFAULT_INSTALLATION_POLICY = "AVAILABLE"
DEFAULT_AUTH_POLICY = "ON_INSTALL"
HASH_BYTES = 12
PLUGIN_ROOT_MARKERS = ("${CLAUDE_PLUGIN_ROOT}", "${PLUGIN_ROOT}")
EXCLUDED_HASH_DIRS = {
    ".codex-plugin",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}
EXCLUDED_HASH_SUFFIXES = {".pyc", ".pyo"}


class SyncError(RuntimeError):
    """Raised when Codex plugin metadata cannot be generated."""


@dataclass(frozen=True)
class GeneratedFile:
    """One generated file and its desired content."""

    path: Path
    content: str


@dataclass
class SyncSummary:
    """Summary of a Codex plugin sync run."""

    written: list[Path] = field(default_factory=list)
    unchanged: list[Path] = field(default_factory=list)
    would_write: list[Path] = field(default_factory=list)
    drifted: list[Path] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.written or self.would_write or self.drifted)


def default_repo_root() -> Path:
    """Return the repository root based on this script's location."""
    return Path(__file__).resolve().parent.parent


def load_json_object(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SyncError(f"missing JSON file: {path}") from error
    except json.JSONDecodeError as error:
        raise SyncError(f"invalid JSON in {path}: {error}") from error

    if not isinstance(payload, dict):
        raise SyncError(f"{path} must contain a JSON object")
    return payload


def dump_json(payload: dict[str, Any]) -> str:
    """Return canonical generated JSON."""
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def normalize_source_path(raw_source: Any, *, plugin_name: str) -> str:
    """Return a local source path from a Claude marketplace entry."""
    if not isinstance(raw_source, str) or not raw_source.startswith("./"):
        raise SyncError(f"{plugin_name}: only local ./ source paths are supported")
    return raw_source.rstrip("/")


def normalize_version(raw_version: Any, *, plugin_name: str) -> str:
    """Return the base semver prefix from a marketplace plugin version."""
    if not isinstance(raw_version, str) or not raw_version.strip():
        raise SyncError(f"{plugin_name}: marketplace entry is missing version")
    return raw_version.split("+", 1)[0]


def display_name(plugin_name: str) -> str:
    """Return a readable display name from a kebab-case plugin id."""
    special_names = {
        "ai": "AI",
        "cdp": "CDP",
        "cli": "CLI",
        "fd": "fd",
        "fzf": "fzf",
        "jq": "jq",
        "jj": "jj",
        "k3s": "k3s",
        "mcp": "MCP",
        "psql": "psql",
        "sql": "SQL",
        "sqlite": "SQLite",
        "tmux": "tmux",
        "ui": "UI",
        "uv": "uv",
    }
    words = [special_names.get(part, part.capitalize()) for part in plugin_name.split("-")]
    return " ".join(words)


def one_line(text: str) -> str:
    """Collapse whitespace for generated JSON fields."""
    return " ".join(text.split())


def short_description(description: str, *, max_length: int = 180) -> str:
    """Return compact plugin copy for Codex UI metadata."""
    normalized = one_line(description)
    if len(normalized) <= max_length:
        return normalized

    cutoff = normalized.rfind(" ", 0, max_length - 1)
    if cutoff < max_length // 2:
        cutoff = max_length - 1
    return normalized[:cutoff].rstrip(".,;:- ") + "..."


def has_skills(plugin_dir: Path) -> bool:
    """Return whether a plugin has at least one nested Codex-compatible skill."""
    skills_dir = plugin_dir / "skills"
    if not skills_dir.is_dir():
        return False
    return any(path.is_dir() and (path / "SKILL.md").is_file() for path in skills_dir.iterdir())


def has_mcp_servers(plugin_dir: Path) -> bool:
    """Return whether a plugin declares MCP servers."""
    return (plugin_dir / ".mcp.json").is_file()


def hashable_paths(plugin_dir: Path) -> list[Path]:
    """Return plugin files that should participate in the Codex cachebuster hash."""
    paths: list[Path] = []
    for path in plugin_dir.rglob("*"):
        relative = path.relative_to(plugin_dir)
        if any(part in EXCLUDED_HASH_DIRS for part in relative.parts):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        if path.suffix in EXCLUDED_HASH_SUFFIXES:
            continue
        paths.append(path)
    return sorted(paths, key=lambda candidate: candidate.relative_to(plugin_dir).as_posix())


def codex_cache_hash(plugin_dir: Path, entry: dict[str, Any]) -> str:
    """Return a deterministic hash for a plugin's source and marketplace metadata."""
    hasher = hashlib.sha256()
    metadata = {
        key: value
        for key, value in entry.items()
        if key not in {"version"} and not key.startswith("_")
    }
    hasher.update(json.dumps(metadata, sort_keys=True, ensure_ascii=True).encode("utf-8"))
    hasher.update(b"\0")

    for path in hashable_paths(plugin_dir):
        relative = path.relative_to(plugin_dir).as_posix()
        hasher.update(relative.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")

    return hasher.hexdigest()[:HASH_BYTES]


def codex_version(base_version: str, cache_hash: str) -> str:
    """Return a strict semver version with a Codex cachebuster suffix."""
    return f"{base_version}+codex.{cache_hash}"


def rewrite_plugin_root_markers(payload: Any) -> tuple[Any, bool]:
    """Rewrite Claude/Codex plugin root variables to paths relative to plugin cwd."""
    if isinstance(payload, str):
        rewritten = payload
        for marker in PLUGIN_ROOT_MARKERS:
            rewritten = rewritten.replace(f"{marker}/", "")
            rewritten = rewritten.replace(marker, ".")
        return rewritten, rewritten != payload

    if isinstance(payload, list):
        changed = False
        values: list[Any] = []
        for item in payload:
            rewritten, item_changed = rewrite_plugin_root_markers(item)
            values.append(rewritten)
            changed = changed or item_changed
        return values, changed

    if isinstance(payload, dict):
        changed = False
        values: dict[str, Any] = {}
        for key, value in payload.items():
            rewritten, item_changed = rewrite_plugin_root_markers(value)
            values[key] = rewritten
            changed = changed or item_changed
        return values, changed

    return payload, False


def mcp_server_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return MCP server config objects from either supported MCP JSON shape."""
    raw_servers = payload.get("mcpServers", payload)
    if not isinstance(raw_servers, dict):
        return []
    return [server for server in raw_servers.values() if isinstance(server, dict)]


def codex_mcp_config(plugin_dir: Path) -> dict[str, Any]:
    """Build a Codex-native MCP config from a plugin's Claude MCP config."""
    source_path = plugin_dir / ".mcp.json"
    payload = load_json_object(source_path)
    rewritten, _ = rewrite_plugin_root_markers(payload)
    if not isinstance(rewritten, dict):
        raise SyncError(f"{source_path}: MCP config must contain a JSON object")

    for server in mcp_server_entries(rewritten):
        if "command" in server and "cwd" not in server:
            server["cwd"] = "."

    return rewritten


def plugin_manifest(repo_root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    """Build one `.codex-plugin/plugin.json` payload."""
    plugin_name = require_string(entry, "name", "marketplace plugin")
    source_path = normalize_source_path(entry.get("source"), plugin_name=plugin_name)
    plugin_dir = repo_root / source_path
    if not plugin_dir.is_dir():
        raise SyncError(f"{plugin_name}: plugin source not found: {plugin_dir}")

    description = one_line(require_string(entry, "description", plugin_name))
    author_name = "Alberto Leal"
    raw_author = entry.get("author")
    if isinstance(raw_author, dict):
        raw_author_name = raw_author.get("name")
        if isinstance(raw_author_name, str) and raw_author_name.strip():
            author_name = raw_author_name
    base_version = normalize_version(entry.get("version"), plugin_name=plugin_name)
    cache_hash = codex_cache_hash(plugin_dir, entry)
    plugin_has_skills = has_skills(plugin_dir)
    plugin_has_mcp = has_mcp_servers(plugin_dir)

    manifest: dict[str, Any] = {
        "name": plugin_name,
        "version": codex_version(base_version, cache_hash),
        "description": description,
        "author": {"name": author_name},
        "license": entry.get("license", "MIT"),
        "keywords": entry.get("keywords", []),
        "interface": {
            "displayName": display_name(plugin_name),
            "shortDescription": short_description(description),
            "longDescription": description,
            "developerName": author_name,
            "category": entry.get("category", DEFAULT_CATEGORY),
            "capabilities": plugin_capabilities(plugin_has_skills, plugin_has_mcp),
            "defaultPrompt": [default_prompt(plugin_name, plugin_has_mcp)],
        },
    }

    repository = entry.get("repository")
    if isinstance(repository, str) and repository.strip():
        manifest["repository"] = repository

    if plugin_has_skills:
        manifest["skills"] = "./skills/"
    elif "skills" in entry:
        raise SyncError(
            f"{plugin_name}: marketplace declares skills but no skills/*/SKILL.md found"
        )

    if plugin_has_mcp:
        manifest["mcpServers"] = CODEX_MCP_CONFIG_MANIFEST_PATH
    elif "mcpServers" in entry:
        raise SyncError(f"{plugin_name}: marketplace declares mcpServers but .mcp.json is missing")

    return manifest


def require_string(payload: dict[str, Any], key: str, label: str) -> str:
    """Return a required non-empty string."""
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SyncError(f"{label}: missing required string field `{key}`")
    return value


def plugin_capabilities(has_skill: bool, has_mcp_server: bool) -> list[str]:
    """Return Codex UI capabilities for a plugin."""
    capabilities: list[str] = []
    if has_skill:
        capabilities.append("Skills")
    if has_mcp_server:
        capabilities.append("MCP")
    return capabilities or ["Local"]


def default_prompt(plugin_name: str, has_mcp_server: bool) -> str:
    """Return a concise starter prompt for Codex plugin metadata."""
    if has_mcp_server:
        return f"Use the {plugin_name} MCP tools for this task."
    return f"Use ${plugin_name} for this task."


def codex_marketplace(claude_marketplace: dict[str, Any]) -> dict[str, Any]:
    """Build `.agents/plugins/marketplace.json` from the Claude marketplace."""
    marketplace_name = require_string(claude_marketplace, "name", "marketplace")
    display = display_name(marketplace_name)
    plugins = claude_marketplace.get("plugins")
    if not isinstance(plugins, list):
        raise SyncError("marketplace: `plugins` must be an array")

    return {
        "name": marketplace_name,
        "interface": {"displayName": display},
        "plugins": [codex_marketplace_entry(entry) for entry in plugins],
    }


def codex_marketplace_entry(entry: Any) -> dict[str, Any]:
    """Build one Codex marketplace plugin entry."""
    if not isinstance(entry, dict):
        raise SyncError("marketplace: plugin entries must be objects")
    plugin_name = require_string(entry, "name", "marketplace plugin")
    source_path = normalize_source_path(entry.get("source"), plugin_name=plugin_name)
    return {
        "name": plugin_name,
        "source": {
            "source": "local",
            "path": source_path,
        },
        "policy": {
            "installation": DEFAULT_INSTALLATION_POLICY,
            "authentication": DEFAULT_AUTH_POLICY,
        },
        "category": entry.get("category", DEFAULT_CATEGORY),
    }


def generated_files(repo_root: Path) -> list[GeneratedFile]:
    """Return all Codex files that should exist for this marketplace."""
    repo_root = repo_root.expanduser().resolve()
    claude_marketplace_path = repo_root / CLAUDE_MARKETPLACE
    claude_marketplace = load_json_object(claude_marketplace_path)
    plugins = claude_marketplace.get("plugins")
    if not isinstance(plugins, list):
        raise SyncError(f"{claude_marketplace_path}: `plugins` must be an array")

    files = [
        GeneratedFile(
            repo_root / CODEX_MARKETPLACE,
            dump_json(codex_marketplace(claude_marketplace)),
        )
    ]

    for entry in plugins:
        if not isinstance(entry, dict):
            raise SyncError("marketplace: plugin entries must be objects")
        plugin_name = require_string(entry, "name", "marketplace plugin")
        source_path = normalize_source_path(entry.get("source"), plugin_name=plugin_name)
        plugin_dir = repo_root / source_path
        if has_mcp_servers(plugin_dir):
            files.append(
                GeneratedFile(
                    plugin_dir / CODEX_MCP_CONFIG,
                    dump_json(codex_mcp_config(plugin_dir)),
                )
            )
        files.append(
            GeneratedFile(
                plugin_dir / CODEX_PLUGIN_MANIFEST,
                dump_json(plugin_manifest(repo_root, entry)),
            )
        )

    return files


def sync_codex_plugins(
    repo_root: Path,
    *,
    check: bool = False,
    dry_run: bool = False,
) -> SyncSummary:
    """Write or check generated Codex plugin files."""
    summary = SyncSummary()
    for generated in generated_files(repo_root):
        current = generated.path.read_text(encoding="utf-8") if generated.path.is_file() else None
        if current == generated.content:
            summary.unchanged.append(generated.path)
            continue

        if check:
            summary.drifted.append(generated.path)
            continue

        if dry_run:
            summary.would_write.append(generated.path)
            continue

        generated.path.parent.mkdir(parents=True, exist_ok=True)
        generated.path.write_text(generated.content, encoding="utf-8")
        summary.written.append(generated.path)

    return summary


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate Codex-native .codex-plugin manifests and "
            ".agents/plugins/marketplace.json from .claude-plugin/marketplace.json."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=default_repo_root(),
        help="repository root containing .claude-plugin/marketplace.json",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if generated Codex plugin files are out of date",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print files that would be written without changing them",
    )
    return parser


def print_summary(summary: SyncSummary, repo_root: Path, stdout: TextIO, stderr: TextIO) -> None:
    """Print sync output."""
    repo_root = repo_root.expanduser().resolve()
    for label, paths, stream in [
        ("updated", summary.written, stdout),
        ("would update", summary.would_write, stdout),
        ("out of date", summary.drifted, stderr),
    ]:
        for path in paths:
            print(f"{label}: {relative_label(path, repo_root)}", file=stream)

    print("", file=stdout)
    checked_count = (
        len(summary.written)
        + len(summary.unchanged)
        + len(summary.would_write)
        + len(summary.drifted)
    )
    print(f"Generated files checked: {checked_count}", file=stdout)
    print(f"Updated: {len(summary.written)}", file=stdout)
    print(f"Unchanged: {len(summary.unchanged)}", file=stdout)
    if summary.would_write:
        print(f"Would update: {len(summary.would_write)}", file=stdout)
    if summary.drifted:
        print(f"Out of date: {len(summary.drifted)}", file=stderr)


def relative_label(path: Path, repo_root: Path) -> str:
    """Return a readable path relative to repo root when possible."""
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.check and args.dry_run:
        print("error: choose only one of --check or --dry-run", file=sys.stderr)
        return 2

    repo_root = args.repo_root.expanduser().resolve()
    try:
        summary = sync_codex_plugins(repo_root, check=args.check, dry_run=args.dry_run)
    except SyncError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print_summary(summary, repo_root, sys.stdout, sys.stderr)
    return 1 if summary.drifted else 0


if __name__ == "__main__":
    sys.exit(main())
