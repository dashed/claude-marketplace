# Session Sourcing

Before any teaching happens, `/teach` must turn a session into a readable narrative to teach *from*. There are three ways to resolve a source. **All synthesis is internal** — never narrate the grep / extract / synthesize process to the human. Resolve the source silently, write the checklist, then start teaching.

## Table of Contents

- [Mode 1: Topic search (default)](#mode-1-topic-search-default)
- [Mode 2: Direct file path](#mode-2-direct-file-path)
- [Mode 3: No argument — recent sessions](#mode-3-no-argument--recent-sessions)
- [Narrative synthesis](#narrative-synthesis)

## Mode 1: Topic search (default)

Triggered by `/teach <topic keywords>` (anything that is not an existing file path).

1. **Search** the session transcripts for the topic across Claude Code's project history:
   ```bash
   grep -rli "<topic keywords>" ~/.claude/projects/ --include="*.jsonl"
   ```
   Claude Code stores one JSONL transcript per session under `~/.claude/projects/<encoded-project-path>/<session-id>.jsonl`.
2. **Rank by recency** — most recently modified first:
   ```bash
   ls -t $(grep -rli "<topic>" ~/.claude/projects/ --include="*.jsonl")
   ```
3. **Extract the key narrative** from the chosen transcript:
   - Pull **assistant** messages that describe findings, decisions, and conclusions.
   - Pull **user** messages that give direction or confirm outcomes.
   - **Skip tool-call noise and internal scaffolding** (tool inputs/outputs, thinking blocks, system reminders).
4. **Disambiguate** — if several transcripts match strongly, show the top 3 with one-line summaries and ask the human to confirm which one.
5. **Synthesize** a readable narrative (see [Narrative synthesis](#narrative-synthesis)) to use as the teaching source.

> **No matches?** If the search returns zero transcripts — or `~/.claude/projects/` is empty or absent — say so plainly and fall back to [Mode 3](#mode-3-no-argument--recent-sessions) (offer the recent-session list). Never fabricate a session to teach from.

> JSONL transcripts are line-delimited JSON objects. Each line typically has a `type`/`role` and a `message` with `content`. Filter to human/assistant text content and drop `tool_use` / `tool_result` blocks when extracting the narrative.

## Mode 2: Direct file path

Triggered by `/teach <path/to/file>` when the argument is an existing file. Read the file directly — no search step. Supported formats:

- **`.jsonl`** — a raw session transcript (extract narrative as in Mode 1, step 3).
- **`.md`** — already-readable material: meeting notes, a processed session export, a PR description, or design doc. Use it as-is.

The `--student <name>` flag may accompany any mode; it switches the loop to teaching mode (see `SKILL.md`) but does not change how the source is resolved.

## Mode 3: No argument — recent sessions

Triggered by a bare `/teach`. List the **10 most recently modified** sessions and ask which one to teach:

```bash
ls -t ~/.claude/projects/**/*.jsonl 2>/dev/null | head -10
```

Present them with a short human-readable hint (project + rough topic + recency) and let the human pick. Then proceed as in Mode 1, step 3.

## Narrative synthesis

From the extracted messages, write a **500–1000 word** narrative that reads like a clear story of the session:

- What problem prompted the work, and why it mattered.
- The key decisions made and the reasoning behind them.
- Alternatives or branches considered and why they were rejected.
- How it was resolved, including notable edge cases.
- What the change impacts and what to watch going forward.

This narrative is the raw material from which the **Problem / Solution / Broader Context** checklist items are drawn (see [checklist-and-workflow.md](checklist-and-workflow.md)). Keep it internal — the human sees the checklist and the questions, not the synthesis.

**Credits:** session sourcing by alexknowshtml, layered on the persona prompt (concept by Suzanne, shared by @trq212/ThariqS); ported to this marketplace.
