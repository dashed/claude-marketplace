# Comment-review weaknesses: fixes, validation, and remaining limits

Rubric 1.2.0 passes all 32 original expectations, including the seven failures
from 1.1.0. It does not change a fixture, threshold, provider, or raw answer.

## Diagnosis and change

The prior information-loss question mixed two concerns: whether a claim was
true and whether a future reader would retain it after deleting the comment.
The state included observed contracts as reviewer evidence. That evidence is
not automatically replacement documentation in the repository. The revised
question explicitly distinguishes those roles and asks whether **any** useful
fact disappears. It also distinguishes visible mechanisms from their reasons:
grouping writes in a transaction does not explain why atomicity matters.

The prior disposition question sometimes kept a whole private docstring because
its later clauses mattered. The revised instructions make the source-only
policy explicit: a conventional summary repeating a name/signature is still a
redundant clause, while published/runtime audience requirements can justify it.
The replacement-preservation question and separate request contexts remain intact.

The [Jev design consultation](jev-weakness-design-2026-09-22.json) supported a
counterfactual check distinguishing reviewer-only evidence from retained accessible
documentation. That advice informed the fresh validation design; it did not set
the expected labels or establish correctness.

## Original regression

| Check group | Rubric 1.1.0 | Rubric 1.2.0 |
|---|---:|---:|
| Original-comment disposition | 14/16 | 16/16 |
| Information lost by full deletion | 6/11 | 11/11 |
| Replacement preserves useful content | 5/5 | 5/5 |
| Total | 25/32 | 32/32 |

The first run returned HTTP 503 for two candidate calls; 29 expectations passed
and three were unavailable. Each unavailable call was retried once with identical
inputs; no successful answer was rerun. Both retries succeeded. Evidence retains
the [first incomplete run](jev-v12-first-2026-09-22.json) and
[completed report with retry provenance](jev-v12-completed-2026-09-22.json).

The original cases are known regression cases. Passing them alone does not
demonstrate generalization or improvement over the coding agent. The revision
was frozen before inspecting fresh held-out labels or outcomes; those results
and a blind agent comparison are recorded below.

## First fresh test and blind comparison

An independent author froze 14 new cases, 38 expectations, and 12 proposals
before rubric 1.2.0 results were inspected. The first unseen result was **26/38**:
9/14 dispositions, 10/12 information-loss forecasts, and 7/12 proposal checks.
Failures included harmful suggestions for published API docs, runtime help, and
a doctest option flag. [Unchanged first report](jev-v12-holdout-2026-09-22.json).
These cases became development cases once those failures informed a revision.

A separate agent reviewed unlabeled states before seeing Jev, then reconsidered
using only the saved responses. It matched all 26 disposition/proposal labels
both times, with no changed decisions. The [comparison and protocol](agent-comparison/README.md)
record no incremental accuracy benefit; the agent rejected Jev's bad advice.
The perfect baseline creates a ceiling effect. These correlated synthetic cases
and sequential reconsideration do not prove real-repository effectiveness or
review-time savings. The comparator has no model calls and preserves ties and
regressions rather than defining a completed comparison as a success for Jev.

## Final bounded revision: rubric 1.3.0

The final revision orders the instructions: inspect essential missing evidence,
correct contradicted claims, honor verified consumers, then judge redundancy for
the actual audience. It explicitly protects doctest option flags and distinguishes
correcting false claims from losing supported facts. No probabilities, labels, or
thresholds are rewritten. The rubric was frozen before reading the final six-case
validation outputs, and was not tuned further after them.

The original seven failures are all corrected. Some replacement judgments
regressed, so 1.3.0 is not described as passing the entire original suite:

| Check | Original regression | Development cases | Untouched validation |
|---|---:|---:|---:|
| Disposition | 16/16 | 13/14 | 6/6 |
| Information lost by full deletion | 11/11 | 12/12 | 5/6 |
| Proposal preservation | 3/5 | 8/12 | 4/6 |
| Total | **30/32** | **33/38** | **15/18** |

