# Codex CLI non-interactive reference

Verified against the Codex CLI source (`codex-rs/exec/src/cli.rs`,
`codex-rs/utils/cli/src/shared_options.rs`) at codex-cli 0.142.x. This covers
only what's needed to drive Codex headlessly from Claude Code; run
`codex exec --help` to re-verify on a newer version.

## Contents

- [codex exec](#codex-exec)
- [Sandbox modes](#sandbox-modes)
- [Capturing output](#capturing-output)
- [codex review](#codex-review)
- [codex exec resume](#codex-exec-resume)
- [Config](#config)
- [Recipes](#recipes)

## codex exec

```
codex exec [OPTIONS] [PROMPT]
```

The prompt is a positional argument; use `-` (or pipe with no prompt) to read
it from stdin. If stdin is piped *and* a prompt argument is given, stdin is
appended as a `<stdin>` block — useful for attaching a diff or file to a
task description.

Key options (shared with the interactive CLI):

| Flag | Meaning |
|------|---------|
| `-m, --model <MODEL>` | Override the config default model for this run |
| `-s, --sandbox <MODE>` | `read-only`, `workspace-write`, or `danger-full-access` |
| `-C, --cd <DIR>` | Working root for the agent |
| `--add-dir <DIR>` | Extra writable directories alongside the workspace |
| `-i, --image <FILE>` | Attach image(s) to the prompt |
| `-p, --profile <NAME>` | Layer `$CODEX_HOME/<name>.config.toml` over the base config |
| `-c key=value` | Ad-hoc config override (e.g. `-c model_reasoning_effort="high"`) |

Exec-specific options:

| Flag | Meaning |
|------|---------|
| `--json` | Print events to stdout as JSONL |
| `-o, --output-last-message <FILE>` | Write only the agent's final message to FILE |
| `--output-schema <FILE>` | JSON Schema the final response must conform to |
| `--skip-git-repo-check` | Allow running outside a git repository |
| `--ephemeral` | Don't persist session files to disk |
| `--ignore-user-config` | Skip `$CODEX_HOME/config.toml` (auth still works) |
| `--color always\|never\|auto` | Output color control |

Notes:

- **exec never prompts**: non-interactive runs hard-code approval policy to
  `never`; commands either run inside the sandbox or fail back to the model.
  The `approval_policy` config key only affects interactive sessions.
- `--full-auto` is **removed** (now a hidden warning trap); use
  `--sandbox workspace-write`.
- `--dangerously-bypass-approvals-and-sandbox` (alias `--yolo`) exists but
  should never be issued from an agent — if a task seems to need it, escalate
  to the user instead.
- `-c` values are parsed as TOML (falling back to literal string); dotted keys
  build nested tables.
- `codex e` is an alias for `codex exec`.

## Sandbox modes

- `read-only` — investigation, analysis, review. Codex can read the repo but
  not write or run mutating commands. **This is the default when `-s` is
  omitted.**
- `workspace-write` — implementation. Codex can edit files and run commands
  inside the working root (plus `--add-dir` paths).
- `danger-full-access` — no sandbox. Only for externally-sandboxed
  environments; never from a subagent.

## Capturing output

For programmatic capture, prefer `-o`:

```bash
codex exec -s read-only -o /tmp/codex-answer.md "<prompt>" && cat /tmp/codex-answer.md
```

This yields just the final message without the event stream. For structured
results, combine `--output-schema schema.json` with `-o`. Use `--json` when
you need the full event stream as JSONL (one `ThreadEvent` per line:
`thread.started`, `turn.completed`, `item.completed`, …; the final answer is
the `agent_message` item).

## codex review

Non-interactive code review of the current repository. The top-level
`codex review` and `codex exec review` are equivalent — both route through
the exec (non-interactive) engine:

```
codex review --uncommitted          # staged + unstaged + untracked
codex review --base main            # diff against a base branch
codex review --commit <SHA> [--title "<title>"]
codex review "<custom review instructions>"
```

The four target forms are mutually exclusive, and **one is required** — with
no target, review errors out. The review model can be overridden with the
`review_model` config key.

## codex exec resume

Continue a previous non-interactive session with context intact:

```
codex exec resume --last "<follow-up prompt>"
codex exec resume <SESSION_ID> "<follow-up prompt>"
```

## Config

`~/.codex/config.toml` keys that matter for routing:

```toml
model = "gpt-5.5"                 # default model for all runs
model_reasoning_effort = "high"   # none|minimal|low|medium|high|xhigh|max|ultra (default: medium)
review_model = "gpt-5.5"          # model used by `codex review`
```

Profiles (`[profiles.<name>]` + `--profile/-p`) can bundle `model`,
`sandbox_mode`, `model_reasoning_effort`, etc. Per-call overrides beat config:
`-m` for model, `-c model_reasoning_effort="medium"` for effort.

Auth: `codex login` (ChatGPT plan OAuth), `codex login --with-api-key`
(key piped on stdin), or the `OPENAI_API_KEY` / `CODEX_API_KEY` env vars.

## Recipes

Investigation (read-only, capture answer):

```bash
codex exec -s read-only -o /tmp/answer.md \
  "Investigate how rate limiting works in /abs/path/repo. Report the entry
   points, the algorithm, and the config knobs, with file:line references."
```

Implementation (workspace writes, self-contained spec):

```bash
codex exec -s workspace-write -C /abs/path/repo \
  "Implement X in src/foo.py per this spec: ... Acceptance: tests in
   tests/test_foo.py pass via 'uv run pytest tests/test_foo.py'."
```

Review a branch (or the working tree with `--uncommitted`):

```bash
codex review --base master
```

Attach a diff from stdin:

```bash
git diff master... | codex exec -s read-only \
  "Review this diff for correctness bugs; the diff follows in <stdin>."
```
