---
name: git
description: Advanced Git CLI mastery, recovery, and troubleshooting (git 2.54+). Use whenever a git task goes beyond the basics — recovering lost commits/branches/stashes (reflog, fsck), undoing a bad reset/merge/rebase/amend, rewriting history (interactive rebase, --autosquash, --update-refs, filter-repo), resolving merge conflicts or using rerere, working with worktrees, bisect, cherry-pick, revert, or stash, understanding refspecs/remotes/push behavior and --force-with-lease, configuring .gitattributes/.gitignore/hooks, exploring git internals (object model, plumbing like cat-file/rev-parse), or diagnosing confusing errors (detached HEAD, dubious ownership, non-fast-forward, CRLF). Trigger even when the user doesn't name the exact command but is clearly stuck or doing something non-trivial in git. For commit-message wording use conventional-commits; for stacked/dependent branches use git-chain; for auto-folding fixups use git-absorb; for Jujutsu use jj.
---

# Git — Advanced CLI Mastery & Recovery

## Overview

This skill is the **power-user and recovery reference** for the Git command line (targeting **git 2.54+**). It is *not* a beginner tutorial — it assumes the everyday `add`/`commit`/`push` loop is already understood and instead focuses on the parts of Git that are **easy to get wrong, easy to forget, or costly to mess up**:

- Getting back work that seems lost (reflog, `fsck`, dangling objects).
- Rewriting history safely and understanding what each operation actually moves.
- The mental models (object graph, HEAD/index/worktree, refspecs) that make confusing behavior obvious.
- Power features Claude tends to underuse: worktrees, bisect, rerere, sparse-checkout, partial clone, notes, bundles.
- Diagnosing cryptic error messages.

**Core principle:** In Git, **commits are rarely truly lost** until garbage collection runs (default ~90 days for reachable-from-reflog, ~30 for unreachable). Almost every "oh no" is recoverable via the reflog or `fsck`. Stay calm; diagnose before acting; avoid `--hard`/`--force`/`clean` until you understand the current state.

## When to Use This Skill

- Recovering lost commits, branches, or stashes; undoing a reset/merge/rebase/amend.
- Interactive rebase, history surgery, squashing/splitting/reordering commits, removing a large file or secret from history.
- Merge strategy choices, conflict resolution, `rerere`, `cherry-pick`, `revert` (including reverting a merge).
- Inspecting history: `log` formats, pickaxe (`-S`/`-G`), line-log (`-L`), `blame`, `range-diff`, `git grep`.
- Remotes, refspecs, fetch/pull/push semantics, upstream tracking, safe force-pushing.
- Worktrees and stash management.
- Git internals / plumbing (`cat-file`, `rev-parse`, `rev-list`, object model, packfiles, gc).
- `git config`, `.gitattributes`, `.gitignore`, hooks, aliases.
- Submodules, subtree, sparse-checkout, partial/shallow clone, bundles, notes, bisect, signing.
- Any confusing git error or unexpected state.

## When NOT to Use This Skill (defer to the specialist)

| Task | Use instead |
|------|-------------|
| Writing/formatting a commit *message* (Conventional Commits) | **conventional-commits** skill |
| Managing/rebasing chains of stacked dependent branches/PRs | **git-chain** skill |
| Auto-folding uncommitted changes into the right earlier commits | **git-absorb** skill |
| Jujutsu (`jj`) workflows | **jj** skill |

This skill covers core git itself; the workflows above have dedicated skills. Cross-reference them rather than reinventing.

## Mental Models You Must Get Right

### The object model

Git stores four object types, addressed by the hash of their content:

- **blob** — file contents (no name).
- **tree** — a directory listing: names → blobs/trees + modes.
- **commit** — a snapshot: one root tree + parent commit(s) + author/committer + message.
- **tag** (annotated) — a named, signed pointer to an object.

