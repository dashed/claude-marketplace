# Document review and comparison workflow

## Select a useful quality profile

Judge coverage against the reader's decision and the document's purpose. A short
ADR and a detailed implementation plan can both be complete. Preserve established
repository conventions when they help readers; do not add headings merely to
satisfy a checklist.

| Kind | Reader needs to establish | Useful checks |
|---|---|---|
| `design` | Whether the proposed behavior and tradeoffs meet the problem | Scope and non-goals; invariants and interfaces; considered alternatives; failure behavior; migration or operational effects where relevant |
| `analysis` | What the evidence supports and what remains uncertain | Observations separated from hypotheses; source provenance; method and assumptions; competing explanations; limits on conclusions; next discriminating evidence |
| `plan` | How to perform and verify the intended change | Actionable steps and dependencies; ownership where needed; prerequisites; success evidence; failure and rollback criteria where consequential |
| `adr` | Which decision was made, why, and with what consequences | Status and context; decision and rejected alternatives; rationale and tradeoffs; consequences and conditions that would reopen the decision |

Across kinds, check whether terms stay consistent, references resolve, key
conditions appear near the action they qualify, and a reader can distinguish
required behavior from recommendations and speculation. Specialized detail is
appropriate when the intended audience needs it. Brevity is not an independent
acceptance condition.

## Establish scope and evidence

Start with the user-requested files or sections. For working-tree changes,
discover candidate files with `git diff --name-only -- '*.md'` and, when relevant,
`git diff --cached --name-only -- '*.md'`. Inspect the actual hunks with `git diff`
or the requested revision range. These Git commands do not discover untracked
files; include newly created documents when the task names or otherwise includes
them. Map hunks to helper-reported section IDs and include nearby definitions or
constraints needed to interpret the selected text. The helper has no `--diff`
mode.

Treat heading renames and section moves carefully: positional section IDs may
refer to different material after editing. Keep the selected scope
consistent and record any mapping needed for comparison. Linked material is
evidence only after it has been read; the helper does not acquire its contents
by seeing a URL.

Build a compact preservation ledger before the rewrite:

| Item | Record and verify |
|---|---|
| Claim or requirement | Original wording, source or location, applicability, and whether it is observed, required, proposed, or unknown |
| Logical force | `must`, `should`, `may`; all/any/only; negation; preconditions; exceptions; ordering and concurrency constraints |
| Quantities | Values, units, ranges, boundaries, identifiers, versions, and whether estimates are distinguished from measurements |
| Technical artifacts | Code blocks, inline code, command flags, link targets, reference definitions, explicit anchors, and referenced headings |
| Rationale and limitations | Why the decision holds, alternatives considered, unresolved questions, uncertainty, failure cases, and evidence limits |

The ledger may stay in working notes for a small task. Do not add a report file
to the repository unless it is part of the requested deliverable. Use source
paths or stable evidence identifiers when a later reviewer needs to audit it.

## Run the static analysis

Begin with `analyze` to inspect sections and choose scope. The report covers the
whole document; map the requested sections to their section IDs and read any
surrounding definitions they depend on. Inputs must be UTF-8 and at most
1,000,000 bytes each; larger inputs are rejected rather than truncated, so
select a bounded excerpt.

## Improve a section without changing its meaning

Use findings to identify a concrete reading problem: a missing prerequisite, an
ambiguous subject, a buried condition, an unsupported conclusion, or a repeated
explanation that obscures the decision. Revise only the requested scope and any
directly affected references. Keep the baseline available for comparison.

Check consequential claims before rewriting them. For example, changing “the
cache may be stale after a timeout; invalidation behavior is unverified” to “the
cache remains consistent after timeouts” introduces a guarantee. A smoother
sentence or higher clarity judgment cannot justify it. Either retain the known
uncertainty or inspect evidence that actually establishes the stronger claim.

Likewise, “clients should retry at most twice after a transient error” cannot
become “clients retry twice after errors” without altering recommendation strength,
the upper bound, and the condition. Such regressions can leave word counts,
numbers, and technical-token inventories nearly unchanged.

