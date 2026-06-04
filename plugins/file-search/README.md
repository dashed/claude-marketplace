# file-search

An [MCP](https://modelcontextprotocol.io) server that finds files by **name /
path** using [`fd`](https://github.com/sharkdp/fd) (regex & glob) and
[`fzf`](https://github.com/junegunn/fzf) (fuzzy matching). It searches file
*names*, **not** file *contents* (use a content/grep tool for that).

## What it does

The server registers two tools with the model:

- **`search_files`** — Find files using patterns (powered by `fd`). Use for
  exact patterns, file extensions, and regex matches. Example: search `\.py$`
  to find all Python files.
- **`filter_files`** — Fuzzy search through file paths (powered by `fzf`). Use
  for partial/fuzzy names. Example: filter `mainpy` finds `main.py`,
  `main_py.txt`, etc. Supports a multiline mode for content-aware records.

Once the plugin is enabled, the tools are available to Claude as:

```
mcp__plugin_file-search_file-search__search_files
mcp__plugin_file-search_file-search__filter_files
```

(The `mcp__plugin_<plugin>_<server-key>__<tool>` form is how the plugin loader
namespaces a plugin MCP tool — verify the exact id from the available tools
after installing.)

### `search_files` parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `pattern` | string (required) | Regex/glob pattern passed to `fd` |
| `path` | string (optional) | Directory to search (default: current dir) |
| `limit` | int (optional) | Cap results (adds `--max-results` to `fd`) |
| `flags` | string (optional) | Extra `fd` flags, e.g. `--hidden --type f` |

### `filter_files` parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `filter` | string (required) | Fuzzy filter string for `fzf` (no regex) |
| `pattern` | string (optional) | Pre-filter `fd` pattern |
| `path` | string (optional) | Directory to search (default: current dir) |
| `first` | bool (optional) | Return only the single best match |
| `limit` | int (optional) | Cap the number of matches |
| `fd_flags` | string (optional) | Extra `fd` flags |
| `fzf_flags` | string (optional) | Extra `fzf` flags, e.g. `--exact` |
| `multiline` | bool (optional) | Treat each file as a multiline record |

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — the server is launched with
  `uv run --script`. The script is a PEP 723 inline-dependency script
  (`requires-python >=3.10`, `mcp>=0.1.0`); uv resolves and caches dependencies
  on first run. No manual `pip install` needed.
- **[`fd`](https://github.com/sharkdp/fd)** (or `fdfind` on Debian/Ubuntu) and
  **[`fzf`](https://github.com/junegunn/fzf)** must be on `PATH`. The server
  checks for both at startup before exposing its tools.

## How it is wired

The plugin declares the server in `.mcp.json`:

```json
{
  "mcpServers": {
    "file-search": {
      "command": "uv",
      "args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_fd_server.py"]
    }
  }
}
```

`${CLAUDE_PLUGIN_ROOT}` is expanded by Claude Code to the installed plugin
directory, so the server runs regardless of where the plugin is checked out.

## CLI usage

The server script doubles as a CLI for quick manual checks:

```bash
uv run --script scripts/mcp_fd_server.py search '\.py$' .
uv run --script scripts/mcp_fd_server.py filter main '\.py$' . --first
```

## Development / tests

The bundled test suite runs against the real `fd`/`fzf` binaries (and falls
back to mocked subprocesses where they are absent):

```bash
uv run --isolated --extra dev pytest tests/ -v
```

`pyproject.toml` sets `pythonpath = ["scripts"]` so `import mcp_fd_server`
resolves the bundled server, and `tests/conftest.py` chdirs into `scripts/` so
the subprocess/CLI tests that launch the server by its bare name work in this
plugin layout.
