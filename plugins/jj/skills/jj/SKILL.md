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

The working copy is snapshotted into `@` when running most jj commands (`new`, `status`, `diff`, `log`, `describe`). Force a snapshot with `jj util snapshot` or just run any jj command.

### Change ID vs Commit ID

- **Change ID**: Stable identifier that persists across rewrites (e.g., `kntqzsqt`)
- **Commit ID**: Hash that changes when commit is rewritten (e.g., `5d39e19d`)

Always prefer change IDs when referring to commits in commands.

**Versioned access (0.37+):** Use `xyz/n` suffix to access hidden/divergent versions:
- `xyz/0` - latest version of change xyz
- `xyz/1` - previous version (useful for `jj restore --from xyz/1 --to xyz`)
- Shown automatically in `jj log` for divergent changes

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
jj redo                  # Redo undone operation
jj op revert <op-id>     # Revert specific operation
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
| `jj file search` | Search file contents | `git grep` |
| `jj commit` | Finalize WC commit + start new | `git commit` |
| `jj absorb` | Auto-squash into right commits | `git commit --fixup` + autosquash |
| `jj evolog` | History of a single change | `git reflog` (per-commit) |
| `jj next` / `jj prev` | Navigate commit graph | `git checkout HEAD~` |
| `jj interdiff` | Compare diffs of two changes | - |
| `jj fix` | Run formatters on commits | - |
| `jj arrange` | TUI to reorder/abandon commits | `git rebase -i` (reorder) |
| `jj bookmark advance` | Move bookmark forward | fast-forward branch |

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

# Option 3: Auto-squash into correct commits in stack
jj absorb                 # Each hunk goes to commit that last changed those lines
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

# Simplify redundant parents during rebase
jj rebase -s <rev> -d <dest> --simplify-parents
```

### Reordering Commits with `jj arrange`

```bash
jj arrange <revset>       # Open TUI to reorder/abandon commits
```

The TUI shows selected commits with their immediate parents/children. Use swap up/down to reorder along graph edges.

### Working with Bookmarks (Branches)

```bash
jj bookmark list          # List bookmarks
jj bookmark create <name> # Create at current commit
jj bookmark set <name>    # Move bookmark to current commit
jj bookmark delete <name> # Delete bookmark
jj bookmark track <name> --remote <remote>  # Track remote bookmark
jj bookmark advance       # Move bookmark forward to @ (like "jj tug")
```

**Gotchas:** Use `--allow-backwards` to move a bookmark to an ancestor. The `*` suffix in log means diverged from remote (push to sync). Use `bookmark set` (not `create`) if the bookmark may already exist on a remote.

### Searching File Contents

```bash
jj file search <pattern>                  # Search with regex (default)
jj file search --pattern "glob:*.rs"      # Use glob pattern
jj file search --pattern "substring:foo"  # Substring match
jj file search -r <rev> <pattern>         # Search at specific revision
```

### Pushing Changes

```bash
# Push specific bookmark
jj git push --bookmark <name>

# Push change by creating auto-named bookmark
jj git push --change <change-id>

# Push all bookmarks (skips ineligible: private/conflicted)
jj git push --all

# Pass push options to remote server
jj git push --bookmark <name> --option key=value
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

### Binary & Merge Conflict Resolution

Binary files cannot have conflict markers - resolve by choosing a version:

```bash
jj restore --from main path/to/binary.wasm    # Take from specific revision
```

Multi-parent merge conflicts:
```bash
jj new <conflicted-merge>    # Create child of merge
# Edit files to resolve
jj squash                    # Move resolutions into merge
```

**Creating multi-parent merges:**
```bash
jj new branch-a branch-b branch-c -m "integration: merge features"
```

### Undoing Mistakes

```bash
jj undo                   # Undo last operation
jj redo                   # Redo undone operation
jj op log                 # View operation history
jj op revert <op-id>      # Revert specific operation
jj op restore <op-id>     # Restore to specific state

# View repo at past operation
jj --at-op=<op-id> log

# Run command without affecting repo state (read-only inspection)
jj --no-integrate-operation log -r 'trunk()..@'
```

## Revsets Quick Reference

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
| `divergent()` | Divergent changes |
| `description(text)` | Commits with matching description |
| `diff_lines(text)` | Commits with matching diff content |
| `remote_tags()` | Remote tag targets |

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

### Converting Existing Git Repo

```bash
cd existing-git-repo
jj git init --colocate    # Add jj to existing Git repo
```

In colocated repos, Git changes are auto-imported. If git and jj disagree, use `jj git import` / `jj git export`. Best practice: primarily use jj commands.

## Configuration

Edit config with `jj config edit --user` (or `--repo` for per-repo config, stored outside the repo since 0.38):

```toml
[user]
name = "Your Name"
email = "your@email.com"

[ui]
default-command = "log"   # Run 'jj log' when no command given
diff-editor = ":builtin"  # For interactive diff editing (split, squash -i)

[revset-aliases]
'wip' = 'description(exact:"") & mine()'  # Custom revset alias
```

