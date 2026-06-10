# Changelog - sequential-thinking

All notable changes to the sequential-thinking plugin in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.0.3] - 2026-06-10

### Fixed
- README: corrected the advertised tool id to the plugin-namespaced form `mcp__plugin_sequential-thinking_sequential-thinking__sequentialthinking` — the form Claude Code actually registers for a plugin install (verified against the live installed plugin). The bare `mcp__sequential-thinking__sequentialthinking` form previously documented only applies to a directly-configured (non-plugin) MCP server
- README: the "How it is wired" `.mcp.json` snippet now matches the real file (includes the `--no-config` flag added in 1.0.2) and explains why the flag is there
- Script shebang now includes `--no-config` (`#!/usr/bin/env -S uv run --no-config --script`) so direct execution (`./mcp_sequential_thinking.py`) gets the same package-index isolation as the `.mcp.json` launch path, instead of re-hitting the resolution failure fixed in 1.0.2
- Corrected stale code comments claiming the SDK was "pinned mcp==1.9.4" — the dependency was an unbounded `mcp>=0.1.0` that floats to the latest release (resolved to 1.27.2 at the time of this fix). Verified on the current SDK that the try/except error-shape workaround is still required (raising from a FastMCP tool still re-wraps the message), so runtime behavior is unchanged; only the rationale was wrong
- Synced `.claude-plugin/plugin.json` and `pyproject.toml` versions with the marketplace version (both were stuck at 1.0.0)

### Changed
- Bounded the `mcp` dependency to `>=1.9.4,<2` in both the PEP 723 script block and the pyproject `dev` extra, so a future mcp 2.x release cannot silently break the server or the test suite (which relies on private SDK API: `mcp._tool_manager`, `fn_metadata.arg_model`)
- Removed the nonstandard `[project.optional-dependencies]` table from the PEP 723 inline metadata — it is not part of the inline-script-metadata spec, uv ignores it, and the dev dependencies actually live in `pyproject.toml`
- Added plugin-install guidance for `DISABLE_THOUGHT_LOGGING` to the README (set via an `env` block on the server entry in `.mcp.json`)

> Note: this release intentionally diverges `scripts/mcp_sequential_thinking.py` from the verbatim `mcp-personal` copy (shebang, dependency bound, two comment corrections). Port these upstream to re-converge.

## [1.0.2] - 2026-06-04

### Fixed
- Added `--no-config` to the `uv run` invocation in `.mcp.json` so the server resolves its pinned `mcp>=0.1.0` dependency from the default PyPI index regardless of the *consuming* repo's uv configuration. Without it, launching Claude Code from a directory whose `pyproject.toml`/`uv.toml` declares a non-PyPI `[[tool.uv.index]]` with `default = true` (e.g. a private mirror) made `uv run --script` adopt that index, so resolution failed with "mcp ... not found in the package registry" and the server reported `✘ failed` in `/mcp`.

## [1.0.1] - 2026-05-30

### Added
- `tests/test_sequential_thinking.py` — the upstream test suite (58 test cases) copied verbatim from `mcp-personal`, covering the `SequentialThinkingServer` core, thought-box rendering, color handling, and the JSON-string argument coercion behavior (issue #3856) that matters for Claude Code clients
- `pyproject.toml` with a `dev` extra (pytest, pytest-asyncio, mcp, anyio) and pytest config (`pythonpath = ["scripts"]`, `asyncio_mode = "auto"`) so the bundled server can be imported and tested
- `make test-sequential-thinking` target (`cd plugins/sequential-thinking && uv run --isolated --extra dev pytest tests/ -v`); all 58 tests pass against the verbatim server copy, confirming the port is faithful

## [1.0.0] - 2026-05-30

### Added
- Initial addition to marketplace — the **first MCP-server plugin** in this marketplace (ships a runnable Model Context Protocol server rather than a `SKILL.md`)
- `scripts/mcp_sequential_thinking.py` — self-contained MCP server (PEP 723 inline-dependency script with `#!/usr/bin/env -S uv run --script` shebang, `requires-python >=3.10`, `mcp>=0.1.0`); a Python port of the official TypeScript `sequential-thinking` server
- Exposes a single `sequentialthinking` tool (registered as `mcp__plugin_sequential-thinking_sequential-thinking__sequentialthinking` when installed via this marketplace; a directly-configured server would be `mcp__sequential-thinking__sequentialthinking`) for dynamic, reflective, step-by-step problem-solving: recording an evolving chain of thoughts, branching to explore alternatives, revising earlier steps, and adjusting the planned thought count on the fly
- `.mcp.json` declaring the stdio server, launched via `uv run --script ${CLAUDE_PLUGIN_ROOT}/scripts/mcp_sequential_thinking.py` with the server key `sequential-thinking`
- `.claude-plugin/plugin.json` carrying plugin metadata only (no `mcpServers`, to keep `.mcp.json` the single source of registration)
- `README.md` documenting the `sequentialthinking` tool and its parameters, the `DISABLE_THOUGHT_LOGGING` environment variable, and the `uv` prerequisite
- Establishes the marketplace pattern for MCP-server plugins: bundle the server under `scripts/`, register it via `.mcp.json`, and point the marketplace entry at it with `"mcpServers": "./.mcp.json"` instead of `"skills"`