**Branches and tags are just refs** — files under `.git/refs/` (or `packed-refs`) containing a commit hash. `HEAD` is a ref that usually *points at a branch* (`ref: refs/heads/main`); when it points directly at a commit you are in **detached HEAD**. A commit is "reachable" if you can walk to it from a ref; unreachable commits await gc. Deep dive: [internals-plumbing.md](references/internals-plumbing.md).

### HEAD, the index, and the working tree

Three states a file moves between:

```
working tree   --(git add)-->   index/staging   --(git commit)-->   HEAD (history)
   (edits)                         (staged)                          (committed)
```

- `git status` shows differences between all three. `git diff` = worktree vs index; `git diff --staged` = index vs HEAD.
- `git restore <path>` (worktree) / `git restore --staged <path>` (unstage) are the modern, scoped undo verbs; `git switch` changes branches. They replace the overloaded `git checkout`.

### The three `git reset` modes (memorize this)

`git reset [--soft|--mixed|--hard] <commit>` moves the current **branch** to `<commit>`, differing only in what else it touches:

| Mode | Moves HEAD/branch | Index | Working tree | Net effect |
|------|:-:|:-:|:-:|------------|
| `--soft` | ✅ | unchanged | unchanged | Prior changes left **staged**. Great for squashing: `git reset --soft HEAD~5 && git commit`. |
| `--mixed` *(default)* | ✅ | reset to commit | unchanged | Prior changes left **unstaged** (un-commits *and* un-stages). |
| `--hard` | ✅ | reset to commit | **reset to commit** | **⚠️ Discards** uncommitted changes; may remove untracked files in the tree. |

Two specialist modes: `--merge` and `--keep` reset while *preserving* local edits (and abort on conflict) — used to back out of a failed merge without losing work. Full treatment: [recovery.md](references/recovery.md).

> `reset` moves a branch pointer; `revert` makes a *new* commit that undoes another (safe on shared history); `restore`/`checkout` change file contents, not the branch.

### Refspecs in one line

A refspec is `[+]<src>:<dst>` mapping refs between repos. `git push origin main` ≈ `refs/heads/main:refs/heads/main`; a leading `+` forces (non-fast-forward); an empty `<src>` deletes (`git push origin :old-branch`). Fetch config like `+refs/heads/*:refs/remotes/origin/*` is why remote branches land under `origin/`. Full treatment: [refspecs-remotes.md](references/refspecs-remotes.md).

## "Oh No" — Recovery Quick Reference

Start here when something went wrong. Each row links to the deep guide. **Diagnose with `git status`, `git reflog`, and `git log --oneline --all --graph` before destructive action.**

| Situation | First move | Depth |
|-----------|-----------|-------|
| Committed to the wrong branch | `git log` note the hash → `git reset --hard HEAD~1` on wrong branch, `git cherry-pick <hash>` on right one | [recovery.md](references/recovery.md) |
| "Lost" a commit after reset/rebase | `git reflog` → find hash → `git branch rescue <hash>` or `git reset --hard <hash>` | [recovery.md](references/recovery.md) |
| Deleted a branch by mistake | `git reflog` (or `reflog show <branch>@{...}`) → `git branch <name> <hash>` | [recovery.md](references/recovery.md) |
| Dropped/lost a stash | `git fsck --no-reflogs --unreachable \| grep commit`, inspect, `git stash apply <hash>` | [recovery.md](references/recovery.md) |
| Bad merge just now | `git reset --merge ORIG_HEAD` (keeps local edits) | [recovery.md](references/recovery.md) |
| Botched rebase mid-flight | `git rebase --abort`; if finished, `git reset --hard ORIG_HEAD` | [recovery.md](references/recovery.md) |
| Amended and lost the old commit | `git reflog` → the pre-amend entry is still there | [recovery.md](references/recovery.md) |
| Undo a *pushed* commit safely | `git revert <hash>` (new inverse commit; never rewrite shared history) | [branching-merging.md](references/branching-merging.md) |
| Unstage / discard a file | `git restore --staged <f>` / `git restore <f>` | [recovery.md](references/recovery.md) |
| Detached HEAD with new commits | `git branch <name>` *before* switching away, or `git switch -c <name>` | [troubleshooting.md](references/troubleshooting.md) |

