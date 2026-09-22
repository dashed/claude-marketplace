---
name: doc-quality
description: Review and improve engineering Markdown designs, analyses, implementation plans, and architecture decision records. Use for section-level clarity edits, requirement and evidence preservation, or comparing a proposed rewrite with its original. Uses static checks and an optional Jev second opinion; not a general prose or code-comment reviewer.
---

# Engineering document quality

Improve the reader's ability to understand a decision or act correctly while
preserving the document's facts, requirements, rationale, and known unknowns.
The agent checks evidence and edits; the bundled helper reports observations and
optional model judgments. It never rewrites files or accepts a candidate.

## Choose the scope

Identify the document kind, intended audience, reader's decision, and requested
sections. Infer these from the task and document where possible. Use the existing
structure unless it obstructs that purpose; designs, analyses, plans, and ADRs
need different coverage, not one mandatory template.

For changed-document review, use Git to discover changed Markdown files, inspect
their hunks, and select affected sections plus necessary context. There is no
`--diff` helper command. Read [references/workflow.md](references/workflow.md) for
kind-specific quality profiles, the preservation ledger, and comparison details.

Before rewriting, record the facts and obligations that must survive: sources,
requirements, conditions, quantities and units, exceptions, uncertainty, examples,
code, links, and anchors. Check consequential claims against supplied sources or
repository evidence. Missing evidence remains missing; plausible prose is not a
reason to add a guarantee or remove a caveat.

## Inspect the document

Resolve `DOC_SKILL_DIR` to the absolute directory containing this `SKILL.md`.
The helper uses Python script dependency metadata with `markdown-it-py==4.0.0`;
`uv` manages that dependency without changing the target project's environment.

```bash
uv run --no-config --no-project "$DOC_SKILL_DIR/scripts/doc_quality.py" \
  analyze docs/design.md --kind design > /tmp/doc-before.json
```

Use `--kind design|analysis|plan|adr`. The static report exposes section IDs,
structural observations, preservation inventories, and prose metrics. Code is
excluded from prose readability calculations. Readability formulas are rough
English-language heuristics; counts do not establish clarity, completeness,
correctness, or semantic equivalence.

For a semantic second opinion, resolve the separately installed general Jev
skill's directory as `JEV_SKILL_DIR` and pass its helper explicitly:

```bash
uv run --no-config --no-project "$DOC_SKILL_DIR/scripts/doc_quality.py" \
  analyze docs/design.md --kind design --section section-1 \
  --context /tmp/doc-context.json \
  --jev-helper "$JEV_SKILL_DIR/scripts/jev.py" --dry-run
```

Preview the selected sections, evidence, and questions; omit `--dry-run` for the
bounded consultation. Dry runs need no helper or credential. Repeat `--section`
for multiple sections. The default model
budget is six sections; select a coherent smaller scope or explicitly set
`--max-sections` before evaluating more. Do not mistake partial coverage for a full
review. Oversized scope retains static results and incomplete semantic coverage.

Jev is optional. An absent helper or provider key skips semantic evaluation;
continue with source inspection and static results without a setup detour. The
general helper defaults to Vercel and reads `AI_GATEWAY_API_KEY` from the process
environment or `~/.config/typesafe-ai/env`. Forward provider options such as
`--provider typesafe` when needed; details belong to the installed Jev skill.
Never assume an adjacent plugin path exists in another installation.

## Rewrite and compare

Save an unchanged baseline outside the target document. Make a targeted revision
to the requested sections after checking the preservation ledger. Retain useful
detail: an explanation, caveat, or example can be necessary even when it makes a
document longer. Prefer precise claims over confident language.

```bash
uv run --no-config --no-project "$DOC_SKILL_DIR/scripts/doc_quality.py" \
  compare /tmp/design-original.md docs/design.md --kind design \
  --context /tmp/doc-context.json \
  --jev-helper "$JEV_SKILL_DIR/scripts/jev.py" > /tmp/doc-comparison.json
```

`compare` reports deterministic preservation differences and, with Jev, evaluates
before quality, after quality, and paired preservation in three separate calls.
It compares both complete files; use coherent matching excerpts for a focused
comparison. Use `--paired-only` to omit separate before/after assessments.
Inspect both candidates and the underlying evidence. Inventory
matches cannot prove meaning is preserved; differences can be justified edits.
Use the same question version, audience, requirements, evidence, and scope for
before/after analysis and paired comparison. Preserve exact requests and hashes
when evaluating whether the workflow helps.

Read statuses before answers. Preview, skipped, failed, missing, and incomplete
judgments are not passes. A probability is neither severity nor an issue count;
0.95 and 0.98 are not universal acceptance thresholds. Do not resample until a
preferred candidate wins. Set a small attempt budget; revise again only for a
specific defect and verify that defect directly.

Finish by checking the actual Markdown diff, source claims, links and anchors,
code or command examples, and the repository's relevant documentation checks.
Report the meaningful improvements, preserved constraints, and unresolved gaps.
If an evaluation pilot shows no benefit, report that result; a successful API
call or a higher score does not establish better documentation.
