# Git History Rewriting

Deliberately rewriting commit history: amending, interactive rebase (reorder/squash/split/edit), autosquash, transplanting with `--onto`, rebasing merges, force-updating stacked branches, and large-scale surgery across an entire repo. Reach for this when you need to *change commits that already exist* — not to undo a mistake (that's [recovery.md](recovery.md)).

**⚠️ The golden rule: never rewrite history that others have based work on.** Rewriting changes commit SHAs, so anyone who pulled the old commits is now forked from yours and must manually reconcile — a ripple that hits everyone downstream. Rewrite freely on local/unpushed branches and your own un-merged feature branches; **do not** rewrite shared branches (`main`, release branches) or anything others have pulled. If you must update a rewritten branch on a remote, push with `--force-with-lease` (never bare `--force`); see [refspecs-remotes.md](refspecs-remotes.md). For cleaning up *after someone upstream* rewrote history you depend on, see the "RECOVERING FROM UPSTREAM REBASE" guidance referenced in [recovery.md](recovery.md).

## Table of contents

- [`commit --amend`: fix the last commit](#commit---amend-fix-the-last-commit)
- [Interactive rebase: the basics](#interactive-rebase-the-basics)
- [The todo commands](#the-todo-commands)
- [Common recipes](#common-recipes)
- [Splitting a commit](#splitting-a-commit)
- [Autosquash: `--fixup` / `--squash`](#autosquash---fixup----squash)
- [`--update-refs`: rewriting stacked branches](#--update-refs-rewriting-stacked-branches)
- [`--onto`, `--keep-base`, `--root`](#--onto---keep-base---root)
- [Rebasing merges (`--rebase-merges`)](#rebasing-merges---rebase-merges)
- [`exec`: test every step](#exec-test-every-step)
- [Other useful rebase flags](#other-useful-rebase-flags)
- [Large-scale surgery: filter-repo, not filter-branch](#large-scale-surgery-filter-repo-not-filter-branch)
- [`fast-export` | `fast-import` surgery](#fast-export--fast-import-surgery)
- [Quick reference & footguns](#quick-reference--footguns)

## `commit --amend`: fix the last commit

Replaces the tip commit with a new one (new SHA, same parents and author unless changed).

```bash
git commit --amend                 # edit message + fold in staged changes
git commit --amend --no-edit       # fold staged changes in, keep the message as-is
git commit --amend -m "new msg"    # rewrite the message only (if nothing staged)
git commit --amend --only -m "msg" # rewrite message without committing already-staged changes
git commit --amend --reset-author  # also reset author name/email + timestamp to you
```

It is roughly equivalent to `git reset --soft HEAD^ && git commit -c ORIG_HEAD`. To amend an *older* commit, use interactive rebase with `edit` or `--fixup`/`--autosquash` (below). To amend by automatically routing fixes to the right commit, use the **git-absorb** skill. Commit-message formatting conventions: the **conventional-commits** skill.

**Footgun:** amending a pushed commit rewrites history — the same golden-rule caveat applies. The pre-amend commit is still recoverable via `HEAD@{1}` ([recovery.md](recovery.md)).

## Interactive rebase: the basics

```bash
git rebase -i <after-this-commit>  # edit every commit AFTER <after-this-commit>
git rebase -i HEAD~5               # edit the last 5 commits
git rebase -i --root               # include the very first commit (no upstream)
```

An editor opens with a **todo list**, one line per commit, oldest at top:

```
pick deadbee Implement feature X
pick fa1afe1 Fix typo
pick c0ffeee Add tests
```

Replace the `pick` verbs and/or reorder lines, then save+close. Git replays the list top-to-bottom. The oneline text is cosmetic — Git keys off the SHA, so don't edit the SHAs. **Deleting a line drops that commit.**

When rebase stops (a `break`/`edit` command, or a conflict):

| Command | Action |
|---------|--------|
| `git rebase --continue` | Resume after staging conflict resolutions / finishing an edit |
| `git rebase --skip` | Skip the current commit |
| `git rebase --abort` | Bail out, restore the original branch state |
| `git rebase --quit` | Stop but leave HEAD where it is (don't restore) |
| `git rebase --edit-todo` | Re-open and edit the remaining todo list |
| `git rebase --show-current-patch` | Show the stuck commit (`git show REBASE_HEAD`) |

On conflict: edit files, `git add` the resolved ones, then `git rebase --continue`. To recover from a rebase gone wrong, see [recovery.md](recovery.md) (`--abort`, `ORIG_HEAD`, `<branch>@{1}`).

## The todo commands

The full command set (verbatim from `git rebase -i`'s help, git 2.54.0). Single-letter aliases in parentheses.

| Command | Does |
|---------|------|
| `pick` (`p`) | Use the commit as-is |
| `reword` (`r`) | Use the commit, but stop to **edit its message** |
| `edit` (`e`) | Use the commit, but **stop for amending** (change content, split, etc.) |
| `squash` (`s`) | **Meld into the previous commit**; combine both messages in the editor |
| `fixup` (`f`) | Like `squash` but **discard this commit's message** (keep the previous one) |
| `fixup -C` | Meld in, but **keep only THIS commit's message** (discard the previous) |
| `fixup -c` | Same as `-C` but **opens the editor** to refine the kept message |
| `drop` (`d`) | **Remove** the commit (same as deleting the line) |
| `exec` (`x`) | **Run a shell command**; non-zero exit halts the rebase |
| `break` (`b`) | **Stop here**; resume later with `git rebase --continue` |
| `label` (`l`) | Label current HEAD with a name (for `--rebase-merges`) |
| `reset` (`t`) | Reset HEAD to a previously set `label` |
| `merge` (`m`) | Create a merge commit (`-C <commit>` reuse message, `-c <commit>` reword) |
| `update-ref` (`u`) | Placeholder to **point `<ref>` at this spot**, updated at rebase end (see `--update-refs`) |

`label`, `reset`, `merge`, and `update-ref` are injected automatically by `--rebase-merges` and `--update-refs`, but you can also write them by hand.

## Common recipes

```bash
# Reword an older commit's message:
git rebase -i HEAD~4        # change `pick` → `reword` (r) on the target line

# Squash the last 3 commits into one:
git rebase -i HEAD~3        # keep the top `pick`, set the other two to `squash` (or `fixup`)

# Drop a specific commit:
git rebase -i <sha>^        # set its line to `drop`, or just delete the line

# Reorder commits: cut-and-paste the lines into the desired order.

# Edit the *content* of an older commit:
git rebase -i <sha>^        # set its line to `edit`; rebase stops at it
#   ...make changes...
git add -A && git commit --amend
git rebase --continue
```

**Empty commits:** a commit that becomes empty after rebasing (its changes already upstream) is dropped by default; control with `--empty=(drop|keep|stop)`. Commits that *start* empty are kept unless `--no-keep-empty`.

## Splitting a commit

Mark the commit `edit`; when rebase stops, undo the commit but keep its changes, then re-commit in pieces (from the rebase docs' SPLITTING COMMITS):

```bash
git rebase -i <commit>^        # set <commit> to `edit`
# When rebase stops on it:
git reset HEAD^                # undo the commit; index + HEAD rewind, working tree untouched
git add -p                     # stage the first logical chunk interactively
git commit -c HEAD@{1}         # commit it (reuse the original message as a starting point)
git add -p && git commit       # repeat for remaining chunks until the tree is clean
git rebase --continue
```

`git reset HEAD^` here is the `--mixed` reset; the three reset modes are detailed in [recovery.md](recovery.md). Use `git add -p`/`git reset -p` to carve hunks; verify with `git diff --cached` between commits.

## Autosquash: `--fixup` / `--squash`

Create specially-named commits now, then let rebase reorder and fold them automatically.

```bash
git commit --fixup=<commit>          # makes "fixup! <subject>" — folds in, drops its message
git commit --squash=<commit>         # makes "squash! <subject>" — folds in, combines messages
git commit --fixup=amend:<commit>    # "amend!" — replaces both content AND message of <commit>
git commit --fixup=reword:<commit>   # "amend!" message-only (no content change)

git rebase -i --autosquash <base>    # reorders squash!/fixup!/amend! commits under their targets
```

`--autosquash` rewrites the matched lines from `pick` to `squash` (for `squash!`), `fixup` (for `fixup!`), or `fixup -C` (for `amend!`) and moves each right after the commit it targets. With `-i` you still get to review the todo list first. Enable by default with `rebase.autoSquash=true` (override per-run with `--no-autosquash`). Match is by subject text or SHA.

To generate these fixup commits **automatically** by detecting which commit each change belongs to, use the **git-absorb** skill (`git absorb`).

## `--update-refs`: rewriting stacked branches

When several branches point at commits *within* the range being rebased (a stack), `--update-refs` force-moves those intervening branch refs to follow their commits instead of being left behind:

```bash
git rebase -i --update-refs <base>   # injects `update-ref refs/heads/<branch>` lines into the todo
git config rebase.updateRefs true    # make it the default for interactive rebases
```

The todo list gains `update-ref` lines at each branch's position; all listed refs are updated atomically when the rebase finishes. **Branches checked out in a worktree are not updated this way.** For full stacked-branch *automation* (rebasing/merging an entire chain, tracking dependencies), use the **git-chain** skill — it's purpose-built for that workflow.

## `--onto`, `--keep-base`, `--root`

`--onto <newbase>` sets where replayed commits land, independently of which commits are selected. The general form is `git rebase --onto <newbase> <upstream> [<branch>]` = "take `<upstream>..<branch>` and replant it onto `<newbase>`".

```bash
# Move topic from being based on `next` to being based on `main`:
git rebase --onto main next topic
#   o--o--o main           →    o--o--o main
#          \                            \
#           (next)..topic                topic'

# Excise a range of commits (drop F and G from a linear topicA):
git rebase --onto topicA~5 topicA~3 topicA      # replays topicA~3..topicA onto topicA~5

# Keep the original base, just clean up the branch's own commits:
git rebase --keep-base <upstream>               # base = merge-base(upstream, HEAD); implies --reapply-cherry-picks

# Rebase including the root commit (edit the very first commit):
git rebase -i --root
```

`--onto` accepts any commit-ish, and the `A...B` merge-base shorthand. `--keep-base` and `--onto`/`--root` are mutually exclusive.

## Rebasing merges (`--rebase-merges`)

By default rebase *flattens* history — merge commits are dropped and their contents linearized. `--rebase-merges` instead **recreates the merge topology**:

```bash
git rebase -i --rebase-merges <base>
git rebase -i --rebase-merges=rebase-cousins <base>     # also rebase commits off the ancestry path
git rebase -i -r --onto Q O                             # replant a topology onto Q
```

The todo list uses `label`/`reset`/`merge` to rebuild structure:

```
label onto
reset onto
pick 123456 Extract Button class
label refactor-button
reset onto
merge -C a1b2c3 refactor-button     # recreate the merge, reusing its message
```

- `label <name>` tags the current HEAD (stored as worktree-local `refs/rewritten/<name>`, deleted when rebase ends).
- `reset <label>` resets HEAD/index/worktree to a label (refuses to clobber untracked files).
- `merge -C <orig>` recreates a merge reusing the original message; `-c` opens the editor; a bare `merge <label>` creates a brand-new merge.
- Modes: `no-rebase-cousins` (default) keeps off-ancestry commits at their original base; `rebase-cousins` moves them onto the new base. Merges use the `ort` strategy; other strategies require an explicit `exec git merge -s …`. **⚠️ Conflict resolutions baked into the original merges must be re-resolved by hand.**

## `exec`: test every step

Run a command after commits to catch breakage at each point in history.

```bash
git rebase -i --exec "make test" <base>   # appends `exec make test` after every commit
git rebase -i --exec "cargo build" --exec "cargo test" <base>   # multiple commands
```

A non-zero exit halts the rebase so you can fix that commit (`--reschedule-failed-exec` re-runs the failed `exec` after you continue). Commands run via the shell from the worktree root. With `--autosquash`, `exec` lines are appended only after each squash/fixup series completes, not for intermediate commits.

## Other useful rebase flags

| Flag | Effect |
|------|--------|
| `--autostash` | Stash dirty worktree before, reapply after (run rebase without committing WIP) |
| `--committer-date-is-author-date` | Set committer date = author date (implies `--force-rebase`) |
| `--ignore-date` / `--reset-author-date` | Set author date = now |
| `--signoff` | Add `Signed-off-by:` to each rebased commit |
| `--reapply-cherry-picks` | Don't auto-drop commits already upstream (re-apply them) |
| `--no-keep-empty` | Also drop commits that *started* empty |
| `-f` / `--force-rebase` | Replay even unchanged commits (fresh SHAs); useful after reverting a merge |
| `-x`/`--exec`, `-r`/`--rebase-merges`, `-i` | As above |

`--autostash` is a convenience, but **its post-rebase reapply can itself conflict** — non-trivial conflicts get left in the worktree for you to resolve.

## Large-scale surgery: filter-repo, not filter-branch

To rewrite **all** history — purge a leaked secret or huge binary from every commit, change every commit's author email, extract a subdirectory into its own repo — the recommended tool is **`git filter-repo`**.

**`git filter-repo` is NOT part of core git** — it is a separate project ([github.com/newren/git-filter-repo](https://github.com/newren/git-filter-repo)), installed separately (e.g. `pip install git-filter-repo`, `brew install git-filter-repo`). It is fast, safe-by-default, and the officially recommended replacement.

```bash
# (external tool) remove a file from ALL history:
git filter-repo --invert-paths --path secrets.env
# extract a subdirectory as the new repo root:
git filter-repo --subdirectory-filter src/lib
# rewrite author/committer email across all commits:
git filter-repo --email-callback 'return email.replace(b"old@x.com", b"new@y.com")'
```

**⚠️ Do NOT use `git filter-branch`.** Its own man page carries this WARNING: it "has a plethora of pitfalls that can produce non-obvious manglings of the intended history rewrite" and "abysmal performance," the safety issues "cannot be backward compatibly fixed and as such, its use is not recommended." Use `git filter-repo` instead. (If somehow unavoidable: `filter-branch` honors `.git/info/grafts` and `refs/replace/`, backs originals up under `refs/original/`, and you must read its SAFETY and PERFORMANCE sections first.)

**⚠️ Whole-history rewrites change every downstream SHA** — coordinate with everyone, force-push with lease, and have collaborators re-clone. To remove a big file going forward *without* rewriting, see partial clone / sparse-checkout in [advanced-features.md](advanced-features.md).

## `fast-export` | `fast-import` surgery

For bespoke rewrites that no canned tool covers, dump history to an editable text stream and feed it back. (`git filter-repo` is built on exactly this.)

```bash
# Mirror a repo through the stream (one-to-one except re-encoding to UTF-8):
git fast-export --all | (cd /empty/repo && git fast-import)

# Rewrite branch names / paths with a stream filter:
git fast-export master~5..master | sed 's|refs/heads/master|refs/heads/other|' | git fast-import
```

Useful `fast-export` options: `--no-data` (refer to blobs by SHA — fast structural rewrites without touching file contents), `--full-tree` (emit a full `deleteall` + file list per commit), `--signed-tags=(strip|abort|…)` and `--signed-commits=…` (signatures break under rewrite), `--tag-of-filtered-object=(abort|drop|rewrite)`, `--anonymize` (share a bug repro with identifying data stripped), `--reencode`, `--mark-tags`/`--export-marks`/`--import-marks` (incremental).

The stream's `commit` block grammar is: `commit <ref>`, optional `mark`, `author`/`committer`, `data` (the message), optional `from`/`merge` (parents), then `filemodify`/`filedelete`/`filecopy`/`filerename`/`filedeleteall` to shape the tree. Editing these lines (or piping through `sed`/a script) is how surgical rewrites are done.

**Non-destructive alternative:** to make a commit *appear* changed without rewriting (e.g. splice in history, swap a commit) use `git replace` — covered in [advanced-features.md](advanced-features.md).

## Quick reference & footguns

| Goal | Command |
|------|---------|
| Fix the last commit | `git commit --amend` |
| Reword/reorder/drop/squash older commits | `git rebase -i <base>` |
| Fold a fix into an older commit automatically | `git commit --fixup=<sha>` → `git rebase -i --autosquash <base>` |
| Edit content of an older commit | `git rebase -i <sha>^`, set `edit` |
| Split one commit into several | `edit` → `git reset HEAD^` → `add -p` + `commit` ×N |
| Move a branch onto a new base | `git rebase --onto <newbase> <upstream> <branch>` |
| Keep stacked branches aligned | `git rebase -i --update-refs <base>` (or the git-chain skill) |
| Preserve merges while rebasing | `git rebase -i --rebase-merges <base>` |
| Test each commit | `git rebase -i --exec "<test cmd>" <base>` |
| Purge a file/secret from all history | `git filter-repo --invert-paths --path <file>` *(external tool)* |

**Footguns recap:** (1) **Never** rewrite shared/published history — coordinate and use `--force-with-lease`. (2) `git filter-branch` is discouraged — use `git filter-repo`. (3) `--rebase-merges` does **not** auto-reapply conflict resolutions. (4) Any rewrite changes SHAs; downstream clones diverge. (5) Mid-rewrite disaster → [recovery.md](recovery.md) (`--abort`, `ORIG_HEAD`, reflog). (6) Rewriting drops commits-that-become-empty by default (`--empty=keep` to retain).
