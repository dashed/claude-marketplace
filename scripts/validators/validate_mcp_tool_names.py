"""Validate MCP tool-name lengths for marketplace plugins.

Claude Code namespaces a plugin MCP tool as
``mcp__plugin_<plugin>_<server-key>__<tool>`` and enforces a 64-character
tool-name limit. A redundant server key (e.g. ``sequential-thinking``)
silently pushes the id over the limit, so this check computes every
namespaced id from each plugin's ``.mcp.json`` server keys plus the tool
names AST-parsed out of the server scripts, and fails when one exceeds it.
"""

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Dict, List

from rich.console import Console
from rich.table import Table

console = Console()

MAX_TOOL_NAME_LENGTH = 64
PLUGIN_ID_PREFIX = "mcp__plugin_"
PLUGIN_ROOT_MARKERS = ("${CLAUDE_PLUGIN_ROOT}", "${PLUGIN_ROOT}")


def tool_names_in_script(script: Path) -> List[str]:
    """Return MCP tool names defined in a server script.

    Tool names come from ``@mcp.tool``-decorated functions (honoring an
    explicit ``name=`` keyword when present).
    """
    tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
    names = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            func = decorator.func if isinstance(decorator, ast.Call) else decorator
            attr = getattr(func, "attr", "")
            value_id = getattr(getattr(func, "value", None), "id", "")
            if attr != "tool" or value_id != "mcp":
                continue
            name = node.name
            if isinstance(decorator, ast.Call):
                for keyword in decorator.keywords:
                    if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                        name = str(keyword.value.value)
            names.append(name)
    return names


def server_script(plugin_dir: Path, entry: Dict) -> Path | None:
    """Resolve the server script from a ``.mcp.json`` server entry's args."""
    for arg in entry.get("args", []):
        if not isinstance(arg, str) or not arg.endswith(".py"):
            continue
        if any(marker in arg for marker in PLUGIN_ROOT_MARKERS):
            # Marker paths resolve against the repo root (the CWD when
            # validators run), not against the plugin dir.
            for marker in PLUGIN_ROOT_MARKERS:
                arg = arg.replace(marker, str(plugin_dir))
            candidate = Path(arg)
        else:
            candidate = Path(arg)
            if not candidate.is_absolute():
                candidate = plugin_dir / candidate
        if candidate.is_file():
            return candidate
    return None


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description="Validate MCP tool-name lengths")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("."),
        help="Base directory of the marketplace (default: current directory)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error code if any validation fails (including warnings)",
    )
    args = parser.parse_args()

    base_dir = args.base_dir
    errors: List[str] = []
    warnings: List[str] = []
    rows = []

    for mcp_json in sorted((base_dir / "plugins").glob("*/.mcp.json")):
        plugin_name = mcp_json.parent.name
        try:
            servers = json.loads(mcp_json.read_text(encoding="utf-8"))["mcpServers"]
        except (json.JSONDecodeError, KeyError) as error:
            errors.append(f"{plugin_name}: cannot read server keys from .mcp.json ({error})")
            continue

        for server_key, entry in servers.items():
            script = server_script(mcp_json.parent, entry)
            if script is None:
                warnings.append(
                    f"{plugin_name}: could not resolve a server script for "
                    f"server key '{server_key}' — tool names not checked"
                )
                continue
            tools = tool_names_in_script(script)
            if not tools:
                warnings.append(
                    f"{plugin_name}: no @mcp.tool definitions found in "
                    f"{script.name} — tool names not checked"
                )
                continue
            for tool in tools:
                namespaced = f"{PLUGIN_ID_PREFIX}{plugin_name}_{server_key}__{tool}"
                rows.append((namespaced, len(namespaced)))
                if len(namespaced) > MAX_TOOL_NAME_LENGTH:
                    over = len(namespaced) - MAX_TOOL_NAME_LENGTH
                    errors.append(
                        f"{namespaced} ({len(namespaced)} chars, "
                        f"{over} over the {MAX_TOOL_NAME_LENGTH}-char limit) — "
                        f"shorten the server key '{server_key}' or the tool "
                        f"name '{tool}'"
                    )

    table = Table(title="MCP namespaced tool ids")
    table.add_column("Tool id", style="cyan")
    table.add_column("Chars", justify="right")
    for namespaced, length in rows:
        style = "red" if length > MAX_TOOL_NAME_LENGTH else "green"
        table.add_row(namespaced, str(length), style=style)
    console.print(table)

    for warning in warnings:
        console.print(f"[yellow]WARNING: {warning}[/yellow]")
    for error in errors:
        console.print(f"[red]ERROR: {error}[/red]")
    console.print(
        f"\nChecked {len(rows)} tool id(s): {len(errors)} error(s), {len(warnings)} warning(s)"
    )

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
