# Refspecs & Remotes

Everything about talking to *other* repositories: managing remotes, the **refspec** grammar that powers `fetch`/`push`, tracking/upstream branches, `push.default`, safe force-pushing, multiple-remote (triangular) workflows, and detached `HEAD`. This is the reference for *why* a fetch updated the ref it did, *why* a push was rejected, and how to force/delete safely. Grounded against git 2.54.0.

Assumes you know the happy path (`git clone`, `git push`, `git pull`). This focuses on the non-obvious mechanics and the footguns.

## Table of contents

- [Managing remotes (`git remote`)](#managing-remotes-git-remote)
- [How `git clone` wires up remotes & tracking](#how-git-clone-wires-up-remotes--tracking)
- [Refspecs in depth](#refspecs-in-depth)
- [Fetching (`git fetch`)](#fetching-git-fetch)
- [Pruning stale remote-tracking refs](#pruning-stale-remote-tracking-refs)
- [Pulling (`git pull`)](#pulling-git-pull)
- [Pushing (`git push`)](#pushing-git-push)
- [`--force` vs `--force-with-lease` vs `--force-if-includes`](#--force-vs---force-with-lease-vs---force-if-includes)
- [`push.default`](#pushdefault)
- [Tracking / upstream branches](#tracking--upstream-branches)
- [Multiple remotes & triangular workflows](#multiple-remotes--triangular-workflows)
- [Pushing & deleting branches and tags](#pushing--deleting-branches-and-tags)
- [Detached HEAD basics](#detached-head-basics)
- [Quick reference](#quick-reference)

## Managing remotes (`git remote`)

A *remote* is a named URL (or pair of URLs) plus a fetch refspec, stored in `.git/config` as `remote.<name>.url` / `remote.<name>.fetch`.

| Command | What it does | Notes |
|---|---|---|
| `git remote -v` | List remotes with fetch+push URLs | `-v` must come *before* the subcommand |
| `git remote add <name> <url>` | Add a remote | `-f` fetch immediately; `-t <branch>` track only that branch; `-m <head>` set `<name>/HEAD`; `--[no-]tags`; `--mirror=fetch\|push` |
| `git remote rename <old> <new>` | Rename + rewrite tracking refs & config | Updates `refs/remotes/<old>/*` → `<new>` and `branch.*.remote` |
| `git remote remove <name>` | Delete remote, its tracking refs & config | Alias `rm` |
| `git remote set-url <name> <newurl> [<oldurl>]` | Change fetch URL | `--push` edits push URL; `--add` adds another; `--delete` removes matching |
| `git remote get-url <name>` | Print URL(s) | `--push`, `--all` |
| `git remote set-head <name> (-a\|-d\|<branch>)` | Set/delete `refs/remotes/<name>/HEAD` | `-a` auto-detect from remote; `-d` delete; lets `<name>` stand in for `<name>/<default>` |
| `git remote set-branches [--add] <name> <branch>...` | Rewrite (or extend) the tracked-branch list | Changes the `fetch` refspec |
| `git remote show <name>` | Detailed status (queries the remote) | `-n` uses cached data, no network |
| `git remote prune <name>` | Delete stale tracking refs | `-n`/`--dry-run` to preview. Same as `fetch --prune` without fetching |
| `git remote update [<group>]` | Fetch multiple remotes/groups | `-p`/`--prune`; groups via `remotes.<group>` |

```bash
# Inspect what a remote really has, without touching the network:
git remote show -n origin

# Point an existing remote at a new URL (e.g. SSH -> HTTPS):
git remote set-url origin git@github.com:owner/repo.git

# Track only two branches of a busy upstream:
git remote add -f -t main -t release upstream https://example.com/repo.git
```

**Exit codes worth knowing** (scripting): `2` = remote not found (for `add`/`rename`/`remove`); `3` = remote already exists.

`--mirror=fetch` mirrors *all* of the remote's `refs/*` directly into your local `refs/*` (bare repos only — a fetch would clobber local commits). `--mirror=push` makes every `git push` behave as `--mirror`. See [Multiple remotes](#multiple-remotes--triangular-workflows) for separate fetch/push URLs.

## How `git clone` wires up remotes & tracking

Clone is "basic," but its *side effects* on remotes/tracking are worth pinning down:

- Creates a remote named **`origin`** (rename with `-o <name>` / `--origin=<name>`, default overridable via `clone.defaultRemoteName`).
- Sets `remote.origin.url` and `remote.origin.fetch = +refs/heads/*:refs/remotes/origin/*` (see [Refspecs](#refspecs-in-depth)).
- Creates remote-tracking branches under `refs/remotes/origin/*`, checks out the default branch, and **sets that branch's upstream** to `origin/<default>`.

| Flag | Effect |
|---|---|
| `-b <name>` / `--branch=<name>` | Point `HEAD` at `<name>` instead of the remote's default (a tag → detached HEAD) |
| `--bare` | `<dir>` *is* `$GIT_DIR`; copies branch heads directly, **no** `refs/remotes/origin/*` and no tracking config |
| `--mirror` | Implies `--bare`, maps *all* refs, and configures `remote.origin.mirror` so `git remote update` overwrites everything (good for backups/migrations) |
| `-n` / `--no-checkout` | Don't check out `HEAD` after cloning |
| `--filter=<spec>`, `--depth=<n>`, `--sparse` | Partial / shallow / sparse clone → see [advanced-features.md](advanced-features.md) |

## Refspecs in depth

A **refspec** maps refs on one side to refs on the other. Full grammar:

```
[+]<src>:<dst>
```

- **`<src>`** — source ref/pattern. On fetch, a ref on the remote; on push, a local ref or any "SHA-1 expression" (see [internals-plumbing.md](internals-plumbing.md) for the full [gitrevisions] syntax).
- **`<dst>`** — destination ref to update. On push it must be a concrete ref name, not an expression.
- **leading `+`** — allow non-fast-forward (force) updates of `<dst>`. Identical to `--force`, but scoped to *this one refspec*.

The default fetch refspec a clone writes:

```ini
[remote "origin"]
	fetch = +refs/heads/*:refs/remotes/origin/*
```

…means "fetch every branch under `refs/heads/` on origin and store it under `refs/remotes/origin/`, allowing forced updates of the tracking refs."

| Form | Meaning |
|---|---|
| `main` | Shorthand for `main:` (fetch) — fetch `main`, update tracking ref via the configured fetch refspec |
| `src:dst` | Map `src` → `dst` |
| `+src:dst` | …allowing non-fast-forward |
| `:dst` (push) | **Empty `<src>` deletes `<dst>` on the remote.** `git push origin :dev` deletes `dev` |
| `refs/heads/*:refs/remotes/origin/*` | Wildcard — exactly one `*` on each side; the match is substituted into `<dst>` |
| `^refs/heads/dev-*` (push) | **Negative refspec** — *exclude* matching refs (src only, no `<dst>`, no hex SHAs) |
| `tag <tag>` (push) | Special syntax expanding to `refs/tags/<tag>:refs/tags/<tag>` |
| `:` (push) | Push "matching" branches (every local branch that already exists on the remote); `+:` allows non-ff |

```bash
# Fetch one remote branch into a differently-named local tracking ref:
git fetch origin +seen:refs/remotes/origin/seen

# Push all branches except dev-* ones:
git push origin 'refs/heads/*' '^refs/heads/dev-*'
```

Configured refspecs live in `remote.<name>.fetch` and `remote.<name>.push` (both multi-valued). When you run a bare `git fetch origin`, the `fetch` values *are* the refspecs; when you pass refspecs on the command line, the `fetch` config only decides *where* fetched refs land (override with `--refmap=<refspec>`, or `--refmap=` to ignore config entirely).

## Fetching (`git fetch`)

`git fetch` downloads objects and updates **remote-tracking** refs. It **never touches your working tree or current branch** — that's what makes it safe to run anytime. Fetched ref tips are also written to `.git/FETCH_HEAD` (used by `git pull`, and handy for peeking: `git fetch <url> <branch> && git log FETCH_HEAD`).

By default, tags pointing into the fetched history are auto-followed. Control with `--tags`/`--no-tags` or `remote.<name>.tagOpt`.

| Flag | Effect |
|---|---|
| `--all` | Fetch all remotes (honors `remote.<name>.skipFetchAll`; config `fetch.all`) |
| `--multiple <repo\|group>...` | Fetch several remotes/groups (no refspecs allowed) |
| `-p` / `--prune` | Delete tracking refs that vanished upstream — see [Pruning](#pruning-stale-remote-tracking-refs) |
| `-P` / `--prune-tags` | Also prune local tags absent upstream (**use with care**) |
| `-t` / `--tags` | Fetch *all* tags too (not subject to pruning by itself) |
| `-n` / `--no-tags` | **`-n` means `--no-tags`, not dry-run!** Disables tag auto-following |
| `--dry-run` | Show what would happen (no short alias for fetch) |
| `-f` / `--force` | Allow non-ff updates of the `<dst>` refs |
| `--atomic` | All-or-nothing ref update |
| `-j <n>` / `--jobs=<n>` | Parallelize fetches |
| `--depth`, `--deepen`, `--unshallow`, `--filter` | Shallow / partial → [advanced-features.md](advanced-features.md) |
| `--set-upstream` | Set upstream tracking for the current branch after a successful fetch |

**⚠️ Footgun — `-n`:** For `git fetch`, `-n` is `--no-tags`. For `git push`, `-n` is `--dry-run`. They are *not* the same option across commands. To preview a fetch, spell out `--dry-run`.

Output status flags (left column of `fetch`/`push` output): space = fast-forward, `+` = forced update, `-` = pruned/deleted, `t` = tag update, `*` = new ref, `!` = rejected/failed, `=` = up to date.

## Pruning stale remote-tracking refs

Git keeps tracking refs even after the upstream branch is deleted, which inflates `git branch -a` and slows big repos. Prune them:

```bash
git fetch --prune origin      # fetch + delete vanished refs/remotes/origin/*
git remote prune origin       # prune only, no fetch
```

Make it automatic with `fetch.prune=true` (global) or `remote.<name>.prune=true` (per-remote).

**⚠️ Footgun — pruning is a function of the refspec, not "branches".** If your refspec includes `refs/tags/*:refs/tags/*` (e.g. a `--mirror` clone, or you pass it explicitly), `--prune` will delete *local tags* not on the remote — including tags that never came from that remote. Tag pruning has its own switch:

```bash
git fetch --prune --prune-tags origin   # prune tracking refs AND local tags missing upstream
```

`--prune-tags` is shorthand for adding `refs/tags/*:refs/tags/*`. Config equivalents: `fetch.pruneTags` / `remote.<name>.pruneTags` (set alongside `fetch.prune` for a clean 1:1 mirror of upstream refs).

## Pulling (`git pull`)

`git pull` = `git fetch` followed by an *integration* step into the current branch. In git 2.54.0 there are four integration modes:

| Invocation | Integration | Config equivalent |
|---|---|---|
| `git pull --ff-only` | Fast-forward only; **fails if branches diverged**. *This is the default.* | `pull.ff = only` |
| `git pull --no-rebase` | `git merge` (creates a merge commit if diverged) | `pull.rebase = false` |
| `git pull --rebase` | `git rebase` onto the upstream | `pull.rebase = true` |
| `git pull --squash` | `git merge --squash` | `pull.squash = true` |

**⚠️ Footgun — the "divergent branches" stop.** With neither `pull.ff` nor `pull.rebase` configured, a *non*-fast-forward pull aborts with:

```
fatal: Need to specify how to reconcile divergent branches.
```

You must then choose: `git pull --rebase`, `git pull --no-rebase` (merge), or set a default. Pick one deliberately:
- `pull.rebase = true` keeps history linear (good for feature branches you haven't shared).
- `pull.ff = only` refuses to auto-merge — you decide each time.
- Default merge (`--no-rebase`) sprays "Merge branch 'main' of …" bubbles into history; usually undesirable on a personal branch.

`-r`/`--rebase` accepts `=merges` (preserve local merge commits via `git rebase --rebase-merges`) and `=interactive`. Set per-branch with `branch.<name>.rebase`. `--autostash` (or `pull.autoStash`/`rebase.autostash`) stashes a dirty tree, pulls, then re-applies — required-ish for rebasing pulls, which refuse to run with local changes.

Rebase/merge *mechanics* (conflict markers, `--continue`, `--rebase-merges`) live in [history-rewriting.md](history-rewriting.md) and [branching-merging.md](branching-merging.md). For automatic rebasing of *stacked* branches, use the **git-chain** skill.

## Pushing (`git push`)

`git push` updates refs on a remote. With no refspec, the ref(s) to push are chosen by precedence: (1) command-line `<refspec>`/`--all`/`--mirror`/`--tags`, then (2) `remote.<name>.push` config, then (3) [`push.default`](#pushdefault) (default `simple`). The `<repository>` defaults to the current branch's upstream remote, else `origin`.

| Flag | Effect |
|---|---|
| `-u` / `--set-upstream` | Set upstream tracking for each pushed branch (so later `git pull`/`git push` need no args) |
| `--all` / `--branches` | Push all of `refs/heads/*` (cannot combine with explicit refspecs) |
| `--tags` | Also push all of `refs/tags/*` |
| `--follow-tags` | Also push annotated tags reachable from the pushed commits (config `push.followTags`) |
| `-d` / `--delete` | Delete the listed remote refs (same as `:`-prefixing them) |
| `--prune` | Remove remote branches with no local counterpart (respects refspecs) |
| `--mirror` | Push *all* `refs/*`; creates/updates/deletes to match local exactly |
| `--atomic` | All-or-nothing: if any ref is rejected, none update |
| `-n` / `--dry-run` | Show what would be pushed (note: opposite meaning vs `fetch -n`) |
| `-o <opt>` / `--push-option=<opt>` | Send a string to server hooks (`push.pushOption`) |
| `--signed[=…]` | GPG-sign the push (`push.gpgSign`) → signing details in [advanced-features.md](advanced-features.md) |
| `--no-verify` | Skip the `pre-push` hook (hooks → [config-attributes-hooks.md](config-attributes-hooks.md)) |
| `-f` / `--force`, `--force-with-lease`, `--force-if-includes` | See next section |

**PUSH RULES (safety):** Pushing to a **branch** (`refs/heads/*`) allows *only* fast-forward updates (destination must be an ancestor of the source). Pushing to a **tag** (`refs/tags/*`) rejects *all* updates (deletions/creations excepted). Override branch ff-rejection with `--force` or a leading `+`; no force will make a branch accept a non-commit, or override a server's `receive.deny*` policy.

```bash
git push origin HEAD                 # push current branch to a same-named remote branch
git push origin HEAD:main            # push current branch to remote 'main' (rename in flight)
git push origin local:remote-name    # create/update 'remote-name' from local branch
git push -u origin feature           # push and set upstream in one go
```

## `--force` vs `--force-with-lease` vs `--force-if-includes`

You need force after rewriting already-pushed history (rebase, `commit --amend`, squash). Choosing the right force flag is the difference between a clean update and silently deleting a teammate's commits.

**`--force` (`-f`) — the blunt instrument.** Replaces the remote ref regardless of its current value. **⚠️ Destructive:** if someone pushed after your last fetch, their commits are overwritten and become unreachable (eligible for the remote's `gc`). Also note `--force` applies to *every* ref being pushed — with `push.default=matching` or multiple `remote.<name>.push` entries it can clobber branches you didn't mean to. To force exactly one ref, prefer a `+` prefix: `git push origin +feature`.

**`--force-with-lease` — the safe default for shared branches.** Updates the remote ref *only if* its current value is what you expect — i.e. it still matches your remote-tracking ref. If someone pushed in the meantime, your tracking ref is stale, the "lease" is invalid, and the push is **rejected** instead of destroying their work.

```bash
git push --force-with-lease origin feature                 # reject if origin/feature moved since last fetch
git push --force-with-lease=feature:<sha> origin feature   # explicit expected value
```

Forms:
- `--force-with-lease` (bare): protect *all* refs being updated, requiring each to equal its remote-tracking ref.
- `--force-with-lease=<ref>`: protect just `<ref>` against its remote-tracking ref.
- `--force-with-lease=<ref>:<expect>`: protect `<ref>` requiring its current value to equal `<expect>` (empty `<expect>` = the ref must not yet exist). **This is the only non-experimental explicit form.**

**⚠️ Footgun — background fetch defeats the lease.** The bare/`=<ref>` forms trust your remote-tracking ref. Anything that auto-runs `git fetch` (editor integrations, a cron job, `git fetch --all`) silently refreshes that ref, so the lease "passes" even though you never *saw* the new commits — and you clobber them anyway. Two mitigations:

```bash
# 1) Belt-and-suspenders: only force if the remote tip is in your local reflog.
git push --force-with-lease --force-if-includes origin feature

# 2) A push-only remote that no background fetch updates:
git remote add origin-push "$(git config remote.origin.url)"
git fetch origin-push
git push --force-with-lease origin-push feature   # fails unless you fetched origin-push yourself
```

**`--force-if-includes`** verifies the remote-tracking tip is reachable from your branch's reflog — i.e. the remote changes were actually *integrated locally* before you rewrote. Pair it with `--force-with-lease` (it's a no-op alone or with the explicit `:<expect>` form). Enable by default with `push.useForceIfIncludes=true`.

**Rule of thumb:** never `--force` a shared branch; use `--force-with-lease --force-if-includes`. Plain `--force` is reserved for branches only you touch, or when you genuinely mean to discard remote history. Recovering history clobbered by a force-push → [recovery.md](recovery.md).

## `push.default`

Controls what a bare `git push` (no refspec) pushes. Default is **`simple`** (since git 2.0).

| Value | Behavior |
|---|---|
| `nothing` | Refuse to push without an explicit refspec (forces you to be deliberate) |
| `current` | Push current branch to a same-named branch on the remote (works centralized *and* triangular) |
| `upstream` | Push current branch to its `@{upstream}` (centralized only — same repo you pull from) |
| `tracking` | Deprecated synonym for `upstream` |
| `simple` | Like `upstream`, **but** also requires the remote branch to have the same name. Safest; the default | 
| `matching` | Push *every* local branch that has a same-named branch on the remote (the old pre-2.0 default — **surprising**, pushes branches you didn't name) |

`push.autoSetupRemote=true` makes the first `git push` of a new branch act like `-u` (set upstream) under `simple`/`upstream`/`current` — convenient when local and remote names always match.

## Tracking / upstream branches

A branch's **upstream** (a.k.a. "tracking information") is the remote branch it's paired with — stored in `.git/config` as `branch.<name>.remote` + `branch.<name>.merge`:

```ini
[branch "main"]
	remote = origin
	merge = refs/heads/main
```

The upstream is the default for argument-less `git fetch`/`git pull`/`git push`, and drives the "ahead/behind" counts in `git status` ("Your branch and 'origin/main' have diverged, and have 2 and 3 different commits each").

**Setting an upstream:**

```bash
git branch -u origin/main                 # set current branch's upstream
git branch --set-upstream-to=origin/main feature   # set a named branch's upstream
git branch --unset-upstream               # remove it
git push -u origin feature                # push and set upstream together
git switch -c feature origin/feature      # checkout remote branch -> auto-creates local + upstream
```

**⚠️ Gone:** `git branch --set-upstream <branch> <upstream>` (the confusing positional form) was **removed**. Use `-u`/`--set-upstream-to=` or `--track` instead.

Auto-setup happens via `--track[=direct|inherit]` (default `direct` = upstream is the start-point; `inherit` = copy the start-point's tracking config), governed by `branch.autoSetupMerge` (default `true` = track when starting from a remote-tracking branch; also `always`/`simple`/`inherit`/`false`). `branch.autoSetupRebase` (default `never`) can make tracked branches default to rebase-on-pull. Disable per-branch with `--no-track`.

**Referencing the upstream** (subset of [gitrevisions] — full syntax in [internals-plumbing.md](internals-plumbing.md)):

| Token | Means |
|---|---|
| `@{upstream}`, `@{u}` | The remote-tracking ref this branch is built on (`refs/remotes/R/X`) |
| `<branch>@{u}` | …for a specific branch, e.g. `main@{u}` |
| `@{push}` | Where `git push` *would* send the current branch (differs from `@{u}` only in triangular setups) |
| `@{-1}`, `-` | The previously checked-out branch (`git switch -` toggles) |

```bash
git log @{u}..               # commits you have that upstream doesn't (ahead)
git log ..@{u}               # commits upstream has that you don't (behind)
git branch -vv               # list branches with upstream + ahead/behind
```

## Multiple remotes & triangular workflows

A **triangular** workflow pulls from one remote (the canonical `upstream`) and pushes to another (your `origin` fork):

```bash
git clone https://github.com/you/fork.git          # origin = your fork
git remote add upstream https://github.com/org/repo.git
git fetch upstream
git switch -c feature upstream/main                 # branch off upstream, track it for pulls
```

Control *where pushes go* independently of *where fetches come from*:

| Setting | Scope | Effect |
|---|---|---|
| `branch.<name>.remote` | one branch | Remote for fetch (and push, unless overridden) |
| `remote.pushDefault` | all branches | Default *push* remote (overrides `branch.<name>.remote` for push) |
| `branch.<name>.pushRemote` | one branch | Push remote for this branch (overrides both above) |

```bash
git config remote.pushDefault origin     # always push to my fork…
# …while branches still track upstream/* for pulls.
```

Now `@{push}` and `@{upstream}` diverge — exactly the case they were designed for:

```bash
git config push.default current
git config remote.pushDefault myfork
git switch -c mybranch origin/master
git rev-parse --symbolic-full-name @{upstream}   # refs/remotes/origin/master  (where you pull)
git rev-parse --symbolic-full-name @{push}       # refs/remotes/myfork/mybranch (where you push)
```

A single remote can also have a **separate push URL** (`remote.<name>.pushurl`; multiple = push to all) — but per the docs the push and fetch URLs must refer to the *same place*; for genuinely different fetch/push destinations, use two remotes.

## Pushing & deleting branches and tags

**Branches:**

```bash
git push origin feature                 # create/update remote 'feature'
git push origin local:remote-name       # push under a different remote name
git push origin --delete feature        # delete remote branch (modern, readable)
git push origin :feature                # same deletion via empty-src refspec
```

**Tags** are *not* pushed by `git push` by default:

```bash
git push origin v1.2.0                   # push one tag
git push origin --tags                   # push ALL tags
git push --follow-tags                   # push reachable annotated tags alongside commits (safest)
git push origin --delete v1.2.0          # delete a remote tag
git push origin :refs/tags/v1.2.0        # same, fully-qualified
```

**⚠️ Tags are immutable by convention.** Remotes reject *updates* to existing tags (PUSH RULES). Moving a tag requires deleting it remotely and pushing the new one — and anyone who already fetched the old tag keeps it. Prefer `--follow-tags` over `--tags` so you don't shove unrelated/local tags upstream. Pruning local tags against a remote → [Pruning](#pruning-stale-remote-tracking-refs). Tag *signing* → [advanced-features.md](advanced-features.md).

## Detached HEAD basics

Normally `HEAD` points at a *branch* (`ref: refs/heads/main`), and the branch points at a commit. **Detached `HEAD`** means `HEAD` points straight at a commit, with no branch in between. You land there by checking out a commit/tag/remote-tracking branch, or during `rebase`/`bisect`:

```bash
git checkout v2.0          # detaches at the tag's commit
git switch --detach v2.0   # explicit, switch-style (-d also works)
git checkout origin/main   # remote-tracking ref -> detached (no local branch)
git status                 # "HEAD detached at <sha>"
```

Commits you make while detached are referenced **only by `HEAD`**. The instant you check out something else, those commits become unreachable and are eventually deleted by `gc`:

```
     e---f   <- HEAD was here (now unreferenced after `git switch main`)
    /
a---b---c---d   main
```

**⚠️ Footgun — leaving detached HEAD loses work.** Before switching away, anchor the commits with a ref:

```bash
git switch -c newbranch    # keep work AND attach HEAD to the new branch (most common)
git branch keep-it         # create a branch at the current commit, HEAD stays detached
git tag keep-it            # tag the current commit, HEAD stays detached
```

If you *already* switched away and lost the commits, they're usually still recoverable via the reflog and `fsck` — see [recovery.md](recovery.md). Note `git switch -c` is transactional: it won't reset/create the branch if that branch is checked out in another worktree (see [worktrees-stash.md](worktrees-stash.md)).

## Quick reference

| Task | Command |
|---|---|
| List remotes + URLs | `git remote -v` |
| Change a remote's URL | `git remote set-url origin <url>` |
| Preview prune | `git remote prune -n origin` |
| Fetch + prune everything | `git fetch --all --prune` |
| Peek a remote branch without adding a remote | `git fetch <url> <branch>` then `git log FETCH_HEAD` |
| Linear pull | `git pull --rebase` (or `pull.rebase=true`) |
| Push + set upstream | `git push -u origin <branch>` |
| Safe force-push | `git push --force-with-lease --force-if-includes` |
| Force exactly one ref | `git push origin +<branch>` |
| Delete remote branch | `git push origin --delete <branch>` |
| Delete remote tag | `git push origin --delete <tag>` |
| Push reachable tags | `git push --follow-tags` |
| Show upstream + ahead/behind | `git branch -vv` |
| Commits ahead of upstream | `git log @{u}..` |
| Set upstream | `git branch -u origin/<branch>` |
| Keep detached-HEAD work | `git switch -c <newbranch>` |

**See also:** merge strategies / ff control for `git merge` and `cherry-pick`/`revert` → [branching-merging.md](branching-merging.md) · rebase mechanics → [history-rewriting.md](history-rewriting.md) · reflog & lost-commit recovery → [recovery.md](recovery.md) · full gitrevisions & object model → [internals-plumbing.md](internals-plumbing.md) · shallow/partial clone, bundles, signing → [advanced-features.md](advanced-features.md) · push-rejection / "divergent branches" errors → [troubleshooting.md](troubleshooting.md) · worktrees → [worktrees-stash.md](worktrees-stash.md) · back to [SKILL.md](../SKILL.md).
