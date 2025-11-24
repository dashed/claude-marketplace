# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.2] - 2025-11-23

### Changed
- tmux skill: Enhanced documentation to require session name conflict checking before creation
- tmux skill: Added IMPORTANT notes to check list-sessions.sh before creating new sessions
- tmux skill: Version bumped to 1.2.3

## [0.6.1] - 2025-11-23

### Added
- tmux skill: lib/time_utils.sh library for time utility functions (time_ago() for ISO 8601 to human-readable conversion)
- tmux skill: Comprehensive test suite for time_ago() function with 10 new tests covering UTC parsing, time intervals, and edge cases

### Fixed
- tmux skill: UTC timezone bug in time_ago() where 'Z' suffix was interpreted as local time instead of UTC on macOS
- tmux skill: Empty array bug in list-sessions.sh when using set -u with no registered sessions

### Changed
- tmux skill: Extracted time_ago() to lib/time_utils.sh for better testability and reusability
- tmux skill: Version bumped to 1.2.2

## [0.6.0] - 2025-11-23

### Changed
- tmux skill: Moved "Alternative" section to references/direct-socket-control.md (progressive disclosure pattern)
- tmux skill: Renamed "Alternative: Manual Socket Management" to "Advanced: Direct Socket Control" (mental model strengthening)
- tmux skill: Reduced SKILL.md by 8% for improved conciseness and focus
- tmux skill: Version bumped to 1.2.1
- skill-reviewer skill: Relaxed Ownership criterion from required to optional
- skill-reviewer skill: Updated quality standards to make SKILL.md version sections optional while marketplace changelogs remain required
- skill-reviewer skill: Enhanced quality-checklist.md with guidance on when to include/skip version metadata
- skill-reviewer skill: Version bumped to 1.1.0

## [0.5.0] - 2025-11-23

### Added
- skill-reviewer skill: Systematic quality review framework with 10-point checklist
- skill-reviewer skill: Review workflow for new skills, updates, and audits
- skill-reviewer skill: Ownership metadata pattern with Version section (version, date, maintainer, changelog link)
- skill-reviewer skill: Testing/verification guidance pattern with Quick Verification section
- skill-reviewer skill: Comprehensive references/examples.md with 4 sample reviews (1,460 words)
- skill-reviewer skill: Sample reviews demonstrating simple, complex, quick audit, and before/after improvement patterns
- skill-reviewer skill: Progressive disclosure structure with 5 reference documents (7,459 words total)

### Changed
- skill-reviewer skill: Enhanced SKILL.md with ownership and testing sections (718 → 888 words, 59% of budget)
- skill-reviewer skill: Restructured Examples section to reference both examples.md and quality-checklist.md
- skill-reviewer skill: Detailed Guidance section now includes Review Examples link

## [0.4.0] - 2025-11-23

### Added
- tmux skill: Session registry system for automatic session tracking (~80% boilerplate reduction)
- tmux skill: tools/lib/registry.sh library for session management (415 lines, 28/28 tests passing)
- tmux skill: Portable file locking (flock on Linux, mkdir-based on macOS)
- tmux skill: create-session.sh tool for creating and registering sessions (229 lines, 20/20 tests passing)
- tmux skill: list-sessions.sh tool for listing sessions with health status (297 lines, 20/20 tests passing)
- tmux skill: cleanup-sessions.sh tool for removing dead/stale sessions (233 lines, 15/15 tests passing)
- tmux skill: Session name lookup via `-s` flag (auto-detection when single session exists)
- tmux skill: Integration test suite (test-session-integration.sh, 12/12 tests passing)
- tmux skill: Comprehensive session registry reference documentation (references/session-registry.md, 530+ lines)
- tmux skill: Session registry architecture documentation in notes/tmux/README.md
- tmux skill: Makefile test targets for session registry (test-session-registry, test-create-session, test-list-sessions, test-cleanup-sessions, test-session-integration)
- tmux skill: Docker-based test infrastructure for all tmux tests (9 test suites total)
- tmux skill: Test grouping in Makefile with helper macros for consistent execution

### Changed
- tmux skill: safe-send.sh now supports `-s` flag for session name lookup
- tmux skill: wait-for-text.sh now supports `-s` flag for session name lookup
- tmux skill: pane-health.sh now supports `-s` flag for session name lookup
- tmux skill: All core tools now support 3-tier session resolution (explicit flags > session name > auto-detect)
- tmux skill: SKILL.md restructured to make session registry the default approach (553 lines)
- tmux skill: Removed "RECOMMENDED" and "NEW" terminology from SKILL.md (mental model shift to "this is the way")
- tmux skill: Added Quickstart section showing session registry as primary usage
- tmux skill: Moved manual socket management to "Alternative: Manual Socket Management" section
- tmux skill: Added Best Practices and Troubleshooting sections to SKILL.md
- tmux skill: Updated notes/tmux/README.md with session registry documentation (v1.2.0)
- tmux skill: Updated helper tools count from 4 to 7 in documentation
- tmux skill: Updated Related Documentation section with all new tools and library
- tmux skill: Removed create-session.sh and cleanup-sessions.sh from Future Enhancements (now implemented)
- tmux skill: Enhanced test-safe-send.sh with 8 unit tests for session registry features (29 total tests, all passing)
- tmux skill: Enhanced test-wait-for-text.sh with 8 unit tests for session registry features (21 total tests, all passing)
- tmux skill: Enhanced test-pane-health.sh with 8 unit tests for session registry features (26 total tests, all passing)
- tmux skill: Test coverage now includes -s flag validation, auto-detection, and priority resolution (24 new tests)
- tmux skill: Version bumped to 1.2.0

