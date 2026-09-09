---
name: test-sloc-cut
description: "Shrink a test suite without losing a single asserted fact or covered branch — the fact-matrix method: read every test into a matrix of the propositions it pins, measure per-test branch coverage and a covering set, and delete only on the intersection of both oracles; relocate a fact to a cheaper layer only after a mutant proves the new assertion catches it. Use when asked to trim, dedupe, consolidate, simplify, shrink, or reduce tests or test SLOC, when a suite has grown by accretion (the same value asserted in a pure test, a DB test and an end-to-end test; tests whose bodies differ by one argument), when deciding whether to delete, fold, parametrize, or share a helper across tests, when a reviewer calls a test file bloated or redundant, or before cutting any test on 'coverage is unchanged' alone. Python/pytest with pytest-cov. Ships the tokenizer line counter, the per-test coverage and covering-set script, the mutant check, and the four-agent investigation briefs."
license: MIT
---

# Cutting test SLOC without losing coverage

A repeatable way to shrink a test suite while keeping every asserted fact and every covered branch. Developed on a billing feature spread over two stacked branches: four test files, 61 tests, 757 code lines went to three files, 46 tests, 608 code lines, and the per-module branch coverage measured after the cut was identical to the map measured before it.

The method rests on one rule and two oracles.

**The rule.** A test, or a line of a test, may go only if every fact it asserts is still asserted by a surviving test on the *same production path*, and the measured branch coverage of the production modules does not change.

**The two oracles.** Neither is sufficient alone.

| Oracle | Answers | Blind to |
|---|---|---|
| Fact matrix (read the code) | which propositions each test pins; which are duplicated, which are pinned once | branches nobody thought to name |
| Per-test branch coverage (run the code) | which lines and arcs each test uniquely reaches | assertion strength: two tests can walk the same lines and assert different values |

"Coverage-redundant" and "assertion-redundant" are different properties. A test with an empty unique-coverage set may still be the only one that fails when a value is wrong. Delete on the intersection of both oracles, never on one.

## When this applies

Use it when a suite has grown by accretion: several review passes, tests added per bug, three files that each provision the same object their own way. Signs: the same value asserted in a pure test, a DB test and an end-to-end test; tests whose names differ but whose bodies differ by one argument; comments that narrate the assertions below them.

Do not use it to reach a number. Every cut is justified by a fact that survives elsewhere or a measured coverage identity. If a proposed cut cannot show either, it is not a simplification — it is a coverage loss with a smaller diff.

## The workflow

1. **Baseline** — pin the commit; count lines and tests per file with the tokenizer.
2. **Investigate** — four angles in parallel, exactly one of which runs tests.
3. **Synthesize** — decide every candidate against the table below; two rules override it.
4. **Execute** — base branch first; lint with explicit paths; mutant-check every relocated fact.
5. **Report** — before/after numbers, and which surviving test now owns each deleted test's facts.

## 1. Baseline

Pin the tree at one commit and record three numbers per file: total lines, code lines (non-blank, non-comment; docstrings count as code because a reader has to read them), test count. Count with the tokenizer, not `grep -v '^#'`, so multi-line strings and trailing comments are classified correctly:

```bash
python3 scripts/count_code_lines.py tests/test_a.py tests/test_b.py
#   26 total    14 code    1 comment-only    5 tests  tests/test_a.py
```

If the files live on stacked branches, write down which branch owns which file. A helper added on the base branch is visible to the dependents; the reverse is not true, and the cut has to be committed base-first.

## 2. Investigate: four angles in parallel, one test runner

Spawn four agents at once, each writing a markdown report to a scratch directory outside the repo. Three are read-only; **exactly one may run tests**, because a shared test database does not tolerate concurrent runs. Keep the prompts lean: file list, production modules, the deliverable's shape, the constraints. The full brief for each is in [references/investigation.md](references/investigation.md).

**Fact matrix.** One row per test: file, name, the production function or branch it drives, and the facts it asserts as short propositions with stable ids (`F12: an override for an unpublished category creates no entry`). Then: facts already owned *outside* the files under review (look one layer down — a parity test there may already pin by exact comparison everything these files re-assert); cross-file duplicates with one owner per fact, where the cheapest layer that can prove the fact wins (pure over DB, DB over end-to-end) *except* facts about wiring, persistence, metric emission or legacy behaviour, which only the layer that exercises them can prove; **strict subsets**, proven against the mutants each would kill, not by name; **single-pinned facts** — the do-not-touch set; fold proposals with honest line estimates.

**Helper and arrangement economics.** Inventory every helper with call-site count and lines saved versus cost. A parametrized block costs `N + 7` lines against 2–3 per replaced test, so break-even is seven two-line tests — and every row must be width-checked at its real indent; rows that need shortening devices pay for those too. Refuse line-neutral parametrization: it deletes the descriptive names. Check what the constructor already accepts before proposing a builder; keep shared helpers local below ten lines net; adopt a width alias everywhere in a file or nowhere.

