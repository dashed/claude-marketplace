# Paired before/after Jev review, 2026-09-22

One request that shows Jev both versions of a refactor predicts an independent author's
preference on **14 of 15** pairs. Scoring each version with the snapshot rubric and subtracting,
on the same pairs, gets **10 of 15**. The paired preference is stable under repeated requests,
reformatting and removing the task, and mostly mirrors when the versions are swapped. Its eight
directional yes/no questions rank true changes well but are miscalibrated, noisy and not
direction-consistent. Treat them as hints about what to inspect, not as findings.

## What changed

- `references/jev-change-rubric.json` 1.0.0: four properties the static censuses cannot decide
  (pass-through layer, named domain rule, mixed responsibilities, duplicated rule), each asked
  in both directions as a presence question with a stated exception and true/false criteria,
  plus a `preferred` choice (before, after, equivalent, insufficient_context). The framing is
  Supercov's: "does `after` show the following where `before` did not?"
- `scripts/jev_review.py --before B --after A`: one request whose state is only the shared task
  and constraints and the two versions' code. It refuses two different contracts.
- `scripts/eval_python_complexity_changes.py`: frozen expectations plus five controls per pair —
  repeat, AST-identical reformat (`ruff format --line-length 40`, AST equality asserted), before and
  after swapped, no task or constraints, and per-signal static separability.

## Freeze and procedure

1. The rubric was written and hashed before any case existed
   (`4b8a9659…`, 22:21:44Z). The control tolerances were set with it: repeat 0.05, reformat 0.15,
   swap 0.25.
2. A separate agent wrote `tests/fixtures/python-complexity-jev-changes.json` from the rubric's
   definitions and the file format only. It read no earlier model output and made no provider
   call. 15 pairs, 129 labeled checks, including traps for every stated exception, a cosmetic
   pair and a pair whose effect depends on code that is not shown.
3. The lead verified the suite offline (behavior passed on both versions of all 15 pairs, 168
   checks; static census complete) and recorded [the freeze](jev-changes-freeze-2026-09-22.json)
   before any live call. No label, rubric or tolerance changed afterwards.
4. One live run through OpenRouter (`typesafe/jev-1.13-20260917`, TypeSafe protocol): 75 paired
   calls, none unavailable, $0.0075. [Summary with every response](jev-changes-live-2026-09-22.json).
5. A snapshot-rubric baseline on the same pairs, with its derivation rule declared before the
   calls ran: [summary and rule](jev-changes-snapshot-baseline-2026-09-22.json).

## Results

**Preference.** 14 of 15, against 7 of 15 for always answering the most common label. It
preferred `before` on `duration_parser_split`, where every static delta improves (maximum
cognitive −9) but the split threads state through five arguments, and called the cosmetic pair
`equivalent`. Static separability for `preferred` is empty: no single census delta splits its
labels on this suite. The miss is `invoice_settlement_unseen`, labeled `insufficient_context`,
which Jev judged `after` (0.84).

| Variant | `preferred` choice unchanged |
|---|---:|
| Repeat of the same request | 15 / 15 |
| AST-identical reformat | 15 / 15 |
| Task and constraints removed | 15 / 15 |
| Before and after swapped (mirrored) | 13 / 15 |

The two swap failures are the cosmetic pair and the unseen-code pair. In both, the swapped
request also favored whichever version sat in the `after` slot: a position bias on ambiguous
changes. Removing the task and constraints changed no preference on this suite, so it does not
show whether context helps.

**Directional questions.** They found 12 of 13 labeled changes but raised 22 false alarms among
101 labeled non-changes, so 91 of 114 overall, below the 101 of 114 of always answering "no".
Their probabilities still rank well: a labeled change outranks a labeled non-change with
probability 0.954, pooled over the eight questions. Fifteen of the 22 false alarms sit between
0.31 and 0.61; seven are confident (≥ 0.7), and the two most confident are exactly the exception traps —
`price_endpoint_alias` (a required public endpoint forwarding, 0.97) and `parking_tariff_names`
(wrappers that add a tariff, 0.91) were both called new pass-throughs.

**Controls.** The frozen tolerances fail 23 times:

| Control | Failed | Largest moves |
|---|---:|---|
| Repeat of the same request | 8 / 15 | 0.06–0.14 |
| AST-identical reformat | 3 / 15 | 0.17–0.21 |
| Swap, mirrored | 12 / 15 | 0.28–0.77 |

Identical requests are not deterministic at this size: a probability can move by about 0.1
between two calls. An earlier three-call check on a short request was identical, so the noise
grows with the input or varies by load; either way, a single answer within about 0.1 of a
threshold decides nothing. Reformatting moves answers little more than repeating does. The swap
control is where the directional questions break: asking "introduced" and then "removed" with
the versions swapped gives answers up to 0.77 apart, so an individual direction answer is not a
reliable statement about the change.

**Against separate snapshot scores.** The snapshot baseline matched 10 of 15. All five misses are
refactors whose four score deltas sum to under 0.15 in magnitude, so the rule calls them
`equivalent`: separately scored versions sit near the top of each scale and barely move. The
snapshot baseline did catch the unseen-code pair (`context_sufficient` 0.22), which the paired
preference missed. The two methods disagree on six pairs, five in the paired request's favor;
an exact McNemar test gives p ≈ 0.22, so this is a direction, not a significant difference.

## What this supports

- Use the paired `preferred` answer as the Jev signal for a refactor, alongside the static
  census and behavior checks. It is the only signal here that beat both a trivial baseline and
  separate scoring, and it held under every control except position on ambiguous changes.
- Read the directional answers as pointers for inspection, weighted by rank, never as findings
  on their own. They miss stated exceptions with high confidence and are not direction-consistent.
- Keep the snapshot `context_sufficient` check for missing code; the paired preference does not
  reliably choose `insufficient_context`.
- Treat any single probability within about 0.1 of a cutoff as undecided.

## Limits

One suite of 15 synthetic single-module pairs, one author, one live run, one provider. The
directional questions have one or two positive labels each, so their per-signal numbers are
thin. The no-context variant was never tested against a pair whose judgment depends on the
constraints. None of this measures whether a coding agent decides better with the paired answer
than without it; the earlier blind comparisons for comment-slop and doc-quality found no such
benefit, and no such comparison exists for python-complexity. The rubric was not tuned on these
results; a revision needs a fresh suite.

## Reproduce

```sh
make test-python-complexity
make eval-python-complexity-changes EVAL_ARGS=--offline
make eval-python-complexity-changes EVAL_ARGS='--output-dir /tmp/jev-changes-new'
```

Live runs use the Jev helper's user configuration and cost well under a cent; results move by
about 0.1 between runs, and failed expectations and controls stay visible as exit 1.
