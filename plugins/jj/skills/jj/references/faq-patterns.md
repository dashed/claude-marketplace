# Common Patterns & FAQ

Practical solutions to problems jj users frequently encounter.

## Table of Contents

- [Private/Local-Only Changes](#privatelocal-only-changes)
- [Accidentally Changed Wrong Commit](#accidentally-changed-wrong-commit)
- [Resume Working on a Change](#resume-working-on-a-change)
- [Reverting a Merge Commit](#reverting-a-merge-commit)
- [Conflicted Bookmarks (??)](#conflicted-bookmarks-)
- [Hidden/Lost Commits](#hiddenlost-commits)
- [Elided Revisions in Log](#elided-revisions-in-log)
- [Scratch Files & Selective Tracking](#scratch-files--selective-tracking)
- [Bookmark Doesn't Move After Commit](#bookmark-doesnt-move-after-commit)
- [Push Says "Nothing Changed"](#push-says-nothing-changed)
- [Interactive Staging Equivalent](#interactive-staging-equivalent)
- [Interactive Rebase Equivalent](#interactive-rebase-equivalent)
- [Empty Merge Commits](#empty-merge-commits)
- [Customizing Default Log Revset](#customizing-default-log-revset)

## Private/Local-Only Changes

**Problem:** You have local config files or credentials you need in your working copy but must never push.

**Solution:** Create a private commit off trunk, then merge it into your working copy:

```bash
# Create a private commit branched from main
jj new main -m "private: my local config"
# Make your private changes (edit config files, etc.)

# Now merge your feature branch with the private commit
jj new feature_change_id private_change_id
# Work normally — squash real work into the feature commit
jj squash --into feature_change_id
```

Prevent accidental pushes with `git.private-commits`:

```bash
jj config set --user git.private-commits "description('private:*')"
```

Any commit whose description starts with `private:` is now blocked from push.

## Accidentally Changed Wrong Commit

**Problem:** You edited files in a commit that should have been a separate change.

**Solution:** Use `jj evolog` to find the last good state, then split the work:

```bash
# Find the commit ID of the last good version
jj evolog --patch

# Create a new commit on top of the last good version
jj new <good_commit_id> -m "new feature work"

# Restore the current (wrong) state into the new commit
jj restore --from <current_commit_id>

# Move any bookmarks and abandon the bad commit
jj bookmark move --from <current_commit_id> --to <good_commit_id>
jj abandon <current_commit_id>
```

For simple cases, `jj split -i` can interactively divide changes between two commits.

## Resume Working on a Change

**Problem:** You want to add more changes to an earlier commit.

**Recommended approach** — `jj new` + `jj squash`:

```bash
# Create a child commit on top of the target
jj new <target_change_id>
# Make your edits...
jj squash  # folds changes into the parent
```

**Alternative** — `jj edit` (use with caution):

```bash
jj edit <target_change_id>
# Changes go directly into the target commit
```

`jj edit` is simpler but hides what you changed (no diff between old and new state). Avoid `jj edit` on commits with conflicts — you may accidentally break conflict markers.

## Reverting a Merge Commit

**Problem:** `jj revert -r <merge>` produces an empty commit because merge commits are typically "empty" (no changes relative to auto-merged parents).

**Solution:** Restore the state from the first parent to undo the merge:

```bash
# Given: C is a merge of B and D
#   C
#  / \
# B   D
# |  /
# A

# Create a revert commit on top of the merge
jj new C
# Restore to the state before the merge (first parent)
jj restore --from B
jj describe -m "Revert merge of D into B"
```

## Conflicted Bookmarks (??)

**Problem:** A bookmark shows `??` after its name, meaning it points to multiple commits.

This happens when jj can't determine the correct position — typically after concurrent operations or conflicting fetches.

**Solution:**

```bash
# See all commits associated with the conflicted bookmark
jj bookmark list

# Resolve by moving the bookmark to the correct commit
jj bookmark move <bookmark_name> --to <correct_commit_id>
```

## Hidden/Lost Commits

**Problem:** A commit you created isn't showing up in `jj log`.

`jj log` only shows a curated subset by default (local commits and their immediate parents).

**Step 1:** Check if it exists at all:

```bash
# Search across ALL commits
jj log -r 'all()'

# Or search by a known commit ID
jj log -r <commit_id>
```

**Step 2:** If the commit shows as "hidden" (abandoned or rewritten):

```bash
# Make it visible again by creating a child
jj new <commit_id>
```

If it's not in `all()`, it was likely garbage-collected. Check the operation log for history: `jj op log`.

## Elided Revisions in Log

**Problem:** `jj log` shows "(elided revisions)" between two commits.

This means the commits are related (ancestor/descendant) but the intermediate commits aren't in your revset.

**Solution:** Use `connected()` to fill in the gaps:

```bash
# Before: shows elided revisions
jj log -r 'abc | xyz'

# After: shows all commits connecting them
jj log -r 'connected(abc | xyz)'
```

## Scratch Files & Selective Tracking

**Problem:** You want scratch notes or temp files in the repo without committing them.

**Option 1:** Use `.gitignore` patterns:

```bash
# Add to .gitignore (or global gitignore)
*.scratch
scratch/
```

**Option 2:** Control auto-tracking via config:

```toml
# In jj config — only track files matching the pattern
[snapshot]
auto-track = "glob:**/*.rs"  # only track Rust files automatically
# auto-track = "none()"      # don't auto-track anything new
```

Untracked files can still be added explicitly with `jj file track <path>`. Changes to already-tracked files are always snapshotted.

## Bookmark Doesn't Move After Commit

**Problem:** After `jj new` or `jj commit`, the bookmark stays on the old commit.

Unlike Git, jj has no concept of a "current bookmark." Bookmarks don't automatically follow HEAD.

**Solution:** Move bookmarks explicitly:

```bash
jj bookmark move <bookmark_name> --to <target>
```

## Push Says "Nothing Changed"

**Problem:** `jj git push --all` says "Nothing changed" even though you have new commits.

`--all` pushes all **bookmarks**, not all commits. If your commit has no bookmark, nothing pushes.

**Solution:**

```bash
# Option 1: Auto-create a bookmark and push
jj git push --change <change_id>

# Option 2: Manually create a bookmark first
jj bookmark create <name> -r <change_id>
jj git push
```

## Interactive Staging Equivalent

**Problem:** You want the equivalent of `git add -p` / `git commit -p`.

In jj, changes are already in the working-copy commit. Use split to interactively separate them:

```bash
# Equivalent of git add -p && git commit
jj split -i       # interactively split working copy into two commits
jj commit -i      # same thing (practically identical)

# Equivalent of git commit --amend -p
jj squash -i      # interactively choose which changes to squash into parent
```

## Interactive Rebase Equivalent

**Problem:** You want the equivalent of `git rebase -i`.

jj doesn't have a single interactive rebase command. Instead, use targeted operations:

```bash
# Reorder: move commit C before B in a chain A-B-C
jj rebase -r C -B B

# Move a commit to a different location
jj rebase -r <commit> -A <new_parent>   # after new parent
jj rebase -r <commit> -B <new_child>    # before new child

# Squash commits together
jj squash         # squash working copy into parent
jj squash -r B    # squash B into its parent

# Split a commit
jj split -i       # interactively split into two

# For complex reordering
jj arrange        # experimental — reorder a chain interactively
```

## Empty Merge Commits

**Problem:** Most merge commits show as "(empty)" in `jj log`.

This is expected. jj defines changes relative to auto-merged parents. A clean merge (no conflict resolution, no extra changes) has no diff compared to what the auto-merge produced.

A non-empty merge means it contains conflict resolutions or additional changes beyond the merge itself.

This definition is consistent throughout jj — `jj diff -r`, `jj rebase`, and `files()` revsets all use the same logic.

## Customizing Default Log Revset

**Problem:** `jj log` doesn't show the commits you want to see by default.

**Solution:** Override the `revsets.log` config:

```toml
[revsets]
# Show all commits (excluding root)
log = ".."

# Show local work plus recent main
log = "ancestors(mine(), 5) | main"
```

To see everything once without changing config:

```bash
jj log -r '..'        # all visible commits
jj log -r 'all()'     # literally everything, including hidden
```

## Megamerge Pattern (Parallel Integration)

Work on multiple features simultaneously while continuously verifying they integrate:

```bash
# Create parallel work streams off main
jj new main -m "feature A"
# ... work on feature A commits (a1, a2) ...
jj new main -m "feature B"
# ... work on feature B commits (b1, b2) ...

# Create integration merge combining all streams
jj new a2 b2 -m "integration: verify A + B together"
jj new                            # Working commit on top of merge

# Work here - build/test with everything combined
# Route changes back to the right branch:
jj squash --into a2 -k            # Move changes to feature A, keep WC
jj squash -i --into b2            # Interactively pick changes for feature B

# Or let jj figure it out automatically:
jj absorb                         # Routes each hunk to correct ancestor
```

The `-k`/`--keep-emptied` flag preserves the integration commit even after squashing content out. This pattern works because jj records conflicts without blocking operations.
