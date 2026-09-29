# Test-pruning campaign

Campaign mode prunes the whole test surface of one subsystem in one pull request: a plugin, an
integration, or one core area. The value bar, retention bar, evidence ledger and validation in
[SKILL.md](../SKILL.md) apply to every lane. This file adds the order of work and the lessons
of a full campaign. Each step ends on its completion criterion; do not start the next step
early.

## Table of contents

- [1. Baseline](#1-baseline)
- [2. Lanes](#2-lanes)
- [3. A read-only ledger per lane](#3-a-read-only-ledger-per-lane)
- [4. A layer plan per lane](#4-a-layer-plan-per-lane)
- [5. Cutover](#5-cutover)
- [6. Preservation review](#6-preservation-review)
- [7. Product defects](#7-product-defects)
- [8. Reconcile and hand off](#8-reconcile-and-hand-off)

## 1. Baseline

Pin the main-branch commit. Record the subsystem's test and test-support line counts, counted
with test-sloc-cut's `count_code_lines.py`, and the pass or fail state of every test file:

```bash
pytest tests/<subsystem> -rA --junitxml=scratch/baseline.xml   # per-test outcomes
```

Keep baseline failures in a list of their own. In the campaign this mode comes from, all three
baseline failures were real delivery bugs, not stale tests.

Done when every in-scope test file has a recorded baseline result.

## 2. Lanes

Split the surface into **lanes** along production owner boundaries, not file-name prefixes —
for a messaging integration: accounts, commands, inbound, outbound, persistence, transport,
shared helpers, the test harness, and live or QA scenarios. Include the subsystem's cases at
shared core boundaries and its QA and live-proof harness tests.

Done when every test file and QA scenario the subsystem owns belongs to exactly one lane.

## 3. A read-only ledger per lane

Give each lane to its own read-only agent. Only one agent at a time may run tests against a
shared database. The agent reads every assigned test in full, including parametrize tables and
fixtures, and reads the production owners: entry points, callers, history and CI routing. Each
test declaration goes into the lane's ledger with one mark and one evidence line:

- `R` retain — name the contract and the bug it catches. A retained test that only moves to a
  better-named file stays `R`, with the move noted.
- `F` retain the contract, repair the assertion — for example a negative check that passes when
  only one of several items is missing, or a copy that never got its distinguishing input.
- `C` consolidate — name the owner that absorbs the assertion first: a row in a sibling table,
  a stronger boundary suite, or the shared owner in another package.
- `D` delete — name the proof that remains, or why no contract exists.

A `@pytest.mark.parametrize` test is one declaration unless its rows need different marks;
then mark each row by its id. Judge a test by its assertions, not its name: one test named for
retiring a progress window asserted that the window was *not* cleared.

For each `C`, record the lane's fact matrix and per-test coverage with test-sloc-cut's
`fact_matrix.py seed` and `coverage_map.py`, so step 6 has a baseline to compare against.

Done when every declaration in the lane has a mark and an evidence line.

## 4. A layer plan per lane

Treat the per-test ledger as input, not as the edit list. A second read-only pass, starting
from the ledger, looks for the redundant **layer**. In the source campaign, several dispatch
suites replayed one shared compositor through a mocked preview, around stronger suites that
ran the real stream against HTTP fixtures. Name the **keeper** suite for each contract, and
prefer the real transport boundary with a fake network to a mocked collaborator. Correct any
ledger errors this pass finds.

Done when each lane plan names its retired files, its keeper per contract, the assertions to
carry into keepers, and the test-only production seams it unlocks (`find_seams.py` limited to
the lane's production paths).

## 5. Cutover

Edit lane by lane. Route every change to a shared harness, `conftest.py` or support module
through one owner, one at a time. With each lane, remove the test-only production seams it
unlocks: injection parameters, getters, reset functions and indirection layers. Register moved
suites in CI routing and test inventories, and update any shrink-only line-count baselines.
Write durable test-ownership rules into the subsystem's agent instructions (`AGENTS.md`,
`CLAUDE.md`), drawn only from mistakes this campaign actually found.

Done when every lane plan is applied and each lane's keepers pass.

## 6. Preservation review

Before you claim completion, have independent reviewers compare the deleted coverage with the
keepers, one reviewer per boundary group. They look for contracts that lost their only proof,
and for new assertions that cannot fail, such as a rejection row that the production code
never reaches. In the source campaign this review found nine real gaps and one unreachable
assertion.

The mechanical half comes from test-sloc-cut: `coverage_map.py --diff` lists lost lines and
arcs by name, `fact_matrix.py compare` lists lost or weakened facts, and
`fact_matrix.py check --coverage` flags a fact whose asserting test never runs its production
lines. The review still reads the code: the tools cannot tell a `D` whose contract was worthless
from one whose contract was lost.

For each restored contract, make one deliberate **mutation** of the production owner and
confirm that the keeper goes red. Then restore the source byte for byte (`git diff` empty for
that file).

Done when every reported gap is restored or rejected with source evidence, and every restored
contract has a caught mutation.

## 7. Product defects

A baseline failure that survives into a keeper is a bug report. Fix it at its owner in a
separate commit, and prove it through the real user flow with a **control** run: revert the
fix, show the old behavior, then show the fixed behavior on the same harness. Record unrelated
product discrepancies you find as follow-ups instead of fixing them in the campaign.

Done when each repaired defect has a failing control and a passing candidate on the same
harness.

## 8. Reconcile and hand off

A campaign outlives many main-branch commits. Merge the main branch rather than rebasing a
long campaign of many commits. When the main branch changed a file that the campaign deleted,
keep the deletion, port the new contract into the keeper, and confirm that every new
regression test from the main branch still has a home. Rerun the whole subsystem suite, and
repeat the live proof on the merged head.

Expect review tooling to see a truncated file list on a diff this large. Record maintainer
decisions about generic compatibility flags in the pull request evidence instead of editing
the gates.

Hand off with the SKILL.md report, plus:

- baseline and final test and test-support line counts, with production counted separately;
- lanes, retired layers, and keepers;
- preservation gaps found, and the mutation that proved each restored one;
- product defects, with control and candidate proof.
