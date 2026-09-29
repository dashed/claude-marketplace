# Changelog - test-audit

All notable changes to the test-audit skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
