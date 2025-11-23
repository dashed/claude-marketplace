# Tool Recommendations for tmux Skill

Analysis of potential helper tools to add to the tmux skill for improved reliability, usability, and automation.

**Date:** 2025-11-23
**Version:** tmux skill v1.0.1
**Status:** Analysis complete, implementation pending

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Current State](#current-state)
- [Analysis Methodology](#analysis-methodology)
- [Identified Gaps](#identified-gaps)
- [Recommended Tools](#recommended-tools)
  - [Critical Priority](#critical-priority)
  - [High Priority](#high-priority)
  - [Medium Priority](#medium-priority)
- [Implementation Considerations](#implementation-considerations)
- [Next Steps](#next-steps)
- [References](#references)

---

## Executive Summary

The tmux skill currently has two helper tools (`wait-for-text.sh`, `find-sessions.sh`) but lacks critical functionality for:
- **Health checking** - No way to verify pane/session state before operations
- **Reliable sending** - Commands can be dropped if pane is busy
- **Automated cleanup** - Complex manual commands required
- **Clean output** - ANSI codes and formatting issues

**Recommendation:** Implement 3 critical tools (pane-health.sh, safe-send.sh, cleanup-sessions.sh) to address these gaps, followed by 2 high-priority tools for improved usability.

---

## Current State

### Existing Tools

**1. wait-for-text.sh**
- **Purpose:** Poll pane for regex pattern with timeout
- **Functionality:** Synchronization primitive for waiting on prompts
- **Status:** ✓ Working well, recently enhanced with socket support (v1.0.1)
- **Location:** `plugins/tmux/tools/wait-for-text.sh`

**2. find-sessions.sh**
- **Purpose:** List sessions on sockets with metadata
- **Functionality:** Discovery of running sessions, supports filtering
- **Status:** ✓ Working well, supports custom sockets
- **Location:** `plugins/tmux/tools/find-sessions.sh`

### Current Capabilities

From SKILL.md analysis:

✓ **Session management**
- Create sessions on isolated sockets
- Find/enumerate sessions
- Manual cleanup operations

✓ **Input handling**
- Send keystrokes with `send-keys`
- Send control characters (C-c, C-d, etc.)
- Literal mode for safe sending

✓ **Output monitoring**
- Capture pane output
- Wait for text patterns (via wait-for-text.sh)
- Manual output inspection

✓ **Interactive tool support**
- Python REPL (with PYTHON_BASIC_REPL=1)
- gdb debugger
- Other interactive shells

### Pain Points Identified

**From SKILL.md:**

1. **Line 70:** "CRITICAL" warning about PYTHON_BASIC_REPL=1
   - Indicates send-keys can fail silently
   - Need better failure detection

2. **Lines 91-93:** Complex cleanup commands
   ```bash
   tmux -S "$SOCKET" kill-session -t "$SESSION"
   tmux -S "$SOCKET" list-sessions -F '#{session_name}' | xargs -r -n1 tmux -S "$SOCKET" kill-session -t
   tmux -S "$SOCKET" kill-server
   ```
   - Error-prone, needs automation

3. **Line 62:** "don't assume they remembered the command"
   - Need easy session state access
   - Monitoring could be simpler

4. **No health checks:** No way to verify if pane is alive before operations

5. **No retry logic:** Commands sent once, can be dropped

---

## Analysis Methodology

### 1. Documentation Review
- Analyzed `SKILL.md` for patterns and pain points
- Reviewed existing tools for capabilities and gaps
- Examined interactive tool recipes (Python, gdb, etc.)

### 2. Codex Consultation
- **Query 1:** Asked for helper tool suggestions for tmux automation
- **Query 2:** Asked about common failure modes and error scenarios

### 3. Failure Mode Analysis

Codex identified critical failure modes:

**Session/Pane Lifecycle:**
- Stale sockets and orphaned sessions
- Dead panes (`#{pane_dead}`)
- Zombie processes
- Detached clients altering state

**Timing/Races:**
- Commands sent before pane ready
- Layout changes after splits
- Resize operations not synchronized
- Fixed sleeps instead of readiness checks

**Process State:**
- No PID tracking
- Can't detect process exit
- No way to read exit status
- Zombie detection missing

**Output Capture:**
- ANSI color codes interfere with parsing
- Long outputs cause issues
- Transient "pane not found" errors
- Newline termination problems

**Cleanup/Resource Leaks:**
- Temp panes/sessions not killed on error
- Socket files accumulate
- Pipe files left behind
- tmux options not reset

---

## Identified Gaps

### Critical Gaps

1. **No health/liveness checking**
   - Can't verify pane exists before operations
   - Can't detect crashed processes
   - No zombie detection
   - **Impact:** Silent failures, poor error messages

2. **No safe command sending**
   - Commands dropped if pane busy
   - No retry logic
   - No readiness checking
   - **Impact:** Unreliable execution, intermittent failures

3. **No automated cleanup**
   - Manual commands required (error-prone)
   - No garbage collection
   - Resource leaks
   - **Impact:** Socket accumulation, process leaks

### High-Priority Gaps

4. **No clean output capture**
   - ANSI codes included in output
   - No formatting options
   - Long output handling missing
   - **Impact:** Parsing difficulties, data corruption

5. **No session creation helper**
   - Boilerplate repeated (lines 14-18)
   - Environment setup manual (PYTHON_BASIC_REPL=1)
   - No standardization
   - **Impact:** Code duplication, easy to forget critical setup

---

## Recommended Tools

### Critical Priority

These tools address fundamental reliability and safety issues.

---

#### 1. pane-health.sh

**Priority:** 🔴 Critical
**Rationale:** Essential for error handling and preventing operations on dead panes

**Purpose:**
Verify pane/session state before operations to prevent "pane not found" errors and detect failures early.

**Functionality:**
- Check if tmux server is running on socket
- Verify session exists (`has-session`)
- Check if pane exists and is alive (`#{pane_dead}`)
- Detect process state (running/exited/zombie)
- Check PID validity via `ps`
- Return structured status information

**Interface:**
```bash
./tools/pane-health.sh -S "$SOCKET" -t "$SESSION":0.0 [--format json|text]

Exit codes:
  0 - Healthy (pane alive, process running)
  1 - Dead (pane marked as dead)
  2 - Missing (pane/session doesn't exist)
  3 - Zombie (process exited but pane still exists)
  4 - Server not running

JSON output example:
{
  "status": "healthy|dead|missing|zombie",
  "pane_exists": true,
  "pane_dead": false,
  "pid": 12345,
  "process_running": true,
  "session_exists": true
}
```

**Use Cases:**
- Before sending commands: verify pane is ready
- After errors: determine if pane crashed
- Periodic health checks during long operations
- Cleanup decision: which panes to kill vs keep

**Codex Insights:**
> "verify server socket exists and matches expected TMUX; check tmux has-session -t name and tmux list-panes before acting; handle stale sockets and orphaned sessions; detect closed panes via pane_dead flag"

**Implementation Notes:**
- Use `tmux list-panes -F "#{pane_dead} #{pane_pid}"` for state
- Validate PID with `ps -p $PID` for process state
- Support both `-S socket` and `-L socket-name` modes
- Cache results for short period to reduce tmux calls

**Dependencies:**
- bash, tmux, ps

**Estimated Effort:** Medium (100-150 lines)

---

#### 2. safe-send.sh

**Priority:** 🔴 Critical
**Rationale:** Prevents dropped keystrokes, most common reliability issue

**Purpose:**
Send keystrokes with readiness checking, retries, and optional prompt waiting to ensure commands are reliably delivered.

**Functionality:**
- Wait for pane to be ready before sending
- Retry on transient "pane not found" errors (with backoff)
- Support both literal (`-l`) and normal send modes
- Optionally wait for prompt/pattern after sending
- Detect send failures
- Timeout protection

**Interface:**
```bash
./tools/safe-send.sh -S "$SOCKET" -t "$SESSION":0.0 -c "command" [options]

Options:
  -S, --socket      Socket path
  -t, --target      Target pane
  -c, --command     Command to send
  -l, --literal     Use literal mode (send-keys -l)
  -w, --wait        Wait for this pattern after sending
  -T, --timeout     Timeout in seconds (default: 30)
  -r, --retries     Max retries (default: 3)
  -i, --interval    Retry interval (default: 0.5s)
  -v, --verbose     Verbose output

Exit codes:
  0 - Command sent successfully
  1 - Failed to send after retries
  2 - Timeout waiting for prompt
  3 - Pane not ready
```

**Use Cases:**
- Send Python code to REPL: `safe-send.sh -c "print('hello')" -w ">>>"`
- Send gdb commands: `safe-send.sh -c "break main" -w "(gdb)"`
- Critical commands: automatic retry on failure
- After session creation: wait for pane readiness

**Codex Insights:**
> "Send keys with prompt-aware pacing: optionally wait for pane silence or a regex prompt before/after sending; retries on pane not found; avoids dropping keystrokes when the target is busy"

**Implementation Notes:**
- Call `pane-health.sh` first to verify readiness
- Use exponential backoff for retries (0.5s, 1s, 2s)
- Integrate with `wait-for-text.sh` for prompt waiting
- Support escape sequences (C-c, C-d) via special handling
- Log failed attempts for debugging

**Dependencies:**
- bash, tmux
- Optional: pane-health.sh (for readiness check)
- Optional: wait-for-text.sh (for prompt waiting)

**Estimated Effort:** Medium (150-200 lines)

---

#### 3. cleanup-sessions.sh

**Priority:** 🔴 Critical
**Rationale:** Automates error-prone cleanup, prevents resource leaks

**Purpose:**
Safe garbage collection of tmux sessions and sockets with policies for age, idle time, and patterns.

**Functionality:**
- Kill sessions by age (created > N hours ago)
- Kill sessions by idle time (no activity for > N minutes)
- Kill sessions by name pattern (regex matching)
- Remove orphaned socket files
- Clean up temp files, FIFOs, pipes
- Reset tmux options to defaults
- Dry-run mode (safe by default)
- Exclude patterns (protect specific sessions)

**Interface:**
```bash
./tools/cleanup-sessions.sh [options]

Options:
  -S, --socket         Specific socket to clean
  -A, --all            Clean all sockets in CLAUDE_TMUX_SOCKET_DIR
  --older-than TIME    Kill sessions older than TIME (e.g., 1h, 30m)
  --idle TIME          Kill sessions idle for TIME
  --pattern REGEX      Kill sessions matching pattern
  --exclude REGEX      Exclude sessions matching pattern
  --dry-run            Show what would be done (default)
  --execute            Actually perform cleanup
  -v, --verbose        Verbose output

Examples:
  # Dry run: sessions older than 1 hour
  cleanup-sessions.sh --older-than 1h --dry-run

  # Execute: idle sessions on all sockets
  cleanup-sessions.sh --all --idle 30m --execute

  # Kill claude-* sessions except claude-main
  cleanup-sessions.sh --pattern "^claude-" --exclude "claude-main" --execute
```

**Use Cases:**
- After agent errors: clean up orphaned sessions
- Periodic maintenance: remove old sessions
- Resource management: free up sockets
- User-requested cleanup: clear all agent sessions
- Testing: reset to clean state

**Codex Insights:**
> "Garbage collects orphaned sockets/sessions by policy (age, idle duration, name pattern); dry-run by default to avoid accidental kills"

**Implementation Notes:**
- Use `tmux list-sessions -F "#{session_created} #{session_activity} #{session_name}"`
- Parse timestamps for age/idle calculations
- Require `--execute` flag for actual cleanup (safety)
- Log all actions (what was killed, why)
- Handle errors gracefully (socket already gone, etc.)
- Clean socket files only if no sessions remain

**Dependencies:**
- bash, tmux, date

**Estimated Effort:** Medium-Large (200-250 lines)

---

### High Priority

These tools improve usability and reduce boilerplate.

---

#### 4. capture-clean.sh

**Priority:** 🟡 High
**Rationale:** Clean output essential for parsing, current capture includes ANSI codes

**Purpose:**
Capture pane output with cleaning (ANSI removal), formatting, and proper handling of long outputs.

**Functionality:**
- Capture pane output with specified line range
- Strip ANSI color codes and control sequences
- Multiple output formats (plain, JSON, structured)
- Handle long outputs (pagination, truncation)
- Proper newline handling
- Timestamp capture times

**Interface:**
```bash
./tools/capture-clean.sh -S "$SOCKET" -t "$SESSION":0.0 [options]

Options:
  -S, --socket      Socket path
  -t, --target      Target pane
  -l, --lines       Number of lines to capture (default: 1000)
  -s, --start       Start line (negative = from end, default: -1000)
  --format FORMAT   Output format: plain|json|raw (default: plain)
  --no-strip        Don't strip ANSI codes
  --max-length N    Truncate output to N chars
  -o, --output FILE Write to file instead of stdout

Output formats:
  plain: Clean text, ANSI stripped
  json:  {"lines": [...], "timestamp": "...", "line_count": N}
  raw:   Raw capture (with ANSI if --no-strip)
```

**Use Cases:**
- Get clean Python REPL output for parsing
- Capture error messages without color codes
- Extract command output as JSON for structured processing
- Save pane history to file

**Codex Insights:**
> "strip color (sed -r 's/\\x1b\\[[0-9;]*[a-zA-Z]//g') when parsing; handle long outputs by paging or chunking; ensure newline termination when relying on prompt detection"

**Implementation Notes:**
- ANSI stripping regex: `sed 's/\x1b\[[0-9;]*[a-zA-Z]//g'`
- Use `tmux capture-pane -p -J` for joined lines
- JSON output includes metadata (timestamp, target, line count)
- Handle `\r\n` vs `\n` newlines correctly
- Support piping to other tools

**Dependencies:**
- bash, tmux, sed

**Estimated Effort:** Small-Medium (80-120 lines)

---

#### 5. create-session.sh

**Priority:** 🟡 High
**Rationale:** Reduces boilerplate, ensures critical setup (PYTHON_BASIC_REPL=1)

**Purpose:**
One-stop session creation with presets for common interactive tools and environment configuration.

**Functionality:**
- Create socket directory + tmux session in one call
- Presets for common tools (python, gdb, node, psql, etc.)
- Auto-configure environment variables
- Return session info in structured format
- Handle errors gracefully
- Support custom initialization commands

**Interface:**
```bash
./tools/create-session.sh --name SESSION [options]

Options:
  --name NAME       Session name (required)
  --preset TYPE     Use preset: python|gdb|node|psql|bash
  --socket PATH     Custom socket path
  --command CMD     Custom command to run (overrides preset)
  --env KEY=VAL     Set environment variable
  --format FORMAT   Output format: json|shell (default: json)
  --window-name     Window name (default: shell)
  -v, --verbose     Verbose output

Presets:
  python: PYTHON_BASIC_REPL=1 python3 -q
  gdb:    gdb --quiet
  node:   node
  psql:   psql
  bash:   bash --norc

Output (JSON):
{
  "socket": "/tmp/claude-tmux-sockets/claude.sock",
  "session": "claude-python",
  "target": "claude-python:0.0",
  "pid": 12345,
  "command": "PYTHON_BASIC_REPL=1 python3 -q"
}

Output (shell):
SOCKET=/tmp/claude-tmux-sockets/claude.sock
SESSION=claude-python
TARGET=claude-python:0.0
PID=12345
```

**Use Cases:**
- Quick Python session: `create-session.sh --name py1 --preset python`
- Custom session: `create-session.sh --name test --command "python app.py"`
- gdb session: `create-session.sh --name debug --preset gdb`
- Get session vars: `eval $(create-session.sh --name s1 --preset python --format shell)`

**Codex Insights:**
> "after new-session/split-window/send-keys, wait for readiness; ensure commands are sent only after pane is created and not dead"

**Implementation Notes:**
- Create socket dir if missing
- Wait for pane to be ready after creation (use sleep or poll)
- Validate preset names, error on unknown
- Return structured output for easy parsing
- Handle existing session names (error or reuse)
- Store metadata (PID, socket, command) for later reference

**Dependencies:**
- bash, tmux

**Estimated Effort:** Medium (120-150 lines)

---

### Medium Priority

Nice-to-have convenience tools.

---

#### 6. send-and-wait.sh

**Priority:** 🟢 Medium
**Rationale:** Convenience wrapper, combines common pattern

**Purpose:**
Single operation to send command and wait for completion (combines safe-send + wait-for-text).

**Functionality:**
- Send command using safe-send.sh
- Wait for pattern using wait-for-text.sh
- Return captured output
- Atomic operation

**Interface:**
```bash
./tools/send-and-wait.sh -S "$SOCKET" -t "$SESSION":0.0 -c "command" -p "pattern" [options]

Options:
  -S, --socket      Socket path
  -t, --target      Target pane
  -c, --command     Command to send
  -p, --pattern     Pattern to wait for
  -T, --timeout     Timeout (default: 30s)
  --capture         Capture output between send and pattern match
  --format FORMAT   Output format (if --capture)

Exit code: 0 if pattern found, 1 if timeout
```

**Use Cases:**
- Python expression: `send-and-wait.sh -c "2+2" -p ">>>" --capture`
- gdb command: `send-and-wait.sh -c "info locals" -p "(gdb)"`

**Implementation Notes:**
- Wrapper around safe-send.sh and wait-for-text.sh
- If --capture: save output between send and pattern
- Simple pass-through to underlying tools

**Dependencies:**
- safe-send.sh, wait-for-text.sh

**Estimated Effort:** Small (50-70 lines)

---

#### 7. monitor-pane.sh

**Priority:** 🟢 Medium
**Rationale:** Debugging aid, not essential for core functionality

**Purpose:**
Continuously stream pane output to file or stdout for monitoring.

**Functionality:**
- Continuous capture of pane output (polling or pipe-pane)
- Write to file or stdout
- Stop on pattern match or signal
- Timestamp each line
- Follow mode (like tail -f)

**Interface:**
```bash
./tools/monitor-pane.sh -S "$SOCKET" -t "$SESSION":0.0 [options]

Options:
  -S, --socket      Socket path
  -t, --target      Target pane
  -o, --output FILE Write to file (default: stdout)
  -s, --stop PATTERN Stop when pattern matches
  --timestamp       Prefix each line with timestamp
  -i, --interval    Poll interval (default: 0.5s)

Usage:
  # Monitor to stdout
  monitor-pane.sh -S "$SOCKET" -t session:0.0

  # Monitor to file with timestamps
  monitor-pane.sh -S "$SOCKET" -t session:0.0 -o log.txt --timestamp &

  # Monitor until "Done"
  monitor-pane.sh -S "$SOCKET" -t session:0.0 -s "^Done"
```

**Use Cases:**
- Debug long-running process
- Log test output
- Real-time monitoring during development
- Capture unexpected crashes

**Implementation Notes:**
- Use polling (capture-pane in loop) or pipe-pane
- Track last captured line to avoid duplicates
- Handle pane death gracefully
- Clean up on exit (remove pipe if used)

**Dependencies:**
- bash, tmux

**Estimated Effort:** Medium (100-130 lines)

---

## Implementation Considerations

### Common Patterns

All tools should follow these patterns for consistency:

**1. Parameter Consistency:**
- `-S/--socket` for socket path
- `-t/--target` for pane target
- `-T/--timeout` for timeout values
- `-v/--verbose` for verbose output
- `-h/--help` for usage info

**2. Exit Code Convention:**
- `0` - Success
- `1` - General error/failure
- `2` - Not found (pane/session missing)
- `3` - Timeout
- `4` - Invalid arguments

**3. Output Handling:**
- Errors/warnings to stderr
- Data/results to stdout
- Support `--quiet` mode where appropriate
- JSON output option for structured data

**4. Error Handling:**
- Validate inputs early
- Fail fast on invalid parameters
- Provide helpful error messages
- Log errors with context
- Support verbose mode for debugging

**5. Documentation:**
- Comprehensive header comments
- Usage function with examples
- Inline comments for complex logic
- Follow wait-for-text.sh comment style

### Script Structure Template

```bash
#!/usr/bin/env bash
#
# tool-name.sh - Brief description
#
# PURPOSE: ...
# USE CASES: ...
# EXAMPLES: ...
# DEPENDENCIES: ...

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: tool-name.sh [options]
...
USAGE
}

# Default configuration
param1=""
param2="default"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -S|--socket) socket="${2-}"; shift 2 ;;
    -t|--target) target="${2-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

# Validate required parameters
[[ -z "$socket" ]] && { echo "Error: socket required" >&2; exit 1; }

# Main logic
# ...

exit 0
```

### Testing Strategy

**Unit Testing:**
- Each tool should have a test script
- Test success cases
- Test error cases (missing pane, dead pane, etc.)
- Test timeout scenarios
- Test edge cases (special characters, long output, etc.)

**Integration Testing:**
- Test tool combinations (safe-send + wait-for-text)
- Test with real Python REPL
- Test with gdb
- Test cleanup scenarios

**Test Environment:**
- Use isolated sockets for testing
- Clean up after each test
- Use fixtures for common scenarios
- Document test requirements

### Performance Considerations

**1. Minimize tmux calls:**
- Batch operations where possible
- Cache results when appropriate
- Use efficient tmux format strings

**2. Avoid busy-waiting:**
- Use appropriate poll intervals (default: 0.5s)
- Implement backoff for retries
- Timeout protection for all loops

**3. Handle large outputs:**
- Limit capture size (default: 1000 lines)
- Truncate if necessary
- Stream instead of buffering when possible

### Security Considerations

**1. Input validation:**
- Sanitize socket paths
- Validate session/target names
- Escape special characters

**2. Safe defaults:**
- Dry-run mode for destructive operations
- Require explicit --execute flag
- Confirm before killing multiple sessions

**3. Resource limits:**
- Timeout protection
- Maximum retries
- Output size limits

---

## Next Steps

### Phase 1: Critical Tools (Week 1-2)

**1. Implement pane-health.sh**
- ✓ Essential for all other tools
- Start with basic functionality
- Add structured output
- Write tests

**2. Implement safe-send.sh**
- Depends on pane-health.sh
- Start with basic retry logic
- Add prompt waiting
- Integrate with wait-for-text.sh

**3. Implement cleanup-sessions.sh**
- Can be developed in parallel
- Start with basic age-based cleanup
- Add idle detection
- Add pattern matching

### Phase 2: High Priority Tools (Week 3)

**4. Implement capture-clean.sh**
- ANSI stripping first
- Add formatting options
- Add JSON output

**5. Implement create-session.sh**
- Python preset first (most common)
- Add other presets
- Add custom command support

### Phase 3: Medium Priority Tools (Week 4+)

**6. Implement send-and-wait.sh** (if needed)
- Evaluate if still useful after safe-send.sh
- May be redundant

**7. Implement monitor-pane.sh** (optional)
- Only if debugging needs arise

### Documentation Updates

After each tool:
- Update SKILL.md with tool documentation
- Add examples to SKILL.md
- Update notes/tmux/README.md with learnings
- Create notes/tmux/implementation-notes.md if needed

### Version Bumping

- Tools 1-3: Minor version bump (1.0.1 → 1.1.0) - new features
- Tools 4-5: Minor version bump (1.1.0 → 1.2.0) - new features
- Tools 6-7: Patch or minor depending on scope

---

## References

### Codex Consultation

**Query 1: Tool Suggestions**
- Asked for helper script ideas for tmux automation
- Received suggestions for safe-send.sh, capture-span.sh, expect-prompt.sh, pane-health.sh, session-clean.sh

**Query 2: Failure Modes**
- Asked about common failure modes and error scenarios
- Received detailed analysis of lifecycle, timing, process state, output capture, and cleanup issues

### Related Documentation

- [SKILL.md](../../plugins/tmux/SKILL.md) - Main skill documentation
- [wait-for-text.sh](../../plugins/tmux/tools/wait-for-text.sh) - Existing pattern waiting tool
- [find-sessions.sh](../../plugins/tmux/tools/find-sessions.sh) - Existing session discovery tool
- [notes/tmux/README.md](./README.md) - Overview of tmux skill notes

### External Resources

- tmux manual: `man tmux`
- tmux format strings: `man tmux` (FORMATS section)
- ANSI escape codes: https://en.wikipedia.org/wiki/ANSI_escape_code

---

## Changelog

**2025-11-23:** Initial analysis and recommendations
- Reviewed current skill state
- Consulted Codex for suggestions
- Identified 7 potential tools
- Prioritized into Critical/High/Medium
- Documented implementation considerations
