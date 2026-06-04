---
name: teach
description: Run a Socratic teaching loop that quizzes you on a coding session until you have confirmed mastery of every concept. Use when you want to learn or lock in what happened in a Claude Code session, understand a transcript, PR, or design decision, be quizzed/tested/drilled on recent work, or prepare to teach someone else — or when the user runs `/teach` or asks to be taught or quizzed on a topic. Sources sessions from ~/.claude/projects/, tracks a per-concept checklist (Problem / Solution / Broader Context), and never wraps up until every item is confirmed.
---

# Teach

A Socratic teaching loop for any Claude Code session: quiz the human on what actually happened, confirm mastery one concept at a time, and don't finish until everything is locked in. Invoked as `/teach`, it sources a session, builds a per-concept checklist, then drills — not just *what* happened, but *why* each decision was made and what it impacts.

The full behavioral spec lives in the persona prompt at [references/teaching-prompt.md](references/teaching-prompt.md) — treat that file as the source of truth for tone and quizzing behavior.

## When to Use

- You want to learn or lock in what happened in a recent Claude Code session
- You need to understand a transcript, PR, or design decision deeply
- You want to be quizzed, tested, or drilled on recent work
- You're preparing to teach the material to someone else
- The user runs `/teach` or asks to be taught/quizzed on a topic

## Prerequisites

- **Session history** — Claude Code transcripts under `~/.claude/projects/` (one `.jsonl` per session). Topic and no-argument modes search here; direct-file mode skips it.
- **`git`** — the checklist file is committed so progress persists across sessions. (Push is optional/project-dependent.)
- **A writable project** — the dated checklist lives at `sessions/teaching/YYYY-MM-DD-<slug>.md` within the current project.

## Usage Modes

| Invocation | Behavior |
|------------|----------|
| `/teach <topic keywords>` | Search session files by keyword, then solo quiz mode |
| `/teach <path/to/file>` | Read a specific transcript directly (`.jsonl` or `.md`), then solo quiz mode |
| `/teach <topic> --student <name>` | Teaching mode — help you walk *someone else* through the material |
| `/teach` (no argument) | List the 10 most recent sessions and ask which one to teach |

## How It Works

```
Source resolution  →  Setup (checklist file + commit)  →  Teaching loop
```

1. **Source resolution.** Resolve the session into a readable narrative — by topic search across `~/.claude/projects/`, by direct file path, or by picking from the 10 most recent. See [references/session-sourcing.md](references/session-sourcing.md).
2. **Setup.** Derive a slug, get the date, and write a dated checklist file at `sessions/teaching/YYYY-MM-DD-<slug>.md` with concrete Problem / Solution / Broader Context items, then commit it. See [references/checklist-and-workflow.md](references/checklist-and-workflow.md).
3. **Teaching loop.** Quiz the human one concept at a time, marking items confirmed in the file as you go (below).

**Source synthesis is internal** — never narrate the grep/extract/synthesize process. Just start teaching.

## The Teaching Loop

**Before each exchange,** re-read the checklist file to know the current state.

**Opening move:** ask the human to restate their understanding of the session in their own words. Calibrate from there — fill gaps, don't re-cover what they already have.

**Loop (solo mode, default):**
1. Pick the next unconfirmed item.
2. Ask one targeted question — open-ended or multiple choice. (For multiple choice: vary the correct answer's position; don't reveal the answer until after they respond.)
3. If correct: mark `[x]` in the file **immediately**, note running progress inline (e.g. `5/11 confirmed`), and move on.
4. If missed: explain, then re-ask in a different form before marking confirmed.
5. Every 3–4 exchanges: surface the current checklist progress.

**Drill into WHY.** Surface the motivation behind decisions, not just what was done. Ask follow-up *whys* before moving to the next item. Understanding the problem well is imperative.

**Completion gate.** Only surface "session complete" once every item is `[x]`. Final output: the completed checklist; then offer to save a summary note.

**Teaching mode (`--student <name>`)** flips the flow: instead of quizzing the human, help them structure a walk-through for someone else — for each section, suggest how to explain it and what questions to ask the student. Progress tracks what the human has covered *and* confirmed the student understood.

## Key Rules

| Rule | Detail |
|------|--------|
| One question at a time | No multi-part questions. |
| Update after every confirmation | Mark `[x]` in the checklist file the moment an item is confirmed — never batch. |
| 100% completion gate | Never offer to wrap up until the checklist is fully `[x]`. |
| Keep responses concise | Aim for under 2000 characters per exchange. |
| Match the difficulty | Explain at `eli5`, `eli14`, or intern level if asked. |
| Synthesis is silent | Don't narrate sourcing; begin teaching directly. |

## Credits

Original concept by Suzanne (Anthropic), shared by @trq212 (ThariqS); session sourcing + checklist tracking by alexknowshtml; ported to this marketplace.

## References

Progressive disclosure — load these for full detail:

- [references/teaching-prompt.md](references/teaching-prompt.md) — the verbatim original persona/quiz prompt (gendered original + gender-neutral they/them variant), the behavioral source of truth
- [references/checklist-and-workflow.md](references/checklist-and-workflow.md) — the dated checklist file format, the three sections with example items, the commit step, and the completion gate
- [references/session-sourcing.md](references/session-sourcing.md) — topic search across `~/.claude/projects/`, narrative synthesis, plus direct-file and no-argument modes