**For automation/LLMs:** Use `-m` flags instead of relying on editors. See [Non-Interactive Workflows](#non-interactive-workflows) for patterns that work without user interaction.

See [references/configuration.md](references/configuration.md) for comprehensive configuration options including editor setup for interactive use.

## Template Language

Customize output with `-T`/`--template`:

```bash
jj log -T 'change_id.short(8) ++ " " ++ description.first_line() ++ "\n"'
jj log -T 'if(conflict, "CONFLICT ", "") ++ description.first_line()'
```

Key: `++` concatenates, `if(cond, then, else)` conditionals, `separate(sep, ...)` joins non-empty. See [references/templates.md](references/templates.md).

## Filesets

Select files in commands using fileset expressions:

```bash
jj diff 'glob:*.rs'              # Rust files in cwd
jj diff '~Cargo.lock'            # Everything except Cargo.lock
jj split 'glob:**/test_*'        # Test files only
jj log -r 'files("src")'         # Commits touching src/
```

See [references/filesets.md](references/filesets.md).

## Advanced Topics

For comprehensive documentation, see:
- [references/github-workflow.md](references/github-workflow.md) - GitHub/GitLab PR workflows
- [references/conflicts.md](references/conflicts.md) - Conflict resolution deep dive
- [references/faq-patterns.md](references/faq-patterns.md) - Common patterns & FAQ
- [references/templates.md](references/templates.md) - Template language reference
- [references/filesets.md](references/filesets.md) - Fileset language reference
- [references/revsets.md](references/revsets.md) - Complete revset reference
- [references/commands.md](references/commands.md) - Full command reference
- [references/configuration.md](references/configuration.md) - Configuration reference
- [references/git-comparison.md](references/git-comparison.md) - Git to jj command mapping

## Troubleshooting

**"Working copy is dirty"** - Never happens in jj! Working copy is always a commit.

**Conflicts after rebase** - Normal in jj. Conflicts are recorded, resolve when convenient.

**Lost commits** - Use `jj op log` to find when commits existed, then `jj op restore`.

**Divergent changes** - Same change ID, different commits. Usually from concurrent edits:
```bash
jj log                    # Shows divergent commits with xyz/0, xyz/1 suffixes
jj diff --from xyz/0 --to xyz/1  # Compare versions
jj abandon <unwanted>     # Remove one version
jj restore --from xyz/1 --to xyz  # Restore to previous version
```

**Immutable commit error** - Can't modify trunk/tagged commits by default:
```bash
jj --ignore-immutable <command>  # Override protection
```

## Non-Interactive Workflows

Many jj commands open an editor by default. Use these flags for automation and CLI workflows:

### Commit Messages Without Editor

| Command | Non-Interactive Flag | Example |
|---------|---------------------|---------|
| `jj describe` | `-m` or `--stdin` | `jj describe -m "Fix bug"` |
| `jj commit` | `-m` | `jj commit -m "Add feature"` |
| `jj new` | `-m` | `jj new -m "Start new work"` |
| `jj squash` | `-m` or `-u` | `jj squash -u` (use destination message) |
| `jj split` | `-m` (first commit only) | `jj split -m "First part" <files>` |

### Squash Without Editor

```bash
# Use destination's message (discard source)
jj squash --use-destination-message    # or -u

# Provide explicit message
jj squash -m "Combined commit message"
```

**Note:** If either commit has an empty description, jj automatically uses the non-empty one without opening an editor.

### Searching Files (Non-Interactive)

```bash
jj file search "pattern"                  # Regex search (default)
jj file search --pattern "glob:*.rs"      # Glob pattern
jj file search -r <rev> "pattern"         # Search at specific revision
```

### Conflict Resolution Without Merge Tool

```bash
# Use built-in tools instead of external merge tool
jj resolve --tool :ours <file>      # Take "our" version (side #1)
jj resolve --tool :theirs <file>    # Take "their" version (side #2)

# Or use restore for complete replacement
jj restore --from <rev> <file>      # Take file from specific revision
```

### Inherently Interactive Commands

These commands cannot be made non-interactive:
- `jj split` (without file arguments) - requires diff selection
- `jj diffedit` - opens diff editor by design
- `jj resolve` (without `--tool`) - opens merge tool
- `jj arrange` - TUI by design

**Workaround for split:** Provide file paths to avoid interactive selection:
```bash
jj split -m "First commit" src/file1.rs src/file2.rs
```

## Common Pitfalls

### Push Flag Combinations

Some `jj git push` flag combinations don't work together:

| Flags | Works? | Notes |
|-------|--------|-------|
| `--all` | ✓ | Pushes all bookmarks (skips ineligible) |
| `--tracked` | ✓ | Pushes tracked bookmarks that changed |
| `--bookmark <name>` | ✓ | Pushes specific bookmark |
| `--change <id>` | ✓ | Creates/pushes auto-named bookmark |
| `--all --allow-new` | ✗ | **Incompatible** |
| `--tracked --allow-new` | ✗ | **Incompatible** |
| `--bookmark <name> --allow-new` | ✓ | For new bookmarks |
| `--option key=value` | ✓ | Pass push options to server |

**Note (0.41+):** `--all`, `--tracked`, and `-r REVSETS` no longer fail when revisions are private or have conflicts - ineligible bookmarks are silently skipped.

### Working Copy Changes on Merge Commits

When you `jj edit` a merge commit, changes appear as "working copy changes" - this is expected. Use `jj new` to trigger snapshot, then `jj abandon @` to remove the empty commit.

### Bookmark Movement Refused

If `jj bookmark set` fails because it would move "backwards":

```bash
jj bookmark set name -r <rev> --allow-backwards
```

This flag is required when moving a bookmark to an ancestor of its current position.

## Minimum Version Requirements

| Feature | Min Version |
|---------|-------------|
| `xyz/n` change offset syntax | 0.37+ |
| `jj file search`, string patterns default to glob | 0.37+ |
| `divergent()`, `remote_tags()`, `diff_lines()` revsets | 0.38+ |
| `git_web_url()`, `hyperlink()` templates | 0.38+ |
| `jj arrange`, `jj bookmark advance` | 0.39+ |
| List methods (`first`, `last`, `get`, `reverse`, `skip`, `take`) | 0.39+ |
| Pattern aliases, fileset aliases | 0.39+ |
| `diff_lines_added()`, `diff_lines_removed()` | 0.40+ |
| `replace()` template, `--no-integrate-operation` | 0.41+ |
