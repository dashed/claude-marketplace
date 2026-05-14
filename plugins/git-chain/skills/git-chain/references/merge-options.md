# Git Chain Merge Options

Comprehensive reference for `git chain merge` command options, strategies, and reporting.

## How Merge Works

Git chain merge updates each branch by merging the parent branch into it:
1. Checks out each branch in chain order
2. Merges the parent branch into it
3. Creates merge commits (unless fast-forward is possible)

Unlike rebase, merge preserves the original commit history.

## Basic Options

### --verbose, -v

Provides detailed output during the merging process.

```bash
git chain merge --verbose
```

Shows exactly what's happening with each branch, including Git's merge output.

### --ignore-root, -i

Skips merging the root branch into the first chain branch.

```bash
git chain merge --ignore-root
```

**Use when:**
- Only want to propagate changes between chain branches
- Root branch has changes you don't want incorporated yet

### --stay

Don't return to the original branch after merging.

```bash
git chain merge --stay
```

By default, git-chain returns you to your starting branch. Use this flag to remain on the last merged branch.

### --chain=<name>

Operate on a specific chain other than the current one.

```bash
git chain merge --chain=feature-x
```

Allows merging a chain even when not on a branch that belongs to it.

## Merge Behavior Controls

### --simple, -s

Use simple merge mode without advanced detection.

```bash
git chain merge --simple
```

Disables fork-point detection and squashed merge handling for a faster, simpler merge process.

### --fork-point, -f

Use Git's fork-point detection (default behavior).

```bash
git chain merge --fork-point
```

Explicitly enables fork-point detection for finding better merge bases.

### --no-fork-point

Disable fork-point detection, use regular merge-base.

```bash
git chain merge --no-fork-point
```

Can be faster but potentially less accurate. Useful for repositories with limited reflog history.

### --squashed-merge=<mode>

How to handle branches that appear squash-merged.

```bash
# Reset branch to match parent (default)
git chain merge --squashed-merge=reset

# Skip branches that appear squashed
git chain merge --squashed-merge=skip

# Force merge despite detection
git chain merge --squashed-merge=merge
```

## Git Merge Options

### Fast-Forward Behavior

```bash
# Allow fast-forward if possible (default)
git chain merge --ff

# Always create a merge commit
git chain merge --no-ff

# Only allow fast-forward merges (fail if real merge needed)
git chain merge --ff-only
```

### --squash

Create a single commit instead of a merge commit.

```bash
git chain merge --squash
```

Combines all changes from the source branch into a single commit.

### --strategy=<strategy>

Use a specific Git merge strategy.

```bash
git chain merge --strategy=recursive
git chain merge --strategy=ours
git chain merge --strategy=resolve
```

Available strategies:
- `recursive` (default) - 3-way merge
- `resolve` - 3-way merge with fewer renames
- `ours` - Keep our version for all conflicts
- `octopus` - For merging more than two heads

### --strategy-option=<option>

Pass strategy-specific options.

```bash
# Ignore whitespace changes
git chain merge --strategy=recursive --strategy-option=ignore-space-change

# Use patience diff algorithm
git chain merge --strategy=recursive --strategy-option=patience

# Prefer ours in conflicts
git chain merge --strategy=recursive --strategy-option=ours
```

## Reporting Options

### --report-level=<level>

Adjust the level of detail in the merge report.

```bash
# Basic success/failure messages
git chain merge --report-level=minimal

# Summary with counts (default)
git chain merge --report-level=standard

# Comprehensive per-branch details
git chain merge --report-level=detailed
```

### --no-report

Suppress the merge summary report entirely.

```bash
git chain merge --no-report
```

### --detailed-report

Same as `--report-level=detailed`.

```bash
git chain merge --detailed-report
```

## Conflict Handling

### When Conflicts Occur

1. Git chain stops at the conflicted branch
2. Repository is left in conflicted state
3. Shows which branches conflicted and which files

### Resolution Process

```bash
# 1. See conflicted files
git status

# 2. Resolve conflicts (edit files, remove markers)
vim <conflicted-file>

# 3. Stage resolved files
git add <resolved-files>

# 4. Complete the merge
git commit

# 5. Continue with remaining branches
git chain merge
```

### Example Conflict Output

```
Processing branch: feature/auth
Merge made by the 'recursive' strategy.
 src/config.js | 10 ++++++++++
 1 file changed, 10 insertions(+)

Processing branch: feature/profiles
Merge conflict between feature/auth and feature/profiles:
Auto-merging src/models/user.js
CONFLICT (content): Merge conflict in src/models/user.js

Merge Summary for Chain: feature
  Successful merges: 1
  Merge conflicts: 1
     - feature/auth into feature/profiles
```

## Example Workflows

### Update Open PRs Without Breaking Comments

```bash
# Merge preserves commits, keeping PR review comments
git chain merge
git chain push
```

### Update Specific Chain While on Unrelated Branch

```bash
git chain merge --chain=feature-login --verbose
```

### Clean History With No Extra Merge Commits

```bash
git chain merge --ff-only
```

Only updates branches that can be fast-forwarded.

### Handle Squashed Branches

```bash
# Skip branches that appear squash-merged
git chain merge --squashed-merge=skip
```

### Maximum Information for Complex Merges

```bash
git chain merge --verbose --detailed-report
```

## When to Use Merge vs Rebase

### Use Merge When:
- Branches have open pull requests with review comments
- You want to preserve complete development history
- Need to maintain context of commits for reviewers
- Collaborating with others on the same branches
- Branches have already been pushed/shared

### Use Rebase When:
- Working on private branches that haven't been shared
- You prefer a linear, cleaner history
- PRs haven't been reviewed yet
- Want each branch's changes to appear fresh
