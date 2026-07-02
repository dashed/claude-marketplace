# Model-Routing Section Template

Pattern source: Theo's multi-model CLAUDE.md workflow —
[x.com/theo/status/2072481845363822914](https://x.com/theo/status/2072481845363822914),
[x.com/theo/status/2072482460122964067](https://x.com/theo/status/2072482460122964067).

Instantiate this template into the target project's CLAUDE.md (or the user's
global `~/.claude/CLAUDE.md` if they want it everywhere). The section below is
a working default for a setup with a Claude Code subscription plus the Codex
CLI defaulting to a GPT model. Before inserting, customize it with the user —
do not paste it unmodified:

- **Table rows**: one per model the user can actually reach. Drop rows for
  models they don't have; add rows (e.g. Gemini via another CLI) if they do.
- **Cost scores**: cost reflects what the user *actually pays* — subscription
  headroom and rate limits, not list price. This is personal; ask. The
  defaults below assume a separate high-headroom GPT plan makes gpt-5.5
  effectively free; for a Claude-subscription-only user the cost column
  inverts.
- **Intelligence/taste scores**: reasonable defaults are below, but let the
  user adjust from their own experience.
- **Rules**: keep only rules the user endorses. Bans like "Never use Haiku"
  and thresholds like "taste ≥ 7" are opinions, not facts. A ban may
  reference a model deliberately left out of the table — that's fine; the
  ban is what keeps it out.
- **Mechanics**: verify the Codex CLI is installed (`codex --version`) and
  which model `~/.codex/config.toml` defaults to (`model = "..."` key).
  Reference only tools and skills that exist in the user's setup.

---

## Picking the right models for workflows and subagents

Rankings, higher = better. Cost reflects what I actually pay (subscription
headroom and rate limits), not list price. Intelligence is how hard a problem
you can hand the model unsupervised. Taste covers UI/UX, code quality, API
design, and copy.

| model    | cost | intelligence | taste |
|----------|------|--------------|-------|
| gpt-5.5  | 9    | 8            | 5     |
| sonnet-5 | 5    | 5            | 7     |
| opus-4.8 | 4    | 7            | 8     |
| fable-5  | 2    | 9            | 9     |

How to apply:

- These are defaults, not limits. You have standing permission to override
  them: if a cheaper model's output doesn't meet the bar, rerun or redo the
  work with a smarter model without asking. Judge the output, not the price
  tag. Escalating costs less than shipping mediocre work.
- Route each task to the **cheapest model that clears its quality bar**. Cost
  is a tie-breaker only: when it's unclear whether a cheaper model clears the
  bar for anything that ships, intelligence > taste > cost — don't trade
  correctness for price.
- Bulk/mechanical work (clear-spec implementation, data analysis, migrations):
  gpt-5.5 — it clears the bar and it's effectively free.
- Anything user-facing (UI, copy, API design) needs taste ≥ 7.
- Reviews of plans/implementations: fable-5 or opus-4.8, optionally gpt-5.5 as
  an extra independent perspective.
- Unnecessarily token-hungry work (computer use, whole-codebase analysis) goes
  to gpt-5.5 via Codex; have it report conclusions back instead of burning
  Claude context on raw exploration.
- Never use Haiku.
- Mechanics: gpt-5.5 is only reachable through the Codex CLI — `codex exec` /
  `codex review` (my `~/.codex/config.toml` defaults to gpt-5.5). For
  investigation and data analysis run `codex exec -s read-only` with a
  self-contained prompt; for implementation run
  `codex exec -s workspace-write`; for code review run
  `codex review --base <branch>` or `codex review --uncommitted`. Capture
  just the final answer with `-o <file>` when you need programmatic output.
- Claude models (sonnet-5, opus-4.8, fable-5) run via the Agent/Workflow
  `model` parameter.

Using gpt-5.5 inside workflows and subagents (the `model` parameter only takes
Claude models, so use a wrapper):

- Spawn a thin Claude wrapper agent on the cheapest Claude model
  (`model: 'sonnet'`; in Workflow `agent()` steps also pass `effort: 'low'` —
  the Agent tool has no effort parameter) whose prompt instructs it to write
  a self-contained codex prompt, run `codex exec` via Bash, and return the
  codex output verbatim as its final message — no summarizing, no
  second-guessing.
- The codex prompt must be self-contained: codex shares none of the
  conversation's context. Include absolute file paths, the exact task spec,
  constraints, and acceptance criteria.
- Pick the sandbox to match the task: `-s read-only` for
  investigation/review, `-s workspace-write` for implementation. Never
  `danger-full-access` from a subagent.