The development improvement from 26/38 to 33/38 is measured on cases used to
revise the rubric, not fresh validation. All seven known harmful proposals now
fail preservation at their original limits: loss of tuple polarity, ordering
rationale, API documentation, runtime help, month format/date semantics, a doctest flag, and
a decoder rationale. For example, preservation falls from 0.71 to 0.09 for API
doc deletion, 0.59 to 0.04 for runtime-help deletion, and 0.63 to 0.08 for removing
the doctest flag. These successes do not erase the fresh runtime-help weakness.

Final reports and service-failure provenance:

- Original: [first run](jev-v13-original-first-2026-09-22.json), [completed](jev-v13-original-completed-2026-09-22.json).
- Development: [first run](jev-v13-development-first-2026-09-22.json), [candidate retries](jev-v13-development-candidate-retries-2026-09-22.json), [completed](jev-v13-development-completed-2026-09-22.json).
- Validation: [first run](jev-v13-validation-first-2026-09-22.json), [completed](jev-v13-validation-completed-2026-09-22.json), [freeze](validation-freeze-2026-09-22.json).

Concurrent initial runs encountered HTTP 429 rate limits. Only unavailable calls
were retried once, sequentially after the initial runs; every successful answer
was retained, including semantic failures. The decoder case's successful candidate
retry first enabled its proposal call, which also returned 429. Only that proposal
was retried once; its candidate was retained. The final reports have no unavailable
judgments. The production helper has no automatic retry behavior.

### Residual errors and practical handling

Ten of 88 frozen expectations fail:

- Seven safe proposals receive insufficient preservation confidence, including
  correcting the false allowlist claim. Check supported facts and actual consumers;
  a low score is not a veto on a verified correction.
- The mixed audio-buffer comment is kept instead of reduced. Select clauses from
  source evidence; a valuable rationale does not justify adjacent narration.
- One new runtime-help case scores 0.65 on information loss (minimum 0.70) and 0.38
  on harmful-proposal preservation (maximum 0.30). Verified help requirements take
  priority regardless of these probabilities. No alternative threshold is used to
  turn these failures into passes.

All cases are synthetic; the final validation specifically probes known classes
of weakness in new examples. This is not a broad independent benchmark. Jev is a
selective second opinion, with no demonstrated improvement over the strong agent
in the recorded pilot. Neither its confidence nor AST equality licenses an edit.

## Deterministic consumer checks

`make test-comment-slop` passes **97 tests**, Ruff lint/format, and ty through uv.
The new consumer regressions demonstrate that:

- Removing a published function's docstring leaves its documentation directive
  without the description it consumes. This checks the directive/docstring
  relationship; it is not a complete Sphinx build.
- The actual runtime-help access pattern becomes an empty string after deletion.
- A real doctest passes before and after safe reduction, but fails when its
  `ELLIPSIS` flag is dropped. Only a fixed, verified benign call is executed;
  fixture implementations are never executed.
- The allowlist claim is contradicted by the resolver and caller ASTs. Correcting
  it retains the executable implementation and the true responsibility boundary.

Structural tests also verify all 23 proposals parse and preserve executable ASTs,
including intentionally harmful doc changes. This demonstrates why consumer
checks must accompany structural checks. Jev remains optional and provider
configurable; missing helper/key skips, and failures remain incomplete.

## Reproduce

```sh
make test-comment-slop
make eval-comment-slop
make eval-comment-slop EVAL_ARGS="--fixtures tests/fixtures/comment-slop-jev-holdout.json"
make eval-comment-slop EVAL_ARGS="--fixtures tests/fixtures/comment-slop-jev-validation.json"
```

Add `--offline` to validate inputs and proposal structure with semantic judgments
skipped. Live results are probabilistic and the known failures should remain
visible as exit 1. See the [blind comparison](agent-comparison/README.md) for its
fully offline reproduction command.
