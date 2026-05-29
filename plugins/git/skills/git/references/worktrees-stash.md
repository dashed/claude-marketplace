# Worktrees & Stash

Two ways to juggle more than one thing at once. **`git worktree`** checks out multiple branches into separate directories that share one object store — parallel work with zero stash dance. **`git stash`** shelves dirty changes onto a stack so you can switch context, then restore them. This reference covers both end-to-end, including the sharp edges: the one-branch-per-worktree rule, stale-worktree cleanup, `stash` internals as real commits, and `apply` vs `pop`. Grounded against git 2.54.0.

## Table of contents

- [git worktree](#git-worktree)
  - [The model](#the-model)
  - [add](#worktree-add)
  - [list](#worktree-list)
  - [remove](#worktree-remove)
  - [prune](#worktree-prune)
  - [move](#worktree-move)
  - [lock / unlock](#worktree-lock--unlock)
  - [repair](#worktree-repair)
  - [Shared vs per-worktree refs & config](#shared-vs-per-worktree-refs--config)
  - [Worktree footguns](#worktree-footguns)
- [git stash](#git-stash)
  - [The model](#the-model-1)
  - [push (stashing)](#stash-push-stashing)
  - [list / show](#stash-list--show)
  - [apply vs pop](#apply-vs-pop)
  - [branch](#stash-branch)
  - [drop / clear](#drop--clear)
  - [create / store (scripting)](#create--store-scripting)
  - [export / import](#export--import)
  - [Stash internals](#stash-internals)
- [Quick reference](#quick-reference)

---

## git worktree

### The model

A repository has **one main worktree** (created by `clone`/`init`) and zero or more **linked worktrees**. Each linked worktree is a separate directory on disk with its *own* `HEAD`, index, and working files — but they all **share a single object database and (most) refs** via the main repo's `$GIT_DIR`.

Mechanics worth knowing:
- A linked worktree's top-level `.git` is a *file* (not a directory) containing `gitdir: /path/main/.git/worktrees/<id>`.
- Per-worktree admin files live in `$GIT_DIR/worktrees/<id>/` (its `HEAD`, `index`, `gitdir`, optional `locked`).
- Because objects are shared, a commit made in one worktree is instantly visible (by SHA) in all of them — no fetch/push between worktrees.

**Why use worktrees** instead of stashing or re-cloning: hotfix a release while a messy refactor sits untouched in another dir; build/test branch A while editing branch B; check out a colleague's PR branch without disturbing your current work. For *stacked dependent* branches specifically, also consider the **git-chain** skill.

### worktree add

```bash
git worktree add <path> [<commit-ish>]
```

Default convenience behavior (no `-b`/`--detach`/`<commit-ish>`):
- Creates a **new branch named after the final path component** (`git worktree add ../hotfix` → branch `hotfix`).
- If that branch *already exists*, it's checked out — **unless it's checked out in another worktree**, in which case `add` refuses (use `--force`).
- If there are *no* local branches yet, the new worktree gets an **unborn** branch (as if `--orphan`).
- `<commit-ish>` may be `-`, meaning `@{-1}` (the previous branch).

| Flag | Effect |
|---|---|
| `-b <new-branch>` | Create `<new-branch>` at `<commit-ish>` (default `HEAD`) and check it out. Refuses if it exists |
| `-B <new-branch>` | Like `-b` but **resets** an existing branch to `<commit-ish>` |
| `-d` / `--detach` | Check out with a **detached `HEAD`** (throwaway/experiments — no branch) |
| `--orphan` | New worktree + index empty, on a new unborn branch (git 2.42+) |
| `--checkout` / `--no-checkout` | `--no-checkout` skips populating files (e.g. to configure sparse-checkout first) |
| `--track` / `--no-track` | Mark/skip upstream when the new branch starts from a branch (auto for remote-tracking starts) → see [refspecs-remotes.md](refspecs-remotes.md) |
| `--guess-remote` | With no `<commit-ish>`: if a single remote has a same-named branch, base on it and set upstream (config `worktree.guessRemote`) |
| `--lock [--reason <s>]` | Create already-locked (race-free vs `add` then `lock`) |
| `-f` / `--force` | Override the "already checked out" / "path in use" safeguards; **twice** to add a missing *locked* path |

```bash
# Hotfix in a sibling dir from a new branch, then clean up:
git worktree add -b emergency-fix ../temp main
# ...fix, commit in ../temp...
git worktree remove ../temp

# Throwaway detached worktree to test a tag:
git worktree add --detach ../test v2.1.0
```

### worktree list

```bash
git worktree list                 # human-readable
git worktree list --porcelain -z  # stable, script-parseable (NUL-terminated)
git worktree list -v              # verbose: shows lock reasons / prunable cause (-v & prunable: git 2.31+)
```

Each entry shows path, checked-out `HEAD` (abbrev SHA), and branch — or `(detached HEAD)`, `(bare)`. Annotations: `locked` and `prunable`. `--porcelain` emits one `label value` per line, blank line between records (`worktree`, `HEAD`, `branch`/`detached`, `bare`, `locked`, `prunable`); combine with `-z` (git 2.36+) so paths containing newlines parse correctly.

### worktree remove

```bash
git worktree remove <worktree>   # git 2.17+
```

Removes the worktree directory *and* its admin files. **Refuses** if the worktree is unclean (untracked files or modifications) or has submodules — override with `-f`/`--force`. For a *locked* worktree, `--force` **twice**. The main worktree cannot be removed. A worktree is identifiable by a unique trailing path component (e.g. `ghi` for `/abc/def/ghi`), not just the full path.

### worktree prune

```bash
git worktree prune -n            # dry-run: show what would be pruned
git worktree prune -v            # verbose
git worktree prune --expire 2.weeks.ago
```

Cleans up `$GIT_DIR/worktrees/<id>` entries whose working tree directory is **missing** — i.e. when you deleted a worktree dir with `rm -rf` instead of `git worktree remove`. Happens automatically over time per `gc.worktreePruneExpire` (default 3 months); `--expire <time>` overrides the threshold for a manual run.

### worktree move

```bash
git worktree move <worktree> <new-path>   # git 2.17+
```

Relocates a worktree and fixes its admin pointers. **Cannot** move the main worktree, or any worktree containing submodules. (Moved the main worktree manually? Run `git worktree repair` from it.) `--force` needed for some locked/occupied-destination cases.

### worktree lock / unlock

```bash
git worktree lock --reason "on USB drive" /mnt/usb/wt
git worktree unlock /mnt/usb/wt
```

Locking prevents a worktree from being auto-pruned, moved, or deleted — for worktrees on removable media or network shares that aren't always mounted (otherwise `prune` would reap them while unmounted). Stored as a `locked` file (containing the reason) in the worktree's admin dir.

### worktree repair

```bash
git worktree repair [<path>...]   # git 2.29+
```

Fixes the two-way links when paths change *outside* git's knowledge:
- Moved the **main** repo/bare dir → run `repair` in it to reconnect linked worktrees.
- Moved a **linked** worktree manually → run `repair` inside it (or from any worktree, passing the new path) to reconnect it to the main repo.
- `--relative-paths` (git 2.48+) rewrites links relative (config `worktree.useRelativePaths`), handy for portable setups.

### Shared vs per-worktree refs & config

Knowing what's shared prevents surprises:

| Category | Shared across worktrees? |
|---|---|
| Object database (commits/trees/blobs) | **Shared** |
| `refs/heads/*`, `refs/tags/*`, `refs/remotes/*`, `refs/stash` | **Shared** |
| `HEAD`, index, and other pseudo-refs | **Per-worktree** |
| `refs/bisect/*`, `refs/worktree/*`, `refs/rewritten/*` | **Per-worktree** |

Reach another worktree's per-worktree refs via the special paths `main-worktree/...` and `worktrees/<id>/...` (e.g. `git rev-parse worktrees/foo/HEAD`). Don't poke inside `$GIT_DIR` by hand — use `git rev-parse --git-path <name>` to resolve whether a path belongs to `$GIT_DIR` or the shared `$GIT_COMMON_DIR`.

Because `refs/stash` is **shared**, `git stash` entries are visible from *every* worktree — they are not per-worktree.

**Per-worktree config:** enable the extension, then write with `--worktree`:

```bash
git config extensions.worktreeConfig true   # git 2.20+
git config --worktree core.sparseCheckout true
```

With this on, `core.bare`/`core.worktree`/`core.sparseCheckout` should live in each worktree's `config.worktree`, not the shared config. (Older git refuses repos using this extension. General config levels → [config-attributes-hooks.md](config-attributes-hooks.md).)

### Worktree footguns

- **⚠️ One worktree per branch.** A given branch can be checked out in **only one** worktree at a time. `add`/`switch` to a branch already checked out elsewhere fails with *"already checked out at …"*. Options: use a different branch, a detached HEAD (`--detach`), or `--force` (rarely advisable — two worktrees on one branch fight over it).
- **⚠️ `rm -rf` leaves ghosts.** Deleting a worktree dir manually leaves stale `$GIT_DIR/worktrees/<id>` admin files. Use `git worktree remove`; if you forgot, run `git worktree prune`.
- **⚠️ Submodules are second-class.** Worktrees containing submodules can't be `move`d, and multiple checkouts of a superproject are explicitly *not recommended* (BUGS section in the docs).
- **Locked worktrees** need `--force` (sometimes twice) for remove/move and survive `prune`.

---

## git stash

### The model

`git stash` records your dirty working tree **and** index, then resets them to `HEAD`, giving you a clean tree. Stashes form a stack: the newest is `refs/stash`, older ones live in that ref's **reflog** as `stash@{1}`, `stash@{2}`, … A bare integer `<n>` is equivalent to `stash@{<n>}` (so `git stash show 1` shows `stash@{1}`), and reflog time syntax is valid (`stash@{2.hours.ago}`). Bare `git stash` == `git stash push` (git 2.13+).

### stash push (stashing)

```bash
git stash [push] [options] [-- <pathspec>...]
```

| Flag | Effect |
|---|---|
| `-m <msg>` / `--message <msg>` | Label the entry (else "WIP on <branch>: …") |
| `-p` / `--patch` | Interactively pick hunks to stash (implies `--keep-index`; override with `--no-keep-index`) |
| `-k` / `--keep-index` | Leave already-**staged** changes in the index (stash a copy; test what's staged) |
| `-S` / `--staged` | Stash **only** staged changes (like committing them, but to the stash; git 2.35+). `--patch` overrides this |
| `-u` / `--include-untracked` | Also stash untracked files (then `git clean`s them from the tree) |
| `-a` / `--all` | Also stash **ignored** + untracked files |
| `-- <pathspec>` | Stash only matching paths (other changes stay in the tree) |
| `--pathspec-from-file=<f>` | Read pathspecs from a file (`-` = stdin); `--pathspec-file-nul` for NUL-separated |
| `-q` / `--quiet` | Suppress feedback |

```bash
git stash -u -m "wip: refactor parser"     # include untracked, with a message
git stash push -- src/auth.py              # stash just one file's changes
git stash push --staged                    # shelve only what's staged, keep the rest working
```

**`save` is deprecated** (since git 2.16) in favor of `push`; `save` can't take a pathspec and treats all args as the message. **⚠️ Bare-form gotcha:** with the `push` keyword omitted, pathspecs are only allowed after `--` (`git stash -- file`), so a mistyped subcommand can't silently create a stash.

**⚠️ Untracked files aren't stashed by default.** A plain `git stash` leaves untracked files in your tree; without `-u`/`-a` they can collide on a later branch switch. Use `-u` when "clean tree" must include new files.

### stash list / show

```bash
git stash list                       # all entries (accepts git log options)
git stash show                       # diffstat of stash@{0} vs its base
git stash show -p stash@{1}          # full patch of the 2nd entry
git stash show -u stash@{0}          # include untracked files in the diff (git 2.32+)
```

`show` defaults to a diffstat; `-p` gives the patch; it accepts any `git diff` option. Defaults are configurable via `stash.showStat` / `stash.showPatch` / `stash.showIncludeUntracked`.

### apply vs pop

```bash
git stash apply [--index] [<stash>]   # reinstate, KEEP the entry on the stack
git stash pop   [--index] [<stash>]   # reinstate AND drop the entry
```

- `apply` leaves the entry in place — safer when you want to apply the same stash to multiple branches, or aren't sure it'll go cleanly. `apply` can take *any* commit that looks stash-shaped (e.g. one from `git stash create`).
- `pop` = `apply` + `drop`. **⚠️ But if applying hits a conflict, `pop` does NOT drop** — the entry stays and you must `git stash drop` by hand after resolving. Don't assume a conflicted pop emptied the slot.
- `--index` also restores the **staged/unstaged split** (the index state), not just the merged working-tree changes. Without it, everything comes back unstaged. `--index` can fail if there are conflicts (conflicts live in the index).
- `apply` accepts `--label-ours=`/`--label-theirs=`/`--label-base=` to rename conflict markers (`--label-base` only with `merge.conflictStyle=diff3`).

The working tree must match the index before `pop`. Conflict-resolution mechanics (markers, `git add`, aborting) → [branching-merging.md](branching-merging.md).

### stash branch

```bash
git stash branch <new-branch> [<stash>]
```

Creates `<new-branch>` **starting from the commit the stash was based on**, checks it out, applies the stash, and — if it applied cleanly and `<stash>` was a `stash@{n}` ref — drops it. This is the clean escape when `git stash apply` conflicts because the branch moved on: re-applying onto the *original* base sidesteps the conflict entirely.

### drop / clear

```bash
git stash drop [<stash>]    # remove one entry (default stash@{0})
git stash clear             # remove ALL entries
```

**⚠️ Destructive — `drop`/`clear` discard work with no built-in undo.** A dropped/cleared stash isn't reachable through normal commands. The commit objects usually survive in the object store until `gc`, so recovery is *possible* via `fsck`/reflog — see the recipe and full walkthrough in [recovery.md](recovery.md). Think before `git stash clear`.

### create / store (scripting)

```bash
sha=$(git stash create "snapshot")     # build a stash COMMIT, print its SHA, store nothing
git stash store -m "snapshot" "$sha"   # put that commit into refs/stash + reflog
```

`create` makes the stash commit object **without** touching `refs/stash` or the stack (and without reverting your tree) — useful for scripts that want a snapshot SHA. `store` records a `create`d commit into the stash ref. You rarely need these interactively; use `push`.

### export / import

Newer (transferable) stashes (git 2.51+) — move stash entries between repos over normal fetch/push:

```bash
git stash export --to-ref refs/stash-export    # encode all stashes into a commit chain at a ref
git stash export --print                        # ...or just print the chain's object ID
git stash import <commit>                        # add exported stashes from <commit> to this repo's stack
```

`import` adds to the existing stack; `git stash clear` first if you want to replace.

### Stash internals

A stash entry **is a commit** — specifically a merge commit:

```
        .----W      W = working-tree state (the stash's tree)
       /    /        I = index state at stash time
 -----H----I         H = HEAD when you stashed (first parent)
```

- **First parent** = `HEAD` at stash time → this is why `stash branch` can recreate the exact base.
- **Second parent** (`I`) = a commit recording the **index** state.
- The stash's **tree** = the working-tree state (`W`).
- With `-u`/`-a`, a **third parent** records untracked/ignored files.

The stack is a ref + reflog: `refs/stash` is the tip, history is its reflog, hence `stash@{n}` *is* reflog syntax. Because these are ordinary reachable commits while referenced (and dangling-but-recoverable after a drop), the stash is far more robust than its "throwaway" reputation. Object model and reflog details → [internals-plumbing.md](internals-plumbing.md); recovering dropped stashes → [recovery.md](recovery.md).

**Worktree note:** `refs/stash` is **shared** across worktrees (see [Shared vs per-worktree refs](#shared-vs-per-worktree-refs--config)) — one stack for the whole repo. To park work *per directory* instead, prefer a dedicated worktree.

---

## Quick reference

| Task | Command |
|---|---|
| New worktree on a new branch | `git worktree add -b <branch> <path> [<base>]` |
| Worktree for an existing branch | `git worktree add <path> <branch>` |
| Throwaway detached worktree | `git worktree add --detach <path> <commit>` |
| List worktrees (scripting) | `git worktree list --porcelain -z` |
| Remove a worktree | `git worktree remove <path>` (`-f` if dirty) |
| Clean up after manual `rm -rf` | `git worktree prune` |
| Reconnect moved worktree | `git worktree repair [<path>]` |
| Stash everything incl. untracked | `git stash -u -m "msg"` |
| Stash only staged | `git stash push --staged` |
| Stash specific files | `git stash push -- <paths>` |
| Keep staged, stash the rest | `git stash push --keep-index` |
| Inspect a stash | `git stash show -p stash@{n}` |
| Reapply, keep entry | `git stash apply --index` |
| Reapply, drop entry | `git stash pop` |
| Escape a conflicting apply | `git stash branch <new-branch>` |
| Drop all stashes | `git stash clear` ⚠️ |

**See also:** detached HEAD, upstream/tracking, refspecs → [refspecs-remotes.md](refspecs-remotes.md) · conflict resolution & merge mechanics → [branching-merging.md](branching-merging.md) · recovering dropped stashes / lost worktree commits via reflog & fsck → [recovery.md](recovery.md) · object model, refs, reflog, `gc` → [internals-plumbing.md](internals-plumbing.md) · config levels & `--worktree` → [config-attributes-hooks.md](config-attributes-hooks.md) · stacked dependent branches → **git-chain** skill · back to [SKILL.md](../SKILL.md).
