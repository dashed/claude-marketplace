# fd Advanced Recipes

Real-world recipes for command execution, exclusion, and integrating `fd` with
other tools. This is the deep layer — for the basics (pattern search, `-t`,
`-e`, `-d`, `-H`, `-g`) see `SKILL.md`.

> **Version note:** A few features below were added in specific fd releases —
> `--format` (fd 10.1+), `--hyperlink` (fd 10.2+), `--batch-size` (fd 8.3+),
> `--and` (fd 8.6+), multiple `-x`/`-X` per invocation (fd 8.4+), and the
> `--strip-cwd-prefix=<when>` argument (fd 10.1+; the bare flag is fd 8.3+).
> These are flagged inline. Everything else (`-x`/`-X`, the five placeholders,
> `-E`/`--exclude`, `.fdignore`, `-u`/`-uu`, `-0`/`--print0`, `-j`/`--threads`)
> is long-standing. For the full feature → version map, see
> [references/version-features.md](version-features.md).
>
> Recipes here are documented against **fd 10.4.2**. Newer-flag examples were
> verified against the upstream `src/cli.rs` and `doc/fd.1` (not run locally —
> a local fd may be older). Confirm on your system with `fd --version`.

## Table of Contents

- [Command Execution in Depth](#command-execution-in-depth)
  - [`-x` (parallel) vs `-X` (batch)](#-x-parallel-vs--x-batch)
  - [Placeholder syntax](#placeholder-syntax)
  - [Terminating the command template](#terminating-the-command-template)
  - [Multiple commands per run](#multiple-commands-per-run)
  - [Controlling parallelism](#controlling-parallelism)
  - [`--batch-size`](#--batch-size)
  - [Execution patterns](#execution-patterns)
- [Excluding Files and Directories](#excluding-files-and-directories)
- [Integration Recipes](#integration-recipes)
  - [fd + fzf](#fd--fzf)
  - [fd + ripgrep](#fd--ripgrep)
  - [fd + xargs / parallel](#fd--xargs--parallel)
  - [fd + git](#fd--git)
  - [Printing as a tree](#printing-as-a-tree)
  - [`--format` templating](#--format-templating-fd-101)
  - [Terminal hyperlinks](#terminal-hyperlinks-fd-102)
- [Troubleshooting](#troubleshooting)

## Command Execution in Depth

Instead of just printing results, `fd` can run a command for each one. There
are two modes, and choosing the right one matters for both correctness and
speed.

### `-x` (parallel) vs `-X` (batch)

| | `-x` / `--exec` | `-X` / `--exec-batch` |
|---|---|---|
| Invocations | **one per result** | **one total** |
| Arguments | each command gets a single path | all paths passed as arguments at once |
| Parallelism | runs in parallel across threads | single process |
| Analogous to | `find -exec cmd {} \;` | `find -exec cmd {} +` / `... \| xargs cmd` |
| Use when | per-file transforms (convert, chmod, format) | aggregating tools (`rm`, `wc`, `ls`, `rg`, `tar`) |

```bash
# -x: run convert once per jpg, in parallel
fd -e jpg -x convert {} {.}.png

# -X: open ALL matches in a single editor instance
fd -g 'test_*.py' -X vim

# -X: search within a class of files by handing them all to ripgrep at once
fd -e cpp -e cxx -e h -e hpp -X rg 'std::cout'
```

Terminal output from parallel `-x` threads is **not** interleaved or garbled —
fd serializes each command's output — so `-x` is a safe way to crudely
parallelize a per-file task:

```bash
fd -tf -x md5sum > file_checksums.txt
```

### Placeholder syntax

The command template uses [GNU-Parallel](https://www.gnu.org/software/parallel/)-style
placeholders. For a result `documents/images/party.jpg`:

| Placeholder | Expands to | Example |
|---|---|---|
| `{}` | full path | `documents/images/party.jpg` |
| `{.}` | path without extension | `documents/images/party` |
| `{/}` | basename | `party.jpg` |
| `{//}` | parent directory | `documents/images` |
| `{/.}` | basename without extension | `party` |

These same five placeholders work in `-x`, `-X`, **and** `--format` (fd 10.1+).

**Implicit `{}`:** if you write no placeholder, fd appends `{}` to the end of
the template automatically. So `fd -e zip -x unzip` is equivalent to
`fd -e zip -x unzip {}`.

**Escaping braces:** use `{{` and `}}` for literal `{` and `}`. This matters
when the command itself needs braces (e.g. an `awk` program or a shell brace
expansion). In fd 10.x, `-x`/`-X`/`--format` share one template parser, so
`{{}}` yields the literal text `{}`:

```bash
# Prints "processing {}: <path>" for each result
fd -e log -x sh -c 'echo "processing {{}}: {}"'
```

> Verified against fd 10.4.2 source (`src/exec/mod.rs` routes the template
> through `FormatTemplate::parse`, which unescapes `{{`/`}}`). **Older fd
> (≤ ~8.x) did not unescape braces in `-x`/`-X` mode** — there `{{}}` matched
> the inner `{}` and substituted the path. If you target old fd, avoid relying
> on brace escaping in exec templates.

> **There are no positional placeholders.** fd has only the five tokens above —
> unlike fzf or GNU parallel, `{1}`, `{2}`, `{n}` do **not** exist. To use a
> field of the path, wrap the command in a shell (`-x sh -c '... {} ...'`).

### Terminating the command template

Everything after `-x`/`-X` is treated as part of the command — including what
look like fd options. To continue with more fd arguments after the template,
terminate it with `\;` (most shells require the backslash):

```bash
# `pattern path` here are fd args, NOT echo args
fd -x echo \; pattern path
```

In practice it's clearer to just put `-x`/`-X` **last**:

```bash
fd pattern path -x echo
```

### Multiple commands per run

You can pass `-x`/`-X` more than once *(fd 8.4+)*; every result runs through
each command in order. All but the last template must be ended with `\;`:

```bash
# For each result: first print it, then word-count it
fd -e md -x echo "==> {}" \; -x wc -l {}
```

### Controlling parallelism

`-x` parallelizes across `-j`/`--threads` workers. Force serial execution when
order or shared-resource contention matters:

```bash
fd -e jpg -x convert {} {.}.png        # parallel (default: all cores)
fd -j 4 -e jpg -x convert {} {.}.png   # cap at 4 workers
fd --threads=1 -e jpg -x convert {} {.}.png  # strictly serial
```

`-X` is always a single process, so `-j` has no effect on it.

### `--batch-size`

*(fd 8.3+; requires `-X`)* Cap the number of arguments handed to each `-X`
invocation. If results exceed the size, `-X` runs again with the remainder —
the same idea as `xargs -n`. `0` (the default) means no limit (though the OS
may still split very long command lines):

```bash
# Process at most 100 files per `mytool` invocation
fd -e txt -X --batch-size=100 mytool
```

### Execution patterns

```bash
# Bulk convert (per-file, parallel)
fd -e jpg -x convert {} {.}.png

# Bulk rename extension via a shell wrapper
fd -e jpeg -x sh -c 'mv "{}" "{.}.jpg"'

# In-place reformat C/C++ sources (-i is a clang-format arg, so -x goes last)
fd -e h -e cpp -x clang-format -i

# chmod every script
fd -e sh -x chmod +x {}

# Checksums of every file, output un-garbled despite parallelism
fd -tf -x md5sum > file_checksums.txt

# Long `ls -l`-style listing for matches (shortcut: `fd … -l`)
fd … -X ls -lhd --color=always

# Delete matching FILES — always dry-run first WITHOUT -X rm
fd -H '^\.DS_Store$' -tf -X rm
fd -H '^\.DS_Store$' -tf -X rm -i   # interactive confirmation
```

> **Deleting directories** needs `rm -r`, e.g. `fd -td node_modules -X rm -r`.
> Beware nested same-named dirs (`…/foo/bar/foo/…`): the outer `foo` may be
> removed before the inner, yielding harmless "No such file or directory"
> errors. When unsure, list first and review before adding `-X rm`.

> **Shell aliases/functions can't be exec'd.** `fd -x`/`-X` calls binaries
> directly (no shell), so `fd -x myalias` fails. Wrap it: `fd -x bash -c
> 'myfunc "$1"' _ {}` (sourcing the function first), or call the underlying
> binary.

## Excluding Files and Directories

`fd` honors `.gitignore`, `.fdignore`, and `.ignore` by default and skips
hidden files. Layered ways to narrow or widen that:

```bash
# Ad-hoc exclude by glob (repeatable)
fd -H -E .git                 # search hidden files but skip .git dirs
fd -E '*.bak' -E node_modules # multiple excludes
fd -E /mnt/external-drive     # skip a mounted path
```

**`.fdignore`** — project-local, `.gitignore` syntax, fd-specific. Drop one at
a repo root:

```
# .fdignore
/mnt/external-drive
*.bak
build/
```

**Global ignore** — applies everywhere: `~/.config/fd/ignore` (macOS/Linux) or
`%APPDATA%\fd\ignore` (Windows) *(fd 8.1+)*. A common entry is `.git/` so that
`.git` contents stay hidden even under `--hidden` (see the note below).

**Override ignore rules** to widen the search:

| Flag | Effect |
|---|---|
| `-I` / `--no-ignore` | ignore `.gitignore`/`.fdignore`/`.ignore` |
| `-u` / `--unrestricted` | `= -HI` (also show hidden) *(fd 8.4+ semantics)* |
| `-uu` | even more permissive (repeat of `-u`) |
| `--no-ignore-vcs` | ignore VCS ignore files only (`.gitignore`) |
| `--no-ignore-parent` | don't apply ignore files from parent dirs *(fd 8.3+)* |
| `--no-require-git` | apply gitignore rules even outside a git repo *(fd 8.7+)* |
| `--ignore-file <path>` | add a custom ignore file *(fd 7.0+)* |
| `--ignore-contain <name>` | skip dirs containing a named entry, e.g. `CACHEDIR.TAG` *(fd 10.4+)* |

> **`.git/` default changed across versions.** In fd 10.x, `.git/` is **not**
> auto-ignored when you pass `--hidden` — add `.git/` to your global fdignore
> to suppress it. (fd 9.x briefly auto-ignored it; reverted in 10.0.) See
> [version-features.md](version-features.md#removed-deprecated-and-changed-defaults).

**Require-at-least matching** — narrow without piping *(fd 8.6+)*:

```bash
# Files whose name matches BOTH 'foo' and '\.txt$'
fd foo --and '\.txt$'
```

## Integration Recipes

### fd + fzf

```bash
# Drive fzf's file/dir sources with fd (in ~/.bashrc or ~/.zshrc)
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_ALT_C_COMMAND='fd --type d --hidden --follow --exclude .git'

# fd's colors survive into fzf with --ansi
export FZF_DEFAULT_COMMAND="fd --type f --color=always"
export FZF_DEFAULT_OPTS="--ansi"
```

```bash
# One-shot picker with preview, open in editor
fd --type f --hidden --exclude .git |
  fzf --preview 'bat --color=always {}' \
      --bind 'enter:become($EDITOR {})'   # become(): fzf 0.38+
```

See the **fzf** skill's `references/integrations.md` for richer fd+fzf pickers.

### fd + ripgrep

`fd` selects *which files*; `rg` searches *inside* them. Hand the whole set to
one `rg` process with `-X`:

```bash
# Search only C++ sources
fd -e cpp -e cxx -e h -e hpp -X rg 'std::cout'

# Search a curated, ignore-aware file set; null-separate for safety
fd -tf -0 | xargs -0 rg 'TODO'
```

> If you just want "ripgrep but respecting my ignores," `rg` already does that
> natively. Reach for `fd … -X rg` when fd's *type/size/time* filters select a
> set ripgrep's globs can't easily express.

### fd + xargs / parallel

`fd` has built-in `-x`/`-X`, but `xargs`/`parallel` give extra control. Always
null-separate to survive spaces/newlines in paths:

```bash
# Count lines across all Rust files (NUL-safe)
fd -0 -e rs | xargs -0 wc -l

# GNU parallel, 4 jobs
fd -e jpg -0 | parallel -0 -j4 convert {} {.}.png

# Confirm before each action
fd -e tmp -0 | xargs -0 -p rm
```

`-X` vs `xargs`: `fd -X` already batches and is ignore-aware in one step;
prefer it unless you need xargs-only features (`-P`, `-p`, `-n` with prompts,
replacement in the middle of args via `-I`).

### fd + git

```bash
# Operate only on files git is tracking-or-not per fd's ignore rules,
# then act with git. Example: stage all modified Rust files fd can see.
fd -e rs -0 | xargs -0 git add

# Clean a class of generated files git would otherwise leave
fd -td -H '^__pycache__$' -X rm -r
```

> For VCS-ignore behavior **outside** a repo, add `--no-require-git`
> *(fd 8.7+)*. To deliberately include VCS-ignored files, add `--no-ignore-vcs`.

### Printing as a tree

`tree` can read a file list from stdin with `--fromfile`, so `fd` becomes a
filtered, ignore-aware front end to `tree` (which otherwise shows everything):

```bash
fd | tree --fromfile
fd --extension rs | tree --fromfile
alias as-tree='tree --fromfile'    # then: fd -e rs | as-tree
```

### `--format` templating *(fd 10.1+)*

`--format <fmt>` prints a custom line per result using the **same five
placeholders** as `-x` (`{}`, `{/}`, `{//}`, `{.}`, `{/.}`) plus `{{`/`}}`
escaping — without spawning a command. Great for generating scripts, manifests,
or rename plans:

```bash
# Emit a move plan you can review then pipe to sh
fd -e jpeg --format 'mv {} {.}.jpg'

# CSV of basename,parent
fd -tf --format '{/},{//}'

# Literal braces via {{ }}
fd -e json --format 'key {{id}} from {/}'
```

> `--format` is print-only (no execution). To *run* the generated lines, pipe
> to a shell: `fd -e jpeg --format 'mv {} {.}.jpg' | sh` — review first.
> Verified against `src/cli.rs` / `doc/fd.1`; not runnable on fd < 10.1.

### Terminal hyperlinks *(fd 10.2+)*

`--hyperlink[=when]` (alias `--hyper`) wraps each output path in an OSC 8
terminal hyperlink (`file://` URL) so supporting terminals make paths
clickable. `when` ∈ `auto`/`always`/`never` and **must use `=`**
(`--hyperlink=always`); a bare `--hyperlink` means `auto`:

```bash
fd -e pdf --hyperlink           # auto (links when output is a TTY)
fd -e pdf --hyperlink=always    # force even when piped
```

> Has no effect on `-x`/`-X` output. Verified against `src/cli.rs`; requires
> fd 10.2+ and a terminal that supports OSC 8 hyperlinks.

## Troubleshooting

**Placeholder not expanding / shell ate it.** Some shells interpret `{}`,
`{/}`, etc. before fd sees them. Quote the placeholders when needed:
`fd -x echo '{}'`. Inside a `sh -c` wrapper, quote for the inner shell too:
`fd -x sh -c 'mv "{}" "{.}.bak"'`.

**Expecting `{1}`/`{2}`.** fd has **no positional placeholders** — only the
five path tokens. Split fields inside a shell wrapper instead.

**Regex vs glob.** The pattern is a **regex by default**; `*` and `?` are regex
metacharacters, not globs. Use `-g`/`--glob` for shell-style globs:

```bash
fd '^test_.*\.py$'      # regex
fd -g 'test_*.py'       # glob (what most people mean)
```

With `-g` **and** `-p`/`--full-path`, a single `*` no longer crosses `/` — use
`**` for that *(fd 8.0+ change)*.

**Colors disappear when piping.** fd disables color when output isn't a TTY.
Force it and tell the pager to interpret escapes:

```bash
fd -e rs --color=always | less -R
```

(Also: `NO_COLOR` in the environment disables color entirely *(fd 7.5+)*.)

**Leading `./` in exec/print0 output.** Under `-x`/`-X`/`-0`, fd prefixes
results with `./`. Strip it with `--strip-cwd-prefix` *(bare flag fd 8.3+)*; the
`=always|never|auto` argument is **fd 10.1+** and requires `=`:

```bash
fd -0 -tf --strip-cwd-prefix | xargs -0 some-tool
fd -tf --strip-cwd-prefix=never -x echo {}   # keep the ./ explicitly (10.1+)
```

**`-X rm` deleted nothing / wrong things.** `-X rm` removes **files**; add
`-r` for directories. Always run the bare `fd …` query (or `… -X echo`) first
to preview the match set.

**Duration filters and `M`.** *(fd 10.3+)* `--changed-within`/`--changed-before`
switched to the `jiff` date parser: `M` no longer means "month" — use
`mo`/`month`/`months` (e.g. `--changed-within 2mo`). See
[version-features.md](version-features.md#removed-deprecated-and-changed-defaults).
