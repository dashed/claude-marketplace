# Document-quality 1.1.0 follow-up

The two known editorial misses are fixed on the unchanged original regression:
**30/30**, up from 28/30. New repository-excerpt comparisons score **28/30**, with
all ten version preferences matching, and profile-specific judgments score
**12/13**. Jev remains optional and advisory. A blind first pass, unassisted
second pass, and Jev-assisted third pass each score **28/30** on the fresh frozen
labels, so there is still no demonstrated incremental agent accuracy.

## Changes and checks

- `--check-links` now checks local files, images, reference links, and Markdown or
  literal HTML anchors within a selected root. It handles duplicate headings,
  encoded destinations, logical symlink paths, and snapshots at one logical path.
  External URLs, renderer-dependent features, and resource limits stay explicitly
  unchecked. Revised broken links return exit 1; positive Jev answers cannot hide
  those failures. Site-specific builds and remote checking remain separate.
- Rubric 1.1.0 changes only the paired editorial-preference instructions and
  criteria: lower unnecessary reading effort can be a real benefit even if facts
  are unchanged. Necessary qualifications, constraints, and useful detail remain
  protected. `equivalent` and `needs_context` remain available.
- A profile eval runner validates single-section inputs, excludes gold labels from
  requests, preserves provenance and failures, and stops on unavailable judgments.
  Both eval runners work offline without a key; a preview never counts as a pass.
- Offline tests exercise link regressions, root boundaries, parsing, provider
  forwarding, no-key behavior, incomplete evidence, and immutable eval inputs.
  Validation uses uv, Ruff, ty, strict repository checks, and skill validation.

The [verification record](verification.json) records **200 passing offline tests**,
Ruff, ty, repository/skill validation, and the standalone uv run.

[Local checks of the skill and workflow](local-link-checks.json) ran with Jev
skipped. The skill's local reference passed; workflow external URLs were reported
unchecked. This is evidence of the bundled checker, not an external URL or site
renderer test. Link checks use POSIX directory-relative opens for bounded reads.
The [final local check](final-local-link-checks.json) also confirms all 17 local
references in this evidence note after the audit artifact was created; the
original audited link report is retained separately.

## Frozen protocol

An independent author created ten comparisons using 122–306-word excerpts from
tracked repository documents: four safe improvements, four harmful changes, one
equivalent edit, and one missing-context case. Revisions are synthetic
counterfactuals, not adopted repository changes. Eight separate profile cases
cover all four kinds with 13 selected expectations. Some profile inputs collapse
subheading markup into one selected section; the freeze records that transformation.

The [freeze](freeze.json) records exact source Git blobs and line ranges, hashes,
author independence, rubric identity, and the control protocol. Commit `c3ccab0`
freezes cases and questions before the live follow-up results. The author did not
see the questions or earlier model outputs; the rubric editor did not see fresh
labels before freezing the change. Original fixture bytes and all new labels
remain unchanged. No question was tuned after these fresh results.

A [Jev design consultation](design-consultation.json) supported explicitly judging
reading effort and adding a rereading control. That is design advice, not ground
truth or an experiment showing benefit.

## Live results

| Evaluation | Matched | Total | Interpretation |
|---|---:|---:|---|
| Original regression, selected preservation checks | 20 | 20 | No observed regression on these assertions |
| Original regression, version preference | 10 | 10 | Both known ADR misses corrected |
| Fresh repository excerpts, selected preservation checks | 18 | 20 | Two narrower-label disagreements retained |
| Fresh repository excerpts, version preference | 10 | 10 | Four harmful edits rejected; equivalence and missing context retained |
| Four profiles, selected judgments | 12 | 13 | One gap versus missing-context disagreement |

The original `case-05` and `case-09` now prefer revised, each with probability
0.95. This is a development regression result after targeted question revision,
not a fresh generalization test. All providers/model aliases, question/state
hashes, distributions, and raw responses are in the evidence:

- [Original regression summary](regression-summary.json) and [all attempts](regression-attempts.json).
- [Fresh challenge summary](challenge-summary.json) and [raw reports](challenge-reports.json).
- [Profile summary](profiles-summary.json) and [raw reports](profiles-reports.json).

