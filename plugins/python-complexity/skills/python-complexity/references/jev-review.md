# Jev semantic complexity review

## Contents

- [Evidence and scope](#evidence-and-scope)
- [Configure and run a provider](#configure-and-run-a-provider)
- [Read the judgments](#read-the-judgments)
- [Compare and decide](#compare-and-decide)
- [Evaluation limits](#evaluation-limits)
- [Sources and implementation choice](#sources-and-implementation-choice)

## Evidence and scope

Jev review is optional. Without the selected provider's API key, complete the static analysis
and behavior checks, and report semantic review as skipped. Do not require the
user to configure credentials to finish a complexity review.

Use static tools to measure complexity; use Jev to judge the maintainability of
the code those measurements identify. The coding agent diagnoses the issue,
edits the code, and verifies behavior. Jev produces typed signals, not a refactor
or a prose explanation.

Start with one function and its necessary context, or one complete public call
path. Include relevant helpers, types, side effects, domain constraints, and the
invariants protected by layers. A diff alone can omit exactly the helper where
complexity moved. Select the files explicitly; the helper does not walk a
repository, read paths named in the JSON, or execute the reviewed code.

Record measurements from the existing census with tool versions, commands,
scope, and unresolved/missing coverage. Additional measurements belong to the
tool that actually computes them: parameter count/nesting to static analysis,
coverage to the test runner, mutation results to mutation tooling. Halstead and
Maintainability Index have Python blind spots documented in
[between-function-complexity.md](between-function-complexity.md); adding more
metrics does not automatically provide independent evidence. Do not ask Jev to
invent these numbers, churn, bug history, or absent test results.

The state file requires a nonempty `scope` and a `sources` array with `path` and
`content` strings. Additional fields hold the review's actual evidence:

```json
{
  "scope": "pricing.py:discount and its complete call path",
  "task": "Return a 10 percent discount for an active member; otherwise zero.",
  "constraints": ["Keep the public signature and return values."],
  "sources": [
    {
      "path": "pricing.py",
      "content": "def discount(active, member):\n    if active:\n        if member:\n            return 0.1\n    return 0.0\n"
    }
  ],
  "measurements": {"status": "not_run"},
  "missing_context": []
}
```

This example is a transport smoke test. For an actual refactor, fill
`measurements` with observed results and retain source revisions or content
hashes. The helper snapshots the submitted state; it does not authenticate
user-supplied measurements or verify that excerpts match files on disk.

## Configure and run a provider

Vercel is the default. Switch presets with `--provider typesafe`, or save a
non-secret config at `~/.config/typesafe-ai/jev-review.json`:

```json
{"provider": "typesafe"}
```

| Preset | Default model | Key variable | API protocol |
|---|---|---|---|
| `vercel` | `typesafe-ai/jev` | `AI_GATEWAY_API_KEY` | Gateway `/v1/evaluate` |
| `typesafe` | `jev-latest` | `TYPESAFE_API_KEY` | TypeSafe `/v1/systemone` |

The selected key is read from the process environment, then from
`~/.config/typesafe-ai/env`. Keep that file mode `600`; it may contain the keys
for several providers as separate literal assignments:

```sh
export AI_GATEWAY_API_KEY='your-gateway-key'
export TYPESAFE_API_KEY='your-typesafe-key'
```

Only the chosen provider's variable is read. A missing TypeSafe key does not
fall back to the Vercel key. `--env-file PATH` explicitly chooses a credential
file instead of the process environment. The parser does not execute shell
commands, expand variables, or source other files. Keys do not belong in the
config JSON, state, rubric, repository, or report.

CLI options override config values. `--config PATH` selects another config;
only the user config is auto-discovered, never a file from the repository being
reviewed. Selecting a different preset with `--provider` discards the previous
provider's config overrides, then applies that preset and explicit CLI options.

For another service exposing either supported evaluation protocol, use:

```json
{
  "provider": "custom",
  "endpoint": "https://your-provider.example/v1/evaluate",
  "protocol": "gateway",
  "model": "your-provider-jev-model-id",
  "api_key_env": "CUSTOM_JEV_API_KEY"
}
```

`endpoint` is the full HTTPS evaluation URL; `protocol` is `gateway` or
`typesafe`. `model`, `api_key_env`, and `env_file` are also configurable, with
corresponding CLI flags (`--api-key-env`, `--env-file`). Changing a preset's
host requires explicitly choosing its key variable. Both supported protocols
use Bearer authentication. A provider with a different authentication or
request/response contract needs an adapter; changing the URL alone is not
sufficient. No fallback to a different provider occurs automatically.

Resolve the helper relative to this skill's installation directory, regardless
of the repository under review. With `skill_dir` set to that absolute directory:

```sh
# Preview the exact request without reading a key or making a request.
uv run --no-project "$skill_dir/scripts/jev_review.py" --state before.json --dry-run

# Live review sends the selected source/context to the configured provider.
uv run --no-project "$skill_dir/scripts/jev_review.py" --state before.json > before-review.json
uv run --no-project "$skill_dir/scripts/jev_review.py" --state after.json > after-review.json

# Switch to direct TypeSafe for this run (uses TYPESAFE_API_KEY).
uv run --no-project "$skill_dir/scripts/jev_review.py" --provider typesafe --state before.json
```

Use live review when external semantic evaluation is within the user's task
and repository policy. Keep unrelated files and secrets out of the selected
state. Reports contain the submitted code, so store them with the same care as
the source. For a static-only task, run the existing censuses directly.

Run the helper with `uv run --no-project`; it uses Python 3.10+ and the standard
library. All rubric questions share one POST. The Gateway protocol uses
`boolean`/`probability`; the TypeSafe protocol uses `noul`/`noul`. The helper
adapts the request and validates the provider's response. Reports expose
provider-independent `answers` (Boolean probabilities use `probability`) and
retain the exact provider `response`, including model, usage, and metadata.

Exit `0` means a request preview, a structurally valid evaluation, or a skip,
**not a quality pass**. When the key is absent or empty, the helper returns
`status: skipped` with `reason: missing_api_key`, makes no network request, and
returns no semantic answers. Continue the static workflow. Exit `2` and
`status: incomplete` mean invalid input, malformed/unreadable credential
configuration, a network/API error with a configured key, or an invalid answer.
No scores are fabricated.
The helper has a 30-second timeout, refuses redirects, and does not retry.
Its 100,000-byte request bound is a local guard, not a token-limit estimate. Split
oversized input into coherent paths; never silently truncate necessary callees.

## Read the judgments

The versioned [rubric](jev-rubric.json) asks independent questions over the same
state. Every Score uses four concrete descriptions, ordered from worse to better:

| Signal | Meaning |
|---|---|
| `readability` | How directly the reader can follow the complete shown path |
| `responsibility_cohesion` | Whether units separate concerns that change for different reasons |
| `simplicity` | Whether the stated task needs the implementation's machinery (KISS) |
| `abstraction_quality` | Whether boundaries encapsulate meaningful decisions or invariants |
| `complexity_justified` | Probability the stated requirements need the visible complexity |
| `split_helpful` | Probability extraction helps after accounting for new indirection |
| `dominant_cost` | A candidate explanation category, including no problem and insufficient context |
| `context_sufficient` | A separate judgment about whether the shown context supports review |

Scores are positions from **0 to 3**, not percentages or probabilities of
correctness. Boolean probabilities range from **0 to 1**. Retain the distributions
and any returned confidence metadata; confidence describes concentration of the
answer distribution, not proof that the judgment is right. The Gateway may put
confidence in provider metadata instead of each answer.

The questions cannot see each other's answers. Interpret `context_sufficient`
and your own known context gaps before acting on the other signals; a high model
probability cannot fill a known missing callee. Do not set a universal cutoff.
Calibrate any prioritization thresholds on representative code in the target
project. A near-0.5 Boolean is uncertainty about yes/no, not medium intensity.

The agent must explain findings with actual source evidence. A `dominant_cost`
choice is a hypothesis to inspect, not a generated explanation or proof. Compare
signals separately; do not blend them into an uncalibrated overall quality grade.

## Compare and decide

1. Capture the baseline's behavior checks and static census; add a semantic
   report when the selected provider key is available. If review is skipped, finish using
   the static evidence, source inspection, and behavior checks.
2. Refactor a specific concern and rerun the relevant behavior checks.
3. Re-census the same behavioral scope, including extracted helpers, new types,
   parameter threading, and unresolved call sites. Re-evaluate with the same
   question definitions, task, constraints, and context-selection rules.
4. Compare per-dimension values and distributions alongside measured changes.
   Reports retain the request, rubric hash/version, state hash, timestamp, model,
   usage, and provider metadata. Check rubric hashes, provider, endpoint, protocol, and requested/returned model
   identities before comparing. Re-evaluate the baseline when switching providers
   or models. A provider model alias can change underneath
   the same name, so these are time-bound observations, not reproducibility proof.
5. Accept based on preserved behavior, required repository checks, and a concrete
   improvement the agent can explain. Describe tradeoffs: clearer explicit
   branches may raise cyclomatic complexity; extracting a domain concept may add
   a justified hop. Reject score-only gains that leave the path harder to follow.

Report static results, test results, semantic signals, and unknowns separately.
Low confidence, inconsistent judgments, missing context, or failed transport
require inspection or an explicitly incomplete semantic review. Do not repeatedly
sample for a higher score or let a semantic result waive a failing behavior check.
Existing user-defined gates still apply; this workflow introduces no new numeric
merge gate and does not automatically accept edits, publish reviews, or merge PRs.

## Evaluation limits

The marketplace includes a reproducible five-case suite at
`tests/fixtures/python-complexity-jev.json`, run with `make eval-python-complexity`
from the source checkout (`EVAL_ARGS=--offline` skips Jev). It compares nested,
flat, forwarding-layer, and dense-ternary implementations, plus a missing-helper
case. These are small regression fixtures, not project-wide calibration.

The initial live run passed six of nine declared semantic expectations. It
detected redundant layers and missing context, but readability barely separated
flat code from nested code or dense ternaries, and the nesting simplicity gap
was below the declared expectation. Those failures are retained. Keep the static
censuses and source inspection; a near-maximum readability score does not
establish that a path is easy to follow. The source checkout's
`notes/python-complexity/jev-evals-2026-09-22.md` records the procedure and results.

## Sources and implementation choice

Checked 2026-09-22:

- [Vercel evaluation API](https://vercel.com/docs/ai-gateway/modalities/evaluation):
  the Gateway request and response contract used by the helper.
- [TypeSafe HTTP API](https://docs.typesafe.ai/api): direct provider endpoint,
  Bearer authentication, native question types, and response fields.
- [TypeSafe Score](https://docs.typesafe.ai/primitives/score) and
  [confidence](https://docs.typesafe.ai/confidence): ordered descriptive rubrics
  and interpretation of distributions.
- [sglenon/jev-semantic-reviewer](https://github.com/sglenon/jev-semantic-reviewer):
  separates static changed-code facts from bounded semantic signals. Some
  capabilities in its roadmap are not implemented; its publishing workflow is
  outside this skill's scope.
- [NiazMorshed2007/jev-review](https://github.com/NiazMorshed2007/jev-review):
  demonstrates focused semantic review through MCP. Its current interface has
  one `jev_review` tool, not the five proposed tools in the motivating example.

This skill already has Python census tools and a call-path model. A focused
provider-configurable helper adds the judgment step without an MCP runtime or another static
analyzer. Neither community project is installed or vendored by this skill.
