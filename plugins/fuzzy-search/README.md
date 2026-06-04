# fuzzy-search

An [MCP](https://modelcontextprotocol.io) server that exposes fuzzy
content/file/document search tools built on **ripgrep**, **fzf**, and
**ripgrep-all** (rga), plus a set of PDF inspection/extraction tools powered by
**PyMuPDF**.

It combines ripgrep's fast scanning with fzf's non-interactive fuzzy filtering,
so you can find code snippets, configuration, or any text pattern across a
codebase — and search inside PDFs and other documents.

## What it does

The server registers seven tools with the model:

| Tool | Description |
|------|-------------|
| `fuzzy_search_files` | Find file **paths** by fuzzy matching (fd/ripgrep file list → fzf). |
| `fuzzy_search_content` | Search file **contents**: ripgrep over all lines → fzf fuzzy filter. |
| `fuzzy_search_documents` | Search **PDFs and other document formats** with ripgrep-all (rga) → fzf. |
| `extract_pdf_pages` | Extract specific PDF pages and convert to various formats (PyMuPDF). |
| `get_pdf_outline` | Get a PDF's table of contents / bookmarks, with optional fuzzy filter. |
| `get_pdf_page_count` | Get the total number of pages in a PDF. |
| `get_pdf_page_labels` | Get a PDF's page labels (0-based index → label). |

> **`fuzzy_filter` is fzf fuzzy syntax, NOT regex.** The content/file/document
> tools fuzzy-match with fzf; they do not accept regular expressions. Use the
> `rg_flags` / pattern arguments for ripgrep-side filtering.

Once the plugin is enabled, the tools are available to Claude under the
plugin-namespaced ids, e.g.
`mcp__plugin_fuzzy-search_fuzzy-search__fuzzy_search_content`.

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — the server is launched with
  `uv run --script`. The script is a PEP 723 inline-dependency script
  (`requires-python >=3.10`, deps `mcp>=0.1.0`, `PyMuPDF>=1.23.0`); uv resolves
  and caches dependencies automatically on first run.
- **[ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`)** and
  **[fzf](https://github.com/junegunn/fzf)** — required for the
  fuzzy file/content search tools. Tools that need a missing binary report a
  clear error instead of crashing.
- **[ripgrep-all](https://github.com/phiresky/ripgrep-all) (`rga`)** —
  required only for `fuzzy_search_documents` (PDFs, Office docs, archives).
- **PyMuPDF** — bundled via the script's PEP 723 header; powers the PDF tools.

## How it is wired

The plugin declares the server in `.mcp.json`:

```json
{
  "mcpServers": {
    "fuzzy-search": {
      "command": "uv",
      "args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_fuzzy_search.py"]
    }
  }
}
```

`${CLAUDE_PLUGIN_ROOT}` is expanded by Claude Code to the installed plugin
directory, so the server runs regardless of where the plugin is checked out.

## Development / tests

The bundled test suite lives in `tests/` and exercises both the in-process MCP
interface and the CLI (including the PDF tools, which require PyMuPDF). Run it
with uv:

```bash
cd plugins/fuzzy-search
uv run --isolated --extra dev pytest tests/ -v
```

`tests/conftest.py` contains a small autouse fixture that runs each test with
its working directory set to `scripts/`, so the CLI subprocess tests — copied
verbatim from upstream, where the script sits at the repo root and is launched
as the bare filename `mcp_fuzzy_search.py` — resolve correctly from this
plugin's `scripts/` layout. The server script and the test module are otherwise
copied verbatim from the upstream `mcp-personal` repository.
