# Git Recovery: Undo, Rescue & "Oh No"

Recovering from mistakes and getting back lost work. Reach for this file after a bad `reset --hard`, a deleted branch, a botched merge/rebase/amend, a dropped stash, or any "I think I just lost a commit" moment.

**The one mental model that makes recovery work:** Git almost never *deletes* commits. A commit you can no longer see has merely become **unreachable** — no branch, tag, or `HEAD` points to it — but the object still sits in `.git/objects` until garbage collection prunes it (weeks later, by default; see [Reflog expiry & the gc deadline](#reflog-expiry--the-gc-deadline)). Recovery is almost always the act of **finding the dangling commit's SHA and pointing a ref at it again**. The reflog and `git fsck` are how you find it.

## Table of contents

- [The reflog: your first resort](#the-reflog-your-first-resort)
- [Recovering lost commits and branches](#recovering-lost-commits-and-branches)
- [Special refs (ORIG_HEAD, MERGE_HEAD, …)](#special-refs-orig_head-merge_head-)
- [The three reset modes (and `--merge`/`--keep`)](#the-three-reset-modes-and---merge--keep)
- [Undoing common operations](#undoing-common-operations)
- [`restore` and `switch` for undo](#restore-and-switch-for-undo)
- [`git fsck`: dangling and unreachable objects](#git-fsck-dangling-and-unreachable-objects)
- [Recovering dropped stashes](#recovering-dropped-stashes)
- [Reflog expiry & the gc deadline](#reflog-expiry--the-gc-deadline)
- ["Oh no" quick reference](#oh-no-quick-reference)

## The reflog: your first resort

The **reflog** records every time a ref's tip moved in *your local repo* — commits, resets, rebases, merges, checkouts, amends. It is local-only, never pushed, and it is what makes most "lost" work recoverable.

```bash
git reflog                      # HEAD's reflog: every move of HEAD, newest first
git reflog show <branch>        # a specific branch's reflog (e.g. main, feature)
git reflog show stash           # the stash reflog (see Recovering dropped stashes)
```

`git reflog show` is just an alias for `git log -g --abbrev-commit --pretty=oneline`, so it accepts any `git log` option (`--date=iso`, `-p`, `--all`, etc.).

```bash
git reflog --date=iso           # show absolute timestamps instead of "2 hours ago"
git log -g --oneline HEAD       # the same data via git log -g
```

**Reflog revision syntax** (see [internals-plumbing.md](internals-plumbing.md) for full `gitrevisions`):

| Spec | Means |
|------|-------|
| `HEAD@{2}` | where `HEAD` pointed **2 moves ago** |
| `main@{1}` | where `main` pointed **1 move ago** |
| `main@{one.week.ago}` | where `main` pointed one week ago *in this repo* |
| `@{-1}` | the **branch** you were on 1 checkout ago (note: different from `HEAD@{1}`) |

**Footgun — `HEAD@{n}` vs `@{-n}`:** `HEAD@{1}` is the *prior position of HEAD* (a commit); `@{-1}` is the *previously checked-out branch*. They are not the same.

**Footgun — per-worktree reflogs:** `HEAD` has a separate reflog in each worktree. A commit visible in another worktree's `HEAD` reflog won't appear in this one. Branch reflogs are shared.

```bash
git reflog exists refs/heads/main   # exit 0 if a reflog exists for the ref
git reflog list                     # list all refs that have a reflog
```

## Recovering lost commits and branches

**Lost a commit** (bad reset, amend, rebase, dropped during `rebase -i`): find it in the reflog, then re-attach a ref.

```bash
git reflog                       # find the SHA of the good state, e.g. abc1234
git switch -c rescue abc1234     # safest: make a new branch at it
# or move the current branch tip back onto it:
git reset --hard abc1234         # ⚠️ Destructive to working tree — see reset modes
# or just look first:
git show abc1234                 # inspect before committing to anything
```

**Deleted a branch** (`git branch -D feature`): the deletion is logged. `git branch -d/-D` prints the SHA it deleted (`Deleted branch feature (was abc1234)`) — scroll up to find it. Otherwise:

```bash
git reflog | grep -i "feature"          # checkouts/commits on it appear in HEAD reflog
git switch -c feature abc1234           # recreate the branch at the recovered SHA
```

A branch's *own* reflog is removed when the branch is deleted, so search `HEAD`'s reflog (above) or fall back to [`git fsck`](#git-fsck-dangling-and-unreachable-objects) for the dangling tip.

**Always recover onto a fresh branch first** (`git switch -c rescue <sha>`) rather than `reset --hard`-ing your current branch — it's non-destructive and lets you verify before discarding anything.

## Special refs (ORIG_HEAD, MERGE_HEAD, …)

Git writes these pseudo-refs in `$GIT_DIR` during operations. They are recovery gold — most "undo X" recipes below are just `reset`/`restore` to one of them. (Source: `gitrevisions`.)

| Ref | Set by | Recovery use |
|-----|--------|--------------|
| `ORIG_HEAD` | `reset`, `merge`, `rebase`, `pull`, `am` (anything that moves HEAD "drastically") | Undo that operation: `git reset --hard ORIG_HEAD` |
| `MERGE_HEAD` | `git merge` (while in progress / conflicted) | The commit(s) being merged in; `git merge --abort` uses it |
| `FETCH_HEAD` | `git fetch` (and `pull`) | What was just fetched; `git merge FETCH_HEAD` |
| `REBASE_HEAD` | rebase, when stopped (conflict or `edit`) | The commit currently being applied; `git show REBASE_HEAD` |
| `REVERT_HEAD` | `git revert` (in progress) | Commit being reverted; `git revert --abort` |
| `CHERRY_PICK_HEAD` | `git cherry-pick` (in progress) | Commit being picked; `git cherry-pick --abort` |
| `AUTO_MERGE` | `ort` strategy after a conflicted merge | A **tree** of the conflicted auto-merge result (diff against it to see what merged cleanly) |
| `BISECT_HEAD` | `git bisect --no-checkout` | Current commit to test |

**Footgun — `ORIG_HEAD` is single-slot and volatile.** It only remembers the *most recent* drastic move. A second `reset`/`rebase`/`merge` overwrites it. If you might need the previous tip later, capture it now: `git branch backup ORIG_HEAD`. During a rebase, `ORIG_HEAD` is set at the start but is *not guaranteed* to still point there at the end (other commands during the rebase can change it) — the robust fallback is the branch reflog, `<branch>@{1}`.

## The three reset modes (and `--merge`/`--keep`)

`git reset [<mode>] [<commit>]` moves the current branch tip to `<commit>` (default `HEAD`) and, depending on mode, also rewrites the index and/or working tree. **`ORIG_HEAD` is set to the old tip before the move**, so a wrong reset is itself undoable: `git reset --hard ORIG_HEAD`.

| Mode | Moves HEAD | Resets index | Resets working tree | Use when |
|------|:---------:|:------------:|:-------------------:|----------|
| `--soft` | ✓ | — | — | Keep everything staged; recombine/re-commit (e.g. squash last N) |
| `--mixed` *(default)* | ✓ | ✓ | — | Unstage, but keep edits in the working tree |
| `--hard` | ✓ | ✓ | ✓ **⚠️** | Throw away staged + working changes; match `<commit>` exactly |
| `--merge` | ✓ | ✓ | resets changed files, **keeps unstaged edits** | Back out of a conflicted merge while preserving local work |
| `--keep` | ✓ | ✓ | keeps local edits, **aborts if they'd be clobbered** | Drop commits but keep working-tree edits, safely |

```bash
# Squash the last 3 commits into one, keeping the combined changes staged:
git reset --soft HEAD~3 && git commit          # author a fresh single commit

# Unstage everything but keep your edits (the default):
git reset                                       # == git reset --mixed HEAD

# Nuke local state back to a known commit (DANGEROUS):
git reset --hard origin/main                    # ⚠️ discards uncommitted work
```

**⚠️ Destructive: `--hard`.** It overwrites tracked files and the index from `<commit>`, and may remove files. **Uncommitted changes destroyed by `--hard` are NOT in the reflog** — the reflog tracks commits, not your working tree. They are only recoverable if they were ever staged (see [`git fsck`](#git-fsck-dangling-and-unreachable-objects), which can find dangling blobs you `git add`-ed). *Committed* work, by contrast, is always reachable via `ORIG_HEAD`/reflog.

`--merge` and `--keep` are the "safe-ish" middle ground: they refuse to silently destroy unstaged work and error out instead. `--merge` exists chiefly to reset *out of* a conflicted merge state.

**Pathspec form** updates only the index, never `HEAD` or files: `git reset [<tree>] -- <paths>` is the inverse of `git add` (it unstages). `git reset -p` does it interactively. To also restore file *contents*, use [`git restore`](#restore-and-switch-for-undo).

## Undoing common operations

| You did… | Undo with | Notes |
|----------|-----------|-------|
| `git commit` (last one, content fine, want to amend) | `git commit --amend` | Mechanics in [history-rewriting.md](history-rewriting.md) |
| `git commit` (want it gone, keep changes staged) | `git reset --soft HEAD~1` | `--mixed` to also unstage |
| `git commit --amend` (regret it) | `git reset --hard ORIG_HEAD` or `HEAD@{1}` | The pre-amend commit is dangling but reflogged |
| `git merge` (made a merge commit) | `git reset --hard ORIG_HEAD` | Or `git revert -m 1 <merge>` if already pushed — see [branching-merging.md](branching-merging.md) |
| `git merge` (conflicted, not committed) | `git merge --abort` | == `git reset --merge` to pre-merge state |
| `git merge` into a **dirty** tree (want local edits kept) | `git reset --merge ORIG_HEAD` | `--hard` would discard the local edits |
| `git pull` | `git reset --hard ORIG_HEAD` | `pull` = fetch + merge/rebase; `ORIG_HEAD` is the pre-pull tip |
| `git rebase` (finished, regret) | `git reset --hard ORIG_HEAD` | If unreliable, use `<branch>@{1}` from the reflog |
| `git rebase` (mid-flight) | `git rebase --abort` | Returns to the original branch state |
| `git reset` (any mode, regret) | `git reset --hard ORIG_HEAD` | `reset` always sets `ORIG_HEAD` first |
| `git cherry-pick`/`git revert` (in progress) | `git cherry-pick --abort` / `git revert --abort` | Uses `CHERRY_PICK_HEAD`/`REVERT_HEAD` |

```bash
# Undo a just-completed merge or rebase, keeping the prior tip safe:
git branch pre-merge-backup ORIG_HEAD   # capture first — ORIG_HEAD is volatile
git reset --hard ORIG_HEAD              # roll the branch back
```

For *how to perform* a rebase or amend (not undo one), and for recovering from a rebase that rewrote **shared** history, see [history-rewriting.md](history-rewriting.md). To recover changes folded into the wrong commit, the **git-absorb** skill and `git rebase -i` are the tools.

## `restore` and `switch` for undo

Modern, single-purpose replacements for `git checkout`'s overloaded behavior.

**`git restore`** — restore file *contents* (working tree and/or index):

```bash
git restore --staged <file>            # unstage (index ← HEAD); == git reset <file>
git restore <file>                     # ⚠️ discard working-tree edits (file ← index)
git restore --source=HEAD~2 <file>     # bring a file back from an older commit
git restore --staged --worktree <f>    # reset both index and working tree to HEAD
git restore --source=main~2 --staged --worktree .   # wholesale revert paths to a rev
```

**⚠️ Destructive: bare `git restore <file>`.** It overwrites your working-tree changes from the index with no reflog and no undo. Uncommitted edits are gone. Stash or commit first if unsure.

During a conflict, restore can re-create or re-stage conflict states: `--ours`/`--theirs` (pick a side from the index), `--merge` (recreate conflict markers), `--conflict=diff3|zdiff3`.

**`git switch`** — move between branches / detach (recovery-relevant flags):

```bash
git switch -                       # go back to the previously checked-out branch (== @{-1})
git switch -c rescue <sha>         # create+switch to a new branch at a recovered commit
git switch --detach <sha>          # inspect a commit without moving any branch
git switch -C feature <sha>        # force-reset feature to <sha> and switch (⚠️ moves the branch)
git switch --discard-changes main  # ⚠️ throw away local changes while switching (alias -f)
```

**Recovering from detached HEAD** (you committed while not on a branch): those commits are reachable only from `HEAD` right now and will become dangling the moment you switch away. **Before switching**, give them a branch:

```bash
git switch -c keep-this            # names current detached HEAD; commits are now safe
# Already switched away and lost them? Find the SHA in the reflog:
git reflog                         # look for the detached-HEAD commits
git switch -c keep-this <sha>
```

## `git fsck`: dangling and unreachable objects

When the reflog can't help — the entry expired, or the commit was *never* on any ref (e.g. a detached-HEAD commit abandoned long ago) — `git fsck` walks the object database and reports what nothing points to.

```bash
git fsck --lost-found              # write dangling objects to .git/lost-found/
git fsck --unreachable             # list objects unreachable from any ref/reflog/index
git fsck --no-reflogs              # treat reflog-only commits as unreachable too (find "lost from a ref")
git fsck --dangling                # (default) report objects never directly referenced
git fsck --name-objects            # annotate how each object is reachable (e.g. HEAD@{2}~3^2)
```

- `--lost-found` writes dangling commits/tags to `.git/lost-found/commit/<sha>` and other objects to `.git/lost-found/other/`; **dangling blobs have their contents written out** (handy for recovering a file you staged then lost via `reset --hard`).
- Diagnostics: **`dangling`** = exists but nothing references it directly (a recoverable root, e.g. a dropped commit); **`unreachable`** = not reachable from your specified heads; **`missing`** = referenced but absent (corruption); **`hash mismatch`** = serious corruption.

```bash
# Triage dangling commits and inspect candidates:
git fsck --no-reflogs --dangling | grep 'dangling commit'
git show <sha>                     # inspect; then recover with git switch -c rescue <sha>
```

`--connectivity-only` skips blob checks for speed; object plumbing (`cat-file`, `git gc`) lives in [internals-plumbing.md](internals-plumbing.md).

## Recovering dropped stashes

The latest stash is `refs/stash`; older ones live in **that ref's reflog** as `stash@{1}`, `stash@{2}`, … Normal access is `git stash show -p stash@{1}`, `git stash apply stash@{2}` (stash *usage* lives in [worktrees-stash.md](worktrees-stash.md)).

A `git stash drop` or `git stash clear` removes entries from the stash reflog, and they **cannot be recovered through normal means**. But a dropped stash is just an unreachable commit (a merge commit whose message starts with `WIP on …`). Find it with `fsck`:

```bash
# Canonical dropped-stash recovery (from git-stash docs):
git fsck --unreachable |
  grep commit | cut -d' ' -f3 |
  xargs git log --merges --no-walk --grep=WIP

# Once you spot the right SHA, turn it back into a stash or a branch:
git stash apply <sha>              # apply it directly
git stash store -m "recovered" <sha>   # re-register it in the stash list
git switch -c recovered-stash <sha>    # or just make a branch from it
```

**Footgun:** stash entries are unreachable from creation, so they are pruned **earlier and more aggressively** than reachable history (subject to `gc.pruneExpire`, default 2 weeks). Recover dropped stashes promptly.

## Reflog expiry & the gc deadline

Recovery has a clock. Unreachable objects survive only until garbage collection prunes them, and reflog entries themselves expire:

| Setting | Default | Controls |
|---------|---------|----------|
| `gc.reflogExpire` | 90 days | Age at which **reachable** reflog entries are dropped |
| `gc.reflogExpireUnreachable` | 30 days | Age for entries now **unreachable** from the ref tip |
| `gc.pruneExpire` | 2 weeks | Loose objects older than this are deleted by `git gc` |

```bash
git reflog expire --expire=now --all              # ⚠️ drop ALL reflog entries now
git reflog expire --expire-unreachable=now --all  # ⚠️ drop unreachable entries now
git gc --prune=now                                # ⚠️ delete dangling objects immediately
```

**⚠️ Destructive — these end the recovery window.** `git reflog expire --expire-unreachable=now --all` followed by `git gc --prune=now` will *permanently* delete everything not currently reachable. Never run them when trying to recover lost work — they are the opposite of recovery. (Note `git gc` also auto-runs via `gc.auto`; it normally respects the expiry windows above, so recent loss is still recoverable. `git stash` usage, `gc`/`repack`/`maintenance` internals: [internals-plumbing.md](internals-plumbing.md).)

To *protect* a found commit before doing anything else, anchor it with a ref so gc can't reap it: `git branch keep <sha>` (or `git tag keep <sha>`).

## "Oh no" quick reference

| Disaster | First move |
|----------|-----------|
| `git reset --hard` blew away commits | `git reset --hard ORIG_HEAD` (or reflog SHA) |
| `git reset --hard` blew away *uncommitted* edits | Mostly gone; if staged earlier, `git fsck --lost-found` for dangling blobs |
| Deleted a branch | `git switch -c <name> <sha>` from reflog / `branch -D` output |
| Committed on detached HEAD then switched | `git reflog` → `git switch -c keep <sha>` |
| Amended and regret it | `git reset --hard HEAD@{1}` |
| Bad merge/pull | `git reset --hard ORIG_HEAD` |
| Bad merge, dirty tree | `git reset --merge ORIG_HEAD` |
| Rebase ruined the branch (finished) | `git reset --hard <branch>@{1}` |
| Rebase going wrong (mid-flight) | `git rebase --abort` |
| `git stash drop`/`clear` by mistake | `git fsck --unreachable \| grep commit` → `git stash apply <sha>` |
| Can't find it in the reflog at all | `git fsck --lost-found`, then inspect `.git/lost-found/` |
| Found the commit — make it stick | `git branch rescue <sha>` *before* anything else |

**Golden rules:** (1) When in doubt, **stop and look** (`git reflog`, `git status`, `git fsck`) before running anything that writes. (2) **Anchor first** — `git branch rescue <sha>` the instant you find lost work. (3) **Never** run `gc --prune=now` / `reflog expire --expire-unreachable=now` while recovering. (4) Recover onto a *new* branch, not by `--hard`-ing the current one.
