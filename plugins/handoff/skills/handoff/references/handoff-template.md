# Handoff Document Template

Sections for a handoff document. Scale to the work — omit sections with nothing in them. Reference artifacts (PRDs, plans, ADRs, issues, commits, diffs) by path or URL; never duplicate their content.

## Header

- **Created**: ISO timestamp
- **Project**: repo name / path
- **Branch / commit**: branch @ short SHA
- **Dirty files**: `git status --short` output, or "clean"

## Goal

What the overall task is and why. One paragraph max; link the originating issue/PRD if one exists.

## Done

What is finished and verified. Reference commits/PRs rather than describing the code.

## In progress

The piece that was mid-flight when the session ended, and its current state.

## Next steps

Ordered list. Make the first action explicit enough to start cold ("Run X, then edit Y to do Z" — not "continue the work").

## Decisions & rationale

Choices made and *why* — especially ones that would look arbitrary or wrong without the context of this conversation.

## Dead ends tried

Approaches that failed and why, so the next agent doesn't re-explore them.

## Verify state

Exact commands to confirm the baseline before continuing (tests, build, running services), each with its expected result. If a command's outcome differs, the repo moved since the handoff — re-assess before following "Next steps".

## Suggested skills

Skills the next agent should invoke, and for what.

## Open questions

Anything blocked on user input or otherwise unresolved.
