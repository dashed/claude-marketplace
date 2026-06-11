---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up. Use when ending a session with unfinished work, transferring context to a fresh agent or a new session, approaching context limits, or when the user says "handoff", "write a handoff doc", or "continue this in another session".
argument-hint: "What will the next session be used for? [--workspace]"
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS by default - not the current workspace. Name it `handoff-<project>-<YYYY-MM-DD-HHMM>.md` so multiple handoffs coexist and sort chronologically. If the user passes `--workspace` (or asks for the document in the workspace), save it to the workspace root instead (same filename); leave it untracked and do not commit it unless asked.

Structure the document using [references/handoff-template.md](references/handoff-template.md). Scale sections to the work and omit empty ones — but always capture decisions-with-rationale and dead ends tried when they exist: those are the two things a fresh agent cannot recover from artifacts.

Anchor the document to verifiable state: timestamp, branch, commit SHA, dirty files, and the exact commands to re-verify the baseline (tests, build, running services) with their expected results. The repo may move between sessions — anchors make staleness detectable instead of silently misleading.

Include a "suggested skills" section in the document, which suggests skills that the agent should invoke.

Do not duplicate content already captured in other artifacts (PRDs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.

When finished, tell the user the full path of the document and give a ready-to-paste starter for the next session, e.g. `claude "Read /tmp/handoff-myrepo-2026-06-11-1430.md and continue"`.

## When NOT to use this

If the next session is on the same machine and the conversation is resumable, suggest `claude --resume`/`--continue` instead — a handoff doc earns its keep for cross-machine moves, post-compaction recovery, or agent-to-agent transfer. Durable facts (user preferences, environment quirks) belong in memory, not the handoff; carry only task state here.
