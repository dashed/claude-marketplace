# Notes - tmux

Meta-documentation for the tmux skill plugin.

## Overview

The tmux skill enables remote control of tmux sessions for interactive CLI tools like Python REPLs, gdb debuggers, and other interactive shells. It provides programmatic control through keystroke sending and output scraping.

## Contents

Currently no detailed documentation files. See "Future Documentation" below.

## Key Insights

- **Critical**: `PYTHON_BASIC_REPL=1` environment variable required for Python REPLs
  - The fancy REPL with syntax highlighting interferes with send-keys
  - Must be set before starting Python

- **Socket isolation**: Custom sockets via `-S` flag prevent interference with user's tmux
  - Convention: `${TMPDIR:-/tmp}/claude-tmux-sockets/`
  - Enables multiple agent sessions without conflicts

- **Synchronization**: `wait-for-text.sh` helper essential for waiting on interactive prompts
  - Polls pane output for regex patterns
  - Prevents race conditions with async tools
  - Now supports custom sockets (v1.0.1)

- **Helper scripts**: Two key utilities
  - `wait-for-text.sh` - Poll for text patterns with timeout
  - `find-sessions.sh` - Discover sessions across sockets

## Related Documentation

- [Plugin Source](../../plugins/tmux/)
- [Changelog](../../changelogs/tmux.md)
- [SKILL.md](../../plugins/tmux/SKILL.md)
- [wait-for-text.sh](../../plugins/tmux/tools/wait-for-text.sh)
- [find-sessions.sh](../../plugins/tmux/tools/find-sessions.sh)

## Version

Documented for tmux skill v1.0.1

## Future Documentation

Potential additions:
- `analysis.md` - Architecture of tmux integration, how send-keys works
- `design-decisions.md` - Why socket isolation, why wait-for-text polling approach
- `implementation-notes.md` - Key gotchas discovered during development
- `testing-strategy.md` - How to test tmux skill (automated testing challenges)
- `known-issues.md` - PYTHON_BASIC_REPL requirement, terminal width limitations
