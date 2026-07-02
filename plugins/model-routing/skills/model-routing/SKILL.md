---
name: model-routing
description: Install and maintain a "model routing" section in a project's CLAUDE.md that teaches Claude Code which model to use for which work — including delegating to GPT models via the Codex CLI. Use when the user wants to add model-picking guidance to CLAUDE.md, set up Codex/GPT as a delegation target or fallback, route subagent and workflow tasks across models by cost/intelligence/taste, or says "add model routing", "use codex as fallback", or "set up multi-model workflows".
---

# Model Routing

## Overview

Claude Code orchestrates subagents and workflows, and each spawned agent can
run on a different model. Left unguided, everything runs on the session's
default model — usually the most expensive one. This skill installs a
**model-routing section** into a project's CLAUDE.md: a rankings table
(cost / intelligence / taste per model) plus application rules and mechanics,
so the orchestrating Claude routes each piece of work to the cheapest model
that clears the quality bar — including non-Claude models reached through the
Codex CLI.

The pattern (popularized by Theo's multi-model workflow:
[x.com/theo/status/2072481845363822914](https://x.com/theo/status/2072481845363822914),
[x.com/theo/status/2072482460122964067](https://x.com/theo/status/2072482460122964067)):
score each available
model on three axes, state routing rules as defaults-not-limits with standing
permission to escalate, and document the exact mechanics (`codex exec`,
Agent/Workflow `model` parameter) so routing actually happens instead of
staying aspirational.

## When to Use

- The user wants Claude Code to delegate bulk/mechanical work to a cheaper
  model (e.g. GPT via Codex) and reserve the expensive model for hard problems
- The user asks to add model-selection guidance to a project's CLAUDE.md
- The user is burning rate limits on token-hungry work (computer use,
  codebase analysis) that a cheaper model could absorb
- Setting up a new project that will use multi-model workflows or agent teams

## Prerequisites

- **Required**: none — a Claude-models-only routing section still works via
  the Agent/Workflow `model` parameter.
- **For GPT routing**: the Codex CLI (`codex --version`), authenticated
  (`codex login` or `OPENAI_API_KEY`). Check `~/.codex/config.toml` for the
  default `model` and `model_reasoning_effort`.

## Workflow

### 1. Discover the environment

```bash
codex --version                     # Codex CLI installed?
grep -E '^(model|model_reasoning_effort)' ~/.codex/config.toml
```

Also note which Claude models the harness exposes for the Agent/Workflow
`model` parameter (check the Agent tool's model enum in the current session —
e.g. `sonnet`, `opus`, `haiku`, `fable`).

### 2. Interview the user

The rankings are personal — cost especially, since it reflects subscription
headroom and rate limits rather than list price. Ask (briefly, with sensible
defaults offered):

- Which subscriptions/plans do they have, and which is closest to its limits?
- Any model they never want used? Any they consider effectively free?
- What kinds of work do they want delegated away from the expensive model?

### 3. Instantiate the template

Copy the section from
[references/claude-md-template.md](references/claude-md-template.md) and
customize the table rows, scores, rules, and mechanics per the interview and
discovery. Only reference models and commands that actually exist in the
user's setup.

### 4. Insert into CLAUDE.md

- Target the **project-local** `CLAUDE.md` at the repo root by default;
  use `~/.claude/CLAUDE.md` only if the user wants it globally.
- If a `## Picking the right models` (or equivalent) section already exists,
  **replace it in place** — don't append a duplicate.
- If CLAUDE.md doesn't exist, create it with just this section.
- Show the user the final section before or right after writing it.

### 5. Verify the mechanics

If GPT routing is enabled, smoke-test the delegation path end-to-end:

```bash
codex exec -s read-only "Reply with exactly: OK"
```

(Add `--skip-git-repo-check` if the target directory isn't a git repository —
codex refuses to run outside one by default.)

If this prompts for auth or fails, fix that now — a routing section that
references a broken command silently degrades to "use the default model for
everything".

## Codex CLI mechanics

For the exact flags (sandbox modes, output capture, model override, session
resume) see [references/codex-cli.md](references/codex-cli.md). The short
version:

| Task shape | Command |
|------------|---------|
| Investigation / analysis | `codex exec -s read-only "<self-contained prompt>"` |
| Implementation | `codex exec -s workspace-write "<spec>"` |
| Code review | `codex review --base <branch>` (or `--uncommitted`) |
| Capture final answer only | `codex exec -o /tmp/out.md "<prompt>"` |
| Different model per-call | `codex exec -m <model> "<prompt>"` |

Codex prompts must be **self-contained**: codex shares none of Claude's
conversation context, so include absolute paths, the full task spec, and
acceptance criteria.

## Troubleshooting

- **Routing never happens**: the section is guidance, not enforcement — it
  must live in a CLAUDE.md that's actually loaded (project root, or global).
  Verify with `/context` or by asking Claude what routing rules it sees.
- **Codex "fails" on implementation tasks**: `codex exec` never prompts for
  approval — commands either run inside the sandbox or fail. If it can't
  write files, the sandbox was `read-only` (the default); rerun with
  `-s workspace-write`.
- **Wrapper agents summarize instead of relaying**: the wrapper prompt must
  say "return the codex output verbatim as your final message".
