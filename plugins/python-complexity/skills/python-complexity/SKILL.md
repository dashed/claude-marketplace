---
name: python-complexity
description: "Measure per-function cyclomatic and cognitive complexity in Python to find refactor targets, using ruff's C901 and complexipy with no project install — then count what neither metric sees between functions: hops per public call, pass-through layers, a selector parameter compared in many places, intermediate types. Use when asking which functions to refactor or clean up first, whether a function or call path is too complex, over-layered, or too indirect, where the worst code in a module or package is, when every function scores low but the code is still hard to follow, when triaging a legacy codebase, when comparing an implementation against the path it replaces, when verifying a refactor reduced complexity rather than relocating it, or when reading C901 / mccabe / complexipy / cognitive-complexity scores. Teaches reading the two metrics as a pair — the gap between them is the signal — the silent-failure modes that make a clean run a lie, and the path-level census a per-function threshold never flags."
license: MIT
---

# Python complexity measurement

Two numbers, two different questions. Run both — neither is trustworthy alone.

| | Cyclomatic (McCabe) | Cognitive (Campbell) |
|---|---|---|
| Tool | `ruff check --select C901` | `complexipy` |
| Counts | branching **statements** | breaks in linear flow, **+1 extra per nesting level** |
| Answers | how many tests cover this? | how hard is this to hold in your head? |
| Blind to | nesting depth, length, expressions | length, params, state, naming |

**The gap between them is the signal.** Identical logic, written three ways (measured, ruff 0.12.7 / complexipy 7.0.1):

| Same 5 conditions, same 6 returns | Cyclo | Cog |
|---|---:|---:|
| flat guard clauses | 6 | 5 |
| nested 5 deep | 6 | **15** |
| nested ternaries | **1** | **15** |

Cyclomatic cannot tell them apart — and scores the *worst* one lowest. Cognitive separates them. That is the whole reason to run two tools.

## When to Use

- "Which functions should I refactor first?" / "where is the worst code here?"
- Triaging a legacy module or an unfamiliar package before working in it
- Checking whether a refactor actually simplified anything — or only moved the numbers
- "Every function here is small, so why is it hard to follow?" / "is this over-layered or too indirect?" / comparing a new implementation against the path it replaces
- Reading a `C901` diagnostic or a complexipy score someone put in front of you

## The two census commands

Both run without installing anything into the project.

```bash
# Cyclomatic — every function, including score-1
ruff check --isolated --ignore-noqa --select C901 --config "lint.mccabe.max-complexity=0" \
  --no-cache --output-format concise path/

# Cognitive — every function, one "<file> <function> <score>" line each
uvx complexipy@7.0.1 --plain --no-ignore path/
```

Five things in the ruff line are load-bearing, not decoration:

- **`max-complexity=0`, not `1`.** C901 fires on `>`, so a threshold of 1 silently omits every complexity-1 function — which is exactly where the worst blind spots live (a 200-line straight-line function scores 1).
- **`--isolated`** — a project's `per-file-ignores` can zero out results with no warning. (A plain `exclude` does *not* silence an explicitly-named path, and `force-exclude` at least warns.) Its cost: project `exclude` stops applying, so vendored and migration dirs reappear.
- **`--output-format concise`** — the default `full` prints a six-line block per function.
- **`--select C901`** — the rule is off by default.
- **`--ignore-noqa`** — `--isolated` does **not** override suppression comments. One `# ruff: noqa: C901` at the top of a file makes the census print `All checks passed!` at exit 0 for that whole file. In triage you want the suppressed ones most: a `# noqa: C901` is usually a marker left on the exact function you are looking for.

`--plain` replaces a box-drawn report full of emoji and `✅ PASSED` markers — never parse the default. But `--plain` is not clean either: advisories interleave into the **same stdout stream**, width-wrapped, while stderr stays empty, so `awk '{print $2, $3}'` picks up junk rows. Filter to lines whose last field is an integer (`awk '$NF ~ /^[0-9]+$/'`), or for anything scripted use JSON:

```bash
uvx complexipy@7.0.1 --output-format json --output scores.json --no-ignore -q path/
jq -r '.[] | "\(.path) \(.function_name) \(.complexity)"' scores.json
```

