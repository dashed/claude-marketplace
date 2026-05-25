# Changelog - statusline

All notable changes to the statusline skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
