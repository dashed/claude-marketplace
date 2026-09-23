# Coverage map and mutant check

The runner's half of the method: how to measure which lines and arcs each test uniquely
reaches, how to get a covering set you can trust, the traps that produce a wrong map, and how to
prove a relocated fact with a mutant.

**Provenance.** Every `coverage_map.py` output block below is real output from the fixture project
in the marketplace repository (`tests/fixtures/test-sloc-cut.json`), measured with pytest 9.0.1,
pytest-cov 7.0.0 and coverage 7.12.0 on Python 3.10. `tests/test_test_sloc_cut.py` re-runs every
block and fails if one drifts. The numbers from the worked example (61 tests, 514 items, an
11-test cover) are quoted from that cut, not re-run here.

## Table of contents

- [The instrumented run](#the-instrumented-run)
- [`scripts/coverage_map.py`](#scriptscoverage_mappy)
- [Reading the map](#reading-the-map)
- [Verify the covering set](#verify-the-covering-set)
- [After the cut](#after-the-cut)
- [Traps that produce a wrong map](#traps-that-produce-a-wrong-map)
- [Mutant check for a relocated fact](#mutant-check-for-a-relocated-fact)

## The instrumented run

Put a `.coveragerc` in a scratch directory **outside the repo**, so the project's own coverage
configuration is bypassed and nothing lands in the working tree:

```ini
[run]
branch = True
relative_files = True
data_file = /path/to/scratch/.coverage
parallel = False
include =
    */package/module_one.py
    */package/module_two.py

[json]
show_contexts = True
```

Run, **serially**, only the test files under review, with one context per test:

```bash
rm -f /path/to/scratch/.coverage
pytest -p no:cacheprovider -q \
  --cov --cov-config=/path/to/scratch/.coveragerc --cov-context=test --cov-report= \
  tests/a_test.py tests/b_test.py
```

`--cov` bare plus `--cov-config=<rcfile>` is what activates the rcfile's `include` filter.
`--cov=<pkg>` would set `source` instead and make `include` inert (see the traps).

## `scripts/coverage_map.py`

```
python3 scripts/coverage_map.py --scratch DIR [--range MOD=LO-HI ...] [--out FILE] MODULE [MODULE ...]
python3 scripts/coverage_map.py --diff BASELINE.json AFTER.json
```

`MODULE` is the repo-relative path as recorded in the data file (`relative_files = True`). Run it
from the project root, with an interpreter that can import the `coverage` that wrote the data
file — the test environment's, or `uvx --with coverage python3 …`. It writes `DIR/analysis.json`
(or `--out`) with four sections:

- `modules`: statements, covered, missing lines, branch arcs, arcs taken, and `covered_items`,
  every covered line and arc by name.
- `per_test`: one entry per test node id, with pytest's setup, call and teardown phases merged.
  Each has its item count per phase, the lines it reaches, `unique` (the lines and arcs no other
  test reaches), and `subline` (reached lines whose outcomes coverage cannot see; see the traps).
- `cover`: a greedy minimum covering set over what only tests supply.
- `provenance`: the module hashes and coverage version that `--diff` requires to match.

`--range pkg/big.py=558-689` scopes a large module to the functions under test. Save the baseline
under its own name before the cut (`--out scratch/baseline.json`); every later run is compared
with it by `--diff`.

On the fixture — a `price()` with an `if`/`elif`/`else` on the kind and a `try/except` around
parsing the discount, a `label()` with one branch, and five tests of which two are equivalent:

```
$ python3 scripts/coverage_map.py --scratch scratch --out scratch/baseline.json pkg/calc.py pkg/fmt.py
pkg/calc.py: lines 11/11 arcs 4/4 missing=[]
pkg/fmt.py: lines 3/4 arcs 1/2 missing=[4]
tests=5 coverage-redundant=2 cover=4
  coverage-redundant: tests/test_calc.py::test_premium
  coverage-redundant: tests/test_calc.py::test_premium_again
covering set: ['tests/test_calc.py::test_bad_discount', 'tests/test_calc.py::test_premium', 'tests/test_calc.py::test_label_neg', 'tests/test_calc.py::test_bulk']
wrote scratch/baseline.json
```

```
$ jq -r '.per_test | to_entries[] | "\(.key): \(.value.unique)"' scratch/baseline.json
tests/test_calc.py::test_bad_discount: ["pkg/calc.py:4->7","pkg/calc.py:7->8","pkg/calc.py:9->10 (exc)","pkg/calc.py:10->11","pkg/calc.py:11->-1","pkg/calc.py:7","pkg/calc.py:10","pkg/calc.py:11"]
tests/test_calc.py::test_bulk: ["pkg/calc.py:4->5","pkg/calc.py:5->8","pkg/calc.py:5"]
tests/test_calc.py::test_label_neg: ["pkg/fmt.py:-1->2 (exc)","pkg/fmt.py:2->3","pkg/fmt.py:3->-1","pkg/fmt.py:2","pkg/fmt.py:3"]
tests/test_calc.py::test_premium: []
tests/test_calc.py::test_premium_again: []
```

## Reading the map

Four things the fixture output shows, each of which the worked example hit at scale:

- **Leave-one-out is not a licence.** `test_premium` and `test_premium_again` both have an
  empty unique set — each is redundant *given the other*. Drop both on that reading and the
  `premium` arm loses its coverage. The covering set keeps exactly one of them. That is why the
  script computes a cover instead of stopping at per-test uniqueness: the cover is the floor
  (4 of 5 here; 11 of 61 in the worked example), and everything above the floor must justify
  itself on assertion strength, which coverage cannot see.
- **`(exc)` marks an arc coverage's static model does not list.** `pkg/calc.py:9->10 (exc)` is
  the jump into the `except` handler. Filtering executed arcs against `arc_possibilities` would
  silently drop it and make `test_bad_discount` — the only error-path test — look redundant.
  The script keeps such arcs and tags them. A function's **entry** arc from a negative line
  (`pkg/fmt.py:-1->2 (exc)`) carries the same tag; it is an entry, not an exception — read the
  tag as "not in the static arc set", nothing more.
- **`(fixture)` marks an item a test reaches only in its setup or teardown phase.** pytest-cov
  records each test in three contexts; the script merges them under the node id, so a test whose
  unique coverage comes from its fixture is not called redundant. See the traps.
- **`missing` distinguishes a hole from a scoping artifact.** `pkg/fmt.py` line 4 (the `"pos"`
  return) is uncovered because no test in the set reaches it. Before calling that a hole, check
  whether a test file *outside* the set owns it. The script only lists them; classifying each
  missing line or arc as a hole or a scoping artifact is the runner agent's deliverable.

Coverage-redundant is **not** assertion-redundant. `test_premium` and `test_premium_again` happen
to assert the same value; had one asserted `== 40` and the other `== 41`, one of them would be
the only test that fails when the multiplier is wrong, and the map would look identical. The
delete needs the fact matrix's agreement.

## Verify the covering set

The greedy cover is computed, not proven. Run only the chosen tests with the same `.coveragerc`
and compare the result with the baseline by identity:

```
$ rm -f scratch/.coverage
$ pytest -p no:cacheprovider -q --cov --cov-config=scratch/.coveragerc --cov-context=test --cov-report= \
    tests/test_calc.py::test_bad_discount tests/test_calc.py::test_premium \
    tests/test_calc.py::test_label_neg tests/test_calc.py::test_bulk
$ python3 scripts/coverage_map.py --scratch scratch --out scratch/cover.json pkg/calc.py pkg/fmt.py
pkg/calc.py: lines 11/11 arcs 4/4 missing=[]
pkg/fmt.py: lines 3/4 arcs 1/2 missing=[4]
tests=4 coverage-redundant=0 cover=4
covering set: ['tests/test_calc.py::test_bad_discount', 'tests/test_calc.py::test_premium', 'tests/test_calc.py::test_label_neg', 'tests/test_calc.py::test_bulk']
wrote scratch/cover.json
$ python3 scripts/coverage_map.py --diff scratch/baseline.json scratch/cover.json
pkg/calc.py: 27 -> 27 covered items, lost 0, gained 0
pkg/fmt.py: 8 -> 8 covered items, lost 0, gained 0
nothing the baseline covered was lost
```

Exit 0: the four tests cover every line and arc the five did, item for item. In the worked
example the 11-test cover reproduced all 514 items.

## After the cut

Run the instrumented command again against the reduced files, write the map under a new name, and
diff it against the baseline. The diff compares covered lines and arcs by name, because equal
counts can hide a lost arc behind a gained one. Deleting `test_bad_discount` from the fixture:

```
$ python3 scripts/coverage_map.py --diff scratch/baseline.json scratch/after.json
pkg/calc.py: 27 -> 19 covered items, lost 8, gained 0
  lost: pkg/calc.py:4->7
  lost: pkg/calc.py:7->8
  lost: pkg/calc.py:9->10 (exc)
  lost: pkg/calc.py:10->11
  lost: pkg/calc.py:11->-1
  lost: pkg/calc.py:7
  lost: pkg/calc.py:10
  lost: pkg/calc.py:11
pkg/fmt.py: 8 -> 8 covered items, lost 0, gained 0
LOST 8 covered items; find the deleted tests that owned them in the baseline's per_test table
```

Exit 0 means nothing was lost; exit 1 lists each lost item, as above; exit 2 means the two maps
cannot be compared — a production module's source, the `--range` scopes or the coverage version
differ — and names what differs. A lost item belongs to a deleted test: find it in the
baseline's `per_test` table and restore its assertion somewhere. Record in the commit message
that coverage was re-measured.

## Traps that produce a wrong map

Each of these yields a confident, wrong map. The first six were hit on the real cut; the last
three were reproduced with pytest-cov afterwards.

- **Coverage does not model exception edges statically.** Filtering executed arcs against
  `arc_possibilities` silently drops the arcs into an `except` handler and makes every error-path
  test look redundant. Keep exception arcs; tag them.
- **`CoverageData.lines()` returns raw traced lines** including signature and continuation lines.
  Intersect with the analysis's `statements` or counts inflate (347 versus a true 226 in the
  worked example).
- **`--cov` bare plus `--cov-config=<rcfile>` activates the rcfile's `include` filter;
  `--cov=<pkg>` sets `source` and makes `include` inert.** Use the bare form with the scratch
  rcfile.
- **Put the rcfile and data file outside the repo**, so the project's own coverage configuration
  is bypassed and nothing lands in the working tree.
- **Serial only.** Worker splitting (`-n`) scatters contexts. `--cov-context=test` conflicts with
  `dynamic_context` in the rcfile; set one, not both.
- **`subTest` iterations fold into the parent test's context.** A sweep with 300 subtests is one
  context, and its unique set is the union of all of them.
- **pytest-cov records every test in three contexts: `nodeid|setup`, `nodeid|run` and
  `nodeid|teardown`.** Counted separately, a test whose body adds nothing but whose fixture is
  the only code reaching a branch looks coverage-redundant. On the fixture, `test_lookup_memory`
  is that test: its `run` phase reaches nothing unique, yet deleting it loses lines 3, 8, 9 and 10
  of `pkg/store.py`. The script merges the phases and tags fixture-only items:

  ```
  $ python3 scripts/coverage_map.py --scratch scratch pkg/store.py
  pkg/store.py: lines 10/10 arcs 3/4 missing=[]
  tests=2 coverage-redundant=0 cover=2
    unique through a fixture: tests/test_store.py::test_lookup_memory (10 items)
  covering set: ['tests/test_store.py::test_lookup_memory', 'tests/test_store.py::test_lookup_remote']
  wrote scratch/analysis.json
  ```

  A module- or session-scoped fixture runs in the setup of the first test that requests it, so
  its items look unique to that test. Deleting the test moves them to the next requester rather
  than losing them; re-run and let `--diff` decide.
- **Branch coverage cannot see outcomes inside a line.** A zero-iteration `for` loop, the operand
  that decides an `and`/`or`, a ternary arm, a comprehension's `if`, a lambda body and a match
  guard all fall on lines another test already reaches. A test that is the *only* one exercising
  such an outcome still has an empty unique set:

  ```
  $ python3 scripts/coverage_map.py --scratch scratch pkg/loops.py
  pkg/loops.py: lines 7/7 arcs 2/2 missing=[]
  tests=4 coverage-redundant=3 cover=2
    coverage-redundant: tests/test_loops.py::test_pick_default  (not seen by coverage: pkg/loops.py:9 or)
    coverage-redundant: tests/test_loops.py::test_pick_set  (not seen by coverage: pkg/loops.py:9 or)
    coverage-redundant: tests/test_loops.py::test_total_zero  (not seen by coverage: pkg/loops.py:3 for)
  covering set: ['tests/test_loops.py::test_total_many', 'tests/test_loops.py::test_pick_default']
  wrote scratch/analysis.json
  ```

  `test_total_zero` is the only test of `total([]) == 0`, yet neither its unique set nor the
  covering set keeps it. The script lists each such site per test under `subline`. Before deleting a test that
  reaches one, name the surviving test in the fact matrix that pins that outcome, or write the
  site's mutant (`a or b` → `a`, drop the comprehension's `if`, swap the ternary arms, return a
  wrong value on empty input) and watch the reduced suite fail on it.
- **Coverage contexts are process-wide.** Work a test hands to a thread, pool or subprocess is
  recorded under whichever test is running when it executes, or not at all. On a timer thread,
  the test that started the work had no context and the next test was credited with it. A test
  whose only measured work runs elsewhere is missing from `per_test` entirely: compare the count
  with `pytest --collect-only -q`, and keep tests that start background work out of any
  coverage-only argument.

## Mutant check for a relocated fact

A fact moved to a cheaper layer is proven, not assumed. Write the new assertion, run it green,
then break production the way the fact forbids and watch the new assertion fail:

```bash
# 1. write the new assertion in the cheaper test; run it green
# 2. break production the way the fact forbids, e.g. with a scripted edit
python - <<'MUTANT'
p = "pkg/module.py"
s = open(p).read()
old = "    scalars = compute_scalars(record, days)\n"
new = "    scalars = derive_from(lifted_by_category)\n"
assert s.count(old) == 1
open(p, "w").write(s.replace(old, new))
MUTANT
# 3. run the one test; it must fail on the new assertion
pytest -q tests/test_pure.py -k the_new_test
# 4. restore production and confirm the tree is clean
git checkout -- pkg/module.py && git diff --stat -- pkg/
```

Pick the fixture so the mutant is visible. A fixture whose value the mutant happens to leave
unchanged — an exemption, a coincidence of defaults — proves nothing. The first attempt in the
worked example had exactly that flaw: the moved fact was "the eligibility lift never reaches the
non-category scalars", the mutant derived the scalars from the lifted per-category mapping, and
the first fixture's thirteen-month exemption kept the two values equal, so the sharpened
assertion passed on the mutant. A fixture with a distinct value made it fail.
