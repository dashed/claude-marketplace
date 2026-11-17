# Changelog - test-audit

All notable changes to the test-audit skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.1.0] - 2026-11-17

### Added
- New pattern group **Pins the past**: a tombstone asserts that removed code stays removed, so no change to the live code can fail it. The retention bar keeps a deliberate guard against bringing back something removed on purpose (a banned dependency, an insecure endpoint, a public API removed in a major release), and a guard that applies only for a while fails with "delete this test" when its condition ends. An absence assertion is a candidate, not a finding: on the 33,619-test Django application, 14 of the 15 absence assertions pinned live behavior, and the fifteenth guarded a banned dependency. The history decides
- Pattern: a test that only exercises a dependency (it passes for any implementation of your code), with an `isinstance` check on a type-checked return value as a special case, and a retention exception for your configuration of the dependency or a dependency behavior you rely on
- Pattern: an expected value that repeats the production formula or reads the production constant, so a wrong rate moves both sides of the comparison. A computed expected value is kept only when it is independent: a reference implementation, an inverse, or a property
- Pattern: private state read from outside the class, with ruff `SLF001` as a fourth discovery pass. It is a triage list: 320 sites in the test suites of requests `3c7baaa`, httpx `7cff5f7`, attrs `2a1fb86`, flask `49943b5`, rich `3a109cc` and click `08b803c`, and 1,467 on the Django application, of which 121 were Django's `_meta`. The documented command ignores `_meta` and werkzeug's `_get_current_object`
- Runnable examples for the dependency-only, formula-copy and private-state patterns in `references/patterns.md`; the repository test suite runs them both ways, and its ruff check now asserts that `SLF001` finds exactly the private-state weak test
- Credit to the `prune-tests` skill in caldoai/skills (MIT), which prompted the three new patterns

### Changed
- The description names the new patterns and triggers on requests to prune tests

## [1.0.0] - 2026-09-28

### Added
- Initial addition to marketplace, adapted from the OpenClaw `test-audit` skill (MIT): one value bar for tests in three modes — an authoring gate for every new or changed test, a focused audit, and a whole-subsystem campaign
- The authoring gate: four questions (what the test protects, which regression fails it, why existing coverage misses that, whether it needs production code no production caller needs), a refactor check for implementation-coupled tests, and a recipe that proves a regression test fails on the pre-fix code for the intended reason
- The owner-boundary rule, reconciled with test-sloc-cut's cheapest-layer ownership: the cheapest test that drives the real production path, never a mock that implements the asserted behavior
- Low-value patterns grouped by what the test pins — nothing, its own inputs, implementation, one thing twice, less than it claims — and the finding that a duplicate test body usually hides a missing test (httpx and flask cases)
- Retention bar, evidence ledger with `R`/`F`/`C`/`D` marks (history, non-test callers, owner proof, unlocked deletions), test-only seam removal, edit shape, pytest validation steps, and the handoff report; `C` hands off to test-sloc-cut's fact matrix and coverage diff
- `scripts/scan_smells.py` (stdlib): per-test `no-assert`, `self-compare`, `repeat-call`, `dup-body` and `reads-source` findings for pytest and unittest files, with `--assert-helper` for assertion helpers defined in other files. Patterns that ruff already reports (PT011, PT012, PT017, B015, F631, PLR0124) are left to ruff and documented as the companion command
- `scripts/find_seams.py` (stdlib): production symbols that only tests refer to, matched by name across any number of `--src` codebases, with `decorated`, `override`, `string`, `exported` and `private` tags and untagged candidates ranked first
- `references/patterns.md`: each pattern with a runnable weak test and fix; the repository test suite runs every example against a working and a broken implementation, and checks that the scanner and ruff find the weak ones
- `references/campaign.md`: lanes, per-lane ledgers, layer plans with keeper suites, cutover, preservation review with mutations (using test-sloc-cut's `--diff` and `compare`), product defects with control runs, and reconciliation
- Detectors measured on six open-source suites (requests, httpx, attrs, flask, rich, click) and a 33,619-test Django application: `dup-body` hits were all real duplicates, several of them copies that never got their distinguishing input; counting delegation to another test as an assertion and four `--assert-helper` patterns cut `no-assert` from 906 to 191; decorator and override tags and a consumer repository under `--src` removed the seam finder's framework-reached and cross-repository false positives
- `tests/test_test_audit.py` and `make test-test-audit` (Ruff, ty, pytest)
