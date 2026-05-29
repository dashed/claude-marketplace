# Advanced Git Features

The big, less-frequently-used tools: composing repositories (submodules, subtree),
shrinking what you download or check out (sparse-checkout, partial clone, shallow
clone, backfill), moving history without a server (bundle), annotating and rewriting
the object graph non-destructively (notes, replace), hunting bugs (bisect), and
cryptographically signing your work (GPG/SSH). Reach here when a plain clone/commit
isn't enough — a giant monorepo, an offline transfer, a regression hunt, or a
signing requirement. Grounded against git 2.54.0.

> For *removing* a big file or secret from history, this file is the wrong tool —
> see [history-rewriting.md](history-rewriting.md). For recovering after a botched
> operation, see [recovery.md](recovery.md).

## Table of Contents

- [Submodules](#submodules)
- [Subtree (contrib, not core)](#subtree-contrib-not-core)
- [Sparse-checkout (cone mode)](#sparse-checkout-cone-mode)
- [Partial clone](#partial-clone)
- [Shallow clone](#shallow-clone)
- [Bundle (offline transfer & backup)](#bundle-offline-transfer--backup)
- [Notes](#notes)
- [Replace & grafts](#replace--grafts)
- [Bisect (binary-search a bug)](#bisect-binary-search-a-bug)
- [Backfill (for blobless partial clones)](#backfill-for-blobless-partial-clones)
- [Signing commits & tags (GPG / SSH)](#signing-commits--tags-gpg--ssh)
- [Putting it together for large repos](#putting-it-together-for-large-repos)

---

## Submodules

A submodule is another repository pinned at a specific commit inside your tree. The
superproject records the submodule's URL in a tracked `.gitmodules` file and the
pinned commit as a special "gitlink" entry (mode `160000`) in the index.

```bash
# Add a submodule (records URL in .gitmodules, clones into ./libs/foo, stages gitlink)
git submodule add https://example.com/foo.git libs/foo

# Clone a superproject AND populate every submodule in one step:
git clone --recurse-submodules https://example.com/super.git

# Already cloned without submodules? Initialize + fetch + checkout them all:
git submodule update --init --recursive

# See state: prefix '-'=uninitialized, '+'=checked-out commit ≠ recorded, 'U'=conflicts
git submodule status --recursive

# Run a command in each checked-out submodule (vars: $name $sm_path $sha1 $toplevel)
git submodule foreach 'git switch main && git pull'

# Move submodules to a new upstream commit (their remote tip), then commit the bump:
git submodule update --remote libs/foo
git add libs/foo && git commit -m "Bump libs/foo"

# Point a submodule at a new URL (updates .gitmodules + syncs .git/config):
git submodule set-url libs/foo https://new.example.com/foo.git   # set-url: git 2.25+
git submodule set-branch --branch release libs/foo   # set-branch: git 2.22+ (track a branch for --remote)

# After upstream URL changes, push the new URLs into your local .git/config:
git submodule sync --recursive
```

| Command | What it does | Notes |
|---|---|---|
| `submodule add <url> [<path>]` | Clone + register a new submodule | Writes `.gitmodules`; commit it |
| `submodule update --init --recursive` | Populate recorded submodules | The everyday "make it work" command |
| `submodule update --remote` | Advance to submodule's remote tip | Fetches first unless `-N`/`--no-fetch` |
| `submodule status [--recursive]` | Show pinned vs checked-out SHA | `+`/`-`/`U` prefixes flag drift |
| `submodule foreach [--recursive] <cmd>` | Run a shell command in each | `||:` to keep going on error |
| `submodule sync [--recursive]` | Copy `.gitmodules` URLs → `.git/config` | Run after upstream URL change |
| `submodule deinit -f <path>` | Remove working tree, unregister | Keeps the gitlink in the index |
| `submodule absorbgitdirs` | Move embedded `.git` into `$GIT_DIR/modules` | Modernizes old-style submodules |

**Updating procedures:** `git submodule update` defaults to `checkout` (detached
`HEAD` at the recorded commit). `--rebase` / `--merge` integrate instead and leave
`HEAD` on a branch. A `submodule.<name>.update` value of `!command` is **not** honored
from `.gitmodules` or the command line — only from `.git/config` — for security.

**Footguns:**
- A submodule sits on a **detached HEAD** after `update`. Commit there and you'll
  lose it on the next update unless you `git switch -c` a branch first. (See detached
  HEAD in [troubleshooting.md](troubleshooting.md).)
- To *remove* a submodule, use `git rm <path>` (stages removal + edits `.gitmodules`).
  `deinit` only un-populates it; it does not stop tracking it.
- Most commands ignore submodules unless told otherwise. Set `submodule.recurse=true`
  to default `checkout/fetch/pull/push/grep/...` to `--recurse-submodules`. Note
  `clone` and `ls-files` do **not** honor it; `git remote update` lacks a
  `--no-recurse-submodules`, so override with `git -c submodule.recurse=0 ...`.
- Old clones may have the submodule's `.git` *inside* the submodule. `git submodule
  absorbgitdirs` relocates it under `$GIT_DIR/modules/` (recursive by default).

See `gitsubmodules(7)` and `gitmodules(5)` for the full data model.

---

## Subtree (contrib, not core)

**⚠️ Not core git:** `git subtree` ships in `contrib/` and is not guaranteed to be
installed (`git subtree --help` to check; on some distros it's a separate package).
Unlike submodules, a subtree is just a subdirectory — consumers of your repo need
**no** special commands and there is no `.gitmodules` or gitlink. The cost is that
the subproject's history is vendored into yours.

```bash
# Vendor an external project into ./vendor/lib, squashing its history to one commit:
git subtree add --prefix=vendor/lib https://example.com/lib.git main --squash

# Pull upstream changes into the subtree later:
git subtree pull --prefix=vendor/lib https://example.com/lib.git main --squash

# Extract your changes to ./vendor/lib back out as standalone history, then push:
git subtree push --prefix=vendor/lib https://example.com/lib.git main
```

| Command | What it does |
|---|---|
| `subtree add -P <prefix> <repo> <ref> [--squash]` | Import a subproject into `<prefix>/` |
| `subtree pull -P <prefix> <repo> <ref> [--squash]` | Merge upstream changes in |
| `subtree push -P <prefix> <repo> <refspec>` | `split` + push your subtree changes out |
| `subtree merge -P <prefix> <local-commit> [--squash]` | Merge a local commit into the subtree |
| `subtree split -P <prefix> [-b <branch>]` | Synthesize standalone history for the subtree |

`-P`/`--prefix` is mandatory for every command. `--squash` keeps your log clean by
collapsing imported history into one commit (recommended); use it consistently across
`add`/`merge`/`pull` and `split --rejoin`. `-S[<keyid>]`/`--gpg-sign` signs the
generated commits.

**Submodule vs subtree:** submodules keep histories separate and pin exact commits
(good for large, independently versioned deps); subtrees embed a copy (good when
consumers must "just clone and build" with zero extra steps).

---

## Sparse-checkout (cone mode)

Sparse-checkout populates only a *subset* of tracked files in the working tree while
keeping the full repo. It uses the skip-worktree bit; absent files are simply ignored.
Ideal for a monorepo where you only need a few directories. (The `git sparse-checkout`
command — cone mode included — is git 2.25+.)

```bash
# Restrict the working tree to two directory cones (cone mode is the default):
git sparse-checkout set apps/web libs/ui

# Add another directory to the active set:
git sparse-checkout add libs/api

# Show the recursive cone directories currently selected:
git sparse-checkout list

# Re-apply patterns after a merge/rebase materialized extra files:
git sparse-checkout reapply

# Go back to a full checkout (clears patterns, keeps the setting off):
git sparse-checkout disable
```

**Cone mode** (default) accepts directories: for each one, all files under it plus
all files directly under its parent directories (and the toplevel) are included. It
is fast (hash-based matching) and required for `--sparse-index`.

```bash
# A maximally lean checkout: only toplevel files, then grow as needed:
git clone --filter=blob:none --sparse https://example.com/mono.git
cd mono
git sparse-checkout set services/payments

# Shrink the on-disk index to match the cone (experimental but big speedup):
git sparse-checkout set --sparse-index services/payments
```

| Subcommand | Purpose | Notes |
|---|---|---|
| `set <dirs…>` | Define the cone (replaces current) | `--stdin`, `--[no-]cone`, `--[no-]sparse-index` |
| `add <dirs…>` | Extend the cone | No `remove`; re-`set` to shrink |
| `list` | Show selected cone directories | |
| `reapply` | Re-enforce sparsity on the worktree | Use after conflicts left files behind |
| `disable` | Restore full working tree | Turns off `core.sparseCheckout` |
| `clean [-f]` | Remove stray files outside the cone (git 2.52+) | Cone mode only; `--dry-run` to preview |
| `init` | **Deprecated** alias for `set` (no paths) | May be removed; use `set` |

**Footguns:**
- `--no-cone` (full gitignore-style patterns) is **deprecated** (since git 2.37): O(N×M) matching,
  no `--sparse-index`, and easy to misfire with an unquoted glob. Stay in cone mode.
- Sparse-checkout does **not** auto-initialize or deinit submodules; manage those
  separately with `git submodule init/deinit`.
- `git commit -a` and branch switches won't touch paths outside the cone — by design,
  but surprising if you expected a deletion to be recorded.

---

## Partial clone

A partial clone omits some objects at clone time and lazily fetches them on demand
from the "promisor" remote. This is the modern way to clone a huge repo fast — usually
preferable to a shallow clone because history stays intact. (Partial clone `--filter`
is git 2.19+.)

```bash
# Blobless: download all commits + trees, but no file contents until needed.
git clone --filter=blob:none https://example.com/big.git

# Treeless: even leaner — omit trees too (great for CI that only builds a tip).
git clone --filter=tree:0 https://example.com/big.git

# Omit only large blobs (keep small files local):
git clone --filter=blob:limit=1m https://example.com/big.git
```

| Filter spec | Omits | Typical use |
|---|---|---|
| `blob:none` | All file contents (blobs) | Dev clone; blobs fetched on checkout/diff |
| `tree:0` | All blobs **and** trees | CI / shallow exploration of a tip (git 2.20+) |
| `blob:limit=<n>[kmg]` | Blobs ≥ `<n>` bytes | Keep small files, defer big assets |
| `object:type=(tag\|commit\|tree\|blob)` | All objects of that type | Niche analysis (git 2.32+) |
| `sparse:oid=<blob-ish>` | Per a sparse-checkout spec blob | Pair with sparse-checkout |
| `combine:<f1>+<f2>` | Apply multiple filters | e.g. `combine:tree:0+blob:none` (git 2.24+) |

After cloning, git sets `remote.origin.promisor=true` and records the filter in
`remote.origin.partialclonefilter`; `extensions.partialClone` names the promisor
remote. Missing objects are fetched automatically when an operation needs them —
which is why `git blame`/`git log -p` over deep history can become **slow** on a
blobless clone (one request per blob). Mitigate with [backfill](#backfill-for-blobless-partial-clones)
or pair with [sparse-checkout](#sparse-checkout-cone-mode).

**Footgun:** a partial clone is tied to a reachable promisor remote. If that remote
disappears, on-demand fetches fail and the repo can't fully materialize.

---

## Shallow clone

A shallow clone truncates history to a fixed depth. Smaller than a full clone, but
the missing ancestry breaks merge-base, blame across the cutoff, and some pushes.
For most "I just want it small" cases, prefer a **partial clone** instead.

```bash
# Only the most recent commit of the default branch:
git clone --depth 1 https://example.com/repo.git

# History after a date, or excluding everything reachable from a ref:
git clone --shallow-since="2024-01-01" https://example.com/repo.git
git clone --shallow-exclude=v1.0 https://example.com/repo.git

# Deepen an existing shallow clone by N more commits from the current boundary:
git fetch --deepen 50

# Set absolute depth from each branch tip:
git fetch --depth 100

# Turn a shallow clone into a complete one:
git fetch --unshallow
```

| Option (clone/fetch) | Effect |
|---|---|
| `--depth <n>` | Keep `<n>` commits from each tip; clone implies `--single-branch` |
| `--shallow-since=<date>` | Keep history after `<date>` |
| `--shallow-exclude=<ref>` | Exclude commits reachable from `<ref>` (repeatable) |
| `--deepen=<n>` (fetch) | Extend `<n>` commits past the current shallow boundary |
| `--unshallow` (fetch) | Fetch the rest; remove all shallow limitations |
| `--update-shallow` (fetch) | Accept refs that need updating `.git/shallow` |

`--depth` on clone implies `--single-branch`; add `--no-single-branch` to get tips of
all branches at that depth. Shallow-clone submodules with `--shallow-submodules`.

---

## Bundle (offline transfer & backup)

A bundle is a single file holding refs + objects — a repo you can email, burn to disc,
or `scp`. You can `clone`/`fetch`/`ls-remote` from a bundle as if it were a remote.
**There is no `push` into a bundle.**

```bash
# Full backup of every ref into one file:
git bundle create backup.bundle --all

# Bootstrap an offline machine: clone straight from the bundle:
git clone backup.bundle myrepo

# Incremental: only what's new since a known tag/commit (a "thin pack"):
git bundle create update.bundle lastsync..main
git tag -f lastsync main          # remember the new cutoff for next time

# On the receiving repo, fetch from the transferred file:
git fetch ../update.bundle main:refs/remotes/origin/main

# Check a bundle applies cleanly (lists any missing prerequisite commits):
git bundle verify update.bundle

# See what refs a bundle offers:
git bundle list-heads backup.bundle
```

| Subcommand | What it does |
|---|---|
| `create <file> <rev-list-args>` | Build a bundle (`--all`, ranges, `--since`, `-<n>`) |
| `verify <file>` | Validate format + report missing prerequisites |
| `list-heads <file> [<ref>…]` | List refs contained in the bundle |
| `unbundle <file>` | Plumbing: unpack objects (called by `git fetch`) |

A range like `old..new` produces a bundle that **requires** `old` to already exist in
the destination (smaller, but not self-contained); a single rev `new` is
self-contained and clonable anywhere. **Note:** bundles carry only refs and reachable
commits — never the index, working tree, stash, config, or hooks.

---

## Notes

Notes attach metadata to an existing object **without changing it** (so the SHA is
untouched). Stored on their own ref — `refs/notes/commits` by default — and shown
under the commit message in `git log`.

```bash
# Annotate a commit (defaults to HEAD); -f to overwrite an existing note:
git notes add -m "Reviewed-by: Dana <dana@x.io>" 1a2b3c4

# Append to an existing note (adds a blank-line separator):
git notes append -m "Also: backport to 2.x" 1a2b3c4

# Read / list:
git notes show 1a2b3c4
git notes list

# Use a separate namespace (e.g. CI results) instead of refs/notes/commits:
git notes --ref=ci add -m "build: green" HEAD

# Copy a note from one commit to another (handy after a rewrite):
git notes copy <from> <to>
```

**Notes are not pushed or fetched by default** — this trips everyone up. Move them
explicitly:

```bash
git push origin refs/notes/commits
git fetch origin refs/notes/commits:refs/notes/commits
# Or make it automatic by adding a fetch refspec:
git config --add remote.origin.fetch '+refs/notes/*:refs/notes/*'
```

| Action | Command |
|---|---|
| Add / overwrite | `git notes add [-f] [-m <msg> \| -F <file> \| -C <obj>] [<obj>]` |
| Append | `git notes append -m <msg> [<obj>]` |
| Show / list | `git notes show [<obj>]` · `git notes list` |
| Copy / remove | `git notes copy <from> <to>` · `git notes remove [<obj>]` |
| Merge namespaces | `git notes merge -s <strategy> <ref>` |
| Pick namespace | `--ref=<name>` (or `core.notesRef` / `GIT_NOTES_REF`) |

Merge strategies for `git notes merge`: `manual` (default, resolve in
`.git/NOTES_MERGE_WORKTREE` then `--commit`/`--abort`), `ours`, `theirs`, `union`,
`cat_sort_uniq`. To surface extra namespaces in `git log`, set `notes.displayRef`
(e.g. `refs/notes/*`). To carry notes across `rebase`/`amend`, configure
`notes.rewriteRef`.

---

## Replace & grafts

`git replace` creates a ref under `refs/replace/` that transparently swaps one object
for another at read time — history *looks* edited without rewriting any SHAs. Most
commands honor it; reachability operations (prune, pack transfer, fsck) do not.

```bash
# Splice history: make an old "root" commit appear to have a parent (graft):
git replace --graft <commit> <new-parent>

# Replace one object with another of the same type (use -f to overwrite):
git replace <object> <replacement>

# Hand-edit an object's content in your editor:
git replace --edit <object>

# List / delete replacements:
git replace -l
git replace -d <object>

# Run a command ignoring all replacements (also: GIT_NO_REPLACE_OBJECTS=1):
git --no-replace-objects log
```

| Option | Effect |
|---|---|
| `<object> <replacement>` | Replace one object with another (same type unless `-f`) |
| `--graft <commit> [<parent>…]` | Synthesize a commit with new parents (reparent/splice) |
| `--edit <object>` | Edit object content interactively, replace with the result |
| `-d` / `-l [<pattern>]` | Delete / list replace refs (`--format=short\|medium\|long`) |
| `--convert-graft-file` | Migrate the deprecated `$GIT_DIR/info/grafts` to replace refs |

**Footguns:**
- Replacements are **local** unless you push `refs/replace/*` explicitly.
- The presence of any replace ref or graft **disables the commit-graph**, which can
  noticeably slow large repos.
- `git reset --hard <replaced-commit>` moves the branch to the *replacement* commit.
- For *permanent* history changes (drop a file/secret, reparent for real), use
  `filter-repo` / interactive rebase — see [history-rewriting.md](history-rewriting.md).
  The old `$GIT_DIR/info/grafts` file is deprecated; convert it with
  `--convert-graft-file`.

---

## Bisect (binary-search a bug)

Bisect binary-searches commits between a known-bad and known-good point to find the
one that introduced a change. The killer feature is `run`, which automates it.

```bash
git bisect start
git bisect bad                 # current commit is broken
git bisect good v2.3.0         # this tag was fine
# git checks out the midpoint; test it, then mark good/bad; repeat until it names
# the first bad commit (left at refs/bisect/bad).
git bisect reset               # return to where you started

# Fully automated: a script's exit status decides each step.
git bisect start HEAD v2.3.0   # <bad> <good> in one line
git bisect run ./test.sh       # exit 0 = good, 1–127 (≠125) = bad, 125 = skip
git bisect reset
```

| Command | What it does |
|---|---|
| `bisect start [<bad> [<good>…]] [-- <pathspec>]` | Begin; optionally seed endpoints/paths |
| `bisect bad [<rev>]` / `good [<rev>…]` | Mark the checked-out (or named) commit |
| `bisect new` / `old` | Generic synonyms for non-regression hunts |
| `bisect terms [--term-old\|--term-new]` | Set/show custom terms (e.g. `fast`/`slow`) |
| `bisect skip [<rev>\|<range>…]` | Can't test this one — pick a neighbor |
| `bisect run <cmd> [<args>]` | Automate via exit codes |
| `bisect log` / `replay <file>` | Save/replay the session (fix a mistaken mark) |
| `bisect visualize` / `view` | Show remaining suspects in gitk / log |
| `bisect reset [<commit>]` | End the session, restore `HEAD` |

**`run` exit-code contract:** `0` = good/old; `1`–`127` **except `125`** = bad/new;
`125` = untestable (skip); any other code aborts. In a build-then-test script, do
`make || exit 125` so unbuildable commits are skipped rather than blamed.

Useful flags: `--first-parent` (git 2.29+; blame the merge, ignore the merged branch's internal
commits) and `--no-checkout` (don't touch the worktree; test against `BISECT_HEAD`,
e.g. for bare repos). For custom good/bad vocabulary use
`git bisect start --term-old <old> --term-new <new>`.

---

## Backfill (for blobless partial clones)

**⚠️ Experimental.** `git backfill` (git 2.49+) batch-downloads the blobs a `--filter=blob:none`
clone deferred, in path-grouped requests that compress well — far better than the
one-blob-at-a-time fetches that make `git blame` crawl on a fresh blobless clone.

```bash
# In a blobless partial clone, fetch all blobs reachable from HEAD in big batches:
git clone --filter=blob:none https://example.com/big.git
cd big
git backfill

# Only blobs under your sparse-checkout cone:
git backfill --sparse
```

| Option | Effect |
|---|---|
| `--min-batch-size=<n>` | Minimum objects per request (default 50,000) |
| `--sparse` / `--no-sparse` | Restrict to sparse-checkout paths (`--sparse` implied if sparse is on) |
| `--include-edges` | Include boundary-commit blobs (default; needed for `A..B` diffs) |
| `<revision-range>` | Limit to blobs reachable from the range (default `HEAD`) |

This lets you split one giant clone into a fast blobless clone plus a few large,
delta-compressed `backfill` requests instead of a single huge transfer.

---

## Signing commits & tags (GPG / SSH)

Git can cryptographically sign commits and tags. The backend is chosen by
`gpg.format`: `openpgp` (default), `x509` (S/MIME via gpgsm), or `ssh` (git 2.34+). SSH signing
is the easiest to set up — any SSH key works.

```bash
# --- One-time setup (SSH backend; swap for openpgp to use a GPG key) ---
git config --global gpg.format ssh
git config --global user.signingKey ~/.ssh/id_ed25519.pub
git config --global commit.gpgSign true     # sign every commit
git config --global tag.gpgSign true        # sign every annotated tag

# --- Signing ---
git commit -S -m "Signed commit"            # -S explicit; redundant if commit.gpgSign
git tag -s v1.2.0 -m "Release 1.2.0"        # signed annotated tag
git tag -u <keyid> v1.2.0 -m "..."          # sign with a specific key

# --- Verifying ---
git verify-commit HEAD
git verify-tag v1.2.0          # or: git tag -v v1.2.0
git log --show-signature       # show signature status inline
git log --pretty="%h %G? %GS"  # %G? = G/B/U/X/Y/R/E/N, %GS = signer

# --- Refuse to merge/pull an unsigned or untrusted tip ---
git merge --verify-signatures topic
git pull --verify-signatures
```

| Setting / flag | Purpose |
|---|---|
| `gpg.format` | `openpgp` (default) · `x509` · `ssh` |
| `user.signingKey` | GPG key id, **or** SSH key path/`key::…` for the ssh backend |
| `commit.gpgSign` / `tag.gpgSign` | Auto-sign commits / annotated tags |
| `tag.forceSignAnnotated` | Force-sign annotated tags created without `-a`/`-s`/`-u` |
| `commit -S` / `tag -s` / `tag -u <id>` | Sign one commit / tag |
| `--no-gpg-sign` / `tag --no-sign` | Override the auto-sign config for one command |
| `verify-commit` / `verify-tag` / `tag -v` | Check a signature |
| `merge`/`pull --verify-signatures` | Abort if the merged tip isn't validly signed |
| `gpg.ssh.allowedSignersFile` | Trusted SSH signers (required to **verify** SSH) |
| `log --show-signature`, `%G?`/`%GS` | Display signature status / signer |

`%G?` codes: `G` good, `B` bad, `U` good but unknown validity, `X` good-but-expired,
`Y` good key now expired, `R` good key revoked, `E` can't check (missing key), `N` no
signature.

**SSH verification footgun:** SSH has no web of trust. `git verify-commit`/`-tag`
will **fail** (`gpg.ssh.allowedSignersFile needs to be configured and exist for ssh
signature verification`) unless the signer's public key is listed in that file. Set it
up before relying on verification:

```bash
# allowed_signers line format: "<principal-email> <key-type> <pubkey>"
echo "you@example.com $(cat ~/.ssh/id_ed25519.pub)" >> ~/.config/git/allowed_signers
git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers
```

> Signing *config* lives here; general `git config` levels/precedence are in
> [config-attributes-hooks.md](config-attributes-hooks.md). For commit-message
> conventions use the **conventional-commits** skill.

---

## Putting it together for large repos

For a huge monorepo, combine the features above rather than reaching for a shallow
clone:

```bash
# Fast initial clone + only the directories you need:
git clone --filter=blob:none --sparse https://example.com/mono.git
cd mono
git sparse-checkout set apps/web libs/shared
# Optionally shrink the index too:
git sparse-checkout reapply --sparse-index
# Pre-fetch the blobs you'll actually touch (avoids slow on-demand blame/log):
git backfill --sparse
```

Layer on a **commit-graph** and **scheduled maintenance** for speed — those mechanics
(`git gc`, `git repack`, `git commit-graph`, `git maintenance`) live in
[internals-plumbing.md](internals-plumbing.md). To *shrink history itself* by purging
large blobs, that's a rewrite — see [history-rewriting.md](history-rewriting.md).

---

## See also

- [SKILL.md](../SKILL.md) — skill overview and index
- [history-rewriting.md](history-rewriting.md) — remove big files/secrets; `filter-repo`
- [internals-plumbing.md](internals-plumbing.md) — `gc`/`repack`/`maintenance`, object model
- [config-attributes-hooks.md](config-attributes-hooks.md) — `git config` levels & precedence
- [recovery.md](recovery.md) — recover lost commits (e.g. from a detached submodule HEAD)
- [troubleshooting.md](troubleshooting.md) — error→fix lookup
- **conventional-commits** skill — commit-message formatting
