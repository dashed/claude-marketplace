---
name: tmux
description: "Remote control tmux sessions for interactive CLIs (python, gdb, git add -p, etc.) by sending keystrokes and scraping pane output. Use when debugging applications, running interactive REPLs (Python, gdb, ipdb, psql, mysql, node), automating terminal workflows, interactive git commands (git add -p, git stash -p, git rebase -i), or when user mentions tmux, debugging, or interactive shells."
license: Vibecoded
---

# tmux Skill

Use tmux as a programmable terminal multiplexer for interactive work. Works on Linux and macOS with stock tmux; avoid custom config by using a private socket.

## Quickstart

The session registry eliminates repetitive socket/target specification through automatic session tracking (~80% reduction in boilerplate):

**IMPORTANT**: Before creating a new session, ALWAYS check existing sessions first to avoid name conflicts:

```bash
# Check existing sessions to ensure name is available
./tools/list-sessions.sh

# Create and register a Python REPL session (choose a unique name)
./tools/create-session.sh -n claude-python --python

# Send commands using session name (auto-lookup socket/target)
./tools/safe-send.sh -s claude-python -c "print(2+2)" -w ">>>"

# Or with a single session, omit -s entirely (auto-detect)
./tools/safe-send.sh -c "print('hello world')" -w ">>>"

# List all registered sessions with health status
./tools/list-sessions.sh

# Clean up dead sessions
./tools/cleanup-sessions.sh
```

After starting a session, ALWAYS tell the user how to monitor it by giving them a command to copy/paste (substitute actual values from the session you created):

```
To monitor this session yourself:
  ./tools/list-sessions.sh

Or attach directly:
  tmux -S <socket> attach -t <session-name>

Or to capture the output once:
  tmux -S <socket> capture-pane -p -J -t <session-name>:0.0 -S -200
```

This must ALWAYS be printed right after a session was started (i.e. right before you start using the session) and once again at the end of the tool loop. But the earlier you send it, the happier the user will be.

## How It Works

The session registry provides three ways to reference sessions:

1. **By name** using `-s session-name` (looks up socket/target in registry)
2. **Auto-detect** when only one session exists (omit `-s`)
3. **Explicit** using `-S socket -t target` (backward compatible)

Tools automatically choose the right session using this priority order:
1. Explicit `-S` and `-t` flags (highest priority)
2. Session name `-s` flag (registry lookup)
3. Auto-detect single session (if only one exists)

**Benefits:**
- No more repeating `-S socket -t target` on every command
- Automatic session discovery
- Built-in health tracking
- Activity timestamps for cleanup decisions
- Fully backward compatible

## Common Workflows

For practical examples of managing tmux sessions through their lifecycle, see the [Session Lifecycle Guide](./references/session-lifecycle.md).

This guide covers:
- **Daily workflows**: Ephemeral sessions, long-running analysis, crash recovery, multi-session workspaces
- **Decision trees**: Create vs reuse, cleanup timing, error handling
- **Tool reference matrix**: Which tools to use at each lifecycle stage
- **Troubleshooting**: Quick fixes for common problems (session not found, commands not executing, cleanup issues)
- **Best practices**: 10 DO's and 10 DON'Ts with examples

## Finding sessions

List all registered sessions with health status:
```bash
./tools/list-sessions.sh           # Table format
./tools/list-sessions.sh --json    # JSON format
```

Output shows session name, socket, target, health status, PID, and creation time.

## Sending input safely

The `./tools/safe-send.sh` helper provides automatic retries, readiness checks, and optional prompt waiting:

```bash
# Using session name (looks up socket/target from registry)
./tools/safe-send.sh -s claude-python -c "print('hello')" -w ">>>"

# Auto-detect single session (omit -s)
./tools/safe-send.sh -c "print('world')" -w ">>>"

# Explicit socket/target (backward compatible)
./tools/safe-send.sh -S "$SOCKET" -t "$SESSION":0.0 -c "print('hello')" -w ">>>"
```

