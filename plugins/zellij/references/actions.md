# Zellij Actions Reference

Complete reference for all `zellij action` commands.

## Table of Contents

- [Text Input](#text-input)
- [Screen Capture](#screen-capture)
- [Pane Actions](#pane-actions)
- [Tab Actions](#tab-actions)
- [Focus & Navigation](#focus--navigation)
- [Resize Actions](#resize-actions)
- [Scroll Actions](#scroll-actions)
- [Mode Switching](#mode-switching)
- [Session Actions](#session-actions)
- [Plugin Actions](#plugin-actions)
- [Layout Actions](#layout-actions)

## Text Input

### write-chars

Write characters to the focused pane's terminal.

```bash
zellij action write-chars "text to send"

# With newline (executes as command)
zellij action write-chars $'echo hello\n'

# Control characters
zellij action write-chars $'\x03'    # Ctrl+C (SIGINT)
zellij action write-chars $'\x04'    # Ctrl+D (EOF)
zellij action write-chars $'\x1a'    # Ctrl+Z (SIGTSTP)
zellij action write-chars $'\x1b'    # Escape
```

### write

Write raw bytes to the focused pane.

```bash
zellij action write 104 101 108 108 111    # "hello" in ASCII
```

## Screen Capture

### dump-screen

Dump pane contents to a file.

```bash
# Visible content only
zellij action dump-screen /path/to/output.txt

# Full scrollback history
zellij action dump-screen --full /path/to/output.txt
```

### dump-layout

Dump current layout to stdout.

```bash
zellij action dump-layout > my-layout.kdl
```

### edit-scrollback

Open pane scrollback in default editor ($EDITOR).

```bash
zellij action edit-scrollback
```

## Pane Actions

### new-pane

Create a new pane.

```bash
# Auto-place in best available space
zellij action new-pane

# Specific direction
zellij action new-pane --direction right
zellij action new-pane --direction down
zellij action new-pane --direction left
zellij action new-pane --direction up

# Floating pane
zellij action new-pane --floating

# With specific position/size (floating only)
zellij action new-pane --floating --x 10 --y 10 --width 50% --height 50%

# In-place (replaces current pane temporarily)
zellij action new-pane --in-place

# With command
zellij action new-pane -- htop
zellij action new-pane --floating -- python3

# Close on exit
zellij action new-pane --close-on-exit -- ls -la

# Start suspended (runs on Enter)
zellij action new-pane --start-suspended -- long-running-command

# Stacked pane
zellij action new-pane --stacked
```

### close-pane

Close the focused pane.

```bash
zellij action close-pane
```

### rename-pane

Rename the focused pane.

```bash
zellij action rename-pane "my-pane-name"
```

### undo-rename-pane

Revert pane to previous name.

```bash
zellij action undo-rename-pane
```

### toggle-pane-embed-or-floating

Convert floating pane to tiled or vice versa.

```bash
zellij action toggle-pane-embed-or-floating
```

### toggle-floating-panes

Toggle visibility of all floating panes.

```bash
zellij action toggle-floating-panes
```

### toggle-fullscreen

Toggle fullscreen for focused pane.

```bash
zellij action toggle-fullscreen
```

### toggle-pane-frames

Toggle pane border frames.

```bash
zellij action toggle-pane-frames
```

### toggle-pane-pinned

Pin/unpin floating pane (always on top).

```bash
zellij action toggle-pane-pinned
```

### stack-panes

Stack multiple panes together.

```bash
zellij action stack-panes -- terminal_1 terminal_2 plugin_1
```

## Tab Actions

### new-tab

Create a new tab.

```bash
# Empty tab
zellij action new-tab

# Named tab
zellij action new-tab --name "servers"

# With layout
zellij action new-tab --layout /path/to/layout.kdl

# With working directory
zellij action new-tab --cwd /path/to/dir
```

### close-tab

Close the current tab.

```bash
zellij action close-tab
```

### go-to-tab

Go to tab by index (1-based).

```bash
zellij action go-to-tab 1
zellij action go-to-tab 3
```

### go-to-tab-name

Go to tab by name.

```bash
zellij action go-to-tab-name "servers"

# Create if doesn't exist
zellij action go-to-tab-name --create "new-tab"
```

### go-to-next-tab

```bash
zellij action go-to-next-tab
```

### go-to-previous-tab

```bash
zellij action go-to-previous-tab
```

### rename-tab

```bash
zellij action rename-tab "new-name"
```

### undo-rename-tab

```bash
zellij action undo-rename-tab
```

### move-tab

Move current tab left or right.

```bash
zellij action move-tab left
zellij action move-tab right
```

### toggle-active-sync-tab

Toggle syncing input to all panes in tab.

```bash
zellij action toggle-active-sync-tab
```

### query-tab-names

Query all tab names (outputs to stdout).

```bash
zellij action query-tab-names
```

## Focus & Navigation

### move-focus

Move focus to adjacent pane.

```bash
zellij action move-focus left
zellij action move-focus right
zellij action move-focus up
zellij action move-focus down
```

### move-focus-or-tab

Move focus to pane, or switch tab if at edge.

```bash
zellij action move-focus-or-tab left
zellij action move-focus-or-tab right
```

### focus-next-pane

```bash
zellij action focus-next-pane
```

### focus-previous-pane

```bash
zellij action focus-previous-pane
```

### move-pane

Move focused pane in direction (or rotate if no direction).

```bash
zellij action move-pane
zellij action move-pane right
zellij action move-pane down
```

### move-pane-backwards

Rotate pane position backwards.

```bash
zellij action move-pane-backwards
```

## Resize Actions

### resize

Resize focused pane.

```bash
# Increase/decrease in direction
zellij action resize increase left
zellij action resize increase right
zellij action resize increase up
zellij action resize increase down

zellij action resize decrease left
zellij action resize decrease right
```

### change-floating-pane-coordinates

Change position/size of floating pane.

```bash
zellij action change-floating-pane-coordinates \
  --pane-id terminal_1 \
  --x 10% --y 10% \
  --width 80% --height 80%
```

## Scroll Actions

### scroll-up

```bash
zellij action scroll-up
```

### scroll-down

```bash
zellij action scroll-down
```

### scroll-to-top

```bash
zellij action scroll-to-top
```

### scroll-to-bottom

```bash
zellij action scroll-to-bottom
```

### page-scroll-up

```bash
zellij action page-scroll-up
```

### page-scroll-down

```bash
zellij action page-scroll-down
```

### half-page-scroll-up

```bash
zellij action half-page-scroll-up
```

### half-page-scroll-down

```bash
zellij action half-page-scroll-down
```

## Mode Switching

### switch-mode

Switch input mode.

```bash
zellij action switch-mode normal
zellij action switch-mode locked
zellij action switch-mode pane
zellij action switch-mode tab
zellij action switch-mode resize
zellij action switch-mode scroll
zellij action switch-mode session
```

## Session Actions

### detach

Detach from current session.

```bash
zellij action detach
```

### rename-session

Rename current session.

```bash
zellij action rename-session "new-name"
```

### switch-session

Switch to different session.

```bash
zellij action switch-session other-session

# With specific tab/pane focus
zellij action switch-session other-session --tab-position 2 --pane-id terminal_1
```

### list-clients

List connected clients.

```bash
zellij action list-clients
```

## Plugin Actions

### launch-plugin

Launch a plugin.

```bash
zellij action launch-plugin zellij:strider
zellij action launch-plugin --floating file:/path/to/plugin.wasm
```

### launch-or-focus-plugin

Launch plugin or focus if already running.

```bash
zellij action launch-or-focus-plugin zellij:strider
```

### start-or-reload-plugin

Start plugin or reload if running.

```bash
zellij action start-or-reload-plugin zellij:status-bar
```

### pipe

Send data to plugins.

```bash
# Send to specific plugin
zellij action pipe --plugin file:/path/to/plugin.wasm --name my_pipe -- "data"

# Send to all listening plugins
zellij action pipe --name my_pipe -- "data"

# Pipe from stdin
echo "data" | zellij action pipe --name my_pipe
```

## Layout Actions

### previous-swap-layout

Switch to previous swap layout.

```bash
zellij action previous-swap-layout
```

### next-swap-layout

Switch to next swap layout.

```bash
zellij action next-swap-layout
```

## Utility Actions

### clear

Clear focused pane buffers.

```bash
zellij action clear
```

## Targeting Specific Sessions

All actions can target a specific session:

```bash
# Target specific session
zellij -s my-session action write-chars "hello"
zellij -s my-session action dump-screen /tmp/out.txt
zellij -s my-session action new-pane --floating
```

## Control Character Reference

| Character | Code | Description |
|-----------|------|-------------|
| Ctrl+C | `$'\x03'` | Interrupt (SIGINT) |
| Ctrl+D | `$'\x04'` | EOF |
| Ctrl+Z | `$'\x1a'` | Suspend (SIGTSTP) |
| Escape | `$'\x1b'` | Escape key |
| Enter | `$'\n'` | Newline |
| Tab | `$'\t'` | Tab |
| Backspace | `$'\x7f'` | Delete previous char |
