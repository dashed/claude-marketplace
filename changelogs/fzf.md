# Changelog - fzf

All notable changes to the fzf skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.1.1] - 2026-06-11

### Added
- Search Syntax: documented `-e`/`--exact` mode and the upstream footnote that under `--exact` the `'`-prefix "unquotes" a term (making it fuzzy), matching the fzf README
- `(fzf 0.55+)` version annotation on the `'wild'` exact-boundary-match token in SKILL.md, plus a corresponding row in references/version-features.md (verified against the fzf CHANGELOG 0.55.0 section)
- `0.60 | --accept-nth` row in references/version-features.md (choose output fields; works in `--filter` batch mode too) — the flag was documented in options.md but missing from the version lookup

## [1.1.0] - 2026-06-04

### Added
- `references/version-features.md` — a consolidated "feature → minimum fzf version" lookup (grouped by version range, with a "unlisted = long-standing" preamble), mirroring the git skill's pattern; verified against the fzf CHANGELOG section headers
- Inline `(fzf X.Y+)` version annotations across SKILL.md and all reference files for version-specific features (e.g. `--popup`/Zellij 0.71, `--nushell`/`every(N)`/`--preview-window=next` 0.73, `toggle-wrap-word` 0.68, footer actions 0.63, `become` 0.38, `transform` 0.45); long-standing basics deliberately left unannotated
- A minimum-version note in SKILL.md (shell-integration flags need fzf ≥0.48) and a `transform`-based unified ripgrep/fzf toggle example in integrations.md

### Fixed
- Documented the actual default binding of `ctrl-/` / `alt-/` as `toggle-wrap-word` (rebound from `toggle-wrap` in fzf 0.68), and corrected the `ALT-R` description to `toggle-raw` ("toggle between cleaned and raw history line")
- `options.md`: `--popup` is now documented as the primary flag (tmux 3.3+ or Zellij 0.44+), with `--tmux` noted as its back-compat alias
- Softened `actions.md`'s "complete reference" claim to point at `man fzf` / `src/actiontype_string.go` for the exhaustive list
- Hardened the git-branch and git-status integration recipes (strip `* `/`remotes/` prefixes; note rename/untracked caveats)

### Changed
- Added missing modern surface: options (`dashed` border, `--nushell`, `--preview-window=next`, `--id-nth`, `--gutter-raw`, `--preview-wrap-sign`); actions/events (`every(N)`, footer + `change-with-nth`/`change-header-lines` + `transform-*` variants, `delete-char/eof`); and a documented smart-case default

## [1.0.0] - 2025-11-24

### Added
- Initial addition to marketplace
- Comprehensive SKILL.md covering shell integration, search syntax, preview windows, and event bindings
- references/actions.md with complete list of bindable actions and events
- references/options.md with full command-line options reference
- references/integrations.md with ripgrep, fd, bat, git, docker, and kubernetes recipes
- Shell integration documentation for bash, zsh, and fish (CTRL-T, CTRL-R, ALT-C, ** completion)
- Search syntax reference with fuzzy matching, exact matching, prefix/suffix, negation, and OR operators
- Common patterns for file search, git workflows, and dynamic list reloading
