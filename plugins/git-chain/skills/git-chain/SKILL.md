---
name: git-chain
description: Manage and rebase chains of dependent Git branches (stacked branches). Use when working with multiple dependent PRs, feature branches that build on each other, or maintaining clean branch hierarchies. Automates the tedious process of rebasing or merging entire branch chains.
---

# Git Chain

## Overview

`git chain` manages chains of dependent Git branches where each branch builds upon the previous one (stacked branches). Instead of manually rebasing each branch in sequence, git-chain tracks relationships and updates all branches with a single command.

```
                        I---J---K  feature-2
                       /
              E---F---G  feature-1
             /
A---B---C---D  master
```

When `master` is updated, git-chain rebases `feature-1` onto `master`, then `feature-2` onto `feature-1` automatically.

## When to Use This Skill

Use git-chain when:
- **Stacked PRs**: Working with multiple dependent pull requests that build on each other
- **Feature chains**: Developing a large feature split into incremental branches
- **Review feedback**: Updating base branches requires propagating changes to dependent branches
- **Clean history**: Maintaining linear commit history across dependent branches
- **Avoiding tedious rebasing**: Don't want to manually rebase 3+ branches in sequence

## Prerequisites

**CRITICAL**: Before proceeding, verify that git-chain is installed:

```bash
git chain --version
```

**If git-chain is not installed:**
- **DO NOT** attempt to install it automatically
- **STOP** and inform the user that git-chain is required
- **RECOMMEND** manual installation:

```bash
# From source (requires Rust)
git clone git@github.com:dashed/git-chain.git
cd git-chain
make install

# Or with Cargo
cargo install --path .
```

**If git-chain is not available, exit gracefully and do not proceed with the workflow below.**

## Key Concepts

- **Chain**: A named sequence of branches with dependency order
- **Root Branch**: Foundation branch (typically `main` or `master`) - NOT part of the chain
- **Branch Order**: The sequence in which branches depend on each other

**Important**: A branch can belong to at most one chain.

## Basic Workflow

### Step 1: Set Up a Chain

Create a chain with your stacked branches:

```bash
git chain setup my-feature master feature-1 feature-2 feature-3
```

This creates chain "my-feature" with `master` as root and branches in order: `feature-1` -> `feature-2` -> `feature-3`.

### Step 2: View the Chain

```bash
git chain          # Show current chain (if on a chain branch)
git chain list     # List all chains in the repository
```

### Step 3: Update the Chain

When the root branch or any branch in the chain has new commits:

**Option A: Rebase (rewrites history, clean linear commits)**
```bash
git chain rebase
```

**Option B: Merge (preserves history, creates merge commits)**
```bash
git chain merge
```

## Common Patterns

### Pattern 1: Stacked PR Workflow

**Scenario**: Working on a feature split into 3 PRs: auth, profiles, settings

```bash
# Create branches
git checkout -b auth main
# ... make auth changes, commit ...
git checkout -b profiles auth
# ... make profile changes, commit ...
git checkout -b settings profiles
# ... make settings changes, commit ...

# Set up the chain
git chain setup user-feature main auth profiles settings

# After main receives new commits, update all branches
git chain rebase
git chain push --force  # Update all PRs
```

### Pattern 2: Review Feedback on Base Branch

**Scenario**: Reviewer requested changes on `auth` branch (first PR)

```bash
git checkout auth
# ... make changes, commit ...

# Update dependent branches automatically
git chain rebase
```

### Pattern 3: Adding a New Branch to Existing Chain

**Scenario**: Need to add `notifications` branch between `profiles` and `settings`

```bash
git checkout -b notifications profiles
# ... make changes, commit ...

# Add to chain with specific position
git chain init user-feature main --after=profiles
```

## Core Commands Reference

| Command | Description |
|---------|-------------|
| `git chain setup <name> <root> <b1> <b2>...` | Create chain with branches |
| `git chain init <name> <root>` | Add current branch to chain |
| `git chain` | Display current chain |
| `git chain list` | List all chains |
| `git chain rebase` | Rebase all branches (rewrites history) |
| `git chain merge` | Merge all branches (preserves history) |
| `git chain push` | Push all branches to remotes |
| `git chain push --force` | Force push all branches |
| `git chain first/last/next/prev` | Navigate between chain branches |
| `git chain backup` | Create backup branches |
| `git chain prune` | Remove branches merged to root |
| `git chain remove` | Remove current branch from chain |
| `git chain remove --chain` | Delete entire chain |

## Rebase vs Merge

**Use Rebase When:**
- Branches are private/not shared
- You prefer clean, linear history
- PRs haven't been reviewed yet

**Use Merge When:**
- Branches have open PRs with review comments
- You need to preserve commit history
- Collaborating with others on the same branches

## Advanced Usage

For comprehensive coverage of all flags and advanced patterns, see:
- [references/rebase-options.md](references/rebase-options.md) - All rebase flags and conflict handling
- [references/merge-options.md](references/merge-options.md) - All merge flags and strategies
- [references/chain-management.md](references/chain-management.md) - Moving, reorganizing, and removing chains

**Key flags:**
- `--step, -s`: Process one branch at a time (rebase)
- `--ignore-root, -i`: Skip updating first branch from root
- `--verbose, -v`: Detailed output (merge)
- `--chain=<name>`: Operate on specific chain
- `--no-ff`: Force merge commits even for fast-forwards
- `--squashed-merge=<mode>`: Handle squash-merged branches (reset/skip/merge)

## Recovery

If something goes wrong during rebase:

```bash
# Abort in-progress rebase
git rebase --abort

# Restore from backup (if created with git chain backup)
git checkout branch-name
git reset --hard branch-name-backup

# Or use reflog
git reflog
git reset --hard branch-name@{1}
```

## Handling Conflicts

When conflicts occur during `git chain rebase`:

1. Git-chain pauses at the conflicted commit
2. Resolve conflicts manually in the marked files
3. `git add <resolved-files>`
4. `git rebase --continue`
5. `git chain rebase` (continues with remaining branches)

## Troubleshooting

**"Branch not part of any chain"**
- Run `git chain list` to see available chains
- Use `git chain init` to add the current branch to a chain

**"Cannot find fork-point"**
- Reflog may have been cleaned up
- Use `--no-fork-point` flag to fall back to merge-base

**Rebase conflicts on every update**
- Consider using `git chain merge` instead to preserve history
- Or use `--step` flag to handle each branch individually

**Squash-merged branch causing issues**
- git-chain detects squash merges; use `--squashed-merge=skip` to skip them
- Or use `--squashed-merge=reset` (default) to reset branch to parent
