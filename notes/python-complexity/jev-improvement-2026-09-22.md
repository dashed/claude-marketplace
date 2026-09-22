# Jev rubric improvement, 2026-09-22

The readability regression is fixed on the original examples, with useful
structure controls passing on separate examples. Transformation probabilities
remain less reliable. This is evidence of better synthetic discrimination,
not proof of better production refactors or calibrated probabilities.

## What changed and why

Rubric 1.0.0 asked whether behavior was apparent; a model could infer a result
while overlooking the work required to change its implementation. Rubric 1.1.0
asks about concrete maintenance bookkeeping: retained guards, condition/outcome
associations, conditional-expression binding, and helper transitions. Simplicity
now includes avoidable control structures. Two separate Boolean questions ask
whether guard flattening or expression expansion would actually help under the
supplied constraints. Scores remain model responses; there is no static-derived
score cap, synthetic adjustment, changed expectation, or sampling for better answers.

Jev also reviewed the proposed design and validation plan. It selected a
same-counts/different-constraints check as the most useful countercheck and gave
only 0.06 to the claim that synthetic validation alone proves general value.
That advisory review is retained in
[the design request and response](jev-design-review-2026-09-22.json).

## Freeze and comparison procedure

1. The eight-case validation corpus and extended runner were committed as
   `340edd4` before editing the rubric. The original nine expectations stayed fixed.
2. The old rubric ran against validation; results were saved without inspecting
   individual outputs until the new rubric was written and the original suite ran.
3. The revised rubric passed the original suite, then was frozen before running
   validation or the separate agent-authored corpus. No validation failure was
   used to tune it or lower thresholds.
4. Calls used the configured Vercel Gateway key, `typesafe-ai/jev`, the same
   fixture context, Ruff 0.15.16 and complexipy 7.0.1. All source is synthetic.
   Each saved summary records timestamps, fixture/rubric/state hashes, actual
   model responses, distributions, metadata, and every failed/skipped check.

## Original suite

| Expectation | Old difference | New difference | Required |
|---|---:|---:|---:|
| Flat readability above nested | 0.05 | 1.68 | >= 0.25 |
| Flat readability above dense ternary | 0.02 | 1.14 | >= 0.25 |
| Flat simplicity above nested | 0.13 | 1.08 | >= 0.25 |

All nine original expectations pass, up from six. All 476 behavior checks and
the three original static relationships pass. The abstraction and missing-context
checks still pass. The changed anchors define a new scale: rerun both sides with
the same rubric before comparing refactors.

Evidence: [original old run](jev-eval-results-2026-09-22.json),
[original revised run](jev-original-v11-2026-09-22.json).

## Separate validation

The old rubric passed 8 of the 10 existing-signal expectations and skipped the
six new action-signal expectations. The revised rubric passes 15 of 16. All 32
behavior checks pass. It separates nested filtering from guard clauses and a
dense shipping expression from explicit branches. Simple ternaries, natural
collection nesting, a named Boolean predicate, and an invariant helper retain
high scores.

One failure remains: already-flat filtering receives 0.35 for flattening benefit,
above the frozen maximum 0.30. This is not a strong yes; it is still a failed
negative-control expectation, and the runner exits 1. Do not interpret Boolean
probabilities as intensity or automatically refactor based on these signals.

Evidence: [validation old run](jev-validation-v1-2026-09-22.json),
[validation revised run](jev-validation-v11-2026-09-22.json).

## Reproduce

```sh
make test-python-complexity
make eval-python-complexity
make eval-python-complexity EVAL_ARGS='--fixtures tests/fixtures/python-complexity-jev-validation.json'
make eval-python-complexity EVAL_ARGS='--offline --fixtures tests/fixtures/python-complexity-jev-validation.json'
```

Expectations are fixture tests, not production quality gates. The evaluator uses
the optional provider configuration; missing credentials produce skipped semantic
checks. It executes trusted fixture Python for behavior checks, never reviewed
application source. A model alias can change, and these single-run observations
do not establish stability, latency/cost benefit, or agreement with human reviewers.
