---
name: jq
description: jq — the command-line JSON processor and its filter language for slicing, filtering, transforming, and reshaping JSON. Use when extracting fields or nested paths from JSON on the command line, filtering/`select`-ing arrays of objects, reshaping or building new JSON objects, emitting CSV/TSV with `@csv`/`@tsv`, getting raw unquoted strings for shell capture with `jq -r`, slurping (`-s`) and aggregating JSON (`add`, `group_by`, averages), parsing API responses, NDJSON pipelines (`-c`), or injecting shell values safely with `--arg`/`--argjson`/`$ENV`. Triggers on mentions of jq, the `jq` command, the jq filter language, `jq -r`, `.foo`/`.[]` filters, `@csv`/`@tsv`, slurp/`fromjson`, or "filter/transform JSON in the terminal". This is the jq CLI and filter language, NOT a generic JSON tutorial and NOT jq language bindings (jaq, gojq, PyPI `jq` — defer those to their own docs).
---

# jq - Command-Line JSON Processor

## Overview

jq is a small, fast command-line tool that **runs a *filter* program over JSON**. You write a
tiny program (the *filter*), jq reads JSON value(s) from stdin or files, runs the filter once
**per input value**, and prints each produced value back as JSON. Think of it as `sed`/`awk` for
structured JSON instead of lines of text.

**Key characteristics:**
- **A filter = a function** from one JSON value to *zero, one, or many* JSON values
- **Composable like a shell pipeline** — `|` pipes one filter's output into the next
- **Pure & functional** — no mutation; "assignment" returns a *modified copy*
- **Streaming by default** — reads whitespace-separated values, runs the filter on each
- **Deterministic, no TTY** — pure stdin→stdout, ideal for scripts, CI, and agents

### Mental model (read this first — it prevents the #1 source of confusion)

**A jq program is a filter: an input *stream* of JSON values → an output *stream* of JSON values.**

- The simplest filter is `.` (identity) — it copies input to output, pretty-printed.
- A filter can emit **0 values** (`empty`, a failed `select`), **1 value** (`.foo`), or
  **many** (`.[]`, `range(3)`). When a filter emits many values, everything downstream runs
  **once per value** (a generator / backtracking model).
- **`|` pipes**, exactly like a Unix shell: `f | g` runs `g` on each output of `f`.
- **`,` forks**: `f, g` emits all of `f`'s values, then all of `g`'s.
- jq never mutates the input. `|=` and `=` produce a *new* value with the change applied.

```bash
echo '{"a":1,"b":2}' | jq '.a'          # 1            (one value)
echo '[1,2,3]'       | jq '.[]'          # 1 2 3        (a stream of three)
echo '{"a":1,"b":2}' | jq '.a, .b'       # 1 2          (, forks the stream)
echo '[1,2,3]'       | jq '[.[] | .+10]' # [11,12,13]   (| pipes; [...] re-collects)
```

> **Disambiguation:** This skill documents the **`jq` CLI and its filter language** — invocation,
> I/O modes, the filter syntax, and the builtin library. It is **not** a generic JSON tutorial,
> and it does **not** cover jq-compatible reimplementations (`jaq`, `gojq`) or library bindings
> (Python `jq`, etc.) — for those, see their own docs.

## Prerequisites

**CRITICAL**: Before proceeding, verify jq is installed and check the version:

```bash
jq --version        # prints e.g. "jq-1.7.1"
```

**Version note:** This skill is documented against **jq 1.7 / 1.7.1** (the modern baseline, the big
release after a 5-year gap). Everything stable **at or before jq 1.6** is "bedrock" and shown
**unannotated**. Features added later are tagged inline as `(jq 1.7+)` / `(jq 1.8+)` **only where
the version is sourced** — see [references/version-features.md](references/version-features.md) for
the full feature → minimum-version map. Distros vary widely (many Linux LTS still ship 1.6 or
1.7); always confirm with `jq --version`. If a function errors with **"is not defined"**, it is
likely newer than your jq.

## Install

jq is a single self-contained binary with no runtime dependencies.

```bash
# macOS
brew install jq

# Debian/Ubuntu
sudo apt-get install jq

# Fedora/RHEL
sudo dnf install jq

# Arch
sudo pacman -S jq

# Alpine
apk add jq

# Windows
winget install jqlang.jq      # or: choco install jq / scoop install jq

# Docker (images moved to ghcr.io in 1.7)
docker run -i ghcr.io/jqlang/jq

# Static binaries / source: https://github.com/jqlang/jq/releases
```

