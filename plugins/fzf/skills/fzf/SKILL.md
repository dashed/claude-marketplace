---
name: fzf
description: Command-line fuzzy finder for interactive filtering of any list. Use when interactively selecting files, searching command history (CTRL-R), creating selection interfaces in scripts, building interactive menus, or integrating fuzzy search with tools like ripgrep, fd, and git. Triggers on mentions of fzf, fuzzy finder, ** completion, interactive filtering, or shell keybindings CTRL-T/CTRL-R/ALT-C.
---

# fzf - Command-Line Fuzzy Finder

## Overview

fzf is a general-purpose command-line fuzzy finder. It reads a list of items from STDIN, allows interactive selection using fuzzy matching, and outputs the selected item(s) to STDOUT. Think of it as an interactive grep.

**Key characteristics:**
- **Fast**: Processes millions of items instantly
- **Portable**: Single binary, works everywhere
- **Versatile**: Customizable via event-action binding mechanism
- **Integrated**: Built-in shell integrations for bash, zsh, and fish

## When to Use This Skill

Use fzf when:
- **Selecting files interactively**: `vim $(fzf)` or fuzzy completion with `**<TAB>`
- **Searching command history**: CTRL-R for fuzzy history search
- **Navigating directories**: ALT-C to cd into selected directory
- **Building interactive scripts**: Create selection menus for any list
- **Filtering output**: Pipe any command output through fzf
- **Integrating with other tools**: ripgrep, fd, git, etc.

## Prerequisites

**CRITICAL**: Before proceeding, you MUST verify that fzf is installed:

```bash
fzf --version
```

**If fzf is not installed:**
- **DO NOT** attempt to install it automatically
- **STOP** and inform the user that fzf is required
- **RECOMMEND** manual installation with the following instructions:

```bash
# macOS
brew install fzf

# Debian/Ubuntu
sudo apt install fzf

# Arch Linux
sudo pacman -S fzf

# From source
git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
~/.fzf/install

# Other systems: see https://github.com/junegunn/fzf#installation
```

**If fzf is not available, exit gracefully and do not proceed with the workflow below.**

## Shell Integration

fzf provides shell integration that enables powerful keybindings (CTRL-T, CTRL-R, ALT-C) and fuzzy completion (`**<TAB>`). These features require the user to configure their shell.

**Note:** Shell integration setup is the user's responsibility. If keybindings don't work, **RECOMMEND** the user add the appropriate line to their shell config:

```bash
# Bash (~/.bashrc)
eval "$(fzf --bash)"

# Zsh (~/.zshrc)
source <(fzf --zsh)

# Fish (~/.config/fish/config.fish)
fzf --fish | source
```

### Key Bindings (requires shell integration)

| Key | Function | Description |
|-----|----------|-------------|
| `CTRL-T` | File selection | Paste selected files/directories onto command line |
| `CTRL-R` | History search | Fuzzy search command history |
| `ALT-C` | Directory jump | cd into selected directory |

**CTRL-R extras:**
- Press `CTRL-R` again to toggle sort by relevance
- Press `ALT-R` to toggle raw mode (see surrounding items)
- Press `CTRL-/` or `ALT-/` to toggle line wrapping

### Fuzzy Completion (`**<TAB>`)

Trigger fuzzy completion with `**` followed by TAB:

```bash
# Files under current directory
vim **<TAB>

# Files under specific directory
vim ../fzf**<TAB>

# Directories only
cd **<TAB>

# Process IDs (for kill)
kill -9 **<TAB>

# SSH hostnames
ssh **<TAB>

# Environment variables
export **<TAB>
```

## Search Syntax

fzf uses extended-search mode by default. Multiple search terms are separated by spaces.

| Token | Match Type | Description |
|-------|------------|-------------|
| `sbtrkt` | Fuzzy match | Items matching `sbtrkt` |
| `'wild` | Exact match | Items containing `wild` exactly |
| `'wild'` | Exact boundary | Items with `wild` at word boundaries |
| `^music` | Prefix match | Items starting with `music` |
| `.mp3$` | Suffix match | Items ending with `.mp3` |
| `!fire` | Inverse match | Items NOT containing `fire` |
| `!^music` | Inverse prefix | Items NOT starting with `music` |
| `!.mp3$` | Inverse suffix | Items NOT ending with `.mp3` |

**OR operator**: Use `|` to match any of several patterns:
```bash
# Files starting with 'core' and ending with go, rb, or py
^core go$ | rb$ | py$
```