Write JSON to a real file, not `--output /dev/stdout` — a `Results saved at …` line gets appended after the array and `-q` does not suppress it.

`--no-ignore` is the counterpart to ruff's `--ignore-noqa`: a `# complexipy: ignore` otherwise hides a function silently.

## Silent failures that make a clean run a lie

Both tools have cases where they report success while measuring nothing, and the cases do not overlap — which is the practical argument for running both. These are the ones that bite most; the references list more.

**ruff: a mistyped path exits `0`.** You get `warning: Failed to lint …` then `All checks passed!` — indistinguishable from a clean package. Confirm the target resolves first:

```bash
ruff check --isolated --show-files path/   # prints one absolute path per file; silence = nothing matched
```

**complexipy: methods of any class not at column 0 are never reported.** Not just nested classes — a class inside a function, and (the one that matters in practice) a class under `if TYPE_CHECKING:` or `try:`. Measured: a method in `class Wrapper: class Hidden:` produces **zero output and exit 0** where the de-nested body scores **21** and exits 1; a class under `if TYPE_CHECKING:` is likewise invisible while ruff reports its method normally. Ruff sees it either way — but **do not try to detect this by diffing the two row sets.** A ruff row with no complexipy counterpart is normal, not a warning: it happens for every nested `def`, for every method (complexipy qualifies them as `Klass::method`), and for anything carrying `# complexipy: ignore`. The signal fires constantly on healthy code. Read both listings, and treat a complexipy run that is quiet on a file ruff found functions in as worth a look.

Also: complexipy writes errors to **stdout**, not stderr, and its exit `1` conflates "over threshold" with "file not found or unparseable" — do not infer success from an empty stderr, and mind that the census exits `1` on any function over 15, which trips `set -e`. It also drops a `.complexipy_cache/` directory into the working directory.

## Reading the pair

| | **Low cognitive** | **High cognitive** |
|---|---|---|
| **Low cyclomatic** | Fine — or an invisible monster (check length, closure depth, ternary density) — or a **distributed** one: sum along the call path (next section). | Nested ternaries, or a comprehension doing too much. Read it. |
| **High cyclomatic** | `match`, dispatch table, `except` ladder, or nested `def`s. Usually leave alone. | **Real target.** Nesting on top of genuine branching. |

Sort by **cognitive descending, tie-break by the gap** (cognitive − cyclomatic). A wide positive gap means few branches but a lot of held state — the cheapest wins are there.

A wide gap has **two** causes, and the fix differs:

- **Nesting** → flatten to guard clauses. Reliable: 15 → 5 on identical logic.
- **Mixed boolean density** → name the sub-predicates. A single flat `if` with seven alternating `and`/`or` measures 2 cyclomatic / 6 cognitive with zero nesting.

## When every function scores low: the path census

The per-function census has a third monster. Same behaviour, three shapes (ruff 0.12.7 / complexipy 7.0.1; 600,000 differential comparisons, 0 mismatches):

| Same behaviour | defs | max cyclo / cog | Σcyclo − defs | Σcog | callables entered | one name threaded through N signatures |
|---|---:|---:|---:|---:|---:|---:|
| one function | 1 | 20 / 47 | 19 | 47 | 1 | 1 |
| split into pass-through layers, a selector string threaded | 26 | **3 / 3** | 20 | 38 | **24** | **10** |
| split by meaning | 9 | 4 / 7 | 9 | 20 | 5 | 2 |

Sorted by cognitive descending, the pass-through split is the *best* of the three, and every one of its 26 functions passes every threshold above. That is layer-golf — the third golf, after comprehensions and ternaries — and a per-function threshold cannot see it because the cost moved *between* functions. A real read path measured the same way: 23 functions, none above cognitive 8, against the 7 it replaced — Σ cognitive 61 vs 24, 34 decisions vs 9, 35 callables entered per public call vs 11.

Two numbers from the census you already ran, summed over the files or the path (`scripts/path_census.py` does both):

