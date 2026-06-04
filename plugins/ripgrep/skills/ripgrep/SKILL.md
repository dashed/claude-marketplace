---
name: ripgrep
description: A fast, gitignore-aware command-line tool for recursively searching file contents by regular expression — a smarter, faster `grep`. Use when searching code or text for a pattern across a directory tree, filtering matches by file type or glob, listing/counting matching files, doing search-and-replace previews, or running gitignore-aware code search. Triggers on mentions of ripgrep, the `rg` command, "search the codebase for", "grep for", "find all files containing", or replacing `grep`/`ack`/`ag`. This is the rg CLI tool, NOT the fuzzy-search MCP server (which wraps rg).
---

# ripgrep - Fast Recursive Content Search

## Overview

ripgrep (`rg`) recursively searches the current directory for lines matching a regex. You type `rg PATTERN` and it walks the tree, searching file **contents** and printing matching lines with their file path and line number. The pattern is a **regular expression by default** (Rust `regex` syntax).

**Key characteristics:**
- **Fast**: Parallel directory traversal plus a fast regex engine; typically much faster than `grep -r`
- **Sensible defaults**: Recursive, smart-case, colorized, and `.gitignore`/`.ignore`/hidden-file aware out of the box — it won't search `.git/`, build artifacts, or ignored files unless you ask
- **Ergonomic syntax**: `rg foo` instead of `grep -rn foo .`
- **Composable**: `--json`, `--vimgrep`, `-0` (NUL) output, and clean piping into fzf, fd, xargs, and editors

## When to Use This Skill

Use ripgrep when:
- **Searching code/text for a pattern**: `rg 'fn main'`, `rg 'TODO|FIXME'`
- **Replacing `grep`/`ack`/`ag`**: any recursive content search — rg is faster and respects `.gitignore`
- **Restricting by file type or glob**: `rg -t py 'def '`, `rg -g '*.rs' unsafe`
- **Listing or counting matches**: which files match (`-l`), or how many (`-c`/`--count-matches`)
- **Previewing a search-and-replace**: `rg -r 'NEW' 'OLD'` (rg prints, it does not edit files)
- **Feeding other tools**: `--json` for editors/scripts, `--vimgrep` for quickfix, `-0` for `xargs -0`

> **Disambiguation:** This skill documents the **rg command-line tool**. It is unrelated to the `fuzzy-search` MCP server plugin — that plugin *wraps* rg to expose `fuzzy_search_content`/`fuzzy_search_files` tools. Here you invoke `rg` directly on the command line.

## Prerequisites

**CRITICAL**: Before proceeding, you MUST verify that ripgrep is installed:

```bash
rg --version
```

The binary is **`rg`** on every platform. The `--version` output also reports whether PCRE2 is available (needed for `-P`).

**Version note:** This skill is documented against **ripgrep 15.x** (flag set verified against the post-15.1 source). Long-standing basics work on any recent rg; features added in a specific release are annotated inline as `(rg X.Y+)`. For the version that introduced any specific flag, see [references/version-features.md](references/version-features.md). Always confirm on the running system with `rg --version`.

**If ripgrep is not installed:**
- **DO NOT** attempt to install it automatically
- **STOP** and inform the user that ripgrep is required
- **RECOMMEND** manual installation:

```bash
# macOS
brew install ripgrep

# Debian/Ubuntu
sudo apt install ripgrep

# Arch Linux
sudo pacman -S ripgrep

# Fedora
sudo dnf install ripgrep

# Cargo (any platform; add features with --features 'pcre2')
cargo install ripgrep

# Other systems: see https://github.com/BurntSushi/ripgrep#installation
```

**If ripgrep is not available, exit gracefully and do not proceed with the workflow below.**

## Basic Usage

```bash
# Recursively search the current directory for a regex
rg PATTERN

# Search within a specific path (pattern first, paths after)
rg PATTERN path/to/dir file.txt

# Search piped stdin
cat file | rg PATTERN
```

**Smart-case** is the default: the search is case-insensitive unless the pattern contains an uppercase letter, in which case it becomes case-sensitive. Override with `-s`/`--case-sensitive` or `-i`/`--ignore-case`. (When flags conflict, the **most recent wins** — `rg foo -s -i` is case-insensitive.)

By default rg prints, per matching line, the **file path, line number, and the line**, grouped under a heading per file when writing to a terminal.

## Regex Syntax

The pattern is a **Rust `regex` regular expression** by default — fast, linear-time, Unicode-aware, but with **no backreferences or look-around** (use `-P` for those).

```bash
rg '^\s*func'          # anchored, with character classes
rg 'foo(bar|baz)'      # alternation and groups
rg '\bcolou?r\b'       # word boundary + optional char
```

