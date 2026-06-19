# Changelog - fuzzy-search

All notable changes to the fuzzy-search plugin in this marketplace will be
documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.2.0] - 2026-06-19

### Fixed
- Unbounded memory on large result sets. The default `fuzzy_search_content`
  (standard) path buffered the entire `rg --json` stream plus a full candidate
  list, mapping, and fzf-input copy simultaneously, amplifying a corpus by
  roughly 150× — measured Python-side peak grew linearly with corpus size
  (2 MB→299 MB, 10 MB→1497 MB, 20 MB→~3 GB), and the `limit` argument only
  trimmed returned rows without bounding peak at all (limit=1, 20, and 5000 all
  produced the same peak). Peak is now bounded by the configurable caps and
  scales with the cap instead of the corpus (e.g. on a 10 MB corpus,
  `MCP_FUZZY_MAX_LINES=5000`→10.7 MB peak, `=500`→1.2 MB peak), while default
  caps leave normal repos byte-identical to before.
- `fuzzy_search_files` multiline mode: the file-list `subprocess.check_output`
  had no timeout (the only subprocess call in the server missing one) and could
  hang forever; it now uses the standard `MCP_FUZZY_SEARCH_TIMEOUT`. Its
  `multiline_input += record` accumulation was genuinely O(n²) on bytes and is
  now `b"".join(...)`; it also now skips binary files, applies an fzf timeout,
  and captures fzf stderr.

### Added
- Three bounded-memory caps, configurable via environment variables and applied
  *before* fzf: `MCP_FUZZY_MAX_LINES` (default 100000), `MCP_FUZZY_MAX_BYTES`
  (default 50 MiB), and `MCP_FUZZY_MAX_FILE_BYTES` (default 1 MiB, per-file in
  multiline modes). Set any to `0` to disable that cap.
- Explicit truncation surfacing: when a cap trips, results gain additive
  `truncated: true` and `truncation_note` keys (and log a warning) instead of
  silently dropping data. The `{"matches": [...]}` shape and tool signatures are
  unchanged; the new keys appear only when truncation occurs.

### Changed
- The `fuzzy_search_content` standard path now reads `rg --json` incrementally
  from the subprocess pipe (instead of `communicate()` buffering the whole
  output) and stops as soon as a cap is reached. The
  `file:line:content` → `{file, line, content}` reconstruction mapping is kept
  (so the existing `rg --json` context/colon-path/encoding fixes are not
  regressed) but is now bounded by the line cap rather than the corpus.
- `fuzzy_search_files` multiline mode brought to parity with the already-hardened
  multiline content path (timeout, `b"".join`, binary-skip, per-file/total
  caps). `fuzzy_search_documents` gained the same candidate cap on its parse
  loop.

## [1.1.2] - 2026-06-11

### Added
- README: "Search query syntax (`fuzzy_filter`)" section with the full fzf extended-search token table (fuzzy, exact `'`, exact-boundary `'…'`, `^`/`$` anchors, `!` inverse variants, `|` OR, smart-case, not-regex) — matching what the server's tool descriptions already document

### Fixed
- Synced `.claude-plugin/plugin.json` version with the marketplace version 1.1.1 (was stuck at 1.0.0)

## [1.1.1] - 2026-06-04

### Fixed
- Added `--no-config` to the `uv run` invocation in `.mcp.json` so the server resolves its pinned `mcp>=0.1.0` and `PyMuPDF` dependencies from the default PyPI index regardless of the *consuming* repo's uv configuration. Without it, launching Claude Code from a directory whose `pyproject.toml`/`uv.toml` declares a non-PyPI `[[tool.uv.index]]` with `default = true` (e.g. a private mirror) made `uv run --script` adopt that index, so resolution failed with "not found in the package registry" and the server reported `✘ failed` in `/mcp`.

## [1.1.0] - 2026-06-04

### Fixed
- `fuzzy_search_content` standard mode now parses ripgrep's `--json` output instead of splitting `file:line:content` text on `:`, fixing broken `-A`/`-B`/`-C` context (context records are now included), file paths containing `:`, and non-UTF-8/non-ASCII encoding (base64 `bytes` fallback decoded with replacement). The `--delimiter ":"`/`--nth` fzf field-scoping and the `{file, line, content}` result shape are unchanged.
- `rg_flags` are now tokenized with `shlex.split()` instead of `str.split()`, so quoted flag values (e.g. `--glob '!node_modules'`) are passed to ripgrep correctly.
- Added subprocess timeouts (default 30s, configurable via `MCP_FUZZY_SEARCH_TIMEOUT`) to all `rg`/`rga`/`fzf` invocations; a timeout now returns a structured `{"error": ...}` instead of hanging the server.
- Multiline content search now skips binary files (NUL-byte detection) and builds its fzf input with `b"".join(...)` instead of repeated `bytes` concatenation (avoids quadratic-time rebuilds).
- PyMuPDF documents are now closed via `try`/`finally` in `extract_pdf_pages`, `get_pdf_page_labels`, `get_pdf_page_count`, `get_pdf_outline`, and the document-search page-label cache, so error and early-return paths no longer leak document handles.

### Changed
- Bundled server script and test module are no longer byte-verbatim from upstream `mcp-personal`; local patches are documented in the plugin README under "Local modifications". Removed a stale fzf-ranking `xfail` from the test suite (`test_fuzzy_search_content` now passes for real).

## [1.0.0] - 2026-06-04

### Added
- Initial addition to the marketplace as an MCP-server plugin.
- Bundles the `mcp_fuzzy_search.py` server (copied verbatim from the upstream
  `mcp-personal` repo) under `scripts/`, launched via `uv run --script` from
  the PEP 723 inline-dependency header (`mcp>=0.1.0`, `PyMuPDF>=1.23.0`).
- Exposes seven tools: `fuzzy_search_files`, `fuzzy_search_content`,
  `fuzzy_search_documents` (ripgrep + fzf, plus ripgrep-all for documents) and
  the PyMuPDF-backed PDF tools `extract_pdf_pages`, `get_pdf_outline`,
  `get_pdf_page_count`, `get_pdf_page_labels`.
- `.mcp.json` declares the server under the `fuzzy-search` key (tool id
  namespaced by the plugin loader as
  `mcp__plugin_fuzzy-search_fuzzy-search__<tool>`).
- Metadata-only `.claude-plugin/plugin.json` (required to pass
  `validate-strict`).
- `pyproject.toml` dev extra (`pytest`, `pytest-asyncio`, `mcp`, `anyio`,
  `PyMuPDF>=1.23.0`) with `pythonpath = ["scripts"]` and `asyncio_mode = "auto"`
  so the bundled test suite — including the PDF tests — runs in isolation.
- Bundled test suite (`tests/test_fuzzy_search.py`, copied verbatim) plus a
  small `tests/conftest.py` autouse fixture that runs each test with its cwd set
  to `scripts/`, so the upstream CLI subprocess tests (which invoke the bare
  filename `mcp_fuzzy_search.py`) resolve under this plugin's `scripts/` layout.
  Server and test logic are otherwise unmodified.
