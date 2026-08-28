# Docstring rewrite conventions: STE-100 wording, body-scoped claims

The full convention behind the skill's rewrite verdict, developed while
rewriting production billing docstrings under review. Two rules govern every
rewritten or freshly written docstring; they are independent — one constrains
*how* a sentence is written, the other *what* it may claim — and each rewrite
is checked against both.

**Ordering still applies.** Content selection (keep / rewrite / delete, the
three-clause test) runs first. These conventions govern only the output of a
rewrite and docstrings you write fresh — applied to a comment that has not
passed selection, Rule 1 is exactly the mechanical trimming pass the skill
warns against.

## Contents

- [Rule 1 — Write to ASD-STE100](#rule-1--write-to-asd-ste100-simplified-technical-english)
- [Rule 2 — Scope every claim to the body it sits in](#rule-2--scope-every-claim-to-the-body-it-sits-in)
- [What a docstring must additionally state](#what-a-docstring-must-additionally-state)
- [What survives untouched](#what-survives-untouched)
- [Process notes](#process-notes)

## Rule 1 — Write to ASD-STE100 (Simplified Technical English)

SKILL.md's style section is the short form. This is the subset of STE-100
that actually bites in docstrings:

- **Complete sentences.** The conventional verbless noun-phrase summary
  ("Whether the grandfathering applies…", "The category-less reads' days.")
  is out — STE forbids dropping words to shorten text. Lead with an approved
  verb: `Tell`, `Find`, `Serve`, `Give`, `Hold`, `Route`.
- **One idea per sentence.** Max ~25 words in descriptive text, max 6
  sentences per paragraph. Split "X, and Y, and Z" chains and semicolon/colon
  splices into one sentence per condition or branch.
- **Approved words in approved senses.** Metaphors fail: a read does not
  *answer*, a rule does not *follow*, code does not *consult* — and *apply*
  in STE means putting a substance on a surface. Prefer `set`, `change`,
  `keep`, `stop`, `include`, `must`, `give`.
- **Active voice, simple present, no `-ing` forms, keep the articles.**
- **No double negation.** "Neither consults nor pays for" → "does no legacy
  work and gets no legacy error."
- **No coined prefix compounds.** `pre-change days` → `the older retention
  days`.
- **No inverted word order.** "Only when X is empty too does the default
  answer" → one plain sentence per branch.

The skill's override rule holds here too: a style edit may not delete a
fact. When an STE rule and a fact collide, the fact wins.

## Rule 2 — Scope every claim to the body it sits in

This is the three-clause test's clause 1 (true at this layer) sharpened into
a per-sentence check for docstrings. Every sentence must be verifiable from
that function's body alone. The test: after drafting, check each sentence
against the body — **if verifying it means opening another function or
module, rewrite it** as a statement about this function's inputs,
conditions, or return value.

What this rejects, with the cases that shaped it:

- **Collaborator behaviour as rationale.** "An organization-level override
  sets the days for every category" explained an early-return gate — but the
  setting happens two functions away. Replaced with the precondition itself:
  "The contract must have no organization-level override." The reason moves
  out; the condition the body checks stays.
- **Claims about other modules.** "Mirrors the legacy read's rule" and
  "including the grandfathering the resolver decides" describe the legacy
  read and the resolver, not the documented function. (SKILL.md mode 1.)
- **Historical claims.** "That tier never dropped" is about past config;
  nothing in the body can confirm it. State the condition the body checks
  instead (`downsampled_days == THIRTEEN_MONTHS`). (The backward mirror of
  SKILL.md mode 5's forward references.)
- **Architectural role claims.** "This module is the only place the two
  systems meet" — a claim about the codebase, not the function. (The
  sibling paste-test: its home is the module docstring or convention doc.)
- **Paraphrases of constants.** "The categories whose default dropped to
  thirty days" → name `NEW_30_DAY_RETENTION_CATEGORIES`, the thing the body
  filters on. A named constant is checkable in place; a paraphrase is
  trusted.

The line, for the boundary cases: describing how the function's **own return
is derived** stays in scope even when a private helper does the arithmetic —
that is still a claim about this function's input-to-output contract. What is
out of scope is a claim about what happens *elsewhere in the system*.

## What a docstring must additionally state

Gaps that surfaced repeatedly once the prose was tightened — each a fact the
signature genuinely cannot carry:

- **Tuple returns**: which position is which, and what each value means. A
  bare `tuple[bool, bool]` explains nothing; "The first value is for the
  standard tier. The second value is for the downsampled tier. A value is
  true when the grandfathering includes that tier."
- **Boolean polarity**, especially when the body computes values by negation
  (`not _tier_overridden(...)`) — a reader scanning code sees the negation
  and cannot tell which polarity means what.
- **Silent defaults and fallbacks**: an `else 0`, a `fallback=` argument, an
  early-return of empty sets. Each undocumented branch gets its own sentence.
- **One word for one concept** across sibling functions (STE's consistency
  rule): a trio of related functions all say *includes*; a pair of
  tuple-returners both say *first value / second value*.

## What survives untouched

- **Why-comments with external justification.** A comment on a magic constant
  citing where the value comes from (another system's
  `DEFAULT_EVENT_RETENTION`, a downstream store's `DEFAULT_RETENTION_DAYS`)
  keeps its external pointers — that reference *is* the why, and removing it
  leaves an unexplained number. Split its sentences; keep its content.
- **Precision comments.** An inline comment nailing an exclusive-vs-inclusive
  boundary conversion is left alone rather than risk blurring it in
  rewording.
- **Interpretive glosses get cut, not reworded.** "These values are for the
  organization, not for one category" restated the summary; it was deleted.

## Process notes

- **Rewrite on request, per function** — not wholesale. The surrounding
  docstrings may still use the old style; say which ones remain inconsistent
  rather than silently converting the file.
- **Verify factual claims empirically before writing them.** A docstring
  sentence like "the override changes both values" is only written after the
  test pinning it is read (or run) — not from memory of the code.
- **Each rewrite is a separate commit**, verified by lint plus the module's
  test suite before committing.

## Origin

Developed across a chain of production billing PRs. Rule 2 was reviewer
feedback ("let's not have docstrings assume behaviour outside of the
function it's tied to") after a rewrite explained a gate by describing a
collaborator; the follow-up ("it doesn't seem to explain why it returns a
tuple of bools") produced the tuple-meaning requirement.
