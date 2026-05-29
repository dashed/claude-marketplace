# Git Feature → Minimum Version

A consolidated lookup of **which git version introduced a feature** this skill documents, so you know what works on an older (or newer) git. Use it to answer "is my git new enough for X?" and "what do I need to upgrade to?"

**How to read this:**
- Versions are when a feature was **introduced** (sometimes experimental first; defaults/stabilization may come later — those are noted).
- Features **not listed here are long-standing** (predate git 2.0 / ~2014) and are safe to assume everywhere — this file deliberately omits them to stay signal-rich.
- A few fixes ship in **point releases** (e.g. `2.35.2`), not a `.0` — noted inline.
- This skill is documented against **git 2.54**. Always confirm on the running system: `git version`, then `git <cmd> --help`.

All versions below were verified against `Documentation/RelNotes/<version>.adoc` in the git source tree.

## Contents

- [Git 2.40 and newer](#git-240-and-newer)
- [Git 2.30 to 2.39](#git-230-to-239)
- [Git 2.20 to 2.29](#git-220-to-229)
- [Git 2.9 to 2.19](#git-29-to-219)
- [Removed, deprecated, and changed defaults](#removed-deprecated-and-changed-defaults)

## Git 2.40 and newer

| Min version | Feature | Area |
|---|---|---|
| 2.52 | `git sparse-checkout clean` (remove files outside the sparse set) | sparse-checkout |
| 2.51 | `git stash export` / `git stash import` (serialize stashes to/from a commit) | stash |
| 2.50 | `git fast-export`/`fast-import --signed-commits` (round-trip signatures; experimental) | history rewriting |
| 2.49 | `git backfill` (bulk-fetch missing blobs in a blobless partial clone) | partial clone |
| 2.48 | `git worktree --relative-paths`, `worktree.useRelativePaths` (relocatable worktrees) | worktree |
| 2.46 | `git config get`/`set`/`unset`/`list` subcommands | config |
| 2.45 | reftable ref backend — `git init --ref-format=reftable` | internals / refs |
| 2.45 | `git pack-refs --auto` | internals |
| 2.45 | `git cherry-pick --empty=stop\|drop\|keep` | cherry-pick |
| 2.44 | `fetch.all` config | remotes |
| 2.42 | `git cat-file -Z` (NUL-delimited batch I/O) | plumbing |
| 2.42 | `git worktree add --orphan` | worktree |
| 2.41 | `git push --branches` (alias for `--all`) | remotes |

## Git 2.30 to 2.39

| Min version | Feature | Area |
|---|---|---|
| 2.38 | `git rebase --update-refs`, `rebase.updateRefs` (retarget stacked branches) | rebase |
| 2.38 | `git ls-files --format` | plumbing |
| 2.37 | `git revert --reference`, `revert.reference` | revert |
| 2.37 | cruft packs — `git gc`/`repack --cruft` | internals |
| 2.36 | `git log`/`show --remerge-diff` | inspection |
| 2.36 | `git cat-file --batch-command` | plumbing |
| 2.36 | `git ls-tree --format` | plumbing |
| 2.36 | `includeIf "hasconfig:remote.*.url"` conditional config | config |
| 2.36 | `git worktree list -z` (NUL output) | worktree |
| 2.36 | `safe.directory = *` (trust-all wildcard) | config / safety |
| 2.35 | `merge.conflictStyle = zdiff3` | merge |
| 2.35 | `git stash -S` / `--staged` (stash only staged changes) | stash |
| 2.34 | **`ort` becomes the default merge strategy** (was `recursive`) | merge |
| 2.34 | SSH commit/tag signing — `gpg.format = ssh` | signing |
| 2.32 | `git commit --fixup=amend:/reword:` & rebase `fixup -C`/`-c` | rebase |
| 2.32 | `git repack --geometric` | internals |
| 2.32 | `git stash show -u`/`--include-untracked` | stash |
| 2.32 | partial clone `--filter=object:type=…` | partial clone |
| 2.31 | `git worktree list -v` + `prunable` annotation | worktree |
| 2.31 | `git rev-list --disk-usage` | plumbing |
| 2.30 | `git push --force-if-includes` (safer force-push) | remotes |
| 2.30 | `clone.defaultRemoteName` | remotes |
| 2.30 | `git diff --merge-base` | inspection |

## Git 2.20 to 2.29

| Min version | Feature | Area |
|---|---|---|
| 2.29 | SHA-256 object format (experimental) — `git init --object-format=sha256` | internals |
| 2.29 | negative refspecs (`^refs/…`) for fetch/push | remotes |
| 2.29 | `git worktree repair` | worktree |
| 2.29 | `git bisect --first-parent` | bisect |
| 2.29 | `git maintenance` (built out further in 2.30–2.31) | internals |
| 2.29 | `git shortlog --group=` (trailer:/format:) | inspection |
| 2.25 | `git sparse-checkout` command + cone mode | sparse-checkout |
| 2.25 | `git submodule set-url` | submodules |
| 2.25 | `git log --pretty=reference` | inspection |
| 2.24 | partial clone `--filter=combine:` | partial clone |
| 2.24 | `git rebase --keep-base` | rebase |
| 2.24 | `pre-merge-commit` hook | hooks |
| 2.24 | `git fetch --set-upstream` | remotes |
| 2.23 | `git switch` / `git restore` (safer than `git checkout`) | core |
| 2.23 | `includeIf "onbranch:…"` conditional config | config |
| 2.23 | `git blame --ignore-rev` / `--ignore-revs-file` | inspection |
| 2.22 | `git submodule set-branch` | submodules |
| 2.21 | `git log --date=human` | inspection |
| 2.20 | `git rebase -i` `break` todo command | rebase |
| 2.20 | partial clone `--filter=tree:0` | partial clone |
| 2.20 | per-worktree config (`extensions.worktreeConfig`, `git config --worktree`) | worktree / config |

## Git 2.9 to 2.19

| Min version | Feature | Area |
|---|---|---|
| 2.19 | `git range-diff` | inspection |
| 2.19 | partial clone `--filter` (experimental) | partial clone |
| 2.18 | `git rebase --rebase-merges` (replaced `--preserve-merges`) | rebase |
| 2.18 | `working-tree-encoding` attribute | attributes |
| 2.17 | `git worktree move` / `remove` | worktree |
| 2.17 | `git fetch --prune-tags` | remotes |
| 2.13 | `git stash push` (replaced `git stash save`) | stash |
| 2.9 | `core.hooksPath` | hooks |

## Removed, deprecated, and changed defaults

These matter most when a script or habit assumes old behavior — or when you read older docs.

| Version | Change |
|---|---|
| 2.34 | **Default change:** `ort` replaced `recursive` as the default merge strategy |
| 2.50 | **Removed:** the `recursive` merge backend (superseded by `ort`; still accepted as a synonym) |
| 2.46 | **Deprecated:** `git config` dashed mode flags (`--get`/`--add`/`--unset`/…) → use the `get`/`set`/`unset`/`list` subcommands |
| 2.45 | **Deprecated:** `git cherry-pick --keep-redundant-commits` → use `--empty=keep` |
| 2.37 | **Deprecated:** non-cone-mode `git sparse-checkout` → use cone mode |
| 2.16 | **Deprecated:** `git stash save` → use `git stash push` |
| 2.15 | **Removed:** `git branch --set-upstream <branch> <upstream>` positional form → use `--set-upstream-to` |

> Note on `safe.directory`: the dubious-ownership check and `safe.directory` config arrived as the **CVE-2022-24765** security fix in **2.35.2**, backported to point releases of 2.30–2.34 (e.g. 2.30.3). The `*` trust-all value is **2.36+**. See [troubleshooting.md](troubleshooting.md).
