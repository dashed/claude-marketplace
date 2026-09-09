# The investigation: four angles, one test runner

The four reports that feed synthesis, what each must deliver, and the brief that produces it.
Spawn all four at once. Three are read-only; exactly one runs tests, because a shared test
database does not tolerate concurrent runs. Each writes a markdown report to a scratch directory
outside the repo.

## Table of contents

- [What every brief shares](#what-every-brief-shares)
- [Fact matrix](#fact-matrix)
- [Helper and arrangement economics](#helper-and-arrangement-economics)
- [Comment audit](#comment-audit)
- [Per-test branch coverage (the runner)](#per-test-branch-coverage-the-runner)
- [Reading the four reports together](#reading-the-four-reports-together)

## What every brief shares

Repo root and commit; the file list under review; the production modules those files drive;
the scratch path for the report; "read-only, no git or jj writes, do not post anywhere"; and,
for the three non-runners, "do not run tests; another agent owns test runs." Keep the rest of the
prompt to the deliverable's shape and the constraints below. A lean brief produces a report that
is easy to dedupe against the other three.

## Fact matrix

For every test, one row: file, name, the production function or branch it drives, and the facts
it asserts stated as short propositions with stable ids
(`F12: an override for an unpublished category creates no entry`). Then:

- **Facts owned outside the files under review.** Look one layer down. In the worked example a
  package-layer parity test already pinned, by exact list comparison, every value the resolver
  tests were re-asserting about real packages. Every "package X publishes value Y" assertion in
  the four files was a duplicate.
- **Cross-file duplicates**, with an owner per fact. Ownership rule: the cheapest layer that can
  prove the fact wins (pure over DB, DB over end-to-end), *except* facts about wiring,
  persistence, metric emission, or legacy behaviour, which only the layer that exercises them
  can prove.
- **Strict subsets**: tests every fact of which is asserted by another test on the same path.
  Check each against the mutants it could kill, not by name. The standard of proof: "t2 asserts
  30 == 30 and t3 asserts 90 == 90 on the same branch; a mutant returning the package value
  passes t2 and fails t3, so t2 kills nothing t3 misses."
- **Single-pinned facts**: asserted by exactly one test. This is the do-not-touch set. A test in
  it survives, or its assertion moves before the test goes.
- **Fold proposals** with the resulting assertion list and an honest line estimate each,
  including the ones that only move lines around.

**Brief — deliver:** per-test rows (path driven, facts as propositions with ids); facts owned
outside the files; cross-file duplicates with an owner under the cheapest-layer rule; strict
subsets with the mutant each would or would not kill; single-pinned facts; fold proposals with
assertion lists and line estimates. Verify by reading code paths, not names.

## Helper and arrangement economics

- Inventory every helper, setUp, and module constant with call-site count and lines saved versus
  lines cost. Helpers with 20 call sites are never the problem; a helper with one caller that
  saves nothing is.
- **Parametrization arithmetic.** A parametrized block costs `N + 7` lines (five of scaffold plus
  a def and an assert) against 2 or 3 per replaced test, so break-even is seven two-line tests.
  Width-check every row at its real indent against the line-length limit: rows that need
  shortening devices (aliases, builders, an extra import) pay for those devices too. In the
  worked example the best candidate went 20 to 15 lines and needed 5 lines of devices: net zero,
  minus eight descriptive test names. Refuse line-neutral parametrization.
- **Construction shortcuts.** Check what the protobuf or dataclass constructor already accepts
  (`Message(field=None)` leaves an optional field unset, so a four-line if/else builder is one
  line). Check the shared test utilities and sibling test packages before proposing a new builder.
- **Shared helpers.** Cost the shared surface honestly: lines added centrally plus imports at
  each site, against lines removed. In the example a shared record builder saved three lines net
  across three files on two branches. Below ten lines net, keep helpers local; the house
  convention was local anyway.
- **Repeated wrapped call shapes.** Calls that are one expression but three lines because a long
  method or enum name pushes them over the limit. Two two-line read aliases and three enum
  aliases recovered 28 lines in one file. Adopt an alias everywhere or nowhere; a mixed style
  costs more than it saves.

**Brief — deliver:** helper inventory with call counts and net lines; parametrize candidates with
the table, ids and width check at real indent; construction shortcuts and existing utilities
checked; shared-helper cost/benefit across branches; repeated wrapped call shapes with occurrence
counts. State which proposals only move lines.

## Comment audit

For prose-heavy files. Parity and integration tests carry rationale that pure tests do not.
Audit every comment block with the three-clause test: the comment states a fact that is true at
this layer, not visible in the code in front of the reader, and not stated better nearby.
Verdict per block: keep, trim (give the replacement text), or delete. The `comment-slop` skill is
the method for the audit itself; this angle adds two outputs:

- **Accuracy defects.** A comment asserting something the code contradicts is a rewrite or a
  delete, never a keep. The example found a module comment claiming "the expected value is
  never written into this file" above five hard-coded 90s; the fix was to import the production
  constant those 90s were, which also made the assertions stronger.
- **Table-driving verdict.** Targeted divergence tests can be table-driven only if their setups
  vary on one axis. When they differ on freeze instant, fixture, mutation kind, and assertion
  shape, a table needs a setup callable and an assert callable per row — which is a harness.
  Recommend zero and say why.

**Brief — deliver:** every comment block with keep/trim/delete and replacement text; whether
targeted tests can be table-driven without losing a named divergence; whether a small file can
fold into a sibling and which of its assertions are already pinned elsewhere; helper call counts;
which sentences of the module comment carry a why nothing else states.

## Per-test branch coverage (the runner)

Run the files under review serially with per-test contexts, then compute each test's unique
contribution and a minimum covering set — commands, the script and the traps are in
[coverage-and-mutants.md](coverage-and-mutants.md). Deliver:

- Baseline per module: statements covered, branch arcs taken, the list of uncovered lines and
  arcs, and whether each is a real hole or a scoping artifact owned by a test file outside the
  set.
- Per test: the lines and arcs no other test reaches. Tests with an empty unique set are
  coverage-redundant. State plainly that this is not assertion-redundant.
- **Leave-one-out is not a licence.** If exactly two tests reach a line, neither is unique, yet
  dropping both loses the line. So also compute a greedy minimum covering set and *verify it by
  running only those tests* and comparing the item set to the baseline. In the example 11 of 61
  tests reproduced all 514 covered items. That is the floor, not a target: the other 50 must
  justify themselves on assertion strength.

**Brief — deliver:** baseline per module with uncovered lines and arcs classified; per-test
unique contribution; the coverage-redundant table; the verified covering set; the exact commands
and artifact paths so the run can be repeated after the cut. Run only the files under review,
serially.

## Reading the four reports together

Read all four before touching a file. Dedupe findings that name the same test or mechanism —
the fact matrix's strict subset and the runner's coverage-redundant row are often the same test
seen from two sides, and it is the *intersection* that licenses a delete. Where they disagree,
the disagreement is the finding: a coverage-redundant test with a single-pinned fact stays, and a
test with unique arcs but no fact of its own is a branch that is exercised without being asserted
— worth an assertion before it is touched **(inferred; the worked example had no such test)**.
Then decide each candidate with the synthesis table in SKILL.md.
