---
name: style-writer
description: "Write content using stored writing styles from the writing-styles/ collection. Use when the user wants to write in a specific voice, apply a stored style, list available writing styles, or evaluate text against a style rubric. Triggers on 'write in [style] style', 'use [style] voice', 'list writing styles', 'apply style', or 'evaluate my writing'."
---

# Style Writer

Write content in any stored writing style. Discovers available styles from the `writing-styles/` collection, loads the appropriate guide into context, applies it during writing, and optionally self-evaluates the result against the style's rubric.

## When to Use

- User wants to write content in a specific stored style
- User asks to "list available styles" or "what voices do we have?"
- User wants to edit or rewrite existing text to match a style
- User asks to evaluate or score text against a style rubric

## Style Discovery & Selection

List directories in `writing-styles/` (exclude `_template/`). Each directory is an available style.

**Selection logic:**

| Scenario | Action |
|----------|--------|
| User names a style exactly | Look it up directly in `writing-styles/<name>/` |
| User describes a style vaguely | List available styles, show each voice-card summary, let user choose |
| Only one style exists | Use it by default, confirm with user |
| No styles found | Tell user to create one with the style-extractor skill |

## Context Loading

Load compact files first — voice card + do/don't list give enough context for most tasks.

| Order | File | When to load | Purpose |
|-------|------|-------------|---------|
| 1 | `style/voice-card.md` | Always | Compact essential reference (~300 words) |
| 2 | `style/do-dont.md` | Always | Actionable guardrails for writing |
| 3 | `style/full-style-guide.md` | Long/complex pieces, or if voice card isn't enough | Deep reference with examples |
| 4 | `evals/style-rubric.md` | Only when evaluating | Scoring dimensions |

Read files using the Read tool.

## Writing

Apply the loaded style to the user's content request:

1. Use the voice card as the primary compass
2. Cross-check against the do/don't list while writing
3. For long pieces: write in chunks, periodically re-read the voice card to prevent drift
4. Incorporate style-appropriate transitions, sentence patterns, and rhetorical moves

### Fiction: Narrative Authenticity

When writing fiction or creative writing, also load [references/narrative-authenticity.md](references/narrative-authenticity.md) and:

1. **Pre-write:** Review the pre-writing checklist. Plan structural choices (timeline, subplots, character moral complexity) before drafting.
2. **During writing:** Vary scene types and emotional intensity. Resist the pull toward clean single-track plots, explicit thematic statements, and embodied-metaphor-only emotion.
3. **Post-write:** Run the post-writing checklist. Audit for AI narrative defaults — especially Claude-specific fingerprints (flat event escalation, epilogue endings, low event diversity).

If the style guide includes narrative construction notes (from fiction extraction), those override the general guidance in narrative-authenticity.md. The style guide captures THIS author's narrative choices; the authenticity guide captures general AI defaults to avoid.

### Task-Specific Approach

| Task | Approach |
|------|----------|
| Short piece (email, paragraph) | Load voice card + do/don't. Write in one pass. |
| Long piece (essay, chapter) | Load full style guide. Write in sections, re-checking voice card between sections. |
| Fiction piece | Load full style guide + narrative-authenticity.md. Plan structure before drafting. Post-audit for AI tells. |
| Editing existing text | Load voice card + do/don't. Identify violations, rewrite to match. |
| Style comparison | Load rubric. Score original text, identify gaps, suggest rewrites. |

## Self-Evaluation

Triggered when user asks "evaluate", "score", or "how well does this match?"

1. Load `evals/style-rubric.md`
2. Score the output on each of the 5 rubric dimensions (1–5)
3. Report total score with per-dimension breakdown
4. **For fiction:** Also score on 5 narrative construction dimensions (structural diversity, thematic subtlety, emotional range, character agency, event/temporal complexity). See the Narrative Construction Evaluation section in [references/evaluation-guide.md](references/evaluation-guide.md).
5. Suggest 2–3 specific improvements

See [references/evaluation-guide.md](references/evaluation-guide.md) for detailed scoring guidance and common pitfalls.

## Anti-Patterns

- **Don't over-load context.** Start with voice card + do/don't, escalate to full guide only if needed.
- **Don't apply style mechanically.** The voice card captures the spirit, not a formula.
- **Don't ignore the do/don't list.** It catches the most common style violations.
- **Don't mix styles.** Apply one style consistently per piece.
- **Don't skip evaluation.** If the user cares about accuracy, score the result.

## References

- [references/evaluation-guide.md](references/evaluation-guide.md) — Detailed self-scoring guide with common pitfalls and improvement strategies
- [references/narrative-authenticity.md](references/narrative-authenticity.md) — AI narrative debiasing guide with Claude-specific fingerprints (fiction only)
