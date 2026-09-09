# Changelog - test-sloc-cut

All notable changes to the test-sloc-cut skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
