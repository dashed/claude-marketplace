# Configuration Reference

Complete guide to configuring git-absorb behavior via `.gitconfig`.

## Quick Reference

```toml
[absorb]
    maxStack = 50
    oneFixupPerCommit = true
    autoStageIfNothingStaged = true
    fixupTargetAlwaysSHA = false
    forceAuthor = false
    forceDetach = false
    createSquashCommits = false
```

## Configuration Options

### `maxStack`

**Default:** `10`

**Purpose:** Maximum number of commits to search when run without `--base`.

**When to configure:**
- Working on feature branches with >10 commits
- Seeing "WARN stack limit reached" messages
- Want to absorb into older commits

**Recommended values:**
- Small projects: `20-30`
- Medium projects: `50`
- Large feature branches: `100+`

**Configuration:**
```bash
# Local (current repository only)
git config absorb.maxStack 50

# Global (all repositories)
git config --global absorb.maxStack 50
```

**In .gitconfig:**
```toml
[absorb]
    maxStack = 50
```

**Warning message when limit reached:**
```
WARN stack limit reached, limit: 10
```

**Alternative:** Use `--base <branch>` flag to specify range without changing config:
```bash
git absorb --base main  # searches all commits since main
```

---

### `oneFixupPerCommit`

**Default:** `false`

**Purpose:** Generate only one fixup commit per target commit instead of per hunk.

**Effect:**
- `false`: Multiple fixup commits if multiple hunks absorb into same commit
- `true`: Single consolidated fixup commit per target

**When to enable:**
- Prefer cleaner rebase history
- Don't need per-hunk granularity
- Many small changes to same commits

**Configuration:**
```bash
git config absorb.oneFixupPerCommit true
git config --global absorb.oneFixupPerCommit true
```

**In .gitconfig:**
```toml
[absorb]
    oneFixupPerCommit = true
```

**Example difference:**

Without `oneFixupPerCommit`:
```
fixup! Add feature X  (for hunk 1)
fixup! Add feature X  (for hunk 2)
fixup! Add feature X  (for hunk 3)
```

With `oneFixupPerCommit`:
```
fixup! Add feature X  (all hunks consolidated)
```

**Command-line alternative:**
```bash
git absorb --one-fixup-per-commit
```

---

### `autoStageIfNothingStaged`

**Default:** `false`

**Purpose:** Automatically stage all changes when nothing is staged.

**Effect:**
- `false`: Only consider explicitly staged files (requires `git add`)
- `true`: Auto-stage all changes if index is empty, unstage remainder after absorb

**When to enable:**
- Frequently run `git add .` before absorbing
- Want streamlined workflow
- Trust git-absorb with all working directory changes

**Configuration:**
```bash
git config absorb.autoStageIfNothingStaged true
git config --global absorb.autoStageIfNothingStaged true
```

**In .gitconfig:**
```toml
[absorb]
    autoStageIfNothingStaged = true
```

**Workflow with this enabled:**
```bash
# Make changes (don't stage)
vim file1.py file2.py

# Run absorb directly (no git add needed)
git absorb --and-rebase
# -> auto-stages all changes
# -> absorbs what it can
# -> unstages remainder
```

**Warning:** Be careful with this if you have unrelated changes in working directory.

---

### `fixupTargetAlwaysSHA`

**Default:** `false`

**Purpose:** Always use commit SHA in fixup messages instead of commit summary.

**Effect:**
- `false`: Use commit summary if unique, fall back to SHA for duplicates
- `true`: Always use SHA

**When to enable:**
- Commit messages have many duplicates
- Prefer consistency in fixup references
- Working with auto-generated commit messages

**Configuration:**
```bash
git config absorb.fixupTargetAlwaysSHA true
git config --global absorb.fixupTargetAlwaysSHA true
```

**In .gitconfig:**
```toml
[absorb]
    fixupTargetAlwaysSHA = true
```

**Example difference:**

Default (`false`):
```
fixup! Add user authentication
fixup! abc123  (if "Add user authentication" appears multiple times)
```

With `fixupTargetAlwaysSHA = true`:
```
fixup! abc123
fixup! def456
```

---

### `forceAuthor`

**Default:** `false`

**Purpose:** Generate fixups for commits authored by anyone, not just you.

**Effect:**
- `false`: Only modify your own commits (filtered by git author)
- `true`: Can modify any author's commits

**When to enable:**
- Pair programming environments
- Shared feature branches with multiple authors
- Taking over someone else's work

