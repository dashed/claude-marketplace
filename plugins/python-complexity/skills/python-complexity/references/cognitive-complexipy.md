# Cognitive complexity with complexipy

Per-function **cognitive complexity** (the SonarSource-style metric) for Python, run install-free
via `uvx`. Every command, output block, score, and exit code below was executed against
**complexipy 7.0.1** on macOS; the scoring table is measured from fixtures, not transcribed from
upstream docs — which are wrong in four places ([see below](#where-upstreams-own-docs-are-wrong)).

> **Before trusting a score, read
> [Silent under-count in expression contexts](#silent-under-count-in-expression-contexts).** 7.0.1
> drops ternaries, boolean operators, and comprehensions entirely when they sit inside an
> arithmetic expression, an f-string, a subscript, a keyword argument, a dict key, or a `yield`.
> The score comes back lower, with no warning.

## Table of contents

- [Invocation and pinning](#invocation-and-pinning)
- [Output surface](#output-surface)
- [Machine-readable output](#machine-readable-output)
- [Parsing `--plain` safely](#parsing---plain-safely)
- [What gets reported](#what-gets-reported)
- [Threshold and exit codes](#threshold-and-exit-codes)
- [The scoring model, measured](#the-scoring-model-measured)
- [Nesting](#nesting)
- [Silent under-count in expression contexts](#silent-under-count-in-expression-contexts)
- [Where upstream's own docs are wrong](#where-upstreams-own-docs-are-wrong)
- [Paths, excludes, and `.gitignore`](#paths-excludes-and-gitignore)
- [Suppression comments](#suppression-comments)
- [Diff mode](#diff-mode)
- [Snapshot mode](#snapshot-mode)
- [Configuration file](#configuration-file)
- [Side-effect files](#side-effect-files)
- [Failure modes](#failure-modes)
- [Flag inventory](#flag-inventory)

## Invocation and pinning

```bash
uvx complexipy path/to/module.py     # floats to latest release
uvx complexipy@7.0.1 path/to/module.py   # pinned — verified working
```

Nothing is installed into the project venv; `uvx` resolves complexipy into its own ephemeral
environment. Pin for anything reproducible: the CLI surface changes across majors — `uvx
complexipy@3.0.0 --version` fails with `No such option: --version`, so even the version probe is
not stable across majors.

`uvx complexipy --version` → `7.0.1`.

> In an environment with a machine-wide `/etc/uv/uv.toml` (a default mirror index), prefix every
> invocation with `UV_NO_CONFIG=1` so uv does not rewrite lockfiles. All output below was captured
> with that prefix; it changes nothing about complexipy's behavior.

## Output surface

The default output is **not** `name score`. It is a rich, box-drawn report with a header rule, a
per-file path line, indented rows carrying a `✅ PASSED` / `❌ FAILED` marker, a conditional summary
line, and a footer rule:

```
──────────────────────────────────── 🐙 complexipy ─────────────────────────────────────
fx/canon.py
    flat_ladder 3  ✅ PASSED 
    nested_ladder 6  ✅ PASSED 

All functions are within the allowed complexity.
────────────────────────────── 🎉 Analysis completed! 🎉 ───────────────────────────────
```

Properties worth knowing:

- The rules are U+2500 box-drawing characters and the width **tracks `COLUMNS`**. Long messages
  hard-wrap mid-token at terminal width.
- `All functions are within the allowed complexity.` prints **only when everything passes** — its
  absence is the failure signal in the rich form.
- Colour auto-detects: piping yields **zero ANSI escapes**. `--color yes` forces 7 escape sequences
  even through a pipe; `--color no` forces none. `--plain` never emits colour, even with
  `--color yes`.
- Rows are sorted **ascending by complexity** by default (`--sort asc`). Other values: `desc`,
  `file_name`.

Use `--plain` for anything programmatic — one space-separated row per function, no decoration:

```console
$ uvx complexipy --plain fx/over.py
fx/over.py trivial 0
fx/over.py messy 17
```

`--plain` and `--quiet` are mutually exclusive (exit 2:
`Invalid value: --plain and --quiet cannot be used together.`). `-q` alone silences stdout while
preserving the exit code.

## Machine-readable output

`--output-format` accepts `csv`, `json`, `gitlab`, `sarif` (comma-separated or repeated), and
`--output` names the destination.

```bash
uvx complexipy --output-format json --output out/c.json src/
```

```json
[
  {
    "complexity": 17,
    "file_name": "over.py",
    "function_name": "messy",
    "path": "fx/over.py",
    "refactor_plans": []
  }
]
```

- `refactor_plans` is populated **only when `--suggest-refactors` is also passed**; otherwise it is
  always `[]`. Populated entries carry `rule_id` (e.g. `C001`), `title`, `line_start`,
  `estimated_reduction`.
- CSV header: `Path,File Name,Function Name,Cognitive Complexity`.
- `gitlab` emits **only violations** (Code Quality report format, with `fingerprint` and
  `severity`), so it is `[]` on a clean run — it is not a full inventory.
- `sarif` emits a SARIF 2.1.0 document with rule id `CC001`.
- **Multiple formats require `--output` to end in a path separator.** A bare existing directory is
  rejected with exit 2 (`--output must point to a directory or end with a path separator`); use
  `--output out/dir/`. Files land as `complexipy-results.{csv,json,gitlab.json,sarif}`.
- Omitting `--output` entirely writes `complexipy-results.<ext>` **into the CWD** — it does not go
  to stdout.

Sorted function→score table:

```bash
tmp=$(mktemp -d)
uvx complexipy -i --output-format json --output "$tmp/c.json" src/ >/dev/null
jq -r 'sort_by(-.complexity)[] | "\(.complexity)\t\(.path)::\(.function_name)"' "$tmp/c.json"
```

```
6	demo/canon.py::nested_ladder
6	demo/sp ace.py::nested_ladder
3	demo/canon.py::flat_ladder
3	demo/sp ace.py::flat_ladder
```

**Do not use `--output /dev/stdout`.** A `Results saved at /dev/stdout` status line is appended
*after* the JSON and `-q` does not suppress it, so the stream never parses. Write a real file.

## Parsing `--plain` safely

Two hazards make naive `awk '{print $2, $3}'` wrong:

1. **Errors and advisories go to stdout, not stderr**, and are rich-wrapped across several lines
   even under `--plain`. stderr is empty.
2. The row format is `<path> <function> <complexity>` **space-separated**, so a path containing a
   space produces more than three fields.

Both, together:

```console
$ uvx complexipy --plain -i fxmix
fxmix/sp ace.py two_args 0
fxmix/sp ace.py zero_complexity 0
fxmix/sp ace.py one_branch 1
fxmix/trivial.py two_args 0
fxmix/trivial.py zero_complexity 0
fxmix/trivial.py one_branch 1
error: Failed to process 
/private/tmp/claude-501/-Users-me-aaa-github-claude-marketplace/ad578631-1d20-4e
68-b308-a2bdea7a14d2/scratchpad/cc/fxmix/broken.py - Please check file/folder 
exists or check syntax
```

`awk '{print $2" "$3}'` yields four junk rows (`Failed to`, ` `, `- Please`, `or check`). Anchoring
on `NF==3` drops the real spaced-path rows instead. Anchor on the **last two fields** and require a
numeric score:

```bash
uvx complexipy --plain -i src/ | awk 'NF>=3 && $NF ~ /^[0-9]+$/ {print $NF"\t"$(NF-1)}' | sort -rn
```

Verified: on the mixed tree above this keeps all six real rows and drops all four error lines; on a
clean tree it still emits every row (i.e. it is not silently filtering everything out). It also
survives the `# complexipy: ignore` advisory block, which is likewise printed to stdout under
`--plain`.

This filter is a heuristic — a wrapped error line whose final token happened to be a bare integer
would slip through. For anything load-bearing, use the JSON path above, which is immune to both
hazards.

## What gets reported

Every function is listed, **including complexity 0** — the listing is a full inventory, not a
violation list:

```console
$ uvx complexipy --plain fx/trivial.py
fx/trivial.py two_args 0
fx/trivial.py zero_complexity 0
fx/trivial.py one_branch 1
```

| Construct | Reported as |
|---|---|
| Module-level function | `func_name` |
| Method | `Klass::method_name` |
| Nested `def` / `lambda` | **Not separate** — folded into the enclosing top-level function |
| Method of **any class not at column 0** | **Not reported at all** |
| Module-level (script) code | Only with `--check-script`, as `<module>` |

Because nested functions are folded away and methods are qualified, **complexipy's listing cannot
be joined by function name to another tool's.** Against ruff's `C901` on one fixture:

| | complexipy | ruff `C901` |
|---|---|---|
| `def outer` containing `def inner` | one row, `outer 3` | **two rows**, `outer` and `inner` |
| `Klass.method_if` | `Klass::method_if` | `method_if` |

So a name join silently drops ruff's nested-function rows and fails to match every method.

The same property that breaks the join makes complexipy's rows **sum** where ruff's do not: each
top-level def appears exactly once with its nested cost folded in, so Σ over a file or a call path
is well-defined — and it is the aggregate Campbell's paper endorses (v1.7 p. 10: "because Cognitive
Complexity does not increment for the method structure, aggregate numbers become useful"). Two
things to know before summing: **no output format prints a total** — not `--plain`, not the rich
report, and the JSON rows carry only `complexity, file_name, function_name, path, refactor_plans`
(verified 7.0.1); compute it (`jq 'map(.complexity) | add'`, or
`scripts/path_census.py`). And **`@overload` stubs are separate rows** scoring 0, so a row count
over-states the def count (25 rows for 23 defs on one measured module) while Σ is unaffected.

**radon shares the nested-class blind spot.** Identical bodies, one at top level and one under a
nested class: ruff 6 / lizard CCN 6 / complexipy absent / `radon cc` absent (6.0.1, which does not
list the inner class either). Only ruff and lizard are safe cross-checks for this trap.

**And there is no key to join on instead.** No census output carries a line number: `--plain` is
`<path> <fn> <score>`, the JSON keys are `complexity, file_name, function_name, path,
refactor_plans`, and the CSV header is `Path,File Name,Function Name,Cognitive Complexity`. Only
`sarif` (`region.startLine`) and `gitlab` (`location.lines.begin`) carry one, and both emit
**violations only** — a clean run yields `[]` — so they cannot supply a census join. Compare the
two listings qualitatively; do not build a join.

Two blind spots deserve emphasis, because both are silent.

**Classes below the top level are invisible.** The rule is not "nested class" — it is any `class`
statement not at column 0. That covers a class in a class, a class defined inside a function, and
— the case that actually occurs in typed code — a class under `if TYPE_CHECKING:` or `try:`.
Measured: `guarded.py` with two such classes, whose methods ruff reports as `gm` and `tm`, prints
nothing at all. Their methods are neither reported nor folded into a parent:

```console
$ cat fx/hidden.py
class Wrapper:
    class Hidden:
        def monster(self, a, b, c, d, e):
            for x in a:
                if b:
                    for y in c:
                        if d:
                            for z in e:
                                if z:
                                    return z
            return None

$ uvx complexipy --plain fx/hidden.py    # no output
$ echo $?
0
```

De-nested to a top-level class, the identical body scores **21** and exits 1. A complexity-21
function inside a nested class passes CI clean.

**Module-level code is invisible by default.** `--check-script` (`-cs`) adds a `<module>` row:

```console
$ uvx complexipy --plain -i fx/script.py
fx/script.py real_fn 0
$ uvx complexipy --plain -i --check-script fx/script.py
fx/script.py real_fn 0
fx/script.py <module> 6
```

## Threshold and exit codes

Default `--max-complexity-allowed` is **15**; a function fails when its score is **strictly
greater** than the threshold. Measured on a ladder of exactly-N-complexity functions:

```console
$ uvx complexipy fx/ladder.py
    ladder_13 13  ✅ PASSED 
    ladder_14 14  ✅ PASSED 
    ladder_15 15  ✅ PASSED 
    ladder_16 16  ❌ FAILED 
    ladder_17 17  ❌ FAILED 
```

The `gitlab` report states it independently: `max allowed: 15`.

**15 is complexipy's own default, not a research finding.** Campbell's cognitive-complexity white
paper specifies the metric, not a limit — it recommends no numeric threshold. Cite the
specification for the scoring model; treat 15 as this tool's chosen default and set it to whatever
your codebase warrants.

| Exit | Meaning |
|------|---------|
| `0` | Every function within threshold, **or** `-i`, **or** `--diff-only` with no other failure |
| `1` | At least one function over threshold, **or** any path/syntax error, **or** a `--diff` regression, **or** a new violation vs a snapshot |
| `2` | CLI usage error (unknown flag, `--plain` with `--quiet`, multi-format `--output` not a directory) |

**Exit 1 is ambiguous**: it conflates "too complex" with "file not found / failed to parse". A tree
whose functions all pass but which contains one unparseable file still exits 1. In CI, if you need
to distinguish them, run the parse check separately — `-i` suppresses the threshold check but
**not** parse errors:

```bash
uvx complexipy -i src/ || echo "a file failed to parse"
```

Verified to discriminate: exit 0 on a clean tree, exit 1 on the same tree plus one syntactically
broken file.

Which flag changes what:

| Flag | Rows printed | `✅/❌` markers | Exit code |
|------|--------------|----------------|-----------|
| *(default)* | all | shown | 1 if any over |
| `-mx N` | all | recomputed vs `N` | 1 if any over `N` |
| `-i` / `--ignore-complexity` | all (unchanged) | **still shown, still `❌`** | forced 0 |
| `-f` / `--failed` | **only failing rows** | shown | 1 if any over |

`-i` is the one most often misread: its help text says "show all functions", but the default
*already* shows all functions. What `-i` actually does is **suppress the failing exit code** —
rows and `❌ FAILED` markers are untouched. `-mx 0` is a real threshold of zero (everything fails),
not a disable switch; `-i` is the disable switch.

`-i` does **not** disable `--diff` enforcement — see [Diff mode](#diff-mode).

## The scoring model, measured

Each row was measured from an isolated fixture at nesting depth 0 unless noted.

| Construct | Cost | Note |
|---|---|---|
| Straight-line code, assignment, `return` | **0** | |
| `if` | **+1** | takes the nesting surcharge |
| `elif` | **+1** | flat — no nesting surcharge |
| `else` (of `if`) | **+1** | flat — no nesting surcharge |
| `for`, `while`, `async for` | **+1** | takes the nesting surcharge |
| `else` of a `for`/`while` | **0** | Python-specific; free |
| `except` handler | **+1 each** | two handlers = 2 |
| `try` block | **0** | and does not raise nesting |
| `else` of `try` | **0** | |
| `finally` | **0** | and does not raise nesting |
| Boolean sequence (`a and b and c and d`) | **+1 total** | length-independent |
| Each operator switch in a chain | **+1** | `a and b or c` = 2; `a and b or c and d` = 3 |
| `not` | **0** | |
| Ternary `x if c else y` | **+1** | takes the nesting surcharge |
| Comprehension / genexp, per `for` clause | **+1** | takes the nesting surcharge |
| Comprehension `if` filter | **+1** | flat — no nesting surcharge |
| `match` statement | **+1 total** | independent of the number of `case`s, guards included |
| Direct recursion | **+1 once per function** | two recursive call sites still +1 |
| Mutual recursion (`a`→`b`→`a`) | **0** | not detected |
| `break`, `continue` | **0** | |
| `with`, `async with` | **0** | and does not raise nesting |
| Nested `def` | **0** | and does **not** raise nesting for its body |
| `lambda` | **0** itself | but **does** raise nesting for its body |
| Decorator | **0** | |
| `async def` | same as `def` | |

The `lambda` / nested-`def` split is a genuine internal inconsistency — the same ternary scores
differently depending on which one wraps it:

```python
def p01_bare_ternary(a):        # -> 1
    return 1 if a else 0

def p02_in_lambda():            # -> 2   lambda body raises nesting
    return lambda a: 1 if a else 0

def p03_in_nested_def():        # -> 1   nested def does not
    def inner(a):
        return 1 if a else 0
    return inner
```

```console
$ uvx complexipy --plain -i fx/score4.py | grep -E ' p0[123]_'
fx/score4.py p01_bare_ternary 1
fx/score4.py p03_in_nested_def 1
fx/score4.py p02_in_lambda 2
```

## Nesting

An increment-carrying construct at nesting depth *d* costs **1 + d**. Measured:

| Fixture | Shape | Score |
|---|---|---|
| `s02_if_x1` | 1 `if` | 1 |
| `s06_nest1` | 2 nested `if` | 3 = 1+2 |
| `s07_nest2` | 3 nested `if` | 6 = 1+2+3 |
| `s08_nest3` | 4 nested `if` | 10 = 1+2+3+4 |

**Raises nesting depth:** `if` / `elif` / `else` bodies, `for` and `while` bodies, `except` bodies,
comprehension `for` clauses, `lambda` bodies, ternaries.

**Does not raise nesting depth:** `try`, `finally`, `with`, nested `def`, module level.

The canonical demonstration — the same three conditions, flat versus nested:

```console
$ cat fx/canon.py
def flat_ladder(v):
    if v == 1: return 1
    if v == 2: return 2
    if v == 3: return 3
    return 0

def nested_ladder(v):
    if v:
        if v > 1:
            if v > 2:
                return 3
    return 0

$ uvx complexipy --plain -i fx/canon.py
fx/canon.py flat_ladder 3
fx/canon.py nested_ladder 6
```

A flat early-return ladder is **not free** — it costs +1 per `if`, linearly (a 15-branch ladder
scores exactly 15 and passes; 16 fails). What it avoids is the *nesting surcharge*: the same
branches nested cost double here, and the gap widens with depth.

## Silent under-count in expression contexts

**Reproducible defect in complexipy 7.0.1** — the latest release at the time of writing (PyPI shows
no newer version), with no matching report on the upstream issue tracker.

Complexity-carrying expressions score **0** when they appear under certain parent nodes. Nothing is
printed; the function simply comes back cheaper than it is.

Minimal control — the same `if` in all four functions, so any difference is the trailing expression:

```python
def c0_if_only(a):                        # -> 1   (baseline)
    if a:
        return 1
    return 0

def c1_if_plus_bare_ternary(a, b):        # -> 2   ternary counted
    if a:
        return 1
    return 2 if b else 3

def c2_if_plus_binop_ternary(a, b, c):    # -> 1   BOTH ternaries dropped
    if a:
        return 1
    return (2 if b else 3) + (4 if c else 5)

def c3_if_plus_fstring_ternary(a, b):     # -> 1   ternary dropped
    if a:
        return 1
    return f"{2 if b else 3}"
```

```console
$ uvx complexipy --plain -i fx/tern.py
fx/tern.py c0_if_only 1
fx/tern.py c2_if_plus_binop_ternary 1
fx/tern.py c3_if_plus_fstring_ternary 1
fx/tern.py c1_if_plus_bare_ternary 2
```

The baseline `if` is still counted, so the function is not being skipped — the expression alone is.

**It is not ternary-specific.** The same holds for boolean operators and comprehensions, which
normally cost +1 each. Measured with the identical `if`-baseline harness (score 1 = payload
dropped):

| Payload placed in context ↓ | `return P` | `P + 1` | `f"{P}"` | `[…][P]` | `f(sep=P)` | `{P: 1}` | `yield P` |
|---|---|---|---|---|---|---|---|
| ternary `(2 if b else 3)` | 2 | **1** | **1** | **1** | **1** | **1** | **1** |
| boolean op `(b and c)` | 2 | **1** | **1** | **1** | **1** | **1** | **1** |
| comprehension `[z for z in (1,2)]` | 2 | **1** | **1** | **1** | **1** | **1** | **1** |
| comprehension + filter | 3 | **1** | **1** | **1** | **1** | **1** | **1** |

**The rule is per-parent-node-type, not "expressions are ignored".** Probing 39 syntactic contexts
with a ternary payload:

| Complexity is **counted** under | Complexity is **dropped** under |
|---|---|
| `return`, parenthesized `return` | Binary operators — `+`, `*`, `%`, string concat |
| `=`, `:=`-style annotated assign, `+=` | Unary operators (`-x`) |
| Comparisons (`x == 1`) | f-strings / `JoinedStr` (with or without surrounding text) |
| Boolean operands (`x and b`) | Subscript index **and** subscripted value |
| List, tuple, and set literals | Slice bounds |
| Dict **values** | Dict **keys** |
| **Positional** call arguments, incl. `.format(…)` | **Keyword** call arguments |
| Comprehension element and iterable | `*`-unpacked arguments |
| `assert`, `raise`, `with` items | Attribute access on the result |
| Nested ternaries, `lambda` bodies | `yield` values |

Note the asymmetries — dict *value* counted but dict *key* dropped; *positional* argument counted
but *keyword* argument dropped. That is the signature of an incomplete set of recursion arms in the
visitor, so treat this table as the tested cases rather than an exhaustive specification, and
assume other unlisted node types may also swallow complexity.

Practical consequences:

- A score is a **lower bound**, not a measurement. Dense one-liners — the exact code cognitive
  complexity exists to flag — are the most affected, because they are where ternaries and
  comprehensions get buried inside f-strings and arithmetic.
- Refactoring `x = a if b else c` into `return f"{a if b else c}"` *reduces* the reported score
  while making the code harder to read. Do not let the number drive that direction.
- A function can be pushed under the threshold by inlining, with no other change. When a score
  looks implausibly low for how a function reads, trust the reading.
- Cross-check anything load-bearing against a second metric. Cyclomatic complexity counts the
  branch in `(2 if b else 3) + (4 if c else 5)`.

## Where upstream's own docs are wrong

<https://rohaquinlop.github.io/complexipy/understanding-scores/> disagrees with the binary in four
places. Each was re-verified against an isolated fixture:

| Rule | Docs claim | Measured | Fixture evidence |
|---|---|---|---|
| `else` clause | `+0` (nesting only) | **+1** | `if`-only = 1, `if/else` = 2 |
| Boolean operators | `+1` each `and`/`or` | **+1 per operator-sequence** | `a and b` = 1, `a and b and c and d` = 1 |
| `match` statement | `+0`, only inner flow counts | **+1** | `match` with a single `case _: pass` = 1 |
| Recursion | "contributes no extra complexity" | **+1** | bare self-call = 1; identical non-recursive call = 0 |

The boolean and `match` behaviours actually match the SonarSource specification (which is
sequence-based, and charges 1 for a `switch`); the docs describe neither the spec nor the code.

Known divergences from the SonarSource spec itself: **mutual recursion is not detected** (the spec
counts recursion cycles), and **nested function declarations do not increment nesting** (the spec
says they do) — though lambdas inconsistently do. Upstream states it is "an independent project
inspired by G. Ann Campbell's research… not affiliated with or endorsed by SonarSource".

## Paths, excludes, and `.gitignore`

`paths` is variadic and accepts files, directories, or a git repository URL. With no path argument
complexipy analyses the CWD.

`.gitignore` is honoured **only inside a real git repository**. Verified on one tree, three ways:

| Setup | `skipme/b.py` analysed? |
|---|---|
| No `.gitignore` | yes |
| `.gitignore` present, directory **not** a git repo | **yes — ignored** |
| `.gitignore` present, after `git init` | no |

So a `.gitignore` in a plain directory buys nothing. Use `--exclude` (`-e`) when you cannot rely on
a repo; it accepts globs *and* bare substrings, comma-separated or repeated:

```bash
uvx complexipy --exclude 'tests/**' --exclude migrations src/
uvx complexipy -e 'tests/**,build/**' src/
```

Quote globs so the shell does not expand them first.

## Suppression comments

`# complexipy: ignore` and `# noqa: complexipy` on the `def` line remove a function from the
listing entirely. A bare `# noqa` is **not** recognised.

```console
$ uvx complexipy --plain -i fx/ign.py
fx/ign.py bare_noqa 1
fx/ign.py plain_fn 1
```

- `--no-ignore` disregards every suppression and analyses all functions.
- `--report-ignored` lists each `file:line` that carries a suppression, plus a
  `Found N suppressed location(s).` count.
- Unprompted, complexipy also prints a "no longer necessary … can be removed" advisory for
  suppressions on functions that are now under threshold. This block goes to **stdout**, including
  under `--plain` — another reason to use the filter in
  [Parsing `--plain` safely](#parsing---plain-safely).

## Diff mode

`--diff <ref>` reports per-function change against a git reference and enforces the threshold on
regressions; `--diff-only <ref>` is visual only.

```console
$ uvx complexipy --diff HEAD .
───────────────────── Complexity diff (vs HEAD) ─────────────────────
Status       Location          Change
REGRESSED    m.py::f     1 → 10  (+9)

Net: 1 regressed
```

Enforcement is **threshold-gated, not delta-gated**: a function that regresses 1 → 10 exits 0,
because 10 ≤ 15. Only a regression that lands *above* `--max-complexity-allowed` exits 1. Isolated
(with `-i` to remove the ordinary threshold check from the picture):

| Command | Exit |
|---|---|
| `complexipy -i m.py` | 0 |
| `complexipy -i --diff HEAD .` | **1** |
| `complexipy -i --diff-only HEAD .` | 0 |

So `-i` does not suppress `--diff` enforcement — only `--diff-only` does.

`--staged` compares the **git index** rather than the working tree against the `--diff` reference
("what am I about to commit?"). With nothing staged it analyses the indexed content, so a dirty
working tree does not affect it.

## Snapshot mode

A legacy-debt ratchet: record today's violations, then fail only on *new* ones.

```bash
uvx complexipy --snapshot-create .   # writes complexipy-snapshot.json, exit 0
uvx complexipy .                     # tolerates recorded violations, exit 0
                                     # a NEW violation -> exit 1
```

The snapshot stores only functions **over** the threshold, grouped per file:

```json
[{"path": "ladder.py", "file_name": "ladder.py",
  "functions": [{"name": "ladder_16", "complexity": 16},
                {"name": "ladder_17", "complexity": 17}]}]
```

On a clean project the snapshot is `[]`. `--snapshot-ignore` (`-spi`) skips the comparison and
falls back to the plain threshold check.

## Configuration file

Three files, in precedence order: `complexipy.toml`, `.complexipy.toml`, then `pyproject.toml`
under `[tool.complexipy]`.

```toml
# complexipy.toml
max-complexity-allowed = 20
exclude = ["tests/**"]
check-script = true
```

Keys are **kebab-case**. The underscore spelling is silently not recognised — verified:
`max-complexity-allowed = 20` lifts the threshold (exit 0), `max_complexity_allowed = 20` does not
(exit 1).

Honoured in TOML: `max-complexity-allowed`, `ignore-complexity`, `exclude`, `quiet`, `sort`,
`check-script`. **CLI-only**: `plain` (documented as such in `--help`) and `top` (undocumented —
`top = 2` in TOML leaves all 17 rows, while `--top 2` returns 2).

## Side-effect files

Running complexipy writes into the **current working directory**:

- `.complexipy_cache/` — always. It self-excludes (ships its own `.gitignore` and `CACHEDIR.TAG`),
  but it does appear.
- `complexipy-results.<ext>` — when `--output-format` is given without `--output`.
- `complexipy-snapshot.json` — from `--snapshot-create`.

## Failure modes

| Condition | Behaviour |
|---|---|
| Missing path | `error: Failed to process <path> - Please check file/folder exists or check syntax`, **exit 1** |
| Syntax error in a file | Same message, same exit. Other files in the tree are still analysed and reported |
| Non-UTF-8 source (e.g. Latin-1) | Same generic message — indistinguishable from a syntax error |
| Modern syntax | Fine: `match`/`case`, walrus, PEP 695 `def f[T]()`, `type` aliases, PEP 701 nested f-string quotes all parse |
| Unknown flag | Usage block, **exit 2** |

The error text is generic across all three of missing-file, bad-syntax, and bad-encoding, so it
cannot be used to classify the fault — check the path exists and the file decodes as UTF-8
separately.

`--suggest-refactors` adds deterministic refactor plans to the rich output (rule `C001`
"Flatten nested condition block with guard clauses", with a line span and an estimated reduction
such as `-~5 complexity (21 -> 16)`). It is ignored under `--plain`, and only populates JSON
`refactor_plans` when passed explicitly.

## Flag inventory

`complexipy --help` at 7.0.1 lists **24 options** plus the variadic `paths` argument. All 24 are
accounted for; 22 are covered above.

| Flag | Short | Covered in |
|---|---|---|
| `--exclude` | `-e` | [Paths, excludes](#paths-excludes-and-gitignore) |
| `--max-complexity-allowed` | `-mx` | [Threshold](#threshold-and-exit-codes) |
| `--snapshot-create` | `-spc` | [Snapshot mode](#snapshot-mode) |
| `--snapshot-ignore` | `-spi` | [Snapshot mode](#snapshot-mode) |
| `--quiet` | `-q` | [Output surface](#output-surface) |
| `--ignore-complexity` | `-i` | [Threshold](#threshold-and-exit-codes) |
| `--failed` | `-f` | [Threshold](#threshold-and-exit-codes) |
| `--color` | `-C` | [Output surface](#output-surface) |
| `--sort` | `-s` | [Output surface](#output-surface) |
| `--output` | | [Machine-readable output](#machine-readable-output) |
| `--output-format` | | [Machine-readable output](#machine-readable-output) |
| `--diff` | `-d` | [Diff mode](#diff-mode) |
| `--diff-only` | | [Diff mode](#diff-mode) |
| `--staged` | | [Diff mode](#diff-mode) |
| `--top` | `-t` | [Output surface](#output-surface), [Config](#configuration-file) |
| `--plain` | | [Parsing `--plain`](#parsing---plain-safely) |
| `--suggest-refactors` | | [Failure modes](#failure-modes) |
| `--check-script` | `-cs` | [What gets reported](#what-gets-reported) |
| `--no-ignore` | | [Suppression comments](#suppression-comments) |
| `--report-ignored` | | [Suppression comments](#suppression-comments) |
| `--version` | | [Invocation](#invocation-and-pinning) |
| `--help` | | — trivial |
| `--install-completion` | | **Omitted** — installs shell completion, unrelated to analysis |
| `--show-completion` | | **Omitted** — prints shell completion script, unrelated to analysis |

Two help-text defects to be aware of when reading `--help` directly:

- `--sort` is described as `'asc', 'desc' or 'name'`, but `name` is **rejected** (exit 2). The
  accepted third value is `file_name`, as shown in the flag's own type signature.
- `--ignore-complexity` is described as "show all functions", which is not what it does — see
  [Threshold and exit codes](#threshold-and-exit-codes).
