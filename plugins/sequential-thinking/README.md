# sequential-thinking

An [MCP](https://modelcontextprotocol.io) server that exposes a single
`sequentialthinking` tool for dynamic, reflective, step-by-step
problem-solving. It is a Python port of the official TypeScript
`sequential-thinking` MCP server.

This is the **first MCP-server plugin** in this marketplace — it ships a
runnable server instead of a `SKILL.md`.

## What it does

The server registers one tool with the model:

- **`sequentialthinking`** — Record one step in an iterative thinking process.
  The model can record an evolving chain of thoughts, branch off to explore
  alternatives, revise earlier steps, and adjust the planned thought count on
  the fly. History is kept in memory for the lifetime of the process.

Once the plugin is enabled, the tool is available to Claude as
`mcp__sequential-thinking__sequentialthinking`.

### Tool parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `thought` | string | Your current thinking step |
| `nextThoughtNeeded` | bool | Whether another thought step is needed |
| `thoughtNumber` | int | Current thought number (e.g., 1, 2, 3) |
| `totalThoughts` | int | Estimated total thoughts needed |
| `isRevision` | bool (optional) | Whether this revises previous thinking |
| `revisesThought` | int (optional) | Which thought is being reconsidered |
| `branchFromThought` | int (optional) | Branching point thought number |
| `branchId` | string (optional) | Branch identifier |
| `needsMoreThoughts` | bool (optional) | If more thoughts are needed |

Numeric and boolean arguments are also accepted as JSON strings (e.g. `"1"`,
`"true"`), working around clients — including Claude Code — that serialize
these values as strings.

## Environment variables

- **`DISABLE_THOUGHT_LOGGING`** — When set (case-insensitive) to `"true"`,
  the server suppresses the formatted thought box that is otherwise written to
  stderr. All other behavior is unchanged.

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — the server is launched with
  `uv run --script`. The script is a PEP 723 inline-dependency script
  (`requires-python >=3.10`, `mcp>=0.1.0`); uv resolves and caches the
  dependencies automatically on first run. No manual `pip install` is needed.

## How it is wired

The plugin declares the server in `.mcp.json`:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "uv",
      "args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_sequential_thinking.py"]
    }
  }
}
```

`${CLAUDE_PLUGIN_ROOT}` is expanded by Claude Code to the installed plugin
directory, so the server runs regardless of where the plugin is checked out.
