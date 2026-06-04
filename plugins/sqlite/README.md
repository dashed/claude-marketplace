# sqlite

An [MCP](https://modelcontextprotocol.io) server that exposes a small,
agent-friendly toolset for working with **SQLite** databases. Writes are
**disabled by default** for safety and must be explicitly enabled.

It ships a runnable MCP server instead of a `SKILL.md`.

## What it does

The server registers five tools with the model:

| Tool | Writes? | Description |
|------|---------|-------------|
| `query` | no | Execute a `SELECT` query and return rows as a list of dicts (with `row_count`). Non-`SELECT` statements are rejected. |
| `list_tables` | no | List all tables in the database. |
| `describe_table` | no | Return a table's schema: columns (name, type, nullable, default, primary_key), the `CREATE TABLE` SQL, and indexes. |
| `execute` | **yes** | Execute an `INSERT`, `UPDATE`, or `DELETE` and return the affected row count. Requires writes enabled. |
| `create_table` | **yes** | Create a new table from a list of column definitions. Requires writes enabled. |

Once the plugin is enabled, the tools are namespaced by the plugin loader as
`mcp__plugin_sqlite_sqlite__<tool>` (e.g.
`mcp__plugin_sqlite_sqlite__query`). Verify the exact id by inspecting the
available tools after installing the plugin.

## Read-only by default

`execute` and `create_table` return an error unless write operations are
enabled. To enable writes, set the environment variable when the server is
launched:

- **Environment variable:** `MCP_SQLITE_ALLOW_WRITES=true`
- **CLI flag (when run standalone):** `--allow-writes`

The bundled `.mcp.json` intentionally launches the server **without**
`--allow-writes`, keeping the safe read-only default. To allow writes, add an
`env` block to the server entry, for example:

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "uv",
      "args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_sqlite_server.py"],
      "env": { "MCP_SQLITE_ALLOW_WRITES": "true" }
    }
  }
}
```

> Note: even with writes disabled, opening a database file that does not yet
> exist is refused (SQLite would otherwise create an empty file).

## Database path (`db_path`)

Every tool accepts an optional `db_path` argument. When omitted, the server's
default database (configured at launch via `--db-path`) is used. Supported
forms:

- **Relative:** `data.db`, `./databases/app.db`
- **Absolute:** `/var/lib/myapp/data.db`
- **In-memory:** `:memory:` — a temporary database whose state persists for the
  lifetime of the server process
- **Home-relative:** `~/myapp/data.db` — expands to the user's home directory

To configure a default database, add `--db-path /path/to/db.sqlite` to the
`args` array in `.mcp.json`.

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — the server is launched with
  `uv run --script`. The script is a PEP 723 inline-dependency script
  (`requires-python >=3.10`, `mcp>=0.1.0`); uv resolves and caches the
  dependency automatically on first run. No manual `pip install` is needed.
- **No database engine to install** — `sqlite3` is part of the Python standard
  library, so there is no external binary prerequisite.

## How it is wired

The plugin declares the server in `.mcp.json`:

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "uv",
      "args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_sqlite_server.py"]
    }
  }
}
```

`${CLAUDE_PLUGIN_ROOT}` is expanded by Claude Code to the installed plugin
directory, so the server runs regardless of where the plugin is checked out.

## Tests

```bash
cd plugins/sqlite
uv run --isolated --extra dev pytest tests/ -v
```
