# Session Lifecycle Guide

> Practical guide for managing tmux sessions through their complete lifecycle - from creation to cleanup

## Overview

Tmux sessions managed by this skill follow a predictable lifecycle. Understanding these stages helps you make better decisions about when to create, reuse, or clean up sessions. This guide provides real-world workflows and decision trees for daily use.

**When to use this guide:**
- You're unsure whether to create a new session or reuse an existing one
- You need to debug a crashed or stuck session
- You want to understand proper cleanup workflows
- You're managing multiple parallel sessions

## Lifecycle Stages

```
┌─────────────┐
│ PRE-CHECK   │  Check existing sessions
│ (optional)  │  Tool: list-sessions.sh
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ CREATE      │  Spawn new tmux session
│             │  Tool: create-session.sh
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ INIT        │  Wait for startup (prompt appears)
│             │  Tool: wait-for-text.sh
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ ACTIVE USE  │  Send commands, capture output
│             │  Tools: safe-send.sh, wait-for-text.sh
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ IDLE        │  Session exists but unused
│             │  Tool: list-sessions.sh (check status)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ CLEANUP     │  Remove dead/stale sessions
│             │  Tools: cleanup-sessions.sh, tmux kill-session
└─────────────┘
```

**Error recovery:**
- If session crashes → Check with `pane-health.sh`
- If session becomes zombie → Remove with `cleanup-sessions.sh`
- If network interruption → Reconnect using `tmux attach` or resume with session name

## Common Workflows

### 1. Quick Python Calculation (Ephemeral Session)

**Use case:** Run a one-off calculation, get the result, and cleanup immediately.

**Duration:** < 5 minutes

**Commands:**
```bash
# 1. Check no conflicts
./tools/list-sessions.sh

# 2. Create session
./tools/create-session.sh -n quick-calc --python

# 3. Send calculation
./tools/safe-send.sh -s quick-calc -c "import math; print(math.factorial(100))" -w ">>>" -T 10

# 4. Capture output
SOCKET=$(jq -r '.sessions["quick-calc"].socket' ~/.local/state/claude-tmux/.sessions.json)
tmux -S "$SOCKET" capture-pane -p -t quick-calc:0.0 -S -10

# 5. Cleanup immediately
tmux -S "$SOCKET" kill-session -t quick-calc
./tools/cleanup-sessions.sh
```

**When to use:** One-time calculations, quick tests, disposable experiments.

### 2. Long-Running Analysis (Persistent Session)

**Use case:** Hours or days of interactive REPL work with state preservation.

**Duration:** Hours to days

**Commands:**
```bash
# 1. Check existing sessions first
./tools/list-sessions.sh

# 2. Create persistent session with descriptive name
./tools/create-session.sh -n data-analysis-2025-11 --python

# 3. Load data (may take time)
./tools/safe-send.sh -s data-analysis-2025-11 -c "import pandas as pd" -w ">>>"
./tools/safe-send.sh -s data-analysis-2025-11 -c "df = pd.read_csv('large_dataset.csv')" -w ">>>" -T 300

# 4. Work interactively over time
./tools/safe-send.sh -s data-analysis-2025-11 -c "df.describe()" -w ">>>"
# ... hours later ...
./tools/safe-send.sh -s data-analysis-2025-11 -c "df.groupby('category').mean()" -w ">>>"

# 5. Check session health periodically
./tools/pane-health.sh -s data-analysis-2025-11

# 6. Cleanup only when done (days later)
./tools/list-sessions.sh  # Verify it's the right session
tmux -S "$(jq -r '.sessions["data-analysis-2025-11"].socket' ~/.local/state/claude-tmux/.sessions.json)" kill-session -t data-analysis-2025-11
./tools/cleanup-sessions.sh
```

**When to use:** Long-running analysis, state preservation, multiple work sessions.

**Best practices:**
- Use descriptive names (include date or project name)
- Check health before resuming work
- Don't cleanup until completely done
- Capture important output early

### 3. Recovering from Crashed Session

**Use case:** Session died unexpectedly, need to investigate and restart.

**Duration:** 5-10 minutes

