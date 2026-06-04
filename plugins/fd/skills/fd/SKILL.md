---
name: fd
description: A fast, user-friendly command-line tool for finding files and directories by name — a simpler, faster `find` replacement. Use when searching for files or directories by name or regex/glob pattern, filtering results by type, extension, size, or modified time, respecting .gitignore, or running a command per result with -x/-X. Triggers on mentions of the fd command, fdfind, "find files named", "search for a file", or replacing `find`. This is the fd CLI tool, NOT the file-search MCP server.
---

# fd - Fast File and Directory Search

## Overview

fd is a program to find entries in your filesystem. It is a fast, ergonomic alternative to `find`: you type `fd PATTERN` and it recursively searches the current directory for entries whose name matches `PATTERN`. The pattern is a **regular expression by default**.

**Key characteristics:**
- **Fast**: Parallel directory traversal; typically much faster than `find`
- **Sensible defaults**: Smart-case matching, colorized output, and `.gitignore`/`.fdignore`/hidden-file awareness out of the box
- **Ergonomic syntax**: `fd foo` instead of `find -iname '*foo*'`
- **Composable**: Run a command per result (`-x`) or batched (`-X`), or pipe into fzf, ripgrep, xargs, and git

## When to Use This Skill

Use fd when:
- **Finding files/directories by name**: `fd readme`, `fd '\.rs$'`
- **Replacing `find`**: Any `find`-style traversal — fd is faster and the syntax is simpler
- **Filtering by metadata**: by type (`-t`), extension (`-e`), size (`-S`), or modified time (`--changed-within`)
- **Respecting (or ignoring) VCS rules**: skip `.gitignore`d files by default, or include them with `-I`/`-u`
- **Running a command per result**: `fd -e jpg -x convert {} {.}.png` or batched with `-X`
- **Feeding other tools**: as a fast source list for fzf, ripgrep, xargs, or GNU parallel

> **Disambiguation:** This skill documents the **fd command-line tool**. It is unrelated to the `file-search` MCP server plugin (which exposes `search_files`/`filter_files` tools).

## Prerequisites

**CRITICAL**: Before proceeding, you MUST verify that fd is installed:

```bash
fd --version
```

**The binary name varies by platform:**
- On most systems the binary is **`fd`**.
- On **Debian/Ubuntu** the package is `fd-find` and the binary is installed as **`fdfind`** (the name `fd` is used by another package). Either invoke `fdfind`, or add an alias: `alias fd=fdfind`.

**Version note:** This skill is documented against **fd 10.4.x** (source: v10.4.2). Long-standing basics work on any recent fd; features added in a specific release are annotated inline as `(fd X.Y+)`. For the version that introduced any specific flag, see [references/version-features.md](references/version-features.md). Always confirm on the running system with `fd --version`.

**If fd is not installed:**
- **DO NOT** attempt to install it automatically
- **STOP** and inform the user that fd is required
- **RECOMMEND** manual installation with the following instructions:

```bash
# macOS
brew install fd

# Debian/Ubuntu (binary is `fdfind`)
sudo apt install fd-find

# Arch Linux
sudo pacman -S fd

# Fedora
sudo dnf install fd-find

# Cargo (any platform)
cargo install fd-find

# Other systems: see https://github.com/sharkdp/fd#installation
```

**If fd is not available, exit gracefully and do not proceed with the workflow below.**

## Basic Usage

```bash
# Recursively search the current directory for entries matching a regex
fd PATTERN

# Search within a specific directory (pattern first, path second)
fd PATTERN path/to/dir

# List everything under the current directory (no pattern = match all)
fd

# List everything under a given directory
fd . path/to/dir
```

**Smart-case** is the default: the search is case-insensitive unless the pattern contains an uppercase letter, in which case it becomes case-sensitive. Override with `-s`/`--case-sensitive` or `-i`/`--ignore-case`.

By default, the pattern matches against the **file name only** (not the full path), as a substring/regex match — `fd app` matches `app.js`, `myapp/`, and `mapping.txt`.

## Pattern Syntax

### Regex (default)

The pattern is a regular expression (Rust `regex` crate syntax):

```bash
fd '^x'           # names starting with x
fd '\.py$'        # names ending in .py (escape the dot)
fd '[0-9]{4}'     # names containing 4 consecutive digits
```

### Glob mode (`-g`/`--glob`)

Switch to glob patterns with `-g`. Use `--regex` to switch back (handy if you `alias fd='fd --glob'`).

```bash
fd -g '*.txt'
fd -g 'test_*.py'
```

### Match against the full path (`-p`/`--full-path`)

By default fd matches the file name. With `-p`, the pattern is tested against the **full path**:

