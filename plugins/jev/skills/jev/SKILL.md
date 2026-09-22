---
name: jev
description: Use Jev as a bounded second opinion during agent work. Use when asked to consult Jev, compare explicit plans or candidates, check claims against supplied evidence, prioritize follow-up work, or challenge a proposed conclusion with typed judgments. For building TypeSafe-powered applications, use the typesafe-ai skill instead.
---

# Jev for agent work

Use Jev where a semantic judgment could change the next step. The agent supplies
evidence and explicit alternatives; Jev returns typed probabilities, choices, and
scores; the agent checks the relevant evidence and owns the final decision.

## Build a useful question

Start from an actual decision, such as which hypothesis to investigate or whether
a refactoring plan addresses the observed problem. Supply the minimum coherent
state: objective, constraints, candidate IDs, relevant source excerpts or observed
results, and known gaps. Keep observations separate from proposed explanations.
Send only task-relevant data suitable for the selected provider, without secrets.

Choose a primitive by its meaning:

| Decision | Primitive | Useful shape |
|---|---|---|
| Does this claim follow from the supplied evidence? | `boolean` / `noul` | One specific claim, supporting evidence, and explicit missing evidence |
| Which candidate best addresses the stated problem? | `choice` | Explicit candidate IDs, concrete selection rule, and a no-suitable-candidate option |
| How much of a defined property is present? | `score` | Ordered levels anchored to observable situations rather than vague adjectives |

Question IDs are bookkeeping: put the full judgment in `instructions`. For
independent dimensions, ask separate questions in the same request. They cannot
read one another's answers. Fetch new evidence before a dependent second call.

For comparisons, prefer a focused question about both candidates over subtracting
two vague absolute scores. Include `equivalent` and `insufficient_context` when
applicable. If order might bias the result, swap the candidate slots, preserve
their underlying identities, and compare answers. Disagreement is a reason to
inspect the evidence, not to average away the uncertainty.

## Run a bounded consultation

The bundled helper is Python 3.10+ with no runtime dependencies. Resolve its path
relative to this `SKILL.md`; `SKILL_DIR` below denotes that absolute directory.

```bash
uv run --no-project "$SKILL_DIR/scripts/jev.py" \
  --request "$SKILL_DIR/examples/review-plan.json" --dry-run
uv run --no-project "$SKILL_DIR/scripts/jev.py" \
  --request "$SKILL_DIR/examples/review-plan.json" > /tmp/jev-review.json
```

The default is Vercel's `typesafe-ai/jev`. It reads `AI_GATEWAY_API_KEY` from the
process environment, then the local convention `~/.config/typesafe-ai/env`.
An explicit `--env-file` takes precedence; assignments are parsed as literals and
never executed. No key produces `status: skipped` and requires no setup detour.
Continue the task using available analysis and say that Jev was not consulted.

For request format, provider switching, and output fields, read
[references/request.md](references/request.md). A TypeSafe switch is just
`--provider typesafe` with `TYPESAFE_API_KEY`; custom endpoints are supported.

## Use the result

Read `status` before `answers`. `evaluated` means the request succeeded, not that
the work passed. `preview` made no call; `skipped` had no credential; `incomplete`
means no reliable judgment is available. Never treat absent answers as zero risk.

Treat Jev's answer as a hypothesis to check. Reopen the evidence for a surprising
choice, inspect the selected candidate, or add the indicated test before acting.
Jev cannot run tests, calculate authoritative metrics, establish authorization,
prove correctness, or inspect context that was not sent. A model preference alone
does not justify widening the user's task or performing an external mutation.

Inspect the full distribution. A boolean near 0.5 is uncertain yes/no, not medium
severity. Choice/Score confidence describes concentration, not real-world truth.
Do not invent a universal confidence threshold. For consequential recurring use,
evaluate thresholds on representative labeled cases and retain a fallback.

Record what changed because of the consultation: selected investigation,
additional evidence, rejected plan, or no change. Preserve the exact request,
raw response, normalized answers, provider/model, and hashes when evaluation
reproducibility matters. Include the agent's evidence check separately from Jev's
judgment. One successful API call proves connectivity, not decision quality.

## Check whether it helps

Before tuning questions, fix expected outcomes for representative cases. Include
correct plans, plausible but flawed plans, ties, insufficient evidence, and
irrelevant evidence. Keep some cases held out. Compare the agent's original
decision with its decision after consulting Jev, then verify each against source,
tests, or an independent label. Report useful corrections, harmful changes, and
unchanged decisions; transport tests alone do not establish value.

Keep deterministic rules and direct lookups in ordinary code. If Jev adds no
actionable distinction on the target cases, skip that judgment instead of adding
more calls or turning a weak signal into an acceptance gate.
