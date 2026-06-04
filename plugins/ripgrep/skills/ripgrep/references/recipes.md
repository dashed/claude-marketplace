# ripgrep Advanced Recipes

Real-world recipes for multiline matching, replacements, custom types,
preprocessing, structured output, configuration, and integrating `rg` with
other tools. This is the deep layer — for the basics (pattern search, `-i`/`-S`,
`-w`, `-A`/`-B`/`-C`, `-t`/`-T`, `-g`, `-l`/`-c`, `-o`) see `SKILL.md`.

> **Version note:** Several features below landed in specific releases —
> `--engine` (rg 12.0+), `--no-require-git` (12.0+), `--stop-on-nonmatch`
> (14.0+), `--generate` (14.0+; replaced the removed `--man`),
> `--hyperlink-format` (14.0+; there is **no** bare `--hyperlink` switch), and
> `-r/--replace` working with `--json` (15.0+). These are flagged inline.
> Long-standing flags (`-U/--multiline`, `--multiline-dotall`, `-r/--replace`,
> `--passthru`, `-P/--pcre2`, `--json`, `--vimgrep`, `--pre`/`--pre-glob`,
> `-z/--search-zip`, `--type-add`/`--type-clear`/`--type-list`,
> `RIPGREP_CONFIG_PATH`, `-u`/`-uu`/`-uuu`) are not annotated. For the full
> feature → version map, see [version-features.md](version-features.md).
>
> Recipes here are documented against **ripgrep 15.x** and verified against the
> upstream `GUIDE.md`, `FAQ.md`, and `crates/core/flags/defs.rs` (15.1.0 source
> tree). Examples marked "spot-run" were executed on a local **rg 14.1.1**;
> 15.x-only examples (e.g. `-r` + `--json`) were verified against source only,
> since they can't run on 14.x. Confirm your build with `rg --version`.

## Table of Contents