```bash
fd -p '.*/test/.*\.py$'          # regex over the whole path
fd -p -g '**/src/**/*.rs'        # glob over the whole path
```

> With `-g` **and** `-p` together, a single `*` no longer matches `/`; use `**` to cross directory separators (fd 8.0+).

### Literal strings (`-F`/`--fixed-strings`)

Treat the pattern as a literal string, not a regex:

```bash
fd -F 'file(1).txt'
```

## Filtering

### By type (`-t`/`--type`)

```bash
fd -t f PATTERN    # files only
fd -t d PATTERN    # directories only  (-t dir also works, fd 10.0+)
fd -t l PATTERN    # symlinks
fd -t x PATTERN    # executable files            (fd 7.0+)
fd -t e PATTERN    # empty files/directories      (fd 7.1+)
fd -t s            # sockets (fd 8.0+);  -t p pipes (fd 8.0+)
fd -t b / -t c     # block / char devices         (fd 9.0+)
```

Multiple `-t` values are OR'd: `fd -t f -t l` matches files **and** symlinks.

### By extension (`-e`/`--extension`)

```bash
fd -e txt                 # all .txt files
fd -e jpg -e png          # .jpg or .png (repeatable)
fd -e py PATTERN          # combine with a pattern
```

### Hidden and ignored files

By default fd **skips hidden files/directories and anything matched by `.gitignore`/`.fdignore`/`.ignore`**.

```bash
fd -H PATTERN     # include hidden files (--hidden)
fd -I PATTERN     # ignore .gitignore/.fdignore rules (--no-ignore)
fd -u PATTERN     # unrestricted: -u = -HI; -uu also disables --ignore-vcs
```

> **`.git/` behavior:** in fd 10.x, `.git/` is **not** auto-ignored when you use `-H` (this reverts a 9.0 change). Add `.git/` to your global fdignore file if you want it skipped. (fd 10.0+)

Custom ignore files: `--ignore-file <path>` (fd 7.0+) adds a `.gitignore`-format file. `--no-ignore-vcs` disables only VCS ignore files. `--no-require-git` (fd 8.7+) applies git-ignore rules even outside a repository.

### By depth

```bash
fd -d 2 PATTERN              # --max-depth: descend at most 2 levels
fd --min-depth 3 PATTERN     # at least 3 levels deep      (fd 8.0+)
fd --exact-depth 2 PATTERN   # exactly 2 levels deep        (fd 8.0+)
fd --prune PATTERN           # match dirs but don't descend (fd 8.2+)
```

### By size (`-S`/`--size`) (fd 7.1+)

Format is `<+-><NUM><UNIT>`. `+` means "at least", `-` means "at most"; an exact size (no sign) is also accepted (fd 8.2+).

```bash
fd -S +1M           # larger than 1 MiB
fd -S -100k         # smaller than 100 KiB
fd -S +10M -S -1G   # between 10 MiB and 1 GiB
```

Units: `b`, `k`/`m`/`g`/`t` (decimal SI) and `ki`/`mi`/`gi`/`ti` (binary).

### By modification time (fd 7.2+)

```bash
fd --changed-within 2weeks   # modified in the last 2 weeks (alias --newer)
fd --changed-before 1d       # modified more than 1 day ago (alias --older)
fd --changed-within 2025-01-01
fd --changed-before @1704067200   # Unix-epoch timestamp (fd 10.0+)
```

