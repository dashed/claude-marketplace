# Changelog - tmux

All notable changes to the tmux skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.2.3] - 2025-11-23

### Changed
- Enhanced SKILL.md with requirement to check existing sessions before creating new ones
- Added IMPORTANT notes in Quickstart and Helper: create-session.sh sections to run list-sessions.sh first
- Improved workflow safety by mandating session name conflict checking to prevent accidental overwrites

## [1.2.2] - 2025-11-23

### Added
- lib/time_utils.sh library with time_ago() function for converting ISO 8601 timestamps to human-readable format
- Comprehensive test suite for time_ago() function with 10 new tests (tests 21-30 in test-list-sessions.sh)
- Test coverage for UTC 'Z' suffix parsing, '+0000' format, time intervals (seconds/minutes/hours/days), UTC midnight boundary, invalid/empty timestamps, and edge cases
- NOW_EPOCH environment variable support in time_ago() for deterministic testing

### Fixed
- UTC timezone bug in time_ago() function where 'Z' suffix was matched as literal character but interpreted as local time instead of UTC on macOS
- Cross-platform UTC timestamp parsing now uses TZ=UTC with %z format on macOS and proper fallbacks for Linux
- Empty array bug in list-sessions.sh when using set -u with no registered sessions (sessions_with_health[@] expansion)

### Changed
- Extracted time_ago() function from list-sessions.sh to lib/time_utils.sh library for better testability and reusability
- list-sessions.sh now sources lib/time_utils.sh for time formatting functionality
- Test infrastructure now sources time_utils.sh directly for isolated unit testing of time functions

## [1.2.1] - 2025-11-23

### Changed
- Moved "Alternative: Manual Socket Management" section to references/direct-socket-control.md for better progressive disclosure
- Renamed section from "Alternative" to "Advanced: Direct Socket Control" to strengthen mental model
- Reduced SKILL.md from ~553 to ~508 lines (8% reduction)
- Added references/direct-socket-control.md with comprehensive manual socket management documentation
- Strengthened mental model positioning: session registry as canonical approach, direct socket control as advanced option
- Added comparison table and migration guide to direct-socket-control.md reference

## [1.2.0] - 2025-11-23

### Changed
- Enhanced test-safe-send.sh with 8 unit tests for session registry features (29 total tests, all passing)
- Enhanced test-wait-for-text.sh with 8 unit tests for session registry features (21 total tests, all passing)
- Enhanced test-pane-health.sh with 8 unit tests for session registry features (26 total tests, all passing)
- Test coverage now includes -s flag validation, auto-detection, and priority resolution (24 new tests)

### Fixed
- Fixed bash syntax errors in test cleanup functions (replaced invalid glob pattern redirection with shopt -s nullglob)
- Fixed test logic in cleanup-sessions test for --older-than flag validation

## [1.1.0] - 2025-11-23

### Added
- pane-health.sh tool for comprehensive health checking of tmux panes (360 lines)
- Health checking supports 5 exit codes for different states (healthy, dead, missing, zombie, server not running)
- JSON and text output formats for pane-health.sh
- Comprehensive test suite for pane-health.sh (18/18 tests passing, 100% success rate)
- pane-health.sh validates: server running, session exists, pane exists, pane dead flag, process running via ps
- safe-send.sh tool for reliable command sending with automatic retries and prompt waiting (367 lines, 21/21 tests passing)
- Automatic retry mechanism with exponential backoff (0.5s → 1s → 2s) for transient failures
- Integration with pane-health.sh for pre-flight readiness checks and wait-for-text.sh for prompt synchronization
- Dual-mode operation (normal mode executes commands, literal mode types text without Enter)
- Comprehensive test suite for safe-send.sh covering error handling, retries, modes, and control sequences

### Changed
- Enhanced SKILL.md with pane-health.sh and safe-send.sh documentation (+111 lines total)
- Added pane-health.sh section with usage examples, exit codes, and JSON output schema
- Updated "Sending input safely" section to recommend safe-send.sh as primary method
- Comprehensive notes/tmux/README.md update (52 → 642 lines, 12x expansion)
- Added detailed "How the tmux Skill Works" section covering architecture, socket isolation, session management, input handling, output capture, synchronization, and health checking
- Updated "Input Handling" section to recommend safe-send.sh for production use
- Added documentation for all 4 helper tools (wait-for-text.sh, find-sessions.sh, pane-health.sh, safe-send.sh)
- Added Interactive Tool Support section with recipes for Python REPL, gdb, and other tools
- Added Common Patterns section with 4 real-world usage patterns
- Added Limitations & Gotchas section documenting known issues and common mistakes
- Added Testing section documenting pane-health.sh and safe-send.sh test results and coverage
- Removed safe-send.sh from "Future Enhancements" section (now implemented)

## [1.0.1] - 2025-11-23

### Fixed
- wait-for-text.sh now supports custom tmux sockets via -S/--socket parameter
- wait-for-text.sh can now work with isolated socket directories as recommended in the skill

### Changed
- Enhanced SKILL.md documentation emphasizing PYTHON_BASIC_REPL=1 as CRITICAL requirement
- Updated all Python REPL examples to include PYTHON_BASIC_REPL=1 environment variable
- Updated quickstart example to show proper Python REPL initialization
- Added example in wait-for-text.sh documentation showing custom socket usage
- Updated synchronization examples to include socket parameter

## [1.0.0] - 2025-11-23

### Added
- Initial addition to marketplace from [mitsuhiko/agent-commands](https://github.com/mitsuhiko/agent-commands/tree/main/skills/tmux)
- Remote control tmux sessions for interactive CLIs (python, gdb, etc.)
- Helper tools for session management:
  - find-sessions.sh for discovering tmux sessions
  - wait-for-text.sh for synchronization and waiting for output
- Version metadata (v1.0.0)
- Author information (Alberto Leal)
- License information (Vibecoded)
- Keywords: tmux, terminal, multiplexer, interactive, debugging, repl
- Plugin configuration with skills loading from root

### Changed
- Enhanced description with "Use when..." clause for improved skill discovery
- Added trigger terms: debugging, interactive shells, REPL usage