Homepage **https://jqlang.org**; online playground **https://play.jqlang.org**.

## Invocation at a Glance

```bash
echo '<json>' | jq '<filter>'          # most common: pipe JSON in via stdin
jq '<filter>' file.json                # read from one or more files
jq -c '<filter>' file.json             # compact output (one value per line ⇒ NDJSON)
jq -r '<filter>'                       # raw output: strings without JSON quotes (shell capture)
jq -n '<filter>'                       # no input: filter starts from null (generate / use $ARGS,$ENV)
jq -f program.jq file.json             # load the filter from a file
jq --arg name "Ada" '<filter>'         # inject a shell value as $name (a string)
```

**Usage:** `jq [options] <filter> [file...]`. With no files, jq reads stdin. The filter is a
program in the jq language; the most useful invocation flags:

| Flag | Meaning |
|------|---------|
| `-n` / `--null-input` | Don't read input; run the filter once with `null`. For generators, `$ARGS`, `$ENV`. |
| `-r` / `--raw-output` | Output strings **without** JSON quotes/escapes (non-strings unchanged). |
| `-c` / `--compact-output` | Compact — one value per line ⇒ NDJSON output. |
| `-s` / `--slurp` | Read **all** inputs into a single array; run the filter once on that array. |
| `-R` / `--raw-input` | Read each line as a JSON **string** (not parsed JSON); with `-s`, the whole input as one string. |
| `-e` / `--exit-status` | Set exit code from the last output (see Troubleshooting). |
| `-j` / `--join-output` | Implies `-r`; no newline between outputs. |
| `-S` / `--sort-keys` | Sort object keys in output. |
| `-f file` / `--from-file` | Load the filter program from a file. |
| `--arg n v` / `--argjson n v` | Bind `$n` to a **string** / a parsed **JSON** value. |

> **Always single-quote the filter** in the shell — jq programs use `$`, `()`, `[]`, `|`, `"`,
> which the shell would otherwise mangle. Inject data with `--arg`/`--argjson`/`$ENV` rather than
> string-interpolating shell values into the program (safer; no quoting or injection bugs).

Full flag reference, I/O modes, arg-passing, exit codes, and module path:
[references/cli.md](references/cli.md).

## Core Workflows

All examples below are runnable and verified on jq 1.7.1.

### 1. Pretty-print / validate JSON

`jq .` reformats (pretty-prints) and exits non-zero on invalid JSON — a cheap validator.

```bash
jq . file.json                  # pretty-print
jq -c . file.json               # re-emit compact (one line)
jq -e . file.json >/dev/null    # validate: exit ≠ 0 ⇒ invalid JSON
```

### 2. Extract a field / nested path (use `-r` for shell capture)

```bash
jq '.user.name'    file.json    # nested object index → "Ada"  (JSON-quoted)
jq '.items[0].id'  file.json    # array index
jq -r '.user.name' file.json    # raw → Ada  (no quotes — what you want for the shell)
NAME=$(jq -r '.user.name' file.json)   # capture a string into a shell variable
```

Indexing a **missing** key yields `null` (not an error). Use `?` to suppress type errors
(`.a.b?`) and `// "default"` for a fallback (see Troubleshooting).

### 3. Filter a list of objects with `select` / pull a field from each

```bash
jq -c '.[] | select(.age > 30)' people.json   # one matching object per line
jq -r '.[] | .email'            people.json    # one email per line
jq    'map(select(.active))'    people.json    # keep the array shape, filtered
```

`.[]` iterates the array into a stream; `select(f)` keeps a value only when `f` is truthy
(only `false` and `null` are falsy — `0`, `""`, `[]` are **truthy**).

### 4. Reshape / build new objects

```bash
jq '[.[] | {id, name: .fullName, active: (.status == "on")}]' people.json
```

`{id}` is shorthand for `{id: .id}`. Object construction inside `[ ... ]` collects every produced
object back into one array. Computed keys: `{(.k): .v}`.

### 5. Emit CSV / TSV (and read line-oriented text)

