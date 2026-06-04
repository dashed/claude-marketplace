# Changelog - file-search

All notable changes to the file-search plugin in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.1] - 2026-06-04

### Fixed
- Added `--no-config` to the `uv run` invocation in `.mcp.json` so the server resolves its pinned `mcp>=0.1.0` dependency from the default PyPI index regardless of the *consuming* repo's uv configuration. Without it, launching Claude Code from a directory whose `pyproject.toml`/`uv.toml` declares a non-PyPI `[[tool.uv.index]]` with `default = true` (e.g. a private mirror) made `uv run --script` adopt that index, so resolution failed with "mcp ... not found in the package registry" and the server reported `✘ failed` in `/mcp`.

## [1.0.0] - 2026-06-04

### Added
- Initial addition to the marketplace as an MCP-server plugin
- `file-search` MCP server (`scripts/mcp_fd_server.py`, a self-contained PEP 723
  `uv run --script` file ported verbatim from mcp-personal) exposing two tools:
  - `search_files` — find files by name/path with `fd` (regex/glob, flags, limit)
  - `filter_files` — fuzzy file-name search with `fzf` (first/limit/flags, multiline)
- `.mcp.json` declaring the stdio server under key `file-search`, so the tools
  register as `mcp__plugin_file-search_file-search__{search_files,filter_files}`
- Metadata-only `.claude-plugin/plugin.json`
- `pyproject.toml` with a `dev` extra (pytest, pytest-asyncio, mcp, anyio),
  `asyncio_mode = "auto"`, and `pythonpath = ["scripts"]`
- Bundled test suite (`tests/test_fd_server.py`, `tests/test_simple.py`,
  `tests/test_cli.py`, `tests/conftest.py`) — 49 tests, all passing against the
  real `fd`/`fzf` binaries
- `README.md` documenting the tools, parameters, prerequisites, and wiring

### Notes
- Test bodies are kept verbatim from upstream. The only packaging adaptation is
  an autouse fixture in `tests/conftest.py` that chdirs into `scripts/` so the
  tests which launch the server by its bare name (`mcp_fd_server.py`) resolve in
  the `scripts/` plugin layout.
