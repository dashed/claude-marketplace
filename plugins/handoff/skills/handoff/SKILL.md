---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up. Use when ending a session with unfinished work, transferring context to a fresh agent or a new session, approaching context limits, or when the user says "handoff", "write a handoff doc", or "continue this in another session".
argument-hint: "What will the next session be used for? [--workspace]"
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS by default - not the current workspace. If the user passes `--workspace` (or asks for the document in the workspace), save it to the workspace root as `HANDOFF.md` instead; leave it untracked and do not commit it unless asked.

Include a "suggested skills" section in the document, which suggests skills that the agent should invoke.

Do not duplicate content already captured in other artifacts (PRDs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