| Flag | Purpose |
|------|---------|
| `-F`/`--fixed-strings` | Treat the pattern as a **literal string**, not a regex |
| `-w`/`--word-regexp` | Require the match to fall on word boundaries |
| `-x`/`--line-regexp` | Require the pattern to match the **whole line** |
| `-e PATTERN` | Add a pattern (repeatable; also lets patterns start with `-`) |
| `-f FILE` | Read patterns from a file (one per line) |
| `-v`/`--invert-match` | Print **non**-matching lines |
| `-P`/`--pcre2` | Use the PCRE2 engine — enables look-around and backreferences |
| `--engine <auto\|default\|pcre2>` | Pick the engine; `auto` falls back to PCRE2 only when needed (rg 12.0+) |

### Multiline matching

By default a match cannot span lines. Enable multiline with `-U`:

```bash
rg -U 'struct\s+\w+\s*\{[^}]*\}'      # match across newlines  (rg 0.10+)
rg -U --multiline-dotall 'foo.*bar'   # let . match newlines too (rg 0.10+)
```

## File Selection

### By file type (`-t`/`-T`)

```bash
rg -t py 'import os'      # only Python files
rg -T js 'TODO'          # everything EXCEPT JavaScript  (--type-not)
rg --type-list           # show all built-in type names and their globs
rg --type-add 'web:*.{html,css,js}' -t web 'href'   # define a type on the fly
```

### By glob (`-g`/`--iglob`)

Globs apply to file **names/paths**; repeat to combine; prefix with `!` to exclude.

```bash
rg -g '*.rs' unsafe              # only .rs files
rg -g '!*_test.go' 'func '       # exclude test files
rg --iglob '*.MD' heading        # case-insensitive glob (rg 0.6+)
```

> Globs support `{a,b}` alternation, including **nested** braces like `{a,{b,c}}` (rg 15.0+).

### Hidden and ignored files

