# Git Internals & Plumbing

How Git actually stores data, and the low-level "plumbing" commands that read and write it directly. Reach for this when porcelain output is ambiguous, when scripting against Git, when inspecting/repairing object and ref state, when reasoning about disk usage and packing, or when you need to spell a revision precisely. Grounded in **git 2.54.0**.

For *recovering* lost commits/branches/stashes (reflog, `fsck --lost-found`, dangling objects, `ORIG_HEAD`/`MERGE_HEAD`), see [recovery.md](recovery.md) — this file covers the model and the read/write tools, not the rescue workflows.

## Table of Contents

- [The object model](#the-object-model)
- [Object names: SHA-1 vs SHA-256](#object-names-sha-1-vs-sha-256)
- [Refs, HEAD, and packed-refs](#refs-head-and-packed-refs)
- [The index (staging area)](#the-index-staging-area)
- [Plumbing command reference](#plumbing-command-reference)
- [Building a commit by hand](#building-a-commit-by-hand)
- [Packfiles, gc, repack, maintenance](#packfiles-gc-repack-maintenance)
- [Reachability](#reachability)
- [gitrevisions: spelling revisions & ranges](#gitrevisions-spelling-revisions--ranges)

## The object model

Git is a content-addressed object store. There are **four object types**:

| Type | Holds | Inspect |
|------|-------|---------|
| **blob** | raw file contents (no name, no mode) | `git cat-file -p <oid>` |
| **tree** | a directory: list of `(mode, type, oid, name)` entries | `git cat-file -p <tree>` or `git ls-tree <tree>` |
| **commit** | one tree oid + zero-or-more parent oids + author/committer/message | `git cat-file -p <commit>` |
| **tag** | *annotated* tag: target oid + type + tagger + message (optionally signed) | `git cat-file -p <tag>` |

**Content addressing.** An object's name (OID) is the hash of its *stored form*: the header `<type> SP <size> NUL` followed by the raw content. Loose objects live zlib-compressed at `.git/objects/ab/cdef…` (first 2 hex of the OID = directory, rest = filename). Identical content → identical OID → automatic dedup. Change one byte → new OID, cascading up through tree and commit (this is why every commit names a complete snapshot, not a diff).

```bash
# Prove the hash. The "blob 6\0hello\n" form is what gets hashed:
printf 'hello\n' | git hash-object --stdin          # ce013625030ba8dba906f756967f9e9ca394464a
printf 'blob 6\0hello\n' | shasum                   # same hash (SHA-1 of the stored form)

git cat-file -t HEAD        # commit
git cat-file -p HEAD        # show commit: tree/parent/author/committer/message
git cat-file -p HEAD^{tree} # the root tree it points at
```

A tree entry's mode is one of: `100644` (file), `100755` (executable), `120000` (symlink), `160000` (gitlink/submodule), `040000` (subtree). Git stores only these — arbitrary permission bits are not tracked.

## Object names: SHA-1 vs SHA-256

The default object format is **SHA-1**, but Git uses a *collision-detecting* SHA-1 implementation (sha1dc) that aborts on inputs resembling the known SHAttered attack, so the practical collision risk is negligible.

A repository can instead use **SHA-256** (git 2.29+, experimental; OIDs are 64 hex chars):

```bash
git init --object-format=sha256 myrepo    # valid values: sha1 (default) | sha256
git rev-parse --show-object-format        # report a repo's format: storage|input|output|compat
```

**Footgun:** object format is fixed at `init`; there is no in-place conversion of an existing repo, and SHA-1↔SHA-256 interoperability (pushing/fetching between formats) is still incomplete. Don't switch an established repo to SHA-256 expecting seamless interop with SHA-1 remotes.

## Refs, HEAD, and packed-refs

A **ref** is a named pointer to an OID. The namespace lives under `.git/refs/`:

| Ref | Meaning |
|-----|---------|
| `refs/heads/<name>` | local branch |
| `refs/tags/<name>` | tag (lightweight = points straight at commit; annotated = points at a tag object) |
| `refs/remotes/<remote>/<name>` | remote-tracking branch |
| `refs/stash` | stash stack (see [worktrees-stash.md](worktrees-stash.md)) |
| `refs/notes/*`, `refs/replace/*` | notes / replacements (see [advanced-features.md](advanced-features.md)) |

**HEAD** is a *symbolic ref*: a file whose content is `ref: refs/heads/<branch>`. When HEAD instead contains a raw OID, you are in **detached HEAD**. Pseudorefs like `ORIG_HEAD`, `MERGE_HEAD`, `CHERRY_PICK_HEAD`, `FETCH_HEAD` live directly in `$GIT_DIR` and are written by porcelain (their recovery uses are covered in [recovery.md](recovery.md)).

**packed-refs.** Loose refs are one file per ref; with thousands of tags that wastes space and slows iteration. `git pack-refs` consolidates them into `.git/packed-refs`. When a ref isn't found as a loose file, Git falls back to this file. Loose refs always win over the packed copy.

```bash
git pack-refs --all          # pack all refs (incl. active branch heads)
git pack-refs --auto         # pack only when heuristics say it's worth it (2.45+)
git for-each-ref --format='%(refname) %(objectname:short)'   # enumerate refs (scriptable)
```

**reftable** (git 2.45+) is an alternative ref backend (binary, faster for huge ref counts): `git init --ref-format=reftable` (valid values `files` (default) | `reftable`). With reftable there is no `.git/refs` tree or `packed-refs` file to edit by hand.

## The index (staging area)

`.git/index` is a binary file: the proposed *next* commit. Each entry records a path, its blob OID, mode, stat data (for fast change detection), and a **stage number**:

| Stage | Meaning |
|-------|---------|
| 0 | normal, merged entry |
| 1 | common ancestor (base) — only during a conflicted merge |
| 2 | "ours" (current branch) |
| 3 | "theirs" (incoming branch) |

A path with stages 1/2/3 present (and no stage 0) *is* an unresolved conflict. `git add`ing the resolved file collapses it to stage 0.

```bash
git ls-files -s              # mode, oid, stage, path for every index entry
git ls-files -u              # only unmerged (stages 1/2/3) — list conflicts precisely
git diff-files               # index vs worktree;  git diff-index --cached HEAD = index vs HEAD
```

**`git update-index` footguns** (rarely what you want — they make Git *lie* about file state):
- `--assume-unchanged <path>` — promise the file won't change so Git skips stat'ing it (perf hack on slow filesystems). If you *do* edit it, the change is silently ignored and easily lost.
- `--skip-worktree <path>` — "the worktree copy is authoritative; don't touch it" (used by sparse-checkout). Survives more operations than assume-unchanged.

Neither is a supported way to ignore *tracked* local edits to config files — they routinely bite users on pull/checkout. Prefer a real solution (untrack + `.gitignore`, or a template file).

## Plumbing command reference

These are the stable, script-friendly primitives. Output is designed for machines; pair with `-z` for NUL-delimited safety.

### `git cat-file` — read objects

```bash
git cat-file -t <obj>        # type:  blob|tree|commit|tag
git cat-file -s <obj>        # size in bytes
git cat-file -e <obj>        # exit 0 if object exists & is valid (no output) — test for existence
git cat-file -p <obj>        # pretty-print by type
git cat-file --batch-check <<<"HEAD"          # "<oid> <type> <size>" per input line
git cat-file --batch-all-objects --batch-check='%(objtype) %(objectsize:disk) %(objectname)'
git cat-file --filters HEAD:file.txt          # apply smudge/eol filters as on checkout
git cat-file --textconv HEAD:diagram.png      # apply textconv (see config-attributes-hooks.md)
```

`--batch`/`--batch-check`/`--batch-command` (the last is git 2.36+) stream over stdin for bulk lookups; add `-Z` (git 2.42+) for NUL-delimited I/O when contents may contain newlines. `--batch-all-objects` walks *every* object (incl. unreachable), not just reachable ones.

### `git hash-object` — write objects

```bash
git hash-object <file>                 # compute OID, do NOT store
git hash-object -w <file>              # compute AND write into the object DB
printf 'data' | git hash-object -w --stdin
git hash-object -t tree -w --stdin     # hash arbitrary type
git hash-object --stdin --literally    # bypass object sanity checks (for testing corrupt objects)
```

`-w` writes; without it, you just get the hash. `--path=<p>` applies the filters that path *would* get even when hashing a temp file; `--no-filters` skips them.

### `git rev-parse` — resolve names & query repo layout

The Swiss-army knife. Two jobs: turn revision expressions into OIDs, and answer "where am I?".

| Invocation | Returns |
|------------|---------|
| `git rev-parse HEAD` | full OID of HEAD |
| `git rev-parse --verify <rev>` | OID iff exactly one valid object (great for scripts; add `-q` to fail silently) |
| `git rev-parse --short[=N] <rev>` | abbreviated unique OID |
| `git rev-parse --abbrev-ref HEAD` | current branch name (`HEAD` if detached) |
| `git rev-parse --symbolic-full-name @{u}` | full upstream ref, e.g. `refs/remotes/origin/main` |
| `git rev-parse --show-toplevel` | absolute path to worktree root |
| `git rev-parse --git-dir` | path to `.git` (file or dir) |
| `git rev-parse --absolute-git-dir` | canonical absolute `.git` path |
| `git rev-parse --git-common-dir` | shared `.git` (differs from `--git-dir` inside linked worktrees) |
| `git rev-parse --show-prefix` | path of CWD relative to worktree root |
| `git rev-parse --is-inside-work-tree` | `true`/`false` |
| `git rev-parse --is-bare-repository` | `true`/`false` |
| `git rev-parse --is-inside-git-dir` | `true`/`false` |

```bash
# Robust "are we in a repo?" guard for a script:
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "not a git repo"; exit 1; }
# Verify a user-supplied rev is a commit before using it (quote + end-of-options for safety):
git rev-parse -q --verify --end-of-options "$REV^{commit}" || exit 1
```

### `git rev-list` — walk the commit graph

```bash
git rev-list --count HEAD                 # number of commits reachable from HEAD
git rev-list --count main..feature        # commits on feature not in main (ahead count)
git rev-list --left-right --count main...feature   # "<behind>\t<ahead>"
git rev-list --objects --all              # every reachable object (oid + path) — feeds repo analysis
git rev-list --max-count=20 --since=1.week HEAD
git rev-list --disk-usage --objects --all # total on-disk size of reachable objects (2.31+)
git rev-list --no-walk <oid>...           # the given commits only, no ancestry walk
```

`--objects` is the basis for "what is taking up space"; combine with `--disk-usage` and `git cat-file --batch-check` to find heavy blobs.

### `git ls-tree` — read a tree

```bash
git ls-tree HEAD               # one level:  <mode> SP <type> SP <oid> TAB <path>
git ls-tree -r HEAD            # recurse into subtrees (files only)
git ls-tree -r -t HEAD        # recurse AND show the tree entries too
git ls-tree -l HEAD           # add blob sizes (column shows '-' for non-blobs)
git ls-tree --name-only -r HEAD            # just paths
git ls-tree -r HEAD -- path/  # limit to a pathspec
```

Default line format is exactly: `%(objectmode) %(objecttype) %(objectname)%x09%(path)`. Use `--format=` (git 2.36+) for custom fields; `-z` for NUL termination.

### `git ls-files` — read the index/worktree

```bash
git ls-files                  # tracked files (default)
git ls-files -s               # staged: <mode> SP <oid> SP <stage> TAB <path>
git ls-files -m               # modified vs index
git ls-files -o --exclude-standard         # untracked files honoring .gitignore
git ls-files -i -o --exclude-standard      # ignored files (what's being skipped)
git ls-files -u               # unmerged (conflict) entries
git ls-files --error-unmatch <path>        # exit nonzero if path isn't tracked (scriptable test)
git ls-files --eol            # show index/worktree eol + applicable text attrs
```

`--exclude-standard` applies the same ignore sources porcelain uses (`.gitignore`, `.git/info/exclude`, `core.excludesFile`).

### `git update-ref` — write refs safely

Prefer this over hand-editing files under `.git/refs` — it locks, optionally checks the old value (compare-and-swap), and writes the reflog.

```bash
git update-ref refs/heads/topic <new-oid>             # set
git update-ref refs/heads/topic <new-oid> <old-oid>   # only if it currently equals <old-oid> (CAS)
git update-ref -d refs/heads/topic                    # delete
git update-ref -m "reason" HEAD <oid>                 # write a custom reflog message
```

`--stdin` performs an **atomic multi-ref transaction**; commands are `update / create / delete / verify` (and `symref-*` for symbolic refs), bracketed by `start … prepare … commit` (or `abort`):

```bash
git update-ref --stdin <<'EOF'
start
create refs/heads/a <oidA>
update refs/heads/b <newB> <oldB>
delete refs/heads/c
prepare
commit
EOF
```

If any check fails, *none* of the updates apply (`prepare` takes all locks first). Use `40 zeros` or empty string for "must not exist".

### `git symbolic-ref` — read/write symbolic refs

```bash
git symbolic-ref HEAD                      # ref/refs/heads/main  (errors if detached)
git symbolic-ref --short HEAD              # main
git symbolic-ref HEAD refs/heads/other     # repoint HEAD without touching the worktree (footgun!)
git symbolic-ref -d HEAD                   # delete (rarely needed)
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main   # set a remote's default
```

**⚠️ Destructive:** `git symbolic-ref HEAD <ref>` changes which branch HEAD points to *without* updating the index/worktree, so the next commit/status compares against the wrong branch. Use `git switch` for normal branch changes.

### `git mktree` / `git write-tree` / `git commit-tree`

Build objects directly:

```bash
# Tree from explicit entries (input is ls-tree format):
printf '100644 blob %s\tREADME\n' "$(git hash-object -w README)" | git mktree   # -> tree oid
git write-tree                              # tree object from the CURRENT index
git commit-tree <tree> -p <parent> -m "msg"  # new commit object -> prints its oid
```

`commit-tree` takes the message via `-m`/`-F`/stdin and `-p` for each parent (omit `-p` for a root commit). `write-tree` requires a fully merged index.

## Building a commit by hand

The entire porcelain `add`→`commit` pipeline expressed in plumbing — useful for scripting commits without a worktree, or understanding what porcelain does:

```bash
blob=$(printf 'hello\n' | git hash-object -w --stdin)        # 1. store content
tree=$(printf '100644 blob %s\tgreeting.txt\n' "$blob" | git mktree)   # 2. build a tree
commit=$(echo "add greeting" | git commit-tree "$tree" -p HEAD)        # 3. wrap in a commit
git update-ref HEAD "$commit"                                # 4. move the branch (atomically)
```

To commit the current index instead of a hand-built tree, replace steps 1–2 with `tree=$(git write-tree)`.

## Packfiles, gc, repack, maintenance

Objects start **loose** (one compressed file each). For efficiency Git also stores them **packed**: many objects delta-compressed into a `.pack` file with a companion `.idx` (index) under `.git/objects/pack/`. Unreachable objects that survive are stored in a **cruft pack** (git 2.37+; `.mtimes` sidecar tracks ages) rather than as loose files.

```bash
git count-objects -vH        # loose count, on-disk size, in-pack count, pack count (human units)
```

### `git gc` — the umbrella housekeeping command

| Flag | Effect |
|------|--------|
| (none) | repack, prune loose unreachable objects older than 2 weeks, pack refs, expire reflogs, update commit-graph |
| `--auto` | do work only if thresholds (`gc.auto`, `gc.autoPackLimit`) are exceeded — what porcelain triggers |
| `--prune=<date>` | prune unreachable objects older than `<date>` (`--prune=now` = no grace period) |
| `--no-prune` | keep all unreachable objects |
| `--aggressive` | recompute all deltas (`-f`), much slower; rarely worth it |
| `--keep-largest-pack` | fold everything except the biggest pack into one |
| `--cruft` / `--no-cruft` | store pruned-but-not-yet-expired objects in a cruft pack (`--cruft` is default) |

**⚠️ Destructive (data-loss risk):** `gc` deletes unreachable objects past the grace period. A commit you "lost" (after a bad reset/rebase) is only recoverable until gc prunes it — and `--prune=now` removes the grace period entirely. If you're mid-rescue, do **not** run gc; see [recovery.md](recovery.md). Also: running `gc` concurrently with another writer risks deleting an object the other process is about to reference.

What gc keeps alive: anything reachable from branches, tags, **the index**, **remote-tracking refs**, **reflogs**, and everything under `refs/*`. (Notes attached to an object do *not* keep it alive.)

### `git repack` — control packing directly

| Flag | Effect |
|------|--------|
| `-a` | pack all objects into a single pack (use with `-d`) |
| `-A` | like `-a`, but unreachable objects become loose (so normal expiry can prune them) |
| `-d` | delete now-redundant packs/loose objects after packing |
| `-f` / `-F` | discard & recompute deltas (`-F` also ignores cached objects) |
| `-b` / `--write-bitmap-index` | write a reachability bitmap (speeds up clones/fetches; needs `-a`/`-A`) |
| `--cruft` | move unreachable objects into a cruft pack instead of loosening |
| `-g<factor>` / `--geometric=<factor>` | maintain a geometric size progression across packs (cheap incremental repacks; git 2.32+) |
| `-m` / `--write-midx` | write a multi-pack index over the resulting packs |

`--window=<n>` (default 10) and `--depth=<n>` (default 50) tune delta search vs. size.

### `git maintenance` — scheduled, background-friendly upkeep

Replaces ad-hoc `gc` with smaller, lock-aware tasks you can schedule. The `git maintenance` command is git 2.29+.

```bash
git maintenance run --task=incremental-repack   # run one task now
git maintenance register                          # opt this repo into background maintenance
git maintenance start --scheduler=auto            # install the OS schedule (cron/systemd/launchd/schtasks)
git maintenance stop                              # remove the schedule
```

Tasks: `gc`, `commit-graph`, `prefetch`, `loose-objects`, `incremental-repack`, `pack-refs`, `reflog-expire`, `rerere-gc`, `worktree-prune`. `register` sets `maintenance.strategy=incremental` (commit-graph & prefetch hourly; loose-objects & incremental-repack daily; gc disabled) and `maintenance.auto=false`.

**Don't mix** `git gc` with `git maintenance run` on the same repo — gc doesn't take the maintenance lock. Use `git maintenance run --task=gc` instead. (The `maintenance.*` config keys are owned by this file; [config-attributes-hooks.md](config-attributes-hooks.md) links here for them.)

The **commit-graph** (`git commit-graph write --reachable [--changed-paths]`, `git commit-graph verify`) is an auxiliary index that makes ancestry/`--graph`/`log` queries dramatically faster on large repos; maintenance keeps it current.

## Reachability

An object is **reachable** if you can walk to it from a *tip* (any ref, HEAD, the index, or a reflog entry) through commit→parent, commit→tree, tree→subtree/blob, tag→target links. Reachability is the dividing line for everything:

- `gc`/`prune` delete only **unreachable** objects (past the grace period).
- `git fetch`/`clone` transfer only objects needed to make the requested refs reachable.
- `git fsck --unreachable` / `--dangling` enumerate objects nothing points to — the entry point for recovery (full treatment in [recovery.md](recovery.md)).

```bash
git rev-list --objects --all | wc -l        # count reachable objects
git fsck --connectivity-only                # fast integrity check of the reachable graph
```

## gitrevisions: spelling revisions & ranges

This is the canonical home for revision syntax; other files link here. A `<rev>` usually names a commit but can name any object.

### Single revisions

| Syntax | Means |
|--------|-------|
| `HEAD`, `@` | current commit (`@` is shorthand for `HEAD`) |
| `<sha>` / unique prefix | that object |
| `<refname>` (`main`, `tags/v1`, `refs/heads/main`) | the ref (disambiguated heads→tags→remotes if bare) |
| `<rev>^` , `<rev>^<n>` | first parent / *n*-th parent (`HEAD^` = `HEAD^1`) |
| `<rev>~<n>` | *n*-th first-parent ancestor (`HEAD~3` = `HEAD^^^`) |
| `<rev>^{<type>}` | dereference until `<type>`: `<tag>^{commit}`, `<rev>^{tree}`, `<rev>^{blob}` |
| `<rev>^{}` | dereference a tag to the non-tag object it points at |
| `<rev>^0` | the commit itself (= `<rev>^{commit}`) |
| `<rev>:<path>` | the blob/tree at `<path>` in `<rev>` (`HEAD:src/main.c`, `HEAD:./rel`) |
| `:<n>:<path>` | the index entry at stage `<n>` (`:0:file`, `:2:file` = "ours" during conflict) |
| `<refname>@{<n>}` | *n*-th prior value via reflog (`main@{1}`); `@{<n>}` = current branch |
| `<refname>@{<date>}` | ref value at a time (`main@{yesterday}`, `HEAD@{2.hours.ago}`) |
| `@{-<n>}` | the *n*-th previously checked-out branch (`@{-1}` = "the branch I was just on") |
| `@{u}` / `@{upstream}` | the upstream of the current/given branch |
| `@{push}` | where `git push` would send the current branch (differs from `@{u}` in triangular workflows) |
| `:/  <text>` (`:/fix typo`) | youngest commit *reachable from any ref* whose message matches the regex |
| `<rev>^{/<text>}` | like `:/`, but youngest match reachable from `<rev>` |

### Ranges

| Syntax | Set of commits |
|--------|----------------|
| `<rev>` | everything reachable from `<rev>` |
| `^<rev>` | exclude everything reachable from `<rev>` |
| `A..B` | reachable from `B` but not `A` (= `^A B`). Omitted side defaults to HEAD (`origin..` , `..origin`) |
| `A...B` | symmetric difference: reachable from `A` or `B` but not both |
| `<rev>^@` | all parents of `<rev>` (their reachable sets, not the commit itself) |
| `<rev>^!` | just `<rev>`, excluding its parents (the single commit "and nothing before it") |
| `<rev>^-<n>` | `<rev>^<n>..<rev>` (commits merged in via the *n*-th parent; `<commit>^-` = a merge's brought-in side) |

```bash
git log main..feature          # what feature adds over main
git log main...feature --left-right    # both sides of the divergence, marked < and >
git log -p HEAD^!              # the diff of exactly one commit
git show HEAD~2:Makefile       # a file as it was two commits ago
git diff @{u}...               # changes since you diverged from upstream
```

**Footgun:** `A..B` is *reachability*, not "commits between two points in time," and `A...B` for `git diff` (two dots vs three) means something different than for `git log` — see [inspection.md](inspection.md). Quote any rev containing `^`, `~`, `{`, `:` or spaces in shells where those are special.
