# Commands Reference

Complete reference for jj commands and their options.

## Table of Contents

- [Repository Setup](#repository-setup)
- [Status and History](#status-and-history)
- [Creating and Editing Commits](#creating-and-editing-commits)
- [History Rewriting](#history-rewriting)
- [Bookmarks (Branches)](#bookmarks-branches)
- [Git Operations](#git-operations)
- [Operation Log](#operation-log)
- [File Operations](#file-operations)
- [Workspaces](#workspaces)
- [Configuration](#configuration)

## Repository Setup

### `jj git clone`

Clone a Git repository:

```bash
jj git clone <url> [destination]
jj git clone --colocate <url>     # Allow git commands (default)
jj git clone --no-colocate <url>  # jj-only repo
jj git clone --branch <branch>    # Clone specific branch
jj git clone --depth <n>          # Shallow clone
```

### `jj git init`

Initialize a new repository:

```bash
jj git init                       # New colocated repo (default)
jj git init --no-colocate         # New jj-only repo
jj git init --git-repo <path>     # Use existing git repo as backend
```

## Status and History

### `jj status` (alias: `st`)

Show working copy status:

```bash
jj status
jj st [paths...]                  # Status for specific paths
```

### `jj log`

Show commit history:

```bash
jj log                            # Default: mutable commits
jj log -r <revset>                # Specific revisions
jj log -r '::'                    # All commits
jj log -n 10                      # Limit to 10 commits
jj log -p                         # Show patches
jj log -s                         # Summary (files changed)
jj log --stat                     # Show diffstat
jj log --no-graph                 # Flat list, no graph
jj log --reversed                 # Oldest first
jj log -T <template>              # Custom template
jj log [paths...]                 # Commits touching paths
```

### `jj show`

Show commit details:

```bash
jj show                           # Current working copy
jj show <rev>                     # Specific revision
jj show -s                        # Summary only
jj show -p                        # Patch (default)
jj show --stat                    # Diffstat
jj show --git                     # Git-format diff
```

### `jj diff`

Show changes:

```bash
jj diff                           # Changes in working copy
jj diff -r <rev>                  # Changes in revision vs parent
jj diff --from <rev>              # From specific revision
jj diff --to <rev>                # To specific revision
jj diff --from <A> --to <B>       # Between two revisions
jj diff -s                        # Summary
jj diff --stat                    # Diffstat
jj diff --git                     # Git format
jj diff --color-words             # Word-level diff
jj diff [paths...]                # Specific paths only
```

## Creating and Editing Commits

### `jj new`

Create a new commit:

```bash
jj new                            # New commit on working copy parent
jj new <rev>                      # New commit on specific revision
jj new <A> <B>                    # Merge commit with multiple parents
jj new -m "message"               # With description
jj new --no-edit                  # Don't make it working copy
jj new -A <rev>                   # Insert after revision
jj new -B <rev>                   # Insert before revision
```

### `jj describe` (alias: `desc`)

Edit commit description:

```bash
jj describe                       # Edit working copy description
jj describe <rev>                 # Edit specific revision
jj describe -m "message"          # Set message directly
jj describe --stdin               # Read from stdin
```

### `jj edit`

Switch working copy to edit existing commit:

```bash
jj edit <rev>                     # Edit specific revision
```

### `jj commit` (alias: `ci`)

Finalize working copy and create new commit:

```bash
jj commit                         # Describe and create new
jj commit -m "message"            # With message
jj commit -i                      # Interactive selection
jj commit [paths...]              # Only specified paths
```

## History Rewriting

### `jj squash`

Move changes into parent:

```bash
jj squash                         # All changes to parent
jj squash -r <rev>                # From specific revision
jj squash -i                      # Interactive selection
jj squash [paths...]              # Only specific paths
jj squash --from <A> --into <B>   # Between arbitrary commits
jj squash -m "message"            # Set combined description
jj squash -k                      # Keep source (don't abandon)
```

### `jj split`

Split commit into two:

```bash
jj split                          # Interactive split of working copy
jj split -r <rev>                 # Split specific revision
jj split [paths...]               # Put paths in first commit
jj split -i                       # Interactive mode
jj split -p                       # Parallel (sibling) commits
jj split -m "message"             # First commit message
```

### `jj rebase`

Move commits to different parents:

```bash
# What to rebase:
jj rebase -b <rev>                # Branch containing rev (default: -b @)
jj rebase -s <rev>                # Source and descendants
jj rebase -r <rev>                # Only revision (not descendants)

# Where to rebase:
jj rebase -d <dest>               # Onto destination
jj rebase -A <rev>                # Insert after
jj rebase -B <rev>                # Insert before

# Examples:
jj rebase -d main                 # Rebase current branch onto main
jj rebase -s X -d Y               # Rebase X and descendants onto Y
jj rebase -r X -d Y               # Rebase only X onto Y
jj rebase -r X -A Y               # Insert X after Y
jj rebase -r X -B Y               # Insert X before Y

# Options:
jj rebase --skip-emptied          # Abandon commits that become empty
```

### `jj diffedit`

Interactively edit commit contents:

```bash
jj diffedit                       # Edit working copy
jj diffedit -r <rev>              # Edit specific revision
jj diffedit --from <A> --to <B>   # Edit diff between revisions
jj diffedit --tool <tool>         # Use specific diff editor
jj diffedit --restore-descendants # Preserve descendant content
```

### `jj duplicate`

Copy commits:

```bash
jj duplicate                      # Duplicate working copy
jj duplicate <revs>               # Duplicate specific revisions
jj duplicate -A <rev>             # Insert duplicates after
jj duplicate -B <rev>             # Insert duplicates before
```

### `jj abandon`

Remove commits (keep content in descendants):

```bash
jj abandon                        # Abandon working copy
jj abandon <revs>                 # Abandon specific revisions
jj abandon --retain-bookmarks     # Move bookmarks to parents
```

### `jj restore`

Restore files from another revision:

```bash
jj restore                        # Restore all from parent
jj restore [paths...]             # Restore specific paths
jj restore --from <rev>           # Source revision
jj restore --into <rev>           # Destination revision
jj restore -c <rev>               # Undo changes in revision
jj restore -i                     # Interactive mode
```

### `jj parallelize`

Make commits siblings instead of parent-child:

```bash
jj parallelize <revs>             # Make revisions parallel
```

## Bookmarks (Branches)

### `jj bookmark` (alias: `b`)

Manage bookmarks:

```bash
# List
jj bookmark list
jj bookmark list -a               # Include all remotes
jj bookmark list -r <revs>        # Bookmarks at revisions

# Create/Set
jj bookmark create <name>         # At working copy
jj bookmark create <name> -r <rev>
jj bookmark set <name>            # Move to working copy
jj bookmark set <name> -r <rev>   # Move to revision
jj bookmark set <name> -r <rev> --allow-backwards  # Move to ancestor

# Modify
jj bookmark move <name>           # Move to working copy
jj bookmark move --from <rev>     # Move from revision
jj bookmark rename <old> <new>

# Delete
jj bookmark delete <name>         # Delete (will push deletion)
jj bookmark forget <name>         # Forget (won't push deletion)

# Remote tracking
jj bookmark track <name>@<remote>
jj bookmark untrack <name>@<remote>
```

## Git Operations

### `jj git fetch`

Fetch from remote:

```bash
jj git fetch                      # From default remote
jj git fetch --remote <name>      # From specific remote
jj git fetch --all-remotes        # From all remotes
jj git fetch --branch <pattern>   # Specific branches
```

### `jj git push`

Push to remote:

```bash
jj git push --bookmark <name>     # Push specific bookmark
jj git push --all                 # Push all bookmarks
jj git push --tracked             # Push all tracked
jj git push --deleted             # Push deletions
jj git push --change <rev>        # Create bookmark from change
jj git push --remote <name>       # To specific remote
jj git push --dry-run             # Show what would be pushed
jj git push --allow-new           # Allow creating new remote bookmark
```

**Flag compatibility:**

| Flags | Works? | Notes |
|-------|--------|-------|
| `--all` | ✓ | Pushes all bookmarks |
| `--tracked` | ✓ | Pushes tracked bookmarks that moved |
| `--bookmark <name>` | ✓ | Push specific bookmark |
| `--change <id>` | ✓ | Creates/pushes auto-named bookmark |
| `--all --allow-new` | ✗ | **Incompatible** |
| `--tracked --allow-new` | ✗ | **Incompatible** |
| `--bookmark <name> --allow-new` | ✓ | For new bookmarks |

### `jj git remote`

Manage remotes:

```bash
jj git remote list
jj git remote add <name> <url>
jj git remote remove <name>
jj git remote rename <old> <new>
jj git remote set-url <name> <url>
```

### `jj git import` / `jj git export`

Sync with underlying Git repo (rarely needed in colocated repos):

```bash
jj git import                     # Import Git changes to jj
jj git export                     # Export jj changes to Git
```

## Operation Log

### `jj op log`

View operation history:

```bash
jj op log                         # Full operation log
jj op log -n 10                   # Limit entries
jj op log -p                      # Show patches
jj op log -d                      # Show operation diffs
```

### `jj undo` / `jj redo`

Undo/redo operations:

```bash
jj undo                           # Undo last operation
jj redo                           # Redo after undo
```

### `jj op restore`

Restore to previous state:

```bash
jj op restore <op-id>             # Restore to operation
```

### `jj op show`

Show operation details:

```bash
jj op show                        # Current operation
jj op show <op-id>                # Specific operation
jj op show -p                     # With patches
```

## File Operations

### `jj file`

File-related commands:

```bash
jj file list                      # List files in working copy
jj file list -r <rev>             # Files in specific revision
jj file show <path>               # Show file content
jj file show -r <rev> <path>      # Content at revision
jj file annotate <path>           # Blame (line origins)
jj file chmod x <path>            # Make executable
jj file chmod n <path>            # Remove executable
jj file track <paths>             # Start tracking
jj file untrack <paths>           # Stop tracking
```

## Workspaces

### `jj workspace`

Manage multiple working copies:

```bash
jj workspace list                 # List workspaces
jj workspace add <path>           # Add workspace
jj workspace add -r <rev> <path>  # At specific revision
jj workspace forget [name]        # Remove workspace
jj workspace root                 # Show workspace root
jj workspace update-stale         # Update stale workspace
```

## Configuration

### `jj config`

Manage configuration:

```bash
jj config list                    # Show all config
jj config get <key>               # Get specific value
jj config set --user <key> <val>  # Set user config
jj config set --repo <key> <val>  # Set repo config
jj config edit --user             # Edit user config
jj config edit --repo             # Edit repo config
jj config path --user             # Show config file path
```

## Utility Commands

### Other useful commands

```bash
jj root                           # Show repo root
jj version                        # Show jj version
jj resolve                        # Resolve conflicts
jj resolve -l                     # List conflicts
jj evolog                         # Show change evolution
jj interdiff --from <A> --to <B>  # Compare changes of commits
jj next                           # Move to child commit
jj prev                           # Move to parent commit
jj fix                            # Run code formatters
jj sign                           # Sign commits
jj sparse set --add <path>        # Add to sparse checkout
jj sparse set --remove <path>     # Remove from sparse
jj util completion <shell>        # Generate shell completions
jj util gc                        # Garbage collect
```

## Global Options

Available on all commands:

```bash
jj -R <path>                      # Use different repo
jj --at-op <op-id>                # Load at operation
jj --ignore-working-copy          # Skip working copy snapshot
jj --ignore-immutable             # Allow modifying immutable
jj --color <when>                 # always/never/auto
jj --no-pager                     # Disable pager
jj --config <key=value>           # Override config
jj --config-file <path>           # Additional config file
jj --quiet                        # Less output
jj --debug                        # Debug output
```