- **Σcyclo − defs (− nested defs) = decisions.** McCabe's number is additive over components and *v = π + 1* (1976, p. 314), so subtracting the def count leaves the predicate count — invariant under extraction: 19 → 20 → 9. If it did not fall, the split removed nothing. Sum top-level ruff rows only; de-duplicate `@overload` stubs by name (both tools list them as rows).
- **Σcog.** Campbell's paper: the metric "does not increment for the method structure, [so] aggregate numbers become useful." It falls under extraction (nesting penalties vanish), but 47 → 38 is not 47 → 3.

Three counts no census gives — `scripts/` has each, and each prints what it could not resolve rather than hiding it:

- **callables entered** from one public call — static (`scripts/hops.py`: every arm; what a reader must read) and dynamic (`scripts/hops_dyn.py`: one input; what runs). Report both; static 24 vs dynamic 19 on the same fixture is normal.
- **argument threading** (`scripts/arg_threading.py`) — for each parameter name, how many signatures on the path carry it. Three or more is a pass-through variable.
- **selector sites** (same script, `--name`) — a parameter compared in several functions to re-discover which public call was made.

There are no thresholds between functions. Compare against the path the code replaced, or a sibling that solves the same problem: 23 defs / Σcog 61 / 34 decisions against 7 / 24 / 9 is the finding; 61 alone is not.

Golfing these numbers pushes code back toward one function, which the per-function census catches. Golfing the per-function census pushes it toward pass-through layers, which these catch. Same argument as running cyclomatic and cognitive together — one level up.

Commands, scripts and each tool's silent failures: [references/between-function-complexity.md](references/between-function-complexity.md). Deciding which layers protect an invariant and which are glue: [references/layering-review.md](references/layering-review.md).

## What the numbers cannot see

Measured fixtures scoring **1 cyclomatic / 0 cognitive** — all obviously bad:

- a 203-line straight-line function
- 15 parameters, 7-deep attribute chains, mutating 8 objects
- a function named `validate_user` whose body sets `is_admin = True`
- nine ternaries buried in arithmetic

Two of these are visible to ruff rules the census does not select, in the same run: `PLR0913` (the 15 parameters) and `PLR0915` (the 203 statements — but it counts `return` and `for` as 0, so a one-line forwarder is invisible at any threshold). A third blind spot — `with` and `try/finally` nesting, which cognitive complexity scores at 0 — is seen by `PLR1702 --preview` (a 5-deep pyramid of either: complexipy 0, PLR1702 5). Nothing sees the closure pyramid except `radon cc --show-closures`. Commands and the per-rule quirks are in [references/cyclomatic-ruff.md](references/cyclomatic-ruff.md).

Two specific traps worth memorizing:

- **A 5-level nested-closure callback pyramid scores cognitive 0** — the deepest visual nesting possible, invisible because closures carry no structural increment.
- **complexipy 7.0.1 drops expression complexity under certain parent nodes.** Control: `if a: return 1` plus `return (2 if b else 3) + (4 if c else 5)` scores 1 — identical to the bare `if` alone — while the same `if` with a *bare* ternary scores 2. It is **not** a ternary bug: the same contexts also swallow boolean operators and comprehensions. Whether the cost survives depends on the *parent node*, with asymmetries that give the game away — a dict **value** counts but a dict **key** does not; a **positional** call argument counts but a **keyword** argument does not. Silently dropped: binary and unary operators, f-strings, subscripts and slice bounds, dict keys, keyword arguments, `*`-unpacking, attribute access, `yield` values. 7.0.1 is the latest release and no upstream issue matches, so assume it is live; the tested-context table is in the reference, and untested node types may drop cost too.

Ruff's McCabe **counts statements, not expressions**, so `and`/`or`, ternaries, and comprehension `if` clauses all cost exactly **0**. One consequence, both directions: rewriting an `if` chain as one boolean expression drives the score toward 1 without making it readable, and expanding a dense predicate back into statements *raises* it.

## Thresholds

Only two numbers here are sourced, and neither is a law:

