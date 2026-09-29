---
name: test-audit
description: "Decide whether a test earns its place, at write time and in audits: an authoring gate for every new or changed test (what it protects, which regression fails it, why existing coverage misses that, whether it needs a test-only seam, and a regression test that fails before the fix); a checklist of low-value patterns — assertion-free tests, expected values computed by the code under test, duplicate bodies that hide a missing test, mocks that implement the asserted behavior, negative controls that pass for the wrong reason, names that promise more than the input exercises; a retention bar; and an evidence ledger before any delete. Use when writing, changing, or reviewing tests; when a reviewer asks whether a test is needed or calls it tautological, redundant, or implementation-coupled; when asked for a regression test; when auditing a suite for junk tests or for production code only tests use; or when planning a subsystem test-pruning campaign. Ships a pytest smell scanner and a test-only-symbol finder."
license: MIT
---

# Test Audit

A test costs maintenance, so it has to earn its place: it protects observable behavior, a credible regression, or a contract that matters on its own. This skill applies that one value bar in three modes:

- **Authoring gate** — every new or changed test, when you write it.
- **Audit** — a focused sweep for tests that pin nothing, pin their own inputs, pin implementation, pin one thing twice, or pin less than they claim, and for the test-only production code they keep alive.
- **Campaign** — prune the whole test surface of one subsystem. Read [references/campaign.md](references/campaign.md) before you start one.

Optimize for confidence, not deletion count.

