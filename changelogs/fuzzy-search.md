# Changelog - fuzzy-search

All notable changes to the fuzzy-search plugin in this marketplace will be
documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
