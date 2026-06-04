# Changelog - sqlite

All notable changes to the sqlite skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-04

### Added
- Initial addition to marketplace as an MCP-server plugin
- SQLite MCP server (`scripts/mcp_sqlite_server.py`) bundled verbatim, run via `uv run --script` (PEP 723 inline dependency on `mcp`)
- Five tools: `query`, `execute`, `list_tables`, `describe_table`, `create_table`
- Read-only by default; writes opt-in via `--allow-writes` flag or `MCP_SQLITE_ALLOW_WRITES=true`
- `.mcp.json` server declaration (server key `sqlite`) using `${CLAUDE_PLUGIN_ROOT}`, keeping the safe read-only default
- Metadata-only `.claude-plugin/plugin.json`
- Bundled test suite (`tests/test_sqlite_server.py`) with a `conftest.py` that resolves the server's absolute path for the subprocess-based CLI tests
- README documenting the five tools, read-only-by-default behavior and how to enable writes, and `db_path` options
