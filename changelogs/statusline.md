# Changelog - statusline

All notable changes to the statusline skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.2.0] - 2026-06-11

### Added
- jj ⇄ git sync segment in the reference script: colocated repos compare `git rev-parse HEAD` against jj's last-imported `git_head()` and show `[jj ⇄ git out of sync: git +N, jj +N]` only when they diverge (e.g. after direct git commits; the script's `--ignore-working-copy` calls never trigger jj's auto-import)
- Detached-HEAD fallback in the git block: `git branch --show-current` prints nothing when detached, so the segment now renders `detached @ <short-hash>` — without it, jj-colocated repos (where git is permanently detached) never showed the git segment at all
- Output examples for both cases and Design Notes covering the sync check, the detached fallback, and the IFS tab gotcha

### Fixed
- IFS tab field-collapse bug in the jj template parsing: the empty no-conflict field (`if(conflict, "conflict", "")`) was swallowed by `IFS=$'\t' read` (tab is IFS whitespace — consecutive tabs collapse instead of preserving empty fields), shifting the commit id into `conflict_status`. Every jj repo permanently showed `: conflict`, and the always-empty `commit_hash` silently disabled the jj ahead/behind feature. All template fields now use a `-` placeholder

## [1.1.0] - 2026-05-25

### Changed
- Dual VCS mode: show both jj and git status independently (both appear for colocated repos)
- Add ahead/behind remote tracking to jj block using commit_id and git rev-list
- Change from jj-priority if/elif to independent if/if blocks
- Fix comma-join bug in status_parts formatting (IFS trick to printf)
- Fix git ahead/behind labels (were swapped in original)
- Add `[git ...]` prefix to git block output for clarity

## [1.0.0] - 2026-05-23

### Added
- Initial addition to marketplace
- Full reference script with git + jj VCS detection (jj priority for colocated repos)
- Complete documentation of all available JSON fields from Claude Code
- Setup instructions with settings.json configuration
- Multi-line statusline example with context bar and cost
- Design notes on --ignore-working-copy for jj performance
- Customization examples (adding description, changing git format)
