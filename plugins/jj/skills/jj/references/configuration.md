# Configuration Reference

Comprehensive reference for jj configuration options, templates, filesets, and aliases.

## Table of Contents

- [Config Files](#config-files)
- [User Settings](#user-settings)
- [UI Settings](#ui-settings)
  - [Basic UI](#basic-ui)
  - [Editor Settings](#editor-settings)
  - [Colors and Styles](#colors-and-styles)
  - [Diff Options](#diff-options)
  - [External Diff Tools](#external-diff-tools)
- [Aliases](#aliases)
- [Templates](#templates)
- [Filesets](#filesets)
- [Git Settings](#git-settings)
- [Signing](#signing)

## Config Files

jj loads configuration from multiple sources (in order of precedence):

1. **Built-in** - Cannot be edited
2. **User** - `~/.config/jj/config.toml` or `~/.jjconfig.toml`
3. **Repo** - `.jj/repo/config.toml`
4. **Workspace** - `.jj/workspace-config.toml`
5. **Command-line** - `--config key=value`

```bash
jj config path --user      # Show user config path
jj config edit --user      # Edit user config
jj config edit --repo      # Edit repo config
jj config list             # Show all config values
jj config get <key>        # Get specific value
```

## User Settings

```toml
[user]
name = "Your Name"
email = "your@email.com"
```

## UI Settings

### Basic UI

```toml
[ui]
# Color output: always, never, auto, debug
color = "auto"

# Default command when running 'jj' with no args
default-command = "log"
# Or with arguments:
default-command = ["log", "--reversed"]

# Pager command
pager = "less -FRX"

# Diff format: :color-words, :git, :summary, :stat, :types, :name-only
diff-formatter = ":color-words"

# Movement commands (next/prev) edit instead of creating new commit
movement.edit = false
```

### Editor Settings

The editor is used for commands that need text input: `jj describe`, `jj squash` (when combining messages), `jj commit`, `jj split` (for commit messages).

**Priority order** (highest to lowest):

```
$JJ_EDITOR > ui.editor > $VISUAL > $EDITOR
```

If none are set, defaults to `nano` (Unix) or `notepad` (Windows).

**Terminal editors:**

```toml
[ui]
editor = "vim"
editor = "nvim"
editor = "nano"
editor = "emacs"
editor = "micro"
editor = "helix"
```

**GUI editors** (require wait flag to block until closed):

```toml
[ui]
editor = "code -w"           # VS Code
editor = "code.cmd -w"       # VS Code on Windows
editor = "subl -n -w"        # Sublime Text
editor = "bbedit -w"         # BBEdit
editor = "mate -w"           # TextMate
editor = "idea --temp-project --wait"  # IntelliJ IDEA

# Array syntax for complex commands:
editor = ["C:/Program Files/Notepad++/notepad++.exe",
    "-multiInst", "-notabbar", "-nosession", "-noPlugin"]
```

**Quick config commands:**

```bash
# Set editor in user config
jj config set --user ui.editor "nvim"

# Set editor in repo config
jj config set --repo ui.editor "code -w"

# Check current editor setting
jj config get ui.editor
```

**Editor vs Diff-Editor:**

| Setting | Used For | Default |
|---------|----------|---------|
| `ui.editor` | Commit messages (`describe`, `squash`, `commit`) | `nano` |
| `ui.diff-editor` | Interactive diff editing (`split`, `squash -i`, `diffedit`) | `:builtin` |
| `ui.merge-editor` | Conflict resolution (`resolve`) | (none) |

### Colors and Styles

```toml
[colors]
# Simple foreground color
commit_id = "green"
change_id = "magenta"

# Hex colors
bookmark = "#ff1525"

# Full style specification
commit_id = { fg = "green", bg = "black", bold = true }
change_id = { underline = true, italic = true }

# Combined labels (like CSS selectors)
"working_copy commit_id" = { underline = true }
"conflict description" = "red"

# Diff colors
"diff removed" = "red"
"diff added" = "green"
"diff removed token" = { bg = "#221111", underline = false }
"diff added token" = { bg = "#002200", underline = false }
```

### Diff Options

```toml
[diff.color-words]
# Max removed/added alternation to inline (-1 = all)
max-inline-alternation = 3
# Lines of context
context = 3

[diff.git]
context = 3
```

### External Diff Tools

```toml
[ui]
diff-formatter = ["difft", "--color=always", "$left", "$right"]
# Or reference a named tool:
diff-formatter = "difftastic"

[merge-tools.difftastic]
program = "difft"
diff-args = ["--color=always", "$left", "$right"]
diff-invocation-mode = "dir"  # or "file-by-file"
```

## Aliases

### Command Aliases

```toml
[aliases]
# Simple alias
l = ["log", "-r", "@::"]

# Complex alias
show-tree = ["log", "-r", "@::", "--no-graph", "-T", "commit_id.short() ++ ' ' ++ description.first_line()"]

# External command (via util exec)
my-script = ["util", "exec", "--", "my-jj-script"]

# Inline script
format = ["util", "exec", "--", "bash", "-c", """
set -euo pipefail
jj fix
""", ""]
```

### Revset Aliases

```toml
[revset-aliases]
# Custom revsets
'wip' = 'description(exact:"") & mine()'
'stacked' = 'trunk()..@'
'recent' = 'ancestors(@, 20) & mine()'
'feature(x)' = 'bookmarks(glob:"feature-" ++ x ++ "*")::'

# Override built-in trunk() detection
'trunk()' = 'latest(remote_bookmarks(exact:"main", exact:"origin") | remote_bookmarks(exact:"master", exact:"origin"))'

# Customize immutable commits
'immutable_heads()' = 'trunk() | tags()'
```

### Template Aliases

```toml
[template-aliases]
# Custom formatting
'format_short_id(id)' = 'id.shortest(8)'
'format_timestamp(ts)' = 'ts.ago()'

# Custom commit format
'my_log' = '''
change_id.short() ++ " " ++
if(description, description.first_line(), "(no description)") ++
if(conflict, " CONFLICT", "")
'''
```

## Templates

Templates are a functional language for customizing output.

### Log Template

```toml
[templates]
log = 'builtin_log_oneline'
# Or custom:
log = '''
separate(" ",
  format_short_change_id_with_hidden_and_divergent_info(self),
  format_short_commit_id(commit_id),
  bookmarks,
  tags,
  if(conflict, label("conflict", "conflict")),
  if(empty, label("empty", "(empty)")),
  if(description, description.first_line(), description_placeholder),
) ++ "\n"
'''
```

### Draft Description Template

```toml
[templates]
draft_commit_description = '''
concat(
  builtin_draft_commit_description,
  "\nJJ: ignore-rest\n",
  diff.git(),
)
'''

[template-aliases]
default_commit_description = '''
"

Closes #NNNN
"
'''
```

### Commit Trailers

```toml
[templates]
commit_trailers = '''
format_signed_off_by_trailer(self)
++ if(!trailers.contains_key("Change-Id"), format_gerrit_change_id_trailer(self))
'''
```

### Template Syntax

```
# Literals
"string"
true / false
42

# Operators
x ++ y           # Concatenate
x && y           # Logical and
x || y           # Logical or
!x               # Logical not
x == y           # Equality

# Conditionals
if(condition, then, else)

# Functions
separate(sep, items...)   # Join non-empty with separator
concat(items...)          # Join all items
coalesce(items...)        # First non-empty
surround(prefix, suffix, content)  # Wrap if non-empty
label(name, content)      # Apply color label
indent(prefix, content)   # Indent lines
fill(width, content)      # Word wrap
```

### Commit Methods

Available in log/show templates:

```
self.commit_id()
self.change_id()
self.description()
self.author()
self.committer()
self.parents()
self.bookmarks()
self.tags()
self.working_copies()
self.conflict()
self.empty()
self.immutable()
self.divergent()
self.hidden()
self.mine()
self.contained_in(revset)
self.diff([fileset])
```

## Filesets

Filesets select files for commands like `jj diff`, `jj split`, `jj squash`.

### Patterns

```bash
# Path prefix (default)
jj diff src                    # Files under src/

# Exact file
jj diff 'file:README.md'

# Glob patterns
jj diff 'glob:*.rs'            # .rs in current dir
jj diff 'glob:**/*.rs'         # All .rs files
jj diff 'glob-i:*.TXT'         # Case-insensitive

# Root-relative (from repo root)
jj diff 'root:src'
jj diff 'root-glob:**/*.rs'
```

### Operators

```bash
# Negation
jj diff '~Cargo.lock'          # Everything except Cargo.lock

# Intersection
jj diff 'src & glob:**/*.rs'   # Rust files in src/

# Difference
jj diff 'src ~ glob:**/*.rs'   # Non-Rust files in src/

# Union
jj diff 'glob:*.rs | glob:*.toml'
```

### Functions

```bash
all()                          # All files
none()                         # No files
```

### Examples

```bash
# Diff excluding lock files
jj diff '~Cargo.lock'

# Split: put all except foo in first commit
jj split '~foo'

# List non-Rust files in src
jj file list 'src ~ glob:**/*.rs'

# Squash only specific files
jj squash 'glob:*.md'
```

## Git Settings

```toml
[git]
# Auto-local-bookmark for new remote bookmarks
auto-local-bookmark = true

# Default push/fetch remote
push = "origin"
fetch = "origin"

# Push bookmark naming template
push-bookmark-prefix = "push-"

# Private commits (won't be pushed)
private-commits = "description(glob:'wip:*')"

# Colocate by default
colocate = true

# Shallow clone depth
shallow-clone-depth = 0  # 0 = full clone

# Fetch tags
fetch-tags = "included"  # all, included, none

# Abandon unreachable commits from remote
abandon-unreachable-commits = true
```

## Signing

```toml
[signing]
# Enable signing
sign-all = false

# Signing backend: gpg, ssh, none
backend = "gpg"

# GPG settings
[signing.backends.gpg]
program = "gpg"
# Allow expired keys
allow-expired-keys = false

# SSH settings
[signing.backends.ssh]
program = "ssh-keygen"
# Allowed signers file
allowed-signers = "~/.ssh/allowed_signers"
# Key to use
key = "~/.ssh/id_ed25519.pub"
```

## Immutable Commits

```toml
[revset-aliases]
# Default: trunk and tags are immutable
'immutable_heads()' = 'trunk() | tags()'

# More restrictive: only trunk
'immutable_heads()' = 'trunk()'

# Include release branches
'immutable_heads()' = 'trunk() | tags() | bookmarks(glob:"release-*")'
```

## Fix Tools (Formatters)

```toml
[fix.tools.rustfmt]
command = ["rustfmt", "--emit=stdout"]
patterns = ["glob:'**/*.rs'"]

[fix.tools.black]
command = ["black", "-", "--stdin-filename=$path"]
patterns = ["glob:'**/*.py'"]

[fix.tools.prettier]
command = ["prettier", "--stdin-filepath=$path"]
patterns = ["glob:'**/*.{js,ts,jsx,tsx,json,md}'"]
```

## Merge Tools

```toml
[merge-tools.meld]
program = "meld"
merge-args = ["$left", "$base", "$right", "-o", "$output"]
edit-args = ["$left", "$right"]

[merge-tools.vimdiff]
program = "vim"
merge-args = ["-d", "$left", "$base", "$right", "$output"]
merge-tool-edits-conflict-markers = true

[ui]
merge-editor = "meld"
diff-editor = ":builtin"
```

## Snapshot Settings

```toml
[snapshot]
# Max file size to track (bytes)
max-new-file-size = "1MiB"

# Auto-track patterns (default: all)
auto-track = "all()"
# Or selective:
auto-track = "glob:**/*.rs"

# Watchman integration
use-watchman = "if-available"
```

## Debug Settings

```toml
[debug]
# Randomize commit IDs (for testing)
randomness-seed = ""
```