```bash
# JSON array of objects → CSV rows (‑r so quotes/escapes are literal)
jq -r '.[] | [.id, .name, .amount] | @csv' file.json
jq -r '.[] | [.id, .name] | @tsv'          file.json   # tab-separated

# Lines of text → JSON array  (raw input + slurp = the whole stdin as one string)
jq -R -s 'split("\n")' file.txt
```

`@csv`/`@tsv` take an **array** and produce one delimited row, correctly quoting/escaping.
Format list (no `@base32` — it doesn't exist): `@text @json @base64 @base64d @uri @csv @tsv @html @sh`.

### 6. Slurp + aggregate (sum, average, group)

```bash
printf '{"x":1}\n{"x":2}\n{"x":3}\n' | jq -s 'map(.x) | add'      # 6  (slurp NDJSON → array)
jq '[.[].amount] | add'                          orders.json      # sum a field
jq 'map(.score) | add/length'                    scores.json      # average
jq 'group_by(.dept) | map({dept: .[0].dept, n: length})' rows.json  # group + count
```

`-s` (slurp) reads **all** input values into one array, then runs the filter once — the standard
way to aggregate across an NDJSON stream or multiple files.

### 7. Pass shell values safely with `--arg`, and reuse programs with `-f`

```bash
# Inject a string as $name (no shell-quoting hazards); --argjson for parsed JSON
jq --arg name "Ada Lovelace" '.[] | select(.fullName == $name)' people.json
jq --argjson min 30 '.[] | select(.age >= $min)'                people.json

# Read a secret from the environment without shell interpolation
TOKEN=… jq -n '{auth: ("Bearer " + $ENV.TOKEN)}'

# Generate from nothing with -n, then save a reusable program with -f
jq -nc '{ts: now, items: ($ARGS.positional)}' --args a b c
jq -f transform.jq data.json
```

`--arg`/`--argjson` also populate `$ARGS.named`; `--args`/`--jsonargs` fill `$ARGS.positional`.
`$ENV` is an object of environment variables — prefer `$ENV.TOKEN` over a shell `"$TOKEN"`.

## Non-Interactive / Agent Usage

jq is excellent for scripts and agents — it never prompts and is pure stdin→stdout.

```bash
# Branch on JSON content via exit code (-e sets status from the last output)
if jq -e '.ok' resp.json >/dev/null; then echo healthy; fi

# Test-and-extract with a meaningful exit code; // empty drops nulls
jq -e '.token // empty' resp.json

# NDJSON pipeline: compact out, line tooling friendly
jq -c '.[]' big.json | while read -r line; do …; done

# Pull a second file in without shell interpolation
jq --slurpfile cfg config.json '. + $cfg[0]' data.json
jq --rawfile body message.txt   '{subject:"hi", body:$body}'

# Stream a huge document leaf-by-leaf (doesn't fit in memory)
jq -n --stream 'fromstream(1 | truncate_stream(inputs))' huge.json
```

**Agent tips:** prefer `-r` + `--arg` to feed other tools without quoting bugs; use `-c` for
NDJSON; use `-e` to branch on content; use `--slurpfile`/`--rawfile`/`$ENV` to combine inputs and
secrets without interpolation; validate cheaply with `jq -e . file >/dev/null`. More patterns:
[references/cli.md](references/cli.md).

## Quick Reference

| Item | Purpose |
|------|---------|
| `.` | Identity — copy input to output (pretty-printed) |
| `.foo` · `.foo.bar` · `.["a b"]` | Object index (dot or bracket; bracket for odd keys) |
| `.[0]` · `.[-1]` · `.[2:5]` | Array index (negative from end) / slice (arrays & strings) |
| `.[]` · `.[]?` | Iterate array/object values into a stream (`?` suppresses non-iterable error) |
| `f \| g` · `f, g` | **Pipe** g over f's outputs / **fork** (concatenate streams) |
| `[ f ]` · `{a: .x, b: .y}` · `{id, name}` | Collect into array / build object / shorthand keys |
| `select(f)` · `map(f)` · `map_values(f)` | Keep when truthy / `[.[]\|f]` / per-value update |
| `add` · `length` · `keys` · `has(k)` · `type` | Sum/concat · count · sorted keys · key present? · value type |
| `group_by(f)` · `sort_by(f)` · `unique_by(f)` · `min_by/max_by` | Grouping & ordering by a key |
| `to_entries` · `from_entries` · `with_entries(f)` | Object ↔ `[{key,value}]` transforms |
| `// "default"` | Alternative: value of LHS unless null/false, else RHS |
| `.a \|= f` · `.a = v` · `.a += 1` · `del(.a)` | Update-in-place (copy) / set / arithmetic update / delete |
| `if C then T elif … else E end` | Conditional (`else` optional, defaults to `.`, jq 1.7+) |
| `try f catch g` · `f?` | Error handling (`f?` ≡ `try f` ⇒ empty on error) |
| `reduce G as $x (INIT; UPD)` · `foreach …` | Fold over a stream / fold that emits each step |
| `@csv` `@tsv` `@json` `@base64` `@uri` `@sh` `@html` | Format/encode (filter, or string-interp prefix) |
| `test/match/capture/scan/sub/gsub(re; flags)` | Regex (Oniguruma): flags `g i x s m` |
| `now` · `todate` · `fromdate` · `strftime(fmt)` | Time: epoch seconds is the lingua franca |
| `--arg n v` · `--argjson n v` · `$ENV` · `$ARGS` | Inject shell string / JSON / env / CLI args |
| `input` · `inputs` | Pull the next / all remaining input values (with `-n`) |

## Troubleshooting

- **Strings print with quotes** — that's JSON. Use **`-r`** for raw output when capturing into a
  shell variable: `NAME=$(jq -r .name f.json)`.
- **`null` vs error** — indexing a *missing* object key yields `null` (not an error); indexing the
  *wrong type* is an error (`Cannot index array with "foo"`). Suppress with `?` (`.a.b?`); supply a
  fallback with `// "default"`.
- **`//` is "alternative", not boolean OR** — `a // b` yields `a` when `a` produces a value that is
  **not null and not false**, else `b` (it also swallows errors in `a`). Great for defaults;
  boolean OR is `or`.
- **Empty output is usually not a crash** — a `select`/filter matched nothing, you used `empty`, or
  a `?` swallowed an error. Check the filter, not the install.
- **Multiple results print one per line** — wrap the filter in `[ ... ]` to collect them into a
  single array.
- **"X is not defined" / "X is not a valid format"** — the function/format is newer than your jq
  (e.g. `trim`/`trimstr`/`toboolean` need jq 1.8+; `abs`/`pick`/`debug(msgs)` need jq 1.7+). Check
  `jq --version` and [references/version-features.md](references/version-features.md). (`@base32`,
  `toarray`, and `dateadd` do **not** exist in any jq version.)
- **Big-number math is lossy** — since jq 1.7 the literal decimal precision is preserved on
  round-trip/compare, but **arithmetic** still uses IEEE-754 doubles (`1e17 + 10` → `…020`). Don't
  rely on jq for big-integer math.
- **Shell quoting** — single-quote the program; inject data with `--arg`/`--argjson`, never string
  concatenation. `--argfile` was **removed in jq 1.7** — use `--slurpfile`/`--arg`.
- **Date math has no `dateadd`** — do arithmetic on epoch seconds: `now + 86400 | todate`. Note
  `gmtime`/`mktime` use a broken-down array `[year, month(0-11), mday, hour, min, sec, wday, yday]`
  (month is **0-indexed**).

## References

For exhaustive detail, see the bundled reference files:

- [references/cli.md](references/cli.md) — every command-line flag, the I/O / slurp / raw modes,
  argument passing & special variables (`$ARGS`/`$ENV`/`$__loc__`), exit codes, modules & search
  path, and non-interactive/agent patterns.
- [references/language.md](references/language.md) — the filter language: paths, composition
  (`|`/`,`), construction, operators, conditionals & error handling, `reduce`/`foreach`, variables
  & destructuring, functions, assignment/path semantics, string interpolation, and comments.
- [references/builtins.md](references/builtins.md) — the builtin library grouped by purpose:
  types, arrays/objects, strings & regex, the `@fmt` format strings, math, dates/time, streaming,
  SQL-style (`INDEX`/`IN`/`JOIN`), and debugging/control.
- [references/version-features.md](references/version-features.md) — feature → minimum jq version
  map (bedrock ≤1.6 vs. what landed in 1.7 / 1.7.1 / 1.8), removed features, and "what version do
  I need?" guidance.

## Resources

- **Help**: `jq --help`, and the manual at https://jqlang.org/manual/
- **Homepage**: https://jqlang.org
- **Playground**: https://play.jqlang.org
- **Source / releases**: https://github.com/jqlang/jq
