# jq Feature → Minimum Version

A consolidated lookup of **which jq release introduced a CLI flag, language construct, builtin
function, or output format** this skill documents, so you know what works on an older (or newer)
jq. Use it to answer "is my jq new enough for X?" and "what do I need to upgrade to?"

**How to read this:**

- These are **jq release versions** (`MAJOR.MINOR[.PATCH]`, e.g. `1.7.1`). The `1.7+` form means
  "the 1.7 release and later." Each row's version is the **earliest release in which the feature
  is available**.
- Annotations are sourced from jq's **`NEWS.md`** release notes (primary), cross-checked against
  the **versioned manuals** (`docs/.../manual/{v1.5,v1.6,v1.7,v1.8}/manual.yml`), **git blame /
  first-appearance grep on `src/builtin.jq`**, and an **empirical run on the installed CLI
  (`jq-1.7.1`)** — a construct that runs on 1.7.1 is `≤ 1.7.1`; one that errors with
  `… is not defined` / `… is not a valid format` there is `≥ 1.8`. **No version is guessed:** a
  feature with no clean "added in vX" source is treated as long-standing and left out of the
  table.
- **Features not listed here are long-standing** — present at or before **jq 1.6** (released
  **November 2018**) and treated as **bedrock**, so they carry no version tag. This includes
  essentially the entire everyday surface: the core CLI flags (`-n -R -s -c -r -j -a -S -C -M -e
  -f -L -h -V`, plus `--tab` / `--indent N` / `--stream` / `--seq` / `--argjson` / `--slurpfile`
  / `--rawfile` / `--args` / `--jsonargs` / `--unbuffered` / `$ARGS`), the language core
  (`try/catch`, `?`, `label`/`break`, `foreach`, `reduce`, destructuring incl. `?//`,
  multi-arity defs, `..` recursive descent, `%` modulo), regex (`test`/`match`/`capture`/`scan`/
  `split`/`sub`/`gsub` via Oniguruma), the math/datetime libm builtins (`gmtime`/`mktime`/
  `strftime`/`strptime`/`now`/`localtime`/`strflocaltime`), the SQL-style builtins
  (`INDEX`/`IN`/`JOIN`), and the format strings `@base64`/`@base64d`/`@csv`/`@tsv`/`@json`/
  `@html`/`@uri`/`@sh`/`@text`. This file omits them to stay signal-rich.
- **Context for the version numbers:** jq 1.6 (2018) sat unchanged for nearly five years, so most
  "modern" features you reach for arrived in the big **1.7 (July 2023)** release, with a 1.7.1
  patch in December 2023. The **1.8 (2025)** line added the trim family and a handful of new
  builtins/behaviors, and is *newer than what many distros ship* — Debian/Ubuntu LTS and CentOS
  commonly still package 1.6 or 1.7.
