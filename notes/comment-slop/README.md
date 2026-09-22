# Optional Jev comment review, 2026-09-22

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
