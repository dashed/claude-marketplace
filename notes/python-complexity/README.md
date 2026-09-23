# Notes - python-complexity

Meta-documentation for the python-complexity skill plugin.

## Overview

For the Jev integration's reproducible evaluations, observed strengths, and
initial failed readability expectations, see [Jev evals](jev-evals-2026-09-22.md).
For the revised rubric and separate validation, see
[Jev improvement](jev-improvement-2026-09-22.md).
For the paired before/after review, its frozen suite, controls and the comparison
with separate snapshot scores, see [paired changes](jev-changes-2026-09-22.md).

The skill measures per-function cyclomatic (ruff `C901`) and cognitive (`complexipy`) complexity
with no project install, and — since v1.1.0 — the path-level census that a per-function threshold
cannot see: the cost that moves *between* functions when logic is spread over many small ones.

**Core mental model**: two censuses, two levels. Per function, cyclomatic and cognitive answer
different questions and neither is trustworthy alone. One level up, Σ cognitive and decisions
(Σ cyclomatic − defs) plus three counts no census gives — callables entered, argument threading,
selector sites — answer the question the per-function census cannot: is this path over-layered?
Golfing either level pushes code into the other's net.

## Why the path census exists (v1.1.0 design decision)

A real review ran the skill's census on a read path of 23 functions, none scoring above cognitive
8, and the skill's own reading ("sort by cognitive descending, read the top") put every one of them
in the bottom half. The path was Σ cognitive 61 against 24 for the 7-function path it replaced,
34 decisions against 9, and one public call entered 35 callables against 11. The reviewer's
instinct was right and the metrics agreed once totalled — but a per-function threshold would never
have flagged it.

The fixture triple (`mono` / `layered` / `seamed`, 600,000 differential comparisons, 0 mismatches)
reproduced the failure in its strongest form: the per-function census ranks the pass-through-layered
shape as the *best* of the three. That made it a third golf, after comprehension-golf and
ternary-golf, and the skill's "never gate CI" argument one level up.

## Design decisions

- **Extend the skill, no companion.** The path census is the same two tool runs summed, plus three
  `ast` counts; splitting it into another skill would put a seam inside one workflow. The judgment
  reference (`layering-review.md`) is the scope risk; it spins out as a companion if it passes ~400
  lines or acquires non-Python tooling.
- **Decisions, not raw Σ cyclomatic.** McCabe 1976 p. 314 proves cyclomatic sums over components and
  *v = π + 1*, so Σcyclo − defs − nested defs is the predicate count, invariant under extraction
  and under `@overload` stubs. Campbell v1.7 p. 4 says raw Σ cyclomatic is "of little use above the
  method level" — because of the +1 per def that the subtraction removes. Σ cognitive is the
  aggregate Campbell endorses (p. 10) but drifts under extraction; both are reported.
- **Static and dynamic hops, both.** A static resolver enters every arm (what a reader must read);
  a `sys.setprofile` counter sees one input (what runs). On the same fixture 24 vs 19; on the real
  case 24 unpruned vs 19 pruned + 2 generated constructors. Neither number is "the" count; the
  definition is stated with the number.
- **Pass-through ratio was dropped.** A prototype (cyclo 1, cog ≤ 1, one forwarding call) scored
  4 % vs 0 % between the layered and by-meaning shapes; glue in practice carries one gate each.
  Argument threading (a name through ≥ 3 signatures) captures the same thing and separates the
  shapes 5×.
- **Scripts ship; two recipes stay inline.** `path_census.py`, `hops.py`, `hops_dyn.py`,
  `arg_threading.py` are stdlib-only and verified on Python 3.10 and 3.14. The intermediate-
  representation and test-breakage counters are short enough to live as recipes in the reference.
  `threading.py` was the first name for the threading script; it shadowed the stdlib module and
  broke `subprocess` once `scripts/` was on `sys.path`.
- **The two censuses co-lead (v1.2.0).** Five fresh-agent probes with layering-worded prompts
  ("every function is tiny now, is this better?", "the reviewer says it's over-layered", "verify
  the refactor reduced complexity") all invoked the skill and reached the path census — so the
  method worked when found. What was weak was prominence: the first layering concept sat at
  character 188 of the description, the path section at 55 % of SKILL.md with no runnable
  command, and the Codex short description truncated at "hops...". The fix was surface-level:
  a "two censuses" opening table, a co-lead description, a quick start, and the first use of the
  `when_to_use` frontmatter field for the overflow triggers. A companion skill was considered and
  rejected again: the probes showed triggering already works, and a companion would split one
  workflow.
- **Every new tool carries its silent-failure list**, per the skill's genre: `trace --trackcalls`
  ignores its ignore flags; `code2flow` dies silently at `@overload` stubs and merges duplicate
  basenames; `lizard -ENS` is a running total; `radon mi` grades a 6/15 nested function 100; radon
  shares complexipy's nested-class blind spot; ruff silently passes a preview rule selected without
  `--preview`.

## Contents

- `plugins/python-complexity/skills/python-complexity/SKILL.md` — the two censuses, ~170 lines
- `references/cyclomatic-ruff.md`, `references/cognitive-complexipy.md` — tool mechanics, including
  the ruff PLR census and why complexipy rows sum
- `references/interpreting-scores.md` — the per-function judgment layer, including the third golf
- `references/between-function-complexity.md` — the path-census measurement layer
- `references/layering-review.md` — the path-census judgment layer
- `scripts/` — the four stdlib scripts

## Known limitations

- Hop counts are definition-dependent: constructors of dataclasses/NamedTuples have no Python frame
  and are listed as "types constructed", not hops; a hand count that includes them reads 2 higher.
- Static resolution cannot follow `getattr`, dict-of-lambdas dispatch, or callbacks; the scripts
  print each such site as `unresolved`. An unresolved count of 0 is the only clean run.
- No open-source tool computes Henry–Kafura or Card–Agresti fan-in/fan-out for Python; the scripts
  are the nearest substitute, not an implementation of either.
- The path census has no thresholds. Every number is a ratio to a baseline (the replaced path or a
  sibling), and the skill says so.
