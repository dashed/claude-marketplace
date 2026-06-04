# Checklist File & Workflow

The checklist is the spine of a `/teach` session: a single dated markdown file that tracks every concept the human must confirm, updated **after every confirmed item**. This file is what makes the completion gate enforceable — the session is over only when every box is `[x]`.

## Table of Contents

- [Setup: create the checklist file](#setup-create-the-checklist-file)
- [Checklist file structure](#checklist-file-structure)
- [The three sections (with example items)](#the-three-sections-with-example-items)
- [The commit step](#the-commit-step)
- [Updating during the loop](#updating-during-the-loop)
- [The completion gate](#the-completion-gate)

## Setup: create the checklist file

After the session source is resolved (see [session-sourcing.md](session-sourcing.md)):

1. **Derive a slug** from the topic or filename (kebab-case, e.g. `auth-token-refresh`).
2. **Get the current date:**
   ```bash
   TZ="America/New_York" date +"%Y-%m-%d"
   ```
   (Adjust the timezone to your own.)
3. **Create the checklist file** at a location that fits the project:
   ```
   sessions/teaching/YYYY-MM-DD-<slug>.md
   ```
4. **Populate it** with concrete, specific items extracted from the session — not generic placeholders (see structure below).
5. **Commit it** (see [The commit step](#the-commit-step)).
6. **Post the file path**, then begin the teaching loop.

## Checklist file structure

```markdown
---
mode: solo | teaching
student: <name, if teaching mode>
source: <topic or file path>
started: <ISO date>
---

# Teaching: <session title>

## Progress: 0/<total> concepts confirmed

### The Problem
- [ ] <the concrete problem this session tackled>
- [ ] <the reason it existed in the first place>
- [ ] <the branches/approaches weighed before deciding>

### The Solution
- [ ] <the resolution that was implemented>
- [ ] <why this path beat the alternatives>
- [ ] <the design decisions that shaped it>
- [ ] <the edge cases it accounts for>

### Broader Context
- [ ] <what this change touches downstream>
- [ ] <why it matters beyond the immediate fix>
- [ ] <what to keep an eye on afterward>

---
*Last updated: <timestamp>*
```

## The three sections (with example items)

Extract **specific, concrete** items from the actual session. The three sections mirror the persona prompt's "1) the problem 2) the solution 3) the broader context" (see [teaching-prompt.md](teaching-prompt.md)).

**The Problem** — what was broken/needed, why it existed, and what branches were considered.
- [ ] Token refresh failed silently after the access token expired mid-request
- [ ] Why it existed: the retry path never re-read the refreshed token from storage
- [ ] Branches considered: refresh-ahead-of-expiry vs. refresh-on-401

**The Solution** — how it was resolved, why this way, the design decisions, the edge cases.
- [ ] Resolved by intercepting 401s and replaying the request with a fresh token
- [ ] Why this approach: avoids a clock-skew dependency that refresh-ahead introduces
- [ ] Design decision: single-flight refresh so concurrent 401s don't stampede
- [ ] Edge case: refresh-token expiry forces a full re-login, not another retry

**Broader Context** — what it impacts, why it matters, what to watch going forward.
- [ ] Impacts every authenticated API call, not just the one that surfaced the bug
- [ ] Matters because silent auth failures looked like flaky network errors in logs
- [ ] Watch for: refresh storms if the single-flight lock is ever bypassed

> These are illustrations of the *shape* and *specificity* expected — derive real items from the session being taught.

## The commit step

Commit the checklist so progress is durable across sessions:

```bash
git add sessions/teaching/YYYY-MM-DD-<slug>.md \
  && git commit -m "data(teaching): add <slug> teaching checklist" \
  && git push
```

(Push is optional and project-dependent; commit so the file and its later `[x]` updates are tracked.)

## Updating during the loop

- **Re-read the file before each exchange** to know the current state.
- The moment an item is confirmed, change `- [ ]` to `- [x]` in the file — **never batch** updates.
- Keep the `## Progress: N/<total>` line current, and note progress inline to the human (e.g. `5/11 confirmed`).
- Every 3–4 exchanges, surface the current checklist progress.

## The completion gate

- **Never offer to wrap up** until every item is `[x]`.
- When (and only when) all items are confirmed, surface "session complete," output the completed checklist, and offer to save a summary note.

**Credits:** session sourcing + checklist tracking by alexknowshtml, layered on the persona prompt (concept by Suzanne, shared by @trq212/ThariqS); ported to this marketplace.
