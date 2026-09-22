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
refer to different material after editing. Keep the selected semantic scope
consistent and record any mapping needed for comparison. Linked material is
evidence only after it has been read; the helper does not acquire its contents
by seeing a URL.

Use `--context` for a JSON file containing the audience, intended reader decision,
relevant source excerpts, requirements, and explicit evidence gaps. Keep observed
facts separate from proposed changes. Send only task-relevant material suitable
for the selected provider; exclude secrets. A context file supplies evidence and
constraints, not an authoritative label that overrides contradictory sources.

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

## Run a bounded analysis

Begin with static analysis to inspect sections and choose scope. Without
`--jev-helper`, the helper still produces its deterministic report. A dry run
previews requests without invoking a helper or provider and needs no credential.
Review that preview before a
first external consultation when the chosen scope or evidence is uncertain.

The default analyze budget covers at most six sections. If the document exceeds
the budget, choose sections explicitly or set a larger explicit `--max-sections`.
Do not quietly send the first six sections and describe the result as complete.
An oversized request must leave usable static findings while reporting the
semantic coverage as incomplete. A selected section may still need surrounding
definitions in the context file; section-level scoring does not infer omitted
cross-document requirements.

Inputs must be UTF-8 and at most 1,000,000 bytes each. Each semantic request is
limited to 100,000 serialized bytes; oversized requests report incomplete and
are not silently truncated. Read and narrow scope when needed.

Keep the general Jev transport separate from this skill. Resolve the available
general skill and pass `--jev-helper` with its actual script path. Do not copy its
transport implementation here or hardcode a relative sibling-plugin layout.
Missing helpers or credentials are ordinary skips: finish the document task
using source inspection and static checks. Ask about provider installation or
configuration only if the user has requested that work.

The CLI forwards the general helper's `--config`, `--provider`, `--model`,
`--endpoint`, `--protocol`, `--api-key-env`, and `--env-file` options. The default
Vercel preset uses `AI_GATEWAY_API_KEY` and the local credential-file convention
`~/.config/typesafe-ai/env`; `--provider typesafe` uses `TYPESAFE_API_KEY`. Read the
installed Jev skill for precedence rules and custom endpoint requirements rather
than assuming that selecting a provider preserves another preset's overrides.

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

Run `compare ORIGINAL CANDIDATE --kind KIND` after the targeted edit, optionally
with the same context and Jev helper. Comparison is read-only and includes both
complete files; it has no `--section` or `--max-sections` flag. For a focused
comparison, create matching temporary excerpts that retain all necessary
definitions and conditions. Its deterministic inventories identify changed
technical artifacts and preservation signals. With
Jev, the default makes three calls: original quality, revised quality, and paired
preservation. The original-quality request contains only the original candidate;
the revised text cannot influence that baseline judgment. Comparison requests
omit filenames that could reveal favorable or unfavorable labels. The paired
questions focus on meaning preservation and the reader's task. None of these
components can accept the rewrite or mutate either document.

Use `--paired-only` to make only the paired call when a bounded evaluation needs
less model work. This mode omits separate before/after quality assessments;
report that limited coverage explicitly. The default returns those assessments
without calculating a numerical quality delta or an acceptance decision.

Review every relevant preservation difference. A changed code block or link can
be intentional, but needs source-backed justification. An unchanged inventory
does not establish semantic equivalence: negation, quantifier scope, temporal
ordering, and exceptions can change while retaining the same words or values.
Inspect removed rationale and uncertainty directly, not just added assertions.

For comparable before/after evidence:

1. Fix the document kind, audience, reader decision, requirements, source
   evidence, known gaps, and selected semantic scope before comparing.
2. Use the same versioned analysis questions and context for both documents;
   change only the candidate text and necessary section mapping. Use the fixed
   paired question set for the comparison, recording its version separately.
3. Retain exact requests, question and state hashes, candidate identities, and
   provider/model details when reporting an evaluation. Different state hashes
   are expected for different documents; unexplained question or context changes
   make a claimed improvement incomparable.
4. Check whether each model judgment points to a defect supported by the actual
   document and sources. Give a concrete evidence-based reason for the final
   edit; do not subtract vague absolute scores to declare a winner.

Successful input processing yields these report parts:

| Field | Interpretation |
|---|---|
| `schema_version`, `rubric_version`, `rubric_sha256`, `advisory` | Report format, exact rubric identity, and advisory nature |
| `analysis` for analyze; `before` and `after` for compare | Deterministic `metrics`, `sections`, `protected` inventories, parser details, and limitations |
| `selected_sections`, `not_selected` for analyze | Section selection coverage; section IDs derive from starting source line numbers |
| `preservation` for compare | Changed artifacts and lexical review signals; `meaning_preservation: not_established` explicitly withholds proof |
| `semantic` | Evaluation `status`, per-request `reports` when prepared, and `not_reviewed` after a stopped sequence or budget failure |
| `acceptance` for compare | Always `requires_evidence_review`; no automatic acceptance |
| `link_validation` | Opt-in local file/anchor checks; compare includes `before` and `after` at one logical document path |

