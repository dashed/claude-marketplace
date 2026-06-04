# Changelog - fd

All notable changes to the fd skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-04

### Added
- Initial addition to marketplace — a skill for the `fd` command-line tool (a fast, user-friendly `find` replacement), authored against fd v10.4.2
- `SKILL.md` spine: overview, install (`fd` vs Debian/Ubuntu `fdfind`), basic usage (regex-by-default + smart-case), pattern syntax (regex vs glob `-g`, full-path `-p`), filtering (type/extension/hidden/ignored/depth/size/time + `.gitignore` behavior), command execution (`-x`/`-X` with the five path placeholders), output (`-l`/`-0`/`--format`/`--hyperlink`), common workflows, integration (fzf/ripgrep/xargs/parallel/git), and troubleshooting
- `references/options.md` — exhaustive flag reference grouped by area (search/pattern, filters, ignore/hidden, traversal, execution, output), verified against fd v10.4.2 `src/cli.rs` + `doc/fd.1`
- `references/recipes.md` — advanced command-execution patterns, exclusion mechanics, tool-integration recipes, and troubleshooting
- `references/version-features.md` — a "feature → minimum fd version" lookup (mirrors the git/fzf skills' pattern), versions traced to their introducing fd CHANGELOG section headers
- Inline `(fd X.Y+)` version annotations across all files for version-specific features (e.g. `--format` 10.1+, `--hyperlink` 10.2+, `--and` 8.6+, `--prune` 8.2+, `-t dir` alias 10.0+); long-standing basics left unannotated
- Documents that fd has **no `{n}`/positional placeholders** (an fzf-ism), and excludes master-only flags (`--exact`, `--ignore-parent` override) not present in v10.4.2
