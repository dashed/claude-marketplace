# Commands Reference

Complete reference for jj commands and their options.

## Table of Contents

- [CLI Revision Options](#cli-revision-options)
- [Repository Setup](#repository-setup)
- [Status and History](#status-and-history)
- [Creating and Editing Commits](#creating-and-editing-commits)
- [History Rewriting](#history-rewriting)
- [Bookmarks (Branches)](#bookmarks-branches)
- [Git Operations](#git-operations)
- [Operation Log](#operation-log)
- [File Operations](#file-operations)
- [Tags](#tags)
- [Workspaces](#workspaces)
- [Configuration](#configuration)

## CLI Revision Options

Many jj commands share a consistent pattern of flags for selecting revisions and destinations. Understanding this pattern makes the CLI predictable across commands.

### Source flags (what to operate on)

| Flag | Short | Meaning |
|------|-------|---------|
| `--revision` (or `--revisions`) | `-r` | Select specific revision(s) — default for most commands |
| `--source` | `-s` | Revision AND all its descendants (same as `-r REV::`) |
| `--from` | `-f` | The _contents_ of a revision, or the bookmarks on a revision |
| `--branch` | `-b` | Whole branch relative to destination |

### Destination flags (where to put it)

| Flag | Short | Meaning |
|------|-------|---------|
| `--onto` / `--destination` | `-d` / `-o` | Place as children of target |
| `--insert-after` | `-A` | Insert between target and its children |
| `--insert-before` | `-B` | Insert between target and its parents |
| `--to` / `--into` | `-t` | Target for contents/bookmarks (use with `--from`) |

### Key examples

```bash
# Rebase operations
jj rebase -r xyz -d main              # Rebase single commit onto main
jj rebase -s xyz -d main              # Rebase xyz and all descendants onto main
jj rebase -b @ -d main                # Rebase current branch onto main

# Content operations
jj squash --from xyz --into abc        # Move xyz's changes into abc
jj restore --from main --to @          # Copy file state from main to working copy

# Insertion
jj rebase -r xyz -A main              # Insert xyz after main
jj rebase -r xyz -B main              # Insert xyz before main
```

### Commands that allow omitting `-r`

Some commands accept revisions as positional arguments (e.g., `jj new xyz` instead of `jj new -r xyz`):
`abandon`, `describe`, `duplicate`, `metaedit`, `new`, `parallelize`, `show`.

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

### `jj evolog` (evolution log)

Show the history of a single change over time. Each time a change is rewritten (rebased, squashed, amended), the update appears here:

```bash
jj evolog                         # Evolution of working copy change
jj evolog -r <rev>                # Evolution of specific change
jj evolog -p                      # Show patches between versions
jj evolog -s                      # Summary of changes
jj evolog -n 5                    # Limit entries
jj evolog -T <template>           # Custom template
```

Use with `jj restore --from` to recover a previous version of a change.

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

Snapshot working copy into the current commit, then create a new empty commit on top. The description editor opens for the CURRENT commit (contrast with `jj new`, which creates a new commit without editing the current one's description):

```bash
jj commit                         # Describe current, create new on top
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

### `jj arrange`

TUI for reordering and abandoning revisions interactively:

```bash
jj arrange                        # Reorder revisions in TUI
jj arrange -r <revset>            # Arrange specific revisions
```

Supports swapping commits up/down along graph edges. Includes parents/children in the view and uses the default log template.

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
jj rebase --simplify-parents      # Remove redundant parent edges
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

### `jj absorb`

Auto-squash working copy changes into the commits where those lines were last modified. Like `git commit --fixup` + `rebase --autosquash` in one step:

```bash
jj absorb                         # Absorb all working copy changes into mutable()
jj absorb [paths...]              # Absorb specific paths only
jj absorb --from <rev>            # Absorb from specific revision (default: @)
jj absorb --into <revset>         # Target specific destination commits (default: mutable())
```

**Behavior:**
- Only considers ancestors of the source revision as destinations
- If the destination for a hunk can't be determined unambiguously, the change stays in the source
- Source is abandoned if all changes are absorbed AND it has no description
- Review what happened with `jj op show -p`

### `jj interdiff`

Compare the *diffs* of two revisions — shows how one implementation differs from another:

```bash
jj interdiff --from <rev> --to <rev>   # Compare what two changes do differently
jj interdiff --from push-xyz@origin --to push-xyz  # What changed since last push
jj interdiff --from @- --to other -s   # Summary of implementation differences
```

Unlike `jj diff --from A --to B` (which compares file contents), interdiff compares *patches* — what each change adds/removes relative to its own parents. Use `jj evolog -p` to see the full evolution history instead.

### `jj fix`

Run configured formatting tools on files in mutable commits:

```bash
jj fix                            # Fix files in reachable(@, mutable())
jj fix -s <rev>                   # Fix from specific revision + descendants
jj fix [paths...]                 # Fix only specific paths
jj fix --all-lines               # Format entire files, not just modified lines (0.41+)
jj fix --include-unchanged-files  # Fix all files, not just changed ones
```

Default scope is `reachable(@, mutable())`. Descendants are also fixed to preserve formatting. Review with `jj op show -p`. Requires `[fix.tools.*]` configuration.

### `jj bisect`

Find a bad revision by running a command across history:

```bash
jj bisect run -s <good> -e <bad> -- <command>  # Find first bad revision
```

### `jj next` / `jj prev`

Navigate the commit graph by moving the working copy forward/backward:

```bash
jj next                           # Move WC to child commit
jj next 2                         # Move 2 commits forward
jj next --edit                    # Edit the child instead of creating new WC on top
jj prev                           # Move WC to parent commit
jj prev 2                         # Move 2 commits backward
jj prev --edit                    # Edit the parent directly
```

Without `--edit`: creates a new empty WC commit as sibling. With `--edit`: changes WC to the target commit directly (like `jj edit`).

### `jj metaedit`

Modify commit metadata without changing file content:

```bash
jj metaedit -m "new message"      # Update description (default: @)
jj metaedit -r <revs> -m "msg"    # Update specific revisions
jj metaedit --update-change-id    # Generate a new change ID
```

### `jj sign` / `jj unsign`

Cryptographically sign or remove signatures from commits:

```bash
jj sign                           # Sign revision (uses revsets.sign default)
jj sign -r <revs>                 # Sign specific revisions
jj unsign -r <revs>               # Remove signature
```

### `jj sparse`

Manage sparse checkouts — control which paths are materialized in the working copy:

```bash
jj sparse list                    # Show current sparse patterns
jj sparse set --add src --remove tests  # Modify patterns
jj sparse set --clear --add src   # Start fresh with only src/
jj sparse reset                   # Include all files again
jj sparse edit                    # Edit patterns in editor
```

### `jj revert`

Create new commit(s) that are the reverse of specified changes. Unlike `jj restore`, this creates new commits rather than modifying existing ones:

```bash
jj revert -r <rev>                # Create commit undoing rev's changes
jj revert -r <revs>              # Revert multiple revisions
jj revert -s <rev>                # Revert rev and all descendants
jj revert -r xyz -d main          # Revert and place onto main
```

### `jj parallelize`

Make sequential revisions into parallel siblings (children of the same parent):

```bash
jj parallelize <revs>             # Make revisions parallel
jj parallelize abc::xyz           # Parallelize a range of commits
```

### `jj simplify-parents`

Remove redundant parent edges from merge commits. Useful after rebasing when a merge commit has a parent that's also an ancestor through another parent:

```bash
jj simplify-parents               # Simplify working copy parents
jj simplify-parents -r <revs>     # Simplify specific revisions
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
jj bookmark rename <old> <new> --overwrite-existing  # Replace existing
jj bookmark advance               # Move bookmarks forward to @
jj bookmark advance -r <rev>      # Move bookmarks forward to revision

# Delete
jj bookmark delete <name>         # Delete (will push deletion)
jj bookmark forget <name>         # Forget (won't push deletion)

# Remote tracking
jj bookmark track <name> --remote <remote>
jj bookmark untrack <name> --remote <remote>
```

`bookmark advance` uses `revsets.bookmark-advance-from` and `revsets.bookmark-advance-to` for customization.

## Git Operations

### `jj git fetch`

Fetch from remote:

```bash
jj git fetch                      # From default remote
jj git fetch --remote <name>      # From specific remote
jj git fetch --all-remotes        # From all remotes
jj git fetch --branch <pattern>   # Specific branches
jj git fetch --tag <pattern>      # Fetch specific tags (experimental)
```

Shows details of abandoned commits after fetch.

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
jj git push -o <key>=<value>      # Pass push options to remote
```

`--all`, `--tracked`, and `-r` skip ineligible bookmarks (private/conflicted) instead of failing.

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
jj git remote set-url <name> --push <url>  # Separate push URL
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

### `jj op revert`

Revert an operation (replaces removed `jj op undo`):

```bash
jj op revert <op-id>              # Revert specific operation
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
jj file search <pattern>          # Search file contents (like git grep)
jj file search <pattern> -r <rev> # Search at specific revision
```

`file search` accepts `kind:pattern` syntax (e.g., `regex:`, `glob:`). The `--pattern` flag defaults to `regex:`.

## Tags

### `jj tag list`

List and filter tags:

```bash
jj tag list                       # List all tags
jj tag list --sort <field>        # Sort by name, date, etc.
jj tag list -r <revset>           # Filter tags by revset
```

## Workspaces

### `jj workspace`

Manage multiple working copies:

```bash
jj workspace list                 # List workspaces
jj workspace add <path>           # Add workspace (uses relative paths)
jj workspace add -r <rev> <path>  # At specific revision
jj workspace forget [name]        # Remove workspace
jj workspace root                 # Show workspace root
jj workspace root --name <name>   # Root of specified workspace
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
jj interdiff --from <A> --to <B>  # Compare changes of commits
jj next                           # Move to child commit
jj prev                           # Move to parent commit
jj fix                            # Run code formatters (line-ranges only)
jj fix --all-lines                # Format entire files (previous default)
jj sign                           # Sign commits
jj sparse set --add <path>        # Add to sparse checkout
jj sparse set --remove <path>     # Remove from sparse
jj util completion <shell>        # Generate shell completions
jj util gc                        # Garbage collect
jj util snapshot                  # Manually trigger working copy snapshot
```

`jj fix` supports line-range formatting via `fix.tools.<name>.line-range-arg` config.

## Global Options

Available on all commands:

```bash
jj -R <path>                      # Use different repo
jj --at-op <op-id>                # Load at operation
jj --ignore-working-copy          # Skip working copy snapshot
jj --ignore-immutable             # Allow modifying immutable
jj --no-integrate-operation       # Run without impacting repo state
jj --color <when>                 # always/never/auto
jj --no-pager                     # Disable pager
jj --config <key=value>           # Override config
jj --config-file <path>           # Additional config file
jj --quiet                        # Less output
jj --debug                        # Debug output
```
