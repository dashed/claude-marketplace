# Engineering Markdown review: implementation and evidence

The `doc-quality` skill combines section-aware static analysis with optional Jev
judgments. The agent edits requested sections and verifies technical meaning;
the helper never writes documents or automatically accepts an edit.

The first frozen Markdown evaluation passed **28/30 expectations**: all 20
preservation checks and 8/10 editorial preferences. All five deliberately harmful
rewrites were rejected. Two safe improvements were judged equivalent to their
originals. A blind agent scored 30/30 both before and after seeing Jev, so this
pilot demonstrates **no incremental accuracy benefit** over that agent.

## Delivered workflow

- A CommonMark/table parser identifies disjoint sections, heading paths, and
  inclusive source lines, including duplicate and setext headings. Fenced text
  does not become a section heading.
- Deterministic observations include sentence/paragraph lengths, heading depth,
  repeated sentences, and approximate English Flesch/Flesch-Kincaid scores. Code
  is excluded from readability. These measurements do not establish correctness
  or writing quality.
- Preservation inventories cover code, inline code, links and images, reference
  definitions, frontmatter, HTML, quantities, requirement modals, negation, and
  headings. Equality cannot detect changed relationships, scope, or implications.
- Four quality profiles target design docs, analyses, implementation plans, and
  ADRs. Profile choices distinguish a real gap from not-applicable or missing
  context. A section need not satisfy every concern of the whole document.
- Optional comparisons make independent original/revised quality calls with the
  same questions and context, then a separate paired preservation call. A
  `--paired-only` option supports bounded evaluation. No revision contaminates
  its original's absolute quality input.
- The general Jev skill owns provider configuration and credentials. Missing
  helper/key skips; API failures stay incomplete. Section/request budgets and
  whole-batch size preflight bound calls. Typed answers, provenance, and hashes
  are checked before accepting helper evidence as evaluated.

No remote link checker, grammar checker, or automatic rewrite command is bundled.
The skill directs the editing agent to run the repository's actual link, renderer,
example, or documentation checks as applicable. Static output labels link checking
as not run. Comparisons always require evidence review, even with positive Jev
answers and unchanged protected content.

## Frozen first evaluation

An independent author wrote ten neutral cases: five safe improvements and five
polished but harmful edits, covering all four document kinds. The questions and
expected outcomes were frozen in commit `6776fb0` before model results were read.
The [freeze manifest](freeze-2026-09-22.json) records file hashes. Neither fixture
labels nor rubric instructions were tuned after this run.

| Check | Passed | Total |
|---|---:|---:|
| Selected preservation assertions | 20 | 20 |
| Preferred version | 8 | 10 |
| Total frozen expectations | 28 | 30 |
| Harmful edits correctly preferred-original | 5 | 5 |

The harmful cases cover invented certainty, weakened requirement strength,
removed exceptions, reassigned quantitative bounds, and an unsupported causal
conclusion. These cases test losses that smoother prose or equal token inventories
can hide. `case-05` and `case-09` remain failures of the frozen preference labels:
Jev chose `equivalent` where the author expected `revised`. These are editorial
preference disagreements, not evidence that those revisions corrupt requirements.

Evidence:

- [Initial summary](live-summary-2026-09-22.json) and [all raw reports](live-reports-2026-09-22.json).
- [Summary with repaired provenance extraction](live-summary-with-provenance-2026-09-22.json).
- [Jev design consultation](design-consultation-2026-09-22.json).

Ten sequential provider calls used Vercel/Gateway and the `typesafe-ai/jev` alias.
No call was unavailable, no successful answer was retried, and no threshold was
relaxed. The evaluation command exits 1 because two expectations fail. The
provenance summary initially expected a nested field that the general helper does
not emit; the extractor was fixed to read actual flat fields and model IDs. The
corrected summary was reconstructed from unchanged raw reports with no new calls.
The raw-file freeze hash and canonical JSON rubric hash use different encodings;
each is retained for its own check.

