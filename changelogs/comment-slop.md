# Changelog - comment-slop

All notable changes to the comment-slop skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.4.0] - 2026-08-28

### Added
- First `references/` file (progressive disclosure): `references/docstring-conventions.md` carries the full docstring-rewrite convention developed under production review — the deeper ASD-STE100 subset (complete-sentence rule with approved-verb leads, ~25-word/6-sentence caps, approved senses that reject metaphors like *consult*/*answer*/*apply*, no `-ing` forms, no double negation, no coined prefix compounds, no inverted word order), the per-sentence body-scope test (every docstring sentence must be verifiable from that function's body alone) with the five rejected claim shapes and its boundary case, plus process notes (rewrite per function on request, verify claims against the pinning test before writing, one rewrite per commit)
- "What a docstring must state" section: the four gaps that recur once slop is gone, each a fact the signature cannot carry — tuple-return positional meanings, boolean polarity (especially when the body computes by negation), silent defaults and fallbacks (each undocumented branch gets its own sentence), and one word for one concept across sibling functions. Mode 4's pass conditions stated generatively
- Mode 1 gains the precondition fix pattern (a wrong-layer sentence justifying a gate is replaced with the precondition the body checks, not reworded) and the scope boundary: describing how the function's own return is derived stays in scope even when a private helper does the arithmetic; claims about elsewhere in the system do not
- Mode 5 extended to historical claims — the backward mirror of forward references: "that tier never dropped" is about past config nothing in the code can confirm; state the condition the body checks instead
- "The what belongs in the code" gains the paraphrase-of-constant case: a docstring describing a constant's value instead of naming it ("the categories whose default dropped to thirty days") is the same failure one level up — a named constant is checkable in place, a paraphrase is trusted
- Style section gains the complete-sentence rule (no verbless noun-phrase summaries — "Whether X applies…" leads with a verb instead) and the no-double-negation rule, with a closing pointer to the full convention in references/
- Workflow step 3 extends the verify-before-preserving bar to claims you write: a factual docstring sentence is written only after reading (or running) the test that pins it, not from memory of the code

### Changed
- Frontmatter description adds the docstring-completeness trigger (writing or reviewing docstrings for tuple-return meanings, boolean polarity, silent defaults and fallbacks)

## [1.3.0] - 2026-08-11

### Added
- The familiar why/what/how rule stated as the folk form of the three-clause test: descriptive names already tell the reader the what and the body is the how (both fail clause 2 when restated), so comments are reserved for the why the code cannot state — outside context, the business rule being implemented, the design decision that looks wrong until explained. With the compass-not-verdict caution: a why-shaped sentence still fails when it sits at the wrong layer or restates a documented convention
- "The what belongs in the code": the generative ordering (make the code state the what via names, extracted variables, and named constants, then comment only the why that survives) and its audit-side inversion — a what-comment that resists deletion is evidence the code under it is unclear, and the fix is rename/extract/name-the-constant plus delete, not a keep. Bounded on both sides: a rename is a code change committed separately from the docs-only cleanup, and only the what moves into names — "the code documents itself" never licenses deleting a why

### Changed
- The verdict default flips to delete: the burden of proof sits on the comment, a keep must name the keep-table fact the code cannot state, and doubt is not a pass. The former keep-when-torn asymmetry survives only in its narrow real case — a comment asserting a rationale, ordering constraint, or trade-off that cannot be cheaply verified; a restatement of the visible never qualifies
- Keep table: the external-context row names business rules explicitly
- Frontmatter description adds the deciding-whether-new-code-needs-a-comment trigger

### Fixed
- marketplace.json description brought back under the schema's 500-character cap (the v1.2.0 description was 591 characters, which made `make validate-strict` fail); the trigger list stays, the feature inventory moves to SKILL.md and this changelog

## [1.2.0] - 2026-08-11

### Added
- "Abstracting is not the fix either": names the second failed-repair pattern — a rewrite that swaps a comment's concrete anchors (who acts, through what mechanism, on what) for a citation of the general convention. A why-shaped fact survives casual inspection but fails clause 3 wherever the convention has a documented home. Built from the same review site as the trimming example, whose repaired wording drew a second review flag one round later in its abstracted form
- Mode 1 gains the sibling paste-test heuristic: a comment equally true pasted onto every neighboring declaration documents the architecture, not this code — its home is the module docstring or the convention doc, not one method among the many it applies to
- The rewrite verdict now requires re-running the three-clause test (noun heuristic first) on the rewrite's output — both documented repair failures are rewrites whose output stopped passing
- The caution that resemblance to one of the skill's own examples is not a verdict: examples locate a failure mode, only the test decides

### Changed
- Intro names generalizing alongside shortening as the transforms that make slop worse
- Frontmatter description adds the repeat-flag trigger (a comment a previous cleanup pass already rewrote)

## [1.1.0] - 2026-08-07

### Added
- "Style for what survives (ASD-STE100)" section: a second-pass wording standard for rewritten comments (and any newly written comment text), applied only after content selection — short sentences with one idea each, active voice with a named actor (mode 1's layer question), present tense for behavior / conditional for guards (mode 6), one-term-one-meaning tied to the code's identifiers (mode 3), and no filler openers or intensifiers. Kept comments stay untouched by default; restyle a keep only when its wording is bad enough to slow the reader. The override rule makes it safe against the skill's own trimming failure: a style edit may not delete a fact — when a rule and a fact collide, the fact wins

### Changed
- The rewrite verdict now covers partial redundancy: a comment wrapped in redundant restatement is *reduced* — the clauses that fail the three-clause test are deleted and the ones that pass are kept, with the distinction spelled out that reduction is selection by the test, not compression
- "Trimming is not the fix" now hands off to the style section: wording edits after the keep-or-delete decision include applying the style rules, not just fixing the layer, the mood, or an undefined term
- Frontmatter description adds the reduce/simplify/restyle-to-ASD-STE100 triggers

## [1.0.1] - 2026-08-07

### Fixed
- Diff commands no longer hardcode `master` as the base branch: a `base=main` variable (with a comment that it is the branch the PR targets) feeds all three commands, so they copy-paste correctly on `main`-based repos
- Repaired a garbled test in the "What to keep" table — "Is the invariant unenforceable to see from one function?" → "Is the invariant impossible to see from one function?"

### Changed
- Documented the blind spots of the added-comment inventory grep: it only matches lines that start with a comment marker, so trailing comments (`x += 1  # why`) and docstring body lines are under-counted — treat it as a starting list, with the full-diff read in step 2 catching the rest

## [1.0.0] - 2026-08-07

### Added
- Initial skill: find and remove AI-slop comments from a code change while protecting the comments that carry real reasoning
- Three-clause test a comment must pass to earn its place — the fact it states must be true at *this* layer, not already visible in the code in front of the reader, and not stated better nearby (signature, module docstring, test name, or the next line). Every failure mode is one clause failing
- Seven-mode taxonomy drawn from a production review, with the real code and the reviewer's actual reaction: wrong layer (a docstring describing the resolver's behavior one layer up — "the comment mentions a package and I don't see a package here"), redundant with the adjacent line (prose restating the TODO below it — "Seems like a useless AI comment?"), undefined term at point of use ("unsealed" — the negation of a term defined 200 lines above, whose fix was deletion rather than definition because the query already encoded the concept), restating the signature, forward references and planning artifacts (phase/step labels, ticket IDs, future-service references), prose that contradicts the code (present-tense claims about what a guard exists to prevent — fixed with the conditional mood), and narrating the code
- "What to keep" table plus the asymmetry that governs the pass: deleting a load-bearing comment costs more than leaving a bland one, so keep when genuinely torn. Six keep-signals (non-obvious approach, race/lock/ordering, invariant and its enforcement, external system or spec context, deliberate trade-off, guard that looks removable) with two verbatim examples that pass and are not short
- "Trimming is not the fix": a style pass constrains sentence *structure* and cannot do content *selection*, so simplified-English rules applied to a comment with real content strip the *why* and leave bland declaratives that read exactly like AI filler — with the before/after of a real comment that drew no review until it was trimmed, then was flagged as slop. The judgment a mechanical pass cannot make: a comment that survives trimming with only obvious statements left should be deleted, not shortened
- Six-step workflow: scope to the diff (`git diff <base>...HEAD`, with an added-comment inventory command) → read the code the comment sits on, never judging from a grep hit → verify the comment's claim against the code before preserving it (a comment may simply be stale, and a false comment is worse than an empty one) → one keep/rewrite/delete verdict per comment → rewrite rather than delete docstrings that feed generated API docs → commit the cleanup separately so it diffs to comment lines only