## Safety Rules (footguns)

- **Never `--force` push a shared branch.** Use `git push --force-with-lease` (refuses if the remote moved under you). See [refspecs-remotes.md](references/refspecs-remotes.md).
- **Don't rewrite published history** others have pulled. Rewrite only local/unshared commits; otherwise `revert`.
- `git reset --hard` and `git clean -fd` **destroy uncommitted/untracked work** with no reflog. Run `git stash` or `git clean -nd` (dry run) first.
- Prefer `git switch`/`git restore` over `git checkout` — narrower, less surprising.
- `git filter-repo` rewrites every commit hash (invalidates clones); `git filter-branch` is **discouraged** by upstream. See [history-rewriting.md](references/history-rewriting.md).
- After any rewrite, collaborators must re-clone or hard-reset to the new history — communicate it.

## Where to Look — Reference Map

Read the focused file for the task at hand (progressive disclosure — don't load them all):

| Reference | Covers |
|-----------|--------|
| [recovery.md](references/recovery.md) | reflog, `fsck --lost-found`, undoing reset/merge/rebase/amend, recovering commits/branches/stashes, the reset modes in depth, `ORIG_HEAD`/`MERGE_HEAD` |
| [history-rewriting.md](references/history-rewriting.md) | interactive rebase (all todo commands), `--autosquash`/`--rebase-merges`/`--update-refs`/`--onto`/`--root`, `amend`, splitting commits, `filter-repo`, why not `filter-branch` |
| [branching-merging.md](references/branching-merging.md) | merge strategies (ort/octopus/ours/subtree), `-X` options, ff control, rebase-vs-merge, `cherry-pick`, `revert` (incl. merges), `rerere` |
| [inspection.md](references/inspection.md) | `log` (formats, `--graph`, `-S`/`-G`, `-L`, `--follow`), `diff` (`..` vs `...`, `--word-diff`), `show`, `blame`, `shortlog`, `range-diff`, `describe`, `git grep` |
| [refspecs-remotes.md](references/refspecs-remotes.md) | remotes, fetch/pull/push semantics, refspecs, upstream tracking, `push.default`, `--force-with-lease`, tags, multiple remotes |
| [worktrees-stash.md](references/worktrees-stash.md) | `git worktree` (add/list/remove/prune/move/lock), `git stash` (push `-p`/`-k`/`-u`, apply vs pop, branch, create/store, internals) |
| [internals-plumbing.md](references/internals-plumbing.md) | object model, refs/packed-refs, the index, `cat-file`/`hash-object`/`rev-parse`/`rev-list`/`ls-tree`/`ls-files`/`update-ref`, packfiles, gc, `gitrevisions` syntax |
| [config-attributes-hooks.md](references/config-attributes-hooks.md) | `git config` (levels, `includeIf`), `.gitattributes` (eol/filters/diff/merge drivers), `.gitignore`, hooks, aliases |
| [advanced-features.md](references/advanced-features.md) | submodules, subtree, sparse-checkout, partial/shallow clone, bundles, notes, replace, **bisect**, backfill, commit/tag **signing** |
| [troubleshooting.md](references/troubleshooting.md) | error→cause→fix lookup: detached HEAD, unrelated histories, non-fast-forward, CRLF, dubious ownership, large files, `.gitignore` not working, wrong author |

## Common Workflows (compact)

### Undo the last commit, keep the changes
```bash
git reset --soft HEAD~1      # keep changes staged
git reset HEAD~1             # (--mixed) keep changes, unstaged
# Pushed already? Don't rewrite — invert it:
git revert HEAD              # new commit undoing the last one
```

### Clean up local commits before pushing
```bash
git rebase -i @{upstream}    # reorder/squash/fixup/reword/drop/edit
# Mark fixup commits and let git slot them automatically:
git commit --fixup=<hash> && git rebase -i --autosquash @{upstream}
```
Full todo-command reference and `--update-refs` (keeps stacked branches aligned): [history-rewriting.md](references/history-rewriting.md). For dedicated stacked-branch tooling use the **git-chain** skill; for auto-fixup use **git-absorb**.

### Find the commit that introduced a bug (bisect)
```bash
git bisect start
git bisect bad                 # current is broken
git bisect good v1.2.0         # known-good point
git bisect run ./test.sh       # automated; git checks out the culprit
git bisect reset               # restore HEAD when done
```
Details, `skip`, and custom `terms`: [advanced-features.md](references/advanced-features.md).

### Work on two branches at once (no stashing)
```bash
git worktree add ../hotfix main     # second working tree on a new path
# ...fix, commit, push from ../hotfix...
git worktree remove ../hotfix
```
Gotchas (a branch checks out in only one worktree, shared object store): [worktrees-stash.md](references/worktrees-stash.md).

### Stash, switch context, come back
```bash
git stash push -u -m "wip: parser"   # include untracked (-u)
git switch other-branch
git switch -                          # back
git stash pop                         # reapply + drop (apply keeps it)
```
Partial stashing (`-p`), keeping the index (`-k`), recovering a dropped stash: [worktrees-stash.md](references/worktrees-stash.md).

### Bring one fix to another branch
```bash
git switch release-1.x
git cherry-pick -x <hash>     # -x records "cherry picked from ..."
# Conflict? resolve, then:
git cherry-pick --continue    # or --abort / --skip
```
Ranges, picking a merge (`-m`), and `rerere` to auto-reuse resolutions: [branching-merging.md](references/branching-merging.md).

### Resolve a merge conflict
```bash
git merge feature             # conflict reported
git status                    # see "Unmerged paths"
git diff                      # ours (HEAD) vs theirs in markers <<<<<<< ======= >>>>>>>
# edit files, then:
git add <resolved> && git merge --continue
git merge --abort             # bail out entirely
```
`-X ours/theirs`, choosing a strategy, and reusing resolutions with `rerere`: [branching-merging.md](references/branching-merging.md). Backing out a *committed* merge: [recovery.md](references/recovery.md).

### Search history for where/when something changed
```bash
git log -S "functionName" --oneline      # commits that add/remove the string (pickaxe)
git log -L :funcName:file.c              # evolution of a function
git log --oneline --follow -- path       # history across renames
git blame -w -C file.c                   # who/why, ignoring whitespace & copies
```
More in [inspection.md](references/inspection.md).

## Git Version Awareness

This skill is **documented against git 2.54**, but most of it works on far older git. Features that need a specific minimum version are tagged inline as **`(git X.Y+)`**; default changes and removals are noted where they matter. When no tag is present, assume the feature is long-standing. For a consolidated lookup, see **[version-features.md](references/version-features.md)**.

High-impact cutoffs worth remembering:

| Feature | Minimum version |
|---------|-----------------|
| `git switch` / `git restore` | git 2.23+ |
| `ort` merge strategy as default | git 2.34 |
| `git rebase --update-refs` | git 2.38+ |
| `git push --force-if-includes` | git 2.30+ |
| `git config get`/`set`/`unset`/`list` subcommands | git 2.46+ |
| `git backfill` (blobless partial clones) | git 2.49+ |

Always confirm against the installed git: `git version`, then `git <cmd> --help`.

## Conventions & Notes

- Verify exact flags against the installed git (`git <cmd> --help`); flag behavior evolves across releases (see [Git Version Awareness](#git-version-awareness)).
- Prefer **non-destructive diagnosis first** (`status`, `reflog`, `log --graph`, `--dry-run`, `--no-` variants) before any command that rewrites or deletes.
- Quote/escape revisions and pathspecs in shells (`'HEAD^'`, `--` to separate paths from revs).
- When in doubt about a destructive op, create a throwaway branch or tag at the current commit first: `git branch backup-$(date +%s)`.
