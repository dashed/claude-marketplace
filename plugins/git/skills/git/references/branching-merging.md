# Branching, Merging, Cherry-pick & Revert

Combining and replaying history: merge **strategies** and their `-X` options, fast-forward control, resolving merge conflicts, reusing resolutions with **rerere**, choosing **rebase vs merge**, and replaying individual commits with **`cherry-pick`** and reversing them with **`revert`** (including the merge gotchas). Targets git 2.54+.

Reach here when you need to merge with a non-default strategy, control whether a merge fast-forwards, untangle a conflict, back out a commit safely, port a fix between branches, or revert a merge. For *undoing* a merge/rebase you already ran (reflog, `reset --merge ORIG_HEAD`), see [recovery.md](recovery.md); for the *mechanics* of interactive rebase todo lists, see [history-rewriting.md](history-rewriting.md).

## Table of Contents

- [Merge strategies](#merge-strategies)
- [`-X` strategy options](#-x-strategy-options)
- [Fast-forward control (`--ff` / `--no-ff` / `--ff-only`)](#fast-forward-control)
- [Squash merge](#squash-merge)
- [Merging tags](#merging-tags)
- [Resolving a merge conflict](#resolving-a-merge-conflict)
- [rerere — reuse recorded resolutions](#rerere--reuse-recorded-resolutions)
- [Rebase vs merge — which to use](#rebase-vs-merge--which-to-use)
- [`cherry-pick`](#cherry-pick)
- [`revert`](#revert)
- [Reverting a merge (and the re-merge gotcha)](#reverting-a-merge-and-the-re-merge-gotcha)
- [Quick reference](#quick-reference)

---

## Merge strategies

`git merge -s <strategy>` (also `git pull -s …`, `git rebase -s …`, `cherry-pick/revert -s …`). With no `-s`, git picks **`ort`** for one branch and **`octopus`** for more than one.

| Strategy | Heads | What it does | Use when |
|----------|:-----:|--------------|----------|
| **`ort`** *(default)* | 2 | 3-way merge; merges multiple merge-bases into a virtual base; detects renames; writes `AUTO_MERGE` on conflict | Almost always. "Ostensibly Recursive's Twin" — replaced `recursive`. |
| **`octopus`** *(default for >2)* | 3+ | Merges many heads at once; **refuses** anything needing manual conflict resolution | Bundling several already-clean topic tips into one merge commit |
| **`ours`** | any | Records a merge but keeps **our** tree verbatim — discards *all* changes from the other side(s) | Superseding a dead side branch while keeping it in history |
| **`subtree`** | 2 | `ort` variant that shifts one tree to match the other's path layout before merging | Merging a project that lives under a subdirectory |
| `resolve` | 2 | Legacy 3-way; no rename detection | Rarely; only if `ort` misbehaves |
| `recursive` | 2 | **Synonym for `ort`** since v2.50 (was the pre-2.34 default) | n/a — just use `ort` |

```bash
git merge topic                  # ort (default)
git merge -s octopus a b c       # one merge commit with 4 parents
git merge -s ours obsolete       # keep our tree; record obsolete as merged
```

**⚠️ `-s ours` is not `-X ours`.** The `ours` *strategy* ignores the other side completely (no content from it ever lands). The `-X ours` *option* (below) does a real 3-way merge and only favors our side **on conflicting hunks** — non-conflicting changes from the other side are still taken. Easy to confuse; the effects are wildly different.

**3-way merge subtlety:** with any 3-way strategy, if a change was made on both branches but later reverted on only one, the change reappears in the merge result — only the two tips and the merge base are compared, not intermediate commits. To truly drop it you must revert again after merging.

## `-X` strategy options

Pass strategy-specific options with `-X` (`--strategy-option`). These apply to the default `ort`:

| `-X` option | Effect |
|-------------|--------|
| `-X ours` | On **conflicting** hunks, take our side automatically (non-conflicting other-side changes still merged). Binary files: take ours whole. |
| `-X theirs` | Opposite of `-X ours`. (There is **no** `theirs` *strategy*, only this option.) |
| `-X ignore-space-change` / `-X ignore-all-space` / `-X ignore-space-at-eol` / `-X ignore-cr-at-eol` | Treat the indicated whitespace change as no change during 3-way merge |
| `-X renormalize` / `-X no-renormalize` | Virtually check out+in all three stages — use when sides differ in EOL/clean filters (see [config-attributes-hooks.md](config-attributes-hooks.md)) |
| `-X find-renames[=<n>]` | Rename detection with optional similarity threshold (default; this is on) |
| `-X no-renames` | Disable rename detection |
| `-X diff-algorithm=(histogram\|minimal\|myers\|patience)` | Diff algorithm used while merging — can avoid mismerges from coincidentally matching lines (e.g. braces). `ort` defaults to `histogram`. |
| `-X subtree[=<path>]` | Advanced subtree shifting |

**Deprecated synonyms (still work, prefer the modern form):** `-X rename-threshold=<n>` → `-X find-renames=<n>`; `-X patience` → `-X diff-algorithm=patience`; `-X histogram` → `-X diff-algorithm=histogram`.

```bash
git merge -X theirs feature              # prefer their side on conflicts
git merge -X ignore-all-space feature    # ignore whitespace-only conflicts
git merge -X diff-algorithm=patience x   # less-confused diff during merge
git rebase -X theirs main                # -X works on rebase too
```

**Footgun:** `-X theirs` resolves *every* conflict in their favor silently. You may discard intentional local changes without noticing. Review the merge diff afterward (`git diff ORIG_HEAD`).

## Fast-forward control

When the other branch is already ahead of yours (your tip is its ancestor), git can just move the pointer — no merge commit. Control it:

| Flag | Behavior |
|------|----------|
| `--ff` *(default)* | Fast-forward when possible; otherwise create a merge commit |
| `--no-ff` | **Always** create a merge commit, even when a fast-forward was possible (preserves the topic branch's existence in history) |
| `--ff-only` | Fast-forward if possible; otherwise **refuse** and exit non-zero (never makes a merge commit) |

```bash
git merge --no-ff feature     # keep an explicit merge bubble for the topic
git merge --ff-only origin/main   # only update if it's a clean fast-forward
git config merge.ff false     # make --no-ff the default for this repo
git config pull.ff only       # pulls must be fast-forwardable
```

Set the default with `merge.ff` (`true`/`false`/`only`). For `pull`'s rebase-vs-merge reconciliation (`pull.rebase`, `pull.ff`), see [refspecs-remotes.md](refspecs-remotes.md).

**Note:** a fast-forward creates no merge commit, so `--no-commit` can't stop it. To guarantee the merge is inspectable before committing, combine `--no-ff --no-commit`.

## Squash merge

`--squash` stages the merged result but makes **no commit** and records **no second parent** — the next `git commit` is an ordinary single-parent commit with the combined effect.

```bash
git merge --squash feature    # stage feature's net change
git commit                    # one normal commit; feature NOT recorded as merged
```

**Footgun:** a squash-merge does **not** mark `feature` as merged (no merge edge). Later `git merge feature` will try to merge it again, and `git branch --merged` won't list it. Delete the squashed branch deliberately. `--squash` with `--commit` is an error.

## Merging tags

Merging an **annotated** tag always creates a merge commit (even if a fast-forward was possible) and seeds the message from the tag. To integrate without an extra commit, unwrap the tag or force fast-forward:

```bash
git merge v1.2.3          # makes a merge commit, with the tag's message
git merge v1.2.3^0        # ^0 = the commit the tag points to → can fast-forward
git merge --ff-only v1.2.3
```

## Resolving a merge conflict

When `ort` can't auto-resolve, the merge **stops**: `HEAD` stays put, `MERGE_HEAD` points at the other tip, conflicting files get markers, and the index records up to three **stages** per conflicted path.

```bash
git merge feature
# CONFLICT (content): Merge conflict in app.py
git status              # lists "Unmerged paths"
```

**Conflict stages** (inspect with `git ls-files -u`, view with `git show :N:<path>`):

| Stage | Source | Diff flag |
|:-----:|--------|-----------|
| 1 | merge base (common ancestor) | `git show :1:app.py` / `git diff --base` (`-1`) |
| 2 | **ours** (`HEAD`) | `git show :2:app.py` / `git diff --ours` (`-2`) |
| 3 | **theirs** (`MERGE_HEAD`) | `git show :3:app.py` / `git diff --theirs` (`-3`) |

**Conflict markers** in the working tree:

```text
<<<<<<< HEAD            ← our side begins
our version
=======
their version
>>>>>>> feature         ← their side ends
```

Set a richer style to also see the original via a middle `|||||||` block:

```bash
git config merge.conflictStyle zdiff3   # diff3 minus duplicated context (recommended)
# values: merge (default, no base) | diff3 (shows base) | zdiff3
```

**Resolve, then continue:**

```bash
git diff                       # combined diff of what's still conflicting
git diff AUTO_MERGE            # what you've changed so far (ort writes AUTO_MERGE)
# --- pick a whole side without editing: ---
git checkout --ours app.py     # take our version wholesale (or: git restore --source=:2 ...)
git checkout --theirs app.py   # take their version wholesale
git mergetool                  # or launch a 3-way GUI
# --- after editing files into shape: ---
git add app.py                 # marks the path resolved (collapses the stages)
git merge --continue           # finishes (checks a merge is in progress, then commits)
```

**Bail out:**

```bash
git merge --abort      # restore pre-merge state (≈ git reset --merge while MERGE_HEAD exists)
git merge --quit       # forget the merge but leave the index/worktree as-is
```

**⚠️** `git merge --abort` may fail to reconstruct **uncommitted** changes that existed before the merge — commit or stash before merging. For deeper undo (already committed the bad merge, recovering with `ORIG_HEAD`/reflog), see [recovery.md](recovery.md). To stop hitting the *same* conflict repeatedly, enable rerere (next).

> Conflict-marker collisions: if your file legitimately contains `<<<<<<<`-like lines, raise `conflict-marker-size` via `.gitattributes` — see [config-attributes-hooks.md](config-attributes-hooks.md).

## rerere — reuse recorded resolutions

**rerere** ("reuse recorded resolution") records how you resolved a conflict and **replays** that resolution automatically the next time the identical conflict appears — invaluable for long-lived branches you re-merge/rebase repeatedly, and for re-resolving after dropping a test merge.

```bash
git config --global rerere.enabled true   # turn it on (once)
# ...resolve a conflict normally: edit, git add, commit...
# rerere silently records base/conflict/resolution under .git/rr-cache/
```

Next time the same textual conflict occurs, git pre-fills the working-tree files with your recorded resolution. By default it leaves the **index** alone, so you still review and `git add`:

```bash
git config rerere.autoUpdate true   # also stage auto-resolved files (default: false)
git merge --no-rerere-autoupdate x  # one-off: double-check before staging
```

rerere is auto-invoked by `merge`, `commit`, and `rebase`. It activates automatically in any repo that already has a `.git/rr-cache/` directory (so `rerere.enabled` effectively sticks once used).

**Commands:**

| Command | Purpose |
|---------|---------|
| `git rerere status` | Paths whose resolution rerere will record |
| `git rerere remaining` | Conflicted paths **not** auto-resolved yet |
| `git rerere diff` | Diff of the in-progress resolution |
| `git rerere forget <pathspec>` | **Discard** a recorded resolution for the current conflict (use when you resolved it wrong and re-resolved) |
| `git rerere gc` | Prune old records (unresolved >15 days, resolved >60 days; tune `gc.rerereUnresolved`/`gc.rerereResolved`) |

**Footgun:** a *wrong* recorded resolution gets replayed silently forever. If a conflict keeps resolving incorrectly, `git rerere forget <path>`, fix it by hand, and re-add. rerere matches on conflict-marker text, so it can mis-fire if markers look unusual.

## Rebase vs merge — which to use

Both integrate branches; they differ in the history they produce. (`rebase` *replays* your commits onto a new base, creating new commit hashes; `merge` *joins* with a merge commit.)

| Prefer **merge** when | Prefer **rebase** when |
|-----------------------|------------------------|
| The branch is **shared/published** (rebasing rewrites hashes others have) | The branch is **local/unpushed** and you want a linear history |
| You want to preserve the true topology / when work happened | Cleaning up before opening a PR (`rebase -i`) |
| Integrating long-running branches | Keeping a feature current atop `main` without merge bubbles |

```bash
git switch feature
git rebase main                 # replay feature's commits on top of main
git merge --no-ff feature       # alternative: explicit merge bubble onto main
```

**⚠️ The golden rule:** never rebase commits that exist in someone else's repository. Rewriting published history forces everyone to recover manually. If it's shared, `merge` or `revert` instead. To rebase *and* keep the topology of merges, use `git rebase --rebase-merges`; for the full interactive-rebase todo language (`pick`/`squash`/`fixup`/`edit`/`drop`/`exec`/…), `--autosquash`, and `--update-refs`, see [history-rewriting.md](history-rewriting.md). For stacked dependent branches use the **git-chain** skill; for auto-folding fixups use the **git-absorb** skill. `pull --rebase` lives in [refspecs-remotes.md](refspecs-remotes.md).

## cherry-pick

Apply the change introduced by existing commit(s) as **new** commits on the current branch. Working tree must be clean.

```bash
git cherry-pick <hash>              # apply one commit here
git cherry-pick A B C               # apply several, in order
git cherry-pick -x <hash>           # append "(cherry picked from commit …)"
git cherry-pick -n <hash>           # apply to worktree+index, do NOT commit (-n/--no-commit)
git cherry-pick -e <hash>           # edit the message before committing
git cherry-pick -s <hash>           # add Signed-off-by trailer
```

| Flag | Meaning |
|------|---------|
| `-x` | Record the source commit in the message. **Only for public→public** ports (e.g. backporting to a maintenance branch); useless/noise for private branches. Added only for conflict-free picks. |
| `-n` / `--no-commit` | Stage the change without committing; index need not match HEAD (lets you pick several into one commit) |
| `-m <parent-number>` | Cherry-pick a **merge** relative to mainline parent N (see below) |
| `--ff` | If HEAD is the picked commit's parent, fast-forward instead of making a new commit |
| `-e` / `--edit`, `-s` / `--signoff`, `-S` | Edit message / add sign-off / GPG-sign (signing → [advanced-features.md](advanced-features.md)) |

**Commit ranges** — cherry-pick takes a range (fed to a single revision walk, no merges traversed by default):

```bash
git cherry-pick A..B       # every commit reachable from B but not A → replay onto HEAD
git cherry-pick A^..B      # include A itself (A^..B = A through B inclusive)
```

**⚠️ `A..B` excludes `A`.** The lower bound is open: `git cherry-pick v1..v2` does **not** include `v1`. Use `A^..B` (or `^A^ B`) to include the start commit. Likewise in the documented form `git cherry-pick maint master..next`, `maint` is silently skipped if it's already contained in `master`.

**Cherry-picking a merge commit** needs `-m` to pick which parent is the mainline (the side whose changes you want to keep as the baseline):

```bash
git cherry-pick -m 1 <merge-hash>   # replay the merge's net change relative to parent #1
```

**Empty / redundant commits:** if a pick's change is already present, the pick *stops* by default so you can inspect it.

```bash
git cherry-pick --empty=drop A..B   # silently drop now-redundant commits
git cherry-pick --empty=keep A..B   # keep them as empty commits
# default is --empty=stop. --keep-redundant-commits is a deprecated synonym for --empty=keep.
# An INITIALLY-empty commit still fails unless --allow-empty (or --empty=keep) is given.
```

**Conflicts** use the sequencer — resolve, then:

```bash
git cherry-pick --continue    # after git add of resolved files
git cherry-pick --skip        # skip this commit, keep going
git cherry-pick --abort       # undo the whole sequence, restore pre-pick state
git cherry-pick --quit        # stop but leave current state (clears sequencer)
```

## revert

Create a **new** commit that undoes a previous commit — the safe way to back out work that's already **pushed** (it adds history rather than rewriting it). Working tree must be clean.

```bash
git revert <hash>             # new commit reversing <hash> (opens editor by default)
git revert --no-edit <hash>   # accept the auto message
git revert -n <hash>          # apply the reversal to worktree+index without committing (-n)
git revert HEAD~3             # revert the 4th-from-top commit
git revert -n A^..B           # reverse a whole range into the index, no commits
```

Same sequencer subcommands as cherry-pick: `--continue` / `--skip` / `--abort` / `--quit`. `revert.reference` (or `--reference`) makes the auto message refer to the reverted commit in `--pretty=reference` style.

> To *discard* uncommitted changes use `git reset`/`git restore`, not `revert` (which is for already-committed work). See [recovery.md](recovery.md).

## Reverting a merge (and the re-merge gotcha)

You can't revert a merge without saying which parent is the mainline, because git doesn't know which side's changes to undo:

```bash
git revert -m 1 <merge-hash>   # undo the changes the merge brought in, relative to parent 1
```

`-m 1` is almost always the first-parent (the branch you were on when you merged), so this reverts the *side branch's* contribution.

**⚠️ The re-merge gotcha.** Reverting a merge undoes the merge's *content* but the **merge edge stays in history**. Git now believes those changes are already integrated, so simply re-merging the branch later **brings in nothing** — the side branch's commits are ancestors of the (reverted) merge. To genuinely re-integrate the branch after fixing it, you must **revert the revert**:

```bash
git revert <the-revert-commit>   # re-apply the changes, THEN merge new work on top
git merge feature                # now picks up only commits made AFTER the original merge
```

This is the classic "I reverted a faulty merge, fixed the branch, re-merged, and my fixes are missing" trap. The canonical write-up is Linus Torvalds' *"How to revert a faulty merge"* (`Documentation/howto/revert-a-faulty-merge.txt` in git's source). For undoing a merge you just made **locally** (not yet shared) without leaving a revert in history, use `git reset --merge ORIG_HEAD` — see [recovery.md](recovery.md). Commit-message wording for any of these → the **conventional-commits** skill.

## Quick reference

| Task | Command |
|------|---------|
| Merge, keep topic visible | `git merge --no-ff feature` |
| Merge only if fast-forward | `git merge --ff-only origin/main` |
| Prefer our/their side on conflicts | `git merge -X ours` / `git merge -X theirs feature` |
| Discard the other side entirely | `git merge -s ours obsolete` |
| Squash a branch into one commit | `git merge --squash feature && git commit` |
| See conflict base/ours/theirs | `git show :1:f` / `:2:f` / `:3:f` |
| Take one whole side of a conflict | `git checkout --ours f` / `--theirs f` |
| Finish / abort a conflicted merge | `git merge --continue` / `git merge --abort` |
| Enable conflict-resolution reuse | `git config --global rerere.enabled true` |
| Forget a bad recorded resolution | `git rerere forget <path>` |
| Backport one commit, note origin | `git cherry-pick -x <hash>` |
| Cherry-pick range incl. start | `git cherry-pick A^..B` |
| Cherry-pick a merge | `git cherry-pick -m 1 <merge>` |
| Undo a pushed commit | `git revert <hash>` |
| Undo a pushed merge | `git revert -m 1 <merge>` |
| Re-enable a reverted merge | `git revert <revert-commit>` then merge |

**See also:** [recovery.md](recovery.md) (undo merge/rebase, reflog, `ORIG_HEAD`) · [history-rewriting.md](history-rewriting.md) (interactive rebase, `--rebase-merges`) · [refspecs-remotes.md](refspecs-remotes.md) (`pull --rebase`, push) · [inspection.md](inspection.md) (`log --graph`, `--cherry`) · [config-attributes-hooks.md](config-attributes-hooks.md) (merge drivers, `conflict-marker-size`) · [SKILL.md](../SKILL.md).
