# Changelog - ripgrep

All notable changes to the ripgrep skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-04

### Added
- Initial addition to marketplace — a skill for the `ripgrep` (`rg`) command-line tool (a fast, gitignore-aware recursive `grep`), authored against ripgrep 15.x
- `SKILL.md` spine: overview, install, basic usage (recursive + smart-case `-S`), regex syntax (Rust default; `-F`/`-P`/`--engine`/`-w`/`-x`/`-U` + `--multiline-dotall`), file selection (`-t`/`-T`/`--type-list`/`--type-add`, `-g`/`--iglob`, hidden/ignored `-.`/`-u`/`-uu`/`-uuu` + gitignore behavior), context (`-A`/`-B`/`-C`), output (`-o`/`-r`/`-c`/`-l`/`--json`/`--vimgrep`/`--color`/`--hyperlink-format`/`-0`), sorting/perf (`--sort`/`-z`/`--pre`), config (`RIPGREP_CONFIG_PATH`), integration (fzf/fd/editors/git), and troubleshooting
- `references/options.md` — exhaustive reference for all 104 flags, grouped by ripgrep's real `doc_category` (Input, Search, Filter, Output, Output Modes, Logging, Other Behaviors), with a deprecated/removed table; verified against `crates/core/flags/defs.rs`
- `references/recipes.md` — multiline search, replacements (with the `$1X` named-group capture gotcha), custom file types, `--json`/`--vimgrep` tooling, `--pre`/`-z` preprocessing, config-file usage, engine selection, and fzf/fd/editor/git integration
- `references/version-features.md` — a "feature → minimum ripgrep version" lookup (mirrors the git/fzf/fd skills), versions traced to their introducing ripgrep CHANGELOG section headers
- Inline `(rg X.Y+)` version annotations across all files for version-specific features (e.g. `--engine` 12.0+, `--field-context-separator` 13.0+, `--hyperlink-format`/`--stop-on-nonmatch`/`--generate` 14.0+, `-r`+`--json` 15.0+); long-standing basics left unannotated
- Documents key corrections verified against source: there is **no bare `--hyperlink`** flag (only `--hyperlink-format`), `--generate` replaced the removed `--man`, and `--engine` replaced the deprecated `--auto-hybrid-regex`
