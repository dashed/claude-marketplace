# fzf Actions Reference

Complete reference for all bindable actions in fzf.

## Table of Contents

- [Action Syntax](#action-syntax)
- [Selection Actions](#selection-actions)
- [Cursor Movement](#cursor-movement)
- [Preview Actions](#preview-actions)
- [Query Actions](#query-actions)
- [Multi-Select Actions](#multi-select-actions)
- [Display Actions](#display-actions)
- [Command Execution](#command-execution)
- [Transform Actions](#transform-actions)
- [Events](#events)

## Action Syntax

### Basic Binding

```bash
fzf --bind 'KEY:ACTION'
fzf --bind 'EVENT:ACTION'
```

### Chaining Actions

```bash
# Use + to chain multiple actions
fzf --bind 'ctrl-a:select-all+accept'
fzf --bind 'ctrl-a:select-all' --bind 'ctrl-a:+accept'
```

### Action Arguments

```bash
fzf --bind 'ctrl-a:change-prompt(NewPrompt> )'
fzf --bind 'ctrl-v:preview(cat {})'
```

Alternative delimiters for arguments with parentheses:

```bash
action-name[...]    action-name{...}    action-name<...>
action-name~...~    action-name!...!    action-name@...@
action-name#...#    action-name$...$    action-name%...%
action-name^...^    action-name&...&    action-name*...*
action-name;...;    action-name/.../    action-name|...|
action-name:...     # Special: no closing char needed (must be last)
```

## Selection Actions

| Action | Default Binding | Description |
|--------|-----------------|-------------|
| `accept` | `enter`, `double-click` | Accept current selection and exit |
| `accept-non-empty` | - | Accept only if selection is not empty |
| `accept-or-print-query` | - | Accept, or print query if no match |
| `abort` | `ctrl-c`, `ctrl-g`, `ctrl-q`, `esc` | Abort and exit |
| `cancel` | - | Clear query if not empty, abort otherwise |
| `close` | - | Close preview if open, abort otherwise |

## Cursor Movement

### Basic Movement

| Action | Default Binding | Description |
|--------|-----------------|-------------|
| `up` | `ctrl-k`, `up` | Move cursor up |
| `down` | `ctrl-j`, `down` | Move cursor down |
| `first` | - | Move to first match |
| `last` | - | Move to last match |
| `best` | - | Move to best match |
| `pos(N)` | - | Move to position N (negative counts from end) |

### Match Navigation

| Action | Default Binding | Description |
|--------|-----------------|-------------|
| `up-match` | `ctrl-p`, `alt-up` | Move to match above cursor |
| `down-match` | `ctrl-n`, `alt-down` | Move to match below cursor |
| `up-selected` | - | Move to selected item above |
| `down-selected` | - | Move to selected item below |

### Page Movement

| Action | Default Binding | Description |
|--------|-----------------|-------------|
| `page-up` | `pgup` | Page up |
| `page-down` | `pgdn` | Page down |
| `half-page-up` | - | Half page up |
| `half-page-down` | - | Half page down |
| `offset-up` | - | Scroll view up (like Vim's CTRL-Y) |
| `offset-down` | - | Scroll view down (like Vim's CTRL-E) |
| `offset-middle` | - | Center current item in view |

## Preview Actions

### Preview Control

| Action | Default Binding | Description |
|--------|-----------------|-------------|
| `toggle-preview` | - | Show/hide preview window |
| `show-preview` | - | Show preview window |
| `hide-preview` | - | Hide preview window |
| `refresh-preview` | - | Refresh preview content |
| `preview(cmd)` | - | Execute preview command |

### Preview Navigation

| Action | Default Binding | Description |
|--------|-----------------|-------------|
| `preview-up` | `shift-up` | Scroll preview up |
| `preview-down` | `shift-down` | Scroll preview down |
| `preview-page-up` | - | Preview page up |
| `preview-page-down` | - | Preview page down |
| `preview-half-page-up` | - | Preview half page up |
| `preview-half-page-down` | - | Preview half page down |
| `preview-top` | - | Scroll to preview top |
| `preview-bottom` | - | Scroll to preview bottom |
| `toggle-preview-wrap` | - | Toggle line wrap in preview |

### Preview Window Options

| Action | Description |
|--------|-------------|
| `change-preview(cmd)` | Change preview command |
| `change-preview-window(opts)` | Change preview window options |
| `change-preview-label(str)` | Change preview label |
| `transform-preview-label(cmd)` | Transform label with command output |

## Query Actions

| Action | Default Binding | Description |
|--------|-----------------|-------------|
| `clear-query` | - | Clear query string |
| `change-query(str)` | - | Set query to string |
| `replace-query` | - | Replace query with current selection |
| `transform-query(cmd)` | - | Transform query with command output |
| `search(str)` | - | Trigger fzf search with string |
| `transform-search(cmd)` | - | Search with command output |

### Line Editing

| Action | Default Binding | Description |
|--------|-----------------|-------------|
| `backward-char` | `ctrl-b`, `left` | Move cursor left |
| `forward-char` | `ctrl-f`, `right` | Move cursor right |
| `backward-word` | `alt-b`, `shift-left` | Move to previous word |
| `forward-word` | `alt-f`, `shift-right` | Move to next word |
| `beginning-of-line` | `ctrl-a`, `home` | Move to line start |
| `end-of-line` | `ctrl-e`, `end` | Move to line end |
| `backward-delete-char` | `ctrl-h`, `bspace` | Delete char before cursor |
| `delete-char` | `del` | Delete char at cursor |
| `backward-kill-word` | `alt-bs` | Delete word before cursor |
| `kill-word` | `alt-d` | Delete word after cursor |
| `kill-line` | - | Delete to end of line |
| `unix-line-discard` | `ctrl-u` | Delete entire line |
| `unix-word-rubout` | `ctrl-w` | Delete word (Unix style) |
| `yank` | `ctrl-y` | Paste killed text |
| `put(str)` | - | Insert string at cursor |

## Multi-Select Actions

| Action | Default Binding | Description |
|--------|-----------------|-------------|
| `toggle` | `right-click` | Toggle selection of current item |
| `toggle+up` | `shift-tab` | Toggle and move up |
| `toggle+down` | `tab` | Toggle and move down |
| `toggle-in` | - | Toggle based on layout direction |
| `toggle-out` | - | Toggle based on layout direction |
| `select` | - | Select current item |
| `deselect` | - | Deselect current item |
| `select-all` | - | Select all matches |
| `deselect-all` | - | Deselect all matches |
| `toggle-all` | - | Toggle all matches |
| `clear-multi` | - | Clear all selections |
| `change-multi` | - | Enable multi-select with no limit |
| `change-multi(N)` | - | Enable with limit N (0 to disable) |

## Display Actions

### UI Elements

| Action | Description |
|--------|-------------|
| `change-prompt(str)` | Change prompt text |
| `transform-prompt(cmd)` | Transform prompt with command |
| `change-header(str)` | Change header text |
| `transform-header(cmd)` | Transform header with command |
| `change-border-label(str)` | Change border label |
| `transform-border-label(cmd)` | Transform border label |
| `change-list-label(str)` | Change list label |
| `change-input-label(str)` | Change input label |
| `change-header-label(str)` | Change header label |
| `change-ghost(str)` | Change ghost text |
| `change-pointer(str)` | Change pointer character |
| `change-nth(expr)` | Change --nth option |

### Visibility Toggles

| Action | Description |
|--------|-------------|
| `toggle-header` | Toggle header visibility |
| `show-header` | Show header |
| `hide-header` | Hide header |
| `toggle-input` | Toggle input visibility |
| `show-input` | Show input |
| `hide-input` | Hide input |
| `clear-screen` | Clear and redraw screen |

### Behavior Toggles

| Action | Description |
|--------|-------------|
| `toggle-sort` | Toggle sorting |
| `toggle-search` | Toggle search functionality |
| `enable-search` | Enable search |
| `disable-search` | Disable search |
| `toggle-wrap` | Toggle line wrap |
| `toggle-hscroll` | Toggle horizontal scroll |
| `toggle-track` | Toggle global tracking |
| `track-current` | Track current item |
| `toggle-track-current` | Toggle tracking current item |
| `toggle-raw` | Toggle raw mode |
| `enable-raw` | Enable raw mode |
| `disable-raw` | Disable raw mode |
| `toggle-multi-line` | Toggle multi-line display |

## Command Execution

### execute()

Run command without leaving fzf:

```bash
fzf --bind 'enter:execute(less {})'
fzf --bind 'ctrl-e:execute(vim {} < /dev/tty > /dev/tty)'
```

### execute-silent()

Run command silently (no screen switch):

```bash
fzf --bind 'ctrl-y:execute-silent(echo {} | pbcopy)'
```

### become()

Replace fzf with command (using execve):

```bash
fzf --bind 'enter:become(vim {})'
fzf --bind 'enter:become(vim {1} +{2})'  # With field expressions
```

**Advantages over `$(fzf)`:**
- No empty file opened on CTRL-C
- No empty file on enter with no results
- Handles multiple selections with spaces

### reload()

Dynamically update input list:

```bash
fzf --bind 'ctrl-r:reload(ps -ef)'
fzf --bind 'change:reload(rg --line-number {q} || true)'
```

### reload-sync()

Synchronous reload (waits for command completion):

```bash
fzf --bind 'load:reload-sync(slow-command)+unbind(load)'
```

### print()

Add to output queue (printed on normal exit):

```bash
fzf --bind 'ctrl-y:print(selected)+accept'
```

## Transform Actions

Transform actions run external commands and use output to modify state.

### Basic Transform

```bash
# Transform header based on focused item
fzf --bind 'focus:transform-header:file --brief {}'

# Conditional actions
fzf --bind 'enter:transform:[[ -n {} ]] && echo accept || echo abort'
```

### Transform Actions List

| Action | Description |
|--------|-------------|
| `transform(cmd)` | Run cmd, output is action sequence |
| `transform-query(cmd)` | Set query to command output |
| `transform-prompt(cmd)` | Set prompt to command output |
| `transform-header(cmd)` | Set header to command output |
| `transform-border-label(cmd)` | Set border label |
| `transform-preview-label(cmd)` | Set preview label |
| `transform-list-label(cmd)` | Set list label |
| `transform-input-label(cmd)` | Set input label |
| `transform-header-label(cmd)` | Set header label |
| `transform-ghost(cmd)` | Set ghost text |
| `transform-pointer(cmd)` | Set pointer |
| `transform-nth(cmd)` | Set nth option |
| `transform-search(cmd)` | Trigger search with output |

### Background Transform

Each transform has a `bg-transform*` variant for async execution:

```bash
# Won't block UI
fzf --bind 'focus:bg-transform-header:slow-command {}'

# Cancel running background transforms
fzf --bind 'ctrl-c:bg-cancel'
```

## Binding Management

| Action | Description |
|--------|-------------|
| `unbind(keys)` | Unbind specified keys/events |
| `rebind(keys)` | Rebind previously unbound keys |
| `toggle-bind` | Toggle all custom bindings |
| `trigger(keys)` | Trigger actions bound to keys |

Example: Mode switching

```bash
fzf --bind 'ctrl-f:unbind(change)+enable-search+rebind(ctrl-r)' \
    --bind 'ctrl-r:unbind(ctrl-r)+disable-search+reload(cmd)+rebind(change)'
```

## Events

Events trigger actions automatically based on state changes.

| Event | Triggered When |
|-------|----------------|
| `start` | fzf starts (list may not be ready) |
| `load` | Input stream complete, initial processing done |
| `change` | Query string changes |
| `focus` | Focused item changes |
| `result` | Result list updates |
| `resize` | Terminal size changes |
| `one` | Exactly one match |
| `zero` | No matches |
| `multi` | Multi-selection changes |
| `backward-eof` | Backspace on empty query |
| `jump` | Successfully jumped in jump mode |
| `jump-cancel` | Jump mode cancelled |
| `click-header` | Mouse click in header |
| `click-footer` | Mouse click in footer |

### Event Examples

```bash
# Auto-accept single match
fzf --bind 'one:accept'

# Reload on empty results
fzf --bind 'zero:reload(alternative-cmd)'

# Update header on focus change
fzf --bind 'focus:transform-header:file --brief {}'

# Initialize after load
fzf --sync --bind 'load:select-all'
```

## Miscellaneous Actions

| Action | Description |
|--------|-------------|
| `ignore` | Do nothing |
| `bell` | Ring terminal bell |
| `jump` | EasyMotion-like 2-keystroke movement |
| `exclude` | Exclude current item from results |
| `exclude-multi` | Exclude selected items from results |

## Environment Variables in Actions

Available in command execution:

| Variable | Description |
|----------|-------------|
| `FZF_QUERY` | Current query string |
| `FZF_ACTION` | Name of last action |
| `FZF_KEY` | Name of last key pressed |
| `FZF_PROMPT` | Current prompt string |
| `FZF_MATCH_COUNT` | Number of matches |
| `FZF_SELECT_COUNT` | Number of selections |
| `FZF_TOTAL_COUNT` | Total items |
| `FZF_POS` | Current position (1-based) |
| `FZF_LINES` | fzf height in lines |
| `FZF_COLUMNS` | fzf width in columns |
| `FZF_PORT` | HTTP server port (with --listen) |
