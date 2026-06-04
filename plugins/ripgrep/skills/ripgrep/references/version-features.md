# ripgrep Feature → Minimum Version

A consolidated lookup of **which ripgrep (`rg`) version introduced a feature** this skill documents, so you know what works on an older (or newer) ripgrep. Use it to answer "is my rg new enough for X?" and "what do I need to upgrade to?"

**How to read this:**
- Versions are when a feature was **introduced** — traced to its own `Add …`/`FEATURE` line under the introducing version header in the upstream `CHANGELOG.md`, *not* a later bug-fix or example line that merely mentions the flag. Behavior/default changes that came in a *later* release are listed separately in [Removed, deprecated, and changed defaults](#removed-deprecated-and-changed-defaults).
- ripgrep jumped from `0.10.0` straight to `11.0.0` in 2019 (calendar-ish major versions, a few per year). So `0.10` → `11.0` is the *next* release, not a downgrade. This file **normalizes display to `rg X.Y+`** and orders sections newest-first.
- `X.Y.0` are feature releases; bug-fix point releases (`11.0.2`, `14.0.3`, `15.1.0`) rarely add surface and are noted inline when they do.
- Features **not listed here are long-standing** (predate ~rg 0.5 / early 2017 — e.g. `-i`/`--ignore-case`, `-S`/`--smart-case`, `-s`/`--case-sensitive`, `-w`/`--word-regexp`, `-v`/`--invert-match`, `-A`/`-B`/`-C` context, `-o`/`--only-matching` is 0.5.1 below, `-n`/`--line-number`, `-c`/`--count`, `-l`/`--files-with-matches`, `-t`/`--type`, `-T`/`--type-not`, `--type-add`/`--type-clear`/`--type-list`, `-g`/`--glob`, `-f`/`--file`, `-e`/`--regexp`, `-r`/`--replace`, `-F`/`--fixed-strings`, `-u`/`--unrestricted`, `--hidden`, `--no-ignore*` family core members, `-L`/`--follow`, `--heading`/`--no-heading`, `--color`/`--colors`, `--vimgrep`, `--null`, `-j`/`--threads`, `--max-depth`). This file deliberately omits them to stay signal-rich.
- This skill is documented against **ripgrep 15.x** (latest CHANGELOG entry `15.1.0`; flag set verified against the post-15.1 `crates/core/flags/defs.rs` source tree). Always confirm on the running system: `rg --version`, then `man rg` (or `rg --help`).

Every version below was verified by locating the feature **under its introducing section header** in the ripgrep source `CHANGELOG.md`, cross-checked against `crates/core/flags/defs.rs` (the canonical per-flag source: category + deprecation) and the generated man pages under `crates/core/flags/doc/`. Versions were **not** inferred from usage examples in later release notes. Low-confidence placements are flagged inline.

## Contents

- [rg 14.0 and newer (14.x–15.x)](#rg-140-and-newer-14x15x)
- [rg 11.0 to 13.0](#rg-110-to-130)
- [rg 0.8 to 0.10 (libripgrep era)](#rg-08-to-010-libripgrep-era)
- [rg 0.5 to 0.7](#rg-05-to-07)
- [Removed, deprecated, and changed defaults](#removed-deprecated-and-changed-defaults)

## rg 14.0 and newer (14.x–15.x)

| Min version | Feature | Area |
|---|---|---|
| 15.1+ | `--hyperlink-format cursor` — built-in hyperlink alias for the Cursor editor (joins `default`, `vscode`, `file`, etc.) | output / hyperlinks |
| 15.0+ | `-r/--replace` now works with `--json` output | output modes |
| 15.0+ | `--color` gains the `italic` style attribute (alongside `bold`/`underline`/etc.) | output / color |
| 15.0+ | `highlight` color type — style **non-matching** text within a matching line | output / color |
| 15.0+ | Globs support **nested alternates / nested curly braces**, e.g. `{a,{b,c}}` (also in the `globset` crate) | filters / glob |
| 15.0+ | Directories containing a `.jj` dir (Jujutsu repos) are treated as git repos, so `jj`'s gitignores are respected | filters / ignore |
| 15.0+ | With `-j`/multithreading, files are scheduled to search in the order given on the CLI | search / traversal |
| 14.0+ | `--hyperlink-format <fmt>` — turn file paths into OSC-8 terminal hyperlinks (`default`, `vscode`, `file://…`, custom `{path}`/`{line}`/`{host}` templates). *(There is **no** separate `--hyperlink` switch — format string alone controls it.)* | output / hyperlinks |
| 14.0+ | `--stop-on-nonmatch` — stop searching a file after the first non-matching line (after the first match) | search |
| 14.0+ | `--generate <kind>` — emit man page / shell completions on stdout (e.g. `rg --generate man`, `rg --generate complete-bash`); **replaced the old `--man` flag** and the asciidoc build dependency | other behaviors |
| 14.0+ | `-d` added as a **short flag for `--max-depth`** | filters / traversal |
| 14.0+ | `--version` output now reports **PCRE2 availability** (and JIT/SIMD) | other behaviors |
| 14.0+ | Flags are now **categorized** in `-h/--help` and the man page (Input/Search/Filter/Output/Output Modes/Logging/Other) | help / docs |
| 14.0+ | An error is shown when searching for a NUL byte with binary detection enabled (FEATURE #1838) | search / binary |
| 14.0+ (low conf.) | `--hostname-bin <cmd>` — program used to resolve `{host}` in hyperlink formats; introduced alongside hyperlink support, not on its own `Add` line | output / hyperlinks |

## rg 11.0 to 13.0

| Min version | Feature | Area |
|---|---|---|
| 13.0+ | `-.` — short alias for `--hidden` | filters |
| 13.0+ | `--field-context-separator` and `--field-match-separator` — customize the `:`/`-` field delimiters between path/line/column and text | output |
| 12.0+ | `--engine <auto\|default\|pcre2>` — single flag to switch regex engine (replaces `--auto-hybrid-regex`) | search |
| 12.0+ | `--no-unicode` (and inverse `--unicode`) — toggle Unicode mode across **both** the default engine and PCRE2 (replaces `--[no-]pcre2-unicode`) | search |
| 12.0+ | `--include-zero` — with `-c/--count`/`--count-matches`, also print files with **zero** matches | output |
| 12.0+ | `--no-context-separator` — never print the `--`/context separator | output |
| 12.0+ | `--no-require-git` — respect gitignore rules even **outside** a git repository | filters / ignore |
| 12.0+ | `--no-ignore-exclude` — disregard `.git/info/exclude` (and local exclude) rules | filters / ignore |
| 12.0+ | `--no-ignore-files` — disable **all** `--ignore-file` paths | filters / ignore |
| 12.1+ | `.Z` decompression via `uncompress` for `-z/--search-zip` | input / decompression |
| 11.0+ | `--binary` — disable binary filtering **without** dumping raw binary to the terminal (this is what `-uuu` enables) | filters / binary |
| 11.0+ | `--max-columns-preview` — show a truncated preview of lines longer than `-M/--max-columns` instead of hiding them | output |
| 11.0+ | `-z/--search-zip` gains **Brotli** and **Zstd** support | input / decompression |
| 11.0+ | `--no-ignore-dot` — ignore `.ignore`/`.rgignore` files | filters / ignore |
| 11.0+ | `--ignore-file-case-insensitive` — match ignore-file globs case-insensitively | filters / ignore |
| 11.0+ | `-I` — short flag for `--no-filename` | output |
| 11.0+ | `-E/--encoding none` — forcefully disable all transcoding (incl. BOM sniffing) | search / encoding |
| 11.0+ | `--pcre2-version` — print PCRE2 version / availability info | other behaviors |
| 11.0+ | `--auto-hybrid-regex` — auto-fall-back to PCRE2 *(deprecated in 12.0 → use `--engine auto`)* | search |
| 11.0.2+ | `--glob-case-insensitive` — make every `-g/--glob` behave like `--iglob` | filters / glob |

## rg 0.8 to 0.10 (libripgrep era)

| Min version | Feature | Area |
|---|---|---|
| 0.10+ | `-U/--multiline` — let a single match span multiple lines | search |
| 0.10+ | `--multiline-dotall` — make `.` match line terminators in multiline mode *(low confidence on exact release: introduced with multiline, no standalone `Add` line)* | search |
| 0.10+ | `-P/--pcre2` — use the PCRE2 engine (look-around, backreferences) | search |
| 0.10+ | `--json` — emit results as JSON Lines (implies `--stats`) | output modes |
| 0.10+ | `--sort <key>` and `--sortr <key>` (path/modified/accessed/created) — replace the older `--sort-files` | output |
| 0.10+ | `--crlf` — treat `\r\n` as the line terminator so `$` works on Windows files | search |
| 0.10+ | `--null-data` — use NUL (`\0`) as the line terminator | search |
| 0.10+ | `--trim` — strip leading whitespace from each printed line | output |
| 0.10+ | `--one-file-system` — don't cross filesystem boundaries while recursing | filters / traversal |
| 0.10+ | `--line-buffered` / `--block-buffered` — force a buffering strategy | output |
| 0.10+ | `--pre-glob` — restrict which files the `--pre` preprocessor runs on | input |
| 0.10+ | `--passthru` now composes with `-r/--replace` (flag itself is 0.8) | output |
| 0.9+ | `--stats` — print aggregate match/timing statistics after results | logging |
| 0.9+ | `-b/--byte-offset` — print the byte offset of each matching line | output |
| 0.9+ | `--count-matches` — count individual matches (not matching lines) | output modes |
| 0.9+ | `--pre <cmd>` — preprocess each file through an arbitrary program before searching | input |
| 0.9+ | `--no-ignore-messages` / `--no-ignore-global` — suppress ignore-parse errors / disable global gitignore | filters / logging |
| 0.9+ | `--max-depth` — renamed from `--maxdepth` (`--maxdepth` kept as hidden alias) | filters / traversal |
| 0.9+ | `--no-column` — disable column numbers | output |
| 0.9+ | `-z/--search-zip` gains **lz4** support | input / decompression |
| 0.8+ | `-z/--search-zip` introduced — search inside gzip/bzip2/lzma/xz archives | input / decompression |
| 0.8+ | Configuration-file support via `RIPGREP_CONFIG_PATH` | config |
| 0.8+ | `--passthru` — print every line read, highlighting matches | output |
| 0.8+ | "True"/24-bit color support (works on Windows 10) | output / color |
| 0.8+ | `.rgignore` files reinstated (higher precedence than `.ignore`) | filters / ignore |
| 0.8+ (low conf.) | `--no-config` — ignore `RIPGREP_CONFIG_PATH`; introduced with config-file support, not on its own `Add` line | config |

## rg 0.5 to 0.7

| Min version | Feature | Area |
|---|---|---|
| 0.6+ | `--iglob <glob>` — case-insensitive variant of `-g/--glob` | filters / glob |
| 0.6+ | `-x/--line-regexp` — require the pattern to match an entire line | search |
| 0.5.2+ | `--regex-size-limit` and `--dfa-size-limit` — bound regex compiled/DFA memory | search |
| 0.5.1+ | `-o/--only-matching` — print only the matched parts of a line | output |
| 0.5.1+ | `-0` — short flag for `--null` | output |
| 0.5+ | `-E/--encoding <enc>` + automatic UTF-16 BOM sniffing (latin-1, GBK, EUC-JP, Shift_JIS, …) | search / encoding |
| 0.5+ | `-M/--max-columns <n>` — omit lines longer than `n` bytes (disabled by default) | output |
| 0.5+ | `--max-filesize <size>` — skip files larger than the given size | filters |

## Removed, deprecated, and changed defaults

These matter most when a script or habit assumes old behavior — or when you read older docs.

| Version | Change |
|---|---|
| 15.0+ | **Behavior:** `rg -vf FILE` where `FILE` is empty now **matches everything** (previously matched nothing). |
| 14.0+ | **BREAKING:** `-A`/`-B` now only **partially** override `-C`. Previously `rg -C1 -A2` ≡ `rg -A2`; now ≡ `rg -B1 -A2`. |
| 14.0+ | **Removed/replaced:** the `--man` flag is gone; generate the man page with `rg --generate man`. The asciidoc/asciidoctor build dependency was dropped (ripgrep writes `roff` itself). |
| 14.1.1+ | **Removed (build):** the `simd-accel` cargo feature was removed (was frequently broken); SIMD/transcoding no longer needs it. |
| 13.0+ | **Output change:** binary-match notice reformatted from `Binary file FOO matches (...)` to `FOO: binary file matches (...)`. |
| 13.0+ | **Behavior:** in `-U/--multiline` mode, `--vimgrep` now prints only the **first line** of each match (was: every line), and `-c/--count` ≡ `--count-matches`. |
| 12.0+ | **Deprecated:** `--auto-hybrid-regex` → use `--engine auto`; `--no-pcre2-unicode`/`--pcre2-unicode` → use `--no-unicode`/`--unicode` (old flags remain as aliases). |
| 11.0+ | **BREAKING:** `-uuu` now ≡ `--no-ignore --hidden --binary` (was `… --text`). `rg -uuu foo` now behaves like `grep -r foo` without dumping raw binary to the terminal. |
| 11.0+ | **BREAKING:** exit codes aligned with GNU grep — a non-fatal error during search now yields exit `2` (was: `2` only for catastrophic errors like a regex syntax error). Under `-q/--quiet`, a found match still yields `0`. |
| 11.0+ | **Removed (build):** the `avx-accel` cargo feature was removed; AVX is enabled automatically via runtime CPU detection. |
| 0.10+ | **Deprecated:** `--sort-files` → use `--sort path`. |
| 0.10+ | **Removed:** the `--line-number-width` flag, and octal escape syntax (`\1` for `U+0001`) — now an error. |
| 0.9+ | **BREAKING:** `--count` + `--only-matching` together now behave like `--count-matches` (total matches, not matching lines). |
| 0.10+ | **Match-semantics:** `-w/--word-regexp` changed from `\b(?:pat)\b` to `(?:^|\W)(?:pat)(?:$|\W)` (GNU-grep-compatible). *(Documented under 0.10.0 BREAKING CHANGES.)* |
| 0.8+ | **Override rule change:** competing flags now follow "most recent wins" (e.g. `rg foo -s -i` is now case-**insensitive**); previously `-s` always beat `-i`. |
| 0.8+ | **BREAKING:** `-M/--max-columns=0` now disables the limit (was: suppress all non-empty lines); glob `[^...]` now ≡ `[!...]` (class negation). |
| 0.5+ | **Default change:** line numbers are hidden by default when printing to a tty **and** the only input is stdin. |

> Security note (13.0 / CVE-2021-3013): on Windows, `-z/--search-zip` and `--pre` could run arbitrary executables from the current directory. Fixed in ripgrep 13.0.0 — prefer 13.0+ on Windows when using those flags.
