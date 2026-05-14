# Git Chain Rebase Options

Comprehensive reference for `git chain rebase` command options and conflict handling.

## How Rebase Works

Git chain rebase updates each branch in sequence by:
1. Finding the fork-point (where branch diverged from parent)
2. Rebasing branch commits onto the updated parent
3. Moving to the next branch in the chain

The underlying command is:
```bash
git rebase --keep-empty --onto <parent_branch> <fork_point> <branch>
```

## Command Options

### --step, -s

Rebase one branch at a time, requiring manual confirmation between steps.

```bash
git chain rebase --step
```

**Use when:**
- Anticipating conflicts and want to handle each branch separately
- Need to review changes before proceeding to next branch
- Debugging issues in the rebase process

### --ignore-root, -i

Skip rebasing the first branch onto the root branch.

```bash
git chain rebase --ignore-root
```

**Use when:**
- Only want to update relationships between chain branches
- Root branch has changes you don't want to incorporate yet
- Testing chain structure without full update

### Combined Options

```bash
# Step through without updating from root
git chain rebase --step --ignore-root
```

## Fork-Point Detection

Git chain uses sophisticated fork-point detection:

1. **First**: Checks if branch can be fast-forwarded
2. **Then**: Uses Git's reflog to find original branching point
3. **Fallback**: Uses regular merge-base if fork-point fails

### When Fork-Point Detection Fails

Fork-point may fail when:
- Reflog entries have been cleaned by `git gc`
- Branch was created from an older commit (not tip) of parent
- Repository history was affected by certain operations

In these cases, git-chain falls back to `git merge-base` which finds the most recent common ancestor.

## Squash Merge Detection

Git chain detects when a branch has been squash-merged into its parent:
- Compares the diff between branch and parent
- If empty diff, assumes branch was squash-merged
- Prevents duplicate changes from being rebased

## Conflict Handling

### When Conflicts Occur

1. **Detection**: Git chain stops at the conflicted commit
2. **State**: Repository is left in conflicted state for resolution
3. **Information**: Shows which branch is being rebased and conflict location
4. **Backups**: May create automatic backup branches

### Resolution Steps

```bash
# 1. See which files are conflicted
git status

# 2. Edit conflicted files (look for markers)
# <<<<<<<, =======, >>>>>>>

# 3. Mark as resolved
git add <resolved-files>

# 4. Continue the rebase
git rebase --continue

# 5. Continue with remaining chain branches
git chain rebase
```

### Aborting a Rebase

If conflicts are too complex or you need to reconsider:

```bash
# Abort current rebase
git rebase --abort

# If backup branches exist, restore
git checkout branch-name
git reset --hard branch-name-backup
```

## Example Workflows

### Standard Chain Update

```bash
# Update all branches from root through chain
git chain rebase
```

### Careful Rebase with Review

```bash
# Process one branch at a time
git chain rebase --step

# After each branch:
# - Review the rebased commits
# - Run tests
# - Press Enter to continue or Ctrl+C to stop
```

### Internal Chain Update Only

```bash
# Update branch relationships without incorporating root changes
git chain rebase --ignore-root
```

### Conflict Workflow Example

```bash
$ git chain rebase
Rebasing branch feature/auth onto master...
Auto-merging src/auth.js
CONFLICT (content): Merge conflict in src/auth.js
error: could not apply 1a2b3c4... Add authentication feature

# Resolve the conflict
$ vim src/auth.js
$ git add src/auth.js
$ git rebase --continue
Successfully rebased branch feature/auth

# Git chain continues automatically
Rebasing branch feature/profiles onto feature/auth...
Successfully rebased branch feature/profiles
```

## Recovery Options

### From Backup Branches

If you used `git chain backup` before rebasing:

```bash
git checkout branch-name
git reset --hard branch-name-backup

# Clean up backup after restoring
git branch -D branch-name-backup
```

### From Reflog

Even without backups, Git's reflog tracks all branch movements:

```bash
# See branch history
git reflog show branch-name

# Reset to previous state
git checkout branch-name
git reset --hard branch-name@{1}  # Previous state
git reset --hard branch-name@{2}  # Two states ago
```

### Abort In-Progress Rebase

```bash
git rebase --abort
```

## Best Practices

1. **Create backups first**: `git chain backup` before complex rebases
2. **Use --step for complex chains**: Easier to handle conflicts one branch at a time
3. **Run tests after rebase**: Ensure nothing broke during the update
4. **Don't rebase shared branches**: Only rebase private/local branches
5. **Pull before rebase**: Ensure root branch is up to date
