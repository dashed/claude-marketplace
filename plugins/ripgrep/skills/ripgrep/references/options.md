# ripgrep Options Reference

Complete reference for ripgrep's (`rg`) command-line flags, grouped by ripgrep's own
help categories (Input, Search, Filter, Output, Output Modes, Logging, Other Behaviors).

> **Version annotations:** Flags marked `(rg X.Y+)` require at least that ripgrep version;
> unmarked flags are long-standing basics (predate ~rg 0.5 / early 2017). For the consolidated
> feature→version lookup (and removed/changed defaults), see
> [references/version-features.md](version-features.md). This reference is documented against
> **ripgrep 15.x** — every flag below was verified against the post-15.1
> `crates/core/flags/defs.rs` source (the canonical per-flag authority: category, negation,
> deprecation). Confirm on your system with `rg --version`, then `man rg` or `rg --help`.
>
> ⚠️ There is **no bare `--hyperlink` switch** — only `--hyperlink-format` (rg 14.0+) controls
> terminal hyperlinks. The old `--man` flag was **removed** in rg 14.0 — use `--generate man`.

## Usage

```
rg [OPTIONS] PATTERN [PATH...]
rg [OPTIONS] -e PATTERN ... [PATH...]
rg [OPTIONS] -f PATTERNFILE ... [PATH...]
rg [OPTIONS] --files [PATH...]
rg [OPTIONS] --type-list
command | rg [OPTIONS] PATTERN
```

- `PATTERN` — a regular expression (default). With `-F/--fixed-strings` it is a literal; with
  `-P/--pcre2` it uses the PCRE2 engine. If it begins with `-`, pass `--` first or use `-e`.
- `PATH...` — files/directories to search (default: current directory, recursively; or stdin
  when piped). `rg` respects `.gitignore`/`.ignore`/`.rgignore` and skips hidden files by default.

## Negated (inverse) flags

Most boolean flags have a paired negation that cancels an earlier or config-file setting
("most recent wins"). They are listed inline below as *(neg: `--no-...`)* or, for flags whose
**primary** form is already the `--no-` variant (e.g. `--no-ignore`), as *(inv: `--ignore`)*.
Negations are useful to override `RIPGREP_CONFIG_PATH` defaults on a single invocation.

## Table of Contents

