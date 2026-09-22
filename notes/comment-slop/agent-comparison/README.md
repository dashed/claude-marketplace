# Blind agent comparison, 2026-09-22

The frozen pilot shows **no incremental decision benefit** from Jev: agent-only
and Jev-assisted reviews both match all 26 decision labels across 14 cases.
There are zero changes, improvements, regressions, or abstentions. The perfect
baseline creates a ceiling effect; agreement is not a demonstrated improvement.

## Protocol and provenance

An independent agent authored 14 synthetic cases with neutral case names. The
[freeze manifest](freeze.json) records the labeled and unlabeled input hashes.
A separate reviewer received the skill and unlabeled states, with no rubric,
expected labels, or Jev responses. It froze [baseline.json](baseline.json) before
the live rubric 1.2.0 run. It then received only the saved Jev reports and recorded
[assisted.json](assisted.json), still without labels. The original baseline was
unchanged. An independent audit recomputed the [comparison](comparison.json)
and verified the input hashes.

The comparator scores disposition and Boolean proposal judgments. Numerical
information-loss forecasts are excluded because the agent did not forecast those
probabilities. Missing, duplicate, extra, or malformed cases make comparison
incomplete; abstentions are separate and never pass. Exit 0 means the comparison
is valid, even if it reveals harm or no benefit.

Jev by itself passed 9/14 dispositions and 7/12 proposal-preservation expectations
on this first unseen set, or 26/38 expectations including information loss.
Its [full report](../jev-v12-holdout-2026-09-22.json) retains all 12 failures.
The assisted reviewer rejected contrary advice, including unsafe suggestions for
published API docs, runtime help, and doctest flags. Do not attribute the agent's
26/26 result to Jev.

Some disposition labels encode editorial policy, particularly keep versus reduce.
These are small, correlated synthetic cases, including paired variants. They are
not 26 independent samples. The workflow records reviewer order but cannot prove
blinding from JSON alone, and has no unassisted second-pass control. Jev's 26
provider calls sum to 82.662 seconds; no matched reviewer-time or cost measurement
establishes an efficiency benefit. Real-repository incremental value remains an
open question.

## Reproduce

```sh
make compare-comment-reviews COMPARE_ARGS="--fixtures tests/fixtures/comment-slop-jev-holdout.json --baseline notes/comment-slop/agent-comparison/baseline.json --assisted notes/comment-slop/agent-comparison/assisted.json"
```

The comparison is offline and does not execute source or call a model.
