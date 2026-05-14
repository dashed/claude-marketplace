# Advanced Usage

This document covers all command-line flags and advanced usage patterns for git-absorb.

## Complete Flag Reference

### Core Flags

#### `--and-rebase` / `-r`
Run rebase automatically after creating fixup commits.

**When to use:**
- You trust git-absorb's output
- You want a streamlined workflow
- Changes are straightforward

**Example:**
```bash
git absorb --and-rebase
```

#### `--dry-run` / `-n`
Preview what would happen without making any changes.

**When to use:**
- First time using git-absorb on a branch
- Testing if changes will absorb correctly
- Understanding which commits would be affected

**Example:**
```bash
git absorb --dry-run
```

#### `--base <commit>` / `-b <commit>`
Specify the base commit for the absorb stack.

**When to use:**
- Feature branch has more than 10 commits (default limit)
- Want to absorb into commits since a specific branch point
- Getting "stack limit reached" warnings

**Examples:**
```bash
# Absorb into all commits since main
git absorb --base main

# Absorb into all commits since specific SHA
git absorb --base abc123
```

### Safety and Control Flags

#### `--force`
Skip all safety checks (equivalent to all `--force-*` flags).

**When to use:**
- Need to bypass author filtering AND detached HEAD restrictions
- Understand the risks and have reviewed changes

**Warning:** Use with caution. This disables protective checks.

**Example:**
```bash
git absorb --force --and-rebase
```

#### `--force-author`
Generate fixups for commits not authored by you.

**When to use:**
- Pair programming with teammate's commits
- Maintaining a branch with multiple authors
- Cleaning up inherited code

**Example:**
```bash
git absorb --force-author --and-rebase
```

#### `--force-detach`
Generate fixups even when HEAD is detached (not on a branch).

**When to use:**
- Working in detached HEAD state intentionally
- Cherry-picking workflow
- Advanced git operations

**Example:**
```bash
git absorb --force-detach
```

### Output Format Flags

#### `--one-fixup-per-commit` / `-F`
Generate only one fixup commit per target commit (instead of per hunk).

**When to use:**
- Want cleaner commit history during rebase
- Multiple hunks absorbing into same commit
- Prefer consolidated fixups

**Example:**
```bash
git absorb --one-fixup-per-commit --and-rebase
```

#### `--squash` / `-s`
Create squash commits instead of fixup commits.

**When to use:**
- Want to edit commit messages during rebase
- Need to document why changes were added
- Prefer squash over fixup in workflow

**Example:**
```bash
git absorb --squash --and-rebase
```

**Note:** When using this flag, all references to "fixup commits" should be read as "squash commits".

### Advanced Matching Flags

#### `--whole-file` / `-w`
Match the first commit that touched the same file (not just the same lines).

**When to use:**
- Adding new functions to a file
- Changes don't overlap with existing lines
- Want to absorb into file's original commit

**Warning:** Use with care! This is less precise than line-based matching.

**Example:**
```bash
git absorb --whole-file
```

### Information Flags

#### `--verbose` / `-v`
Display more detailed output about the absorption process.

**When to use:**
- Debugging unexpected behavior
- Understanding how changes are being matched
- Learning how git-absorb works

**Example:**
```bash
git absorb --verbose --dry-run
```

#### `--version` / `-V`
Display git-absorb version information.

```bash
git absorb --version
```

#### `--help` / `-h`
Display help information.

```bash
git absorb --help
```

### Options

#### `--message <MESSAGE>` / `-m <MESSAGE>`
Use the same commit message body for all generated fixup commits.

**When to use:**
- Want consistent messaging across fixups
- Documenting a batch of related changes
- Organization requires specific commit formats

**Example:**
```bash
git absorb -m "Address PR review feedback" --and-rebase
```

#### `-- <REBASE_OPTIONS>`
Pass options to git rebase (must be last argument, requires `--`).

**When to use:**
- Need to pass specific rebase options
- Custom rebase behavior required
- Using with `--and-rebase` flag

**Example:**
```bash
git absorb --and-rebase -- --autostash
```

**Note:** Only valid when `--and-rebase` is used.

## Advanced Patterns

### Pattern 1: Large Feature Branch

**Scenario:** Working on a feature branch with 50+ commits

```bash
# Option 1: Use --base to specify range
git add <fixed-files>
git absorb --base main --and-rebase

# Option 2: Configure maxStack permanently
git config absorb.maxStack 100
git add <fixed-files>
git absorb --and-rebase
```

### Pattern 2: Selective Absorption

**Scenario:** Only want to absorb specific files, not everything staged

```bash
# Stage only the files you want to absorb
git add file1.py file2.py

# Other staged files won't be absorbed
git absorb --and-rebase
```

### Pattern 3: Review Before Committing

**Scenario:** Want to inspect fixup commits before rebasing

```bash
# Step 1: Create fixup commits (no rebase)
git absorb

# Step 2: Review what was created
git log --oneline -10

# Step 3: If satisfied, rebase manually
git rebase -i --autosquash main

# If not satisfied, reset
git reset --soft PRE_ABSORB_HEAD
```

### Pattern 4: Team Branch with Multiple Authors

**Scenario:** Fixing bugs across a shared feature branch

```bash
# Allow absorbing into teammates' commits
git absorb --force-author --and-rebase

# Or configure permanently for this repo
git config absorb.forceAuthor true
git absorb --and-rebase
```

### Pattern 5: Verbose Debugging

**Scenario:** Understanding why changes aren't absorbing

```bash
# Use verbose mode with dry-run
git absorb --verbose --dry-run

# Look for messages like:
# "Can't find appropriate commit for hunk..."
# "Stack limit reached..."
```

### Pattern 6: Consolidate Multiple Hunks

**Scenario:** Many small fixes to the same commit, want one fixup

```bash
git absorb --one-fixup-per-commit --and-rebase
```

### Pattern 7: Detached HEAD Workflow

**Scenario:** Working in detached HEAD state (cherry-pick, bisect, etc.)

```bash
git absorb --force-detach --and-rebase
```

## Flag Combinations

### Recommended Combinations

**Safe exploration:**
```bash
git absorb --dry-run --verbose
```

**Aggressive auto-fix:**
```bash
git absorb --force --and-rebase
```

**Team branch cleanup:**
```bash
git absorb --force-author --one-fixup-per-commit --and-rebase
```

**Large feature branch:**
```bash
git absorb --base main --verbose --and-rebase
```

## Common Issues and Solutions

### "Can't find appropriate commit"

**Cause:** Changes are too new or don't match any commits in range

**Solutions:**
```bash
# Increase range
git absorb --base main

# Check if file exists in commits
git log --oneline --follow <file>

# Consider if change belongs in new commit
```

### "Stack limit reached"

**Cause:** Default 10-commit limit exceeded

**Solutions:**
```bash
# Use --base
git absorb --base main --and-rebase

# Or increase maxStack
git config absorb.maxStack 50
```

### "Conflicts during rebase"

**Cause:** Changes can't be cleanly absorbed

**Solutions:**
```bash
# Abort and try manual approach
git rebase --abort
git reset --soft PRE_ABSORB_HEAD

# Or resolve conflicts manually
# (follow git's conflict resolution prompts)
```

### Unintended absorption into wrong commit

**Cause:** git-absorb matched lines incorrectly

**Prevention:**
```bash
# Always use --dry-run first
git absorb --dry-run

# Review before rebasing
git absorb  # no --and-rebase
git log --oneline -10  # review fixups
```

**Recovery:**
```bash
git reset --soft PRE_ABSORB_HEAD
```
