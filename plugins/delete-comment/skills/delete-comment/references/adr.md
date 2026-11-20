# Moving decision records into ADRs

An architecture decision record (ADR) is a short Markdown file that records one decision: the forces behind it, the decision itself, and its consequences. When a comment that records a decision is deleted, its fact moves here, unless a name, a type, an assertion, or a test can carry it (see SKILL.md, "Decision records").

## Contents

- [Where ADRs live](#where-adrs-live)
- [Template](#template)
- [Recover the decision's history](#recover-the-decisions-history)
- [Writing rules](#writing-rules)
- [Keep ADRs findable without comments](#keep-adrs-findable-without-comments)
- [Example](#example)

## Where ADRs live

Use the repository's existing ADR directory and its conventions. Look for, in this order: `docs/adr/`, `doc/adr/` (adr-tools), `docs/decisions/` (MADR), `docs/architecture/decisions/`, `adr/`. If one exists, copy its template, its file names, its numbering, and its index (a `README.md` or `index.md` that lists the records). Do not introduce a second format.

If none exists, create `docs/adr/` with:

- `0001-keep-decisions-in-adrs-not-code-comments.md`: the decision to ban comments, which the ratchet's failure message can point to
- a `README.md` index: one line per ADR with its number, title, status, and the paths it governs

File names are `NNNN-title-in-kebab-case.md`, numbered in sequence. Numbers are never reused.

## Template

```markdown
# NNNN. <The decision, as a short imperative phrase>

- Status: Accepted
- Date: YYYY-MM-DD (the day the ADR is written)
- Governs: `path/to/file.py` (`ClassName.method`), `path/to/other.ts` (`functionName`)
- Recovered from: a code comment removed in <commit or PR>; introduced in <commit> (<date>)

## Context

The forces that make the obvious alternative wrong: the outside system's behavior, the
incident, the requirement, the measurement. Quote the original comment word for word.

## Decision

The rule a change must keep, stated so that a reader can check code against it.

## Consequences

What a change must preserve. What breaks if someone removes or "simplifies" the code, and
which test fails when they do. The cost that was accepted.
```

Write `Status: Accepted` for a decision the code already implements. Leave out the "Recovered from" line for an ADR that does not come from a comment.

## Recover the decision's history

The comment rarely carries the whole reason. Before you write the Context section, find the commit that added the comment and read its message and the pull request:

```bash
git log -S'a distinctive phrase from the comment' --oneline -- path/to/file.py
git log -L '/def retry_upload/,+20:path/to/file.py' --oneline
git blame -L 40,46 path/to/file.py
```

`-S` (the pickaxe) finds the commit that added or removed the text; `-L` follows a function or a line range through history. Quote what the commit message or the pull request adds. When neither adds anything, say so in the Context section; do not invent a reason.

## Writing rules

- **One decision per ADR.** Merge comments that record the same decision at several sites; list every site under "Governs".
- **The rule, not the implementation.** "Upload retries stop after two attempts" stays true through a refactor; "the loop in `upload()` runs twice" does not. An ADR that narrates the code goes stale like the comment it replaced.
- **Symbols, not line numbers.** Name the file and the function, class, or constant. Line numbers change with every edit.
- **Never edit a decision.** When a later change reverses it, write a new ADR, mark the old one "Superseded by NNNN", and link both ways. The chain answers "why is it like this" years later.
- **Short.** Most recovered decisions fit in fifteen lines. If an ADR needs a page, it is probably two decisions.
- **Review it.** Use the doc-quality skill, if it is installed, to check the sections and the links.

## Keep ADRs findable without comments

With comments banned, the code can no longer point to its ADR. Use all three of these:

1. **The index lists the governed paths.** A reader who opens `src/upload.py` finds its ADRs with `grep -rl 'src/upload.py' docs/adr`.
2. **Agent instructions say where to look.** Add one line to `AGENTS.md` or `CLAUDE.md`: "Before changing a file, search `docs/adr/` for its path and follow the ADRs that govern it."
3. **Tests carry the link.** A test that protects a decision can name the ADR in its module docstring or its name. Docstrings are not comments, so the ratchet allows them.

If the team prefers pointers in the code, allow them in the ratchet config with a narrow pattern, for example `"allow": ["^\\W*ADR-\\d{4}$"]`, so that a comment holding only `# ADR-0007` passes and nothing longer does. That is a policy choice; ask the user before you add it.

## Example

The comment:

```python
def upload(chunk: bytes) -> None:
    # Retry at most twice: the storage vendor blocks the client after a third
    # failed attempt within a minute (support ticket, 2025).
    for attempt in range(2):
        ...
```

First, try to encode it: `MAX_UPLOAD_ATTEMPTS = 2` carries the number, and `test_upload_gives_up_after_two_attempts` carries the behavior. The reason, a vendor ban after the third attempt, fits neither, so it goes to an ADR:

```markdown
# 0007. Stop upload retries after two attempts

- Status: Accepted
- Date: 2026-11-20
- Governs: `src/storage/upload.py` (`upload`, `MAX_UPLOAD_ATTEMPTS`)
- Recovered from: a code comment removed in #412; introduced in a1b2c3d (2025-03-14)

## Context

The storage vendor blocks a client for ten minutes after a third failed upload within one
minute. The removed comment said: "Retry at most twice: the storage vendor blocks the
client after a third failed attempt within a minute (support ticket, 2025)." Commit a1b2c3d
links the support ticket.

## Decision

`upload` makes at most two attempts per chunk.

## Consequences

A third attempt locks every upload for ten minutes, which is worse than failing one chunk.
`test_upload_gives_up_after_two_attempts` fails if the limit rises. A transient error that
outlasts two attempts fails the chunk; the caller's job retry handles it later.
```

The verdict for the comment then gets `"ref": "docs/adr/0007-stop-upload-retries-after-two-attempts.md"`, and `delete` removes it.
