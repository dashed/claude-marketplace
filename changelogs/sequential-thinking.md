# Changelog - sequential-thinking

All notable changes to the sequential-thinking plugin in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-05-30

### Added
- Initial addition to marketplace — the **first MCP-server plugin** in this marketplace (ships a runnable Model Context Protocol server rather than a `SKILL.md`)
- `scripts/mcp_sequential_thinking.py` — self-contained MCP server (PEP 723 inline-dependency script with `#!/usr/bin/env -S uv run --script` shebang, `requires-python >=3.10`, `mcp>=0.1.0`); a Python port of the official TypeScript `sequential-thinking` server
- Exposes a single `sequentialthinking` tool (resolves to `mcp__sequential-thinking__sequentialthinking`) for dynamic, reflective, step-by-step problem-solving: recording an evolving chain of thoughts, branching to explore alternatives, revising earlier steps, and adjusting the planned thought count on the fly
- `.mcp.json` declaring the stdio server, launched via `uv run --script ${CLAUDE_PLUGIN_ROOT}/scripts/mcp_sequential_thinking.py` with the server key `sequential-thinking`
- `.claude-plugin/plugin.json` carrying plugin metadata only (no `mcpServers`, to keep `.mcp.json` the single source of registration)
- `README.md` documenting the `sequentialthinking` tool and its parameters, the `DISABLE_THOUGHT_LOGGING` environment variable, and the `uv` prerequisite
- Establishes the marketplace pattern for MCP-server plugins: bundle the server under `scripts/`, register it via `.mcp.json`, and point the marketplace entry at it with `"mcpServers": "./.mcp.json"` instead of `"skills"`
