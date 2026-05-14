---
name: git-absorb
description: Automatically fold uncommitted changes into appropriate commits on a feature branch. Use when applying review feedback, fixing bugs in feature branches, or maintaining atomic commit history without manual interactive rebasing. Particularly useful for making corrections to recent commits without creating messy "fixes" commits.
---

# Git Absorb

## Overview

`git absorb` automatically identifies which commits should contain your staged changes and creates fixup commits that can be autosquashed. This eliminates the need to manually find commit SHAs or run interactive rebases when applying review feedback or fixing bugs in feature branches.

## When to Use This Skill

Use git-absorb when:
- **Applying review feedback**: Reviewer pointed out bugs or improvements across multiple commits
- **Fixing bugs**: Discovered issues in your feature branch that belong in specific earlier commits
- **Maintaining atomic commits**: Want to keep commits focused without creating "fixes" or "oops" commits
- **Avoiding manual rebasing**: Don't want to manually identify which commits need which changes

## Prerequisites

**CRITICAL**: Before proceeding, you MUST verify that git-absorb is installed:

```bash
git absorb --version
```

**If git-absorb is not installed:**
- **DO NOT** attempt to install it automatically
- **STOP** and inform the user that git-absorb is required
- **RECOMMEND** manual installation with the following instructions:

```bash
# macOS
brew install git-absorb

# Linux (Debian/Ubuntu)
apt install git-absorb

# Arch Linux
pacman -S git-absorb

# Cargo (all platforms)
cargo install git-absorb

# Other systems: see https://github.com/tummychow/git-absorb
```

**If git-absorb is not available, exit gracefully and do not proceed with the workflow below.**

### Important Default Behaviors

Before using git-absorb, understand these key defaults:

**Author Filtering**: By default, git-absorb **only modifies commits you authored**. It will not absorb changes into commits made by teammates.
- To absorb into any author's commits, use `git absorb --force-author`
- Or configure globally: `git config absorb.forceAuthor true`

**Stack Size Limit**: By default, git-absorb searches only the **last 10 commits**. If you're working on a larger feature branch, you may need to:
- Use `--base <branch>` to specify a range (e.g., `--base main`)
- Or increase the limit in `.gitconfig` (see Configuration section below)

**Staged Changes Only**: git-absorb only considers changes in the git index (staging area). Unstaged changes are ignored.

## Basic Workflow

**ONLY proceed with this workflow if git-absorb is confirmed to be installed.**

### Step 1: Make Your Changes

Make fixes or improvements to files in your working directory.

### Step 2: Stage the Changes

```bash
git add <files-you-fixed>
```

**Important**: Only stage changes you want absorbed. git-absorb only considers staged changes.

### Step 3: Run git absorb

**Option A: Automatic (recommended for trust)**
```bash
git absorb --and-rebase
```

This creates fixup commits AND automatically rebases them into the appropriate commits.

**Option B: Manual review**
```bash
git absorb
git log  # Review the generated fixup commits
git rebase -i --autosquash <base-branch>
```

Use this when you want to inspect the fixup commits before integrating them.

## Common Patterns

### Pattern 1: Review Feedback

**Scenario**: PR reviewer found bugs in commits A, B, and C

```bash
# 1. Make all the fixes
vim file1.py file2.py file3.py

# 2. Stage all fixes
git add file1.py file2.py file3.py

# 3. Let git-absorb figure out which fix goes where
git absorb --and-rebase
```

git-absorb analyzes each change and assigns it to the appropriate commit.

### Pattern 2: Bug Fix in Feature Branch

**Scenario**: Found a bug in an earlier commit while developing

```bash
# 1. Fix the bug
vim src/module.py

# 2. Stage and absorb
git add src/module.py
git absorb --and-rebase
```

The fix is automatically folded into the commit that introduced the bug.

### Pattern 3: Multiple Small Fixes

**Scenario**: Several typos, formatting issues across multiple commits

```bash
# Fix everything first
vim file1.py file2.py README.md

# Stage and absorb in one go
git add -A
git absorb --and-rebase
```

## Advanced Usage

For comprehensive coverage of all flags and advanced patterns, see [references/advanced-usage.md](references/advanced-usage.md).

**Key flags:**
- `--base <commit>`: Specify range (e.g., `--base main`)
- `--dry-run`: Preview without making changes
- `--force`: Skip safety checks
- `--one-fixup-per-commit`: Generate one fixup per target commit
- `--verbose`: See detailed output

**Example:**
```bash
git absorb --base main --dry-run --verbose
```

## Configuration

For complete configuration reference with all options, see [references/configuration.md](references/configuration.md).

**Most important configuration:**

If you see "WARN stack limit reached, limit: 10", increase the stack size:

```bash
git config absorb.maxStack 50  # Local
git config --global absorb.maxStack 50  # Global
```

By default, git-absorb only searches the last 10 commits. For larger feature branches, increase this to 50 or higher.

**Other useful configs:**
- `oneFixupPerCommit`: One fixup per commit instead of per hunk
- `autoStageIfNothingStaged`: Auto-stage all changes if nothing staged
- `forceAuthor`: Allow absorbing into teammates' commits

See [references/configuration.md](references/configuration.md) for details and all 7 configuration options.

## Recovery

If something goes wrong or you're not satisfied:

```bash
git reset --soft PRE_ABSORB_HEAD
```

This restores the state before running git-absorb. You can also find the commit in `git reflog`.

## How It Works

git-absorb uses commutative patch theory:
1. For each staged hunk, check if it commutes with the last commit
2. If not, that's the parent commit for this change
3. If it commutes with all commits in range, leave it staged (warning shown)
4. Create fixup commits for absorbed changes

This ensures changes are assigned to the correct commits based on line modification history.

## Safety Considerations

- **Always review**: Use manual mode first until comfortable with automatic mode
- **Local only**: Only use on local branches, never on shared/pushed commits
- **Backup**: git-absorb is safe, but `git reflog` is your friend
- **Test after**: Run tests after absorbing to verify nothing broke

## Troubleshooting

**"WARN stack limit reached, limit: 10"**
- git-absorb only searches the last 10 commits by default
- Increase the stack size: `git config absorb.maxStack 50`
- Or use `--base <branch>` to specify the range (e.g., `--base main`)
- See the Configuration section above for details

**"Can't find appropriate commit for these changes"**
- The changes may be too new (modify lines not in recent commits)
- Try increasing the range with `--base <branch>`
- Try increasing stack size: `git config absorb.maxStack 50`
- Changes may need to be in a new commit

**"Command not found: git-absorb"**
- Not installed. See Prerequisites section above for manual installation instructions
- Do NOT attempt automatic installation

**"Conflicts during rebase"**
- Some changes couldn't be absorbed cleanly
- Resolve conflicts manually or use `git rebase --abort`
- Consider breaking changes into smaller pieces
