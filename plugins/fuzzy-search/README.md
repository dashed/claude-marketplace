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

### Search query syntax (`fuzzy_filter`)

The `fuzzy_filter` argument is passed to `fzf --filter` and uses fzf's
extended-search syntax. Space-separated terms are ANDed; a bare term is a
fuzzy (subsequence) match:

| Token | Match type | Description |
|-------|------------|-------------|
| `sbtrkt` | fuzzy-match | Items that match `sbtrkt` |
| `'wild` | exact-match (quoted) | Items that include `wild` |
| `'wild'` | exact-boundary-match (quoted both ends) | Items that include `wild` at word boundaries (fzf 0.55+) |
| `^music` | prefix-exact-match | Items that start with `music` |
| `.mp3$` | suffix-exact-match | Items that end with `.mp3` |
| `!fire` | inverse-exact-match | Items that do not include `fire` |
| `!^music` | inverse-prefix-exact-match | Items that do not start with `music` |
| `!.mp3$` | inverse-suffix-exact-match | Items that do not end with `.mp3` |

A single `|` term acts as an OR for the adjacent terms: `^core go$ | rb$ | py$`
matches items that start with `core` and end with `go`, `rb`, or `py`. Queries
are smart-case (all-lowercase → case-insensitive; any uppercase letter →
case-sensitive). `.`, `*`, `(`, `[` are literal characters, not regex
metacharacters.

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
plugin's `scripts/` layout. The server script and the test module were
originally copied from the upstream `mcp-personal` repository and then patched
locally (see below).

## Local modifications (diverges from mcp-personal upstream)

`scripts/mcp_fuzzy_search.py` is no longer byte-verbatim from upstream. The
following audit fixes were applied locally and are candidates for upstreaming:

1. **`fuzzy_search_content` standard mode now parses `rg --json`** instead of
   splitting ripgrep's `file:line:content` text on `:`. The structured stream is
   parsed (path / line number / line text from both `match` **and** `context`
   records) into the same `file:line:content` lines fed to fzf — the existing
   `--delimiter ":"` / `--nth` field-scoping and the `{file, line, content}`
   result shape are unchanged. This fixes three defects at once:
   - advertised `-A`/`-B`/`-C` context records are now included (previously they
     were dropped/mangled by the text parser);
   - file paths containing `:` are no longer corrupted (no more colon-splitting
     or Windows-drive-letter heuristic);
   - non-UTF-8 / non-ASCII bytes survive (ripgrep's base64 `bytes` fallback is
     decoded with replacement).
2. **`rg_flags` is split with `shlex.split()`** rather than `str.split()`, so
   quoted flag values (e.g. `--glob '!node_modules'`) are tokenized correctly.
3. **Subprocess timeouts** on every `rg` / `rga` / `fzf` call (default 30s,
   configurable via the `MCP_FUZZY_SEARCH_TIMEOUT` env var); a timeout returns a
   structured `{"error": ...}` instead of hanging the server.
4. **Multiline mode** skips binary files (NUL-byte detection) and accumulates
   file contents in a list joined once with `b"".join(...)` instead of repeated
   `bytes +=` concatenation (avoids quadratic-time rebuilds).
5. **PyMuPDF documents are closed via `try`/`finally`** in every PDF tool
   (`extract_pdf_pages`, `get_pdf_page_labels`, `get_pdf_page_count`,
   `get_pdf_outline`) and in the document-search page-label cache, so error and
   early-return paths no longer leak document handles.

The test module (`tests/test_fuzzy_search.py`) was correspondingly updated: the
subprocess mocks for `fuzzy_search_content` now feed `rg --json` records, and an
over-specific fzf-ranking-dependent assertion in `test_fuzzy_search_content` was
loosened (its previous `xfail` in `tests/conftest.py` was removed — it now
passes for real).