See the [Helper: safe-send.sh](#helper-safe-sendsh) section below for full documentation.

## Watching output

- Capture recent history (joined lines to avoid wrapping artifacts): `tmux -S "$SOCKET" capture-pane -p -J -t target -S -200`.
- For continuous monitoring, poll with the helper script (below) instead of `tmux wait-for` (which does not watch pane output).
- You can also temporarily attach to observe: `tmux -S "$SOCKET" attach -t "$SESSION"`; detach with `Ctrl+b d`.
- When giving instructions to a user, **explicitly print a copy/paste monitor command** alongside the action—don't assume they remembered the command.

## Spawning Processes

Some special rules for processes:

- when asked to debug, use lldb by default
- **CRITICAL**: When starting a Python interactive shell, **always** set the `PYTHON_BASIC_REPL=1` environment variable before launching Python. This is **essential** - the non-basic console (fancy REPL with syntax highlighting) interferes with send-keys and will cause commands to fail silently.
  ```bash
  # When using create-session.sh, this is automatic with --python flag
  ./tools/create-session.sh -n my-python --python
  
  # When creating manually:
  tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- 'PYTHON_BASIC_REPL=1 python3 -q' Enter
  ```

## Synchronizing / waiting for prompts

Use timed polling to avoid races with interactive tools:

```bash
# Wait for Python prompt
./tools/wait-for-text.sh -s claude-python -p '^>>>' -T 15 -l 4000

# Auto-detect single session
./tools/wait-for-text.sh -p '^>>>' -T 15

# Explicit socket/target
./tools/wait-for-text.sh -S "$SOCKET" -t "$SESSION":0.0 -p '^>>>' -T 15 -l 4000
```

For long-running commands, poll for completion text (`"Type quit to exit"`, `"Program exited"`, etc.) before proceeding.

## Interactive tool recipes

- **Python REPL**: Use `./tools/create-session.sh -n my-python --python`; wait for `^>>>`; send code; interrupt with `C-c`. The `--python` flag automatically sets `PYTHON_BASIC_REPL=1`.
- **gdb**: Use `./tools/create-session.sh -n my-gdb --gdb`; disable paging with safe-send; break with `C-c`; issue `bt`, `info locals`, etc.; exit via `quit` then confirm `y`.
- **Interactive git** (`git add -p`, `git stash -p`, `git checkout -p`, `git reset -p`): Use `./tools/create-session.sh -n my-git --shell`; run the git command; wait for hunk prompt pattern `\?\s*$`; send single-letter responses (`y` stage, `n` skip, `s` split, `q` quit). Each response requires Enter.
- **Other TTY apps** (ipdb, psql, mysql, node, bash): Use `./tools/create-session.sh -n my-session --shell`; poll for prompt; send literal text and Enter.

## Cleanup

Killing sessions (recommended - removes both tmux session and registry entry):
```bash
# Kill a specific session by name
./tools/kill-session.sh -s session-name

# Auto-detect and kill single session
./tools/kill-session.sh

# Dry-run to see what would be killed
./tools/kill-session.sh -s session-name --dry-run
```

Registry cleanup (removes registry entries only, doesn't kill tmux sessions):
```bash
# Remove dead sessions from registry
./tools/cleanup-sessions.sh

# Remove sessions older than 1 hour
./tools/cleanup-sessions.sh --older-than 1h

# See what would be removed (dry-run)
./tools/cleanup-sessions.sh --dry-run
```

Manual cleanup (when not using registry):
- Kill a session when done: `tmux -S "$SOCKET" kill-session -t "$SESSION"`.
- Kill all sessions on a socket: `tmux -S "$SOCKET" list-sessions -F '#{session_name}' | xargs -r -n1 tmux -S "$SOCKET" kill-session -t`.
- Remove everything on the private socket: `tmux -S "$SOCKET" kill-server`.

## Helper: create-session.sh

`./tools/create-session.sh` creates and registers new tmux sessions with automatic registry integration.

**IMPORTANT**: Before creating a session, ALWAYS run `./tools/list-sessions.sh` to check for existing sessions and ensure your chosen name is unique.

```bash
./tools/create-session.sh -n <name> [--python|--gdb|--shell] [options]
```

**Key options:**
- `-n`/`--name` session name (required)
- `--python` launch Python REPL with PYTHON_BASIC_REPL=1
- `--gdb` launch gdb debugger
- `--shell` launch bash shell (default)
- `-S`/`--socket` custom socket path (optional, uses default)
- `-w`/`--window` window name (default: "shell")
- `--no-register` don't add to registry

**Examples:**

```bash
# Create Python REPL session
./tools/create-session.sh -n claude-python --python

# Create gdb session
./tools/create-session.sh -n claude-gdb --gdb

# Create session without registering
./tools/create-session.sh -n temp-session --shell --no-register

# Create session with custom socket
./tools/create-session.sh -n my-session -S /tmp/custom.sock --python
```

**Returns JSON with session info:**
```json
{
  "name": "claude-python",
  "socket": "/tmp/claude-tmux-sockets/claude.sock",
  "target": "claude-python:0.0",
  "type": "python-repl",
  "pid": 12345,
  "registered": true
}
```

## Helper: list-sessions.sh

`./tools/list-sessions.sh` lists all registered sessions with health status.

```bash
./tools/list-sessions.sh [--json]
```

**Options:**
- `--json` output as JSON instead of table format

**Table output (default):**
```
NAME            SOCKET          TARGET          STATUS    PID    CREATED
claude-python   claude.sock     :0.0            alive     1234   2h ago
claude-gdb      claude.sock     :0.0            dead      -      1h ago

Total: 2 | Alive: 1 | Dead: 1
```

**JSON output:**
```json
{
  "sessions": [
    {"name": "claude-python", "status": "alive", ...}
  ],
  "total": 2,
  "alive": 1,
  "dead": 1
}
```

**Health statuses:**
- `alive` - Session running and healthy
- `dead` - Pane marked as dead
- `missing` - Session/pane not found
- `zombie` - Process exited but pane exists
- `server` - Tmux server not running

## Helper: cleanup-sessions.sh

`./tools/cleanup-sessions.sh` removes dead or old sessions from the registry.

```bash
./tools/cleanup-sessions.sh [--dry-run] [--all] [--older-than <duration>]
```

**Options:**
- `--dry-run` show what would be cleaned without removing
- `--all` remove all sessions (even alive ones)
- `--older-than <duration>` remove sessions older than threshold (e.g., "1h", "2d")

**Examples:**

```bash
# Remove dead sessions
./tools/cleanup-sessions.sh

# Dry-run to see what would be removed
./tools/cleanup-sessions.sh --dry-run

# Remove sessions inactive for more than 1 hour
./tools/cleanup-sessions.sh --older-than 1h

# Remove all sessions
./tools/cleanup-sessions.sh --all
```

**Duration format:** `30m`, `2h`, `1d`, `3600s`

## Helper: kill-session.sh

Kill tmux session and remove from registry (atomic operation).

**Purpose**: Provides a single operation to fully clean up a session by both killing the tmux session and removing it from the registry.

**Key features**:
- Atomic operation (kills session AND deregisters)
- Three operation modes: registry lookup, explicit socket/target, auto-detect
- Dry-run support for safety
- Proper exit codes for all scenarios

**Usage**:
```bash
# Kill session by name (registry lookup)
tools/kill-session.sh -s claude-python

# Kill with explicit socket and target
tools/kill-session.sh -S /tmp/claude.sock -t my-session:0.0

# Auto-detect single session
tools/kill-session.sh

# Dry-run to see what would happen
tools/kill-session.sh -s claude-python --dry-run
```

**Options**:
- `-s NAME` - Session name (uses registry lookup)
- `-S PATH` - Socket path (explicit mode, requires -t)
- `-t TARGET` - Target pane (explicit mode, requires -S)
- `--dry-run` - Show operations without executing
- `-v` - Verbose output
- `-h` - Show help

**Exit codes**:
- 0 - Complete success (killed AND deregistered)
- 1 - Partial success (one operation succeeded)
- 2 - Complete failure (both failed or not found)
- 3 - Invalid arguments

**Priority order** (when multiple methods specified):
1. Explicit -S and -t (highest priority)
2. Session name -s (registry lookup)
3. Auto-detect (if no flags and only one session exists)

**When to use**:
- Cleaning up after interactive debugging sessions
- Removing sessions that are no longer needed
- Ensuring complete cleanup (both tmux and registry)
- Batch operations with proper error handling

**Notes**:
- Unlike `cleanup-sessions.sh` (which only removes registry entries), this tool also kills the actual tmux session
- Use auto-detect mode when you have only one session and want quick cleanup
- Dry-run mode is helpful to verify what will be cleaned up before executing

## Helper: safe-send.sh

`./tools/safe-send.sh` sends keystrokes to tmux panes with automatic retries, readiness checks, and optional prompt waiting. Prevents dropped commands that can occur when sending to busy or not-yet-ready panes.

```bash
# Session registry mode
./tools/safe-send.sh -s session-name -c "command" [-w pattern]

# Auto-detect mode (single session)
./tools/safe-send.sh -c "command" [-w pattern]

# Explicit mode (backward compatible)
./tools/safe-send.sh -t session:0.0 -c "command" [-S socket] [-w pattern]
```

**Target selection (priority order):**
- `-s`/`--session` session name (looks up socket/target in registry)
- `-t`/`--target` explicit pane target (session:window.pane)
- (no flags) auto-detect if only one session exists

**Key options:**
- `-c`/`--command` command to send (required; empty string sends just Enter)
- `-S`/`--socket` tmux socket path (for custom sockets via -S)
- `-L`/`--socket-name` tmux socket name (for named sockets via -L)
- `-l`/`--literal` use literal mode (send text without executing)
- `-m`/`--multiline` use multiline mode (paste-buffer for code blocks)
- `-w`/`--wait` wait for this pattern after sending
- `-T`/`--timeout` timeout in seconds (default: 30)
- `-r`/`--retries` max retry attempts (default: 3)
- `-i`/`--interval` base retry interval in seconds (default: 0.5)
- `-v`/`--verbose` verbose output for debugging

**Exit codes:**
- `0` - Command sent successfully
- `1` - Failed to send after retries
- `2` - Timeout waiting for prompt
- `3` - Pane not ready
- `4` - Invalid arguments

**Modes:**
- **Normal mode (default):** Sends command and presses Enter (executes in shell/REPL)
- **Multiline mode (-m):** Sends multiline code blocks via paste-buffer (~10x faster than line-by-line). Auto-appends blank line for Python REPL execution. Incompatible with `-l`.
- **Literal mode (-l):** Sends exact characters without Enter (typing text). Incompatible with `-m`.

**Use cases:**
- Send commands to Python REPL with automatic retry and prompt waiting
- Send gdb commands and wait for the gdb prompt
- Critical commands that must not be dropped
- Send commands immediately after session creation
- Automate interactions with any interactive CLI tool

**Examples:**

```bash
# Send Python command using session registry
./tools/safe-send.sh -s claude-python -c "print('hello')" -w ">>>" -T 10

# Auto-detect single session
./tools/safe-send.sh -c "print('world')" -w ">>>"

# Send text in literal mode (no Enter)
./tools/safe-send.sh -s claude-python -c "some text" -l

# Send with custom retry settings
./tools/safe-send.sh -s claude-python -c "ls" -r 5 -i 1.0

# Send control sequence
./tools/safe-send.sh -s claude-python -c "C-c"

# Send multiline Python function (fast, preserves indentation)
./tools/safe-send.sh -s claude-python -m -c "def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)" -w ">>>" -T 10

# Send multiline class definition
./tools/safe-send.sh -s claude-python -m -c "class Calculator:
    def __init__(self):
        self.result = 0

    def add(self, x):
        self.result += x
        return self" -w ">>>"

# Interactive git add -p workflow (stage specific hunks)
./tools/create-session.sh -n claude-git --shell
./tools/safe-send.sh -s claude-git -c "git add -p" -w "\?" -T 10
./tools/safe-send.sh -s claude-git -c "y" -w "\?"    # Stage this hunk
./tools/safe-send.sh -s claude-git -c "n" -w "\?"    # Skip this hunk
./tools/safe-send.sh -s claude-git -c "s" -w "\?"    # Split into smaller hunks
./tools/safe-send.sh -s claude-git -c "q"            # Quit interactive mode

# Explicit socket/target (backward compatible)
SOCKET_DIR=${TMPDIR:-/tmp}/claude-tmux-sockets
SOCKET="$SOCKET_DIR/claude.sock"
./tools/safe-send.sh -S "$SOCKET" -t "$SESSION":0.0 -c "print('hello')" -w ">>>"
```

**Multiline mode benefits:**
- **~10x faster** than sending line-by-line (single operation vs N separate calls)
- **Preserves indentation** perfectly (important for Python)
- **Auto-executes** in Python REPL (blank line appended automatically)
- **Cleaner logs** (one operation instead of many)
- **Best for:** Function definitions, class definitions, complex code blocks

## Helper: wait-for-text.sh

`./tools/wait-for-text.sh` polls a pane for a regex (or fixed string) with a timeout. Works on Linux/macOS with bash + tmux + grep.

```bash
# Using session name (looks up socket/target from registry)
./tools/wait-for-text.sh -s claude-python -p '^>>>' -T 15

# Auto-detect single session (omit -s)
./tools/wait-for-text.sh -p '^>>>' -T 15

# Explicit socket/target (backward compatible)
./tools/wait-for-text.sh -S "$SOCKET" -t "$SESSION":0.0 -p '^>>>' -T 15
```

**Target selection (priority order):**
- `-s`/`--session` session name (looks up socket/target in registry)
- `-t`/`--target` explicit pane target (session:window.pane)
- (no flags) auto-detect if only one session exists

**Options:**
- `-p`/`--pattern` regex to match (required); add `-F` for fixed string
- `-S`/`--socket` tmux socket path (for custom sockets via -S)
- `-T` timeout seconds (integer, default 15)
- `-i` poll interval seconds (default 0.5)
- `-l` history lines to search from the pane (integer, default 1000)
- Exits 0 on first match, 1 on timeout. On failure prints the last captured text to stderr to aid debugging.

**Examples:**

```bash
# Wait for Python prompt using session name
./tools/wait-for-text.sh -s claude-python -p '^>>>' -T 10

# Wait for gdb prompt with auto-detect
./tools/wait-for-text.sh -p '(gdb)' -T 10

# Explicit socket/target (backward compatible)
SOCKET_DIR=${TMPDIR:-/tmp}/claude-tmux-sockets
SOCKET="$SOCKET_DIR/claude.sock"
./tools/wait-for-text.sh -S "$SOCKET" -t "$SESSION":0.0 -p '^>>>' -T 15
```

## Helper: pane-health.sh

`./tools/pane-health.sh` checks the health status of a tmux pane before operations to prevent "pane not found" errors and detect failures early. Essential for reliable automation.

```bash
# Using session name (looks up socket/target from registry)
./tools/pane-health.sh -s claude-python [--format json|text]

# Auto-detect single session (omit -s)
./tools/pane-health.sh --format text

# Explicit socket/target (backward compatible)
./tools/pane-health.sh -S "$SOCKET" -t "$SESSION":0.0 [--format json|text]
```

**Target selection (priority order):**
- `-s`/`--session` session name (looks up socket/target in registry)
- `-t`/`--target` explicit pane target (session:window.pane)
- (no flags) auto-detect if only one session exists

**Options:**
- `-S`/`--socket` tmux socket path (for custom sockets via -S)
- `--format` output format: `json` (default) or `text`
- Exits with status codes indicating health state

**Exit codes:**
- `0` - Healthy (pane alive, process running)
- `1` - Dead (pane marked as dead)
- `2` - Missing (pane/session doesn't exist)
- `3` - Zombie (process exited but pane still exists)
- `4` - Server not running

**JSON output includes:**
- `status`: overall health (`healthy`, `dead`, `missing`, `zombie`, `server_not_running`)
- `server_running`: boolean
- `session_exists`: boolean
- `pane_exists`: boolean
- `pane_dead`: boolean
- `pid`: process ID (or null)
- `process_running`: boolean

**Use cases:**
- Before sending commands: verify pane is ready
- After errors: determine if pane crashed
- Periodic health checks during long operations
- Cleanup decision: which panes to kill vs keep

**Examples:**

```bash
# Check health using session name (JSON output)
./tools/pane-health.sh -s claude-python
# Output: {"status": "healthy", "server_running": true, ...}

# Check health with auto-detect (text output)
./tools/pane-health.sh --format text
# Output: Pane claude-python:0.0 is healthy (PID: 12345, process running)

# Conditional logic with session registry
if ./tools/pane-health.sh -s my-session --format text; then
  echo "Pane is ready for commands"
  ./tools/safe-send.sh -s my-session -c "print('hello')"
else
  echo "Pane is not healthy (exit code: $?)"
fi

# Explicit socket/target (backward compatible)
SOCKET_DIR=${TMPDIR:-/tmp}/claude-tmux-sockets
SOCKET="$SOCKET_DIR/claude.sock"
./tools/pane-health.sh -S "$SOCKET" -t "$SESSION":0.0
```

## Advanced: Direct Socket Control

For advanced users who need explicit control over socket paths without using the session registry, see the [Direct Socket Control](references/direct-socket-control.md) reference.

This is useful for:
- Custom socket isolation requirements
- Integration with existing tmux workflows
- Testing or debugging tmux configuration

Most workflows should use the session registry tools described above.

## Best Practices

For comprehensive guidance on using the session registry effectively, see:

- **[Session Registry Reference](references/session-registry.md)** - Complete documentation including:
  - Registry architecture and file format
  - Advanced usage patterns
  - Troubleshooting guide
  - Migration from manual socket management
  - Best practices for session naming, cleanup strategies, and error handling
  - When to use registry vs. manual approach

Key recommendations:
- Use descriptive session names (e.g., `claude-python-analysis`, not `session1`)
- Run `./tools/cleanup-sessions.sh` periodically to remove dead sessions
- Use `./tools/list-sessions.sh` to verify session health before long operations
- For single-session workflows, omit `-s` flag to leverage auto-detection
- For multiple sessions, always use `-s session-name` for clarity

## Troubleshooting

**Session not found in registry:**
- Use `./tools/list-sessions.sh` to see all registered sessions
- Session may have been created with `--no-register` flag
- Registry file may be corrupted (check `$CLAUDE_TMUX_SOCKET_DIR/.sessions.json`)

**Auto-detection fails with "Multiple sessions found":**
- Specify session name explicitly with `-s my-session`
- Or clean up unused sessions with `./tools/cleanup-sessions.sh`

**Pane health check fails:**
- Session may have crashed - check with `./tools/list-sessions.sh`
- Tmux server may not be running - verify socket exists
- Use `./tools/pane-health.sh -s session-name --format text` for detailed diagnostics

**Registry lock timeout:**
- Another process may be writing to registry
- Wait a moment and retry
- Check for stale lock file: `$CLAUDE_TMUX_SOCKET_DIR/.sessions.lock`

For more detailed troubleshooting, see the [Session Registry Reference](references/session-registry.md#troubleshooting).
