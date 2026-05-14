---
name: zellij
description: "Terminal workspace and multiplexer for interactive CLI sessions. Use when managing terminal sessions, running interactive REPLs, debugging applications, automating terminal workflows, or when user mentions zellij, terminal multiplexer, floating panes, or session layouts. Simpler alternative to tmux with native session management."
license: MIT
---

# Zellij Skill

Zellij is a terminal workspace/multiplexer with a focus on simplicity and power. Use it for managing terminal sessions, running interactive programs, and automating terminal workflows.

## Quickstart

```bash
# Start a new session (auto-generates name)
zellij

# Start a named session
zellij -s my-session

# List active sessions
zellij list-sessions    # or: zellij ls

# Attach to a session
zellij attach my-session    # or: zellij a my-session

# Attach or create if doesn't exist
zellij attach -c my-session

# Kill a session
zellij kill-session my-session    # or: zellij k my-session
```

## Programmatic Control

Zellij provides CLI commands to control sessions programmatically - simpler than tmux (no socket management needed).

### Sending Text to Panes

Use `write-chars` to send text to the focused pane:

```bash
# Send text to current session's focused pane
zellij action write-chars "echo hello"

# Send to a specific session
zellij -s my-session action write-chars "print('hello')"

# Send with newline (executes command)
zellij action write-chars $'echo hello\n'

# Send control characters
zellij action write-chars $'\x03'    # Ctrl+C
```

### Capturing Output

Use `dump-screen` to capture pane contents:

```bash
# Dump current pane to file
zellij action dump-screen /tmp/output.txt

# Dump with full scrollback history
zellij action dump-screen --full /tmp/output.txt

# For a specific session
zellij -s my-session action dump-screen /tmp/output.txt
```

### Running Commands in New Panes

```bash
# Run command in a new pane
zellij run -- htop

# Run in floating pane
zellij run --floating -- python3

# Run in specific direction
zellij run --direction down -- tail -f /var/log/syslog

# Run and close pane when command exits
zellij run --close-on-exit -- ls -la

# Run command in specific session
zellij -s my-session run -- python3
```

## Input Modes

Zellij uses a modal interface. Switch modes with `zellij action switch-mode`:

| Mode | Purpose | Default Key |
|------|---------|-------------|
| `normal` | Default mode, basic navigation | (default) |
| `locked` | Disable all keybindings except unlock | Ctrl+g |
| `pane` | Pane manipulation (new, close, move) | Ctrl+p |
| `tab` | Tab manipulation | Ctrl+t |
| `resize` | Resize focused pane | Ctrl+n |
| `scroll` | Scroll within focused pane | Ctrl+s |
| `session` | Session management, detach | Ctrl+o |

```bash
# Switch to locked mode (useful when app conflicts with keybindings)
zellij action switch-mode locked

# Switch back to normal
zellij action switch-mode normal
```

## Common Workflows

### Python REPL

```bash
# Start session with Python
zellij -s python-dev
zellij -s python-dev run -- python3

# Send commands
zellij -s python-dev action write-chars $'print("hello world")\n'

# Capture output
zellij -s python-dev action dump-screen /tmp/python-output.txt
```

### Interactive Debugging (gdb/lldb)

```bash
# Start debugger session
zellij -s debug-session run -- gdb ./my-program

# Send debugger commands
zellij -s debug-session action write-chars $'break main\n'
zellij -s debug-session action write-chars $'run\n'
zellij -s debug-session action write-chars $'bt\n'

# Capture backtrace
zellij -s debug-session action dump-screen /tmp/backtrace.txt
```

### Interactive Git (git add -p)

```bash
# Start git session
zellij -s git-work

# Run interactive staging
zellij -s git-work action write-chars $'git add -p\n'

# Respond to prompts
zellij -s git-work action write-chars $'y\n'    # Stage hunk
zellij -s git-work action write-chars $'n\n'    # Skip hunk
zellij -s git-work action write-chars $'s\n'    # Split hunk
zellij -s git-work action write-chars $'q\n'    # Quit
```

## Pane Management

```bash
# Create new pane
zellij action new-pane
zellij action new-pane --direction right
zellij action new-pane --floating

# Close focused pane
zellij action close-pane

# Move focus
zellij action move-focus left
zellij action move-focus right
zellij action move-focus up
zellij action move-focus down

# Toggle floating panes
zellij action toggle-floating-panes

# Resize pane
zellij action resize increase left
zellij action resize decrease right
```

## Tab Management

```bash
# Create new tab
zellij action new-tab
zellij action new-tab --name "servers"

# Navigate tabs
zellij action go-to-next-tab
zellij action go-to-previous-tab
zellij action go-to-tab 1

# Close tab
zellij action close-tab

# Rename tab
zellij action rename-tab "my-tab-name"
```

## Session Management

```bash
# List sessions with details
zellij list-sessions

# List sessions (short format)
zellij ls --short

# Attach to session by index
zellij attach --index 0

# Create detached session in background
zellij attach -b my-session

# Kill all sessions
zellij kill-all-sessions --yes

# Delete session (removes from disk)
zellij delete-session my-session
zellij delete-session --force my-session    # Force kill if running
```

## Layouts

Zellij supports declarative layouts in KDL format:

```bash
# Start with a layout
zellij --layout /path/to/layout.kdl

# Start with built-in compact layout
zellij --layout compact

# Dump current layout
zellij action dump-layout
```

See [references/layouts.md](references/layouts.md) for layout syntax.

## Tips

1. **Session targeting**: Always use `-s session-name` when automating to avoid ambiguity
2. **Newlines**: Use `$'\n'` in bash to send actual newlines that execute commands
3. **Control characters**: Use `$'\x03'` for Ctrl+C, `$'\x04'` for Ctrl+D
4. **Output capture**: `dump-screen --full` captures scrollback; without `--full` only visible content
5. **Floating panes**: Great for temporary tasks - toggle with `toggle-floating-panes`

## Troubleshooting

**Session not found:**
```bash
# List all sessions first
zellij ls
# Use exact session name
zellij -s exact-session-name action write-chars "test"
```

**Text not appearing:**
- Ensure the target pane is focused
- Check if the pane is in a mode that accepts input
- Try switching to normal mode first: `zellij action switch-mode normal`

**Commands not executing:**
- Remember to include newline: `$'command\n'`
- Check if application is waiting for input

## Reference

For comprehensive documentation:
- [Actions Reference](references/actions.md) - All available actions
- [Layouts Reference](references/layouts.md) - Layout system documentation
- [Official Docs](https://zellij.dev/documentation/)