- [Input](#input)
- [Search](#search)
- [Filter](#filter)
- [Output](#output)
- [Output Modes](#output-modes)
- [Logging](#logging)
- [Other Behaviors](#other-behaviors)
- [Deprecated & removed flags](#deprecated--removed-flags)

## Input

How patterns and file contents get into ripgrep.

| Flag | Description |
|------|-------------|
| `-e, --regexp <PATTERN>` | A pattern to search for; repeatable (logical OR). Required to match a pattern that starts with `-`, or to supply multiple patterns |
| `-f, --file <PATTERNFILE>` | Read one pattern per line from a file (or `-` for stdin); repeatable. An empty file matches nothing (with `-v`, an empty file matches **everything** as of rg 15.0+) |
| `-z, --search-zip` (rg 0.8+) | Search inside compressed files (gzip, bzip2, xz, lzma, lz4 (0.9+), Brotli/Zstd (11.0+), `.Z`/uncompress (12.1+)). *(neg: `--no-search-zip`)* |
| `--pre <COMMAND>` (rg 0.9+) | Preprocess each file through `COMMAND` (e.g. `pdftotext`); search the program's stdout. *(neg: `--no-pre`)* |
| `--pre-glob <GLOB>` (rg 0.10+) | Restrict which files `--pre` runs on; repeatable. Files not matching are searched normally |

> **Security (rg 13.0+, CVE-2021-3013):** on Windows, `-z`/`--pre` could run executables from
> the current directory. Fixed in 13.0 — prefer 13.0+ on Windows with these flags.

## Search

What counts as a match: case, literals, regex engine, multiline, encoding, limits.

| Flag | Description |
|------|-------------|
| `-i, --ignore-case` | Case-insensitive search (overridden by a later `-s`/`-S`) |
| `-s, --case-sensitive` | Case-sensitive search (the default); overrides smart case |
| `-S, --smart-case` | Case-insensitive unless the pattern contains an uppercase letter |
| `-w, --word-regexp` | Require matches to be surrounded by word boundaries (`\b`) |
| `-x, --line-regexp` (rg 0.6+) | Require the pattern to match a whole line |
| `-v, --invert-match` | Select lines that do **not** match. *(neg: `--no-invert-match`)* |
| `-F, --fixed-strings` | Treat all patterns as literal strings, not regexes. *(neg: `--no-fixed-strings`)* |
| `-U, --multiline` (rg 0.10+) | Allow a single match to span multiple lines (`.` still excludes line terminators unless `--multiline-dotall`). *(neg: `--no-multiline`)* |
| `--multiline-dotall` (rg 0.10+) | In `-U` mode, let `.` match line terminators too. *(neg: `--no-multiline-dotall`)* |
| `-P, --pcre2` (rg 0.10+) | Use the PCRE2 engine (look-around, backreferences). *(neg: `--no-pcre2`)* |
| `--engine <ENGINE>` (rg 12.0+) | Select the regex engine: `default`, `pcre2`, or `auto` (fall back to PCRE2 only if the default engine can't compile the pattern). Replaces `--auto-hybrid-regex` |
| `--no-unicode` (rg 12.0+) | Disable Unicode mode for **both** engines (replaces `--no-pcre2-unicode`). *(inv: `--unicode`)* |
| `-E, --encoding <ENCODING>` (rg 0.5+) | Force the text encoding (e.g. `utf-16`, `latin1`, `gbk`, `shift_jis`); `auto` (default) sniffs BOMs, `none` disables all transcoding (11.0+). *(neg: `--no-encoding`)* |
| `--crlf` (rg 0.10+) | Treat `\r\n` as the line terminator so `$` works on Windows files. *(neg: `--no-crlf`)* |
| `--null-data` (rg 0.10+) | Use NUL (`\0`) as the line terminator instead of `\n` |
| `-m, --max-count <NUM>` | Stop after `NUM` matching lines **per file** |
| `--stop-on-nonmatch` (rg 14.0+) | After the first match in a file, stop at the first subsequent non-matching line |
| `-a, --text` | Search binary files as if they were text (may dump raw bytes). *(neg: `--no-text`)* |
| `--regex-size-limit <NUM+SUFFIX?>` (rg 0.5.2+) | Cap the memory of a single compiled regex (e.g. `1G`, default `10M`) |
| `--dfa-size-limit <NUM+SUFFIX?>` (rg 0.5.2+) | Cap the memory of the regex DFA cache (e.g. `1G`) |
| `-j, --threads <NUM>` | Approximate number of search threads (`0` = auto, the default) |
| `--mmap` | Search using memory maps when possible (sometimes faster). *(neg: `--no-mmap`)* |

> `-s`/`-i`/`-S` follow "most recent wins": `rg foo -s -i` is case-insensitive.

## Filter

Which files get searched: types, globs, ignore rules, hidden/binary, depth, size.

| Flag | Description |
|------|-------------|
| `-t, --type <TYPE>` | Only search files of this type (e.g. `py`, `rust`, `js`); repeatable. See `--type-list` |
| `-T, --type-not <TYPE>` | Do **not** search files of this type; repeatable |
| `--type-add <TYPESPEC>` | Define/extend a type, e.g. `--type-add 'web:*.{html,css,js}'`; repeatable. `name:include:globs` form extends an existing type |
| `--type-clear <TYPE>` | Clear all globs for a type (override built-ins); repeatable |
| `-g, --glob <GLOB>` | Include/exclude files by glob (prefix `!` to exclude), e.g. `-g '*.rs' -g '!target/'`; repeatable. Overrides ignore rules |
| `--iglob <GLOB>` (rg 0.6+) | Case-insensitive `--glob`; repeatable |
| `--glob-case-insensitive` (rg 11.0.2+) | Make every `-g/--glob` behave like `--iglob`. *(neg: `--no-glob-case-insensitive`)* |
| `-., --hidden` (`-.` short: rg 13.0+) | Search hidden files/directories (names starting with `.`). *(neg: `--no-hidden`)* |
| `-u, --unrestricted` | Reduce filtering, repeatable: `-u` = `--no-ignore`, `-uu` = `--no-ignore --hidden`, `-uuu` = `--no-ignore --hidden --binary` (rg 11.0+; ≈ `grep -r`) |
| `--no-ignore` | Don't respect any ignore files (`.gitignore`, `.ignore`, `.rgignore`, parents, global). *(inv: `--ignore`)* |
| `--no-ignore-vcs` | Don't respect VCS ignore files (`.gitignore`); still honors `.ignore`/`.rgignore`. *(inv: `--ignore-vcs`)* |
| `--no-ignore-dot` (rg 11.0+) | Don't respect `.ignore`/`.rgignore` files. *(inv: `--ignore-dot`)* |
| `--no-ignore-global` (rg 0.9+) | Don't respect the global gitignore / global `.ignore`. *(inv: `--ignore-global`)* |
| `--no-ignore-parent` | Don't respect ignore files in parent directories. *(inv: `--ignore-parent`)* |
| `--no-ignore-exclude` (rg 12.0+) | Don't respect local exclusion files (`.git/info/exclude`). *(inv: `--ignore-exclude`)* |
| `--no-ignore-files` (rg 12.0+) | Don't respect any `--ignore-file` paths. *(inv: `--ignore-files`)* |
| `--ignore-file <PATH>` | Add a custom gitignore-format ignore file (low precedence); repeatable |
| `--ignore-file-case-insensitive` (rg 11.0+) | Match `--ignore-file` globs case-insensitively. *(neg: `--no-ignore-file-case-insensitive`)* |
| `--no-require-git` (rg 12.0+) | Respect gitignore rules even outside a git repository. *(inv: `--require-git`)* |
| `--binary` (rg 11.0+) | Disable binary filtering without dumping raw binary to the terminal (what `-uuu` enables; unlike `-a`, stops at the first NUL-containing line's notice). *(neg: `--no-binary`)* |
| `--max-filesize <NUM+SUFFIX?>` (rg 0.5+) | Skip files larger than `NUM` (e.g. `50K`, `2M`, `1G`) |
| `-d, --max-depth <NUM>` (`-d` short: rg 14.0+) | Descend at most `NUM` directory levels (`--maxdepth` is a hidden alias) |
| `-L, --follow` | Follow symbolic links while recursing. *(neg: `--no-follow`)* |
| `--one-file-system` (rg 0.10+) | Don't cross filesystem boundaries while recursing. *(neg: `--no-one-file-system`)* |

## Output

Formatting, context, colors, replacement, separators, sorting, hyperlinks.

| Flag | Description |
|------|-------------|
| `-A, --after-context <NUM>` | Show `NUM` lines after each match |
| `-B, --before-context <NUM>` | Show `NUM` lines before each match |
| `-C, --context <NUM>` | Show `NUM` lines before and after each match. As of rg 14.0+, `-A`/`-B` only *partially* override `-C` (e.g. `rg -C1 -A2` ≡ `rg -B1 -A2`) |
| `--context-separator <SEPARATOR>` | Set the string printed between non-adjacent context chunks (default `--`). `--no-context-separator` (rg 12.0+) prints nothing. *(neg)* |
| `-n, --line-number` | Show line numbers (default when printing to a tty) |
| `-N, --no-line-number` | Suppress line numbers (default when piping) |
| `--column` | Show 1-based column numbers (implies `-n`). *(neg: `--no-column`, rg 0.9+)* |
| `-b, --byte-offset` (rg 0.9+) | Print the 0-based byte offset of each matching line (or each match with `-o`). *(neg: `--no-byte-offset`)* |
| `-o, --only-matching` (rg 0.5.1+) | Print only the matched (non-empty) parts of each line, one per output line |
| `-r, --replace <REPLACEMENT>` | Replace each match with `REPLACEMENT` in output (use `$1`, `${name}` for capture groups). Works with `--json` as of rg 15.0+ |
| `--passthru` (rg 0.8+) | Print every line (matching and not), highlighting matches; composes with `-r` (0.10+) |
| `-H, --with-filename` | Print the file path with each match (default when searching multiple files / recursing) |
| `-I, --no-filename` (`-I` short: rg 11.0+) | Never print the file path with matches |
| `--heading` | Group matches under one file-path heading. *(neg: `--no-heading`)* |
| `--color <WHEN>` | When to use color: `auto` (default), `always`, `ansi`, `never` |
| `--colors <COLOR_SPEC>` | Configure color/style per element, e.g. `--colors 'match:fg:red' --colors 'line:style:bold'`; styles include `bold`/`underline`/`italic` (15.0+); repeatable. Color types include `highlight` (15.0+) for non-matching text |
| `-p, --pretty` | Alias for `--color always --heading --line-number` |
| `-M, --max-columns <NUM>` (rg 0.5+) | Omit lines longer than `NUM` bytes (`0` disables the limit) |
| `--max-columns-preview` (rg 11.0+) | Instead of hiding over-long lines, print a truncated preview. *(neg: `--no-max-columns-preview`)* |
| `--trim` (rg 0.10+) | Strip leading whitespace from each printed line. *(neg: `--no-trim`)* |
| `--sort <SORTBY>` (rg 0.10+) | Sort results ascending by `path`, `modified`, `accessed`, or `created` (forces single-threaded). `none` = default |
| `--sortr <SORTBY>` (rg 0.10+) | Like `--sort` but descending |
| `-0, --null` | Print a NUL byte after each file path (for `xargs -0`); `-0` short flag since rg 0.5.1+ |
| `--path-separator <SEPARATOR>` | Use a custom path separator when printing paths (e.g. `/` on Windows) |
| `--field-context-separator <SEP>` (rg 13.0+) | Set the field delimiter before context lines (default `-`) |
| `--field-match-separator <SEP>` (rg 13.0+) | Set the field delimiter before matching lines (default `:`) |
| `--hyperlink-format <FORMAT>` (rg 14.0+) | Emit OSC-8 terminal hyperlinks for file paths. Aliases: `default`, `none`, `file`, `vscode`, `cursor` (15.1+), etc., or a custom template using `{path}`/`{line}`/`{column}`/`{host}`. **There is no separate `--hyperlink` flag** |
| `--hostname-bin <COMMAND>` (rg 14.0+) | Program used to resolve `{host}` in hyperlink formats (e.g. `hostname`) |
| `--line-buffered` (rg 0.10+) | Force line buffering. *(neg: `--no-line-buffered`)* |
| `--block-buffered` (rg 0.10+) | Force block buffering. *(neg: `--no-block-buffered`)* |
| `-h, --help` | Show help (`-h` short / `--help` long form) |

## Output Modes

Mutually-exclusive modes that change *what* is printed instead of matching lines.

| Flag | Description |
|------|-------------|
| `-c, --count` | Print a count of matching **lines** per file (suppresses individual matches) |
| `--count-matches` (rg 0.9+) | Print a count of individual **matches** per file (counts multiple per line) |
| `-l, --files-with-matches` | Print only the paths of files that contain at least one match |
| `--files-without-match` | Print only the paths of files that contain **zero** matches |
| `--json` (rg 0.10+) | Emit results as JSON Lines (implies `--stats`). *(neg: `--no-json`)* |
| `--vimgrep` | Print one match per line as `file:line:col:text` (Vim quickfix friendly). In `-U` mode, prints only the first line of each match (rg 13.0+) |
| `-q, --quiet` | Print nothing; exit `0` on the first match (stops searching early) |
| `--include-zero` (rg 12.0+) | With `-c`/`--count-matches`, also list files with **zero** matches. *(neg: `--no-include-zero`)* |

> `--vimgrep` and `-q` live in the Output / Search help groups respectively but function as
> output modes; grouped here for discoverability.

## Logging

Diagnostics and message suppression.

| Flag | Description |
|------|-------------|
| `--stats` (rg 0.9+) | Print aggregate match/timing statistics after results (implied by `--json`). *(neg: `--no-stats`)* |
| `--debug` | Show debug messages (useful for diagnosing ignore/type rules) |
| `--trace` | Show very verbose trace messages (more than `--debug`) |
| `--no-messages` | Suppress error messages (e.g. unreadable files). *(inv: `--messages`)* |
| `--no-ignore-messages` (rg 0.9+) | Suppress gitignore/ignore-file parse error messages. *(inv: `--ignore-messages`)* |

## Other Behaviors

Meta operations and process-level behavior.

| Flag | Description |
|------|-------------|
| `--files` | List every file ripgrep *would* search (respecting ignore/type rules), without searching |
| `--type-list` | List all supported file types and their globs |
| `--generate <KIND>` (rg 14.0+) | Print generated docs/completions to stdout: `man`, `complete-bash`, `complete-zsh`, `complete-fish`, `complete-powershell`. **Replaced the removed `--man` flag** |
| `-V, --version` | Print ripgrep's version (reports PCRE2/SIMD availability as of rg 14.0+) |
| `--pcre2-version` (rg 11.0+) | Print the PCRE2 version ripgrep was built with (or that it's unavailable) |
| `--no-config` (rg 0.8+) | Never read configuration files (ignore `RIPGREP_CONFIG_PATH`) |

> **Configuration file (rg 0.8+):** set `RIPGREP_CONFIG_PATH` to a file of one flag per line
> (lines starting with `#` are comments) to apply defaults to every invocation. Override a
> config default on a single run with the flag's negation (see [Negated flags](#negated-inverse-flags)).

## Deprecated & removed flags

These still parse (as aliases) unless noted, but newer equivalents are preferred. See
[version-features.md](version-features.md#removed-deprecated-and-changed-defaults) for the
full history.

| Flag | Status | Use instead |
|------|--------|-------------|
| `--auto-hybrid-regex` / `--no-auto-hybrid-regex` | Deprecated (rg 12.0+) | `--engine auto` / `--engine default` |
| `--no-pcre2-unicode` / `--pcre2-unicode` | Deprecated (rg 12.0+) | `--no-unicode` / `--unicode` |
| `--sort-files` / `--no-sort-files` | Deprecated (rg 0.10+) | `--sort path` / `--sortr path` |
| `--man` | **Removed** (rg 14.0) | `rg --generate man` |
| `--line-number-width` | **Removed** (rg 0.10) | *(no replacement)* |

> **Not flags but worth knowing:** the `simd-accel` (rg 14.1.1+) and `avx-accel` (rg 11.0+)
> Cargo build features were removed — SIMD/AVX is now enabled via runtime CPU detection, so no
> special build is needed.
