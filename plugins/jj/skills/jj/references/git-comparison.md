# Git to jj Command Comparison

This reference maps common Git commands and workflows to their jj equivalents.

## Quick Reference Table

| Git Command | jj Equivalent | Notes |
|-------------|---------------|-------|
| `git init` | `jj git init` | Creates colocated repo by default |
| `git clone` | `jj git clone` | Creates colocated repo by default |
| `git status` | `jj status` | Alias: `jj st` |
| `git log` | `jj log` | Shows graph by default |
| `git log --oneline` | `jj log --no-graph` | Or customize template |
| `git show` | `jj show` | |
| `git diff` | `jj diff` | |
| `git diff --staged` | N/A | No staging area in jj |
| `git add` | N/A | Auto-tracked |
| `git add -p` | `jj split -i` | Interactive commit splitting |
| `git commit` | `jj commit` or `jj new` | Different workflow |
| `git commit --amend` | `jj describe` + changes | Working copy is always amendable |
| `git commit --amend -m` | `jj describe -m "msg"` | |
| `git reset HEAD~` | `jj squash` | Move changes to parent |
| `git reset --hard` | `jj restore` | |
| `git checkout <file>` | `jj restore <file>` | |
| `git checkout <branch>` | `jj new <bookmark>` | Creates new working copy |
| `git switch` | `jj new` | |
| `git branch` | `jj bookmark` | Alias: `jj b` |
| `git branch -d` | `jj bookmark delete` | |
| `git merge` | `jj new <A> <B>` | Creates merge commit |
| `git rebase` | `jj rebase` | More powerful |
| `git rebase -i` | `jj squash -i`, `jj split` | Different approach |
| `git cherry-pick` | `jj new <rev>; jj squash` | Or `jj duplicate` |
| `git revert` | `jj revert` | |
| `git stash` | N/A | Not needed - use `jj new` |
| `git stash pop` | N/A | Use `jj squash` |
| `git fetch` | `jj git fetch` | |
| `git pull` | `jj git fetch` + `jj rebase` | No single command |
| `git push` | `jj git push` | |
| `git blame` | `jj file annotate` | |
| `git reflog` | `jj op log` | More powerful |
| `git tag` | `jj tag` | |

## Workflow Comparisons

### Creating a New Commit

**Git:**
```bash
git add .
git commit -m "message"
```

**jj:**
```bash
# Changes are auto-tracked
jj describe -m "message"
jj new  # Start new work
# Or:
jj commit -m "message"  # Same effect
```

### Amending the Last Commit

**Git:**
```bash
git add .
git commit --amend
```

**jj:**
```bash
# Changes automatically amend current working copy
# Just edit files, done!
# To change message:
jj describe -m "new message"
```

### Interactive Staging

**Git:**
```bash
git add -p
git commit
```

**jj:**
```bash
# Split current changes into separate commits
jj split -i
# Or squash parts into parent
jj squash -i
```

### Undoing Last Commit (Keep Changes)

**Git:**
```bash
git reset HEAD~
```

**jj:**
```bash
jj squash  # Moves changes to parent, abandons if empty
```

### Discarding Changes

**Git:**
```bash
git checkout -- .
git reset --hard
```

**jj:**
```bash
jj restore  # Restore from parent
```

### Switching Branches

**Git:**
```bash
git checkout feature
# or
git switch feature
```

**jj:**
```bash
jj new feature  # Create working copy on feature
# Or to edit feature directly:
jj edit feature
```

### Creating a Branch

**Git:**
```bash
git checkout -b feature
# or
git switch -c feature
```

**jj:**
```bash
jj bookmark create feature
# Then work - changes go to working copy
```

### Stashing Changes

**Git:**
```bash
git stash
# ... do other work ...
git stash pop
```

**jj:**
```bash
# Not needed! Working copy is already a commit.
# To work on something else:
jj new main  # Start new work from main
# ... do other work ...
jj edit <original-change-id>  # Go back
```

