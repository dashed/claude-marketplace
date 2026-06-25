# Changelog - fuzzy-filter

All notable changes to the fuzzy-filter skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.0.2] - 2026-06-25

### Added
- "Code-navigation idioms" table to `SKILL.md` capturing the patterns that recur in real codebase navigation — jump to a definition (`'def\ parse_config`), a symbol minus its tests (`'UserSession !tests/`), symbol + area + skip-tests (`'HttpClient 'handlers/ !tests/`) — distilling the shape "exact term(s) with `\ ` for phrases + `!path` exclusions"
- Escaped-space (`def\ get`) row to the "Fuzzy Filter Syntax" table, plus a note explaining that because a bare space is the AND separator, a multi-word phrase must backslash-escape its spaces (`'def\ parse_config` = contiguous phrase vs. `'def 'parse_config` = two independent terms), and that the escape survives the shell in double quotes and is a literal backslash through the fuzzy-search MCP `fuzzy_filter` string

## [1.0.1] - 2026-06-11

### Added
- `references/pipelines.md`: "Clipboard & editor hand-off" section — batch analogs of the classic interactive fif/fiv-style shell helpers over `file:line:content` rows (best content hit → clipboard via pbcopy; best hit → `code`/`cursor --goto file:line` via `--accept-nth='{1}:{2}'`), including reusable `ffq` (no hand-off, ranked rows only)/`fifq`/`fivq` function forms; verified against fzf 0.73.1
- Content-search recipes for a single-file target — rg drops the path column so rows become `line:content` and fields shift to `--nth=2..` — plus the `-H`/`--with-filename` fix that pins the standard `file:line:content` shape

### Changed
- Expanded the "Fuzzy Filter Syntax" table from a terse recap to the full upstream token set — added `'wild'` exact-boundary-match `(fzf 0.55+)`, `!^prefix`, and `!suffix$` inverse-anchor rows — so the skill no longer defers to the fzf skill for the full table
- Documented that `--exact` also applies in batch mode (`fzf --exact --filter Q`), with the `'`-prefix inverting to mean "unquote" (fuzzy)

### Fixed
- `--with-nth` does **not** affect `--filter` output (it only restyles the interactive UI; batch mode always prints the full row) — the "hide `file:line:` from the OUTPUT" recipe in pipelines.md and the SKILL.md field-scoping table claimed otherwise. Replaced with `--accept-nth` `(fzf 0.60+)` plus a `cut -d: -f3-` pre-0.60 fallback, and corrected the field-scoping table and output notes

## [1.0.0] - 2026-06-04

### Added
- Initial addition to marketplace — a skill for the **non-interactive** `rg`/`fd`/`rga` → `fzf --filter` pipeline, the CLI technique behind the `fuzzy-search` MCP server
- `SKILL.md`: two-stage mental model (regex scan → fuzzy rank; fuzzy ≠ regex), a when-to-use/when-not disambiguation table (vs. the fzf skill's interactive use, vs. the fuzzy-search MCP, vs. plain rg/fd), prerequisites, terse fuzzy-syntax recap (linking the fzf skill), fuzzy FILE search (`rg --files`/`fd` → fzf, NUL-safe `--read0`/`--print0`, `--scheme=path`), fuzzy CONTENT search (`rg --line-number --no-heading --color=never . PATH | fzf --filter Q --delimiter : --nth=1,3..`; content-only `--nth=3..`; why field 2/line-number is skipped), a `--delimiter`/`--nth`/`--with-nth` field-scoping deep-dive, document/PDF search via `rga`, gotchas, and See-also cross-links
- `references/pipelines.md`: full recipe catalog (files/content/documents, NUL-safe end-to-end, limiting/sorting/xargs hand-off) **plus the exact MCP-equivalent command for every `fuzzy-search` tool** (`fuzzy_search_files`/`fuzzy_search_content`/`fuzzy_search_documents` + PDF tools) — the "replicate the MCP" payload
- `references/pdf.md`: `rga` adapter configuration and PDF page-count/outline/extraction via `pdftotext`/`pdfinfo`/PyMuPDF — the CLI analog of the MCP's PDF inspection tools
- Light `(rga 0.10+)` / `(fzf 0.36+)` version annotations only where genuinely version-specific; long-standing basics left unannotated
- All recipes verified against ripgrep 14.1.1, fzf 0.55, fd 8.6, and ripgrep-all 0.10.9
- See-also cross-links added from the fzf, ripgrep, and fd skills' integration/recipe references back to this skill for the non-interactive technique
