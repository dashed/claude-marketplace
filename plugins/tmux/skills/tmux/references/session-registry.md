# Session Registry Reference

This document provides comprehensive documentation for the tmux skill session registry system.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Registry File Format](#registry-file-format)
4. [Tool Reference](#tool-reference)
5. [Session Resolution](#session-resolution)
6. [Troubleshooting](#troubleshooting)
7. [Migration Guide](#migration-guide)
8. [Best Practices](#best-practices)
9. [Advanced Patterns](#advanced-patterns)

---

## Overview

The session registry is an automatic session tracking system that eliminates ~80% of boilerplate when working with tmux sessions. Instead of repeatedly specifying socket paths and targets, sessions are registered once and can be referenced by name.

### Key Benefits

- **Reduced boilerplate**: No more repeating `-S socket -t target` on every command
- **Automatic discovery**: Tools auto-detect single sessions when no name specified
- **Health tracking**: Built-in integration with pane health checks
- **Activity tracking**: Automatic timestamps for cleanup decisions
- **Backward compatible**: All existing workflows continue to work

### Quick Example

**Before (manual approach):**
```bash
SOCKET="/tmp/claude-tmux-sockets/claude.sock"
SESSION="my-python"
tmux -S "$SOCKET" new -d -s "$SESSION" -n shell
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 'PYTHON_BASIC_REPL=1 python3 -q' Enter
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 'print("hello")' Enter
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 'print("world")' Enter
```

**After (registry approach):**
```bash
./tools/create-session.sh -n my-python --python
./tools/safe-send.sh -s my-python -c 'print("hello")' -w ">>>"
./tools/safe-send.sh -c 'print("world")' -w ">>>"  # Auto-detects single session
```

---

## Architecture

### Components

The session registry consists of:

1. **Registry Library** (`tools/lib/registry.sh`)
   - Core CRUD operations
   - Portable file locking
   - JSON validation
   - Activity tracking

2. **Registry File** (`$CLAUDE_TMUX_SOCKET_DIR/.sessions.json`)
   - JSON database of registered sessions
   - Atomic updates with write-then-move
   - Human-readable format

3. **Management Tools**
   - `create-session.sh` - Create and register sessions
   - `list-sessions.sh` - View all sessions with health status
   - `cleanup-sessions.sh` - Remove dead/old sessions

4. **Enhanced Tools**
   - `safe-send.sh` - Send commands by session name
   - `wait-for-text.sh` - Wait for patterns by session name *(planned)*
   - `pane-health.sh` - Check health by session name *(planned)*

### File Locking Mechanism

The registry uses portable locking to ensure atomic operations:

**On Linux (flock available):**
- Uses kernel-level `flock` for fast, reliable locking
- Lock file: `$CLAUDE_TMUX_SOCKET_DIR/.sessions.lock`
- Timeout: 5 seconds (configurable via `LOCK_TIMEOUT`)

**On macOS (flock not available):**
- Falls back to mkdir-based locking (atomic directory creation)
- Lock directory: `$CLAUDE_TMUX_SOCKET_DIR/.sessions.lock/`
- Contains owner info for debugging
- Same timeout behavior as flock

**Lock acquisition:**
```bash
# Try to acquire lock with timeout
registry_lock || return 75  # Exit code 75 = lock timeout

# ... perform registry operations ...

# Always release lock
registry_unlock
```

### Atomic Updates

All registry modifications use an atomic write-then-move pattern:

1. **Lock** - Acquire registry lock
2. **Read** - Load current registry data
3. **Modify** - Make changes to in-memory copy
4. **Write** - Write to temporary file
5. **Validate** - Verify JSON with `jq`
6. **Move** - Atomically move temp file to registry (if valid)
7. **Unlock** - Release registry lock

This ensures the registry is never corrupted, even if a process crashes mid-update.

---

## Registry File Format

### Location

The registry file is located at:
```bash
$CLAUDE_TMUX_SOCKET_DIR/.sessions.json
```

Where `CLAUDE_TMUX_SOCKET_DIR` defaults to:
```bash
${TMPDIR:-/tmp}/claude-tmux-sockets
```

### JSON Schema

The registry is a JSON file with the following structure:

```json
{
  "sessions": {
    "session-name": {
      "socket": "/path/to/socket",
      "target": "session:window.pane",
      "type": "python-repl|debugger|shell",
      "pid": 12345,
      "created_at": "2025-11-23T10:30:00Z",
      "last_active": "2025-11-23T12:45:00Z"
    }
  }
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `socket` | string | Absolute path to tmux socket file |
| `target` | string | Tmux target in format `session:window.pane` |
| `type` | string | Session type: `python-repl`, `debugger`, `shell` |
| `pid` | number | Process ID of the pane (if available) |
| `created_at` | string | ISO8601 timestamp of session creation |
| `last_active` | string | ISO8601 timestamp of last use |

### Example Registry File

```json
{
  "sessions": {
    "claude-python": {
      "socket": "/tmp/claude-tmux-sockets/claude.sock",
      "target": "claude-python:0.0",
      "type": "python-repl",
      "pid": 45678,
      "created_at": "2025-11-23T10:00:00Z",
      "last_active": "2025-11-23T15:30:00Z"
    },
    "debug-api": {
      "socket": "/tmp/claude-tmux-sockets/claude.sock",
      "target": "debug-api:0.0",
      "type": "debugger",
      "pid": 45789,
      "created_at": "2025-11-23T11:00:00Z",
      "last_active": "2025-11-23T14:20:00Z"
    }
  }
}
```

---

## Tool Reference

### create-session.sh

Create and register new tmux sessions with automatic registry integration.

#### Usage

```bash
./tools/create-session.sh -n <name> [options]
```

#### Options

| Flag | Description |
|------|-------------|
| `-n, --name <name>` | Session name (required) |
| `-S, --socket <path>` | Custom socket path (optional, uses default) |
| `-w, --window <name>` | Window name (default: "shell") |
| `--python` | Launch Python REPL with `PYTHON_BASIC_REPL=1` |
| `--gdb` | Launch gdb debugger |
| `--shell` | Launch bash shell (default) |
| `--no-register` | Don't add to registry |
| `-h, --help` | Show help message |

#### Session Types

**`--shell` (default)**
- Launches bash shell
- General-purpose interactive environment
- Type recorded as: `shell`

**`--python`**
- Launches Python REPL with `PYTHON_BASIC_REPL=1` set
- Critical for compatibility with tmux send-keys
- Disables fancy prompt/highlighting that interferes with automation
- Type recorded as: `python-repl`

**`--gdb`**
- Launches gdb debugger
- Automatically sets `set pagination off` recommended
- Type recorded as: `debugger`

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid arguments |
| 2 | Session already exists |
| 3 | Tmux command failed |
| 4 | Registry operation failed |

#### JSON Output

Returns session information as JSON:

```json
{
  "name": "my-python",
  "socket": "/tmp/claude-tmux-sockets/claude.sock",
  "target": "my-python:0.0",
  "type": "python-repl",
  "pid": 12345,
  "window": "shell",
  "registered": true
}
```

#### Examples

**Create Python REPL session:**
```bash
./tools/create-session.sh -n claude-python --python
```

**Create gdb session:**
```bash
./tools/create-session.sh -n debug-app --gdb
```

**Create session with custom socket:**
```bash
./tools/create-session.sh -n isolated-session -S /tmp/custom.sock --shell
```

**Create without registering (one-off session):**
```bash
./tools/create-session.sh -n temp-work --shell --no-register
```

**Create with custom window name:**
```bash
./tools/create-session.sh -n data-analysis -w "jupyter" --python
```

#### When to Use

- **With registration (default)**: Interactive development, debugging, exploration
- **Without registration (`--no-register`)**: Temporary sessions, scripts that manage cleanup, CI/CD

---

### list-sessions.sh

List all registered sessions with health status information.

#### Usage

```bash
./tools/list-sessions.sh [--json]
```

#### Options

| Flag | Description |
|------|-------------|
| `--json` | Output as JSON instead of table format |
| `-h, --help` | Show help message |

#### Output Formats

**Table format (default):**
```
NAME            SOCKET          TARGET          STATUS    PID    CREATED
claude-python   claude.sock     :0.0            alive     1234   2h ago
debug-api       claude.sock     :0.0            dead      -      1h ago

Total: 2 | Alive: 1 | Dead: 1
```

**JSON format (`--json`):**
```json
{
  "sessions": [
    {
      "name": "claude-python",
      "socket": "/tmp/claude-tmux-sockets/claude.sock",
      "socket_basename": "claude.sock",
      "target": "claude-python:0.0",
      "type": "python-repl",
      "status": "alive",
      "pid": 1234,
      "created_at": "2025-11-23T10:00:00Z"
    }
  ],
  "total": 2,
  "alive": 1,
  "dead": 1
}
```

#### Health Statuses

| Status | Meaning | Exit Code from pane-health.sh |
|--------|---------|-------------------------------|
| `alive` | Session is running and healthy | 0 |
| `dead` | Pane is marked as dead | 1 |
| `missing` | Session/pane not found in tmux | 2 |
| `zombie` | Process exited but pane exists | 3 |
| `server` | Tmux server not running | 4 |
| `unknown` | pane-health.sh not available | - |

#### Examples

**List sessions in table format:**
```bash
./tools/list-sessions.sh
```

**List sessions as JSON for scripting:**
```bash
./tools/list-sessions.sh --json | jq '.sessions[] | select(.status == "alive")'
```

**Count alive sessions:**
```bash
./tools/list-sessions.sh --json | jq '.alive'
```

**Get all Python sessions:**
```bash
./tools/list-sessions.sh --json | jq '.sessions[] | select(.type == "python-repl")'
```

#### When to Use

- Check what sessions are currently registered
- Verify session health before operations
- Monitor session activity and age
- Identify dead sessions before cleanup
- Generate reports or dashboards

---

### cleanup-sessions.sh

Remove dead or old sessions from the registry.

#### Usage

```bash
./tools/cleanup-sessions.sh [options]
```

#### Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would be cleaned without removing |
| `--all` | Remove all sessions (even alive ones) |
| `--older-than <duration>` | Remove sessions older than threshold |
| `-h, --help` | Show help message |

#### Duration Format

Supported units: `s` (seconds), `m` (minutes), `h` (hours), `d` (days)

Examples:
- `30m` - 30 minutes
- `2h` - 2 hours
- `1d` - 1 day
- `3600s` - 3600 seconds (1 hour)

#### Cleanup Modes

**Default mode (no flags):**
- Removes only dead/missing/zombie sessions
- Safest option
- Preserves all healthy sessions

**Age-based mode (`--older-than`):**
- Removes sessions older than specified duration
- Based on `created_at` timestamp
- Can combine with default mode (dead OR old)

**All mode (`--all`):**
- Removes all sessions regardless of health
- Use with caution
- Good for "clean slate" scenarios

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid arguments |

#### Examples

**Remove dead sessions (safe default):**
```bash
./tools/cleanup-sessions.sh
```

**Dry-run to preview cleanup:**
```bash
./tools/cleanup-sessions.sh --dry-run
```

**Remove sessions inactive for more than 1 hour:**
```bash
./tools/cleanup-sessions.sh --older-than 1h
```

**Remove sessions older than 2 days:**
```bash
./tools/cleanup-sessions.sh --older-than 2d
```

**Remove all sessions (clean slate):**
```bash
./tools/cleanup-sessions.sh --all
```

**Combine dry-run with age filter:**
```bash
./tools/cleanup-sessions.sh --dry-run --older-than 1d
```

#### When to Use

- **Manual cleanup**: After finishing work with sessions
- **Periodic cleanup**: Cron job to remove old sessions
- **Aggressive cleanup**: Before starting new work session
- **Debugging**: Dry-run to see what's stale

#### Automation Examples

**Daily cleanup via cron:**
```bash
# Remove sessions older than 1 day, runs daily at 3am
0 3 * * * cd /path/to/tmux/tools && ./cleanup-sessions.sh --older-than 1d
```

**Pre-work cleanup script:**
```bash
#!/bin/bash
# Clean slate before starting work
./tools/cleanup-sessions.sh --all
./tools/create-session.sh -n work-python --python
./tools/create-session.sh -n work-gdb --gdb
```

---

### safe-send.sh (Session Registry Features)

The `safe-send.sh` tool has been enhanced with session registry support.

#### Session Resolution Options

**Three ways to specify the target:**

1. **Session name** (`-s`): Look up socket/target from registry
2. **Explicit** (`-S` + `-t`): Specify socket and target directly (backward compatible)
3. **Auto-detect**: Omit all flags, auto-detect single session

#### Priority Order

When multiple options are provided, they are resolved in this order:

1. **Explicit flags** (`-S` and `-t`): Highest priority, backward compatible
2. **Session name** (`-s`): Look up in registry
3. **Auto-detect**: If no flags provided and exactly one session exists

#### New Flags

| Flag | Description |
|------|-------------|
| `-s, --session <name>` | Session name (looks up socket/target in registry) |

All other flags remain the same (see SKILL.md for full reference).

#### Examples

**Using session name:**
```bash
./tools/safe-send.sh -s claude-python -c "print('hello')" -w ">>>"
```

**Auto-detect single session:**
```bash
./tools/safe-send.sh -c "print('world')" -w ">>>"
```

**Explicit (backward compatible):**
```bash
SOCKET="/tmp/claude-tmux-sockets/claude.sock"
./tools/safe-send.sh -S "$SOCKET" -t "my-session:0.0" -c "ls"
```

#### Activity Tracking

When using `-s` flag or auto-detect, the session's `last_active` timestamp is automatically updated. This helps cleanup-sessions.sh make better decisions about session age.

#### Error Messages

**Session not found:**
```
Error: Session 'my-session' not found in registry
Use 'list-sessions.sh' to see available sessions
```

**Multiple sessions (auto-detect fails):**
```
Error: Multiple sessions found (3 total)
Please specify session name with -s or use -t/-S explicitly
Use 'list-sessions.sh' to see available sessions
```

**No sessions registered:**
```
Error: No sessions found in registry
Create a session with 'create-session.sh' or specify -t and -S explicitly
```

---

## Session Resolution

### Resolution Algorithm

The session resolution logic determines which tmux session and socket to use:

```
if (socket AND target specified):
    use explicit values (backward compatible)
elif (session name specified with -s):
    lookup in registry
    if not found:
        error: session not found
    else:
        extract socket and target
        update last_active timestamp
elif (no flags provided):
    count sessions in registry
    if count == 1:
        auto-use the single session
        update last_active timestamp
    elif count == 0:
        error: no sessions
    else:
        error: multiple sessions, specify -s
```

### Decision Tree

```
┌─────────────────────────────┐
│  Parse command-line flags   │
└──────────┬──────────────────┘
           │
           ▼
    ┌──────────────┐
    │ -S and -t ?  │──Yes──► Use explicit socket/target
    └──────┬───────┘         (backward compatible)
           │
          No
           │
           ▼
    ┌──────────────┐
    │  -s flag ?   │──Yes──► Look up session in registry
    └──────┬───────┘         Update last_active
           │                 Error if not found
          No
           │
           ▼
    ┌──────────────────┐
    │ Count sessions   │
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────┐
    │  count == 1 ?    │──Yes──► Auto-use single session
    └──────┬───────────┘         Update last_active
           │
          No
           │
           ▼
    ┌──────────────────┐
    │  count == 0 ?    │──Yes──► Error: No sessions
    └──────┬───────────┘
           │
          No (multiple)
           │
           ▼
    Error: Multiple sessions,
    specify -s or -t/-S
```

### Examples

**Scenario 1: Single session exists**
```bash
# Create one session
./tools/create-session.sh -n my-python --python

# These all work the same way:
./tools/safe-send.sh -s my-python -c "print(1)"  # Explicit name
./tools/safe-send.sh -c "print(1)"               # Auto-detect
```

**Scenario 2: Multiple sessions exist**
```bash
# Create multiple sessions
./tools/create-session.sh -n python-1 --python
./tools/create-session.sh -n python-2 --python

# Must specify which one:
./tools/safe-send.sh -s python-1 -c "print(1)"  # ✓ Works
./tools/safe-send.sh -c "print(1)"              # ✗ Error: multiple sessions
```

**Scenario 3: Backward compatibility**
```bash
# Old-style explicit socket/target still works:
SOCKET="/tmp/claude-tmux-sockets/claude.sock"
./tools/safe-send.sh -S "$SOCKET" -t "my-session:0.0" -c "ls"  # ✓ Always works
```

---

## Troubleshooting

### Common Errors

#### Error: Session not found in registry

**Message:**
```
Error: Session 'my-session' not found in registry
Use 'list-sessions.sh' to see available sessions
```

**Causes:**
- Session was never created
- Session was removed from registry
- Typo in session name

**Solutions:**
```bash
# List all registered sessions
./tools/list-sessions.sh

# Create the session if it doesn't exist
./tools/create-session.sh -n my-session --python

# Check for typos in session name (case-sensitive)
```

---

#### Error: Failed to acquire lock

**Message:**
```
registry: Failed to acquire lock after 5s
```

**Causes:**
- Another process is performing a registry operation
- Previous lock wasn't released (crash/kill)
- Very slow filesystem (rare)

**Solutions:**

**1. Wait and retry** (usually self-resolves):
```bash
# Wait a few seconds and try again
sleep 2
./tools/safe-send.sh -s my-session -c "command"
```

**2. Check for stuck lock:**
```bash
# Check if lock exists
ls -la "$CLAUDE_TMUX_SOCKET_DIR/.sessions.lock"*

# If flock-based (file):
ls -la "$CLAUDE_TMUX_SOCKET_DIR/.sessions.lock"

# If mkdir-based (directory):
ls -la "$CLAUDE_TMUX_SOCKET_DIR/.sessions.lock/"
cat "$CLAUDE_TMUX_SOCKET_DIR/.sessions.lock/owner"  # See who owns it
```

**3. Manual lock removal** (last resort):
```bash
# Remove stuck lock (use with caution!)
rm -rf "$CLAUDE_TMUX_SOCKET_DIR/.sessions.lock"

# Then retry your operation
```

**Prevention:**
- Don't kill registry operations with `kill -9`
- Let operations complete normally
- Increase `LOCK_TIMEOUT` for slow filesystems:
  ```bash
  export LOCK_TIMEOUT=10  # Increase to 10 seconds
  ./tools/safe-send.sh -s my-session -c "command"
  ```

---

#### Error: Multiple sessions found

**Message:**
```
Error: Multiple sessions found (3 total)
Please specify session name with -s or use -t/-S explicitly
Use 'list-sessions.sh' to see available sessions
```

**Cause:**
- Auto-detect only works when exactly one session exists
- You have multiple registered sessions

**Solution:**
```bash
# List sessions to see what's registered
./tools/list-sessions.sh

# Specify which session to use
./tools/safe-send.sh -s specific-session -c "command"

# Or clean up unused sessions
./tools/cleanup-sessions.sh
```

---

#### Error: Pane not ready

**Message:**
```
Error: Pane not ready (health check failed with exit code 1)
```

**Causes:**
- Session crashed or was killed
- Pane is marked as dead by tmux
- Process inside pane exited

**Solutions:**

**1. Check session health:**
```bash
./tools/list-sessions.sh
# Look for status: dead, zombie, or missing
```

**2. Check pane directly:**
```bash
./tools/pane-health.sh -s my-session
```

**3. Recreate session:**
```bash
# Remove dead session from registry
./tools/cleanup-sessions.sh

# Create fresh session
./tools/create-session.sh -n my-session --python
```

**4. Debug manually:**
```bash
# Get session details from registry
./tools/list-sessions.sh --json | jq '.sessions["my-session"]'

# Try to attach to see what happened
SOCKET="/tmp/claude-tmux-sockets/claude.sock"
tmux -S "$SOCKET" attach -t my-session
```

---

### Stale Registry Entries

#### What are stale entries?

Stale entries occur when:
- Sessions are in the registry but tmux session is gone
- Tmux server was killed without cleanup
- Registry was manually edited incorrectly

#### How to detect

**Check health status:**
```bash
./tools/list-sessions.sh
# Look for: dead, missing, zombie, server
```

**Check with health tool:**
```bash
./tools/pane-health.sh -s session-name
# Non-zero exit code means unhealthy
```

#### How to fix

**Automatic cleanup (recommended):**
```bash
# Remove all dead/missing/zombie sessions
./tools/cleanup-sessions.sh

# Preview what would be removed
./tools/cleanup-sessions.sh --dry-run
```

**Manual removal:**
```bash
# Remove specific session
cd plugins/tmux/tools
source lib/registry.sh
registry_remove_session "session-name"
```

**Nuclear option (clean slate):**
```bash
# Remove ALL sessions from registry
./tools/cleanup-sessions.sh --all

# Or delete registry file entirely
rm "$CLAUDE_TMUX_SOCKET_DIR/.sessions.json"
```

#### Prevention

**Use cleanup tools regularly:**
```bash
# At end of work session
./tools/cleanup-sessions.sh

# Automated daily cleanup (cron)
0 3 * * * /path/to/tools/cleanup-sessions.sh --older-than 1d
```

**Kill sessions properly:**
```bash
# ✓ Good: Kill session, then cleanup registry
tmux -S "$SOCKET" kill-session -t my-session
./tools/cleanup-sessions.sh

# ✗ Bad: Kill tmux server without cleanup
tmux -S "$SOCKET" kill-server  # Leaves stale registry entries
```

---

### Registry Corruption

#### What is corruption?

Registry corruption occurs when `.sessions.json` contains invalid JSON.

#### How it happens (rare)

- Disk full during write
- Process crash during write (atomic write-then-move prevents this)
- Manual editing with syntax errors
- Filesystem corruption

#### How to detect

**Symptoms:**
- Registry operations fail with jq errors
- Tools report "invalid JSON" errors

**Verify registry:**
```bash
# Check if registry is valid JSON
jq empty "$CLAUDE_TMUX_SOCKET_DIR/.sessions.json"
# Exit code 0 = valid, non-zero = invalid
```

#### How to fix

**1. Backup current registry:**
```bash
cp "$CLAUDE_TMUX_SOCKET_DIR/.sessions.json" \
   "$CLAUDE_TMUX_SOCKET_DIR/.sessions.json.backup"
```

**2. Try to salvage data:**
```bash
# View the file to see what's wrong
cat "$CLAUDE_TMUX_SOCKET_DIR/.sessions.json"

# Try to fix with jq (if minor issue)
jq '.' "$CLAUDE_TMUX_SOCKET_DIR/.sessions.json.backup" > \
  "$CLAUDE_TMUX_SOCKET_DIR/.sessions.json"
```

**3. Rebuild registry (if salvage fails):**
```bash
# Remove corrupted registry
rm "$CLAUDE_TMUX_SOCKET_DIR/.sessions.json"

# Registry will be recreated on next operation
./tools/list-sessions.sh
# Shows: No sessions registered

# Re-register active sessions manually
./tools/create-session.sh -n my-session --python
```

**4. Recover from tmux sessions:**
```bash
# List actual tmux sessions
SOCKET="/tmp/claude-tmux-sockets/claude.sock"
tmux -S "$SOCKET" list-sessions

# Re-register them manually
./tools/create-session.sh -n session-name --shell --no-register
# Note: --no-register prevents duplicate registration check
```

#### Prevention

- **Don't edit `.sessions.json` manually** (use tools instead)
- **Monitor disk space** (atomic writes fail gracefully if disk full)
- **Use the tools** (they validate JSON before writing)
- **Regular backups** (if registry is critical):
  ```bash
  # Backup registry (cron)
  0 * * * * cp "$CLAUDE_TMUX_SOCKET_DIR/.sessions.json" \
    "$HOME/.sessions.json.$(date +%Y%m%d%H)"
  ```

---

## Migration Guide

### From Manual Socket Management

#### Before: Manual Approach

Typical manual workflow with repetitive boilerplate:

```bash
# Setup (every session)
SOCKET_DIR=${TMPDIR:-/tmp}/claude-tmux-sockets
mkdir -p "$SOCKET_DIR"
SOCKET="$SOCKET_DIR/claude.sock"
SESSION="my-python"

# Create session
tmux -S "$SOCKET" new -d -s "$SESSION" -n shell
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 \
  'PYTHON_BASIC_REPL=1 python3 -q' Enter

# Use session (repeat socket/target every time)
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 'print("hello")' Enter
./tools/wait-for-text.sh -S "$SOCKET" -t "$SESSION":0.0 -p '>>>'
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 'import numpy' Enter
./tools/wait-for-text.sh -S "$SOCKET" -t "$SESSION":0.0 -p '>>>'

# Cleanup
tmux -S "$SOCKET" kill-session -t "$SESSION"
```

**Problems:**
- Repetitive `-S "$SOCKET" -t "$SESSION":0.0` on every command
- Must track socket/session variables across script
- No automatic session discovery
- No built-in health tracking

#### After: Registry Approach

Same workflow with ~80% less boilerplate:

```bash
# Create session (auto-registered)
./tools/create-session.sh -n my-python --python

# Use session (auto-detects socket/target)
./tools/safe-send.sh -s my-python -c 'print("hello")' -w '>>>'
./tools/safe-send.sh -c 'import numpy' -w '>>>'  # Auto-detect single session

# Cleanup
./tools/cleanup-sessions.sh
```

**Benefits:**
- No socket/target repetition
- Auto-detection for single sessions
- Built-in health tracking
- Centralized session management

#### Step-by-Step Migration

**1. Install new tools** (already available in `tools/`)
- ✓ `create-session.sh`
- ✓ `list-sessions.sh`
- ✓ `cleanup-sessions.sh`
- ✓ `safe-send.sh` (enhanced)

**2. Start using registry for new sessions:**
```bash
# Instead of:
# tmux -S "$SOCKET" new -d -s my-session -n shell
# Do:
./tools/create-session.sh -n my-session --shell
```

**3. Replace socket/target with session name:**
```bash
# Instead of:
# ./tools/safe-send.sh -S "$SOCKET" -t "$SESSION":0.0 -c "command"
# Do:
./tools/safe-send.sh -s my-session -c "command"
```

**4. Use auto-detect for single sessions:**
```bash
# If only one session exists:
./tools/safe-send.sh -c "command"  # Omit -s entirely
```

**5. Use registry for cleanup:**
```bash
# Instead of:
# tmux -S "$SOCKET" kill-session -t "$SESSION"
# Do:
./tools/cleanup-sessions.sh
```

#### Gradual Migration Strategy

You can use both approaches simultaneously during migration:

**Phase 1: New sessions only**
- Create new sessions with `create-session.sh`
- Keep existing manual sessions as-is
- Learn the registry workflow

**Phase 2: Mixed usage**
- Use registry for new sessions
- Continue manual approach for existing sessions
- Both work side-by-side (backward compatible)

**Phase 3: Full adoption**
- Migrate remaining manual sessions
- Clean up old manual scripts
- Standardize on registry approach

---

## Best Practices

### When to Use Registry vs Manual

#### Use Registry When:

✓ **Interactive development**
- Debugging applications
- Exploring code in REPLs
- Running ad-hoc commands
- Frequent context switching

✓ **Multi-session workflows**
- Managing multiple Python/gdb sessions
- Switching between different projects
- Parallel debugging tasks

✓ **Learning and experimentation**
- Testing new tools
- Prototyping workflows
- Educational contexts

#### Use Manual When:

✓ **Automation scripts**
- CI/CD pipelines
- Deployment scripts
- Automated testing
- Scripts run by other users

✓ **Precise control needed**
- Custom socket paths for isolation
- Multiple sessions with same name on different sockets
- Temporary sessions that shouldn't be tracked

✓ **One-off operations**
- Quick debugging session
- Single command execution
- Script that manages its own cleanup

#### Hybrid Approach:

Use `--no-register` flag for one-off sessions:
```bash
# Create session without registering
./tools/create-session.sh -n temp-debug --gdb --no-register

# Use it manually
SOCKET="/tmp/claude-tmux-sockets/claude.sock"
tmux -S "$SOCKET" send-keys -t temp-debug:0.0 "break main" Enter

# Kill when done
tmux -S "$SOCKET" kill-session -t temp-debug
```

---

### Session Naming Conventions

#### Good Session Names

✓ **Descriptive and specific:**
```bash
claude-python          # Python REPL for Claude agent
debug-api-server       # Debugging API server
test-database-queries  # Testing database operations
dev-frontend           # Frontend development
```

✓ **Use hyphens (not spaces):**
```bash
my-python-session      # ✓ Good
my_python_session      # ✓ OK
my python session      # ✗ Bad (spaces cause issues)
```

✓ **Keep it short:**
```bash
api-debug              # ✓ Good (concise)
debugging-the-new-api  # ✗ Too long
```

✓ **Use prefixes for grouping:**
```bash
# Project-based prefixes
proj-backend-api
proj-frontend-dev
proj-database-debug

# Type-based prefixes
python-data-analysis
python-ml-training
gdb-core-dump
gdb-memory-leak

# Environment prefixes
dev-api-server
test-integration
prod-hotfix-debug
```

#### Avoid These Patterns

✗ **Generic names:**
```bash
session1, session2, test, temp, debug
# Hard to remember what they're for
```

✗ **Special characters:**
```bash
my@session, session#1, session.test
# May cause issues with shell parsing
```

✗ **Very long names:**
```bash
my-very-long-session-name-for-debugging-the-authentication-module
# Tedious to type, hard to remember
```

---

### Cleanup Strategies

#### Manual Cleanup

**After each work session:**
```bash
# Remove dead sessions
./tools/cleanup-sessions.sh

# Or preview first
./tools/cleanup-sessions.sh --dry-run
```

**When switching projects:**
```bash
# Clean slate for new work
./tools/cleanup-sessions.sh --all
```

#### Automated Cleanup

**Daily cleanup via cron:**
```bash
# Remove sessions older than 1 day (runs at 3am)
0 3 * * * cd /path/to/tmux/tools && ./cleanup-sessions.sh --older-than 1d
```

**Weekly cleanup via cron:**
```bash
# Aggressive cleanup once a week (Sunday 2am)
0 2 * * 0 cd /path/to/tmux/tools && ./cleanup-sessions.sh --all
```

**Pre-work cleanup script:**
```bash
#!/bin/bash
# ~/bin/start-work.sh

# Clean up old sessions
cd ~/tmux-skill/tools
./cleanup-sessions.sh --older-than 12h

# Create fresh sessions for today
./create-session.sh -n work-python --python
./create-session.sh -n work-gdb --gdb

echo "Work environment ready!"
./list-sessions.sh
```

#### Conditional Cleanup

**In shell scripts:**
```bash
# Cleanup only if more than N sessions exist
session_count=$(./tools/list-sessions.sh --json | jq '.total')
if [[ $session_count -gt 5 ]]; then
  echo "Too many sessions ($session_count), cleaning up..."
  ./tools/cleanup-sessions.sh --older-than 2h
fi
```

**Cleanup based on disk usage:**
```bash
# Cleanup if disk usage high (rare scenario)
disk_usage=$(df /tmp | tail -1 | awk '{print $5}' | sed 's/%//')
if [[ $disk_usage -gt 90 ]]; then
  echo "Disk usage high, cleaning up sessions..."
  ./tools/cleanup-sessions.sh --all
fi
```

#### Best Practices

✓ **Preview first** (dry-run before aggressive cleanup):
```bash
./tools/cleanup-sessions.sh --dry-run --all
```

✓ **Keep recent sessions** (use time-based cleanup):
```bash
./tools/cleanup-sessions.sh --older-than 1d  # Keep today's work
```

✓ **Document your strategy:**
```bash
# Add comment in crontab
# Cleanup old tmux sessions daily at 3am
0 3 * * * /path/to/cleanup-sessions.sh --older-than 1d
```

✗ **Don't cleanup aggressively during active work:**
```bash
# Bad: Cron job every hour during work hours
0 9-17 * * * cleanup-sessions.sh --all  # ✗ Will kill active sessions
```

---

## Advanced Patterns

### Multiple Sessions on Same Socket

You can have multiple registered sessions sharing a single socket file:

```bash
# All use default socket: /tmp/claude-tmux-sockets/claude.sock
./tools/create-session.sh -n python-1 --python
./tools/create-session.sh -n python-2 --python
./tools/create-session.sh -n gdb-debug --gdb

# Each session has unique target (session:window.pane)
# python-1 → python-1:0.0
# python-2 → python-2:0.0
# gdb-debug → gdb-debug:0.0

# Use sessions independently
./tools/safe-send.sh -s python-1 -c "print(1)"
./tools/safe-send.sh -s python-2 -c "print(2)"
./tools/safe-send.sh -s gdb-debug -c "break main"

# List all sessions on default socket
SOCKET="/tmp/claude-tmux-sockets/claude.sock"
tmux -S "$SOCKET" list-sessions
```

**Benefits:**
- Easier session discovery (all on one socket)
- Simplified cleanup (kill-server removes all)
- Lower resource usage (one tmux server)

**When to use:**
- Multiple debugging contexts in one project
- Parallel Python REPLs for different experiments
- Related sessions that should be grouped together

---

### Custom Socket Paths for Isolation

Use custom sockets to isolate sessions by project or environment:

```bash
# Project A sessions
./tools/create-session.sh -n proj-a-python \
  -S /tmp/project-a.sock --python
./tools/create-session.sh -n proj-a-gdb \
  -S /tmp/project-a.sock --gdb

# Project B sessions
./tools/create-session.sh -n proj-b-python \
  -S /tmp/project-b.sock --python

# Sessions are isolated by socket
./tools/list-sessions.sh
# Shows all sessions across all sockets

# Can still use session names
./tools/safe-send.sh -s proj-a-python -c "print('Project A')"
./tools/safe-send.sh -s proj-b-python -c "print('Project B')"
```

**Benefits:**
- Clean separation between projects
- Can kill entire project's sessions: `tmux -S /tmp/project-a.sock kill-server`
- Prevents naming conflicts across projects
- Easier project-based cleanup

**When to use:**
- Multiple long-running projects
- Client work requiring isolation
- Different tmux configurations per project

---

### CI/CD Integration

Use registry for debugging but not for automated pipelines:

#### Option 1: Don't Register CI Sessions

```bash
#!/bin/bash
# ci-test.sh - CI/CD test script

# Create unregistered session
./tools/create-session.sh -n ci-test-$$  \
  --shell --no-register

# Use explicit socket/target (bypass registry)
SOCKET="/tmp/claude-tmux-sockets/claude.sock"
TARGET="ci-test-$$:0.0"

# Run tests
./tools/safe-send.sh -S "$SOCKET" -t "$TARGET" \
  -c "pytest tests/" -w "passed"

# Cleanup (explicit kill, no registry)
tmux -S "$SOCKET" kill-session -t "ci-test-$$"
```

**Why:**
- CI sessions are ephemeral
- No need to track them in registry
- Explicit socket/target gives full control

#### Option 2: Use Registry with Auto-Cleanup

```bash
#!/bin/bash
# ci-test-with-registry.sh

# Create registered session
./tools/create-session.sh -n ci-test-$$ --python

# Use session name
./tools/safe-send.sh -s ci-test-$$ \
  -c "import pytest; pytest.main(['tests/'])" -w "passed"

# Cleanup via registry
./tools/cleanup-sessions.sh
```

**Why:**
- Easier debugging (can inspect sessions)
- Automatic cleanup with registry tools
- Good for hybrid local/CI workflows

#### Best Practice for CI

Use environment variable to decide:

```bash
#!/bin/bash
# Smart CI/local script

if [[ -n "$CI" ]]; then
  # CI: Use explicit approach, no registry
  SESSION="ci-test-$$"
  ./tools/create-session.sh -n "$SESSION" --python --no-register
  SOCKET="/tmp/claude-tmux-sockets/claude.sock"
  ./tools/safe-send.sh -S "$SOCKET" -t "$SESSION:0.0" -c "pytest"
  tmux -S "$SOCKET" kill-session -t "$SESSION"
else
  # Local: Use registry for convenience
  ./tools/create-session.sh -n local-test --python
  ./tools/safe-send.sh -s local-test -c "pytest"
  # Manual cleanup when done
fi
```

---

## See Also

- SKILL.md - Quick reference and common usage (in plugin root)
- [tmux man page](https://man.openbsd.org/tmux.1) - Official tmux documentation
- `notes/tmux/session-registry-implementation.md` - Development status and roadmap (in marketplace root)
