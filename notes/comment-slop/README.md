# Optional Jev comment review, 2026-09-22

For the subsequent fix to the seven remaining weaknesses and fresh validation,
see [rubric 1.2.0 results](jev-weakness-fix-2026-09-22.md).

The `comment-slop` skill now asks Jev about redundancy and concrete reductions
while preserving its source-based cleanup workflow. The general `jev` skill owns
provider configuration and credentials. The comment adapter supplies its rubric
and source-anchored evidence; neither adapter nor evaluator edits or executes it.
No helper or provider key means skipped, with no setup detour.

## Design and frozen evaluation

An independent agent wrote 16 synthetic cases and 32 expectations, frozen in
commit `f70c270` before live evaluation. The fixture hash is
`d85913c6d94de354caf6e7af1fd2d80a8a1384819425e0d6c7125041d4c0615d`.
Cases cover pure narration, duplicate signatures, rationale/races/invariants,
mixed docstrings, published docs, runtime `__doc__`, doctests, tool directives,
missing context, stale return contracts, and paired useful/harmful reductions.

Five proposed replacements parse and preserve Python's executable AST after
excluding leading docstrings. Two intentionally lose necessary information.
That distinction tests whether Jev can detect harm invisible to this structural
check. AST equality does not prove docs, tooling, or runtime preservation.

The [initial design consultation](jev-design-review-2026-09-22.json) selected
loss of documentation/runtime consumers as the principal risk and supported
checking actual replacements separately. Jev's advice was checked against the
skill and fixtures; it did not supply the expected labels or authorize edits.

## First run and the input-design correction

The first run passed 23/32 expectations. Dispositions matched 14/16 labels:
both obvious deletes and all protected-consumer cases were correct; two mixed
tuple docstrings were conservatively kept instead of reduced. Both harmful
reductions were rejected (preservation probabilities 0.05 and 0.13). Several
safe-reduction and information-loss judgments missed the frozen probability
limits. [Full initial evidence](jev-first-eval-2026-09-22.json).

The first input design exposed a correctness issue: candidate and proposal
questions shared the full state. The same original tuple docstring received
information-loss probabilities 0.89 versus 0.60 depending only on its proposed
replacement; the same ordering comment received 0.80 versus 0.56. Instructions
to ignore the proposal did not remove this influence.

The adapter now sends original-candidate questions without the proposal, then
uses a separate focused request for replacement preservation. This makes the
candidate payload independent of proposed edits by construction. Reports retain
each call; answers are combined only when both succeed. A second-call failure
keeps the first evidence but marks the combined review incomplete. No successful
answer is repeatedly sampled to find a pass. The
[Jev input-design consultation](jev-input-design-2026-09-22.json) also selected
this separation; tests verify the actual request boundary.

## Final rubric and results

Separation alone passed 21/32 expectations and kept four mixed blocks that the
labels expected to reduce. That run is [retained separately](jev-split-eval-2026-09-22.json).
Rubric 1.1.0 clarifies two definitions: a useful clause does not earn a redundant
neighbor its place, and a safe reduction need not retain literal statements
already evident to the intended reader. The known cases therefore became
regression cases for this revision, not untouched held-out evidence. No fixture
or threshold changed.

The final run passes **25/32 expectations**:

| Check group | Passed | Total |
|---|---:|---:|
| Original-comment disposition | 14 | 16 |
| Information lost by full deletion | 6 | 11 |
| Concrete replacement preserves useful content | 5 | 5 |

Both harmful reductions fail preservation as intended, and all three safe
reductions pass. This is the strongest result for using Jev on actual proposed
edits. All protected documentation/runtime/tooling cases are kept. Two mixed
tuple docstrings are still conservatively kept rather than reduced; five
information-loss probabilities remain below the declared 0.70 expectation.
These seven failures are visible in the runner's exit 1 and
[complete final report](jev-final-eval-2026-09-22.json).

The final reports use adapter schema 2, rubric 1.1.0, and 21 provider calls for
16 candidates plus five proposals. The question/state hashes and per-call
responses are retained; provider aliases and probabilities may change over time.
All five proposal syntax/AST checks still pass, including both semantically
harmful proposals. No scores were rewritten, capped, or selected by retry.

## Independent end-to-end exercise

A separate reviewer selected three new synthetic examples and recorded its
[decisions before consulting Jev](forward-test/pre-review-decisions.json): delete
visible narration, reduce an API docstring, and keep runtime usage text. Jev
agreed with all three; the API reduction was uncertain (reduce 0.58, keep 0.40).
No decision changed, so this exercise does not establish incremental benefit.

The reviewer applied the cleanup to a temporary module. Its
[before](forward-test/before.py.txt) and [after](forward-test/after.py.txt) retain
the bounds/polarity contract and executable example in
[generated documentation](forward-test/api-reference.md), preserve the runtime
usage string, pass one doctest before and after, and match four behavior examples.
[Verification](forward-test/verification.json) records those consumer checks.
The three live reports used the original schema 1; they are independent workflow
evidence, not extra passes for the revised rubric. The reviewer separately
[verified the schema 2 request boundary](forward-test/split-boundary-verification.json)
without more network calls.

## Implementation checks

`make test-comment-slop` passes 70 offline tests plus Ruff lint/format and ty,
all through uv. The transport remains covered by the general Jev helper's
existing tests. Strict repository validation passes. Review found and corrected
an outer evaluator timeout that needed to cover both optional calls; the wrapper
now has 110 seconds, above their combined local budgets. There is no automatic
retry and no change to user credentials or the dependency lockfile.

## Reproduce and interpret

```sh
make test-comment-slop
make eval-comment-slop EVAL_ARGS=--offline
make eval-comment-slop
```

The offline run validates exact candidate anchors and proposed Python structure,
with all 32 semantic expectations skipped. [Offline evidence](jev-offline-eval-2026-09-22.json).
Live runs use Vercel by default and the general Jev provider configuration.
Exit 1 retains failed semantic or structural expectations; exit 2 is incomplete.
No result is an automatic deletion command.

These small synthetic cases are regression evidence. They do not measure real
repository cleanup accuracy, prove AI authorship, or calibrate a universal
deletion threshold. The agent must inspect the facts, preserve known consumer
requirements, and run the relevant docs/doctest/help/tooling checks for edits.
