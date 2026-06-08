# jq CLI Reference

Complete reference for the `jq` command line: invocation forms, every command-line flag,
the input / output / slurp modes, argument passing and special variables (`$ARGS`, `$ENV`),
exit codes, the module search path, and non-interactive / agent usage patterns.

`jq` is a filter: it reads JSON value(s) from stdin or files, runs the filter **once per
input value**, and prints each produced value as JSON on stdout. It never prompts and needs
no TTY — pure stdin → stdout — which makes it ideal inside scripts, CI, and agent pipelines.

> **Verification & version annotations.** Every flag and behavior below was confirmed against
> the installed **`jq-1.7.1` (`jq-1.7.1-apple`)** via `jq --help`, the upstream versioned
> manuals, and empirical runs (exit codes, `$ARGS`, `$ENV`, `--slurpfile`/`--rawfile`,
> `--stream`, `get_search_list`). **Treat jq 1.6 and earlier as bedrock — left unannotated.**
> Only items with a sourced release carry a `(jq 1.X+)` tag; the big modern release is
> **jq 1.7 (2023)** after a 5-year gap, with **1.8 (2025)** adding more. Check your build with
> `jq --version` (e.g. `jq-1.7.1`) — distros vary widely (many Linux LTS still ship 1.6/1.7).

## Table of Contents

