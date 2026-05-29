# Git Troubleshooting

You hit an error or git is in a confusing state. This file is a fast **symptom →
cause → fix** lookup. Each entry gives the quick fix and links to the topical
reference where the full how-to lives — so look here first, then follow the link if
you need depth. Start with the [diagnostic cheat sheet](#diagnostic-cheat-sheet) to
see *what* state you're in, scan the [master lookup table](#master-lookup-table), then
jump to the detailed section for the tricky ones. Grounded against git 2.54.0.

## Table of Contents

- [Diagnostic cheat sheet](#diagnostic-cheat-sheet)
- [Master lookup table](#master-lookup-table)
- [Detached HEAD](#detached-head)
- [Refusing to merge unrelated histories](#refusing-to-merge-unrelated-histories)
- [Non-fast-forward / "Updates were rejected"](#non-fast-forward--updates-were-rejected)
- [CRLF / autocrlf line-ending churn](#crlf--autocrlf-line-ending-churn)
- [Detected dubious ownership](#detected-dubious-ownership)
- [Accidentally committed a huge file or secret](#accidentally-committed-a-huge-file-or-secret)
- [fatal: not a git repository](#fatal-not-a-git-repository)
- [Merge-conflict state confusion](#merge-conflict-state-confusion)
- [.gitignore not ignoring a file](#gitignore-not-ignoring-a-file)
- [Wrong author / email on a commit](#wrong-author--email-on-a-commit)
- [HTTP vs SSH auth & credential helpers](#http-vs-ssh-auth--credential-helpers)

---

## Diagnostic cheat sheet

Before fixing anything, find out where you are. None of these change state.

| Command | Tells you |
|---|---|
| `git status` / `git status -sb` | Branch, staged/unstaged, conflicts, ahead/behind |
| `git status -uall` | Also lists individual untracked files (not just dirs) |
| `git log --oneline --graph --all --decorate` | Shape of history, where every ref points |
| `git reflog` | Where `HEAD` has *been* — your safety net for "lost" commits |
| `git rev-parse --abbrev-ref HEAD` | Current branch name (`HEAD` if detached) |
| `git rev-parse --show-toplevel` | Worktree root (errors if you're not in a repo) |
| `git rev-parse --git-dir` | Location of the `.git` directory in use |
| `git branch -vv` | Each branch's upstream + ahead/behind |
| `git remote -v` | Remote names and URLs (spot http-vs-ssh, wrong origin) |
| `git config --show-origin --get-all <key>` | A setting's value(s) **and which file** set it |
| `git check-ignore -v <path>` | Which ignore rule (file:line:pattern) excludes a path |
| `git ls-files --error-unmatch <path>` | Whether a path is tracked (nonzero if not) |
| `git diff --check` | Whitespace errors and leftover conflict markers |
| `GIT_TRACE=1 git <cmd>` | Trace what git actually runs (deep debugging) |

---

## Master lookup table

| Symptom (message, abbreviated) | Cause | Quick fix | Deep dive |
|---|---|---|---|
| `fatal: not a git repository (or any of the parent directories)` | Not inside a worktree, or wrong `GIT_DIR` | `cd` into the repo, or `git init` | [below](#fatal-not-a-git-repository) |
| `You are in 'detached HEAD' state.` | `HEAD` points at a commit, not a branch | `git switch -c <name>` to keep work; `git switch -` to leave | [below](#detached-head) |
| `fatal: refusing to merge unrelated histories` | Two roots with no common ancestor | `git merge --allow-unrelated-histories` *(only if intended)* | [below](#refusing-to-merge-unrelated-histories) |
| `! [rejected] ... (non-fast-forward)` / `Updates were rejected because the tip of your current branch is behind` | Remote moved on; your push isn't a fast-forward | `git fetch` then `git rebase`/`git merge`; push again | [below](#non-fast-forward--updates-were-rejected) |
| `! [rejected] ... (fetch first)` | Remote has work you don't have locally | `git fetch` + integrate, then push | [below](#non-fast-forward--updates-were-rejected) |
| `! [rejected] ... (stale info)` | `--force-with-lease` saw the ref move | Re-`fetch`, review, retry the lease | [refspecs-remotes.md](refspecs-remotes.md) |
| `warning: ... LF will be replaced by CRLF` (whole files "modified") | autocrlf/eol normalization | Commit a `.gitattributes` `text=auto`; renormalize | [below](#crlf--autocrlf-line-ending-churn) |
| `fatal: detected dubious ownership in repository at '...'` | Repo owned by another user (CI/container/sudo) | `chown` it, or `git config --global --add safe.directory <path>` | [below](#detected-dubious-ownership) |
| Huge file / secret committed | Blob baked into history | If unpushed: amend/reset. If in history: rewrite | [below](#accidentally-committed-a-huge-file-or-secret) |
| `.gitignore` ignored but file still shows | File was already tracked | `git rm --cached <file>` then commit | [below](#gitignore-not-ignoring-a-file) |
| Wrong name/email on commit(s) | Bad `user.name`/`user.email` at commit time | `commit --amend --reset-author` (last); rebase (older) | [below](#wrong-author--email-on-a-commit) |
| `Authentication failed` / `Permission denied (publickey)` | Password used instead of PAT; missing/wrong SSH key | Use a PAT or SSH key; set a credential helper | [below](#http-vs-ssh-auth--credential-helpers) |
| `error: Your local changes ... would be overwritten by` | Dirty worktree blocks checkout/merge/pull | `git stash` (or commit), redo, `git stash pop` | [worktrees-stash.md](worktrees-stash.md) |
| `CONFLICT (content): Merge conflict in <file>` | Overlapping edits during merge/rebase/cherry-pick | Resolve, `git add`, `--continue`; or `--abort` | [below](#merge-conflict-state-confusion) |
| `fatal: The current branch <b> has no upstream branch` | No tracking ref set for push | `git push -u origin <b>` | [refspecs-remotes.md](refspecs-remotes.md) |
| `warning: adding embedded git repository: <path>` | A repo nested inside a repo (stray `.git`) | Remove the inner `.git`, or make it a submodule | [advanced-features.md](advanced-features.md) |
| `error: cannot pull with rebase: You have unstaged changes` | Rebase pull needs a clean tree | `git stash` (or commit) first | [worktrees-stash.md](worktrees-stash.md) |
| Lost a commit after reset/rebase/amend | Old tip is now unreferenced (not gone) | `git reflog` → `git reset`/`git switch -c` to it | [recovery.md](recovery.md) |

---

## Detached HEAD

**Symptom:** `You are in 'detached HEAD' state.` `git status` says *HEAD detached at
<sha>* instead of naming a branch.

**Why:** You checked out a commit, tag, or remote-tracking ref directly (`git checkout
<sha>`, `git checkout v1.2`, `git checkout origin/main`), or you're mid-rebase /
inside a submodule. `HEAD` points straight at a commit, so new commits belong to no
branch and become unreachable once you leave.

**Quick fix:**
```bash
# Keep the commits you made here — turn them into a branch:
git switch -c my-work

# Or you only looked around and want to go back to a branch:
git switch -            # previous branch
git switch main         # or a named one
```

**If you already left and lost commits**, they're in the reflog — recover them via
[recovery.md](recovery.md). Detached HEAD is normal during `git bisect` and inside
submodules (see [advanced-features.md](advanced-features.md)); just branch before
committing. (`git switch`/`git restore` are git 2.23+; on older git use `git checkout`.)

---

## Refusing to merge unrelated histories

**Symptom:** `fatal: refusing to merge unrelated histories`.

**Why:** The two branches share **no common ancestor** (two independent root commits).
This is a safety check — it almost always means a mistake: you `git init`'d a new repo
and then added a remote that already had history, cloned the wrong URL, or are merging
two genuinely separate projects.

**Quick fix:**
```bash
# FIRST confirm it's intentional — are you merging the repo you think you are?
git log --oneline -1 HEAD
git log --oneline -1 MERGE_HEAD 2>/dev/null || git log --oneline -1 origin/main

# Only if you really want to stitch unrelated histories together:
git merge --allow-unrelated-histories origin/main
git pull --allow-unrelated-histories origin main   # same flag works on pull
```

**Footgun:** if this appeared right after `git init` + `git remote add` + `git pull`,
you probably want to **clone** the remote instead and move your files in — overriding
the check glues two unrelated trees together permanently.

---

## Non-fast-forward / "Updates were rejected"

**Symptom:**
```
 ! [rejected]        main -> main (non-fast-forward)
error: failed to push some refs to '...'
hint: Updates were rejected because the remote contains work that you do
hint: not have locally. ... use 'git pull' before pushing again.
```

**Why:** Someone pushed to the remote after you last fetched, so your branch and the
remote branch have diverged — your push isn't a fast-forward.

**Quick fix — integrate, don't bulldoze:**
```bash
git fetch origin
git rebase origin/main      # replay your commits on top (linear history)
#   …resolve any conflicts, then:
git push

# Prefer a merge instead of a rebase? (keeps a merge commit)
git pull --no-rebase        # then push
```

**⚠️ Destructive:** `git push --force` overwrites whatever's on the remote and can
erase a teammate's commits. If you *must* force (e.g. after an intentional rebase of
your own branch), use the safe variant that refuses when the remote moved unexpectedly:
```bash
git push --force-with-lease
```
The `(fetch first)` and `(stale info)` reject reasons are the same family — fetch and
re-evaluate. Force semantics and `--force-with-lease` vs `--force` are covered in
[refspecs-remotes.md](refspecs-remotes.md).

---

## CRLF / autocrlf line-ending churn

**Symptom:** `git diff` shows an entire file changed though you edited one line;
`warning: in the working copy of '<file>', LF will be replaced by CRLF the next time
Git touches it`; cross-platform teammates fight over line endings.

**Why:** Line-ending conversion is driven by `core.autocrlf`/`core.eol` and/or the
`text` attribute. When settings differ between machines (or aren't committed), CRLF↔LF
flips make whole files look modified.

**Quick fix — make the policy part of the repo, not per-machine config:**
```bash
# Commit a .gitattributes so everyone normalizes identically:
printf '* text=auto\n' >> .gitattributes
git add .gitattributes

# Renormalize the existing tree to the policy in one commit:
git add --renormalize .
git commit -m "Normalize line endings"
```
`core.autocrlf=true` (Windows checkout-CRLF/commit-LF) or `input` (commit-LF only) is
a per-user fallback, but a committed `.gitattributes` is the real fix because it's
shared. Mark binaries explicitly (`*.png binary`) so they're never converted. Full
attribute mechanics — `text`, `eol`, `working-tree-encoding`, custom filters — are in
[config-attributes-hooks.md](config-attributes-hooks.md).

---

## Detected dubious ownership

**Symptom:**
```
fatal: detected dubious ownership in repository at '/path/to/repo'
To add an exception for this directory, call:
	git config --global --add safe.directory /path/to/repo
```

**Why:** The repository's files are owned by a **different user** than the one running
git. Git refuses to read such a repo's config (let alone run its hooks) to prevent a
malicious checkout from hijacking your session. Common in CI runners, Docker
containers (host bind-mounts), and when a repo was created with `sudo`. (This
dubious-ownership check and `safe.directory` arrived as a security fix in git 2.35.2,
backported to 2.30.3 / 2.31.2 / 2.32.1 / 2.33.2 / 2.34.2 — CVE-2022-24765.)

**Quick fix:**
```bash
# Best: fix ownership so it actually belongs to you:
sudo chown -R "$(id -u):$(id -g)" /path/to/repo

# Or tell git this specific path is trusted (it's "protected" config — global/system):
git config --global --add safe.directory /path/to/repo

# Containers/CI where the path is known-safe and disposable (blunt; use sparingly):
git config --global --add safe.directory '*'    # trusts ALL repos
```
`safe.directory` is honored only in protected (global/system) config, never from a
repo's own config. `<dir>/*` trusts everything under a directory. The `*` wildcard
(trust everything) is git 2.36+. See
[config-attributes-hooks.md](config-attributes-hooks.md) for config scopes.

---

## Accidentally committed a huge file or secret

**Symptom:** A large binary or a credential is now in a commit; remote rejects the
push for size, or a secret is exposed.

**Quick fix depends on whether it left your machine:**

```bash
# (A) Not pushed yet, and it's the LAST commit — drop it from that commit:
git rm --cached path/to/secret            # un-stage from tracking
echo 'path/to/secret' >> .gitignore
git commit --amend --no-edit              # rewrites only the last (local) commit

# (B) Not pushed, a few commits back — un-commit back to before it, recommit cleanly:
git reset --soft <commit-before-the-mistake>   # keeps your changes staged
#   …then drop the file as in (A) and recommit.
```

**If it's already in pushed history**, amending isn't enough — the blob lives in old
commits. You must **rewrite history** with `git filter-repo` (the recommended,
non-core tool) and force-push; see [history-rewriting.md](history-rewriting.md).

**⚠️ A leaked secret is compromised the moment it's pushed** — rewriting history does
**not** un-leak it. Rotate/revoke the credential immediately, then scrub history.

To fold small corrections into the *right* earlier commit on a feature branch (instead
of a messy "fix" commit), use the **git-absorb** skill.

---

## fatal: not a git repository

**Symptom:** `fatal: not a git repository (or any of the parent directories): .git`.

**Why:** Your current directory (and its parents) have no `.git`, or a `GIT_DIR` /
`--git-dir` points somewhere wrong, or you're standing above the repo root.

**Quick fix:**
```bash
git rev-parse --show-toplevel     # where (if anywhere) is the repo root?
cd /path/to/the/repo              # …then re-run your command

git init                          # only if this dir SHOULD be a new repo
echo "$GIT_DIR"                   # is a stale GIT_DIR overriding discovery?
unset GIT_DIR                     # clear a bad override
```
If a nested/embedded repo is involved (a `.git` inside another repo), see submodules
in [advanced-features.md](advanced-features.md).

---

## Merge-conflict state confusion

**Symptom:** `git status` shows *Unmerged paths* and *both modified*; you're unsure
what `ours`/`theirs` mean or how to get out.

**Why:** A merge/rebase/cherry-pick hit overlapping edits and paused, leaving conflict
markers (`<<<<<<<`, `=======`, `>>>>>>>`) and an in-progress operation
(`MERGE_HEAD`/`REBASE_HEAD` present).

**Quick fix:**
```bash
git status                         # list unmerged files
git diff --check                   # find leftover conflict markers

# Take one whole side for a file (know which is which — see note below):
git checkout --ours  path          # keep "our" version
git checkout --theirs path         # keep "their" version

# After hand-resolving, stage and continue the operation:
git add path
git merge --continue               # or: git rebase --continue / cherry-pick --continue

# Bail out entirely and return to the pre-operation state:
git merge --abort                  # or: git rebase --abort / cherry-pick --abort
```

**Footgun — `ours`/`theirs` flip during rebase.** In a `merge`, *ours* = the branch
you're on, *theirs* = the branch being merged in. In a `rebase`, it's **inverted**:
*ours* = the upstream you're replaying onto, *theirs* = your commit being replayed.

The interactive resolution workflow and `rerere` live in
[branching-merging.md](branching-merging.md); recovering after a bad `--abort`/reset is
in [recovery.md](recovery.md).

---

## .gitignore not ignoring a file

**Symptom:** A path is listed in `.gitignore`, yet `git status` still shows it (or it
keeps getting committed).

**Why (most common):** `.gitignore` only affects **untracked** files. If the file was
committed before you ignored it, git keeps tracking it. Less often: a broader negation
(`!`) rule, or precedence between `.gitignore`, `.git/info/exclude`, and
`core.excludesFile`, re-includes it.

**Quick fix:**
```bash
# Stop tracking it but keep the local copy, then commit the removal:
git rm --cached path/to/file          # use -r for a directory
git commit -m "Stop tracking path/to/file"

# Figure out exactly which rule is (or isn't) matching:
git check-ignore -v path/to/file      # prints  <source>:<line>:<pattern>  path
```
If `check-ignore -v` prints nothing, no rule matches (the file is shown because it's
*tracked*, per above). Pattern syntax, precedence, and negation are detailed in
[config-attributes-hooks.md](config-attributes-hooks.md).

---

## Wrong author / email on a commit

**Symptom:** Commits show the wrong name/email (e.g. a default identity, or a work
email on a personal repo).

**Why:** `user.name`/`user.email` were unset or wrong when you committed. Fix the
config first so future commits are correct, then repair the existing ones.

**Quick fix:**
```bash
# 1) Correct identity going forward (per-repo here; drop --local for global):
git config --local user.name  "Your Name"
git config --local user.email "you@example.com"

# 2a) Just the LAST commit — adopt the (now-correct) committer identity:
git commit --amend --reset-author --no-edit
#     …or set an explicit author without changing config:
git commit --amend --author="Your Name <you@example.com>" --no-edit

# 2b) Several recent commits — rebase and re-stamp each one:
git rebase -i <commit-before-the-bad-ones>
#     mark the offenders 'edit', then at each stop:
git commit --amend --reset-author --no-edit && git rebase --continue
#     …or non-interactively across a range:
git rebase <base> --exec 'git commit --amend --reset-author --no-edit'
```

**⚠️ Rewrites shared history.** If these commits were already pushed, you'll need a
force-push (`--force-with-lease`) and coordination — see
[history-rewriting.md](history-rewriting.md). For bulk author rewrites across an entire
repo, `git filter-repo --mailmap` is the right tool (also in history-rewriting.md).

---

## HTTP vs SSH auth & credential helpers

**Symptom:**
- HTTPS: `remote: Support for password authentication was removed.` /
  `fatal: Authentication failed for 'https://...'`
- SSH: `git@github.com: Permission denied (publickey).` /
  `fatal: Could not read from remote repository.`

**Why:** Over **HTTPS**, hosts no longer accept account passwords — you need a
**personal access token (PAT)** (or OAuth), and without a credential helper git
re-prompts every time. Over **SSH**, the host can't match your key (no key loaded,
wrong key, or key not added to the account).

**Diagnose which transport you're on:**
```bash
git remote -v                     # https://...  vs  git@host:...
ssh -T git@github.com             # SSH: should greet you by username
```

**Quick fix — HTTPS:** authenticate with a PAT (paste it at the password prompt) and
cache it so you're not asked again:
```bash
git config --global credential.helper cache          # in-memory, short-lived
git config --global credential.helper store          # plaintext on disk (less safe)
# Prefer a secure OS keychain helper where available:
#   macOS:   git config --global credential.helper osxkeychain
#   Windows: git config --global credential.helper manager
#   Linux:   git config --global credential.helper libsecret
```

**Quick fix — SSH:** ensure a key exists, is loaded, and is registered with the host:
```bash
ssh-add -l                        # is a key loaded in the agent?
ssh-add ~/.ssh/id_ed25519         # load it if not
# …add the matching ~/.ssh/id_ed25519.pub to your account on the host, then test:
ssh -T git@github.com
```

**Switch transports** if one is blocked (e.g. corporate proxy eats SSH):
```bash
git remote set-url origin https://github.com/me/repo.git   # SSH -> HTTPS
git remote set-url origin git@github.com:me/repo.git       # HTTPS -> SSH
```
Remote URL management lives in [refspecs-remotes.md](refspecs-remotes.md). See
`gitcredentials(7)` for the full helper list.

---

## See also

- [SKILL.md](../SKILL.md) — skill overview and index
- [recovery.md](recovery.md) — reflog, recovering lost commits, undoing reset/merge/rebase
- [refspecs-remotes.md](refspecs-remotes.md) — push/fetch, refspecs, `--force-with-lease`
- [history-rewriting.md](history-rewriting.md) — rewrite/scrub history, `filter-repo`
- [branching-merging.md](branching-merging.md) — conflict resolution workflow, `rerere`
- [config-attributes-hooks.md](config-attributes-hooks.md) — config scopes, attributes, ignore rules
- [worktrees-stash.md](worktrees-stash.md) — stashing dirty changes out of the way
- **git-absorb** skill — fold fixes into the right earlier commit