**Comment audit** (prose-heavy files). Every comment block passes or fails the three-clause test — true at this layer, not visible in the code in front of the reader, not stated better nearby — with a verdict of keep, trim (with replacement text) or delete. A comment the code contradicts is never a keep; the fix is often to import the production constant the literal was. The `comment-slop` skill is the method for this angle.

**Per-test branch coverage** (the runner). Run only the files under review, serially, with per-test contexts; compute each test's unique contribution and a greedy minimum covering set, and **verify the set by running only those tests** and comparing the item union to the baseline. Commands, the script, and the six traps that produce a wrong map are in [references/coverage-and-mutants.md](references/coverage-and-mutants.md).

**Leave-one-out is not a licence.** If exactly two tests reach a line, neither is unique, yet dropping both loses the line. The covering set is the floor, not a target: in the worked example 11 of 61 tests reproduced all 514 covered items, and the other 50 had to justify themselves on assertion strength.

## 3. Synthesis

Read all four reports before touching a file. Dedupe findings that name the same test or mechanism, then decide each with this table.

| Candidate | Take when | Refuse when |
|---|---|---|
| delete a test | the fact matrix shows a strict subset on the same path *and* coverage shows no unique arcs | the coverage runner lists it in the covering set, or any fact is single-pinned |
| fold N tests into one | they share a fixture and the merged test asserts every fact of each; a shared patch (a distinct sentinel value) makes the merged assertions stronger | the merge collapses two distinct input paths into one row label |
| move a fact to a cheaper layer | the fact is about a pure function but was only pinned through a DB or end-to-end test | the fact is about wiring, persistence, metric emission, or legacy behaviour |
| parametrize | net lines saved after counting shortening devices, and ids carry what the names carried | line-neutral, or the rows exceed the width limit |
| shared helper | at least 10 lines net and no house convention against it | below that, or it needs a wrapper per file anyway |
| alias for width | ten or more wrapped calls; apply everywhere in the file | fewer than about four sites |
| trim a comment | a clause narrates the assertions below it or restates a sibling file | the clause is the only statement of a why |

Two rules override the table:

1. **A relocated fact is proven, not assumed.** Write the new assertion, then temporarily break production the way the fact forbids and watch the new assertion fail. Pick the fixture so the mutant is visible: a fixture whose value the mutant happens to leave unchanged (an exemption, a coincidence of defaults) proves nothing — the first attempt in the worked example had exactly that flaw. Recipe in [references/coverage-and-mutants.md](references/coverage-and-mutants.md).
2. **Boundary pairs stay as two named tests.** A test on the cutoff day and a test one day past it differ by one day on purpose. The names are the documentation; do not fold them into a table row.

Multi-value assertions can be one tuple comparison (`assert (standard, downsampled) == (365, 90)`): pytest prints both tuples on failure and the names sit on one line.

## 4. Execution on stacked branches

1. Base branch first. Move the working copy onto its tip, write the files, delete the files whose facts moved.
2. Lint with **explicit file paths**. In zsh an unquoted `$files` variable is not word-split, so a linter receives one bogus path and passes having checked nothing — three over-width lines reached a pushed tip that way. After the linter, read `git diff --stat` to see what hooks rewrote.
3. Type-check the tests too; helper signatures need annotations.
4. Run the affected suites, then the mutant check for every relocated fact, then restore production.
5. Commit, move the bookmark or branch, rebase the dependent branch onto it.
6. Repeat on the dependent branch.
7. Re-run the coverage command against the reduced files and compare per-module `covered` and `arcs taken` against the baseline JSON. The numbers must be identical per module. If a module lost an arc, find the deleted test that owned it in the baseline's per-test table and restore its assertion somewhere.
8. Commit messages say what was folded into what and why the facts survive, and record that coverage was re-measured.

## 5. Report

| | before | after |
|---|---|---|
| tests | | |
| code lines | | |
| total lines | | |
| branch coverage per module | baseline | identical / differences |

Then, per branch: which tests were deleted and which test now owns each of their facts; which facts moved to a cheaper layer and the mutant that proved them; which comments were trimmed and which false claims fixed; what was refused on the reports' own advice and why. Name the process defects found on the way. The condensed worked example — what the oracles said, what was done, what was refused — is [references/worked-example.md](references/worked-example.md).

## Scripts and references

- `scripts/count_code_lines.py` — the tokenizer line counter (stdlib).
- `scripts/coverage_map.py` — per-test unique coverage and the verified covering set, from a serial per-test-context run (needs `coverage` importable in the test environment).
- [references/investigation.md](references/investigation.md) — the four angles in full, and the brief skeleton for each agent.
- [references/coverage-and-mutants.md](references/coverage-and-mutants.md) — the `.coveragerc`, the pytest command, reading the map, the six traps, verifying the covering set, and the mutant check for a relocated fact.
- [references/worked-example.md](references/worked-example.md) — the 61 → 46 cut: what each oracle found, what was done, what was refused.

Related skills: `comment-slop` for the comment audit; `pytest` for the runner's mechanics.