The design consultation favored testing semantic fidelity under attractive but
harmful rewrites and keeping absolute quality contexts separate. It supplied
advice, not gold labels or proof that the architecture improves decisions.

## Blind comparison

A separate reviewer received only neutral unlabeled cases and the skill. It froze
[its baseline](agent-comparison/baseline.json) before seeing Jev. It then received
only the raw Jev reports, still without expected labels, and recorded
[its assisted decisions](agent-comparison/assisted.json). The baseline remained
byte-identical. An independent audit recomputed the
[comparison](agent-comparison/comparison.json) and verified its input hashes.

Both reviews matched all 30 frozen decision labels. There were no changes,
improvements, regressions, or abstentions. Probability-bound labels become Boolean
labels when scoring the reviewers; their answers are not probability forecasts.
Only the signals with frozen labels are counted, not every incidental answer.
The agent retained its safe-rewrite preferences despite Jev's equivalent choices.

This perfect baseline has a ceiling effect. Thirty assertions across ten small
synthetic examples are not thirty independent samples. The sequence has no
unassisted second-pass control, and no matched time or cost measurement establishes
an efficiency gain. Blinding is a recorded workflow property, not something JSON
alone can prove. These results do not calibrate universal cutoffs or establish
safety, broad generalization, or superiority to comment review.

## Independent forward exercise

A separate agent used the skill on a fresh fictional rollout plan. Its
[original](forward-test/before.md), [revision](forward-test/after.md), and
[protocol evidence](forward-test/protocol.md) retain mandatory force, cancellation
exceptions, two retries, 750 ms spacing, an 8 MiB bound, code, links, rationale,
and uncertainty about duplicate processing. It changed the requested section and
left rollout evidence untouched. The [verification](forward-test/verification.json)
records a manual fact ledger plus 24 passing interface/artifact checks. Local link
target and heading existence were checked; no renderer or remote link checker ran.

The count rose from 138 to 140 words while mean sentence length fell from 17.25
to 9.33 words. This is a density observation, not an acceptance criterion. The
[full live comparison](forward-test/live-comparison.json) used identical question
hashes for the two quality calls. Clarity rose from 2.56 to 2.87 on the declared
0–3 scale. However, the paired preference was `equivalent`, with probabilities
0.38 equivalent, 0.32 revised, 0.29 original, and 0.01 needs-context. That uncertain
preference does not establish a quality win or authorize an edit.

This exercise verifies the before/after plumbing and a concrete rewrite workflow.
It is not a calibrated assessment of the four quality profiles; only the plan
profile received this live absolute-quality exercise.

## Verification and use

`make test-doc-quality` passes **106 tests** plus Ruff lint/format and ty, all
through uv. Strict repository and skill validation pass. Tests cover parser edge
cases, code/link preservation, numeric rebinding limitations, optional credentials,
provider forwarding, request isolation, early-stop behavior, invalid evidence,
budget preflight, and eval failure retention. The standalone PEP 723 command was
also run with uv outside project dependency selection.

```sh
# Review without Jev; static results remain available.
uv run --no-config --no-project plugins/doc-quality/skills/doc-quality/scripts/doc_quality.py \
  analyze docs/design.md --kind design

# Compare bounded originals/revisions with the shared optional helper.
uv run --no-config --no-project plugins/doc-quality/skills/doc-quality/scripts/doc_quality.py \
  compare original.md revised.md --kind design --context context.json \
  --jev-helper plugins/jev/skills/jev/scripts/jev.py

make test-doc-quality
make eval-doc-quality EVAL_ARGS=--offline
make eval-doc-quality
```

The offline evaluation previews all ten comparisons and records all 30 semantic
checks as skipped, never passed. Live probabilities and provider aliases may
change. Keep failures visible, inspect source evidence, and use Jev only when its
judgments could improve the next action. Skill instructions are in
[SKILL.md](../../plugins/doc-quality/skills/doc-quality/SKILL.md).
