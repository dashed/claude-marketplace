# Git Chain Management

Comprehensive reference for creating, modifying, and navigating branch chains.

## Creating Chains

### git chain setup

Create a new chain with multiple branches at once.

```bash
git chain setup <chain_name> <root_branch> <branch_1> <branch_2> ... <branch_N>
```

**Example:**
```bash
git chain setup user-feature main auth profiles settings
```

Creates chain "user-feature" with:
- Root: `main` (not part of the chain)
- Order: `auth` -> `profiles` -> `settings`

### git chain init

Add the current branch to a chain.

```bash
# Add to end of chain (default)
git chain init <chain_name> <root_branch>

# Add at specific position
git chain init <chain_name> <root_branch> --before=<other_branch>
git chain init <chain_name> <root_branch> --after=<other_branch>
git chain init <chain_name> <root_branch> --first
```

**Examples:**
```bash
# Add current branch at end
git checkout notifications
git chain init user-feature main

# Add before settings
git chain init user-feature main --before=settings

# Add after profiles
git chain init user-feature main --after=profiles

# Add as first branch in chain
git chain init user-feature main --first
```

## Viewing Chains

### git chain

Display the current chain (if current branch is part of one).

```bash
git chain
```

Shows:
- Chain name
- Root branch
- All branches in order
- Current branch indicator

### git chain list

List all chains in the repository.

```bash
git chain list
```

## Modifying Chains

### git chain move

Move a branch within its chain or to a different chain.

```bash
# Move to different position in same chain
git chain move --before=<other_branch>
git chain move --after=<other_branch>

# Move to different chain
git chain move --chain=<other_chain_name>
```

**Examples:**
```bash
# Move current branch before settings
git chain move --before=settings

# Move current branch after auth
git chain move --after=auth

# Move to a different chain
git chain move --chain=api-feature
```

### git chain rename

Rename the current chain.

```bash
git chain rename <new_chain_name>
```

**Example:**
```bash
git chain rename user-management
```

## Removing from Chains

### git chain remove

Remove the current branch from its chain.

```bash
git chain remove
```

**Note:** This only removes the branch from the chain metadata. The branch itself still exists.

### git chain remove --chain

Remove the entire chain.

```bash
# Remove the current chain
git chain remove --chain

# Remove a specific chain
git chain remove --chain=<chain_name>
```

**Note:** This removes the chain metadata only. All branches continue to exist.

## Chain Navigation

Navigate between branches in a chain without remembering branch names.

### git chain first

Switch to the first branch in the chain.

```bash
git chain first
```

### git chain last

Switch to the last branch in the chain.

```bash
git chain last
```

### git chain next

Switch to the next branch in the chain.

```bash
git chain next
```

### git chain prev

Switch to the previous branch in the chain.

```bash
git chain prev
```

**Navigation Example:**
```bash
# Chain: auth -> profiles -> settings
# Currently on: profiles

git chain next   # Switches to settings
git chain prev   # Switches back to profiles
git chain first  # Switches to auth
git chain last   # Switches to settings
```

## Utility Commands

### git chain backup

Create backup branches for all branches in the chain.

```bash
git chain backup
```

Creates branches named `<branch-name>-backup` for each branch.

**Use before:**
- Complex rebases
- Experimental changes
- When you want a safety net

### git chain push

Push all branches in the chain to their remotes.

```bash
# Normal push
git chain push

# Force push (uses --force-with-lease for safety)
git chain push --force
```

**Useful for:**
- Updating all PRs at once
- After rebasing the chain

### git chain prune

Remove branches that have been merged to the root branch.

```bash
git chain prune
```

Detects and removes branches whose changes are already in the root branch.

## Chain Storage

Git chain stores relationships in your repository's Git config:
- Which chain a branch belongs to
- The order of branches within a chain
- Each branch's root branch

You can view this with:
```bash
git config --get-regexp chain
```

## Example Workflows

### Creating a Feature Chain from Scratch

```bash
# Create base branch
git checkout -b auth main
# ... develop auth feature ...
git commit -m "Add authentication"

# Create dependent branch
git checkout -b profiles auth
# ... develop profiles feature ...
git commit -m "Add user profiles"

# Create another dependent branch
git checkout -b settings profiles
# ... develop settings feature ...
git commit -m "Add settings page"

# Set up the chain
git chain setup user-features main auth profiles settings
```

### Inserting a Branch Mid-Chain

```bash
# Need to add notifications between profiles and settings
git checkout -b notifications profiles
# ... develop notifications ...
git commit -m "Add notifications"

# Add to chain in correct position
git chain init user-features main --after=profiles
```

### Reorganizing a Chain

```bash
# Move notifications to be first
git checkout notifications
git chain move --before=auth

# Or move to after settings
git chain move --after=settings
```

### Cleaning Up After Merges

```bash
# After auth PR is merged to main
git chain prune  # Removes auth from chain

# Chain is now: profiles -> settings (with main as root)
```

### Splitting a Chain

```bash
# Remove middle branch to create two chains
git checkout profiles
git chain remove

# Now auth is alone in user-features chain
# Create new chain for profiles and settings
git checkout profiles
git chain init profile-features main
git checkout settings
git chain init profile-features main --after=profiles
```
