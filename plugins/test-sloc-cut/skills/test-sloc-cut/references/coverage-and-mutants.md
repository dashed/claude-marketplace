# Coverage map and mutant check

The runner's half of the method: how to measure which lines and arcs each test uniquely
reaches, how to get a covering set you can trust, the traps that produce a wrong map, and how to
prove a relocated fact with a mutant.

**Provenance.** Every command and output block below was run on a five-test fixture with
pytest 9.1.1, pytest-cov 7.1.0, coverage 7.16.0 (Python 3.13.11, resolved by `uvx`). The
numbers from the worked example (61 tests, 514 items, an 11-test cover) are quoted from that
cut, not re-run here.

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
```

`MODULE` is the repo-relative path as recorded in the data file (`relative_files = True`). Run it
with an interpreter that can import the `coverage` that wrote the data file — the test
environment's, or `uvx --with coverage python3 …`. It writes `DIR/analysis.json` with three
sections: `modules` (statements, covered, missing lines, branch arcs, arcs taken), `per_test`
(item count and the lines/arcs no other test reaches), and `cover` (a greedy minimum covering set
over what only tests supply). `--range pkg/big.py=558-689` scopes a large module to the
functions under test. Save the baseline run's output under its own name before the cut
(`--out scratch/baseline.json`); the after-the-cut comparison diffs against it.

On the fixture — a `price()` with two `elif` arms and a `try/except`, a `label()` with one
branch, and five tests of which two are byte-identical in effect:

```
$ python3 scripts/coverage_map.py --scratch scratch pkg/calc.py pkg/fmt.py
pkg/calc.py: lines 11/11 arcs 6/6 missing=[]
pkg/fmt.py: lines 3/4 arcs 1/2 missing=[4]
tests=5 coverage-redundant=2 cover=4
  coverage-redundant: tests/test_calc.py::test_premium_again|run
  coverage-redundant: tests/test_calc.py::test_premium|run
covering set: ['tests/test_calc.py::test_bad_discount|run', 'tests/test_calc.py::test_premium_again|run', 'tests/test_calc.py::test_label_neg|run', 'tests/test_calc.py::test_bulk|run']
wrote scratch/analysis.json
```

```
$ jq -r '.per_test | to_entries[] | "\(.key): \(.value.unique)"' scratch/analysis.json
tests/test_calc.py::test_bad_discount|run: ["pkg/calc.py:5->7","pkg/calc.py:7->8","pkg/calc.py:8->9","pkg/calc.py:9->10 (exc)","pkg/calc.py:10->11","pkg/calc.py:11->-1","pkg/calc.py:8","pkg/calc.py:9","pkg/calc.py:10","pkg/calc.py:11"]
tests/test_calc.py::test_bulk|run: ["pkg/calc.py:5->6","pkg/calc.py:6->7","pkg/calc.py:6"]
tests/test_calc.py::test_label_neg|run: ["pkg/fmt.py:-1->2 (exc)","pkg/fmt.py:2->3","pkg/fmt.py:3->-1","pkg/fmt.py:2","pkg/fmt.py:3"]
tests/test_calc.py::test_premium_again|run: []
tests/test_calc.py::test_premium|run: []
```

## Reading the map

Three things the fixture output shows, each of which the worked example hit at scale:

- **Leave-one-out is not a licence.** `test_premium` and `test_premium_again` both have an
  empty unique set — each is redundant *given the other*. Drop both on that reading and the
  `premium` arm loses its coverage. The covering set keeps exactly one of them. That is why the
  script computes a cover instead of stopping at per-test uniqueness: the cover is the floor
  (4 of 5 here; 11 of 61 in the worked example), and everything above the floor must justify
  itself on assertion strength, which coverage cannot see.
- **`(exc)` marks an arc coverage's static model does not list.** `pkg/calc.py:9->10 (exc)` is
  the jump into the `except` handler. Filtering executed arcs against `arc_possibilities` would
  silently drop it and make `test_bad_discount` — the only error-path test — look redundant.
  The script keeps such arcs and tags them. Measured on 7.16.0, a function's **entry** arc from a
  negative line (`pkg/fmt.py:-1->2 (exc)`) carries the same tag; it is an entry, not an
  exception — read the tag as "not in the static arc set", nothing more.
- **`missing` distinguishes a hole from a scoping artifact.** `pkg/fmt.py` line 4 (the `"pos"`
  return) is uncovered because no test in the set reaches it. Before calling that a hole, check
  whether a test file *outside* the set owns it. The script only lists them; classifying each
  missing line or arc as a hole or a scoping artifact is the runner agent's deliverable.

Coverage-redundant is **not** assertion-redundant. `test_premium` and `test_premium_again` happen
to assert the same value; had one asserted `== 20` and the other `== 21`, one of them would be
the only test that fails when the multiplier is wrong, and the map would look identical. The
delete needs the fact matrix's agreement.

## Verify the covering set

The greedy cover is computed, not proven. Run only the chosen tests with the same `.coveragerc`
and compare the item union to the baseline:

```
$ rm -f scratch/.coverage
$ pytest -p no:cacheprovider -q --cov --cov-config=scratch/.coveragerc --cov-context=test --cov-report= \
    tests/test_calc.py::test_bad_discount tests/test_calc.py::test_premium_again \
    tests/test_calc.py::test_label_neg tests/test_calc.py::test_bulk
4 passed in 0.02s
$ python3 scripts/coverage_map.py --scratch scratch --out scratch/after.json pkg/calc.py pkg/fmt.py
pkg/calc.py: lines 11/11 arcs 6/6 missing=[]
pkg/fmt.py: lines 3/4 arcs 1/2 missing=[4]
$ jq '.cover.union_items' scratch/analysis.json scratch/after.json
35
35
```

Identical per-module lines, arcs and missing lists, and the same union — the four tests supply
everything the five did. In the worked example the 11-test cover reproduced all 514 items.

## After the cut

Run the instrumented command again against the reduced files and diff the per-module numbers
against the baseline JSON:

```bash
jq -c '.modules' scratch/baseline.json
jq -c '.modules' scratch/after.json
```

`n_covered` and `n_branch_arcs_taken` must be identical per module. If a module lost an arc, find
the deleted test that owned it in the baseline's `per_test` table and restore its assertion
somewhere. Record in the commit message that coverage was re-measured.

## Traps that produce a wrong map

Each of these was hit on the real cut; each yields a confident, wrong map.

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