- [Multiline Search](#multiline-search)
- [Replacements](#replacements)
- [Custom File Types](#custom-file-types)
- [Structured Output for Tooling](#structured-output-for-tooling)
  - [`--vimgrep`](#--vimgrep)
  - [`--json`](#--json)
- [Search & Replace Across a Repo](#search--replace-across-a-repo)
- [Preprocessing & Compressed Search](#preprocessing--compressed-search)
- [Configuration File](#configuration-file)
- [Regex Engine Selection](#regex-engine-selection)
- [Integration Recipes](#integration-recipes)
  - [rg + fzf (interactive)](#rg--fzf-interactive)
  - [fd | rg](#fd--rg)
  - [rg in editors](#rg-in-editors)
  - [rg + git](#rg--git)
- [Troubleshooting](#troubleshooting)

## Multiline Search

By default ripgrep matches **within** a single line — a pattern can never span a
line terminator. `-U`/`--multiline` lifts that restriction so one match can
cross newlines.

```bash
# Match a struct definition spanning several lines
rg -U 'struct Config \{[^}]*\}'

# Find a function whose body mentions TODO (lazy, bounded)
rg -U 'fn \w+\([^)]*\)\s*\{.*?TODO.*?\}'
```

In multiline mode `.` still does **not** match a line terminator. Add
`--multiline-dotall` (implies `-U`) to make `.` match across newlines too:

```bash
# Without dotall, `.` stops at \n; with it, start.*end spans lines
rg -U --multiline-dotall 'start.*end'   # spot-run: matches across 3 lines
```

Equivalently, you can use the inline regex flag `(?s)` for dotall, or
`\p{any}` which matches any Unicode codepoint **including** line terminators in
multiline mode.

> **Behavior to know (rg 13.0+):** in multiline mode `--vimgrep` prints only the
> **first line** of each match (previously every line), and `-c/--count` counts
> like `--count-matches`. See
> [version-features.md](version-features.md#removed-deprecated-and-changed-defaults).

> **Cost:** multiline mode reads whole files into memory and disables some
> line-oriented optimizations — it's slower. Use it only when a match genuinely
> crosses lines.

## Replacements

`-r`/`--replace` rewrites the matched portion of each line on output (it never
touches files on disk). Capture groups from the pattern are available:

```bash
# Reorder "first last" -> "last, first"
rg '(\w+)\s+(\w+)' -r '$2, $1'

# Named captures
rg '(?P<y>\d{4})-(?P<m>\d{2})' -r '$m/$y'
```

**Capture syntax (this trips people up):** after `$`, ripgrep greedily consumes
letters, digits, and underscores (`[_0-9A-Za-z]`) as the group name. So
`$1foo` means *the group named `1foo`*, not "group 1 then `foo`". Use braces to
delimit:

```bash
# WRONG: $1X is parsed as capture name "1X" (invalid) -> empty
rg -r 'X$1X' '(foo)'      # spot-run -> "X bar"  (the foo vanished!)

# RIGHT: brace-delimit the index
rg -r 'X${1}X' '(foo)'    # spot-run -> "XfooX bar"
```

Other rules:
- `$0` is the **entire match**.
- An index/name that doesn't refer to a valid group expands to **empty**.
- Write a literal `$` as `$$`.

**`--passthru`** prints *every* line of input (not just matches), applying the
replacement to matching lines — turning `rg` into a `sed`-like stream filter
that keeps non-matching lines intact:

```bash
# Print the whole file, redacting emails
rg --passthru -r '[redacted]' '[\w.]+@[\w.]+' notes.txt

# spot-run: rg --passthru -r FOO foo  ->  every line printed, foo->FOO
```

> `-r` + `--json` works since **rg 15.0+** — JSON `match` objects then carry the
> replaced text. On older ripgrep the two are silently incompatible. Verified
> against source (CHANGELOG 15.0.0: "The `-r/--replace` flag now works with
> `--json`"); not runnable on 14.x.

## Custom File Types

ripgrep ships a large built-in type table (`rg --type-list`). Define your own
with `--type-add 'name:glob'`, then filter with `-t<name>` / `-T<name>`:

```bash
# Define a 'web' type and search only those files
rg --type-add 'web:*.{html,css,js}' -tweb 'addEventListener'

# Only ONE glob per --type-add; repeat the flag for more
rg --type-add 'web:*.html' --type-add 'web:*.css' -tweb 'flex'
```

**Compose types** with the `include` directive — pull rules from existing types
(comma-separated) into a new one:

```bash
# 'src' = C++ + Python + Markdown
rg --type-add 'src:include:cpp,py,md' -tsrc 'BUG'

# include + extra globs (repeat the flag)
rg --type-add 'src:include:cpp,py,md' --type-add 'src:*.foo' -tsrc 'BUG'
```

`--type-clear <name>` wipes a type's globs (e.g. to redefine a built-in), and
`--type-list` prints the resolved table:

```bash
rg --type-clear py --type-add 'py:*.py' --type-add 'py:*.pyi' -tpy 'def '
rg --type-list | rg '^web:'    # inspect a type's globs
```

> **Type settings are not persisted** — every invocation needs the flags. The
> idiomatic fix is to put your `--type-add` lines in the config file (below).
> Type names must be Unicode letters/numbers only (no punctuation).

## Structured Output for Tooling

### `--vimgrep`

`--vimgrep` prints one line per match as `file:line:col:text` — the format Vim's
`:grep`, quickfix tools, and many scripts expect. Each match on a line gets its
own row (handy for `:cnext`):

```bash
rg --vimgrep 'TODO'
# spot-run -> rgtest.txt:1:1:foo bar
#             rgtest.txt:2:5:baz foo qux
```

Customize the field delimiters when a downstream parser needs it (rg 13.0+):
`--field-context-separator` and `--field-match-separator`.

### `--json`

`--json` emits **JSON Lines** (one JSON object per line, `--stats` implied).
Five message `type`s appear in order: `begin`, `match`, `context`, `end`,
`summary`. A `match` object looks like (spot-run, formatting added):

```jsonc
{"type":"match","data":{
  "path":{"text":"rgtest.txt"},
  "lines":{"text":"foo bar\n"},
  "line_number":1,
  "absolute_offset":0,
  "submatches":[{"match":{"text":"foo"},"start":0,"end":3}]
}}
```

Key points for consumers:
- Each data element is an object with either a `text` key (valid UTF-8) **or** a
  `bytes` key (base64) when the data isn't valid UTF-8 — always handle both.
- `submatches[].start`/`end` are **byte** offsets into `lines.text`.
- `--json` is for search results only; it **errors** if combined with `--files`,
  `-l/--files-with-matches`, `--files-without-match`, `-c/--count`, or
  `--count-matches`.

```bash
# Pretty-print every match's path + line with jq
rg --json 'fn ' | jq -r 'select(.type=="match") | "\(.data.path.text):\(.data.line_number)"'

# Count matches per file
rg --json error | jq -r 'select(.type=="end") | "\(.data.path.text) \(.data.stats.matches)"'
```

## Search & Replace Across a Repo

`rg -r` only rewrites **output** — to edit files you pair ripgrep's *file
discovery* with an in-place editor. Two reliable patterns:

```bash
# 1) sd (simplest; regex is the same flavor you'd use in rg)
#    rg picks the files (ignore-aware), sd does the in-place edit.
rg -l 'oldName' | xargs sd 'oldName' 'newName'

# 2) GNU sed (note: sed regex != rg regex — escape accordingly)
rg -l 'oldName' | xargs sed -i 's/oldName/newName/g'   # Linux
rg -l 'oldName' | xargs sed -i '' 's/oldName/newName/g' # macOS/BSD sed
```

Make it robust against odd filenames with `-0`/`--null` (pairs with `xargs -0`):

```bash
rg -l0 'oldName' | xargs -0 sd 'oldName' 'newName'
```

> **Preview before you write.** Run `rg -r 'newName' 'oldName'` (no in-place
> tool) first — it shows exactly what the replacement produces. Then commit to
> the `sd`/`sed` pass. Use `-l` to scope which files get edited.

> **Don't reach for `sed` to do the matching.** Let `rg -l` select files (it
> honors `.gitignore`, types, globs); hand only that set to the editor.

## Preprocessing & Compressed Search

**Compressed files** — `-z`/`--search-zip` transparently decompresses gzip,
bzip2, xz, lzma, lz4, brotli, and zstd (also `.Z` via `uncompress`, rg 12.1+):

```bash
rg -z 'panic' ./logs/*.gz
rg -z 'OutOfMemory' app.log.zst
```

**Arbitrary formats** — `--pre <cmd>` runs a program on each file first and
searches its stdout. ripgrep passes the file path as the command's only argument
*and* streams the file to its stdin. Classic use: searching PDFs via
`pdftotext`:

```bash
# preprocess script (must be on PATH or given as an absolute path):
#   #!/bin/sh
#   exec pdftotext - -
rg --pre ./preprocess 'Commentz-Walter' 1995-watson.pdf
```

A robust preprocessor dispatches on file type and falls back to `cat` so
non-target files still get searched:

```sh
#!/bin/sh
case "$1" in
  *.pdf) [ -s "$1" ] && exec pdftotext - - || exec cat ;;
  *.gz)  exec gzip -dc ;;
  *)     exec cat ;;
esac
```

**Cut the overhead** — running a preprocessor per file is slow when most files
don't need it. Gate it with `--pre-glob` so the command fires only on matching
paths (in the GUIDE's own benchmark this dropped a search from 0.138s to
0.008s):

```bash
rg --pre ./preprocess --pre-glob '*.pdf' 'algorithm'
```

> **Security (Windows, fixed in rg 13.0 / CVE-2021-3013):** older ripgrep could
> run executables from the current directory via `--pre`/`-z`. Prefer rg 13.0+
> on Windows when using these flags.

## Configuration File

ripgrep reads default flags from the file named by the `RIPGREP_CONFIG_PATH`
environment variable. There is **no** default/auto-discovered path — if the
variable is unset, no config is read.

```bash
export RIPGREP_CONFIG_PATH="$HOME/.ripgreprc"
```

Format rules:
1. One shell argument per line (whitespace trimmed).
2. Lines starting with `#` (any leading whitespace) are comments; blank lines OK.
3. **No escaping or quoting** — each line is passed verbatim as one argument.
4. A flag that takes a value must be `--flag=value` on one line, **or** the flag
   and value on two separate lines. `--flag value` on one line is **wrong** (it
   becomes a single bogus argument).

Example `~/.ripgreprc`:

```
# Don't dump absurdly long lines; show a preview instead
--max-columns=150
--max-columns-preview

# Smart case by default
--smart-case

# Search dotfiles, but never descend into .git
--hidden
--glob=!.git/*

# Persist a custom type (value on its own line is fine)
--type-add
web:*.{html,css,js}

# Colors
--colors=line:style:bold
```

Gotchas:
- **Config is prepended** to your CLI args, and "later wins", so anything on the
  command line overrides the config. e.g. with `--max-columns=150` in config,
  `rg -M0 …` re-enables unlimited columns for that run.
- **Don't put a search pattern or path in the config** — it'll be applied to
  *every* invocation.
- Confused about what's loaded? `rg --debug …` prints which config file was read
  and the args parsed from it.
- `--no-config` ignores `RIPGREP_CONFIG_PATH` entirely for one run.

## Regex Engine Selection

ripgrep's default engine is a finite-automata regex (linear-time, **no**
backreferences or look-around). For those fancier features, switch to PCRE2:

```bash
# Look-around + backreferences via PCRE2
rg -P '(\w{10})\1'                 # backreference: find a repeated 10-char run
rg -P 'foo(?=bar)'                 # lookahead
rg -P '(?<=\$)\d+'                 # lookbehind
```

`--engine <auto|default|pcre2>` (rg 12.0+) is the modern selector and replaces
the deprecated `--auto-hybrid-regex`:

```bash
rg --engine pcre2 '(\w+)\s+\1'     # same as -P
rg --engine auto '(\w+)\s+\1'      # try default engine, fall back to PCRE2 if the
                                   # pattern needs features it doesn't support
```

> `-P`/`--pcre2` requires a PCRE2-enabled build. Check with `rg --version`
> (reports `+pcre2`) or `rg --pcre2-version`. PCRE2 can be slower and has a
> backtracking worst case — prefer the default engine unless you need
> look-around/backreferences; `--engine auto` is a good middle ground.

## Integration Recipes

### rg + fzf (interactive)

The canonical "live grep" — restart ripgrep on every keystroke and let fzf just
display, with a `bat` preview jumping to the matched line:

```bash
INITIAL_QUERY=""
RG="rg --column --line-number --no-heading --color=always --smart-case"
fzf --ansi --disabled --query "$INITIAL_QUERY" \
    --bind "start:reload:$RG {q} || true" \
    --bind "change:reload:sleep 0.1; $RG {q} || true" \
    --delimiter : \
    --preview 'bat --color=always {1} --highlight-line {2}' \
    --preview-window 'up,60%,+{2}/2' \
    --bind 'enter:become($EDITOR {1} +{2})'
```

See the **fzf** skill's `references/integrations.md` for the full
reload-vs-filter explanation and editor-launch variants.

### fd | rg

When you need file selection that ripgrep's globs/types can't express (by mtime,
size, etc.), let `fd` pick the files and hand them to `rg` — null-separated for
safety:

```bash
# Search only files fd selected (e.g. by type + recency)
fd -e rs --changed-within 1d -0 | xargs -0 rg 'unsafe'
```

> If you only need "grep but respecting ignores," `rg` already does that — reach
> for `fd … | rg` when fd's filters select a set rg can't easily target. See the
> **fd** skill for the reverse (`fd … -X rg`).

### rg in editors

- **Vim/Neovim:** `set grepprg=rg\ --vimgrep` and `set grepformat=%f:%l:%c:%m`,
  then `:grep pattern` populates the quickfix list. Plugins like fzf.vim
  (`:Rg`), telescope.nvim (`live_grep`), and CtrlP use ripgrep under the hood.
- **Emacs:** built-in `M-x rgrep`/`project-find-regexp`, or the `rg.el`,
  `consult-ripgrep`, and `projectile-ripgrep` packages.
- **VS Code:** the editor's search already uses ripgrep internally. To drive the
  CLI yourself, `--hyperlink-format vscode` (rg 14.0+) makes paths clickable into
  VS Code from a supporting terminal:

```bash
rg --hyperlink-format vscode 'TODO'
```

> There is **no** bare `--hyperlink` flag — only `--hyperlink-format <fmt>`
> (rg 14.0+), with built-in formats like `default`, `vscode`, `file`, and
> `cursor` (rg 15.1+), or a custom `{path}`/`{line}` template.

### rg + git

```bash
# Search only files tracked by git (bypass rg's own walker)
git ls-files | xargs rg 'pattern'

# Search a past revision without checking it out
git grep 'pattern' <rev>        # git grep, not rg, sees history

# Respect .gitignore even OUTSIDE a git repo (rg 12.0+)
rg --no-require-git 'pattern' /some/exported/tree

# Grep a diff / staged changes
git diff | rg '^\+.*TODO'       # added lines containing TODO
```

> ripgrep already honors `.gitignore`/`.ignore`/`.rgignore` and global gitignore
> automatically inside a repo — you rarely need `git ls-files`. Use it only to
> restrict strictly to tracked files (excludes untracked-but-not-ignored).

## Troubleshooting

**"My file is being skipped."** ripgrep ignores hidden files, `.gitignore`/
`.ignore`/`.rgignore` entries, and binary files by default. Escalate
unrestriction:

| Flag | Effect |
|---|---|
| `-u` / `--unrestricted` | don't respect `.gitignore`/`.ignore`/`.rgignore` |
| `-uu` | also search **hidden** files/dirs (`= --no-ignore --hidden`) |
| `-uuu` | also search **binary** files (`= --no-ignore --hidden --binary`) |
| `--no-ignore` | ignore-file rules only (keeps hidden hidden) |
| `--hidden` | include dotfiles/dirs |

```bash
rg -uu 'TODO'              # include hidden + dotfiles
rg --debug 'TODO' path/    # explains WHY a given file was skipped
```

> `-uuu` ≡ `grep -r` (rg 11.0+ semantics) — it enables `--binary`, which finds
> matches in binary files **without** dumping raw bytes to your terminal (you
> get a "binary file matches" notice). To actually print binary content as text,
> use `-a`/`--text`.

**Binary files show "binary file matches" but no lines.** That's `--binary`
behavior. Use `-a`/`--text` to treat the file as text and print matches (beware
terminal garbage). Searching for a literal NUL byte with binary detection on is
an error (rg 14.0+).

**Globs vs regex.** The positional pattern is a **regex**; `-g`/`--glob` is a
shell-style glob for *file paths*. Don't confuse them:

```bash
rg 'config.*\.ya?ml'        # regex: matches text inside files
rg pattern -g '*.yaml'      # glob: restrict WHICH files are searched
rg pattern -g '!**/test/**' # negated glob: exclude paths
```

Globs support `{a,b}` alternation and (rg 15.0+) nested `{a,{b,c}}`. For
case-insensitive globs use `--iglob` or `--glob-case-insensitive` (rg 11.0.2+).

**Regex rejected / wants look-around.** The default engine has no look-around or
backreferences — add `-P`/`--pcre2` (or `--engine auto`). See
[Regex Engine Selection](#regex-engine-selection).

**Multiline pattern matches nothing.** Add `-U`; if your `.` needs to cross
newlines, add `--multiline-dotall` (or use `(?s)` / `\p{any}`).

**Replacement dropped a capture group.** `$1foo` is read as group name `1foo`.
Brace-delimit: `${1}foo`. Literal `$` is `$$`. See [Replacements](#replacements).

**Colors vanish when piping.** `--color` defaults to `auto` (off when not a
TTY). Force it for a pager: `rg --color=always pattern | less -R`.

**Want to bail early per file.** `--stop-on-nonmatch` (rg 14.0+) stops searching
a file after the first non-matching line that follows a match — useful for
files where all matches are clustered at the top.