The top-level `status` follows semantic status, so `skipped` can accompany useful
static analysis. `preview` means no helper or provider call occurred. `skipped`,
missing answers, failed calls, and incomplete coverage supply no favorable
evidence. An evaluated response establishes that the consultation ran, not that
the candidate passed. Exit 0 includes skipped and preview reports; exit 1 means
the selected document (revised for compare) has broken local links; exit 2 means
incomplete semantic review or invalid inputs and takes precedence over link failure.
Invalid inputs can return only error metadata. A skipped or failed
request stops the remaining calls without retries; inspect `not_reviewed`.

Preview reports retain the exact request and `questions_sha256`; successful Jev
reports also carry the general helper's raw response and reproducibility fields.
Field names belong to their respective report formats: do not assume preview
metadata includes a provider response or every successful-call hash.

A boolean probability estimates the model's support for the particular question.
It is not an issue count, severity scale, or proof. A 0.95 or 0.98 cutoff has no
universal validity. Preserve explicit uncertain or insufficient-evidence outcomes
and investigate them when they affect the user's decision. One uncertain score
does not justify deleting correct but complex content.

Inspect dimensions separately. A finding about unsupported authority or changed
behavior may influence several answers; it does not establish that every
dimension failed independently. For a `gap` versus `needs_context` disagreement,
check the section purpose and missing evidence before editing. Retrieve the
needed evidence or preserve the explicit unknown; do not fill it with plausible
prose. A supported statement in one draft can still lack authority to replace a
conflicting requirement in another.

Set a small bounded attempt budget, normally one analysis per selected candidate
and one paired comparison. Fix a specific supported defect before another
attempt. Report transient failures as failures; do not repeatedly sample an
unchanged request, hide conflicting responses, or tune wording until the model
prefers the desired answer.

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
facts, skipped semantic evaluation, or limited scope that affects the conclusion.
Edit only the requested documents and directly necessary references. Do not
create additional policy, acceptance thresholds, or recurring jobs as a side
effect of a document edit.

When evaluating this workflow itself, freeze representative cases and expected
outcomes before tuning questions; keep held-out cases blind. Compare the agent's
decision before and after consultation against source evidence or independent
labels. Include an unassisted second-pass control to distinguish consultation
from rereading. Record review time when available without treating elapsed tool
time as a matched cost experiment. Count useful corrections, harmful changes, unchanged decisions, missing
answers, and failures. Report bounded attempts and coverage. An earlier
code-comment pilot showed no incremental gain; that does not establish either
benefit or failure for Markdown. Demonstrate value on document tasks before
adopting model judgments as a recurring acceptance mechanism.

## Recorded validation snapshot

On 2026-09-22, the frozen ten-case Markdown pilot passed 28/30 semantic
expectations. All five harmful rewrites were rejected; two safe improvements
were judged equivalent. A blind agent-only/assisted comparison matched all
30 labels both ways, with no changed decisions. This is useful preservation
regression evidence, not proof of added accuracy over the agent or broad
document quality. The source checkout records raw results and limitations in
`notes/doc-quality/`. Provider aliases and probabilities may change.

The 1.1.0 follow-up improved the unchanged original regression to 30/30. An
independent repository-excerpt challenge scored 28/30 (all ten version
preferences matched), and eight profile cases scored 12/13. A blind reviewer
scored 28/30 before consultation, on an unassisted second pass, and after Jev;
no scored incremental accuracy was observed. Two additional changed dimensions
were not pre-labeled and remain exploratory. Three HTTP 503 attempts were retained
and manually retried once each; successful responses were never resampled.
These bounded results support advisory use and do not justify automatic acceptance.

Question design follows TypeSafe's [Score](https://docs.typesafe.ai/primitives/score),
[Noul](https://docs.typesafe.ai/primitives/noul), and
[confidence](https://docs.typesafe.ai/confidence) guidance. Parsing uses
[markdown-it-py](https://markdown-it-py.readthedocs.io/en/latest/using.html).
Heading IDs use the pinned [github-slugger](https://pypi.org/project/github-slugger/)
port; the report names this profile rather than claiming every Markdown renderer
uses it.
The `#top` fallback follows the HTML standard's
[fragment navigation](https://html.spec.whatwg.org/multipage/browsing-the-web.html#the-indicated-part-of-the-document)
rule after explicit anchor lookup.
