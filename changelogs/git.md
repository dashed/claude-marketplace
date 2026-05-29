# Changelog - git

All notable changes to the git skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-05-29

### Added
- Initial addition to marketplace
- Advanced Git CLI mastery + recovery skill targeting git 2.54+
- SKILL.md spine (<500 lines): the object model, HEAD/index/working-tree model, the three `git reset` modes comparison table, refspecs in brief, an "Oh No" recovery quick-reference table, safety/footgun rules, compact common workflows, and a reference map routing to the detailed files
- 10 progressive-disclosure reference files:
  - `recovery.md` — reflog, `fsck --lost-found`, undoing reset/merge/rebase/amend, recovering lost commits/branches/stashes, reset modes deep-dive
  - `history-rewriting.md` — interactive rebase (all todo commands), `--autosquash`/`--rebase-merges`/`--update-refs`/`--onto`/`--root`, `commit --amend`, splitting commits, `filter-repo`, why not `filter-branch`
  - `branching-merging.md` — merge strategies (ort/octopus/ours/subtree), `-X` options, fast-forward control, rebase-vs-merge, `cherry-pick`, `revert` (incl. merges), `rerere`
  - `inspection.md` — `log` (formats, `--graph`, pickaxe `-S`/`-G`, line-log `-L`, `--follow`), `diff`, `show`, `blame`, `shortlog`, `range-diff`, `describe`, `git grep`
  - `refspecs-remotes.md` — remotes, fetch/pull/push semantics, refspecs, upstream tracking, `push.default`, `--force-with-lease`, tags, multiple remotes
  - `worktrees-stash.md` — `git worktree` (add/list/remove/prune/move/lock), `git stash` (push `-p`/`-k`/`-u`, apply vs pop, branch, create/store, internals)
  - `internals-plumbing.md` — object model, refs/packed-refs, the index, plumbing commands (`cat-file`/`hash-object`/`rev-parse`/`rev-list`/`ls-tree`/`ls-files`/`update-ref`), packfiles, gc, `gitrevisions` syntax
  - `config-attributes-hooks.md` — `git config` (levels, `includeIf`), `.gitattributes` (eol/filters/diff/merge drivers), `.gitignore`, hooks, aliases
  - `advanced-features.md` — submodules, subtree, sparse-checkout, partial/shallow clone, bundles, notes, replace, bisect, backfill, commit/tag signing
  - `troubleshooting.md` — error→cause→fix lookup (detached HEAD, unrelated histories, non-fast-forward, CRLF, dubious ownership, large files, `.gitignore` not working, wrong author)
- Explicitly defers to the `conventional-commits`, `git-chain`, `git-absorb`, and `jj` skills to avoid overlap
