# Direct Socket Control

This guide covers using direct tmux commands for session management without the session registry. This is an advanced approach for users who need explicit control over socket paths and session management.

**Note:** The session registry is recommended for most workflows. It eliminates ~80% of boilerplate and provides automatic session tracking, health checking, and cleanup. See [Session Registry Reference](session-registry.md) for the standard approach.

## When to Use This Approach

Use direct socket control when you need:
- Custom socket isolation requirements
- Integration with existing tmux workflows
- Multiple sessions on different sockets with complex routing
- Testing or debugging tmux configuration

For most interactive development, debugging, and REPL workflows, use the session registry tools instead.

## Manual Setup

```bash
SOCKET_DIR=${TMPDIR:-/tmp}/claude-tmux-sockets  # well-known dir for all agent sockets
mkdir -p "$SOCKET_DIR"
SOCKET="$SOCKET_DIR/claude.sock"                # keep agent sessions separate from your personal tmux
SESSION=claude-python                           # slug-like names; avoid spaces
tmux -S "$SOCKET" new -d -s "$SESSION" -n shell
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- 'PYTHON_BASIC_REPL=1 python3 -q' Enter
tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION":0.0 -S -200  # watch output
tmux -S "$SOCKET" kill-session -t "$SESSION"                   # clean up
```

After starting a session, ALWAYS tell the user how to monitor it:

```
To monitor this session yourself:
  tmux -S "$SOCKET" attach -t claude-python

Or to capture the output once:
  tmux -S "$SOCKET" capture-pane -p -J -t claude-python:0.0 -S -200
```

## Socket Convention

- Agents MUST place tmux sockets under `CLAUDE_TMUX_SOCKET_DIR` (defaults to `${TMPDIR:-/tmp}/claude-tmux-sockets`) and use `tmux -S "$SOCKET"` so we can enumerate/clean them. Create the dir first: `mkdir -p "$CLAUDE_TMUX_SOCKET_DIR"`.
- Default socket path to use unless you must isolate further: `SOCKET="$CLAUDE_TMUX_SOCKET_DIR/claude.sock"`.

## Targeting Panes and Naming

- Target format: `{session}:{window}.{pane}`, defaults to `:0.0` if omitted. Keep names short (e.g., `claude-py`, `claude-gdb`).
- Use `-S "$SOCKET"` consistently to stay on the private socket path. If you need user config, drop `-f /dev/null`; otherwise `-f /dev/null` gives a clean config.
- Inspect: `tmux -S "$SOCKET" list-sessions`, `tmux -S "$SOCKET" list-panes -a`.

## Finding Sessions Manually

- List sessions on a specific socket: `./tools/find-sessions.sh -S "$SOCKET"`; add `-q partial-name` to filter.
- Scan all sockets: `./tools/find-sessions.sh --all` (uses `CLAUDE_TMUX_SOCKET_DIR`)

## Direct tmux send-keys

- Prefer literal sends to avoid shell splitting: `tmux -S "$SOCKET" send-keys -t target -l -- "$cmd"`
- When composing inline commands, use single quotes or ANSI C quoting to avoid expansion: `tmux ... send-keys -t target -- $'python3 -m http.server 8000'`.
- To send control keys: `tmux ... send-keys -t target C-c`, `C-d`, `C-z`, `Escape`, etc.

## Comparison with Session Registry

| Feature | Direct Socket Control | Session Registry |
|---------|----------------------|------------------|
| Setup complexity | Manual, verbose | Automated with tools |
| Socket/target specification | Required every time | Once at creation |
| Session discovery | Manual enumeration | Automatic tracking |
| Health checking | Manual verification | Built-in health status |
| Cleanup | Manual kill commands | Automated cleanup tools |
| Auto-detection | Not available | Single session auto-detect |
| Best for | Custom isolation, CI/CD | Interactive workflows |

## Migrating to Session Registry

If you're using direct socket control and want to migrate to the registry approach:

1. **Create sessions with registry tools:**
   ```bash
   # Instead of:
   # tmux -S "$SOCKET" new -d -s my-session -n shell
   # Use:
   ./tools/create-session.sh -n my-session --shell
   ```

2. **Replace socket/target with session name:**
   ```bash
   # Instead of:
   # ./tools/safe-send.sh -S "$SOCKET" -t "$SESSION":0.0 -c "command"
   # Use:
   ./tools/safe-send.sh -s my-session -c "command"
   ```

3. **Use registry for cleanup:**
   ```bash
   # Instead of:
   # tmux -S "$SOCKET" kill-session -t "$SESSION"
   # Use:
   ./tools/cleanup-sessions.sh
   ```

See the [Migration Guide](session-registry.md#migration-guide) in the Session Registry Reference for complete migration instructions.

## See Also

- [Session Registry Reference](session-registry.md) - The recommended approach for most workflows
- [Session Registry: Best Practices](session-registry.md#best-practices) - When to use registry vs. manual
- [Migration Guide](session-registry.md#migration-guide) - Transition from manual to registry approach