- **Cyclomatic 10** — McCabe 1976, §III p. 314: "a reasonable, but not magical, upper limit." The same page prescribes the response to exceeding it — "recognize and modularize subfunctions" — and §IV proves that modularizing does not reduce the total: the complexity of a collection of components is the sum of their complexities. The threshold and the third golf come from one page. It is ruff's default. (Definition 1 there is *v = e − n + p*; the *e − n + 2p* form is program complexity after the virtual exit→entry edge.)
- **Cognitive 15** — complexipy's tool default (verified by bisection: 15 passes, 16 fails). **Campbell's white paper recommends no numeric threshold at all** — verified across pp. 1–17 of v1.7, including the Appendix B specification; it specifies the metric, not a limit. Do not cite "SonarSource says 15" as a research finding.

Treat both as screening lines that decide *what to read*, never as pass/fail gates.

## Workflow

1. **Census, not screening.** Threshold `0` for ruff; complexipy lists everything by default (`-i` changes only the exit code, not which rows print).
2. **Sort by cognitive, tie-break by the gap.**
3. **Read the top candidates.** The number says *where to look*, never what is wrong. Confirm the shape — nesting, boolean density, or neither — before touching anything.
4. **Pin behavior first.** Get the function under test with branch coverage *before* editing. A falling score is not evidence of behavior preservation; the two are unrelated.
5. **Split by meaning, not to move the number.** If you cannot name the extracted piece without `_part2` or `_helper`, the seam is wrong — put it back. Then count what the split added — callables entered, names threaded through three or more signatures, types introduced. If the decisions count (Σcyclo − defs) did not fall, the split removed nothing.
6. **Re-measure and re-read — the path, not the function.** The number must drop *and* the code must read better. If only the number moved, you golfed it — revert. If every function reads fine alone and the path does not, you layer-golfed — same verdict.

**Never gate CI on these numbers.** As a merge gate they select for exactly the constructs both metrics undercount: comprehensions, ternary chains, and splitting — an 11/18 function cut into eight ≤ 3s passes every per-function gate. A measured example — a rules loop refactored from 11/18 to 1/6, behavior verified identical over 20,000 randomized inputs — moved the scoring rules into a module-level lambda table and started silently swallowing unknown operators that an `elif` chain had made visible. Cyclomatic fell 91%, and the code got worse.

The metrics are a **locator, not a verdict**. They answer "which 20 of these 800 functions should a human read first?" well — one function at a time. They cannot locate a monster spread over 23 functions that each score under 8; that is what the path census is for. They do not answer "is this function good?"

## References

- [references/cyclomatic-ruff.md](references/cyclomatic-ruff.md) — the full `C901` surface: threshold mechanics, all 12 output formats and JSON extraction, exit codes, config interference and what `--isolated` costs, `noqa` suppression, a measured construct→increment table, scope/granularity, caching, and 0.12.7 vs 0.16.x differences
- [references/cognitive-complexipy.md](references/cognitive-complexipy.md) — complexipy's flags and output modes, machine-readable extraction, the measured construct→cost table and what raises nesting depth, exit-code semantics, `.gitignore` handling, its diff and snapshot modes, and four places the upstream scoring docs are wrong
- [references/interpreting-scores.md](references/interpreting-scores.md) — the fixture corpus behind the tables above, the three seed heuristics tested (one needed qualification), the blind-spot catalogue with a failed-attempt negative result, and the full metric-golfing worked example
- [references/between-function-complexity.md](references/between-function-complexity.md) — open when every function scores low and the code is still hard to follow: the layering fixture triple, the path census (Σ cognitive, decisions), callables entered static and dynamic, argument threading and selector sites, intermediate representations, predicting what a refactor breaks, the ruff PLR rules that see the non-branching blind spots, and the silent failures of every tool involved
- [references/layering-review.md](references/layering-review.md) — open when the path census says a path is 2–4× its baseline and you have to decide which layers stay: structure vs safety, the layer → invariant → verdict table, comparing against sibling implementations, what the tests pin, the alternatives and before/after tables, ordering the work, and separating policy questions from layering questions

Scripts (stdlib only; `python3 scripts/<name>.py` prints usage): `scripts/path_census.py`, `scripts/hops.py`, `scripts/hops_dyn.py`, `scripts/arg_threading.py`.
