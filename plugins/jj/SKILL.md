---
name: jj
description: Jujutsu (jj) version control system - a Git-compatible VCS with novel features. Use when working with jj repositories, managing stacked/dependent commits, needing automatic rebasing with first-class conflict handling, using revsets to select commits, or wanting enhanced Git workflows. Triggers on mentions of 'jj', 'jujutsu', change IDs, operation log, or jj-specific commands.
---

# Jujutsu (jj) Version Control System

## Overview

Jujutsu is a powerful Git-compatible version control system that combines ideas from Git, Mercurial, Darcs, and adds novel features. It uses Git repositories as a storage backend, making it fully interoperable with existing Git tooling.

**Key differentiators from Git:**
- Working copy is automatically committed (no staging area)
- Conflicts can be committed and resolved later
- Automatic rebasing of descendants when commits change
- Operation log enables easy undo of any operation
- Revsets provide powerful commit selection
- Change IDs stay stable across rewrites (unlike commit hashes)

## When to Use This Skill

- User mentions "jj", "jujutsu", or "jujutsu vcs"
- Working with stacked/dependent commits
- Questions about change IDs vs commit IDs
- Revset queries for selecting commits
- Conflict resolution workflows in jj
- Git interoperability with jj
- Operation log, undo, or redo operations
- History rewriting (squash, split, rebase, diffedit)
- Bookmark management (jj's equivalent of branches)

## Key Concepts

### Working Copy as a Commit

In jj, the working copy is always a commit. Changes are automatically snapshotted:

```bash
# No need for 'git add' - changes are tracked automatically
jj status        # Shows working copy state
jj diff          # Shows changes in working copy commit
```

### When Snapshots Are Triggered

The working copy is snapshotted into the current commit (`@`) when running most jj commands. Key triggers:

- `jj new` - Creates new commit, snapshots working copy into parent
- `jj status` - Triggers snapshot before showing status
- `jj diff`, `jj log`, `jj describe` - All trigger snapshot first

**Forcing a snapshot manually:**

```bash
# If you edited files but need to ensure they're committed:
jj new                       # Snapshot into parent, create new @
jj abandon @                 # Remove empty new commit if not needed

# Alternative: describe triggers snapshot
jj describe -m "updated"     # Snapshot and update description
```

**Important:** When you `jj edit` a commit and make changes, those appear as "working copy changes" until a snapshot is triggered. This is normal behavior.

### Change ID vs Commit ID

- **Change ID**: Stable identifier that persists across rewrites (e.g., `kntqzsqt`)
- **Commit ID**: Hash that changes when commit is rewritten (e.g., `5d39e19d`)

Always prefer change IDs when referring to commits in commands.

### No Staging Area

Instead of staging, use these patterns:
- `jj split` - Split working copy into multiple commits
- `jj squash -i` - Interactively move changes to parent
- Direct editing with `jj diffedit`

### First-Class Conflicts

Conflicts are recorded in commits, not blocking operations:

```bash
jj rebase -s X -d Y     # Succeeds even with conflicts
jj log                   # Shows conflicted commits with ×
jj new <conflicted>      # Work on top of conflict
# Edit files to resolve, then:
jj squash                # Move resolution into parent
```

### Operation Log

Every operation is recorded and can be undone:

```bash
jj op log                # View operation history
jj undo                  # Undo last operation
jj op restore <op-id>    # Restore to specific operation
```

## Essential Commands

| Command | Description | Git Equivalent |
|---------|-------------|----------------|
| `jj git clone <url>` | Clone a Git repository | `git clone` |
| `jj git init` | Initialize new repo | `git init` |
| `jj status` / `jj st` | Show working copy status | `git status` |
| `jj log` | Show commit history | `git log --graph` |
| `jj diff` | Show changes | `git diff` |
| `jj new` | Create new empty commit | - |
| `jj describe` / `jj desc` | Edit commit message | `git commit --amend` (msg only) |
| `jj edit <rev>` | Edit existing commit | `git checkout` + amend |
| `jj squash` | Move changes to parent | `git commit --amend` |
| `jj split` | Split commit in two | `git add -p` + multiple commits |
| `jj rebase` | Move commits | `git rebase` |
| `jj bookmark` / `jj b` | Manage bookmarks | `git branch` |
| `jj git fetch` | Fetch from remote | `git fetch` |
| `jj git push` | Push to remote | `git push` |
| `jj undo` | Undo last operation | `git reflog` + reset |
| `jj file annotate` | Show line origins | `git blame` |

## Common Workflows

### Starting a New Change

```bash
# Working copy changes are auto-committed
# When ready to start fresh work:
jj new                    # Create new commit on top
jj describe -m "message"  # Set description
# Or combine:
jj new -m "Start feature X"
```

### Editing a Previous Commit

```bash
# Option 1: Edit in place
jj edit <change-id>       # Make working copy edit that commit
# Make changes, they're auto-committed
jj new                    # Return to working on new changes

# Option 2: Squash changes into parent
jj squash                 # Move all changes to parent
jj squash -i              # Interactively select changes
jj squash <file>          # Move specific file
```

### Rebasing Commits

```bash
# Rebase current branch onto main
jj rebase -d main

# Rebase specific revision and descendants
jj rebase -s <rev> -d <destination>

# Rebase only specific revisions (not descendants)
jj rebase -r <rev> -d <destination>

# Insert commit between others
jj rebase -r X -A Y       # Insert X after Y
jj rebase -r X -B Y       # Insert X before Y
```

### Working with Bookmarks (Branches)

```bash
jj bookmark list          # List bookmarks
jj bookmark create <name> # Create at current commit
jj bookmark set <name>    # Move bookmark to current commit
jj bookmark delete <name> # Delete bookmark
jj bookmark track <name>@<remote>  # Track remote bookmark
```

**Bookmark gotchas:**

```bash
# Moving backwards requires a flag:
jj bookmark set feature -r <ancestor>                  # FAILS if ancestor
jj bookmark set feature -r <ancestor> --allow-backwards  # Works

# The * suffix means bookmark diverged from tracked remote:
# feature* 123abc  ← Push to sync with remote
jj git push --bookmark feature

# Create vs Set:
jj bookmark create feature     # FAILS if feature@origin exists
jj bookmark set feature -r @   # Works, moves existing bookmark
```

### Pushing Changes

```bash
# Push specific bookmark
jj git push --bookmark <name>

# Push change by creating auto-named bookmark
jj git push --change <change-id>

# Push all bookmarks
jj git push --all
```

### Resolving Conflicts

```bash
# After a rebase creates conflicts:
jj log                    # Find conflicted commit (marked with ×)
jj new <conflicted>       # Create commit on top
# Edit files to resolve conflicts
jj squash                 # Move resolution into conflicted commit

# Or use external merge tool:
jj resolve                # Opens merge tool for each conflict
jj resolve --list         # List all conflicted files
```

### Resolving Binary File Conflicts

Binary files (images, `.wasm`, compiled files) cannot have conflict markers. Resolve by choosing one version:

```bash
# Take version from specific revision (e.g., main):
jj restore --from main path/to/binary.wasm

# Take version from feature branch:
jj restore --from feature path/to/binary.wasm

# For multiple binary files:
jj resolve --list         # See all conflicted files
for file in file1.wasm file2.wasm; do
  jj restore --from main "path/to/$file"
done
```

### Multi-Parent (Merge) Conflict Resolution

When a merge commit has conflicts:

```bash
# Option 1: Work on child of merge
jj new <conflicted-merge>    # Create child of merge
# Edit files to resolve
jj squash                    # Move resolutions into merge

# Option 2: Edit the merge directly
jj edit <conflicted-merge>   # Edit the merge itself
# Make changes - they appear as "working copy changes"
jj new                       # Snapshot changes into merge
jj abandon @                 # Remove empty temp commit
```

**Creating multi-parent merges:**
```bash
jj new branch-a branch-b branch-c -m "integration: merge features"
```

### Undoing Mistakes

```bash
jj undo                   # Undo last operation
jj op log                 # View operation history
jj op restore <op-id>     # Restore to specific state

# View repo at past operation
jj --at-op=<op-id> log
```

## Revsets Quick Reference

Revsets select commits using a functional language:

| Expression | Description |
|------------|-------------|
| `@` | Working copy commit |
| `@-` | Parent of working copy |
| `x-` | Parents of x |
| `x+` | Children of x |
| `::x` | Ancestors of x (inclusive) |
| `x::` | Descendants of x (inclusive) |
| `x..y` | Ancestors of y not in ancestors of x |
| `x::y` | Commits between x and y (DAG path) |
| `bookmarks()` | All bookmark targets |
| `trunk()` | Main branch (main/master) |
| `mine()` | Commits by current user |
| `conflicts()` | Commits with conflicts |
| `description(text)` | Commits with matching description |

**Examples:**
```bash
jj log -r '@::'           # Working copy and descendants
jj log -r 'trunk()..@'    # Commits between trunk and working copy
jj log -r 'mine() & ::@'  # My commits in working copy ancestry
jj rebase -s 'roots(trunk()..@)' -d trunk()  # Rebase branch onto trunk
```

## Git Interoperability

### Colocated Repositories

By default, `jj git clone` and `jj git init` create colocated repos where both `jj` and `git` commands work:

```bash
jj git clone <url>        # Creates colocated repo (default)
jj git clone --no-colocate <url>  # Non-colocated (jj only)
```

### Using Git Commands

In colocated repos, Git changes are auto-imported. For non-colocated:

```bash
jj git import             # Import changes from Git
jj git export             # Export changes to Git
```

### Converting Existing Git Repo

```bash
cd existing-git-repo
jj git init --colocate    # Add jj to existing Git repo
```

### Colocated Mode Deep Dive

In colocated mode, both jj and Git operate on the same repository. This creates some nuances to understand:

**Understanding git status output:**

```bash
$ git status
HEAD detached from 82f30e2c
nothing to commit, working tree clean
```

The "detached from X" message shows the *original* detachment point, not current HEAD. To verify actual HEAD position:

```bash
git log --oneline -1 HEAD  # Shows current HEAD
```

**Git index sync issues:**

After jj conflict resolution, git may show unmerged paths:

```bash
$ git status
Unmerged paths:
  both modified:   Cargo.lock
```

Fix by updating the git index:
```bash
git add <files>           # Clears unmerged entries
```

**When git and jj disagree:**

```bash
jj git import             # Force import git state to jj
jj git export             # Force export jj state to git
```

**Best practice:** Primarily use jj commands in colocated repos. Only use git for operations jj doesn't support (like interactive rebase with git add -p style workflows).

## Configuration

Edit config with `jj config edit --user`:

```toml
[user]
name = "Your Name"
email = "your@email.com"

[ui]
default-command = "log"   # Run 'jj log' when no command given
diff-editor = ":builtin"  # Or "meld", "kdiff3", etc.

[revset-aliases]
'wip' = 'description(exact:"") & mine()'  # Custom revset alias
```

## Advanced Topics

For comprehensive documentation, see:
- [references/revsets.md](references/revsets.md) - Complete revset reference
- [references/commands.md](references/commands.md) - Full command reference
- [references/git-comparison.md](references/git-comparison.md) - Git to jj command mapping

## Troubleshooting

**"Working copy is dirty"** - Never happens in jj! Working copy is always a commit.

**Conflicts after rebase** - Normal in jj. Conflicts are recorded, resolve when convenient.

**Lost commits** - Use `jj op log` to find when commits existed, then `jj op restore`.

**Divergent changes** - Same change ID, different commits. Usually from concurrent edits:
```bash
jj log                    # Shows divergent commits
jj abandon <unwanted>     # Remove one version
```

**Immutable commit error** - Can't modify trunk/tagged commits by default:
```bash
jj --ignore-immutable <command>  # Override protection
```

## Common Pitfalls

### Push Flag Combinations

Some `jj git push` flag combinations don't work together:

| Flags | Works? | Notes |
|-------|--------|-------|
| `--all` | ✓ | Pushes all bookmarks |
| `--tracked` | ✓ | Pushes tracked bookmarks that changed |
| `--bookmark <name>` | ✓ | Pushes specific bookmark |
| `--change <id>` | ✓ | Creates/pushes auto-named bookmark |
| `--all --allow-new` | ✗ | **Incompatible** |
| `--tracked --allow-new` | ✗ | **Incompatible** |
| `--bookmark <name> --allow-new` | ✓ | For new bookmarks |

### Working Copy Changes on Merge Commits

When you `jj edit` a merge commit, changes appear as "working copy changes" even if you're resolving conflicts. This is expected - use `jj new` to trigger snapshot:

```bash
jj edit <merge-commit>       # Edit the merge
# Make changes...
jj new                       # Snapshot into merge, create new @
jj abandon @                 # Remove empty commit
```

### Git Status Shows Detached HEAD

In colocated repos, `git status` shows "HEAD detached from X" - this is normal. The message shows the *original* detachment point. Check actual HEAD with:

```bash
git log --oneline -1 HEAD    # Current HEAD position
```

### Bookmark Movement Refused

If `jj bookmark set` fails because it would move "backwards":

```bash
jj bookmark set name -r <rev> --allow-backwards
```

This flag is required when moving a bookmark to an ancestor of its current position.
