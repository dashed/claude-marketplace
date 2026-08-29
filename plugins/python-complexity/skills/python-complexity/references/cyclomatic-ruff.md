# Cyclomatic complexity from ruff (`C901`)

`C901` (`complex-structure`, from the `mccabe` plugin) is normally a CI gate: "fail if any function
exceeds 10". Inverted, it is a **read-only measurement tool** — set the threshold below every real
score and ruff prints one line per function with its exact McCabe number.

Every behavior on this page was executed against **ruff 0.12.7, 0.16.3, and 0.16.5**. Differences
are called out inline; where nothing is said, all three behave identically.

## Table of contents

- [The threshold-inversion technique](#the-threshold-inversion-technique)
- [Exit codes](#exit-codes)
- [Output formats](#output-formats)
- [Ranked scans](#ranked-scans)
- [Config interference and `--isolated`](#config-interference-and---isolated)
- [Suppression that `--isolated` does not fix](#suppression-that---isolated-does-not-fix)
- [What ruff's McCabe actually counts](#what-ruffs-mccabe-actually-counts)
- [Scope and granularity](#scope-and-granularity)
- [Caching and `--no-cache`](#caching-and---no-cache)
- [Version differences](#version-differences)
- [Flag relevance map](#flag-relevance-map)
- [Why the number misleads](#why-the-number-misleads)

## The threshold-inversion technique

```bash
ruff check --isolated --select C901 \
  --config "lint.mccabe.max-complexity=0" \
  --no-cache --output-format concise path/to/package/
```

```text
pkg/handlers.py:1:5: C901 `dispatch` is too complex (9 > 0)
pkg/handlers.py:20:5: C901 `validate` is too complex (3 > 0)
pkg/handlers.py:28:5: C901 `render` is too complex (1 > 0)
pkg/util.py:1:5: C901 `normalize` is too complex (1 > 0)
pkg/util.py:5:5: C901 `pick` is too complex (3 > 0)
Found 5 errors.
```

**The threshold must be `0`, not `1`.** The rule fires on `complexity > max-complexity`, not `>=`.
With `max-complexity=1`, every function whose complexity is exactly 1 — the majority of any real
codebase — is silently omitted:

```bash
$ ruff check --select C901 --config "lint.mccabe.max-complexity=1" --no-cache fixtures/base.py
All checks passed!          # both functions score 1; neither is reported. exit 0
```

`0` is the floor. Negative values are rejected at argument-parse time:

```text
$ ruff check --config "lint.mccabe.max-complexity=-1" ...
invalid value: integer `-1`, expected usize
in `lint.mccabe.max-complexity`          # exit 2
```

Other requirements:

- `--select C901` is **mandatory**. C901 is not in ruff's default rule set, so without `--select`
  you get **no complexity rows at all**. Note the command does not necessarily go quiet: ruff's
  default rules still run, so the output and exit code reflect those instead (a fixture of one-line
  `if` bodies returns 3×`E701`, exit 1) — an exit 1 without `--select` says nothing about
  complexity. `--select C90` and `--select C` also work (prefix selection).
- The config key is `lint.mccabe.max-complexity` (default `10`). The pre-`lint`-section spelling
  `mccabe.max-complexity` still works in 0.12.7–0.16.5 but prints
  `warning: The top-level linter settings are deprecated…`. The key has **not** moved between these
  versions.
- The default of `10` is convention, not calibration. It traces to McCabe's 1976 paper *A Complexity
  Measure*, which calls 10 "a reasonable, but not magical, upper limit" — the paper itself allows
  relaxing to 15. Nothing about the number is empirically derived, so do not present a score of 11
  as a threshold breach in a codebase that never adopted the gate.
- `--config` takes inline TOML, so quote the whole `key=value` pair as one shell word.

## Exit codes

| Situation | Exit | Notes |
|---|---|---|
| Findings present | `1` | The normal case at threshold 0 |
| No findings | `0` | |
| Invalid `--config` value or unknown key | `2` | Loud, on stderr |
| `required-version` mismatch in a project config | `2` | `ruff failed / Cause: Required version …` |
| Syntax error in a scanned file | `1` | `SyntaxError` diagnostics; **no C901 rows for that file** |
| **Path does not exist** | **`0`** | `warning: Failed to lint …: No such file or directory`, then `All checks passed!` |
| Directory contains no Python files | `0` | `warning: No Python files found under the given path(s)` |
| `--exit-zero` passed | `0` | Regardless of findings — useful under `set -e` |

A mistyped path is the dangerous one: it looks exactly like "this package has no complex functions".
Confirm the path resolves to something before trusting an empty result:

```bash
$ ruff check --isolated --show-files path/to/pkg/     # prints one absolute path per file
$ ruff check --isolated --show-files path/to/typo.py  # prints nothing, exit 0
```

Verified in both directions: `--show-files` emits the resolved path for a real target and emits
nothing at all for a missing one.

## Output formats

Both versions accept the same twelve values for `--output-format`: `concise`, `full`, `json`,
`json-lines`, `junit`, `grouped`, `github`, `gitlab`, `pylint`, `rdjson`, `azure`, `sarif`
(env var `RUFF_OUTPUT_FORMAT`).

The **default is `full`**, which interleaves a source snippet and a caret ruler after every
diagnostic — roughly six lines per function, useless for scanning:

```text
fixtures/base.py:1:5: C901 `c1_trivial` is too complex (1 > 0)
  |
1 | def c1_trivial():
  |     ^^^^^^^^^^ C901
2 |     return 1
  |
```

Practical choices for this workflow:

| Format | Line shape | Use |
|---|---|---|
| `concise` | ``path:row:col: C901 `fn` is too complex (N > 0)`` | Best for eyeballing and `sed`; path is **as given** (relative) |
| `json` | array of objects | Best for scripting; `code` is preview-proof (see below) |
| `json-lines` | one object per line | Same fields, streamable |
| `grouped` | per-file header, then ``row:col C901 `fn` …`` | Readable per module |
| `pylint` | ``path:row: [C901] `fn` …`` | Drops the column |
| `full` (default) | 6-line block | Avoid |
| `--statistics` | `24	C901	complex-structure` | **Only a count.** No per-function data — not an option here |

JSON object (0.12.7):

```json
{
  "cell": null,
  "code": "C901",
  "end_location": { "column": 15, "row": 1 },
  "filename": "/abs/path/fixtures/base.py",
  "fix": null,
  "location": { "column": 5, "row": 1 },
  "message": "`c1_trivial` is too complex (1 > 0)",
  "noqa_row": 1,
  "url": "https://docs.astral.sh/ruff/rules/complex-structure"
}
```

Notes:

- **The complexity number has no dedicated field.** It only exists inside `message`, so a regex is
  required either way. `message` is stable across 0.12.7–0.16.5.
- `filename` is **absolute** in JSON, but **as-given** (usually relative) in `concise`.
- 0.16.x adds two fields: `name` (`"complex-structure"`) and `severity` (`"error"`). **`name` is the
  rule name, not the function name** — reading `.name` expecting `dispatch` yields
  `complex-structure` on 0.16.x and `null` on 0.12.7.

### Do not join this table to another tool's by function name

The obvious next move — join ruff's rows against a second complexity tool to cross-check — does not
work, and `complexipy` (7.0.1) is the concrete case. Same file, same run:

| function | ruff `C901` | complexipy |
|---|---|---|
| `long_but_flat` | 1 | 0 |
| `gnarly_one_liner` | **1** | **8** |
| `flat_dispatch` | **5** | 4 |
| `deep_nest` | **5** | **10** |
| `only_nested_defs` | 7 | 6 |
| `h1`, `h2`, `h3` (nested in the above) | 2 each | *no row* |

Three independent reasons the join fails:

1. **Different row sets.** complexipy emits **top-level functions only** and folds nested cost into
   the parent; ruff emits a row per nested `def` *as well as* folding. Eight ruff rows against five
   complexipy rows here — 14 against 4 on the closure-pyramid fixture. Nested names simply do not
   exist on one side.
2. **Different metric.** complexipy computes **cognitive** complexity, not cyclomatic — its own
   package summary says so. The two disagree by 8× on `gnarly_one_liner`, where ruff ignores
   `and`/`or`/ternaries and cognitive complexity charges for each.
3. **Different ranking.** Ruff's most complex function here (`only_nested_defs`, 7) is complexipy's
   third; complexipy's worst (`deep_nest`, 10) is one of ruff's joint-second. Cross-checking one
   ranking against the other produces disagreement everywhere, not confirmation.

Use a second tool as a *separate* opinion on the same code, not as a column beside this one.

### Preview mode changes the text format (0.16.x only)

Under `--preview` (or `preview = true` in a project config), ruff 0.16.x drops the code from
text formats:

```text
fixtures/base.py:1:5: complex-structure: `c1_trivial` is too complex (1 > 0)
```

That breaks any parser keyed on the literal `C901 `. Three facts, each verified:

- **ruff 0.12.7 does not do this** — it prints `C901` even with `--preview`.
- **`--output-format json` is immune**: `.code` is `"C901"` under preview on 0.16.5.
- `--config "output-prefer-rule-codes=true"` restores `C901 ` in text formats under preview.

`--isolated` also avoids it when the change comes from a project config rather than an explicit
`--preview` flag.

## Ranked scans

Point the command at a directory; ruff walks it. `concise` + `sed` + `sort` is enough:

```bash
ruff check --isolated --select C901 --config "lint.mccabe.max-complexity=0" \
    --no-cache --output-format concise path/to/pkg/ \
  | sed -nE 's/^(.*):([0-9]+):[0-9]+: C901 `(.*)` is too complex \(([0-9]+) > [0-9]+\)$/\4\t\3\t\1:\2/p' \
  | sort -rn
```

```text
9	dispatch	pkg/handlers.py:1
3	validate	pkg/handlers.py:20
3	pick	pkg/util.py:5
1	render	pkg/handlers.py:28
1	normalize	pkg/util.py:1
```

The JSON variant survives preview mode and paths containing colons:

```bash
ruff check --isolated --select C901 --config "lint.mccabe.max-complexity=0" \
    --no-cache --output-format json path/to/pkg/ \
  | jq -r '.[] | select(.code=="C901")
      | (.message|capture("`(?<fn>.+)` is too complex \\((?<n>[0-9]+) >")) as $m
      | [($m.n|tonumber), $m.fn, "\(.filename):\(.location.row)"] | @tsv' \
  | sort -rn
```

**Guard against unparseable files.** A file with a syntax error produces `SyntaxError` diagnostics
(`"code": null`) and **zero** C901 rows, so `select(.code=="C901")` silently drops the whole file
while the run still exits 1. Count what you filtered out:

```bash
ruff check --isolated --select C901 --config "lint.mccabe.max-complexity=0" \
    --no-cache --output-format json path/to/pkg/ \
  | jq '[.[] | select(.code != "C901")] | length'
```

Verified: `0` on a clean package, `2` once a file with a syntax error is added to it — while the
ranked table above is identical in both runs.

Timings on 4,675 files (`sentry/src/sentry`): 0.19–0.25 s with `--no-cache`, 0.12 s warm. Rerunning
is free; there is no reason to scan incrementally.

## Config interference and `--isolated`

Without `--isolated`, ruff resolves the nearest `pyproject.toml` / `ruff.toml` and that project's
settings can change or erase the answer. Tested against a project config, one vector at a time:

| Project config | Effect on this workflow |
|---|---|
| `lint.select = ["E", "F"]` | **None.** CLI `--select C901` wins |
| `lint.mccabe.max-complexity = 10` | **None.** CLI `--config` wins |
| `lint.ignore = ["C901"]` | **None.** CLI `--select` re-enables it |
| `lint.extend-ignore = ["C"]` | **None** |
| `exclude = ["pkg"]` (path passed explicitly) | **None** — explicit paths bypass excludes |
| `exclude = ["pkg"]` + `force-exclude = true` | **Silent.** `No Python files found`, exit 0 |
| `lint.per-file-ignores = {"pkg/mod.py" = ["C901"]}` | **Silent.** `All checks passed!`, exit 0 |
| `lint.extend-per-file-ignores` | **Silent.** Same |
| `preview = true` | Output shape changes on 0.16.x (above) |
| `required-version = "==0.1.0"` | Loud, exit 2 |

The two silent ones are the reason to use `--isolated`. Demonstrated:

```bash
# with pyproject.toml: lint.per-file-ignores = {"pkg/mod.py" = ["C901"]}
$ ruff check --select C901 --config "lint.mccabe.max-complexity=0" --no-cache pkg/mod.py
All checks passed!                                                    # exit 0 — wrong

$ ruff check --isolated --select C901 --config "lint.mccabe.max-complexity=0" --no-cache pkg/mod.py
pkg/mod.py:1:5: C901 `complex_fn` is too complex (6 > 0)              # exit 1 — correct
```

### What `--isolated` costs

`--isolated` discards **all** config files, so the project's `exclude` / `extend-exclude` list goes
with them. Generated code, migrations, and vendored trees the project deliberately skips reappear in
the ranking:

```bash
# pyproject.toml: extend-exclude = ["*/migrations/*"]
$ ruff check          --select C901 … pkg/   # → pkg/real.py only
$ ruff check --isolated --select C901 … pkg/ # → pkg/real.py AND pkg/migrations/0001.py
$ ruff check --isolated --extend-exclude '*/migrations/*' --select C901 … pkg/   # → pkg/real.py
```

Two things `--isolated` does **not** cost:

- `.gitignore` is still honored (`respect-gitignore` defaults to true and is not config-supplied) —
  a gitignored `pkg/generated/pb2.py` stayed absent from both runs.
- **Parsing is unaffected.** Ruff parses with the newest supported grammar regardless of
  `target-version`, so `--isolated` does not turn PEP 695 `type X = int` or `match` into syntax
  errors even though `requires-python` inference is lost. Verified on 0.12.7 and 0.16.5.

## Suppression that `--isolated` does not fix

`# noqa` lives in the source, so config isolation cannot reach it. All three of these silence C901:

```python
def suppressed(a, b):  # noqa: C901
def blanket(a):        # noqa
# ruff: noqa: C901     ← file-level, silences the entire file
```

In a codebase that already has a C901 gate these are exactly the functions you most want to see.
`--ignore-noqa` restores them:

```bash
$ ruff check --isolated --select C901 --config "lint.mccabe.max-complexity=0" --no-cache f.py
fixtures/noqa.py:13:5: C901 `visible` is too complex (2 > 0)          # 1 of 3 functions

$ ruff check --isolated --ignore-noqa --select C901 … f.py
fixtures/noqa.py:1:5:  C901 `suppressed` is too complex (3 > 0)
fixtures/noqa.py:8:5:  C901 `blanket` is too complex (2 > 0)
fixtures/noqa.py:13:5: C901 `visible` is too complex (2 > 0)          # all 3
```

The file-level `# ruff: noqa: C901` case is the worst: it takes the file to `All checks passed!`,
exit 0, with no warning. `--ignore-noqa` recovers it.

## What ruff's McCabe actually counts

Measured, not recited: one fixture per construct, complexity read off at `max-complexity=0`. A
function body of `pass` scores **1**; the delta below is the measured increment over that baseline.
**Identical on 0.12.7, 0.16.3, and 0.16.5** — 80 fixtures, byte-identical output.

| Construct | Δ | Notes |
|---|---|---|
| `if` | **+1** | |
| `elif` | **+1** each | `if/elif/elif` = 4 |
| `else` (on `if`) | **0** | `if/else` scores the same as a bare `if` |
| `for` / `async for` | **+1** | |
| `while` | **+1** | |
| `else` on `for`/`while` | **0** | |
| `break` / `continue` | **0** | |
| `except` handler | **+1** each | `try` + 3 handlers = 4 |
| `except*` handler | **+1** each | Same as `except` |
| `else` on `try` | **+1** | Asymmetric with `if/else` |
| `finally` | **0** | `try`/`finally` with no handler scores 1 |
| `match` case (refutable) | **+1** each | Literal, class, and `1 \| 2` or-patterns each count once |
| `case _:` (wildcard) | **0** | A `match` with only `case _` scores 1 |
| `case … if guard:` | **0** | The guard adds nothing |
| **`and` / `or`** | **0** | `a and b and c and d` scores **1** |
| **`not`** | **0** | |
| **Ternary `b if a else c`** | **0** | Nested ternaries also **0** |
| **Comprehension `if` clause** | **0** | Two `if`s: still 0 |
| Comprehension `for` clause | **0** | Including nested `for` and dict/set/genexp |
| `with` / `async with` | **0** | Multiple items and nesting also 0 |
| `assert` | **0** | |
| `raise` | **0** | |
| `return` | **0** | Extra returns cost nothing on their own |
| `await` | **0** | |
| Walrus `:=` | **0** | Beyond the enclosing `if` |
| `lambda` | **0** | Even a lambda containing a ternary |
| Decorator | **0** | One or many |
| **Nested `def`** | **+ the whole inner score** | See below |
| **Nested `class`** | **+ its methods' scores** | |

The four zero rows in bold are where ruff departs from the textbook McCabe definition, which counts
each boolean operator and each conditional expression as a decision point. Ruff's implementation
counts **statements**, not expressions. Consequences:

```python
def gnarly_one_liner(cfg):        # scores 1
    return (
        cfg.a if cfg.b and cfg.c or not cfg.d
        else (cfg.e if cfg.f and (cfg.g or cfg.h) else cfg.i)
    )
```

Refactoring a chain of `if` statements into one boolean expression or a comprehension therefore
drives the score toward 1 without changing how hard the code is to read. Rewriting a dense predicate
back out into statements *raises* it. The metric can be gamed in both directions.

## Scope and granularity

One diagnostic per `def` / `async def`, at the function name's column. Verified exactly: a fixture
with 56 `def`s produced 56 JSON entries.

- **Methods are scored individually**, including `@property`, `@staticmethod`, and `async def`.
- **Classes are never scored.** A 3,000-line class with 40 methods contributes 40 low rows and no
  aggregate. There is no per-class or per-file number — `--statistics` only counts diagnostics.
- **Lambdas produce no row** and add nothing to their enclosing function.
- **Module-level code is invisible.** A module with a top-level `if/elif/else`, a `for` loop, and a
  `try/except` yielded exactly one row, for its single trivial `def`. Scripts that do their work at
  module scope measure as complexity-free.
- **Nested functions are double-counted.** A nested `def` is reported on its own row *and* its
  **entire score** — not merely the `def` statement — is folded into every enclosing function,
  recursively. The measured law is:

  ```text
  score(f) = 1 + decision_points(f.body) + Σ score(g) for each g nested directly in f
  ```

  Isolating the two candidate readings settles it: a function whose only content is one helper
  containing one `if` scores **3**, not 2. Full-score folding predicts `1 + 2`; `def`-statement-only
  folding would predict `1 + 1`.

  ```text
  bare_if            2      # def bare_if(x): if x: pass
  hosts_one_helper   3      # body is just `return helper`; helper itself is 2
    helper           2

  only_nested_defs   7      # body is just `return h1, h2, h3`;  7 = 1 + 2 + 2 + 2
    h1               2
    h2               2
    h3               2
  ```

  A function that merely defines three small helpers outranks nearly everything in a typical module.
  Nested classes behave the same way (`1 + Σ` of their methods). When a ranked list puts an
  unfamiliar function at the top, check whether its body is mostly `def`.

  **Corollary: the rows do not sum.** Totalling a ranked list, or averaging it per file, counts every
  nested function once for itself and again inside each ancestor. Worse, **ruff's output cannot tell
  you which rows to drop.** The reported column is not a usable proxy for nesting: methods and nested
  defs collide at column 9, and `async def` shifts the name right by 6 (a top-level `async def`
  reports at column 11, a method at 15). The JSON payload carries no parent or scope field — only
  `cell`, `code`, `end_location`, `filename`, `fix`, `location`, `message`, `noqa_row`, `url`.
  Deduplicating requires parsing the source yourself (`ast`). Rank the rows; do not aggregate them.

## Caching and `--no-cache`

Ruff writes `.ruff_cache/` next to the resolved project root. Whether the cache can hand back a wrong
number **depends on the version**:

| Scenario | 0.12.7 | 0.16.3 / 0.16.5 |
|---|---|---|
| Edit that advances mtime | fresh | fresh |
| Different `max-complexity` on a later run | fresh | fresh |
| **Edit that preserves mtime** | **STALE** | fresh |

The 0.12.7 cache is keyed on **mtime**, not content. Rewriting a file completely — different size,
different function name, different score — while restoring the old mtime returns the previous run's
result verbatim, naming a function that no longer exists:

```bash
# 0.12.7, file rewritten from `def f` (3) to `def g` (1), mtime restored with touch -t
$ ruff check --select C901 --config "lint.mccabe.max-complexity=0" m.py
m.py:1:5: C901 `f` is too complex (3 > 0)          # stale
$ ruff check --select C901 --config "lint.mccabe.max-complexity=0" --no-cache m.py
m.py:1:5: C901 `g` is too complex (1 > 0)          # correct
```

Two follow-ons, both verified on 0.12.7:

- **`--no-cache` does not refresh the stored cache.** The next run without the flag is stale again.
  Pass it on every run, or `ruff clean` first.
- Ordinary editing advances mtime and is safe. The realistic triggers are `cp -p`, `rsync -t`,
  `tar -x`, and same-second scripted rewrites.

So `--no-cache` is not cargo cult at 0.12.7 and is redundant at 0.16.3+. It costs ~0.1 s on 4,675
files, so keeping it unconditionally is the cheap, version-agnostic choice.

## Version differences

Everything below was checked against 0.12.7 (PATH), 0.16.3, and 0.16.5 (latest at time of writing).
Use `UV_NO_CONFIG=1 uvx ruff@0.16.5 …` to pin a version without touching the project environment.

**Identical across all three:**

- The `>` (not `>=`) threshold semantics, and `0` as the floor.
- The config key `lint.mccabe.max-complexity`, its default of `10`, and the top-level
  `mccabe.max-complexity` deprecation warning.
- The measured complexity of all 80 construct fixtures — byte-identical output.
- The message text: `` `NAME` is too complex (N > T) ``.
- The twelve `--output-format` values.
- Exit codes, including exit 0 for a nonexistent path.
- Every config-interference and `# noqa` result above.

**Differences:**

| | 0.12.7 | 0.16.3 / 0.16.5 |
|---|---|---|
| `ruff check` long flags | 46 | 48 |
| `--color <auto\|always\|never>` on `check` | **absent** (`error: unexpected argument`) | present |
| `--add-ignore` | absent | present |
| Preview text output | still `C901` | `complex-structure:` |
| JSON fields | 9 | 11 (adds `name`, `severity`) |
| Cache invalidation | mtime-keyed → can go stale | content-aware |

`ruff check --help` is byte-identical between 0.16.3 and 0.16.5, as is their output on every fixture.

## Flag relevance map

`ruff check --help` at 0.16.5 is 173 lines / 6,297 bytes, ending at `--color`; at 0.12.7 it is 111
lines / 5,691 bytes, ending at `--isolated`. Extracting every `--[a-z][a-z0-9-]*` token gives **48**
distinct long flags (46 at 0.12.7) plus short forms `-e -h -n -o -q -s -v -w`.

**Used by this workflow (9):**

| Flag | Role |
|---|---|
| `--select` | Required — C901 is off by default |
| `--config` | Carries `lint.mccabe.max-complexity=0` |
| `--isolated` | Blocks `per-file-ignores` / `force-exclude` from silently zeroing the result |
| `--output-format` | `concise` or `json`; the `full` default is unscannable |
| `--no-cache` | Required at 0.12.7; harmless later |
| `--ignore-noqa` | Reveals functions with `# noqa: C901` |
| `--show-files` | Confirms a path resolves before trusting an empty result |
| `--extend-exclude` | Restores project excludes lost to `--isolated` |
| `--exit-zero` | Suppresses exit 1 under `set -e` |

**Verified as no-ops or actively wrong here (the remaining 39):**

- `--statistics` — aggregates to a single count (`24	C901	complex-structure`); loses every score.
- `--fix`, `--fix-only`, `--no-fix`, `--no-fix-only`, `--diff`, `--fixable`, `--unfixable`,
  `--extend-fixable`, `--unsafe-fixes`, `--no-unsafe-fixes`, `--exit-non-zero-on-fix`,
  `--show-fixes`, `--no-show-fixes` — **C901 has no autofix.** `--fix` leaves the file byte-identical
  and still exits 1.
- **`--add-noqa` — destructive.** Combined with `max-complexity=0` it writes `# noqa: C901` onto
  *every function in the tree* (`Added 3 noqa directives.`, exit 0) and permanently blinds future
  scans. Never combine it with the inverted threshold.
- `--ignore`, `--add-ignore` (0.16+), `--per-file-ignores`, `--extend-per-file-ignores` — can only
  remove rows. Both `--ignore C901` and `--per-file-ignores 'f.py:C901'` take the run to
  `All checks passed!`, exit 0. `--extend-select` is redundant once `--select C901` is passed.
- `--preview`, `--no-preview` — no effect on scores; `--preview` reshapes 0.16.x text output.
- `--target-version` — **no effect on any score**, but not inert: an explicit *old* value adds
  `SyntaxError` diagnostics for newer syntax while still scoring the function.
  `--target-version py37` over a file using `type X = int` and `match` emitted two SyntaxErrors
  alongside an unchanged score of 3 for the same function. That noise trips the non-C901 guard
  above, so leave the flag off.
- `--exclude`, `--force-exclude`, `--no-force-exclude`, `--respect-gitignore`,
  `--no-respect-gitignore`, `--extension` — file-discovery tuning, orthogonal to measurement.
- `--output-file`/`-o`, `--cache-dir`, `--verbose`, `--quiet`, `--silent`, `--color` (0.16+) —
  plumbing.
- `--stdin-filename` — works (`… - --stdin-filename virtual.py` scores piped source) but only reaches
  one file at a time.
- `--watch` — interactive; irrelevant to a one-shot measurement.
- `--show-settings` — debugging aid; prints `linter.mccabe.max_complexity = 0`, confirming the
  `--config` override landed. Useful once, when a threshold appears not to apply.
- `--help` — n/a.

## Why the number misleads

Four fixtures, all measured:

```text
long_but_flat      1     # 25 locals, dense arithmetic, one 7-line return tuple
gnarly_one_liner   1     # nested ternaries over and/or/not
flat_dispatch      5     # four `if kind == …: return N` guards, trivially readable
deep_nest          5     # four levels of nesting, genuinely hard to follow
only_nested_defs   7     # body is `return h1, h2, h3`; the 7 belongs to the helpers
```

`flat_dispatch` and `deep_nest` tie at 5. Cyclomatic complexity counts branches, so **nesting depth
is invisible** — the metric cannot distinguish a flat guard chain from a four-deep pyramid. It also
ignores length entirely (`long_but_flat` scores 1), ignores expression complexity
(`gnarly_one_liner` scores 1), and over-credits functions that merely host closures.

The closure case degenerates completely: **a pyramid of nested `def`s with no conditionals at all
scores its own depth.** An N-deep pyramid of empty functions gives the outermost a score of N,
measured at N = 2, 3, 4, and 5:

```python
def d1():
    def d2():
        def d3():
            def d4():
                def d5():
                    return 1
                return d5
            return d4
        return d3
    return d2
```

```text
d1 5    d2 4    d3 3    d4 2    d5 1
```

Zero decision points anywhere in that file, and `d1` still outranks a real four-way dispatcher. Any
decorator factory, closure-based builder, or `functools.wraps` wrapper picks up the same inflation.

Treat the ranking as a **triage queue, not a verdict**: it reliably finds functions with many
branching statements, which correlates with the number of tests needed to cover them. It says nothing
about nesting, length, coupling, naming, or how many concepts a reader must hold at once. Read the
top ~20 and decide for yourself; several will not deserve the position, and some genuinely awful
code will score 1.