Readability metrics help locate dense prose. They are heuristic estimates for
English and may penalize necessary technical vocabulary. Code is excluded from
prose calculations, but surrounding explanations can still need review. Counts
of headings, sentences, links, or obligation words expose material to inspect;
they cannot determine whether the reader has enough evidence or whether a
requirement retained its original force.

## Compare the original and candidate

Run `compare ORIGINAL CANDIDATE` after the targeted edit. Comparison is
read-only and includes both complete files. For a focused comparison, create
matching temporary excerpts that retain all necessary definitions and
conditions. Its deterministic inventories identify changed technical artifacts
and preservation signals. It cannot accept the rewrite or mutate either
document.

Review every relevant preservation difference. A changed code block or link can
be intentional, but needs source-backed justification. An unchanged inventory
does not establish semantic equivalence: negation, quantifier scope, temporal
ordering, and exceptions can change while retaining the same words or values.
Inspect removed rationale and uncertainty directly, not just added assertions.

Successful input processing yields these report parts:

| Field | Interpretation |
|---|---|
| `schema_version`, `advisory`, `status` | Report format, advisory nature, and `analyzed` (or `incomplete` with an `error` for invalid inputs) |
| `analysis` for analyze; `before` and `after` for compare | Deterministic `metrics`, `sections`, `protected` inventories, parser details, and limitations; section IDs derive from starting source line numbers |
| `preservation` for compare | Changed artifacts and lexical review signals; `meaning_preservation: not_established` explicitly withholds proof |
| `acceptance` for compare | Always `requires_evidence_review`; no automatic acceptance |
| `link_validation` | Opt-in local file/anchor checks; compare includes `before` and `after` at one logical document path |

Exit 0 means the report was produced; exit 1 means the selected document
(revised for compare) has broken local links; exit 2 means invalid inputs or
options, and the report carries only error metadata.

## Verify and report the result

Use `--check-links --link-root .` to check local files and fragments inside the
repository. Without `--link-root`, access is limited to the logical document's
directory. `--document-path docs/design.md` locates a saved snapshot logically;
for comparisons both versions default to the revised path. Self-links use each
snapshot's supplied text, even if that logical file does not exist on disk.
The helper never fetches external URLs or reads targets outside the resolved root,
including symlink escapes. Root-relative URLs start at the selected link root.

Link reports expose `checked`, `failed`, `partial`, or `not_applicable` status,
per-link findings, and coverage counts. `checked` counts fully evaluated links,
including the `broken` subset. External URLs and unsupported targets are
`not_checked`, so a mix of successful local links and external links is partial.
Limits bound input, linked-file bytes, target count and link count. Exceeding a
limit is incomplete coverage, never a successful check of omitted material.

The declared renderer profile uses CommonMark plus tables/strikethrough,
`github-slugger==0.0.3` heading IDs, and literal HTML `id`/`name` anchors. This is
not a guarantee of a site's routes, generated pages, plugins, or host-specific
HTML sanitization. Use the actual site's build/link checker for those rules.

Inspect the final Markdown diff against the ledger. Confirm source claims,
requirement force, units, exception paths, and remaining unknowns. Check actual
link targets and renderer-specific heading anchors where applicable. Parsed link
destinations are inventoried, and changed headings flag possible anchor changes;
neither proves links work. Enable the bounded local checker above. No remote
broken-link checker is bundled: report that
check as not run unless the repository's link checker or another actual check
ran. Run relevant existing documentation builds or lint checks, and verify
altered executable examples with the
appropriate tool when practical. Do not run unrelated application suites merely
because prose changed.

Report the concrete improvement and verification performed, plus unresolved
facts or limited scope that affects the conclusion.
Edit only the requested documents and directly necessary references. Do not
create additional policy, acceptance thresholds, or recurring jobs as a side
effect of a document edit.

## Sources

Parsing uses
[markdown-it-py](https://markdown-it-py.readthedocs.io/en/latest/using.html).
Heading IDs use the pinned [github-slugger](https://pypi.org/project/github-slugger/)
port; the report names this profile rather than claiming every Markdown renderer
uses it.
The `#top` fallback follows the HTML standard's
[fragment navigation](https://html.spec.whatwg.org/multipage/browsing-the-web.html#the-indicated-part-of-the-document)
rule after explicit anchor lookup.