**Escape spaces**: Use `\ ` to match literal space characters.

## Basic Usage

### Simple Selection

```bash
# Select a file and open in vim
vim $(fzf)

# Safer with xargs (handles spaces, cancellation)
fzf --print0 | xargs -0 -o vim

# Using become() action (best approach)
fzf --bind 'enter:become(vim {})'
```

### Multi-Select

```bash
# Enable multi-select with -m
fzf -m

# Select with TAB, deselect with Shift-TAB
# Selected items printed on separate lines
```

### Preview Window

```bash
# Basic preview
fzf --preview 'cat {}'

# With syntax highlighting (requires bat)
fzf --preview 'bat --color=always {}'

# Customize preview window position/size
fzf --preview 'cat {}' --preview-window=right,50%
fzf --preview 'cat {}' --preview-window=up,40%,border-bottom
```

## Display Modes

### Height Mode

```bash
# Use 40% of terminal height
fzf --height 40%

# Adaptive height (shrinks for small lists)
seq 5 | fzf --height ~100%

# With layout options
fzf --height 40% --layout reverse --border
```

### tmux Mode

```bash
# Open in tmux popup (requires tmux 3.3+)
fzf --tmux center         # Center, 50% width/height
fzf --tmux 80%            # Center, 80% width/height
fzf --tmux left,40%       # Left side, 40% width
fzf --tmux bottom,30%     # Bottom, 30% height
```

## Essential Options

### Layout and Appearance

```bash
--height=HEIGHT[%]     # Non-fullscreen mode
--layout=reverse       # Display from top (default: bottom)
--border[=STYLE]       # rounded, sharp, bold, double, block
--margin=MARGIN        # Margin around finder
--padding=PADDING      # Padding inside border
--info=STYLE           # default, inline, hidden
```

### Search Behavior

```bash
-e, --exact            # Exact match (disable fuzzy)
-i                     # Case-insensitive
+i                     # Case-sensitive
--scheme=SCHEME        # default, path, history
--algo=TYPE            # v2 (quality), v1 (performance)
```

### Input/Output

```bash
-m, --multi            # Enable multi-select
--read0                # Read NUL-delimited input
--print0               # Print NUL-delimited output
--ansi                 # Enable ANSI color processing
```

### Field Processing

```bash
--delimiter=STR        # Field delimiter (default: AWK-style)
--nth=N[,..]           # Limit search to specific fields
--with-nth=N[,..]      # Transform display of each line
```

## Event Bindings

Customize behavior with `--bind`:

```bash
# Basic syntax
fzf --bind 'KEY:ACTION'
fzf --bind 'EVENT:ACTION'
fzf --bind 'KEY:ACTION1+ACTION2'  # Chain actions

# Examples
fzf --bind 'ctrl-a:select-all'
fzf --bind 'ctrl-d:deselect-all'
fzf --bind 'ctrl-/:toggle-preview'
fzf --bind 'enter:become(vim {})'
```

### Key Actions (Selection)

| Action | Description |
|--------|-------------|
| `accept` | Accept current selection |
| `abort` | Abort and exit |
| `toggle` | Toggle selection of current item |
| `select-all` | Select all matches |
| `deselect-all` | Deselect all |
| `toggle-all` | Toggle all selections |

### Useful Actions

| Action | Description |
|--------|-------------|
| `reload(cmd)` | Reload list from command |
| `become(cmd)` | Replace fzf with command |
| `execute(cmd)` | Run command, return to fzf |
| `execute-silent(cmd)` | Run command silently |
| `preview(cmd)` | Change preview command |
| `toggle-preview` | Show/hide preview |
| `change-prompt(str)` | Change prompt string |

### Events

| Event | Triggered When |
|-------|----------------|
| `start` | fzf starts |
| `load` | Input loading completes |
| `change` | Query string changes |
| `focus` | Focused item changes |
| `result` | Result list updates |

For complete action reference, see [references/actions.md](references/actions.md).

## Environment Variables

### Core Configuration

```bash
# Default command when input is TTY
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'

# Default options (applied to all fzf invocations)
export FZF_DEFAULT_OPTS='--height 40% --layout reverse --border'

# Options file (alternative to FZF_DEFAULT_OPTS)
export FZF_DEFAULT_OPTS_FILE=~/.fzfrc
```

### Shell Integration Variables

