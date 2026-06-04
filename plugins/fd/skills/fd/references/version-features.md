# fd Feature → Minimum Version

A consolidated lookup of **which fd version introduced a feature** this skill documents, so you know what works on an older (or newer) fd. Use it to answer "is my fd new enough for X?" and "what do I need to upgrade to?"

**How to read this:**
- Versions are when a feature was **introduced** (under its own "Added …"/"New …" line in the upstream `CHANGELOG.md`). Behavior/default changes that came in a *later* release are listed separately in [Removed, deprecated, and changed defaults](#removed-deprecated-and-changed-defaults).
- fd's changelog uses an **inconsistent `v` prefix** across the 10.x boundary (`# v9.0.0`, `# v10.0.0`, but `# 10.1.0`, `# 10.4.2`). This file **normalizes display to `fd X.Y+`** — the prefix carries no meaning.
- Versions `X.Y.0` are fd's feature releases; bug-fix point releases (`8.7.1`, `10.4.2`) rarely add surface and are noted inline when relevant.
- Features **not listed here are long-standing** (predate ~fd 7.0 / 2018 — e.g. basic pattern (regex) search, `-H`/`--hidden`, `-I`/`--no-ignore`, `-t`/`--type` file·dir·symlink, `-e`/`--extension`, `-d`/`--max-depth`, `-x`/`--exec`, `-E`/`--exclude`, `-a`/`--absolute-path`, `-p`/`--full-path`, `-c`/`--color`, smart-case, `.gitignore`/`.fdignore` handling). This file deliberately omits them to stay signal-rich.
- This skill is documented against **fd 10.4.x** (source: v10.4.2). Always confirm on the running system: `fd --version`, then `man fd` (or `fd --help`).

Every version below was verified by locating the feature **under its introducing section header** in the fd source `CHANGELOG.md`, cross-checked against `src/cli.rs` (current flags) and `doc/fd.1`. Versions were **not** inferred from usage examples in later release notes.

## Contents

- [fd 10.0 and newer](#fd-100-and-newer)
- [fd 8.0 to 9.x](#fd-80-to-9x)
- [fd 7.0 to 7.5](#fd-70-to-75)
- [Removed, deprecated, and changed defaults](#removed-deprecated-and-changed-defaults)

## fd 10.0 and newer

| Min version | Feature | Area |
|---|---|---|
| 10.4+ | `--ignore-contain <name>` — ignore directories that contain a named entry (e.g. `CACHEDIR.TAG`) | filters / ignore |
| 10.2+ | `--hyperlink[=when]` (alias `--hyper`) — OSC 8 terminal hyperlinks on output paths; `when` ∈ `auto`/`always`/`never`, defaults to `auto` if given bare | output |
| 10.1+ | `--format <fmt>` — format-template output (`{}`, `{/}`, `{//}`, `{.}`, `{/.}`); like the `--exec` template but for direct printing | output |
| 10.1+ | `--strip-cwd-prefix` accepts an **optional argument** `always`/`never`/`auto` (must use `=`, e.g. `--strip-cwd-prefix=never`); bare = `always` | output |
| 10.0+ | `dir` accepted as an alias for `directory` in `-t`/`--type` (so `-t dir` works) | filters / type |
| 10.0+ | `@<seconds>` (Unix-epoch) timestamps accepted in time filters, GNU-`date`-style, for `--changed-within`/`--changed-before` (`--newer`/`--older`) | filters / time |
| 10.3+ | hidden `--mindepth` alias for `--min-depth` (mirrors the older `--maxdepth` alias) | traversal |

## fd 8.0 to 9.x

| Min version | Feature | Area |
|---|---|---|
| 9.0+ | `--type block-device` (`-t b`) and `--type char-device` (`-t c`) | filters / type |
| 8.7+ | `--no-require-git` — respect git ignore rules even outside a git repository (override with `--require-git`) | filters / ignore |
| 8.6+ | `--and <pattern>` — additional pattern(s) that must *also* match (repeatable); regex unless `--glob`/`--fixed-strings` | search / pattern |
| 8.6+ | `--changed-after` added as an alias for `--changed-within` (parallels `--changed-before`) | filters / time |
| 8.4+ | Multiple `--exec`/`-x` instances in one invocation (each result runs every command) | exec |
| 8.3+ | `--batch-size <n>` — cap arguments per `--exec-batch`/`-X` invocation (`0` = no limit) | exec |
| 8.3+ | `-q`/`--quiet` (alias `--has-results`) — print nothing, exit 0 if any match | output |
| 8.3+ | `--no-ignore-parent` — don't apply ignore files from parent directories | filters / ignore |
| 8.3+ | `--strip-cwd-prefix` flag introduced — strip the leading `./` added under `-x`/`-X`/`-0` *(medium confidence: appears under v8.3.0 bugfixes rather than an explicit "Add flag" line; the `always/never/auto` arg came in 10.1)* | output |
| 8.3+ | "Opposing" override flags added broadly (`--no-hidden`, `--ignore`, `--ignore-vcs`, `--relative-path`, `--no-follow`, …) to cancel an earlier flag | general |
| 8.2+ | `--prune` — match directories but don't descend into them | traversal |
| 8.2+ | Exact file sizes in `--size`/`-S` (e.g. `-S 100k` with no `+`/`-`) | filters / size |
| 8.1+ | `-o`/`--owner [user][:group]` filter (Unix; `!` prefix on either side to exclude) | filters |
| 8.1+ | Global ignore file support (`~/.config/fd/ignore` on Unix) | filters / ignore |
| 8.0+ | `--max-results <count>` and its alias `-1` (= `--max-results=1`, quit after first match) | output |
| 8.0+ | `-l`/`--list-details` — `ls -l`-style long output (alias for `--exec-batch ls -l` + extras; deterministic order) | output |
| 8.0+ | `--type socket` (`-t s`) and `--type pipe` (`-t p`) | filters / type |
| 8.0+ | `--min-depth <d>` and `--exact-depth <d>` (complement the long-standing `--max-depth`) | traversal |

## fd 7.0 to 7.5

| Min version | Feature | Area |
|---|---|---|
| 7.5+ | `--one-file-system` (aliases `--mount`, `--xdev`) — don't cross filesystem boundaries | traversal |
| 7.5+ | `-C`/`--base-directory <path>` — change fd's working directory before searching | traversal |
| 7.5+ | `NO_COLOR` environment variable honored (disables color when set) | output / env |
| 7.4+ | `-g`/`--glob` glob-based search + `--regex` to switch back (handy with `alias fd='fd --glob'`) | search / pattern |
| 7.4+ | `--path-separator <sep>` — override the OS path separator in output | output |
| 7.4+ | Hidden-file support on Windows | platform |
| 7.3+ | `-X`/`--exec-batch <cmd>` — run one command with *all* results as arguments (xargs-style) | exec |
| 7.2+ | `--changed-within`/`--changed-before` time filters (aliases `--change-newer-than`/`--newer`, `--change-older-than`/`--older`) | filters / time |
| 7.2+ | `--show-errors` — surface filesystem errors (permission denied, dead symlinks) | output |
| 7.2+ | `--search-path <path>` — supply search roots as an option instead of positional args | traversal |
| 7.2+ | hidden `--maxdepth` alias for `--max-depth` | traversal |
| 7.1+ | `-S`/`--size` filter (`<+-><NUM><UNIT>`) | filters / size |
| 7.1+ | `--type empty` (`-t e`) — empty files and/or directories | filters / type |
| 7.0+ | `--type executable` (`-t x`) | filters / type |
| 7.0+ | `--ignore-file <path>` — add a custom `.gitignore`-format ignore file | filters / ignore |
| 7.0+ | `.fdignore` file support | filters / ignore |

> **Pre-7.0, still current (long-standing):** `-F`/`--fixed-strings`/`--literal` (6.3), multiple `-e`/`--extension` and `-t`/`--type` values (6.2), multiple search paths and `--no-ignore-vcs` (6.1), `--exec`/`-x` parallel execution (5.0), `-u`/`-uu` unrestricted aliases (5.0), `-i`/`--ignore-case` (5.0), `-E`/`--exclude` (5.0, see reassignment note below).

## Removed, deprecated, and changed defaults

These matter most when a script or habit assumes old behavior — or when you read older docs.

| Version | Change |
|---|---|
| Unreleased | **New:** `--exact` (match the entire filename literally, non-substring) and `--ignore-parent` (override `--no-ignore-parent`) landed on `master` but are **not in a tagged release** as of 10.4.2 — *don't rely on them yet.* |
| 10.3+ | **Date-parsing change:** switched to the `jiff` crate. In durations, **`M` no longer means "month"** (ambiguous with minutes) — use `mo`/`mos`/`month`/`months`. `month`/`year` now respect calendar variability instead of fixed seconds. Affects `--changed-within`/`--changed-before`. |
| 10.0+ | **Default change (BREAKING, reverts 9.0):** fd **no longer auto-ignores `.git/`** when `--hidden` is used with VCS-ignore enabled. To get the old behavior, add `.git/` to your global fdignore file. |
| 9.0+ | **Default change (BREAKING):** `.git/` **is** ignored by default when using `--hidden`/`-H` (override with `--no-ignore`/`-I` or `--no-ignore-vcs`). *Reverted again in 10.0.* |
| 8.6+ | **BREAKING (Unix):** `--type executable` now *additionally* requires the file be executable **by the current user**, not merely have an execute bit. |
| 8.5+ | **Default change:** reverted to **no leading `./` prefix** for non-interactive output (the 8.3 behavior). The `./` prefix now appears only with `-x`/`--exec`, `-X`/`--exec-batch`, or `-0`/`--print0`; use `--strip-cwd-prefix` to drop it there. |
| 8.4+ | **Default change:** directories are printed with a **trailing path separator** (`foo/bar/`). |
| 8.4+ | **Flag semantics:** a single `-u` is now equivalent to `-HI` (previously a single `-u` meant only `-I`). Extra `-u`s are accepted but ignored. |
| 8.0+ | **Glob + full-path change:** with `--glob` *and* `--full-path`/`-p`, a `*` **no longer matches a path separator** — use `**` (e.g. `fd -p -g '/base/*/*/*.txt'` now means exactly two levels). |
| 8.0+ | **Removed:** legacy single-dash `fd -exec`. Use `fd -x`/`--exec` (or `-X`/`--exec-batch`). |
| 7.3+ | **Short-flag reassignment:** `-X` now means `--exec-batch` (introduced here). It previously meant `--exclude` (added in 5.0); `--exclude` is now the long form of **`-E`**. *(Medium confidence on the exact release the `-E` short flag took over — confirmed current in `src/cli.rs`, not pinned to a changelog line.)* |
| 7.1+ | **Default change:** `.gitignore` files are now respected **only inside Git repositories**, not in arbitrary directories. |
| 7.0+ | **Removed:** `.ignore` and `.rgignore` files are no longer parsed — use `.fdignore` or `--ignore-file` instead. |
| 5.0+ | **Short-flag change:** `--type symlink` short code changed from `-s` to **`-l`** (consistency with ripgrep). |
| 3.0+ | **Short-flag change:** `--follow` short code changed from `-f` to **`-L`** (consistency with ripgrep). |

> Note on the `./` prefix saga: 8.3 briefly made `./` the default for non-TTY output, then 8.5 reverted it. Net current behavior (10.x): **no `./` prefix** unless `-x`/`-X`/`-0` is used, and `--strip-cwd-prefix[=always|never|auto]` (arg since 10.1) controls it explicitly.