**Commands:**
```bash
# 1. Check session status
./tools/list-sessions.sh
# Output shows: status "dead" or "zombie"

# 2. Diagnose the issue
./tools/pane-health.sh -s crashed-session --format text
# Check exit code: 1=dead, 2=missing, 3=zombie

# 3. Capture any remaining output for debugging
SOCKET=$(jq -r '.sessions["crashed-session"].socket' ~/.local/state/claude-tmux/.sessions.json)
tmux -S "$SOCKET" capture-pane -p -t crashed-session:0.0 -S -200 > crash-output.txt 2>/dev/null || echo "Pane unavailable"

# 4. Remove dead session from registry
./tools/cleanup-sessions.sh  # Removes dead sessions automatically

# 5. Create replacement session
./tools/create-session.sh -n crashed-session-recovery --python

# 6. Resume work with new session
./tools/safe-send.sh -s crashed-session-recovery -c "# Resuming from crash..." -w ">>>"
```

**When to use:** Session crashed, process died, debugging needed.

**Troubleshooting tips:**
- Always capture output before cleanup (may contain error messages)
- Check system logs if crash is mysterious: `dmesg`, `journalctl`
- Verify PYTHON_BASIC_REPL=1 was set (common cause of silent failures)

### 4. Multi-Session Workspace (Parallel Tasks)

**Use case:** Multiple parallel tasks (data loading, analysis, monitoring) in separate sessions.

**Duration:** Variable

**Commands:**
```bash
# 1. Check existing sessions
./tools/list-sessions.sh

# 2. Create multiple sessions with clear names
./tools/create-session.sh -n loader-session --python
./tools/create-session.sh -n analysis-session --python
./tools/create-session.sh -n monitor-session --python

# 3. Start parallel work
# Session 1: Load large dataset
./tools/safe-send.sh -s loader-session -c "import pandas as pd; df = pd.read_csv('huge.csv')" -w ">>>" -T 600 &

# Session 2: Run analysis on existing data
./tools/safe-send.sh -s analysis-session -c "results = analyze_data()" -w ">>>" -T 300 &

# Session 3: Monitor system
./tools/safe-send.sh -s monitor-session -c "import psutil; psutil.cpu_percent()" -w ">>>"

# 4. Check all sessions status
./tools/list-sessions.sh

# 5. Cleanup when done
./tools/cleanup-sessions.sh --all  # Or cleanup individually
```

**When to use:** Parallel independent tasks, workspace organization, resource isolation.