> **Duration units changed in fd 10.3+:** `M` no longer means "month" (it's ambiguous with minutes). Use `mo`/`month`/`months`. This affects `--changed-within`/`--changed-before`.

## Command Execution

fd can run a command for each result instead of printing it. **Use `-x`/`-X`, not find's `-exec`** — fd does not support `-exec` (it was removed in fd 8.0).

### Per-result, in parallel (`-x`/`--exec`)

Runs the command **once per result**, in parallel:

```bash
fd -e zip -x unzip                 # unzip each .zip file
fd -e jpg -x convert {} {.}.png    # convert each .jpg to .png
fd -t f -x echo                    # echo each result (implicit {} at end)
```

Use `--threads=1` (or `-j 1`) for sequential execution. Multiple `-x` blocks may be given in one invocation (fd 8.4+).

### Batched (`-X`/`--exec-batch`)

Runs the command **once**, passing all results as arguments (like `xargs`):

```bash
fd -e rs -X wc -l            # count lines across all .rs files
fd -g 'test_*.py' -X vim     # open all matches in one editor session
```

Cap arguments per invocation with `--batch-size <n>` (fd 8.3+).

### Placeholders

These are substituted in the command template (for both `-x` and `-X`). If no placeholder is present, an implicit `{}` is appended.

| Placeholder | Expands to |
|-------------|------------|
| `{}` | Full path of the result |
| `{/}` | Basename (file name only) |
| `{//}` | Parent directory |
| `{.}` | Path without file extension |
| `{/.}` | Basename without extension |

Escape literal braces with `{{` and `}}`. fd has **no `{n}` numbered-field placeholder** (that is an fzf feature, not fd).

```bash
fd -e md -x echo '{//}'    # print each match's parent directory
fd -e log -x mv {} {//}/archive/{/}
```

> Under `-x`/`-X`/`-0`, fd prefixes paths with `./`. Strip it with `--strip-cwd-prefix` (fd 8.3+; takes an optional `=always|never|auto` arg in fd 10.1+).

## Output

```bash
fd -l PATTERN              # ls -l-style long listing       (fd 8.0+)
fd -0 PATTERN              # NUL-separated output (--print0), pairs with xargs -0
fd -a PATTERN              # print absolute paths (--absolute-path)
fd -1 PATTERN              # quit after the first match (= --max-results=1, fd 8.0+)
fd --max-results 5 PATTERN # stop after N matches             (fd 8.0+)
fd -q PATTERN              # quiet: print nothing, exit 0 if any match (fd 8.3+)
```

### Format templates (`--format`) (fd 10.1+)

Print each result through a template using the same placeholders as `-x` (`{}`, `{/}`, `{//}`, `{.}`, `{/.}`) — without spawning a process:

```bash
fd -e flac --format '{/.}'             # just the basenames, no extension
fd -e mp3 --format 'file://{}'         # build URIs
```

### Color and hyperlinks

```bash
fd -c always PATTERN       # force color (auto|always|never); NO_COLOR is honored
fd --hyperlink PATTERN     # OSC 8 terminal hyperlinks on paths (fd 10.2+)
```

## Common Workflows

```bash
# Delete all .DS_Store files
fd -H -t f -g '.DS_Store' -X rm

# Find large files (>50 MiB) modified in the last week
fd -t f -S +50M --changed-within 1week

# List every directory two levels down
fd -t d --exact-depth 2

# Find TODO-containing Rust files, edit them all at once
fd -e rs -X grep -l TODO | xargs $EDITOR

# Touch-rebuild: re-run a build command per changed source file
fd -e c --changed-within 10min -x cc -c {}
```

## Integration

fd shines as a fast file-list source for other tools.

```bash
# fzf — fd as the source list (also the recommended FZF_DEFAULT_COMMAND)
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'
fd -t f | fzf

# ripgrep — restrict a content search to fd-selected files (NUL-safe)
fd -e py -0 | xargs -0 rg 'def main'

# xargs — always pair fd -0 with xargs -0 to handle spaces/newlines
fd -e tmp -0 | xargs -0 rm

# GNU parallel — one job per result
fd -e png -0 | parallel -0 optipng {}

# git — operate on tracked-but-matching files
fd -e js -X git add
```

> Prefer `fd -0 | xargs -0 …` over `fd … | xargs …` whenever paths may contain spaces or newlines. For one command per result, `fd -x` is usually simpler than piping to xargs.

## Troubleshooting

**"Command not found: fd"**
- On Debian/Ubuntu the binary is **`fdfind`** — try `fdfind --version`, or `alias fd=fdfind`.
- Otherwise fd is not installed. See Prerequisites for manual installation. Do NOT auto-install.

**"My file isn't found":**
- It may be **hidden** or **`.gitignore`d**. Add `-H` (hidden), `-I` (ignore VCS rules), or `-u`/`-uu` (unrestricted).
- The pattern matches the **name**, not the path — use `-p`/`--full-path` to match against the whole path.
- The pattern is a **regex** by default; special characters like `.`, `(`, `+` need escaping, or use `-F` for a literal string / `-g` for a glob.

**"`fd -exec` doesn't work":**
- fd has no `-exec` (a find-ism, removed in 8.0). Use `-x` (per result) or `-X` (batched).

**"Too many / unexpected results":**
- Constrain with `-t` (type), `-e` (extension), `-d` (max depth), or `--max-results`.

**A flag from older docs is missing or behaves differently:**
- See [references/version-features.md](references/version-features.md) for version introductions and changed defaults (e.g. the `./`-prefix history, `.git/` ignoring, `M`→`mo` duration change).

## References

For exhaustive detail, see the bundled reference files:

- [references/options.md](references/options.md) — complete flag reference (every option, grouped by area)
- [references/recipes.md](references/recipes.md) — command-execution patterns, integrations, and worked recipes
- [references/version-features.md](references/version-features.md) — which fd version introduced each feature, plus removed/changed defaults (minimum-version lookup)

## Resources

- **Man page**: `man fd` or `fd --help`
- **GitHub**: https://github.com/sharkdp/fd
- **User guide (README)**: https://github.com/sharkdp/fd#how-to-use