**Configuration:**
```bash
git config absorb.forceAuthor true
git config --global absorb.forceAuthor true
```

**In .gitconfig:**
```toml
[absorb]
    forceAuthor = true
```

**Security consideration:** Only enable if you have permission to modify others' commits.

**Command-line alternative:**
```bash
git absorb --force-author
```

---

### `forceDetach`

**Default:** `false`

**Purpose:** Allow generating fixups when HEAD is detached (not on a branch).

**Effect:**
- `false`: Refuse to run when HEAD is detached
- `true`: Run even in detached HEAD state

**When to enable:**
- Frequently work in detached HEAD state
- Using git-absorb during cherry-pick/bisect workflows
- Advanced git workflows

**Configuration:**
```bash
git config absorb.forceDetach true
git config --global absorb.forceDetach true
```

**In .gitconfig:**
```toml
[absorb]
    forceDetach = true
```

**Warning:** Detached HEAD state can be confusing. Only enable if you understand the implications.

**Command-line alternative:**
```bash
git absorb --force-detach
```

---

### `createSquashCommits`

**Default:** `false`

**Purpose:** Generate squash commits instead of fixup commits.

**Effect:**
- `false`: Create `fixup!` commits (message discarded during autosquash)
- `true`: Create `squash!` commits (message kept and editable during autosquash)

**When to enable:**
- Need to document why changes were added
- Want to edit commit messages during rebase
- Organizational requirements for commit message detail

**Configuration:**
```bash
git config absorb.createSquashCommits true
git config --global absorb.createSquashCommits true
```

**In .gitconfig:**
```toml
[absorb]
    createSquashCommits = true
```

**Example difference:**

With `fixup!` (default):
```
fixup! Add feature X
# During rebase: message discarded, change absorbed silently
```

With `squash!` (createSquashCommits = true):
```
squash! Add feature X
# During rebase: editor opens, can edit combined message
```

**Command-line alternative:**
```bash
git absorb --squash
```

---

## Configuration Scope

### Local vs Global

**Local** (repository-specific):
```bash
git config absorb.maxStack 50
```
- Stored in `.git/config`
- Only affects current repository
- Use for project-specific settings

**Global** (all repositories):
```bash
git config --global absorb.maxStack 50
```
- Stored in `~/.gitconfig`
- Affects all repositories
- Use for personal preferences

### Checking Current Configuration

**View all absorb settings:**
```bash
git config --get-regexp absorb
```

**View specific setting:**
```bash
git config absorb.maxStack
```

**View with source:**
```bash
git config --list --show-origin | grep absorb
```

### Removing Configuration

**Remove local setting:**
```bash
git config --unset absorb.maxStack
```

**Remove global setting:**
```bash
git config --global --unset absorb.maxStack
```

---

## Recommended Configurations

### Conservative (default behavior)
```toml
[absorb]
    maxStack = 10
    oneFixupPerCommit = false
    autoStageIfNothingStaged = false
    fixupTargetAlwaysSHA = false
    forceAuthor = false
    forceDetach = false
    createSquashCommits = false
```

### Balanced (recommended for most users)
```toml
[absorb]
    maxStack = 50
    oneFixupPerCommit = true
    autoStageIfNothingStaged = false
    fixupTargetAlwaysSHA = false
    forceAuthor = false
    forceDetach = false
    createSquashCommits = false
```

### Aggressive (streamlined workflow)
```toml
[absorb]
    maxStack = 100
    oneFixupPerCommit = true
    autoStageIfNothingStaged = true
    fixupTargetAlwaysSHA = false
    forceAuthor = true
    forceDetach = false
    createSquashCommits = false
```

### Team collaboration
```toml
[absorb]
    maxStack = 50
    oneFixupPerCommit = true
    autoStageIfNothingStaged = false
    fixupTargetAlwaysSHA = true
    forceAuthor = true  # Allow fixing teammates' commits
    forceDetach = false
    createSquashCommits = false
```

---

## Command-Line Flags Override Configuration

All configuration options can be overridden with command-line flags:

| Configuration | Command-Line Flag |
|--------------|-------------------|
| `oneFixupPerCommit` | `--one-fixup-per-commit` / `-F` |
| `forceAuthor` | `--force-author` |
| `forceDetach` | `--force-detach` |
| `createSquashCommits` | `--squash` / `-s` |
| `maxStack` | `--base <commit>` |

**Example:**
```bash
# Even with forceAuthor = false in config
git absorb --force-author  # Will absorb into any author's commits
```
