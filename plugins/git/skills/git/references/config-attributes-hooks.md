# Config, Attributes, Ignore & Hooks

How to *configure* Git's behavior and *automate* around it: `git config` (levels, conditional includes, high-value settings), `.gitattributes` (line endings, filters, custom diff/merge drivers, archive control), `.gitignore` (patterns, precedence, debugging), hooks (client- and server-side), and aliases. Grounded in **git 2.54.0**.

Cross-references: commit/tag **signing** config (`commit.gpgsign`, `gpg.format`, `user.signingkey`) lives in [advanced-features.md](advanced-features.md); `maintenance.*` config lives in [internals-plumbing.md](internals-plumbing.md); diagnosing line-ending / "dubious ownership" / ".gitignore not working" problems is in [troubleshooting.md](troubleshooting.md); commit-*message* formatting is the **conventional-commits** skill.

## Table of Contents

- [git config: levels & precedence](#git-config-levels--precedence)
- [Reading and writing config](#reading-and-writing-config)
- [Conditional config with includeIf](#conditional-config-with-includeif)
- [High-value settings](#high-value-settings)
- [.gitattributes](#gitattributes)
- [.gitignore](#gitignore)
- [Hooks](#hooks)
- [Aliases](#aliases)

## git config: levels & precedence

Config is read from several files, each a **scope**. Later scopes override earlier ones for the same key; the order, lowest → highest precedence:

| Scope | File | Flag |
|-------|------|------|
| system | `$(prefix)/etc/gitconfig` | `--system` |
| global | `$XDG_CONFIG_HOME/git/config`, then `~/.gitconfig` | `--global` |
| local | `$GIT_DIR/config` (the repo) | `--local` (default for writes) |
| worktree | `$GIT_DIR/config.worktree` | `--worktree` (needs `extensions.worktreeConfig`) |
| command | `git -c key=val …`, `GIT_CONFIG_{COUNT,KEY,VALUE}` | (highest) |

For a single key the **last value wins**; for multi-valued keys, values from *all* files accumulate. Inspect where a value actually came from:

```bash
git config list --show-origin --show-scope     # every value + its file + its scope
git config get --show-origin user.email        # which file set my email here?
```

`--worktree` only diverges from `--local` once you enable it (per-worktree config is otherwise shared); see [worktrees-stash.md](worktrees-stash.md):

```bash
git config set extensions.worktreeConfig true  # then --worktree writes config.worktree
```

**"command" scope is a power tool:** `git -c user.email=me@x.com commit …` overrides config for one invocation without touching any file — ideal in scripts and CI.

## Reading and writing config

Git 2.46+ exposes **subcommands** (`get`/`set`/`unset`/`list`/…). These are the recommended forms; the old dashed flags still work but are deprecated.

```bash
git config get user.email                  # read (last value)
git config get --all push.default          # all values of a multi-valued key
git config get --regexp '^alias\.'         # keys matching a regex (+ --show-names to print keys)
git config set core.editor "vim"           # write (to --local by default)
git config set --append remote.origin.fetch '+refs/pull/*:refs/pull/*'   # add a line (multivar)
git config unset core.editor               # remove
git config unset --all branch.main.merge   # remove all values of a multivar
git config list                            # dump everything
git config edit --global                   # open ~/.gitconfig in $EDITOR
git config rename-section branch.old branch.new
git config remove-section submodule.libfoo
```

| New subcommand | Deprecated flag |
|----------------|-----------------|
| `git config get <k>` | `git config <k>` / `--get` |
| `git config get --all <k>` | `--get-all` |
| `git config get --all --show-names --regexp <re>` | `--get-regexp` |
| `git config set <k> <v>` | `git config <k> <v>` |
| `git config set --append <k> <v>` | `--add` |
| `git config unset <k>` | `--unset` |
| `git config list` | `-l` / `--list` |
| `git config edit` | `-e` / `--edit` |

Type-checking on read avoids parsing bugs: `git config get --type=bool core.bare`, `--type=int`, `--type=path` (expands `~`), `--type=expiry-date`, `--type=color`. Add `--default=<v>` to supply a fallback. For multivars, target one line with `--value=<regex>` (or `--fixed-value` for a literal).

## Conditional config with includeIf

Pull in another config file *only when a condition holds* — the standard way to use different identities/settings per directory tree, branch, or remote. `[include] path=…` is unconditional; `[includeIf "<cond>"] path=…` is conditional. Relative `path` is resolved against the file containing the directive; `~/` expands to `$HOME`.

Condition keywords:

| Condition | True when |
|-----------|-----------|
| `gitdir:<glob>` | the repo's `.git` dir matches the glob |
| `gitdir/i:<glob>` | same, case-insensitive |
| `onbranch:<glob>` | the currently checked-out branch matches |
| `hasconfig:remote.*.url:<glob>` | any configured remote URL matches |

`gitdir` glob conveniences: a trailing `/` appends `**` (matches the dir and everything under it); a pattern without `~/`, `./`, or a leading `/` gets `**/` prepended (so `foo/bar` matches `/any/foo/bar`).

```ini
# ~/.gitconfig
[user]
    name = Jane Dev
[includeIf "gitdir:~/work/"]
    path = ~/.gitconfig-work        # work identity for everything under ~/work/
[includeIf "gitdir:~/oss/"]
    path = ~/.gitconfig-oss
[includeIf "onbranch:release/"]
    path = ~/.gitconfig-release     # extra guards while on release/* branches

# ~/.gitconfig-work
[user]
    email = jane@employer.com
[commit]
    gpgsign = true                  # signing setup: see advanced-features.md
```

**Footgun:** the condition is evaluated against the *real* `.git` location (symlinks under `$GIT_DIR` are not resolved before matching, but both symlink and realpath forms outside `$GIT_DIR` are tried). If `gitdir:~/work` silently fails to switch your email, check the glob has a trailing `/` and the repo really lives under that path (`git rev-parse --absolute-git-dir`).

## High-value settings

Settings that change behavior in ways worth knowing (not an exhaustive list — `git help --config`):

| Key | Why it matters |
|-----|----------------|
| `init.defaultBranch` | name for the initial branch (`main`) |
| `core.autocrlf` / `core.eol` | line-ending conversion — see [.gitattributes](#gitattributes) and [troubleshooting.md](troubleshooting.md) |
| `core.editor` / `core.pager` | editor for messages; pager for output |
| `core.excludesFile` | global ignore file (default `$XDG_CONFIG_HOME/git/ignore`) |
| `core.hooksPath` | relocate the hooks dir (share hooks across repos) |
| `core.fileMode` | track the executable bit or not |
| `core.fsmonitor` | speed up status on huge worktrees |
| `pull.rebase` | `true`/`false`/`merges` — rebase vs merge on pull |
| `pull.ff` = `only` | refuse pulls that would create a merge |
| `push.default` = `simple` | what bare `git push` pushes |
| `push.autoSetupRemote` | auto-create upstream on first push of a new branch |
| `fetch.prune` = `true` | delete remote-tracking refs for deleted upstream branches |
| `rebase.autosquash` | honor `fixup!`/`squash!` automatically (see [history-rewriting.md](history-rewriting.md)) |
| `rebase.autoStash` | stash/unstash a dirty tree around rebase/pull |
| `rebase.updateRefs` | move dependent branch refs during interactive rebase |
| `merge.conflictStyle` = `zdiff3` | show the common ancestor in conflict markers (much easier merges) |
| `rerere.enabled` | record/replay conflict resolutions (owned by [branching-merging.md](branching-merging.md)) |
| `diff.algorithm` = `histogram` | better diffs than default `myers` |
| `diff.colorMoved` | highlight moved (vs added/removed) lines |
| `commit.verbose` | show the diff in the commit-message editor |
| `help.autocorrect` | run/suggest the intended command on typos |
| `column.ui` = `auto` | columnar `branch`/`status` listings |
| `rerere.autoUpdate`, `branch.sort`, `tag.sort` | quality-of-life ordering & automation |
| `credential.helper` | cache/store credentials (see [troubleshooting.md](troubleshooting.md) for auth) |
| `url.<base>.insteadOf` | rewrite remote URLs (e.g. force SSH over HTTPS) |
| `safe.directory` | allow operating on a repo owned by another user (see [troubleshooting.md](troubleshooting.md)) |
| `maintenance.*` | background upkeep — see [internals-plumbing.md](internals-plumbing.md) |
| `commit.gpgsign`, `gpg.format`, `user.signingkey` | signing — see [advanced-features.md](advanced-features.md) |

```bash
git config set --global pull.ff only
git config set --global merge.conflictStyle zdiff3
git config set --global fetch.prune true
git config set --global url."git@github.com:".insteadOf "https://github.com/"
```

## .gitattributes

Attribute rules attach behavior to path patterns: line-ending policy, diff/merge drivers, filters, archive inclusion. Each line is `<pattern> <attr> <attr>…`, where an attr is `name` (set), `-name` (unset), `name=value`, or `!name` (force back to *unspecified*). Patterns use `.gitignore` syntax **except** negative patterns are forbidden and a directory pattern does **not** recurse (use `path/**`).

**Where they're read & precedence** (highest → lowest): `$GIT_DIR/info/attributes` → `.gitattributes` nearest the path → parent `.gitattributes` (farther = weaker) → `core.attributesFile` (default `$XDG_CONFIG_HOME/git/attributes`) → `$(prefix)/etc/gitattributes`. Within one file, a later matching line overrides earlier, per attribute.

Inspect what actually applies:

```bash
git check-attr -a -- path/to/file        # all attributes on a path
git check-attr text eol diff -- file.c   # specific ones:  prints set | unset | unspecified | <value>
git check-attr --all --cached -- file    # consult .gitattributes in the index, not the worktree
```

### Line endings: text / eol / encoding

```gitattributes
* text=auto                 # normalize to LF in the repo; convert on checkout per platform
*.sh   text eol=lf          # always LF in the worktree
*.bat  text eol=crlf        # always CRLF in the worktree
*.png  binary               # never touch (macro: -text -diff -merge)
*.ps1  text working-tree-encoding=UTF-16LE eol=crlf   # store UTF-8, checkout as UTF-16LE
```

- `text` / `text=auto`: enables LF-in-index normalization (`auto` lets Git detect text vs binary). When unspecified, `core.autocrlf`/`core.eol` decide.
- `eol=lf|crlf`: forces the worktree line ending (implies `text`).
- `working-tree-encoding=<enc>`: store as UTF-8 internally, re-encode on checkout. **Footgun:** clients/old Git without support will checkout mangled content; always pair with `eol` and confirm all clients support it.
- Committing a `.gitattributes` `text=auto` change? Re-normalize once: `git add --renormalize .`

### Filters (clean / smudge)

A filter transforms content on the way in (`clean`, on `add`) and out (`smudge`, on checkout). Declare the attribute in `.gitattributes`, define the commands in config.

```gitattributes
*.secret  filter=crypt
```
```ini
[filter "crypt"]
    clean  = openssl enc -e ...     # worktree -> repo
    smudge = openssl enc -d ...     # repo -> worktree
    required = true                 # fail loudly if filter is missing/errors
```

**Footgun:** without `required = true`, a missing/failing filter is a silent no-op pass-through — you can commit unencrypted content thinking it was encrypted. Git LFS is the canonical real-world `clean`/`smudge` (+ `process`) filter.

### Custom diff drivers

```gitattributes
*.json  diff=json
*.png   diff=exif
```
```ini
[diff "json"]
    algorithm = histogram           # per-path diff algorithm
[diff "exif"]
    textconv = exiftool             # diff a text rendering of a binary (cacheable: cachetextconv=true)
[diff "tex"]
    xfuncname = "^(\\\\(sub)*section\\{.*)$"   # custom @@ hunk-header text
```

Built-in language drivers give good hunk headers out of the box — just enable them: `*.py diff=python` (also `c`/`cpp`, `golang`, `rust`, `java`, `kotlin`, `php`, `ruby`, `bash`, `markdown`, `html`, `css`, and more). For a fully external differ use `[diff "x"] command = …`.

### Custom merge drivers

```gitattributes
*.lock   merge=binary        # built-in: keep ours, mark conflicted
CHANGELOG merge=union        # built-in: keep BOTH sides' lines, no markers
*.db     merge=keepmine      # custom
```
```ini
[merge "keepmine"]
    name   = keep my version
    driver = my-merge %O %A %B %L %P    # %O=base %A=ours/result %B=theirs %L=marker-size %P=path
    recursive = binary                  # driver to use for inner ancestor merges
```

The driver writes the merged result into the `%A` file and exits 0 (clean) or non-zero (conflict). Built-ins: `text` (normal 3-way), `binary` (keep ours + conflict), `union` (concatenate both sides — handy for append-only files like changelogs, **but** ordering is arbitrary; verify the result).

### Archive control & misc

```gitattributes
.gitattributes  export-ignore    # omit from `git archive` output
/test/          export-ignore
VERSION         export-subst     # expand $Format:%H$ etc. when archiving
*.bin           -delta           # skip delta compression for these blobs
```

**Macro attributes** expand one name into several. The built-in `binary` = `[attr]binary -diff -merge -text`. Define your own only in a *top-level* attributes file:

```gitattributes
[attr]lockfile  -diff -merge -text
*.lock lockfile
```

**`linguist-*`** (`linguist-language`, `linguist-vendored`, `linguist-generated`, `linguist-documentation`) are **not** core Git — they're consumed by GitHub's Linguist for language stats and diff suppression. Git ignores them; they're safe to set but only affect GitHub.

## .gitignore

Tells Git which **untracked** files to leave alone. Sources, highest → lowest precedence (and *within* one file, the **last matching pattern wins**):

1. command-line patterns (for commands that take them)
2. `.gitignore` in the file's dir, then parent dirs up to the worktree root (**deeper files override shallower**)
3. `$GIT_COMMON_DIR/info/exclude` (repo-local, not committed)
4. `core.excludesFile` (default `$XDG_CONFIG_HOME/git/ignore`) — your personal global ignores

Choose by intent: share project build artifacts → committed `.gitignore`; your private scratch files in this one repo → `.git/info/exclude`; editor backups everywhere → global `core.excludesFile`.

### Pattern syntax

```gitignore
# comment (escape a literal leading # with \#)
build/            # trailing slash => directories only
/TODO             # leading slash => anchored to THIS .gitignore's dir
*.log             # glob; * and ? and [a-z] do NOT cross '/'
!keep.log         # '!' re-includes a previously excluded file
doc/**/*.pdf      # ** matches across directory levels
**/node_modules   # match node_modules at any depth
```

Key rules: a `/` at the start or middle anchors the pattern to the `.gitignore`'s directory; otherwise it can match at any depth below. `**` spans directories (`a/**/b`); leading `**/` matches in all dirs; trailing `/**` matches everything inside.

**⚠️ Footgun:** you **cannot** re-include a file with `!` if an *ancestor directory* is already excluded — Git never descends into ignored dirs. Use the "exclude all, then re-include" idiom:

```gitignore
/*               # ignore everything at top level
!/src            # but not src/ (the directory)
/src/*           # ignore src's contents
!/src/keep/      # except this subtree
```

**⚠️ Footgun:** `.gitignore` only affects **untracked** files. Adding a pattern for an already-tracked file does nothing — you must `git rm --cached <file>` first. (Full diagnosis in [troubleshooting.md](troubleshooting.md).)

### Debugging with check-ignore

```bash
git check-ignore -v <path>        # print the source:line:pattern that ignores <path>
git check-ignore -v -n <path>     # also report paths that are NOT ignored (with --verbose)
git check-ignore --no-index <p>   # ignore the index — debug why `git add` did/didn't skip it
```

Output `path/to/.gitignore:12:*.log    path/to/file.log` tells you exactly which rule fired and where. Exit 0 = at least one path is ignored, 1 = none.

## Hooks

Hooks are executables Git runs at lifecycle points. They live in `$GIT_DIR/hooks/` (relocatable via `core.hooksPath`), must have the **executable bit set**, and a name with **no extension**. Git ships disabled `*.sample` examples there. A **non-zero exit** from a "pre-" hook aborts the operation.

```bash
ls "$(git rev-parse --git-path hooks)"           # see this repo's hooks
git config set core.hooksPath ~/.git-hooks       # share one hooks dir across many repos
chmod +x .git/hooks/pre-commit                   # remember: must be executable
```

### Client-side hooks

| Hook | Fires on | Input | Notes |
|------|----------|-------|-------|
| `pre-commit` | `git commit` | none | abort commit on non-zero; **bypassable** with `--no-verify` |
| `prepare-commit-msg` | before the editor opens | msg-file, source, [commit-oid] | edit the message; **not** suppressed by `--no-verify` |
| `commit-msg` | after message entered | msg-file | validate/normalize the message; **bypassable** with `--no-verify` |
| `post-commit` | after commit | none | notification only; can't abort |
| `pre-merge-commit` | `git merge` (auto-commit) | none | bypassable with `--no-verify` |
| `pre-rebase` | `git rebase` | upstream, [branch] | block a rebase |
| `post-checkout` | `checkout`/`switch`/`clone`/`worktree add` | prev-HEAD, new-HEAD, flag (1=branch,0=file) | set up worktree state |
| `post-merge` | after a merge (incl. `pull`) | squash-flag | restore worktree metadata |
| `pre-push` | `git push` | remote-name, remote-url **+ stdin** | inspect refs before push; abort on non-zero |
| `pre-auto-gc` | `git gc --auto` | none | veto background gc |

`pre-push` reads one line per ref on **stdin**: `<local-ref> SP <local-oid> SP <remote-ref> SP <remote-oid>`. A deletion arrives as `(delete)` with an all-zero local oid; a not-yet-existing remote ref has an all-zero remote oid. Typical use: block pushing WIP commits or non-fast-forwards.

```bash
#!/bin/sh
# .git/hooks/pre-push — reject pushing commits whose subject starts with WIP
while read local_ref local_oid remote_ref remote_oid; do
    [ "$local_oid" = "$(printf '0%.0s' $(seq 40))" ] && continue   # deletion
    if git rev-list "$remote_oid..$local_oid" --grep '^WIP' --format=%H | grep -q .; then
        echo "Refusing to push WIP commits to $remote_ref" >&2
        exit 1
    fi
done
```

For *commit-message* validation in `commit-msg` (Conventional Commits, ticket refs), use the **conventional-commits** skill rather than hand-rolling format rules.

**Footgun:** `--no-verify` (or `-n`) skips `pre-commit`, `pre-merge-commit`, and `commit-msg` — so client hooks are advisory, never a security boundary. Enforce real policy server-side.

### Server-side hooks

Run by `git receive-pack` on the receiving repo during a push; they always execute in `$GIT_DIR`.

| Hook | Fires | Input | Notes |
|------|-------|-------|-------|
| `pre-receive` | once, before any ref updates | stdin: `<old-oid> SP <new-oid> SP <ref>` per ref | non-zero rejects the **entire** push |
| `update` | once **per ref**, before that ref updates | args: `<ref> <old-oid> <new-oid>` | non-zero rejects just that ref; classic place to enforce fast-forward-only |
| `post-receive` | once, after all updates | stdin like `pre-receive` | notifications/CI; can't abort |
| `post-update` | after updates | args: updated ref names | legacy; `post-receive` supersedes it |

```bash
#!/bin/sh
# hooks/update — enforce fast-forward-only on main
refname=$1 old=$2 new=$3
if [ "$refname" = "refs/heads/main" ]; then
    base=$(git merge-base "$old" "$new")
    [ "$base" = "$old" ] || { echo "main is protected: non-fast-forward rejected" >&2; exit 1; }
fi
```

Push options are exposed as `GIT_PUSH_OPTION_COUNT` / `GIT_PUSH_OPTION_0…`. (Hosting platforms like GitHub/GitLab don't expose raw server hooks — use their protected-branch rules / CI instead.)

## Aliases

Two flavors. **Git-subcommand aliases** just substitute git commands:

```bash
git config set --global alias.co switch
git config set --global alias.st "status -sb"
git config set --global alias.last "log -1 --stat"
git config set --global alias.unstage "restore --staged"
```

**Shell aliases** start with `!` and run an arbitrary command (from the repo root):

```bash
git config set --global alias.root '!pwd'
git config set --global alias.aliases '!git config get --regexp ^alias\\. '
# Positional args: wrap in a function, because the alias text is appended verbatim:
git config set --global alias.ignore '!f() { curl -sL https://www.gitignore.io/api/$@; }; f'
```

**Footgun:** in a plain (non-`!`) alias, any trailing arguments you pass are *appended* after the expansion — so `alias.co = checkout` makes `git co -b x` become `git checkout -b x` (fine), but you cannot put an argument *before* the appended args. When you need argument *placement* or shell features, use the `!f() { …; }; f` function pattern. Also: an alias **cannot shadow a built-in command** (e.g. you can't redefine `git commit`), and `!`-aliases run from the worktree top level, not your CWD.