```bash
# CTRL-T options
export FZF_CTRL_T_COMMAND="fd --type f"
export FZF_CTRL_T_OPTS="--preview 'bat --color=always {}'"

# CTRL-R options
export FZF_CTRL_R_OPTS="--bind 'ctrl-y:execute-silent(echo -n {2..} | pbcopy)+abort'"

# ALT-C options
export FZF_ALT_C_COMMAND="fd --type d"
export FZF_ALT_C_OPTS="--preview 'tree -C {}'"
```

### Completion Customization

```bash
# Change trigger sequence (default: **)
export FZF_COMPLETION_TRIGGER='~~'

# Completion options
export FZF_COMPLETION_OPTS='--border --info=inline'
```

## Common Patterns

### Find and Edit Files

```bash
# Using fd for better performance
fd --type f | fzf --preview 'bat --color=always {}' | xargs -o vim

# Or with become()
fd --type f | fzf --preview 'bat --color=always {}' --bind 'enter:become(vim {})'
```

### Search File Contents (with ripgrep)

```bash
# Basic ripgrep integration
rg --line-number . | fzf --delimiter : --preview 'bat --color=always {1} --highlight-line {2}'

# Open result in vim at line
rg --line-number . | fzf --delimiter : --bind 'enter:become(vim {1} +{2})'
```

### Git Integration

```bash
# Select git branch
git branch | fzf | xargs git checkout

# Select commit
git log --oneline | fzf --preview 'git show {1}' | cut -d' ' -f1

# Stage files interactively
git status -s | fzf -m | awk '{print $2}' | xargs git add
```

### Dynamic List Reloading

```bash
# Reload process list with CTRL-R
ps -ef | fzf --bind 'ctrl-r:reload(ps -ef)' --header 'Press CTRL-R to reload'

# Toggle between files and directories
fd | fzf --bind 'ctrl-d:reload(fd --type d)' --bind 'ctrl-f:reload(fd --type f)'
```

### Interactive ripgrep Launcher

```bash
# fzf as ripgrep frontend (search updates on typing)
RG_PREFIX="rg --column --line-number --no-heading --color=always"
fzf --ansi --disabled \
    --bind "start:reload:$RG_PREFIX ''" \
    --bind "change:reload:$RG_PREFIX {q} || true" \
    --bind 'enter:become(vim {1} +{2})' \
    --delimiter :
```

## Placeholders

Use in `--preview`, `--bind`, etc.:

| Placeholder | Description |
|-------------|-------------|
| `{}` | Current selection (quoted) |
| `{+}` | All selected items (space-separated) |
| `{q}` | Current query string |
| `{n}` | Zero-based index of current item |
| `{1}`, `{2}`, etc. | Nth field (with --delimiter) |
| `{-1}` | Last field |
| `{1..3}` | Fields 1 through 3 |
| `{2..}` | Fields 2 to end |

**Flags:**
- `{+}` - All selected items
- `{f}` - Write to temp file (for large lists)
- `{r}` - Raw (unquoted) output

## Advanced Topics

For detailed documentation on advanced features, see:

- [references/actions.md](references/actions.md) - Complete list of bindable actions
- [references/options.md](references/options.md) - Full options reference
- [references/integrations.md](references/integrations.md) - ripgrep, fd, git, bat integrations

## Troubleshooting

**"Command not found: fzf"**
- fzf is not installed. See Prerequisites section for manual installation instructions
- Do NOT attempt automatic installation

**Shell keybindings not working (CTRL-T, CTRL-R, ALT-C):**
- Shell integration must be configured by the user
- RECOMMEND adding the appropriate line to shell config (see Shell Integration section)
- For bash, must be sourced after any PS1 modifications

**Performance issues:**
- Avoid `--ansi` in `FZF_DEFAULT_OPTS` (slows initial scan)
- Use `--nth` sparingly (requires tokenization)
- Prefer string `--delimiter` over regex

**Preview not showing:**
- Check preview command syntax
- Use `{}` placeholder for current selection
- Test preview command manually first

**CTRL-R not finding old commands:**
- fzf searches shell history, not history file
- Increase `HISTSIZE` and `HISTFILESIZE`

## Resources

- **Man page**: `man fzf` or `fzf --man`
- **Wiki examples**: https://github.com/junegunn/fzf/wiki/examples
- **Advanced examples**: https://github.com/junegunn/fzf/blob/master/ADVANCED.md
- **Theme playground**: https://vitormv.github.io/fzf-themes/
- **fzf-git.sh**: https://github.com/junegunn/fzf-git.sh (git keybindings)
