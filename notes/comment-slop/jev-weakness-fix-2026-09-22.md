# Addressing the seven comment-review weaknesses

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
and a blind agent comparison are recorded separately below when complete.

## Reproduce

```sh
make test-comment-slop
make eval-comment-slop
```

Jev remains optional and advisory. Missing helper/key skips; service failures stay
incomplete. Scores do not authorize deletion or replace consumer verification.
