---
name: doc-quality
description: Review and improve engineering Markdown designs, analyses, implementation plans, and architecture decision records. Use for section-level clarity edits, requirement and evidence preservation, or comparing a proposed rewrite with its original. Uses static Markdown checks; not a general prose or code-comment reviewer.
---

# Engineering document quality

Improve the reader's ability to understand a decision or act correctly while
preserving the document's facts, requirements, rationale, and known unknowns.
The agent checks evidence and edits; the bundled helper reports static
observations. It never rewrites files or accepts a candidate.

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
The helper pins its Markdown parser and heading slugger in Python script metadata;
`uv` manages those dependencies without changing the target project's environment.

```bash
uv run --no-config --no-project "$DOC_SKILL_DIR/scripts/doc_quality.py" \
  analyze docs/design.md --check-links --link-root . > /tmp/doc-before.json
```

The static report exposes section IDs, structural observations, preservation
inventories, and prose metrics. Code is excluded from prose readability
calculations. Readability formulas are rough
English-language heuristics; counts do not establish clarity, completeness,
correctness, or semantic equivalence.

`--check-links` checks local files and anchors within `--link-root` (default: the
document's directory). Remote URLs, unsupported syntax, and targets outside that
root remain explicitly unchecked. Read the renderer profile and coverage in
`link_validation`; this bounded check does not replace the site's build checks.

## Rewrite and compare

Save an unchanged baseline outside the target document. Make a targeted revision
to the requested sections after checking the preservation ledger. Retain useful
detail: an explanation, caveat, or example can be necessary even when it makes a
document longer. Prefer precise claims over confident language.

```bash
uv run --no-config --no-project "$DOC_SKILL_DIR/scripts/doc_quality.py" \
  compare /tmp/design-original.md docs/design.md \
  --check-links --link-root . --document-path docs/design.md > /tmp/doc-comparison.json
```

`compare` reports deterministic preservation differences between both complete
files; use coherent matching excerpts for a focused comparison. Inspect both
candidates and the underlying evidence. Inventory matches cannot prove meaning
is preserved; differences can be justified edits.
Both snapshots use the same logical `--document-path` (default: revised file),
so self-links are checked against each snapshot's own headings. Link failures in
the revised file return exit 1; historical failures remain visible separately.

For faithful revisions, compare reading effort explicitly: removing redundant
framing or grouping a decision with its reason can help even when facts stay the
same. Shortness alone is not a gain. When a revision has no clear audience
benefit, or choosing needs evidence you do not have, say so instead of picking one.

Finish by checking the actual Markdown diff, source claims, links and anchors,
code or command examples, and the repository's relevant documentation checks.
Report the meaningful improvements, preserved constraints, and unresolved gaps.
Better readability metrics or unchanged inventories do not establish better
documentation.
