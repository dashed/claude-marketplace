# Changelog - test-sloc-cut

All notable changes to the test-sloc-cut skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.2.0] - 2026-09-22

### Added
- `scripts/fact_matrix.py` makes the fact matrix machine-checkable. `seed` lists every assertion site in the files under review — `assert`, `pytest.raises`/`warns`, `assert*` methods and helpers, and calls to module helpers that assert — each anchored by test, line and exact text. `--from` keeps the mapping of every unchanged assertion when re-seeding after the cut.
- `check` fails on unmapped sites, facts no site asserts, unknown fact ids, drifted anchors, invalid kinds, an `absent` fact without its observation window, subsumption by a weaker kind, and open questions. It refuses (exit 2) a matrix whose test files changed since seeding. With `--coverage` it requires that some test asserting each fact runs the fact's production lines, which catches facts pinned only through a mock. It computes the single-pinned and duplicated-fact tables.
- `compare BASELINE AFTER` fails on any fact lost, weakened to a weaker kind of check, or moved to other tests without a recorded `mutant`, turning the relocated-fact rule into a checked record.
- Fact kinds (`eq`, `contains`, `len`, `truthy`, `raises`, `called_with`, `absent`, `other`), so two tests pin the same fact only when the kind of check matches.

### Changed
- SKILL.md, the fact-matrix brief and the synthesis step now record the matrix with the script, join it with the coverage map before reasoning about deletes, and finish the cut with `compare`.

## [1.1.0] - 2026-09-22

### Fixed
- `coverage_map.py` counted pytest-cov's `setup`, `run` and `teardown` contexts as separate tests. A test whose unique coverage came only from its fixture was listed as coverage-redundant, yet deleting it lost that coverage (reproduced: 10 of 10 lines fell to 6). Phases are now merged under the test's node id, and unique items reached only through a fixture are tagged `(fixture)`.
- The after-the-cut check compared per-module counts, and equal counts can hide a lost arc behind a gained one. `coverage_map.py --diff BASELINE AFTER` now compares covered lines and arcs by name. Exit 0 means nothing was lost, exit 1 lists each lost item, and exit 2 means the two maps cannot be compared because a production module's source, the `--range` scopes or the coverage version differ.

### Added
- Sub-line sites. `per_test.subline` lists the reached lines whose outcomes coverage cannot see: zero-iteration `for` loops, `and`/`or` operands, ternary arms, comprehensions, lambdas and match guards. Each coverage-redundant test prints its sites, and the delete rule now requires a surviving fact owner or a mutant for each one.
- Three traps, nine in total: pytest's per-phase contexts, outcomes inside a line, and process-wide contexts that credit thread, pool or subprocess work to whichever test is running.
- `analysis.json` schema 2, adding `modules.covered_items`, `per_test.phases`, `per_test.lines`, `per_test.subline` and `provenance`.
- `tests/test_test_sloc_cut.py`, which runs real per-test pytest-cov runs on a committed fixture project, and `make test-test-sloc-cut`. Every `coverage_map.py` output block in `references/coverage-and-mutants.md` is now real output from that fixture, and the test fails if a block drifts.

### Changed
- The rule, the two-oracle table, the synthesis table's delete row, the runner's brief and execution step 7 now use the identity diff and name the sub-line blind spot.

## [1.0.0] - 2026-09-08

### Added
- Initial addition to marketplace: the fact-matrix method for shrinking a test suite without losing an asserted fact or a covered branch, developed on a real cut (61 → 46 tests, 757 → 608 code lines, per-module branch coverage identical before and after)
- The one rule (a test may go only if every fact it asserts survives on the same production path and measured branch coverage is unchanged) and the two oracles — a fact matrix read from the code and per-test branch coverage run from the code — with the distinction that coverage-redundant and assertion-redundant are different properties and a delete needs both
- The four-angle investigation (fact matrix, helper and arrangement economics, comment audit, per-test coverage runner) with a brief skeleton for each; exactly one agent runs tests
- The synthesis table (delete / fold / move to a cheaper layer / parametrize / shared helper / width alias / trim a comment, each with take-when and refuse-when) and the two rules that override it: a relocated fact is proven by a mutant, and boundary pairs stay as two named tests
- Parametrization arithmetic (`N + 7` lines against 2–3 per test; break-even at seven; width-check every row at its real indent; refuse line-neutral), the ten-lines-net rule for shared helpers, and everywhere-or-nowhere for width aliases
- `scripts/count_code_lines.py` (tokenizer-based total / code / comment-only / test counts, docstrings counted as code) and `scripts/coverage_map.py` (per-test unique lines and arcs, exception arcs tagged, greedy minimum covering set) — verified end to end on a fixture with pytest 9.1.1, pytest-cov 7.1.0, coverage 7.16.0
- `references/coverage-and-mutants.md` with the `.coveragerc`, the serial per-test-context pytest command, the six traps that produce a wrong map (exception arcs dropped by static filtering, raw traced lines inflating counts, bare `--cov` vs `--cov=<pkg>`, rcfile placement, worker splitting, `subTest` folding), covering-set verification, the after-the-cut comparison, and the mutant check for a relocated fact
- `references/investigation.md` (the four angles in full and their briefs) and `references/worked-example.md` (what each oracle found, what was done, what was refused, the process defects)
- Execution on stacked branches: base first, lint with explicit paths (an unquoted zsh `$files` is not word-split and let three over-width lines through), mutant-check every relocated fact, re-measure coverage and compare per module