- [Invocation](#invocation)
- [Flag reference](#flag-reference)
- [Input / output / slurp modes](#input--output--slurp-modes)
- [Argument passing & special variables](#argument-passing--special-variables)
- [Exit codes](#exit-codes)
- [Modules & search path](#modules--search-path)
- [Non-interactive / agent patterns](#non-interactive--agent-patterns)
- [Gotchas](#gotchas)

---

## Invocation

```
jq [options] <filter> [file...]
jq [options] --args     <filter> [strings...]    # extra args → $ARGS.positional (as strings)
jq [options] --jsonargs <filter> [JSON_TEXTS...]  # extra args → $ARGS.positional (parsed JSON)
```

```bash
echo '{"a":1}' | jq '.a'           # most common: pipe JSON in on stdin
jq '.users[0].name' data.json      # read from one or more files
jq -n '<filter>'                    # no input; filter starts from null (generate / use $ARGS,$ENV)
jq -f filter.jq data.json           # load the filter program from a file
cat *.json | jq -s 'add'            # slurp many inputs into one array
```

- **The simplest filter is `.`** (identity) — it copies input to output, pretty-printed.
  `jq . file.json` reformats/validates; `jq -c .` compacts.
- **Always single-quote the filter** in the shell — jq programs use `$ ( ) [ ] | "` which the
  shell would otherwise mangle. Inject shell values with `--arg`/`--argjson` (see below) rather
  than string-interpolating into the program — it avoids quoting bugs and injection.
- **`[file...]`** are concatenated into one input stream. With **no files**, jq reads stdin.
  `-n`/`--null-input` ignores input entirely.
- **`--`** terminates option processing; the next token is taken literally (as the filter, or as
  positionals under `--args`/`--jsonargs`). An inline filter is allowed right after `--`
  (`jq -- '.+1'`) `(jq 1.7.1+)`.

---

## Flag reference

Verified verbatim against `jq --help` on 1.7.1. Bedrock flags are unannotated; sourced
version tags are inline.

### Output formatting

| Flag | Short | Meaning |
|------|-------|---------|
| `--compact-output` | `-c` | Compact output — no pretty-printing, one value per line (⇒ NDJSON). |
| `--raw-output` | `-r` | Output strings **without** JSON quotes/escapes (non-strings unchanged). The usual choice for capturing a string into a shell variable. |
| `--raw-output0` | | Implies `-r` and writes a **NUL** (`\0`) after each output — pairs with `xargs -0`. Errors if an output string contains a NUL. `(jq 1.7+)` |
| `--join-output` | `-j` | Implies `-r` and writes **no newline** after each output. |
| `--ascii-output` | `-a` | Escape all non-ASCII characters to `\uXXXX`. |
| `--sort-keys` | `-S` | Sort object keys in the output. |
| `--color-output` | `-C` | Force colorized JSON output (e.g. when piping). |
| `--monochrome-output` | `-M` | Disable colored output. |
| `--tab` | | Indent with tabs. `(jq 1.5+)` |
| `--indent n` | | Indent with `n` spaces (max 7). On 1.7.1 `--indent 0` gives no newlines but is **not** the same as `-c`; that quirk was fixed in 1.8. `(jq 1.5+)` |
| `--unbuffered` | | Flush the output stream after each value — for real-time/streaming pipes. |

Color is also configurable via the **`JQ_COLORS`** env var (8 fields incl. object keys on 1.7;
truecolor on 1.8) `(jq 1.7+)`, and **`NO_COLOR`** disables color entirely `(jq 1.7+)`.

### Input control

| Flag | Short | Meaning |
|------|-------|---------|
| `--null-input` | `-n` | **Don't read input**; run the filter once with `null` as the input. Use for generators, `$ARGS`, `$ENV`, or pulling inputs on demand with `input`/`inputs`. |
| `--raw-input` | `-R` | Read each **line** as a JSON string instead of parsing JSON. With `-s`, read the **entire** input as one string. |
| `--slurp` | `-s` | Read **all** inputs into a single array and run the filter once on that array. |
| `--stream` | | Parse the input in streaming fashion — emit `[path, leaf]` pairs (and `[path]` end markers) instead of whole values. For inputs too big to hold in memory. `(jq 1.5+)` |
| `--stream-errors` | | Implies `--stream`; report a parse error as a `[[path], "msg"]` array instead of aborting. `(jq 1.7+)` |
| `--seq` | | Use `application/json-seq` (RFC 7464): input/output values are framed by the RS byte (`0x1E`). `(jq 1.5+)` |

### Filter & module source

| Flag | Short | Meaning |
|------|-------|---------|
| `--from-file file` | `-f` | Load the filter **program** from a file (instead of the command line). |
| `-L directory` | | Prepend `directory` to the module search path. Repeatable; `-L dir` or `-Ldir`. The long form `--library-path` exists only on **jq 1.8+** (not 1.7.1). |

### Argument / variable binding

| Flag | Meaning |
|------|---------|
| `--arg name value` | Bind `$name` to the **string** `value` (also appears in `$ARGS.named`). |
| `--argjson name value` | Bind `$name` to the parsed **JSON** `value`. `(jq 1.5+)` |
| `--slurpfile name file` | Bind `$name` to an **array** of all JSON values read from `file`. `(jq 1.5+)` |
| `--rawfile name file` | Bind `$name` to the **string** contents of `file`. `(jq 1.6+)` |
| `--args` | Treat remaining command-line args as **positional strings** → `$ARGS.positional`. `(jq 1.6+)` |
| `--jsonargs` | Treat remaining command-line args as **positional parsed JSON** → `$ARGS.positional`. `(jq 1.6+)` |

### Status, info & control

| Flag | Short | Meaning |
|------|-------|---------|
| `--exit-status` | `-e` | Set the process exit status from the last output value (see [Exit codes](#exit-codes)). |
| `--binary` | `-b` | (Windows only) binary output — no CRLF translation. `(jq 1.7+)` |
| `--version` | `-V` | Print the version string and exit. |
| `--build-configuration` | | Print jq's build configuration and exit. `(jq 1.7+)` |
| `--help` | `-h` | Show help and exit. |
| `--` | | End of options; the next token is the filter (or positionals under `--args`/`--jsonargs`). |

> **Removed flag — do NOT use:** `--argfile name file` was **removed in jq 1.7** and errors on
> 1.7.1 (`jq: Unknown option --argfile`). Use **`--slurpfile`** (array of values from the file)
> or **`--rawfile`** (file contents as a string), or `--arg`/`--argjson` for inline values.

---

## Input / output / slurp modes

The `-n` / `-R` / `-s` flags combine into the input-handling matrix that trips up newcomers:

| Mode | What jq does |
|------|--------------|
| *(default)* | Parse a stream of whitespace-separated JSON values; run the filter **once per value**. NDJSON in. |
| `-s` (slurp) | Collect **all** input values into one array; run the filter **once**. E.g. sum across NDJSON: `jq -s 'map(.x) \| add'`. |
| `-R` (raw input) | Treat each **line** as a JSON string; run the filter once per line. E.g. defensively parse NDJSON with `jq -R 'fromjson'`. |
| `-R -s` (raw + slurp) | The **entire** input (newlines included) becomes one big string. E.g. `jq -Rs 'split("\n")'`. |
| `-n` (null input) | Ignore input entirely; `.` is `null`. Combine with `input`/`inputs` to pull values on demand, or with `$ARGS`/`$ENV` to generate. |

On the output side: `-c` compacts (one value per line ⇒ NDJSON out), `-r` drops string quotes,
`-j` drops the trailing newline, `--raw-output0` NUL-separates, `-a` escapes non-ASCII.

**Pull-based input builtins** (handy with `-n`): `input` (read the next value), `inputs`
(stream all remaining values), `input_filename`, `input_line_number`, `$__loc__`.

```bash
# Sum the .amount field across an NDJSON stream
cat events.ndjson | jq -s 'map(.amount) | add'

# Each input line → a JSON object
printf 'a\nb\n' | jq -R '{line: .}'

# Whole file as one string, split into an array
jq -Rs 'split("\n")' notes.txt

# Generate without input
jq -n '[range(3)]'                 # => [0,1,2]
```

---

## Argument passing & special variables

| Source | Binds |
|--------|-------|
| `--arg n v` | `$n` (string) **and** `$ARGS.named.n` |
| `--argjson n v` | `$n` (parsed JSON) **and** `$ARGS.named.n` |
| `--slurpfile n f` | `$n` = array of JSON values from file `f` |
| `--rawfile n f` | `$n` = string contents of file `f` |
| `--args A B …` | `$ARGS.positional` = `["A","B",…]` (strings) |
| `--jsonargs A B …` | `$ARGS.positional` = parsed JSON of each arg |

- **`$ARGS`** is `{ "positional": [...], "named": {...} }`. Named args (`--arg`/`--argjson`)
  always show up in `$ARGS.named`; positional args (`--args`/`--jsonargs`) in `$ARGS.positional`.
- **`$ENV`** is an object of environment variables (snapshot at startup); **`env`** is the builtin
  returning the current environment. **Prefer `$ENV.TOKEN` over shell `"$TOKEN"` interpolation** —
  no quoting or injection risk. Both `jq -n '$ENV.HOME'` and `jq -n 'env.HOME'` work on 1.7.1.
- **`$__loc__`** → `{"file","line"}` of its own source location; useful in error/debug messages.
- There is **no** `$__prog_args` — positional CLI args are `$ARGS.positional`.

```bash
# Inject shell values safely — no quoting/injection issues
name="O'Brien"
jq -n --arg n "$name" '{greeting: ("hi " + $n)}'

# Positional args, parsed as JSON
jq -n --jsonargs '$ARGS.positional | add' 1 2 3        # => 6

# Read a secret from the environment, never the command line
TOKEN=abc123 jq -n '{auth: ("Bearer " + $ENV.TOKEN)}'

# Pull a second file in as a variable (array of values)
jq --slurpfile extra extra.json '. + $extra' main.json
```

---

## Exit codes

jq's exit status (all verified empirically on 1.7.1):

| Situation | Exit |
|-----------|------|
| Normal success | `0` |
| `-e` and the **last** output value is `false` or `null` | `1` |
| Usage / CLI error (bad or unknown flag) | `2` |
| Compile error in the jq program | `3` |
| `-e` and **no** output was produced at all | `4` |
| Runtime error · JSON parse error · `error`/`error(msg)` · `halt_error` (default) | `5` |
| `halt` | `0` (exits immediately, success) |
| `halt_error(n)` | `n` (custom code) |

Notes:
- **`-e`/`--exit-status` only matters for codes `1` and `4`.** Without `-e`, a `false`/`null`/
  no-output run still exits `0`. The status is based on the **last** output value, so
  `jq -ne '1,2'` exits `0` (last value `2` is truthy).
- Verified: `jq -ne true`→`0`, `jq -ne false`→`1`, `jq -ne null`→`1`, `jq -ne empty`→`4`,
  compile error `jq '.['`→`3`, bad input parse→`5`, `error("x")`→`5`, `halt`→`0`,
  `halt_error`→`5`, `halt_error(7)`→`7`, unknown flag→`2`.
- jq 1.7 fixed several exit-status bugs; on older jq the `-e` codes can be less reliable.

This makes `-e` a clean branch primitive: `if jq -e '.ok' resp.json >/dev/null; then …`.

---

## Modules & search path

- Pull in modules at the **top** of a program (or `-f` file):
  `import "path/module" as ns;` / `include "path/module";`. Optional metadata:
  `import "m" as m {search: "..."};`. A data file can be imported as a variable:
  `import "data" as $d;`.
- Module files are `.jq`. The search path is built from any **`-L dir`** entries (repeatable)
  prepended to the default `$ORIGIN`-relative list. On 1.7.1 the default
  (`jq -n 'get_search_list'`) is:

  ```json
  ["~/.jq", "$ORIGIN/../lib/jq", "$ORIGIN/../lib"]
  ```

  `~/.jq` is auto-loaded as a **personal library** — drop helper `def`s there (it may be a file
  or a directory).
- Introspection builtins: **`get_search_list`** (effective path), **`modulemeta`** (a module's
  metadata; since 1.7 it also exposes the module's function names),
  `get_jq_origin`/`get_prog_origin` (`$ORIGIN` resolution).

---

## Non-interactive / agent patterns

jq is built for this: deterministic, no TTY, pure stdin→stdout, meaningful exit codes.

```bash
# Branch on JSON content via exit code (-e)
if jq -e '.status == "ok"' resp.json >/dev/null; then echo healthy; fi

# Cheap JSON validator — nonzero exit ⇒ invalid JSON
jq -e . file.json >/dev/null || echo "invalid JSON"

# Capture a string cleanly into a shell variable (note -r)
name=$(jq -r '.user.name' user.json)

# NUL-safe streaming into xargs (filenames with spaces/newlines)
jq -r --raw-output0 '.files[]' manifest.json | xargs -0 ls -l

# NDJSON pipeline — one compact value per line
jq -c '.[] | select(.active)' users.json | while read -r line; do …; done

# Combine inputs / secrets without shell interpolation
jq --slurpfile cfg config.json --rawfile key key.pem -n \
   '{config: $cfg[0], key: $key, token: $ENV.TOKEN}'

# Stream a huge document leaf-by-leaf (won't fit in memory)
jq -n --stream 'fromstream(1 | truncate_stream(inputs))' huge.json

# Real-time pass-through to a downstream consumer
tail -f log.ndjson | jq --unbuffered -c '{ts, level, msg}'
```

**Agent checklist:**

- **`-r`** whenever the output feeds another tool as a plain string (drops the JSON quotes).
- **`-e`** to turn JSON content into a process exit code for `if`/`&&`/`||`.
- **`-c`** for NDJSON pipelines (one value per line, line-tooling friendly).
- **`--raw-output0` + `xargs -0`** for safe filename/argument streaming `(jq 1.7+)`.
- **`--arg`/`--argjson`/`$ENV`** to inject data and secrets — never string-concatenate into the
  program.
- **`--slurpfile`/`--rawfile`** to read additional files in without a second process.
- **`--stream`** for inputs too large for memory; **`--unbuffered`** for real-time output.

---

## Gotchas

- **`-r` is for strings only.** Without `-r`, strings print with JSON quotes (`"foo"`); `-r`
  removes them but leaves non-strings (numbers, objects) untouched. `name=$(jq -r .name f.json)`
  is almost always what you want for shell capture.
- **`-e` is based on the *last* output, not "did it match".** `jq -ne '1,2'` exits `0`. To test
  "did this produce anything," combine with `// empty` and rely on the **`4`** (no-output) code:
  `jq -e '.field // empty'`.
- **`-n` ignores input.** With `-n`, `.` is `null`; you must use `input`/`inputs` to read values.
  Forgetting `-n` (or adding it by mistake) is a common "why is my input empty/`null`" bug.
- **`-s` changes the shape.** After `-s`, your filter sees **one array** of all inputs, not each
  value — `.` is the whole array. Combine carefully with `-R` (`-Rs` ⇒ one big string).
- **`--argfile` is gone** (removed in 1.7) — use `--slurpfile`/`--rawfile`. `-b`/`--binary` only
  does anything on Windows.
- **`--library-path` is jq 1.8+.** On 1.7.1 only the short `-L` form exists (the long form errors
  with `Unknown option`).
- **"X is not defined" / "not a valid format" usually means your jq is too old.** Newer builtins
  (`abs`, `pick` need 1.7; `trim` needs 1.8) error on older binaries — check `jq --version`.
- **Quoting:** single-quote the program in the shell; pass data via `--arg`/`--argjson`, not
  string concatenation.

---

## Appendix: `jq --help` (1.7.1, verbatim)

```
jq - commandline JSON processor [version 1.7.1-apple]

Usage:	jq [options] <jq filter> [file...]
	jq [options] --args <jq filter> [strings...]
	jq [options] --jsonargs <jq filter> [JSON_TEXTS...]

jq is a tool for processing JSON inputs, applying the given filter to
its JSON text inputs and producing the filter's results as JSON on
standard output.

The simplest filter is ., which copies jq's input to its output
unmodified except for formatting. For more advanced filters see
the jq(1) manpage ("man jq") and/or https://jqlang.github.io/jq/.

Example:

	$ echo '{"foo": 0}' | jq .
	{
	  "foo": 0
	}

Command options:
  -n, --null-input          use `null` as the single input value;
  -R, --raw-input           read each line as string instead of JSON;
  -s, --slurp               read all inputs into an array and use it as
                            the single input value;
  -c, --compact-output      compact instead of pretty-printed output;
  -r, --raw-output          output strings without escapes and quotes;
      --raw-output0         implies -r and output NUL after each output;
  -j, --join-output         implies -r and output without newline after
                            each output;
  -a, --ascii-output        output strings by only ASCII characters
                            using escape sequences;
  -S, --sort-keys           sort keys of each object on output;
  -C, --color-output        colorize JSON output;
  -M, --monochrome-output   disable colored output;
      --tab                 use tabs for indentation;
      --indent n            use n spaces for indentation (max 7 spaces);
      --unbuffered          flush output stream after each output;
      --stream              parse the input value in streaming fashion;
      --stream-errors       implies --stream and report parse error as
                            an array;
      --seq                 parse input/output as application/json-seq;
  -f, --from-file file      load filter from the file;
  -L directory              search modules from the directory;
      --arg name value      set $name to the string value;
      --argjson name value  set $name to the JSON value;
      --slurpfile name file set $name to an array of JSON values read
                            from the file;
      --rawfile name file   set $name to string contents of file;
      --args                consume remaining arguments as positional
                            string values;
      --jsonargs            consume remaining arguments as positional
                            JSON values;
  -e, --exit-status         set exit status code based on the output;
  -V, --version             show the version;
  --build-configuration     show jq's build configuration;
  -h, --help                show the help;
  --                        terminates argument processing;

Named arguments are also available as $ARGS.named[], while
positional arguments are available as $ARGS.positional[].
```