### Rebasing a Branch

**Git:**
```bash
git checkout feature
git rebase main
```

**jj:**
```bash
jj rebase -b feature -d main
# Or if on feature:
jj rebase -d main
```

### Interactive Rebase

**Git:**
```bash
git rebase -i HEAD~5
```

**jj:**
```bash
# Different approach - use individual commands:
jj squash        # Combine commits
jj split         # Split commits
jj rebase        # Reorder
jj describe      # Edit messages
jj abandon       # Drop commits
```

### Cherry-picking

**Git:**
```bash
git cherry-pick <commit>
```

**jj:**
```bash
jj new <commit>        # Create child of commit
jj rebase -r @ -d main # Move to destination
# Or simpler:
jj duplicate <commit>
jj rebase -r <duplicated> -d main
```

### Resolving Conflicts

**Git:**
```bash
git merge feature
# Conflicts occur
# Edit files
git add .
git commit
```

**jj:**
```bash
jj new main feature  # Create merge (may have conflicts)
# Conflicts are recorded in commit
jj log  # Shows conflict marker
# Edit files
# Changes auto-commit, conflict resolved
```

### Undoing Operations

**Git:**
```bash
git reflog
git reset --hard HEAD@{2}
```

**jj:**
```bash
jj op log
jj op restore <op-id>
# Or simply:
jj undo
```

### Viewing History at a Point

**Git:**
```bash
git log HEAD@{yesterday}
```

**jj:**
```bash
jj --at-op=<op-id> log
```

## Conceptual Differences

### No Staging Area

Git has a staging area (index) between working directory and commits. jj doesn't:

- **Git**: working directory → staging area → commit
- **jj**: working copy (IS a commit) → new commit

### Working Copy is a Commit

In jj, the working copy is always a commit. Changes are automatically recorded:

- No "dirty" working directory
- No lost changes from checkout
- Can always undo

### Change IDs vs Commit IDs

- **Git**: Only commit hashes (SHA), change when commit is amended
- **jj**: Change IDs (stable) + Commit IDs (change on rewrite)

Use change IDs (`kntqzsqt`) when referring to commits.

### Conflicts as First-Class Citizens

- **Git**: Conflicts block operations, must resolve immediately
- **jj**: Conflicts are recorded in commits, resolve when convenient

### Operations are Atomic

Every jj operation is recorded and reversible:

```bash
jj op log      # See all operations
jj undo        # Undo last operation
jj op restore  # Go to any point
```

### Bookmarks vs Branches

- **Git branches**: Automatically move with commits
- **jj bookmarks**: Named pointers, move explicitly

```bash
# Git: branch moves with HEAD
git commit  # branch advances

# jj: bookmark stays unless moved
jj new      # bookmark doesn't move
jj bookmark set <name>  # explicit move
```

## Common Patterns

### "Pull and Rebase"

**Git:**
```bash
git pull --rebase
```

**jj:**
```bash
jj git fetch
jj rebase -d <remote>@origin  # or main@origin
```

### "Push New Branch"

**Git:**
```bash
git push -u origin feature
```

**jj:**
```bash
jj git push --bookmark feature
# Or create bookmark from change:
jj git push --change <change-id>
```

### "Squash Last N Commits"

**Git:**
```bash
git rebase -i HEAD~3
# Mark commits as squash
```

**jj:**
```bash
# Squash into parent repeatedly:
jj squash -r <commit>
jj squash -r <commit>
# Or use revsets:
jj squash --from 'trunk()..@'
```

### "Edit Old Commit"

**Git:**
```bash
git rebase -i <commit>^
# Mark commit as edit
# Make changes
git commit --amend
git rebase --continue
```

**jj:**
```bash
jj edit <commit>
# Make changes (auto-committed)
jj new  # Continue with new work
# Descendants auto-rebased!
```
