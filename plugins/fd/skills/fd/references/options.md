# fd Options Reference

Complete reference for fd's command-line flags, grouped by area.

> **Version annotations:** Flags marked `(fd X.Y+)` require at least that fd version; unmarked flags are long-standing basics (predate ~fd 7.0). For the consolidated feature→version lookup (and removed/changed defaults), see [references/version-features.md](version-features.md). This reference is documented against **fd 10.4.x** (verified against v10.4.2 source) — confirm on your system with `fd --version`, then `man fd` or `fd --help`. Flags that exist only on the upstream `master` branch (e.g. `--exact`, the `--ignore-parent` override) are intentionally **excluded** — they are not in a tagged release as of 10.4.2.

## Usage

```
fd [OPTIONS] [pattern] [path...]
fd [OPTIONS] --search-path <path> --search-path <path2> [pattern]
```

- `pattern` — regular expression (default) or glob (with `--glob`); optional. If omitted, every entry matches. If it starts with `-`, pass `--` first: `fd -- '-foo'`.
- `path...` — one or more root directories to search (default: current directory).

## Table of Contents

- [Search & Pattern](#search--pattern)
- [Type, Extension & Attribute Filters](#type-extension--attribute-filters)
- [Time & Owner Filters](#time--owner-filters)
- [Ignore & Hidden Files](#ignore--hidden-files)
- [Traversal & Depth](#traversal--depth)
- [Command Execution](#command-execution)
- [Output & Formatting](#output--formatting)
- [Environment Variables](#environment-variables)
- [Notable Conflicts & Groups](#notable-conflicts--groups)

## Search & Pattern

| Flag | Description |
|------|-------------|
| `-g, --glob` (fd 7.4+) | Glob-based search instead of regex |
| `--regex` | Regular-expression search (default); overrides `--glob` |
| `-F, --fixed-strings` | Treat pattern as a literal string (substring match); alias `--literal` |
| `--and <pattern>` (fd 8.6+) | Additional pattern that must *also* match; repeatable. Regex unless `--glob`/`--fixed-strings` |
| `-p, --full-path` | Match the pattern against the full path, not just the filename |
| `-s, --case-sensitive` | Force case-sensitive search (overrides smart case) |
| `-i, --ignore-case` | Force case-insensitive search (overrides smart case) |

Default matching is **smart-case**: case-insensitive unless the pattern contains an uppercase character. `-s` and `-i` override each other (last wins).

## Type, Extension & Attribute Filters

| Flag | Description |
|------|-------------|
| `-t, --type <filetype>` | Filter by entry type; repeatable to include multiple types |
| `-e, --extension <ext>` | Filter by file extension; repeatable |
| `-S, --size <±NUM[UNIT]>` (fd 7.1+) | Filter by file size; repeatable. Exact sizes (no `+`/`-`) since fd 8.2+ |

**`--type` values** (each has a short alias):

| Value | Alias | Matches |
|-------|-------|---------|
| `file` | `f` | Regular files |
| `directory` / `dir` (fd 10.0+) | `d` | Directories |
| `symlink` | `l` | Symbolic links |
| `executable` (fd 7.0+) | `x` | Executable files (implies `--type file`; on Unix, executable by the current user since fd 8.6+) |
| `empty` (fd 7.1+) | `e` | Empty files and/or directories |
| `socket` (fd 8.0+) | `s` | Sockets |
| `pipe` (fd 8.0+) | `p` | Named pipes (FIFOs) |
| `block-device` (fd 9.0+) | `b` | Block devices |
| `char-device` (fd 9.0+) | `c` | Character devices |

`--type empty` searches both empty files and directories unless you also pass `--type file` or `--type directory`.

**`--size` units** (case-insensitive): `b` bytes; `k`/`m`/`g`/`t` base-10 (kilo/mega/giga/tera); `ki`/`mi`/`gi`/`ti` base-2 (kibi/mebi/gibi/tebi). Prefix `+` = at least, `-` = at most, none = exactly. Example: `-S +10m -S -1g`.

## Time & Owner Filters

| Flag | Description |
|------|-------------|
| `--changed-within <date\|dur>` (fd 7.2+) | Only entries modified **after** the given time; aliases `--change-newer-than`, `--newer`, `--changed-after` (fd 8.6+) |
| `--changed-before <date\|dur>` (fd 7.2+) | Only entries modified **before** the given time; aliases `--change-older-than`, `--older` |
| `-o, --owner <[user][:group]>` (fd 8.1+, Unix only) | Filter by owning user and/or group; prefix either side with `!` to exclude |

Time arguments accept a point in time (`YYYY-MM-DD HH:MM:SS`, `YYYY-MM-DD`, or `@<unix-epoch>` since fd 10.0+) or a duration (`10h`, `1d`, `2weeks`, `35min`). **fd 10.3+** (jiff crate): in durations `M` no longer means "month" — use `mo`/`month`/`months`.

## Ignore & Hidden Files

| Flag | Description |
|------|-------------|
| `-H, --hidden` | Include hidden files and directories (names starting with `.`) |
| `-I, --no-ignore` | Don't respect `.gitignore`, `.ignore`, `.fdignore`, or the global ignore file |
| `--no-ignore-vcs` | Don't respect `.gitignore` files (still honors `.fdignore`/`.ignore`) |
| `--no-ignore-parent` (fd 8.3+) | Don't apply ignore files from parent directories |
| `--no-require-git` (fd 8.7+) | Respect gitignore rules even outside a git repository |
| `--no-global-ignore-file` | Don't read the global ignore file (`$XDG_CONFIG_HOME/fd/ignore`) |
| `-u, --unrestricted` | Unrestricted search; alias for `--no-ignore --hidden`. Repeatable (`-uu`) |
| `--ignore-file <path>` (fd 7.0+) | Add a custom `.gitignore`-format ignore file (low precedence); repeatable |
| `-E, --exclude <glob>` | Exclude entries matching a glob (overrides all ignore logic); repeatable |
| `--ignore-contain <name>` (fd 10.4+) | Ignore directories that contain an entry with the given name (e.g. `CACHEDIR.TAG`); repeatable |
| `--prune` (fd 8.2+) | Match directories but don't descend into them |

Since fd 8.4+, a single `-u` is equivalent to `-HI`; extra `-u`s are accepted but ignored.

**Override ("opposing") flags** (fd 8.3+) cancel an earlier flag — useful in shell aliases:

| Flag | Cancels |
|------|---------|
| `--no-hidden` | `--hidden` |
| `--ignore` | `--no-ignore` |
| `--ignore-vcs` | `--no-ignore-vcs` |
| `--require-git` | `--no-require-git` |
| `--relative-path` | `--absolute-path` |
| `--no-follow` | `--follow` |

## Traversal & Depth

| Flag | Description |
|------|-------------|
| `-d, --max-depth <depth>` | Limit traversal depth (default: unlimited); alias `--maxdepth` |
| `--min-depth <depth>` (fd 8.0+) | Only show results at or below the given depth; alias `--mindepth` (fd 10.3+) |
| `--exact-depth <depth>` (fd 8.0+) | Only show results at exactly this depth (= `--min-depth N --max-depth N`) |
| `-L, --follow` | Follow symbolic links; alias `--dereference` |
| `--one-file-system` (fd 7.5+) | Don't cross filesystem boundaries; aliases `--mount`, `--xdev` (Unix/Windows) |
| `-C, --base-directory <path>` (fd 7.5+) | Change fd's working directory before searching |
| `-j, --threads <num>` | Number of threads for searching & executing (default: CPU cores, capped at 64) |
| `--search-path <path>` (fd 7.2+) | Supply search roots as an option instead of positional args; repeatable |

## Command Execution

| Flag | Description |
|------|-------------|
| `-x, --exec <cmd> [;]` | Run a command for each result, in parallel. Multiple `-x` allowed (fd 8.4+) |
| `-X, --exec-batch <cmd> [;]` (fd 7.3+) | Run one command with all results as arguments (xargs-style) |
| `--batch-size <size>` (fd 8.3+) | Max arguments per `--exec-batch` invocation (`0` = no limit); requires `-X` |

**Placeholders** (in `-x`/`-X` command templates): `{}` full path · `{/}` basename · `{//}` parent directory · `{.}` path without extension · `{/.}` basename without extension · `{{`/`}}` literal braces. If no placeholder is present, an implicit `{}` is appended. Use `\;` to terminate the template and continue passing fd arguments. Use `--threads=1` for sequential `-x` execution.

## Output & Formatting

| Flag | Description |
|------|-------------|
| `-l, --list-details` (fd 8.0+) | `ls -l`-style long output with metadata and deterministic order |
| `--format <fmt>` (fd 10.1+) | Print each result via a format template (`{}`, `{/}`, `{//}`, `{.}`, `{/.}`) |
| `-0, --print0` | Separate results with the null character (for `xargs -0`) |
| `-a, --absolute-path` | Print absolute instead of relative paths |
| `-c, --color <when>` | When to colorize: `auto` (default), `always`, `never` |
| `--hyperlink[=when]` (fd 10.2+) | Emit OSC 8 terminal hyperlinks; `when` ∈ `auto`/`always`/`never` (bare = `auto`); alias `--hyper` |
| `--path-separator <sep>` (fd 7.4+) | Override the OS path separator in output |
| `--strip-cwd-prefix[=when]` (fd 8.3+) | Drop the leading `./` added under `-x`/`-X`/`-0`; optional `always`/`never`/`auto` arg requires `=` (fd 10.1+) |
| `--max-results <count>` (fd 8.0+) | Stop after `count` matches |
| `-1` (fd 8.0+) | Stop after the first match (alias for `--max-results=1`) |
| `-q, --quiet` (fd 8.3+) | Print nothing; exit 0 if any match, 1 otherwise; alias `--has-results` |
| `--show-errors` (fd 7.2+) | Surface filesystem errors (permission denied, dead symlinks) |

Color output also honors `--color` together with the `LS_COLORS` and `NO_COLOR` environment variables.

## Environment Variables

| Variable | Effect |
|----------|--------|
| `LS_COLORS` | Colors for search results (see `dircolors(1)`) |
| `NO_COLOR` (fd 7.5+) | Disables colorized output when set |
| `XDG_CONFIG_HOME` / `HOME` | Locate the global ignore file: `$XDG_CONFIG_HOME/fd/ignore`, else `$HOME/.config/fd/ignore` |

## Notable Conflicts & Groups

- **Execution group** — `-x/--exec`, `-X/--exec-batch`, and `-l/--list-details` are mutually exclusive, and all three conflict with `--max-results`, `-q/--quiet`, and `-1`.
- `-g/--glob` conflicts with `-F/--fixed-strings`.
- `-l/--list-details` conflicts with `-a/--absolute-path`; `--format` and `-0/--print0` each conflict with `-l/--list-details`.
- `--prune` conflicts with `-S/--size` and `--exact-depth`.
- `--exact-depth` conflicts with `-d/--max-depth` and `--min-depth`.
- `--search-path` conflicts with the positional `path` argument; `--strip-cwd-prefix` conflicts with any path / `--search-path`.
- `--batch-size` requires `-X/--exec-batch`.
- `--max-results` and `-1` override each other (last wins).

## Exit Codes

- `0` — at least one match (or, under `-q/--quiet`, a match was found).
- `1` — no match (or, under `-q`, none found), or an error occurred.