Three original-regression calls returned HTTP 503: `case-02`, `case-06`, and
`case-10`. Each stopped its invocation. Manual continuations selected only
unanswered cases and retried each unavailable request once; later calls were
paced at least two seconds apart. There were 13 attempts for ten successful
regression judgments. No successful judgment was repeated or selected from
multiple responses. Fresh challenge and profile runs each completed in one
sequential pass with no retry. Historical incomplete summaries are retained;
the combined regression summary explicitly records the failed attempts.

Retained disagreements:

1. `challenge-06/evidence_supported`: 0.31 against a frozen minimum of 0.7.
   A draft table's discovery target changes from >90% to 95%+, supported by a
   conflicting summary but with no authority establishing which target governs.
   Jev correctly chose `needs_context`. The narrow label treats historical source
   presence as support; the question also requires support at the strength stated.
2. `challenge-08/requirements_preserved`: 0.03 against a minimum of 0.7.
   Numbers survive, but a manual documentation audit becomes purported upstream
   maintainer validation. Jev correctly preferred original and rejected the
   invented support. The label intended to distinguish normative requirements
   from attribution; the context explicitly requires preserving the author.
3. `profile-04/claim_evidence`: `gap` rather than `needs_context`.
   The selected section presents an accuracy claim; context asks for
   evidence-dependent validation. Expression of a claim and validation of its
   truth are different judgments, and the current framing crosses that boundary.

These remain failures against their frozen labels. They also expose ambiguity in
how dimensions and gold labels are defined; they are not three cleanly isolated
model errors. The [independent audit](audit.json) rechecks scores and discusses
these boundaries. Neither labels nor probabilities are changed to improve results.
The skill now directs the editor to inspect missing evidence and dimensions
separately before acting on such findings.

## Agent comparison with a rereading control

The reviewer received only [unlabeled cases](unlabeled.json), then froze its
[baseline](baseline.json). It reread the same cases without Jev and froze an
[unassisted control](control.json). Finally it received only the
[Jev reports](assisted-input.json) and froze its [assisted review](assisted.json).
The supplied reports include question wording; only the third pass saw it. Gold
labels and additional repository evidence were never supplied to that reviewer.

| Review | Frozen labels matched | Wall-clock seconds |
|---|---:|---:|
| First pass | 28/30 | 65.82 |
| Unassisted second pass | 28/30 | 38.70 |
| Jev-assisted third pass | 28/30 | 98.21 |

The two scored disagreements are the same narrow signals as Jev's fresh misses.
No version preference changed. Jev prompted the reviewer to reconsider two
additional signals on `challenge-08`: behavior and uncertainty preservation both
changed from true to false because the attribution changes the reported review
process and its epistemic authority. Those dimensions had **no pre-registered
labels**; they are exploratory observations, not counted accuracy improvements.

[Scoring and input hashes](agent-comparison.json) retain every counted decision
and both unregistered changes. Probability-bound gold expectations become
Boolean labels for the agent; their probabilities are not forecasts by the agent.
Earlier frozen files remain byte-identical.

This adds a rereading control but remains one reviewer in fixed sequential order,
without randomization or a matched third unassisted pass. It cannot isolate Jev's
causal effect. Timings include reading and tool overhead; they establish neither
cost savings nor an efficiency gain. The small sample, correlated assertions,
synthetic revisions, label-boundary ambiguity, and mutable model alias still
limit generalization. No universal confidence cutoff or autonomous acceptance
policy follows from these results.

## Reproduce new runs

Run from the repository root, preserving these artifacts:

```bash
make test-doc-quality
make validate-strict
make eval-doc-quality EVAL_ARGS='--offline --output-dir /tmp/docs-regression-preview-new'
make eval-doc-quality EVAL_ARGS='--fixtures tests/fixtures/doc-quality-challenge.json --offline --output-dir /tmp/docs-challenge-preview-new'
make eval-doc-profiles EVAL_ARGS='--offline --output-dir /tmp/docs-profiles-preview-new'
```

Omit `--offline` for a paid live call through the configured general Jev helper.
Use a new output directory each time. Live exit 1 means a frozen expectation
mismatch; exit 2 means unavailable/incomplete. Inspect those results without
resampling successful requests or revising the existing labels. Collect fresh,
independently labeled cases before another rubric revision or provider comparison.
