"""Tests for syncing Claude marketplace plugins into Codex plugin metadata."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from scripts.sync_codex_plugins import (
    CODEX_MARKETPLACE,
    CODEX_MCP_CONFIG,
    CODEX_PLUGIN_MANIFEST,
    main,
    sync_codex_plugins,
)


def write_marketplace(repo_root: Path, plugins: list[dict[str, object]]) -> None:
    """Write a minimal Claude marketplace fixture."""
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
    marketplace_path.parent.mkdir(parents=True)
    marketplace_path.write_text(
        json.dumps({"name": "alberto-marketplace", "plugins": plugins}),
        encoding="utf-8",
    )


def marketplace_entry(name: str, **overrides: object) -> dict[str, object]:
    """Return a complete marketplace plugin entry."""
    entry: dict[str, object] = {
        "name": name,
        "source": f"./plugins/{name}",
        "description": f"Test plugin {name}.",
        "version": "1.2.3",
        "author": {"name": "Test Author"},
        "license": "MIT",
        "keywords": ["test"],
    }
    entry.update(overrides)
    return entry


def create_skill_plugin(repo_root: Path, name: str) -> Path:
    """Create a plugin with a nested skill directory."""
    skill_dir = repo_root / "plugins" / name / "skills" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Test skill {name}\n---\n\n# {name}\n",
        encoding="utf-8",
    )
    return repo_root / "plugins" / name


def create_mcp_plugin(repo_root: Path, name: str) -> Path:
    """Create a plugin with a Claude-style MCP config."""
    plugin_dir = repo_root / "plugins" / name
    scripts_dir = plugin_dir / "scripts"
    scripts_dir.mkdir(parents=True)
    (scripts_dir / "server.py").write_text("print('server')\n", encoding="utf-8")
    (plugin_dir / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    name: {
                        "command": "uv",
                        "args": [
                            "run",
                            "--script",
                            "${CLAUDE_PLUGIN_ROOT}/scripts/server.py",
                            "--root",
                            "${PLUGIN_ROOT}",
                        ],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return plugin_dir


def load_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_sync_generates_codex_marketplace_and_skill_manifest(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill_plugin(repo_root, "alpha")
    write_marketplace(repo_root, [marketplace_entry("alpha", skills=["./skills"])])

    summary = sync_codex_plugins(repo_root)

    assert len(summary.written) == 2
    marketplace = load_json(repo_root / CODEX_MARKETPLACE)
    assert marketplace["name"] == "alberto-marketplace"
    assert marketplace["plugins"] == [
        {
            "name": "alpha",
            "source": {"source": "local", "path": "./plugins/alpha"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        }
    ]

    manifest = load_json(repo_root / "plugins" / "alpha" / CODEX_PLUGIN_MANIFEST)
    assert manifest["name"] == "alpha"
    assert manifest["skills"] == "./skills/"
    assert isinstance(manifest["version"], str)
    assert re.fullmatch(r"1\.2\.3\+codex\.[a-f0-9]{12}", manifest["version"])
    assert manifest["interface"]["capabilities"] == ["Skills"]


def test_sync_generates_codex_mcp_config_with_plugin_relative_cwd(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_mcp_plugin(repo_root, "demo-mcp")
    write_marketplace(repo_root, [marketplace_entry("demo-mcp", mcpServers="./.mcp.json")])

    sync_codex_plugins(repo_root)

    manifest = load_json(repo_root / "plugins" / "demo-mcp" / CODEX_PLUGIN_MANIFEST)
    assert manifest["mcpServers"] == "./.codex-plugin/mcp.json"
    assert manifest["interface"]["capabilities"] == ["MCP"]

    mcp_config = load_json(repo_root / "plugins" / "demo-mcp" / CODEX_MCP_CONFIG)
    server = mcp_config["mcpServers"]["demo-mcp"]
    assert server["args"] == ["run", "--script", "scripts/server.py", "--root", "."]
    assert server["cwd"] == "."


def test_check_reports_drift_without_rewriting(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill_plugin(repo_root, "alpha")
    write_marketplace(repo_root, [marketplace_entry("alpha", skills=["./skills"])])
    sync_codex_plugins(repo_root)

    marketplace_path = repo_root / CODEX_MARKETPLACE
    marketplace_path.write_text("{}\n", encoding="utf-8")

    summary = sync_codex_plugins(repo_root, check=True)

    assert summary.written == []
    assert summary.drifted == [marketplace_path.resolve()]
    assert marketplace_path.read_text(encoding="utf-8") == "{}\n"


def test_cli_dry_run_does_not_write_generated_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo_root = tmp_path / "repo"
    create_skill_plugin(repo_root, "alpha")
    write_marketplace(repo_root, [marketplace_entry("alpha", skills=["./skills"])])

    exit_code = main(["--repo-root", str(repo_root), "--dry-run"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "would update: .agents/plugins/marketplace.json" in captured.out
    assert not (repo_root / CODEX_MARKETPLACE).exists()
