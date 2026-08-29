# Interpreting complexity scores

How to read a cyclomatic and a cognitive score *together* to locate refactor targets, and where
both numbers lie to you.

Tool mechanics live in the sibling files — [cyclomatic-ruff.md](cyclomatic-ruff.md) and
[cognitive-complexipy.md](cognitive-complexipy.md). This file is the judgment layer.

**Provenance.** Every number below was measured on ruff 0.12.7 (`C901`) and complexipy 7.0.1,
macOS, against fixtures written for this file. Nothing is quoted from a blog post. Where a claim
is inference rather than measurement it is labelled **(inferred)**.

## Table of contents

- [What each number actually counts](#what-each-number-actually-counts)
- [Measurement hygiene](#measurement-hygiene)
- [The fixture corpus](#the-fixture-corpus)
- [Reading the pair](#reading-the-pair)
- [The three heuristics, tested](#the-three-heuristics-tested)
- [Magnitude guidance](#magnitude-guidance)
- [Blind spots](#blind-spots)
- [Metric golfing](#metric-golfing)
- [The workflow](#the-workflow)

## What each number actually counts

**Cyclomatic (McCabe 1976)** counts linearly independent paths — the minimum number of test cases
for full branch coverage. It was designed "to identify software modules that will be difficult to
test or maintain." It is a *testability* number that gets borrowed as a readability number.

**Cognitive (Campbell / SonarSource)** was written specifically because the borrowing fails. Its
white paper opens by noting that cyclomatic "is not a satisfactory measure of understandability"
and "cries wolf" by over-valuing some structures and under-valuing others. Three rules: ignore
shorthand, +1 per break in linear flow, and **+1 extra per level of nesting**.

The nesting rule is the whole difference. Everything useful about reading the two numbers together
follows from it.

Behaviours confirmed against both the published spec and measurement here: `try` and `finally` are
ignored entirely, each `except` is +1, a whole `match` costs +1 total, early `return` costs
nothing, and a *sequence* of like boolean operators costs +1 for the sequence rather than +1 per
operator.

## Measurement hygiene

Two things that silently corrupt a survey before you interpret anything.

**1. A threshold of 1 does not list everything.** `C901` fires on `>`, so `max-complexity=1` hides
every complexity-1 function. Use `0` for an exhaustive census:

```
lint.mccabe.max-complexity=1  ->  c1_trivial absent, c2_one_if (2 > 1), c3_two_ifs (3 > 1)
lint.mccabe.max-complexity=0  ->  c1_trivial (1 > 0), c2_one_if (2 > 0), c3_two_ifs (3 > 0)
```

This matters because complexity-1 functions are exactly where the worst [blind spots](#blind-spots)
live. Screening at 1 discards the evidence.

**2. The two tools do not enumerate the same functions.** Measured on a thin wrapper containing one
fat closure:

| | ruff | complexipy |
|---|---|---|
| `outer_thin` | 7 | 7 |
| `inner_fat` (nested `def`) | 6 | *not reported* |

ruff emits a row per function **including nested ones**, and the parent's score **includes its
children**. complexipy reports top-level functions only and rolls nested cost into the parent.
So: do not join the two outputs by name — ruff's `inner_fat` has no counterpart, and its
`outer_thin: 7` double-counts what it already reported. And a high ruff score can be pure `def`
nesting: `register` below scores **6 with zero conditionals**, one point per nested `def`.

## The fixture corpus

Purpose-built shapes, both metrics, one measurement pass.

| Fixture | Shape | Cyclo | Cog | Gap |
|---|---|---:|---:|---:|
| `gate_flat` | 5 guard clauses, early return | 6 | 5 | −1 |
| `gate_nested` | **identical logic**, nested 5 deep | 6 | **15** | +9 |
| `gate_ternary` | **identical logic**, nested ternaries | **1** | **15** | +14 |
| `overlay_regions` | loop + layered conditionals | 8 | 18 | +10 |
| `read_shape` | 3-arm dispatch, per-arm branching | 8 | 14 | +6 |
| `collect_loop` | nested loop with filters | 6 | 11 | +5 |
| `collect_comp` | **same logic** as one comprehension | 1 | 5 | +4 |
| `bool_guard` | one `if`, 7 mixed boolean operators | 2 | 6 | +4 |
| `elif_chain_12` | 12-arm `if/elif` ladder | 12 | 11 | −1 |
| `match_12` | 12-arm `match` | 12 | **1** | **−11** |
| `try_except_ladder` | 3 `except` handlers | 4 | 3 | −1 |
| `build_report` | 200 straight-line statements | 1 | 0 | 0 |
| `register` | 5-deep nested-closure pyramid | 6 | **0** | −6 |
| `sync` | 15 params, deep chains, mutation | 1 | 0 | 0 |
| `enter` | 3-deep `try/finally`, global mutation | 1 | 0 | 0 |
| `price_ternary` | 9 ternaries inside arithmetic | 1 | **0** | 0 |

`gate_flat` / `gate_nested` / `gate_ternary` are the same five conditions and the same six return
values, written three ways. That triple is the core result: **cyclomatic cannot distinguish them
at all** (6, 6, 1 — and the 1 is *lowest* for the worst one), while cognitive separates them 5 / 15
/ 15.

## Reading the pair

|  | **Low cognitive** | **High cognitive** |
|---|---|---|
| **Low cyclomatic** | Fine — or an invisible monster. Check length, closure depth, ternary density before believing it. | Rare. Nested ternaries or a comprehension doing too much. Read it. |
| **High cyclomatic** | `match`, dispatch table, `except` ladder, or nested `def`s. Usually leave alone. | Real target. Nesting on top of genuine branching — refactor here first. |

Priority order for a survey: **sort by cognitive descending, then break ties by the gap
(cognitive − cyclomatic).** A large positive gap means the branch count is small but the reader
still has to hold state — the cheapest wins are there. `gate_nested` (6/15) is a better target than
`elif_chain_12` (12/11) despite half the cyclomatic score.

## The three heuristics, tested

**1. "cognitive >> cyclomatic → branches are nested" — half right; needs a second cause.**

Confirmed in the strongest possible form: `gate_flat` and `gate_nested` have *identical* cyclomatic
(6) and cognitive 5 vs 15. Same logic, same branch count, 3× the cognitive score, and nesting is the
only difference.

But nesting is not the only thing that opens the gap. `bool_guard` is a **single flat `if`** with
zero nesting and scores 2 / 6. Isolating it:

| Condition | Cyclo | Cog |
|---|---:|---:|
| `if a` | 2 | 1 |
| `if a and b and c and d` | 2 | 2 |
| `if a and b or c and d` | 2 | 4 |
| `if a and b or c and d or e and f or g and h` | 2 | 6 |

ruff's mccabe charges **nothing** for boolean operators — all four are 2. Cognitive charges +1 per
*sequence of like operators*, so alternating `and`/`or` inflates it with no nesting at all. Revised
rule: **a large positive gap means nesting *or* mixed-operator boolean density.** Look at the code
to tell which; the fix differs (flatten vs. name the sub-predicates).

**2. "cognitive ≈ cyclomatic at modest values → flat ladder, often fine" — holds.**

`gate_flat` 6/5, `elif_chain_12` 12/11, `try_except_ladder` 4/3. Every near-equal pair in the corpus
is genuinely a flat ladder. The heuristic did not misfire once.

Caveat on the "modest" qualifier: near-equality at *high* values is still a lot of branches. 12/11
is a fine ladder to read but still needs 12 test cases.

**3. "a gate cascade of early returns scores low cognitive even with several branches" — holds.**

`gate_flat`: 5 conditions, cognitive 5 — one point per `if`, nothing for the five `return`s. The
spec is explicit that early exits are free ("because an early return can often make code much
clearer, no other jumps or early exits cause an increment"). Converting nesting to a guard-clause
cascade is the one refactor where the cognitive drop reliably tracks a real readability gain:
15 → 5 on identical logic.

## Magnitude guidance

Thresholds are conventions, not laws. Only these are sourced:

- **Cyclomatic 10** — McCabe's own figure from the 1976 paper, described there as
  "a reasonable, but not magical, upper limit," later adopted by NIST. It is **ruff's default**
  (`max-complexity = 10`; measured — ruff's own message reads `is too complex (14 > 10)` with no
  config).
- **Cognitive 15** — **complexipy 7.0.1's default**, established here by bisection: a function
  scoring 15 passes, 16 fails.

**The Campbell white paper recommends no numeric threshold at all.** Read pages 1–13 (introduction
through conclusion and references) of v1.7, 29 Aug 2023: it specifies the *metric*, not a limit. Do
not cite "SonarSource says 15" as a research finding — 15 is a tool default. **(inferred)** Treat
both defaults as screening lines that decide *what to read*, never as pass/fail gates.

## Blind spots

Constructed adversarially: code that is obviously bad and scores near zero. All measured.

| Fixture | What is wrong with it | Cyclo | Cog |
|---|---|---:|---:|
| `build_report` | 200 straight-line statements, 203 lines | 1 | 0 |
| `sync` | 15 parameters, 7-deep attribute chains, mutates 8 objects | 1 | 0 |
| `enter` | 3-deep `try/finally`, mutates a module global | 1 | 0 |
| `validate_user` | name says validate; body clears the password and sets `is_admin = True` | 1 | 0 |
| `transform` | `dict(zip(map(lambda...), map(lambda...)))` over two sorts | 1 | 0 |
| `register` | 5-level nested-closure callback pyramid | 6 | **0** |
| `price_ternary` | 9 ternaries buried in arithmetic | 1 | **0** |

Neither metric sees: length, parameter count, attribute-chain depth, shared-state mutation,
naming, `try`/`finally` nesting, or `with` nesting. **Cognitive complexity scored a five-level
callback pyramid at 0** — the deepest visual nesting in the corpus, invisible because closures
carry no structural increment and there is no branch inside to collect the nesting penalty.

### Testing the two stock caveats

**"Ternaries barely register in either" — wrong for cognitive, right for cyclomatic.**

Cyclomatic ignores conditional expressions **absolutely**: ten ternary variants, every one scored 1.
Cognitive is position-dependent:

| Form | Cog |
|---|---:|
| `return 1 if a else 2` | 1 |
| `return 1 if a else 2 if b else 3 if c else 4` | 6 |
| `gate_ternary` (5 nested ternaries) | **15** |
| `return max(1 if a else 2, 3 if b else 4)` | 2 |
| `return [1 if a else 2, 3 if b else 4]` | 2 |
| `return (1 if a else 2) > 0` | 1 |
| `return (1 if a else 2) + 3` | **0** |
| `return (1 if a else 2) + (3 if b else 4)` | **0** |
| `return f"{1 if a else 2}"` | **0** |

So nested ternaries *do* register — `gate_ternary` ties `gate_nested` at 15. The caveat is wrong
there.

**But there is a reproducible defect underneath.** A ternary that is an operand of an arithmetic
`BinOp`, or inside an f-string, scores **0** — and the suppression propagates outward
(`max(0, (1 if a else 2) + (3 if b else 4))` is also 0). Control, proving the ternary specifically
is dropped rather than the function skipped:

| | Cyclo | Cog |
|---|---:|---:|
| `if a: return 1` / `return b` | 2 | 1 |
| same `if` + `return (2 if b else 3) + (4 if c else 5)` | 2 | **1** |
| same `if` + `return 2 if b else 3` | 2 | 2 |

The `if` still counts; two ternaries add nothing. This contradicts the spec, which lists ternary
operators as taking a structural increment. **(inferred)** complexipy 7.0.1 defect, not a design
choice. Practical consequence: `price_ternary` — nine ternaries, mixed polarity, no early exit —
measures **1 / 0**, indistinguishable from an empty function. Arithmetic-heavy ternary code is the
one place both metrics are simultaneously blind.

**"Comprehension tricks lower both scores while hurting readability" — confirmed, and worse than
stated.**

| Same logic, three ways | Cyclo | Cog |
|---|---:|---:|
| `collect_loop` — nested `for` with `continue` filters | 6 | 11 |
| `collect_comp` — one flat comprehension | **1** | 5 |
| `collect_comp_nested` — comprehension over a comprehension | **1** | 7 |

Cyclomatic collapses to **1 regardless** — comprehension `for`/`if` clauses are invisible to it.
Cognitive halves. And `collect_comp_nested` is harder to read than `collect_comp` yet still scores
1/7 against the loop's 6/11. Rewriting a loop as a comprehension is the single cheapest way to make
a number drop without touching the difficulty.

### One more, and a failed attempt

The nested-closure result above is the additional blind spot: **cyclomatic can be inflated by pure
`def` nesting with no branching** (`register`: 6, zero conditionals), which is the mirror image —
a false *positive*. A survey sorted by cyclomatic alone puts a branch-free registration function
next to genuinely tangled code.

**Failed attempt, reported as negative result:** I could not construct a function that is hard to
read *because of its control flow* and still scores low on cognitive complexity. Every attempt —
deep `if` nesting, loops in loops, `except` ladders, nested ternaries — was caught. The metric is
sound within its domain; every successful blind spot I found was some *other* axis of badness
(length, naming, state, parameters, closures) or the arithmetic-ternary defect. **(inferred)** That
is the honest scope: cognitive complexity measures branching structure well and measures nothing
else at all.

## Metric golfing

Both numbers fail Goodhart's law hard. A worked pair — identical behaviour, verified by a
differential test over 20,000 randomized inputs (0 mismatches):

```python
# BEFORE — cyclomatic 11, cognitive 18
def classify_before(rec, rules):
    score = 0
    for rule in rules:
        if rule.field not in rec:
            continue
        value = rec[rule.field]
        if rule.op == "eq":
            if value == rule.arg:
                score += rule.weight
        elif rule.op == "gt":
            ...
    if score >= 100:
        return "high"
    if score >= 50:
        return "medium"
    return "low"

# AFTER — cyclomatic 1, cognitive 6
_OPS = {"eq": lambda v, a: v == a, "gt": lambda v, a: v > a, "in": lambda v, a: v in a}

def classify_after(rec, rules):
    score = sum(
        r.weight
        for r in rules
        if r.field in rec and _OPS.get(r.op, lambda v, a: False)(rec[r.field], r.arg)
    )
    return "high" if score >= 100 else "medium" if score >= 50 else "low"
```

Cyclomatic −91%, cognitive −67%, and the code got worse: the scoring rules moved into a
module-level lambda table, `_OPS.get(..., lambda v, a: False)` silently swallows an unknown
operator that the `elif` chain at least made visible, and the thresholds became a ternary chain.
A reviewer told only "complexity dropped from 11 to 1" would approve this.

Both techniques used here — comprehension-ification and ternary chains — are the exact ones the
[blind spots](#blind-spots) section shows are undercounted. **Metric-driven refactoring
preferentially selects for the constructs the metric cannot see.**

## The workflow

1. **Census, not screening.** Run cyclomatic at threshold `0`; complexipy already lists every
   function by default (`-i` changes only the exit code, not which rows print). Screening
   cyclomatic at a threshold hides the complexity-1 monsters.
2. **Sort by cognitive, tie-break by the gap.** See [Reading the pair](#reading-the-pair).
3. **Read the top candidates.** The number said *where to look*. It did not say what is wrong.
   Confirm the shape — nesting, or boolean density, or neither — before touching anything.
4. **Pin behaviour first.** Get the function under test with branch coverage *before* editing.
   A falling score is not evidence of behaviour preservation; the two are unrelated. Nothing below
   is safe without this step.
5. **Split by meaning, not to move the number.** Name the extracted piece after the concept it
   owns. If you cannot name it without "part2", "helper", or "_impl", the split point is wrong —
   put it back and find a real seam.
6. **Re-measure, then re-read.** The number must drop *and* the code must read better. If only the
   number moved, you golfed. Revert.
7. **Never gate CI on the number alone.** Use it to rank a backlog. As a merge gate it selects for
   comprehensions and ternaries — see [Metric golfing](#metric-golfing).

The metrics are a **locator, not a verdict**. They answer "which 20 of these 800 functions should a
human read first?" — well. They do not answer "is this function good?", and `sync`, `enter`,
`register`, and `price_ternary` are the proof.
