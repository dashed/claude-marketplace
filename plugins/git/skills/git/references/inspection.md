# Inspecting History — log, diff, show, blame, grep

Reading and searching a repository: `git log` (pretty formats, graph, pickaxe `-S`/`-G`, line-log `-L`, `--follow`, author/date filters), `git diff` (its modes and the critical `..` vs `...` distinction), `git show`, `git blame` (move/copy detection, ignore-revs), `git shortlog`, `git range-diff`, `git describe`, and content search with `git grep`. Targets git 2.54+.

Reach here to answer "who/what/when/why did this change", to format log output precisely, to find the commit that introduced or removed a string, to trace a function's evolution, or to compare two versions of a patch series. For revision **syntax** itself (`HEAD~3`, `@{u}`, `:/msg`, `^{tree}`) see [internals-plumbing.md](internals-plumbing.md); for `git bisect` see [advanced-features.md](advanced-features.md); for reflog-based recovery (`log -g`) see [recovery.md](recovery.md).

## Table of Contents

- [`git log` essentials](#git-log-essentials)
- [Pretty formats & placeholders](#pretty-formats--placeholders)
- [Filtering which commits show](#filtering-which-commits-show)
- [Pickaxe: search history by content (`-S` / `-G`)](#pickaxe-search-history-by-content)
- [Line-log: a function's history (`-L`)](#line-log-a-functions-history)
- [Following a file across renames (`--follow`)](#following-a-file-across-renames)
- [Two-dot vs three-dot: `..` vs `...` in log vs diff](#two-dot-vs-three-dot--vs--in-log-vs-diff)
- [`git diff`](#git-diff)
- [`git show`](#git-show)
- [`git blame`](#git-blame)
- [`git shortlog`](#git-shortlog)
- [`git range-diff`](#git-range-diff)
- [`git describe`](#git-describe)
- [`git grep` — search current content](#git-grep--search-current-content)
- [Quick reference](#quick-reference)

---

## `git log` essentials

```bash
git log --oneline --graph --decorate --all   # the "show me everything" view
git log -p <path>                  # patch (diff) for each commit touching <path>
git log --stat                     # per-commit file/insertion/deletion summary
git log -3                         # last 3 (also -n 3 / --max-count=3)
git log --reverse                  # oldest first (applied after limiting)
git log --first-parent             # follow only first parents (clean topic view)
```

- `--graph` draws the ASCII commit graph (implies topo-order; can't combine with `--no-walk`).
- `--decorate[=short|full|auto|no]` shows ref names; `--oneline` = `--pretty=oneline --abbrev-commit`.
- `--all` / `--branches` / `--tags` / `--remotes` widen the starting refs; `--not <ref>` excludes.
- Merge commits show **no diff** by default with `-p`; add `-m`, `-c`, `--cc`, or `--remerge-diff` (git 2.36+) to see merge diffs (or `--first-parent`, which shows first-parent diffs).

## Pretty formats & placeholders

```bash
git log --pretty=oneline          # <hash> <subject>
git log --pretty=short|medium|full|fuller|reference|raw|email
git log --pretty=format:'%h %an %ar  %s'   # custom (see table)
```

Built-in `--pretty=reference` (git 2.25+) → `<abbrev-hash> (<subject>, <short-date>)` — exactly the format to cite a commit in a message.

**Most useful `format:` placeholders:**

| Code | Expands to | Code | Expands to |
|------|-----------|------|-----------|
| `%H` / `%h` | full / abbrev commit hash | `%T` / `%t` | full / abbrev tree hash |
| `%P` / `%p` | parent hashes / abbrev | `%an` / `%ae` | author name / email |
| `%cn` / `%ce` | committer name / email | `%s` / `%b` | subject / body |
| `%ad` | author date (honors `--date=`) | `%cd` | committer date |
| `%ar` / `%cr` | author / committer date, **relative** | `%as` / `%cs` | date, short `YYYY-MM-DD` |
| `%d` / `%D` | ref decorations (with / without parens) | `%S` | which `--source` ref reached it |
| `%G?` | signature status (`G`ood/`B`ad/`U`/`E`/`N`…) | `%C(auto)` | auto-color the following placeholders |
| `%n` | newline | `%%` | literal `%` |

Use `%aN`/`%aE` (capitalized) for `.mailmap`-canonicalized name/email. Add `+`/`-`/` ` after `%` to conditionally insert a leading newline/strip newlines/space when the field is (non-)empty.

**Date formats** (`--date=`): `relative`, `short`, `iso` (`iso8601`), `iso-strict`, `rfc`, `human` (git 2.21+), `unix`, `raw`, `format:%Y-%m-%d %H:%M` (strftime), and `*-local` variants. `format.pretty` config sets the default `--pretty`.

```bash
git log --pretty=format:'%C(auto)%h%d %s %C(dim)(%an, %ar)' --graph
git log --date=format:'%Y-%m-%d' --pretty=format:'%ad %s'
```

## Filtering which commits show

These are **commit-limiting** options (applied before ordering); combining them narrows further.

| Filter | Effect |
|--------|--------|
| `--author=<re>` / `--committer=<re>` | Author/committer header matches regex (repeat = OR) |
| `--grep=<re>` | Commit **message** matches regex (repeat = OR) |
| `--all-match` | With multiple `--grep`, require **all** to match |
| `--invert-grep` | Commits whose message does **not** match `--grep` |
| `-i` | Case-insensitive matching for the above |
| `-E` / `-P` / `-F` | Extended / Perl / fixed-string patterns (default is basic regex) |
| `--since=<date>` / `--after` | Commits newer than date |
| `--until=<date>` / `--before` | Commits older than date |
| `--no-merges` / `--merges` | Exclude / show only merges (= `--max-parents=1` / `--min-parents=2`) |
| `--min-parents=<n>` / `--max-parents=<n>` | By parent count (`--max-parents=0` = roots; `--min-parents=3` = octopus) |
| `--first-parent` | Don't descend into merged side branches |
| `-- <path>` | Only commits touching `<path>` (the `--` separates paths from revs) |

```bash
git log --author='Alberto' --since='2 weeks ago' --oneline
git log --grep='fix' --grep='bug' --all-match -i      # message has BOTH (any case)
git log --no-merges --since='2026-01-01' --oneline -- src/
```

**Note:** date strings accept absolute (`2026-01-01`), ISO, and approxidate (`"2 weeks ago"`, `yesterday`). `--since` stops the walk at the first older commit; use `--since-as-filter` to keep walking and filter individually.

## Pickaxe: search history by content

Find the commits where a string or pattern's presence **changed** — the fastest way to answer "when was this added/removed?".

| Option | Finds commits that… |
|--------|---------------------|
| `-S<string>` | change the **number of occurrences** of `<string>` (added or removed it) |
| `-S<string> --pickaxe-regex` | as above, but `<string>` is an (extended POSIX) regex |
| `-G<regex>` | have any **added/removed line** matching `<regex>` (even if the count is unchanged) |
| `--pickaxe-all` | when a match is found, show **all** files changed in that commit, not just matches |
| `--find-object=<oid>` | change the number of occurrences of a specific blob/object |

```bash
git log -S'getUserById' --oneline           # commits that introduced/removed the symbol
git log -S'getUserById' -p                   # ...with the diffs
git log -G'TODO.*security' --oneline         # commits whose diff touched a matching line
```

**`-S` vs `-G`:** for a commit that both adds `return frotz(nitfol, …)` and removes `hit = frotz(nitfol, …)`, `git log -G'frotz\(nitfol'` **shows** it (a matching line moved) but `git log -S'frotz\(nitfol' --pickaxe-regex` **does not** (the occurrence count didn't change). Use `-S` to track a block's existence; `-G` to find any edit mentioning a pattern.

> Pickaxe searches **history/diffs**. To search the **current** working tree or a tree object, use `git grep` (below) — it's far faster for "where is this now?".

## Line-log: a function's history

`-L` traces a specific line range or function across history (implies `-p`):

```bash
git log -L 40,80:app.py                  # evolution of lines 40–80
git log -L :parseConfig:app.py           # evolution of the parseConfig function
git log -L '/^class Parser/',/^}/:app.py # regex-bounded range
```

`<start>,<end>` may use `/regex/` bounds; `-L` may be given multiple times; no pathspec limiters allowed. Powered by the same hunk-header detection as `git diff` (tunable per language via `.gitattributes` — see [config-attributes-hooks.md](config-attributes-hooks.md)).

## Following a file across renames

```bash
git log --follow -- path/to/file         # continue history past renames (SINGLE file only)
git log --oneline --follow -- src/old_name.py
```

`--follow` works for **one file at a time**. For commit-level rename detection in diffs use `-M`/`-C` (below).

## Two-dot vs three-dot: `..` vs `...` in log vs diff

**⚠️ This is one of git's sharpest footguns:** the same notation has near-opposite meanings in history-walking commands versus `git diff`.

**In `git log` / `rev-list` / `shortlog` (revision *ranges*):**

| Notation | Means | Equivalent |
|----------|-------|-----------|
| `A..B` | commits reachable from **B but not A** | `^A B` |
| `A...B` | **symmetric difference** — reachable from A *or* B but **not both** | `A B --not $(git merge-base --all A B)` |
| `B` (single) | everything reachable from B | — |
| `^A B` | reachable from B, excluding A | = `A..B` |

```bash
git log main..feature        # what feature has that main doesn't (your unmerged work)
git log origin/main..        # omitted end = HEAD → "what have I done since origin/main?"
git log --left-right --oneline A...B    # mark <left (A-only) and >right (B-only)
git log --cherry-pick A...B  # drop commits that are patch-equivalent on both sides
git log --cherry main...topic  # = --right-only --cherry-mark --no-merges (like git cherry)
```

**In `git diff` (compares two *endpoints*, NOT ranges):**

| Notation | Means | Equivalent |
|----------|-------|-----------|
| `git diff A B` | difference between the two trees | — |
| `git diff A..B` | **same as `A B`** (the two dots are cosmetic here) | `git diff A B` |
| `git diff A...B` | changes on **B's side since the merge base** | `git diff $(git merge-base A B) B` |

```bash
git diff main feature        # total tree difference between the two tips
git diff main..feature       # IDENTICAL to the line above
git diff main...feature      # only what feature added since it forked from main
```

**The trap:** `git log A...B` is symmetric (both sides); `git diff A...B` is one-sided (B since fork). And `git diff A..B` ignores the base entirely while `git log A..B` is defined *by* exclusion. When reviewing a PR's own changes, `git diff main...feature` (three dots) is usually what you want; for log it's `git log main..feature` (two dots). Writing two two-dot ranges (`git log A..B C..D`) does **not** mean two ranges — it's one combined set.

## git diff

Compare endpoints: working tree, index, commits, blobs, or files on disk.

| Invocation | Compares |
|------------|----------|
| `git diff` | working tree ↔ index (unstaged changes) |
| `git diff --staged` (`--cached`) | index ↔ HEAD (what you'd commit) |
| `git diff HEAD` | working tree ↔ last commit (staged + unstaged) |
| `git diff <commit>` | working tree ↔ that commit |
| `git diff <a> <b>` | two commits/trees (also `<a>..<b>`; `<a>...<b>` = since merge-base) |
| `git diff <a> <b> -- <path>` | limited to `<path>` |
| `git diff --no-index <p1> <p2>` | two files/dirs **outside** git |
| `git diff <blob> <blob>` | raw blob contents |
| `git diff --merge-base A [B]` | use merge-base of A and HEAD (or A,B) as the "before" (git 2.30+) |

**Output modes:**

| Option | Output |
|--------|--------|
| `--stat` / `--numstat` / `--shortstat` | diffstat / machine-readable counts / one-line totals |
| `--compact-summary` | diffstat + creations/deletions/mode changes |
| `--dirstat[=files,10,cumulative]` | per-directory change distribution |
| `--name-only` / `--name-status` | filenames / filenames+status letters |
| `--diff-filter=ACDMRTUXB` | keep only Added/Copied/Deleted/Modified/Renamed/Type-changed/Unmerged/…; **lowercase excludes** (`--diff-filter=d` = drop deletions) |
| `--word-diff[=color\|plain\|porcelain]` | word-level instead of line-level (`--color-words` = `--word-diff=color`) |
| `--word-diff-regex=<re>` | define what a "word" is (e.g. `.` = per-character) |
| `--color-moved[=<mode>]` | colorize moved lines distinctly from add/del |
| `-R` | reverse the diff |

**Rename/copy & whitespace:**

```bash
git diff -M HEAD~5            # detect renames (default 50% similarity; -M90% to tighten)
git diff -C HEAD~5            # detect copies as well as renames
git diff --find-copies-harder # inspect even unmodified files as copy sources (slow)
git diff -w                   # ignore ALL whitespace (-w/--ignore-all-space)
git diff -b                   # ignore whitespace-amount changes (--ignore-space-change)
git diff --ignore-space-at-eol --ignore-blank-lines
git diff --diff-algorithm=histogram   # or --patience / --minimal / myers (default)
```

```bash
git diff --staged --stat                 # summary of what's about to be committed
git diff main...feature -- src/          # PR's changes to src/ since fork
git diff --word-diff HEAD~1              # word-level last-commit diff (great for prose)
git diff AUTO_MERGE                       # mid-conflict: what you've resolved so far (ort)
```

While resolving conflicts, `git diff -1`/`-2`/`-3` (`--base`/`--ours`/`--theirs`) compare the worktree against each conflict stage — see [branching-merging.md](branching-merging.md).

## git show

Display any single object — commit (message + diff), tag, tree, or blob:

```bash
git show <commit>                 # message + diff (merges shown combined / dense-combined)
git show <commit>:<path>          # the file's contents AT that commit (blob)
git show HEAD~3:src/app.py        # historical version of a file
git show <tag>                    # tag message + the object it points to
git show v1.0^{tree}             # the tree object a tag/commit points to
git show -s --format=%s <commit>  # subject only (-s suppresses the diff)
git show --stat <commit>          # message + file summary, no patch
```

`git show` accepts the same pretty/diff options as `git log`. `git show <a> <b>` shows several objects in turn.

## git blame

Annotate each line with the commit that last changed it.

```bash
git blame file.c                  # full-file annotation
git blame -L 40,80 file.c         # only lines 40–80 (also -L 40,+41)
git blame -L :parseConfig:file.c  # only the parseConfig function
git blame <rev> -- file.c         # blame as of <rev>
git blame -e file.c               # show emails; -s suppress author+date; -n orig line no.
```

**Seeing through noise** — the options that make blame actually useful:

| Option | Effect |
|--------|--------|
| `-w` | Ignore whitespace when matching lines to their origin |
| `-M[<n>]` | Detect lines **moved/copied within the same file** (default threshold 20 chars) |
| `-C[<n>]` | Also detect lines **moved/copied from other files changed in the same commit**. `-C -C` also checks the commit that *created* the file; `-C -C -C` checks **any** commit (slowest, most thorough) |
| `--ignore-rev <rev>` | Blame as if `<rev>` never happened — skip a bulk-reformat commit (git 2.23+) |
| `--ignore-revs-file <file>` | Skip every commit listed in the file (format like `fsck.skipList`); set `blame.ignoreRevsFile=.git-blame-ignore-revs` to apply automatically |
| `--color-by-age` / `--color-lines` | Color by line age / by repeated commit |
| `--reverse <start>..<end>` | Walk **forward**: show the last commit in which each line still existed (find when a line was deleted) |

```bash
git blame -w -C file.c                          # ignore whitespace + follow moved code
git blame --ignore-revs-file .git-blame-ignore-revs file.c   # skip "ran prettier" commits
git blame -C -C -f <commit>^! -- file.c         # find copy-pasted lines in a new file
```

**Pattern to neutralize formatting commits:** put the reformat commit hashes (one per line) in `.git-blame-ignore-revs`, commit it, and set `git config blame.ignoreRevsFile .git-blame-ignore-revs`. Whole-file rename-following is automatic and cannot be disabled.

## git shortlog

Summarize `git log` grouped by author — the release-notes / contribution view.

```bash
git shortlog -s -n               # author → commit count, sorted by count (the idiom: -sn)
git shortlog -s -n -e            # ...with emails
git shortlog -n HEAD~50..        # only the last 50 commits' worth
git shortlog -sn --group=trailer:Co-authored-by   # tally co-authors
git shortlog -sn --group=trailer:Reviewed-by      # tally reviewers
```

`-s`/`--summary` = counts only; `-n`/`--numbered` = sort by count; `-e`/`--email` = show emails. `--group=` (git 2.29+) can be `author` (default), `committer` (or `-c`), `trailer:<field>`, or `format:<fmt>`. Accepts any `git log` revision range and pathspec.

## git range-diff

Compare **two versions of a patch series** (e.g. before/after a rebase or a re-roll) — shows which commits were added, dropped, reordered, or modified, with a diff-of-diffs (`git range-diff`: git 2.19+).

```bash
git range-diff @{u} @{1} @       # after a rebase: old upstream..old-HEAD vs ..new-HEAD
git range-diff main..v1 main..v2 # two ranges explicitly
git range-diff v1...v2           # shorthand for: v2..v1  v1..v2
git range-diff <base> <rev1> <rev2>   # base..rev1 vs base..rev2
```

Three input forms: `<range1> <range2>`, `<rev1>...<rev2>`, or `<base> <rev1> <rev2>`. Output markers per line: `=` unchanged, `!` modified (with inner diff), `<`/`>` dropped/added. Tune pairing with `--creation-factor=<pct>` (default 60) if it misjudges a big edit as a wholesale rewrite. Merges are ignored unless `--remerge-diff` / `--diff-merges=<fmt>`. Especially useful to confirm a rebase changed nothing but the base.

## git describe

Produce a human-readable name from the nearest reachable tag: `<tag>-<n>-g<abbrev-hash>` (n commits past the tag; `g` = git).

```bash
git describe                  # nearest annotated tag, e.g. v1.0.4-14-g2414721
git describe --tags           # also consider lightweight tags
git describe --all            # consider any ref (branches, remotes)
git describe --abbrev=0       # just the closest tag name (drop the suffix)
git describe --long           # always full form even when on a tag exactly
git describe --dirty          # append "-dirty" if the worktree has changes
git describe --contains <c>   # nearest tag that comes AFTER <c> (implies --tags)
git describe --match 'v*' --exclude '*rc*'   # filter candidate tags
```

`--candidates=<n>` widens the search; `--exact-match` (= `--candidates=0`) only prints a tag that points exactly at the commit; `--always` falls back to an abbreviated hash when no tag is found. A blob is described as `<commit-ish>:<path>`.

## git grep — search current content

Search **tracked file contents** (or the index / a tree / non-git files) — vastly faster than piping through `grep` and respects git's view of the repo.

```bash
git grep 'TODO'                       # tracked files in the working tree
git grep -n 'TODO'                    # with line numbers (-n)
git grep -i -w 'parse'                # case-insensitive (-i), whole word (-w)
git grep -l 'deprecated'              # just file names (-l); -L = files WITHOUT match
git grep -c 'import'                  # count matches per file (-c)
git grep --cached 'foo'               # search the index (staged content)
git grep --untracked 'foo'           # also search untracked files
git grep --no-index 'foo'            # search files outside any git repo
git grep 'foo' v2.1.0                 # search a tag/commit/tree (history snapshot)
git grep 'foo' -- '*.py' ':^vendor'   # pathspec limits; ':^' excludes a path
```

**Context & structure:**

| Option | Effect |
|--------|--------|
| `-n` / `--line-number` | Prefix line numbers |
| `-W` / `--function-context` | Show the **whole enclosing function** of each match |
| `-p` / `--show-function` | Show the function-name line preceding the match |
| `-A<n>` / `-B<n>` / `-C<n>` | After / before / around context lines |
| `--break` / `--heading` | Blank line between files / filename as a heading (grep-app style) |
| `-O[<pager>]` | Open matching files in the pager/editor |

**Patterns & boolean logic:**

```bash
git grep -e 'foo' --and \( -e 'bar' -e 'baz' \)   # 'foo' AND ('bar' OR 'baz') on a line
git grep --all-match -e 'foo' -e 'bar'            # FILES containing lines matching both
git grep -P '(?<=\bfn_)\w+'                        # Perl regex (-P)
git grep -F 'a.b.c'                                # fixed string (-F), no regex
git grep -e '-flag'                                # -e needed for patterns starting with -
```

`-E`/`-G`/`-P`/`-F` choose extended/basic(default)/Perl/fixed patterns; `--and`/`--or`/`--not`/`( )` combine multiple `-e` patterns (`--or` is implicit, `--and` binds tighter). `-v` inverts.

> **`git grep` vs pickaxe (`git log -S`/`-G`):** grep searches a **snapshot** (current tree, index, or one commit) — "where is X *now*?"; pickaxe searches **diffs across history** — "*when* did X change?". Use the right one.

## Quick reference

| Task | Command |
|------|---------|
| Compact graph of all branches | `git log --oneline --graph --decorate --all` |
| My unmerged work vs main | `git log main..HEAD --oneline` |
| A PR's own diff | `git diff main...feature` |
| When was a symbol added/removed | `git log -S'name' --oneline` |
| Any diff line touching a pattern | `git log -G'regex' -p` |
| A function's history | `git log -L :func:file.c` |
| File history across renames | `git log --follow -- path` |
| Who changed these lines, ignoring fmt | `git blame -w -C --ignore-revs-file .git-blame-ignore-revs file` |
| When was a line deleted | `git blame --reverse <old>..HEAD -- file` |
| File contents at a commit | `git show <rev>:<path>` |
| Contributor counts | `git shortlog -sn` |
| Did the rebase change anything? | `git range-diff @{u} @{1} @` |
| Human version string | `git describe --tags --dirty` |
| Find text in current tree | `git grep -n 'text'` |
| Find text with full function | `git grep -W 'text'` |

**See also:** [internals-plumbing.md](internals-plumbing.md) (revision syntax `HEAD~`/`@{u}`/`:/`/`^{tree}`, `rev-list`, `rev-parse`) · [recovery.md](recovery.md) (`log -g`/reflog) · [advanced-features.md](advanced-features.md) (`bisect`, signature verification) · [branching-merging.md](branching-merging.md) (conflict-stage diffs `-1`/`-2`/`-3`, `--cherry`) · [config-attributes-hooks.md](config-attributes-hooks.md) (hunk-header/diff drivers, `.mailmap`) · [SKILL.md](../SKILL.md).