### Fixed
- tmux skill: Fixed bash syntax errors in test cleanup functions (replaced invalid glob pattern redirection with shopt -s nullglob)
- tmux skill: Fixed test logic in cleanup-sessions test for --older-than flag validation

## [0.3.0] - 2025-11-23

### Added
- tmux skill: safe-send.sh tool for reliable command sending with automatic retries and prompt waiting (367 lines, 21/21 tests passing)
- tmux skill: Automatic retry mechanism with exponential backoff (0.5s → 1s → 2s) for transient failures
- tmux skill: Integration with pane-health.sh for pre-flight readiness checks and wait-for-text.sh for prompt synchronization
- tmux skill: Dual-mode operation (normal mode executes commands, literal mode types text without Enter)
- tmux skill: Comprehensive test suite for safe-send.sh covering error handling, retries, modes, and control sequences
- tmux skill: pane-health.sh tool for comprehensive health checking (360 lines, 18/18 tests passing)
- tmux skill: Health checking with 5 exit codes (healthy, dead, missing, zombie, server not running)
- tmux skill: JSON and text output formats for pane-health.sh
- tmux skill: Comprehensive notes/tmux/README.md documentation (52 → 642 lines, 12x expansion)
- tmux skill: Detailed architecture documentation (socket isolation, session management, input/output handling)
- tmux skill: Interactive tool support recipes (Python REPL, gdb debugger, and others)
- tmux skill: Common usage patterns section with 4 real-world examples
- tmux skill: Limitations & gotchas documentation with security considerations

### Fixed
- tmux skill: wait-for-text.sh now supports custom sockets via -S/--socket parameter

### Changed
- git-absorb skill: Implemented progressive disclosure pattern with references/ directory
- git-absorb skill: Added comprehensive reference documentation (advanced-usage.md, configuration.md)
- git-absorb skill: Reduced SKILL.md size by 14% (269 → 232 lines) while improving discoverability
- tmux skill: Enhanced documentation emphasizing PYTHON_BASIC_REPL=1 as critical requirement
- tmux skill: Updated all Python REPL examples to include PYTHON_BASIC_REPL=1
- tmux skill: Enhanced SKILL.md with safe-send.sh and pane-health.sh documentation (+111 lines total)
- tmux skill: Updated "Sending input safely" section to recommend safe-send.sh as primary method
- tmux skill: Enhanced notes/tmux/README.md with safe-send.sh documentation and updated helper tools count to 4
- tmux skill: Updated "Input Handling" section to recommend safe-send.sh for production use
- tmux skill: Removed safe-send.sh from "Future Enhancements" section (now implemented)
- tmux skill: Version bumped to 1.1.0

## [0.2.0] - 2025-11-23

### Added
- Static validation system with comprehensive checks for marketplace integrity
- JSON schemas for validation: plugin-schema.json, marketplace-schema.json, skill-frontmatter-schema.json
- Python validation scripts: validate_yaml.py, validate_json.py, validate_structure.py, validate_all.py
- Makefile with targets for validation, testing, linting, and formatting
- uv-based Python environment management with pyproject.toml
- Automated validation for YAML frontmatter in SKILL.md files
- Automated validation for JSON manifests (plugin.json, marketplace.json)
- File structure and naming convention validation
- git-absorb skill for automatically folding uncommitted changes into appropriate commits
- Comprehensive documentation analysis (ANALYSIS.md) for git-absorb skill comparing against official documentation
- tmux skill for remote controlling tmux sessions for interactive CLIs (python, gdb, etc.) from [mitsuhiko/agent-commands](https://github.com/mitsuhiko/agent-commands/tree/main/skills/tmux)
- tmux skill helper tools: find-sessions.sh and wait-for-text.sh for session management and synchronization
- Version metadata (v1.0.0) for both plugins
- Author information for plugin attribution
- License information (Apache-2.0 for skill-creator, MIT for git-absorb, Vibecoded for tmux)
- Keywords for better plugin discovery and categorization
- Python/uv/testing artifacts to .gitignore

### Changed
- Modernized validation workflow to use `uv run` pattern for all Python scripts
- Removed unnecessary shebang lines from validator scripts (scripts/validators/*.py)
- Cleaned up dependencies: removed yamllint, markdown-it-py, linkchecker, mypy, and types-pyyaml (27% reduction)
- git-absorb skill: Removed automatic installation attempts (now recommends manual installation only)
- git-absorb skill: Added important default behaviors section explaining author filtering and stack size limits
- git-absorb skill: Added configuration section with critical maxStack setting and other useful options
- git-absorb skill: Enhanced troubleshooting with stack limit warning solutions
- tmux skill: Enhanced description with "Use when..." clause and trigger terms for improved skill discovery

## [0.1.0] - 2025-11-22

### Added
- Initial marketplace structure with `.claude-plugin/marketplace.json`
- skill-creator skill from [Anthropic's skills repository](https://github.com/anthropics/skills/tree/main/skill-creator)
- README with instructions for adding marketplace locally
- Marketplace metadata and owner information
- Plugin entry with `skills` field for proper skill loading

[Unreleased]: https://github.com/dashed/claude-marketplace/compare/v0.6.2...HEAD
[0.6.2]: https://github.com/dashed/claude-marketplace/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/dashed/claude-marketplace/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/dashed/claude-marketplace/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/dashed/claude-marketplace/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/dashed/claude-marketplace/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/dashed/claude-marketplace/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/dashed/claude-marketplace/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/dashed/claude-marketplace/releases/tag/v0.1.0
