# Changelog - git-absorb

All notable changes to the git-absorb skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.1.0] - 2026-01-15

### Changed
- Implemented progressive disclosure pattern with references/ directory
- Added references/advanced-usage.md with comprehensive flag reference (13 flags documented, 7 usage patterns)
- Added references/configuration.md with all 7 configuration options and examples
- Updated SKILL.md to be leaner (269 → 232 lines, 14% reduction) with references to detailed documentation
- Moved ANALYSIS.md to top-level marketplace references/ (not useful for Claude during skill execution)

## [1.0.0] - 2025-11-23

### Added
- Initial addition to marketplace for automatically folding uncommitted changes into appropriate commits
- Comprehensive documentation analysis (ANALYSIS.md) comparing against official git-absorb documentation
- Use case: Applying review feedback and maintaining atomic commit history
- Version metadata (v1.0.0)
- Author information (Alberto Leal)
- License information (MIT)
- Keywords: git, workflow, commits, rebase, fixup
- Plugin configuration with skills loading from root

### Changed
- Removed automatic installation attempts (now recommends manual installation only)
- Added important default behaviors section explaining author filtering and stack size limits
- Added configuration section with critical maxStack setting and other useful options
- Enhanced troubleshooting section with stack limit warning solutions