**Relation to test-sloc-cut.** test-sloc-cut removes duplicate pins of facts worth keeping, and it refuses to lose a fact. This skill decides whether a fact is worth pinning at all. A consolidation (`C` in the [ledger](#evidence-ledger)) goes through test-sloc-cut's fact matrix and coverage diff; a deletion (`D`) goes through the ledger here.

## Authoring gate

Before you add or change a test, answer four questions. A missing answer means: do not add it yet.

1. **What does it protect?** An observable behavior, an invariant, or an independent contract, stated as something a caller or user could notice.
2. **Which regression makes it fail?** A credible change to production code, not a typo in the test.
3. **Why does existing coverage not catch that regression?** Each contract has one owner test at its [owner boundary](#owner-boundary). A test at another layer needs its own risk that the owner cannot reach: wiring, persistence, transport, a lifecycle edge. Prefer a new row in an existing parametrized table, or an existing fixture, to a near-copy of a test.
4. **Does it need production code that no production caller needs** — an export, a flag, a reset hook, an injection parameter, a wrapper? If yes, move the test to the real boundary instead.

Then check the test against the [low-value patterns](#low-value-patterns). A match fails the gate unless the [retention bar](#retention-bar) names the contract that the test alone guards.

**Refactor check.** If a behavior-preserving refactor breaks the test — a private helper renamed, internal calls reordered, two modules merged — the test asserts implementation. Rewrite it at the owner boundary before it lands.

**A regression test must fail before the fix, for the intended reason.** A regression test that never failed proves the mock, not the fix. Keep the new test, put the production files back to the pre-fix revision, run the test, and read the failure: it must be the assertion that names the bug, not an import error, a missing fixture, or a different exception. Then restore the fix.

```bash
git stash push -- src/pkg/billing.py                     # or: git checkout <fix>^ -- src/pkg/billing.py
pytest tests/test_billing.py::test_refund_is_capped -x   # must FAIL on the bug's own assertion
git stash pop                                             # or: git checkout HEAD -- src/pkg/billing.py
```

If the test passes on the pre-fix code, it does not reach the bug: drive the owner boundary the bug went through, or assert the value the bug changed, and do not land it until it fails. One regression test at the owner boundary covers a bug. Do not replay the same scenario at every layer it crosses.

### Owner boundary

The owner of a contract is the cheapest test that drives the real production path of that contract: the public entry point before a private helper; a real collaborator or a fake transport before a mock that implements the asserted behavior; a pure function before a database test before an end-to-end test, as long as each one runs the same real code. Facts about wiring, persistence, metric emission, or legacy behavior belong to the layer that exercises them. test-sloc-cut uses the same ownership rule.

## Low-value patterns

One checklist for both modes: the gate rejects a new test that matches a pattern, and an audit hunts for existing tests that do. [references/patterns.md](references/patterns.md) gives each pattern with a runnable pytest example, the fix, and the detector.

**Pins nothing**
- an assertion-free test: it pins only "does not raise" — keep it only when not raising is the contract, and then name that contract;
- a comparison without `assert`, or an `assert` on a tuple or a constant;
- an expression compared with itself (`assert sub.interval == sub.interval`).

**Pins its own inputs**
- an expected value that the code under test computes (`expected = slug(t); assert slug(t) == expected`);
- a determinism, idempotency or caching check that never pins a value: a function that always returns `""` passes `key(a) == key(a)`;
- a mock that implements the asserted behavior, or one bare `Mock` that stands in for different APIs — `create_autospec` makes the mock reject calls the real API rejects;
- a fixture that supplies the state, ordering or callback the owner should produce, or persistence asserted against a store that the path never writes;
- a copied inventory: a literal list, manifest or `__all__` compared with the production constant — it fails on every legitimate addition and catches nothing else.

**Pins implementation**
- private predicates and call shapes (`assert_called_once_with` on an internal helper) that the real boundary already covers;
- source and string greps (`inspect.getsource`, reading a `.py` file);
- a test whose only job is to keep a test-only export, global, flag or wrapper alive, and production code that only tests call ([test-only seams](#test-only-seams)).

**Pins one thing twice**
- the same contract invoked again with nothing new, a shared helper replayed once per caller, two tests with one body.

**Pins less than it claims**
- a negative control that passes for an unrelated reason: `pytest.raises(ValueError)` satisfied by a different guard or by setup code inside the `with` block, or a denial from a different permission check than the one named;
- a capability test that restates a declared flag instead of exercising what the flag promises;
- a name or fixture that promises more than the input exercises.

**A duplicate body is more often a missing test than a redundant one.** In httpx (`b5addb6`), `test_client_decode_text_using_explicit_encoding` is a copy of the autodetect test and still passes `default_encoding=autodetect`, so the explicit-encoding path it is named for has no test. In flask (`d73fa1c`), `test_teardown_request_handler_debug_mode` never enables debug mode. Read the name before the body, and repair (`F`) before you delete (`D`).

## Discovery

Keep discovery read-only, and report evidence before any edit. Three mechanical passes start it. None of them is a verdict.

```bash
# Patterns ruff cannot see: no-assert, self-compare, repeat-call, dup-body, reads-source.
python3 scripts/scan_smells.py tests/ --assert-helper '^get_(success|error)_response$'

# Patterns ruff can see: broad raises (PT011), setup inside raises (PT012), assertions in
# except (PT017), a comparison without assert (B015), assert on a tuple (F631), a name
# compared with itself (PLR0124).
ruff check --isolated --select PT011,PT012,PT017,B015,F631,PLR0124 tests/

# Production symbols that only tests refer to.
python3 scripts/find_seams.py --src src/pkg ../consumer-repo/pkg --tests tests
```

- **Name your assertion helpers.** `scan_smells.py` sees the helpers and fixtures defined in the same file. A base-class method or an imported helper that asserts — a response helper that checks the status code, a schema validator, a snapshot fixture, a browser wait — stays invisible until you pass it with `--assert-helper`. Rank the calls inside `no-assert` hits and add the helpers you confirm assert. On a 33,619-test Django suite, four such patterns took `no-assert` from 886 hits to 191.
- **`dup-body` is the most precise signal.** It needs the same decorators, arguments and body in one class or module, so every hit is either redundant or a copy that never got its distinguishing input. On the same suite, the 56 hits included a staff-permission test that logs in as a superuser and a "with extra slash" test whose URL has no extra slash.
- **`self-compare` is usually a bug** (a typo for the expected value). **`repeat-call` is usually a deliberate determinism, idempotency or caching test**; check that it also pins a value.
- **`find_seams.py` matches by name.** It misses a seam whose name production uses for anything, and it cannot see a codebase you do not pass under `--src`. `decorated`, `override`, `string` and `exported` tags mean "check how production reaches it"; start from the untagged candidates. A cluster of candidates in one package, all subclasses of one base, is usually a registry that production loads by name.
- **ruff's PT011** flags every `pytest.raises` of a broad type without `match=`. Triage it by asking whether another guard on the path raises the same type.

For a broad scope, split discovery into parallel read-only lanes — core packages, plugins or apps, tooling and scripts, and one cross-cutting pattern sweep. Outside a campaign, prefer a few high-confidence candidates to a large speculative list.

## Value bar

In an audit, an existing test that must change for a behavior-preserving refactor is suspect, not automatically deletable. The gate still rejects a new one.

Before you judge a candidate, read the complete test and its production owner: the entry point, callers, callees, sibling implementations, overlapping tests, CI routing, and the history of both. Read the repository's agent instructions (`AGENTS.md`, `CLAUDE.md`) first. When a test claims behavior of a dependency, read the dependency's source or types.

## Retention bar

Keep a test that alone enforces a public API, protocol, configuration, migration, storage format, security, platform, default, serialization, generated-code, packaging, release or architecture contract. Also keep:

- call ordering, when the order is observable behavior;
- a regression test with a credible failure mode;
- source inspection, when it is the cheapest independent guard: it fails when the contract changes (a user-facing key, a byte, a path, generated code) and survives a rename;
- an assertion-free test whose contract is not raising (a validator that accepts valid input, a handler that must swallow an error, a Hypothesis `@given` property that the code never raises) — mark it `F` so its name or a comment states that contract;
- a retained test that fails on the baseline: treat the failure as a possible product bug, reproduce it, and repair the owner, not the test.

Static or slow is not a reason to delete. A test that looks like implementation may still be the independent contract; prove otherwise before you remove it.

## Evidence ledger

Record every field for a candidate before you edit. A missing field means the candidate is not ready.

| Field | Content |
|---|---|
| test | node id: `tests/test_x.py::TestY::test_z` |
| mark | `R` retain · `F` fix the assertion or the input · `C` consolidate into a named owner · `D` delete |
| detects | the failure it can actually detect; prove a doubtful claim with a mutant |
| owner proof | the stronger owner-boundary test that remains, or why no contract exists |
| seam callers | the non-test callers of the production or support code it drives (`find_seams.py`, `rg -w`) |
| history | why it exists: `git log --follow -S '<test name>' -- <file>`, the commit message, the linked bug |
| unlocks | the production or test-support code the change lets you delete |
| risk and proof | the risk, and the focused command that validates the change |

Judge a test by its assertions, not its name. A `C` candidate goes through test-sloc-cut: the absorbing test asserts every fact of the absorbed one, and the fact matrix and coverage diff pass. A `D` candidate that claims a regression needs a mutant: break production the way the regression would, and watch the owner test go red.

## Test-only seams

A production symbol that only tests use — a `reset_for_tests()`, an injection parameter, a flag, a setter hook, a dead model method, an RPC method with no caller — is maintenance the product pays for the test. Delete it together with the tests that exist only to keep it, instead of leaving an alias. Where a test must observe or replace something, move it to the real boundary: a fake transport, `monkeypatch` on the real dependency, `tmp_path` for the file system, the public API.

Before you delete one, confirm three things: `find_seams.py` found no production reference by name; `rg -w <name>` finds no string, configuration, template or other-repository use; and no framework reaches it through a registering decorator, a base-class call, or subclass registration.

## Edit shape

- Choose one coherent owner-boundary batch per change.
- Delete obsolete test-only exports, globals, wrappers and dead production paths. Do not leave aliases.
- Move retained regressions to their owner. Fold repeated package or dependency assertions into one generic contract test.
- `F` before `D`: fix a weak assertion that guards a real contract — assert the value, add `match=`, use `create_autospec`, give the duplicate its missing input.
- Prefer net-negative production lines. Do not add replacement tests that restate the implementation, and do not turn uncertain candidates into cleanup to raise a deletion count.

## Validation

1. Do not edit source or tests while a watch-mode runner (`ptw`, `pytest-watch`, `--looponfail`) runs in the checkout.
2. Run the owner and sibling tests of every changed file.
3. After you remove a seam, run the type checker and the tests of the whole affected package: an import of the deleted name fails there, not in the file you edited.
4. For a removed source grep or plan assertion, run the script or dry run that owns the real contract.
5. Run the formatter and linter with explicit file paths, then `git diff --check`.
6. Read `git diff --numstat`, and report production and tooling lines apart from test lines.
7. Review the final diff (`/code-review`, or the repository's review gate) before handoff.

Commit, push or open a pull request only when the user authorizes it. Land one coherent batch at a time; after it lands, refresh from the main branch and run read-only discovery again for the next batch.

## Handoff

Report:

- the low-value categories removed, and their root cause;
- production owner simplifications, and the seams removed;
- retained false positives, and why each stays;
- the focused and full proof actually run;
- production versus test line counts;
- pull request and merge state;
- named follow-ups.

## Scripts and references

- `scripts/scan_smells.py` — per-test `no-assert`, `self-compare`, `repeat-call`, `dup-body` and `reads-source` findings for pytest and unittest files; `--assert-helper` names assertion helpers from other files (stdlib).
- `scripts/find_seams.py` — production symbols that only tests refer to, ranked, with reachability tags (stdlib).
- [references/patterns.md](references/patterns.md) — each low-value pattern with a runnable weak test, the fix, and the detector.
- [references/campaign.md](references/campaign.md) — campaign mode: lanes, ledgers, layer plans, preservation review, product defects, reconciliation.

Related skills: `test-sloc-cut` for lossless consolidation, `comment-slop` for the comments in tests, `pytest` for the runner, `ruff` for the lint rules above.

Adapted from the OpenClaw `test-audit` skill (Copyright (c) 2026 OpenClaw Foundation, MIT License), with the pytest detectors, the owner-boundary rule shared with test-sloc-cut, and the evidence from the runs above added here.