By default rg **skips hidden files/dirs and anything matched by `.gitignore`/`.ignore`/`.rgignore`** (and won't descend into `.git/`).

```bash
rg -. PATTERN      # include hidden files/dirs (--hidden, short -. is rg 13.0+)
rg -u PATTERN      # -u  = don't respect .gitignore
rg -uu PATTERN     # -uu = --no-ignore --hidden (search hidden + ignored)
rg -uuu PATTERN    # -uuu = also search binary files (rg 11.0+; like grep -r)
```

Finer control: `--no-ignore` (all ignore rules), `--no-ignore-vcs` (only VCS), `--no-ignore-dot` (`.ignore`/`.rgignore`, rg 11.0+), `--no-ignore-parent`, `--no-require-git` (apply gitignore outside a repo, rg 12.0+), `--no-ignore-global`. Follow symlinks with `-L`/`--follow`.

## Context

Print lines around each match:

```bash
rg -A 3 PATTERN     # 3 lines After
rg -B 2 PATTERN     # 2 lines Before
rg -C 2 PATTERN     # 2 lines of Context (before AND after)
```

> In rg 14.0+, `-A`/`-B` only **partially** override `-C`: `rg -C1 -A2` ≡ `rg -B1 -A2` (previously ≡ `-A2`).

## Output

```bash
rg -o PATTERN              # print only the matched part(s) of each line (--only-matching)
rg -r 'REPL' PATTERN       # print matches with replacement applied (preview only; $1/$2 refs)
rg -c PATTERN              # per-file count of matching LINES (--count)
rg --count-matches PAT     # count individual matches, not lines
rg -l PATTERN              # list only files WITH a match (--files-with-matches)
rg --files-without-match PAT  # list files with NO match
rg -n PATTERN / rg -N PAT  # force / suppress line numbers (--line-number / --no-line-number)
rg -H PAT / rg -I PAT      # force / suppress the file path (-I is --no-filename, rg 11.0+)
rg -0 -l PATTERN           # NUL-separate file names for safe piping (--null)
```

> `-r`/`--replace` only changes what is **printed** — it never modifies files. To rewrite files, pipe matched files through `sed`/`sd` or an editor (see [references/recipes.md](references/recipes.md)).

### Machine-readable and color

```bash
rg --json PATTERN          # JSON Lines events (matches, stats); ideal for editors/scripts (rg 0.10+)
rg --vimgrep PATTERN       # one match per line: file:line:col:text (quickfix-friendly)
rg --color always PATTERN  # force color (auto|always|never|ansi); honors NO_COLOR
rg --hyperlink-format default PATTERN   # OSC-8 terminal hyperlinks on paths (rg 14.0+)
```

> There is **no bare `--hyperlink` switch** — `--hyperlink-format <fmt>` (e.g. `default`, `vscode`, `file`, or a custom `{path}`/`{line}` template) is what turns paths into links (rg 14.0+).

## Sorting & Performance

```bash
rg --sort path PATTERN     # deterministic order (path|modified|accessed|created); disables parallelism
rg --sortr modified PAT    # reverse sort  (rg 0.10+)
rg -j 4 PATTERN            # cap worker threads (--threads); -j1 forces single-threaded
rg -z PATTERN              # search inside gzip/bzip2/xz/lz4/zstd/brotli archives (--search-zip)
rg --pre ./script PATTERN  # run each file through a preprocessor first (rg 0.9+)
```

> `--sort`/`--sortr` and `-z` impose ordering/decoding work; rg is fastest with its default parallel, unsorted traversal. `--pre-glob` limits which files `--pre` runs on. (Security: prefer rg 13.0+ on Windows when using `-z`/`--pre`.)

## Configuration File

Set `RIPGREP_CONFIG_PATH` to a file of default flags (one per line, `#` for comments) applied to every invocation (rg 0.8+):

```bash
export RIPGREP_CONFIG_PATH="$HOME/.config/ripgrep/ripgreprc"
```

```
# ~/.config/ripgrep/ripgreprc
--smart-case
--hidden
--glob=!.git/*
--max-columns=200
```

Bypass the config for one run with `--no-config`. Command-line flags override config-file flags.

## Common Workflows

```bash
# Find every TODO/FIXME in Python, with 2 lines of context
rg -t py -C2 'TODO|FIXME'

# Count matches per file, only files that match, sorted
rg -c 'import' -t py | sort -t: -k2 -nr

# List files containing a symbol, NUL-safe, then open in your editor
rg -l -0 'class Widget' | xargs -0 $EDITOR

# Whole-word, case-sensitive search excluding tests
rg -w -s -g '!*_test.*' 'deprecated'

# Preview a rename across the codebase (no files changed)
rg 'old_name' -l -0 | xargs -0 rg -r 'new_name' --passthru -N 'old_name'

# Search a specific commit's files via git + rg
git ls-files -z | xargs -0 rg 'pattern'
```

## Integration

```bash
# fzf — live ripgrep, feed selection to editor
rg --vimgrep '' | fzf

# fzf default source restricted to text files
export FZF_DEFAULT_COMMAND='rg --files --hidden --glob=!.git/*'

# fd — restrict a content search to fd-selected files (NUL-safe)
fd -e py -0 | xargs -0 rg 'def main'

# editors — Vim/Neovim quickfix
:grep! pattern        " with  set grepprg=rg\ --vimgrep

# git — search only tracked files
git ls-files -z | xargs -0 rg PATTERN
```

> `rg --files` lists every file rg *would* search (honoring ignore rules) — a fast, gitignore-aware file lister you can pipe anywhere. Always pair `rg -0`/`rg --files -0` with `xargs -0` when paths may contain spaces or newlines.

## Troubleshooting

**"Command not found: rg"**
- ripgrep is not installed. See Prerequisites for manual installation. Do NOT auto-install.

**"My file isn't being searched":**
- It may be **hidden** or **`.gitignore`d**. Add `-.`/`--hidden`, `-u` (ignore VCS), `-uu` (hidden + ignored), or `-uuu` (also binary). Use `rg --files` to see exactly what rg would search.
- It may be detected as **binary** — rg stops at the first NUL by default. Use `-a`/`--text` or `-uuu`.
- A built-in type filter (`-t`) may exclude it; check `rg --type-list`.

**"My regex doesn't match":**
- rg's default engine has **no backreferences or look-around** — use `-P`/`--pcre2` (requires a PCRE2-enabled build) or `--engine auto`.
- For a literal string with regex metacharacters, use `-F`/`--fixed-strings`.
- To match across lines, use `-U`/`--multiline` (and `--multiline-dotall` for `.`).

**"`rg` changed my files" — it didn't:**
- `-r`/`--replace` only changes printed output. ripgrep never edits files in place.

**"Too many / unexpected results":**
- Narrow with `-t`/`-g` (type/glob), `-w` (word), `-x` (whole line), or `--max-depth`.

**A flag from older docs is missing or behaves differently:**
- See [references/version-features.md](references/version-features.md) for version introductions and changed defaults (e.g. `--man`→`--generate`, `--auto-hybrid-regex`→`--engine auto`, `-uuu` semantics, `-A`/`-B` vs `-C`).

## References

For exhaustive detail, see the bundled reference files:

- [references/options.md](references/options.md) — complete flag reference (every option, grouped by area)
- [references/recipes.md](references/recipes.md) — search-and-replace, integrations, config, and worked recipes
- [references/version-features.md](references/version-features.md) — which rg version introduced each feature, plus removed/changed defaults (minimum-version lookup)

## Resources

- **Man page**: `man rg`, `rg --help`, or generate it with `rg --generate man` (rg 14.0+)
- **GitHub**: https://github.com/BurntSushi/ripgrep
- **User guide**: https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md
