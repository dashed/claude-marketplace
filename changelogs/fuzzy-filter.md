# Changelog - fuzzy-filter

All notable changes to the fuzzy-filter skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-04

### Added
- Initial addition to marketplace — a skill for the **non-interactive** `rg`/`fd`/`rga` → `fzf --filter` pipeline, the CLI technique behind the `fuzzy-search` MCP server
- `SKILL.md`: two-stage mental model (regex scan → fuzzy rank; fuzzy ≠ regex), a when-to-use/when-not disambiguation table (vs. the fzf skill's interactive use, vs. the fuzzy-search MCP, vs. plain rg/fd), prerequisites, terse fuzzy-syntax recap (linking the fzf skill), fuzzy FILE search (`rg --files`/`fd` → fzf, NUL-safe `--read0`/`--print0`, `--scheme=path`), fuzzy CONTENT search (`rg --line-number --no-heading --color=never . PATH | fzf --filter Q --delimiter : --nth=1,3..`; content-only `--nth=3..`; why field 2/line-number is skipped), a `--delimiter`/`--nth`/`--with-nth` field-scoping deep-dive, document/PDF search via `rga`, gotchas, and See-also cross-links
- `references/pipelines.md`: full recipe catalog (files/content/documents, NUL-safe end-to-end, limiting/sorting/xargs hand-off) **plus the exact MCP-equivalent command for every `fuzzy-search` tool** (`fuzzy_search_files`/`fuzzy_search_content`/`fuzzy_search_documents` + PDF tools) — the "replicate the MCP" payload
- `references/pdf.md`: `rga` adapter configuration and PDF page-count/outline/extraction via `pdftotext`/`pdfinfo`/PyMuPDF — the CLI analog of the MCP's PDF inspection tools
- Light `(rga 0.10+)` / `(fzf 0.36+)` version annotations only where genuinely version-specific; long-standing basics left unannotated
- All recipes verified against ripgrep 14.1.1, fzf 0.55, fd 8.6, and ripgrep-all 0.10.9
- See-also cross-links added from the fzf, ripgrep, and fd skills' integration/recipe references back to this skill for the non-interactive technique