- This skill is documented and verified against the installed CLI **`jq-1.7.1`**. Always confirm
  on the running system — see [Checking your version](#checking-your-version).

Rows marked **(breaking)** changed existing behavior in that release; review jq's `NEWS.md`
before upgrading.

## Contents

- [Versioned features (ascending by jq release)](#versioned-features-ascending-by-jq-release)
- [Removed builtins & flags](#removed-builtins--flags)
- [Checking your version](#checking-your-version)

## Versioned features (ascending by jq release)

Sorted ascending by minimum jq release; within a release, grouped by **Area**
(CLI / language / builtins / formats / streaming). Date/time builtins are all bedrock (≤ 1.6)
and therefore not listed.

| Min version | Feature | Area |
|---|---|---|
| 1.7+ | `--raw-output0` — output values NUL-separated (pairs with `xargs -0`) | CLI |
| 1.7+ | `--binary` / `-b` — open I/O in binary mode (Windows; no CRLF translation) | CLI |
| 1.7+ | `--build-configuration` — print how the binary was built | CLI |
| 1.7+ | `NO_COLOR` environment variable honored (disable color) | CLI |
| 1.7+ | `JQ_COLORS` gains an **8th field** (object-key color); truecolor escape support added in 1.8 | CLI |
| 1.7+ | `--stream-errors` — emit parse errors as `["error", …]` events (implies `--stream`) | streaming |
| 1.7+ | `if` with no `else` — the missing branch defaults to `.` | language |
| 1.7+ | Dot-before-bracket: `.a.["k"]`, `.a.[]`, `.a.[1]` | language |
| 1.7+ | `$var` usable as an object-literal key: `{$k: …}` | language |
| 1.7+ | `nan` accepted in JSON input | language |
| 1.7+ | `(…) \|= empty` deletes the matched array elements | language |
| 1.7+ | Decimal / large-integer literal precision preserved on round-trip & compare (arithmetic may still truncate) | language |
| 1.7+ | `abs` — absolute value (preserves literal precision) | builtins |
| 1.7+ | `pick(pathexps)` — project a subset of paths out of the input | builtins |
| 1.7+ | `debug(msgs)` — like `debug` but applies a filter to build the debug message | builtins |
| 1.7+ | `scan(re; flags)` (`scan/2`) — previously documented but not implemented | builtins |
| 1.7+ | `modulemeta` now also exposes a module's function names | builtins |
| 1.7.1+ | Inline filter program after `--` on the command line | CLI |
| 1.7.1+ | decimal-number → binary64 conversion behavior change (subtle numeric effect) *(breaking)* | language |
| 1.7.1+ | `getpath` / `paths` internal simplifications (behavior unchanged) | builtins |
| 1.8+ | `--library-path` — long-form alias of `-L` (`-L` itself is bedrock) | CLI |
| 1.8+ | `--indent 0` no longer implies compact output *(breaking)* | CLI |
| 1.8+ | Tcl-style `#` multiline comments / shebang line-continuation `\` trick | language |
| 1.8+ | CRLF line breaks allowed in filter programs (bare CR in comments since 1.7) | language |
| 1.8+ | Binding precedence vs unary/binary operators adjusted; more expressions allowed as object values *(breaking)* | language |
| 1.8+ | String `index` / `indices` / `rindex` use codepoint (not byte) offsets *(breaking)* | language |
| 1.8+ | `trim`, `ltrim`, `rtrim` — strip whitespace | builtins |
| 1.8+ | `trimstr(s)` — strip a prefix+suffix string from both ends | builtins |
| 1.8+ | `toboolean` — parse the strings `"true"`/`"false"` to booleans | builtins |
| 1.8+ | `add(f)` (`add/1`) — sum/concatenate the outputs of a generator | builtins |
| 1.8+ | `skip(n; g)` (`skip/2`) — drop the first `n` outputs of a generator (counterpart to `limit`) | builtins |
| 1.8+ | `have_literal_numbers`, `have_decnum` — build/precision introspection | builtins |
| 1.8+ | `ltrimstr` / `rtrimstr` now error on non-string input (was: pass through) *(breaking)* | builtins |
| 1.8+ | `last(empty)` yields nothing (now matching `first(empty)`) | builtins |
| 1.8+ | `@urid` — percent-decode (reverse of `@uri`) | formats |

## Removed builtins & flags

These were removed in the release shown — code relying on them breaks when you upgrade past it.
They are listed here for migration only and are **not** part of the "minimum version" table above.

| Removed in | Item | Replacement / note |
|---|---|---|
| 1.7 | `--argfile` flag | use `--slurpfile` (or `--arg` for a single value) |
| 1.7 | `leaf_paths` | use `paths(scalars)` |
| 1.7 | `recurse_down` | use `recurse` |
| 1.7 | `scalars_or_empty` (private/undocumented) | — |
| 1.8 | `pow10` | use `exp10` |
| 1.8 | `_nwise` (private/undocumented) | — |

## Checking your version

Check what you are running:

```
jq --version          # e.g. jq-1.7.1
```

The current released line is **1.8.x** (2025); the long-standing **bedrock is 1.6** (2018), which
many Linux LTS distros still ship. Because jq does **not** backport features to old release lines,
the "Min version" column is a hard floor: a feature tagged `1.8+` simply is not present on 1.7.x —
upgrade the binary to pick it up.

For scripts that must run across unknown jq versions, either gate on `jq --version`, or
feature-probe and fall back, e.g.:

```bash
jq -n 'def _f: trim; 1' >/dev/null 2>&1 && echo "have 1.8 trim" || echo "pre-1.8"
```

When you can't control the installed jq, stick to **bedrock (≤ 1.6)** builtins and avoid the
1.7/1.8 rows above.