**Best practices:**
- Use descriptive session names (purpose-based: loader-*, analysis-*, monitor-*)
- One session per major task (don't overload single session)
- Check `list-sessions.sh` frequently to monitor all sessions
- Cleanup all related sessions together when project complete

## Decision Trees

### Should I Create a New Session or Reuse?

```
Start
  │
  ├─→ Is this a quick one-off task?
  │   └─→ YES → Create new ephemeral session
  │             (cleanup immediately after)
  │
  ├─→ Do I have an existing session for this work?
  │   ├─→ YES → Is it still alive?
  │   │   ├─→ YES → Reuse existing session
  │   │   └─→ NO  → Create new session
  │   └─→ NO  → Create new session
  │
  └─→ Am I starting a new long-running project?
      └─→ YES → Create new persistent session
                (descriptive name with date/project)
```

**Rules of thumb:**
- ✅ **Create new** for: Different projects, parallel tasks, isolation needed
- ✅ **Reuse** for: Continuing same work, state preservation needed
- ❌ **Don't reuse** for: Unrelated tasks (state pollution), different projects

### When Should I Clean Up Sessions?

```
Start
  │
  ├─→ Is session marked as "dead" or "zombie"?
  │   └─→ YES → Cleanup immediately
  │             (./tools/cleanup-sessions.sh)
  │
  ├─→ Has the task completed?
  │   └─→ YES → Cleanup immediately
  │             (tmux kill-session + cleanup-sessions.sh)
  │
  ├─→ Is session idle for > 1 hour?
  │   ├─→ AND no state preservation needed?
  │   │   └─→ YES → Cleanup
  │   └─→ OR state needed?
  │       └─→ NO  → Keep (long-running analysis)
  │
  └─→ Am I done for the day but continuing tomorrow?
      └─→ Keep session (resume later)
```

**Cleanup commands:**
```bash
# Remove only dead/zombie sessions (safe, default)
./tools/cleanup-sessions.sh

# Remove sessions older than 1 hour
./tools/cleanup-sessions.sh --older-than 1h

# Remove all sessions (careful!)
./tools/cleanup-sessions.sh --all

# Preview what would be removed (dry-run)
./tools/cleanup-sessions.sh --dry-run
```

### How Should I Handle Session Errors?

```
Error Detected
  │
  ├─→ Is session responding to commands?
  │   ├─→ NO  → Check health (pane-health.sh)
  │   │         ├─→ Dead/zombie → Capture output → Cleanup → Recreate
  │   │         └─→ Alive but hung → Send C-c → Retry command
  │   └─→ YES → Problem is elsewhere (not session)
  │
  ├─→ Are commands being executed but output wrong?
  │   └─→ Check PYTHON_BASIC_REPL=1 was set
  │       └─→ Not set? Restart session with env var
  │
  └─→ Is prompt not appearing?
      └─→ Increase timeout (-T flag)
          └─→ Still failing? Check pane content manually
```

## Tool Reference Matrix

| Lifecycle Stage | Tool | Purpose | Example Command |
|-----------------|------|---------|-----------------|
| **Pre-check** | `list-sessions.sh` | Check existing sessions | `./tools/list-sessions.sh` |
| **Create** | `create-session.sh` | Spawn new session | `./tools/create-session.sh -n my-session --python` |
| **Init** | `wait-for-text.sh` | Wait for startup prompt | `./tools/wait-for-text.sh -s my-session -p ">>>" -T 15` |
| **Active Use** | `safe-send.sh` | Send commands safely | `./tools/safe-send.sh -s my-session -c "print(42)" -w ">>>"` |
| **Active Use** | `safe-send.sh` (multiline) | Send code blocks | `./tools/safe-send.sh -s my-session -m -c "def foo():\n    return 42" -w ">>>"` |
| **Monitoring** | `pane-health.sh` | Check session health | `./tools/pane-health.sh -s my-session` |
| **Monitoring** | `list-sessions.sh` | View all sessions | `./tools/list-sessions.sh --json` |
| **Capture** | `tmux capture-pane` | Get session output | `tmux -S $SOCKET capture-pane -p -t session:0.0 -S -100` |
| **Cleanup** | `cleanup-sessions.sh` | Remove dead sessions | `./tools/cleanup-sessions.sh` |
| **Cleanup** | `tmux kill-session` | Terminate specific session | `tmux -S $SOCKET kill-session -t my-session` |

## Troubleshooting Quick Reference

### Session Not Found

**Symptom:** `./tools/safe-send.sh -s my-session -c "cmd"` fails with "Session 'my-session' not found in registry"

**Causes:**
1. Session was never created
2. Session was created but not registered (`--no-register` flag used)
3. Session was cleaned up by mistake

**Fixes:**
```bash
# Check what sessions exist
./tools/list-sessions.sh

# Check if session exists outside registry
./tools/find-sessions.sh --all

# Recreate session
./tools/create-session.sh -n my-session --python
```

### Commands Not Executing

**Symptom:** Commands sent but REPL shows no activity

**Causes:**
1. PYTHON_BASIC_REPL=1 not set (most common!)
2. Session crashed/dead
3. Prompt not detected correctly

**Fixes:**
```bash
# Check session health
./tools/pane-health.sh -s my-session --format text

# Manually check what's in the pane
SOCKET=$(jq -r '.sessions["my-session"].socket' ~/.local/state/claude-tmux/.sessions.json)
tmux -S "$SOCKET" capture-pane -p -t my-session:0.0 -S -20

# If Python REPL, verify PYTHON_BASIC_REPL=1 was set
# Symptom: You'll see fancy colored prompts instead of plain >>>
# Fix: Kill and recreate with correct env var
```

### Output Capture Issues

**Symptom:** `tmux capture-pane` returns incomplete or truncated output

**Causes:**
1. Pane history buffer too small
2. Lines wrapped due to terminal width
3. ANSI color codes interfering

**Fixes:**
```bash
# Capture more history (-S flag = start line)
tmux -S "$SOCKET" capture-pane -p -t session:0.0 -S -500

# Join wrapped lines (-J flag)
tmux -S "$SOCKET" capture-pane -p -J -t session:0.0 -S -200

# Strip ANSI color codes
tmux -S "$SOCKET" capture-pane -p -t session:0.0 | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g'
```

### Dead/Zombie Sessions

**Symptom:** `./tools/list-sessions.sh` shows status "dead" or "zombie"

**Causes:**
1. Process crashed
2. Session was killed manually
3. Out of memory / system issue

**Fixes:**
```bash
# Capture any remaining output for debugging
SOCKET=$(jq -r '.sessions["dead-session"].socket' ~/.local/state/claude-tmux/.sessions.json)
tmux -S "$SOCKET" capture-pane -p -t dead-session:0.0 -S -500 > debug.txt 2>/dev/null

# Remove from registry
./tools/cleanup-sessions.sh

# Recreate if needed
./tools/create-session.sh -n replacement-session --python
```

### Multiple Sessions with Same Name

**Symptom:** `./tools/create-session.sh -n my-session --python` fails with "session already exists"

**Causes:**
1. Forgot to check existing sessions first
2. Previous session not cleaned up

**Fixes:**
```bash
# Check existing sessions
./tools/list-sessions.sh

# Use different name OR cleanup old session first
tmux -S "$SOCKET" kill-session -t my-session
./tools/cleanup-sessions.sh

# Then create new session
./tools/create-session.sh -n my-session --python
```

## Best Practices

### ✅ DO

1. **Always check before creating**
   ```bash
   ./tools/list-sessions.sh  # Check for conflicts first
   ```

2. **Use descriptive session names**
   ```bash
   # Good: data-analysis-2025-11, debug-api-auth, monitor-prod
   # Bad: session1, test, tmp
   ```

3. **Set PYTHON_BASIC_REPL=1 for Python**
   ```bash
   # This is handled by create-session.sh --python automatically
   # But verify if creating manually
   ```

4. **Wait for prompts after every command**
   ```bash
   ./tools/safe-send.sh -s session -c "command" -w ">>>" -T 10
   # Always include -w flag for synchronization
   ```

5. **Use session registry (-s flag)**
   ```bash
   # Preferred: ./tools/safe-send.sh -s my-session -c "cmd"
   # Avoid: ./tools/safe-send.sh -S $SOCKET -t session:0.0 -c "cmd"
   ```

6. **Check health before critical operations**
   ```bash
   if ./tools/pane-health.sh -s session; then
     ./tools/safe-send.sh -s session -c "critical_command"
   fi
   ```

7. **Use multiline mode for code blocks**
   ```bash
   # 10x faster than line-by-line
   ./tools/safe-send.sh -s session -m -c "def foo():\n    return 42" -w ">>>"
   ```

8. **Cleanup dead sessions regularly**
   ```bash
   # Run periodically or in cleanup scripts
   ./tools/cleanup-sessions.sh
   ```

9. **Capture output early and often**
   ```bash
   # Before making destructive changes
   tmux -S "$SOCKET" capture-pane -p -t session:0.0 -S -200 > backup.txt
   ```

10. **Use --dry-run for cleanup preview**
    ```bash
    # See what would be removed before executing
    ./tools/cleanup-sessions.sh --dry-run
    ./tools/cleanup-sessions.sh --older-than 2d --dry-run
    ```

### ❌ DON'T

1. **Don't create sessions without checking first** - Leads to name conflicts
2. **Don't reuse sessions for unrelated work** - State pollution causes bugs
3. **Don't forget -w flag when sending commands** - Race conditions
4. **Don't skip health checks before critical operations** - Pane might be dead
5. **Don't use generic session names** - Hard to manage multiple sessions
6. **Don't leave dead sessions in registry** - Clutters output, wastes resources
7. **Don't forget to cleanup ephemeral sessions** - Resource leaks
8. **Don't send commands too fast** - Wait for prompts between commands
9. **Don't ignore session health warnings** - Investigate issues early
10. **Don't use line-by-line for large code blocks** - Use multiline mode instead

## Related References

- [Session Registry Guide](./session-registry.md) - Deep dive on registry system
- [Direct Socket Control](./direct-socket-control.md) - Advanced manual socket management
- [Main SKILL.md](../SKILL.md) - Complete tmux skill documentation

---

**Version:** Documented for tmux skill v1.3.0+ (includes multiline support)
