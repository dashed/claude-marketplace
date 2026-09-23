# Jev semantic complexity review

## Contents

- [Evidence and scope](#evidence-and-scope)
- [Configure and run a provider](#configure-and-run-a-provider)
- [Read the judgments](#read-the-judgments)
- [Compare a refactor in one request](#compare-a-refactor-in-one-request)
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
| `flattening_helpful` | Probability local guard exits help while preserving traversal, order, and lifetimes |
| `expression_expansion_helpful` | Probability explicit branches help unpack a compressed conditional expression |
| `dominant_cost` | A candidate explanation category, including no problem and insufficient context |
| `context_sufficient` | A separate judgment about whether the shown context supports review |

Rubric 1.1.0 distinguishes understanding the final result from the bookkeeping needed
to change a path: pending guards, condition/outcome associations, expression binding,
and helper transitions. Natural collection nesting, a simple ternary, and a useful
short-circuit predicate can still score well. The two transformation judgments
are specific hypotheses to inspect, not requests to flatten or expand every case.

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

## Compare a refactor in one request

To judge a refactor, send both versions in **one** request instead of scoring each
and subtracting. A version already scored near the top of a scale has no room left
to rise, so two absolute requests can miss a real change; the snapshot scores in
this skill's first evaluation clustered near 3 for exactly that reason. Supercov's
quality command reached the same conclusion and asks "does `after` show this where
`before` did not?" in one request.

```sh
uv run --no-project "$skill_dir/scripts/jev_review.py" \
  --before before.json --after after.json > change-review.json
```

`before.json` and `after.json` are ordinary state files for the same behavioral
scope. Their `task` and `constraints` must be identical, because the two versions
must satisfy one contract; the helper refuses otherwise. The request carries only
that contract and the two versions' code (several sources are joined under
`# file:` headers). Measurements, scope and missing-context notes stay in your
report, not in the request: extra structure around the versions weakened detection
in Supercov's testing, and static numbers belong to the static tools.

The [change rubric](jev-change-rubric.json) asks about four properties that the
static censuses cannot decide, each in both directions, plus one preference:

| Question | Yes means |
|---|---|
| `introduced_pass_through` / `removed_pass_through` | The change added / removed a layer that only forwards to one callee and adds no validation, conversion, invariant or domain name |
| `introduced_domain_rule` / `removed_domain_rule` | The change named one domain rule in a single place / inlined or scattered one |
| `introduced_mixed_responsibilities` / `removed_mixed_responsibilities` | The change merged / separated concerns that change for different reasons |
| `introduced_duplicated_rule` / `removed_duplicated_rule` | The change copied / consolidated one rule written in several places |
| `preferred` | `before`, `after`, `equivalent` (cosmetic, or an even trade) or `insufficient_context` |

Each yes/no question states its exception — a forwarding public entry point or
adapter is not a pass-through; similar-looking code implementing different rules is
not duplication — and defines both answers. The questions are presence questions,
not "would this help?" questions, which stayed indecisive in the snapshot rubric.
The agent still decides what to change and why.

How far to trust each answer, from the frozen suite described under
[Evaluation limits](#evaluation-limits):

- **`preferred` is the signal.** It matched an independent author on 14 of 15
  refactors and held under repeated requests, reformatting and a missing task.
  On ambiguous changes it leans toward whichever version is in the `after` slot.
- **The directional answers are pointers, not findings.** They rank real changes
  well but raised confident false alarms on exactly the stated exceptions (a
  forwarding public endpoint called a new pass-through at 0.97), and asking with
  the versions swapped moved them by up to 0.77. Use a high one to decide what to
  inspect; confirm the property in the source before reporting it.
- **Missing code needs the snapshot check.** The paired preference picked `after`
  for a change that called code not shown; the snapshot `context_sufficient`
  question flagged it (0.22). When the change depends on unseen callees, run a
  snapshot review of the after version too.
- **Any answer can move by about 0.1 between identical requests.** A probability
  within that distance of a cutoff decides nothing.

A `preferred` answer does not outrank a concrete introduced problem that the agent
can point to in the source.

## Compare and decide

1. Capture the baseline's behavior checks and static census. If review is skipped,
   finish using the static evidence, source inspection, and behavior checks.
2. Refactor a specific concern and rerun the relevant behavior checks.
3. Re-census the same behavioral scope, including extracted helpers, new types,
   parameter threading, and unresolved call sites.
4. When the selected provider key is available, send the paired request above with
   the same task, constraints and context-selection rules for both versions. Compare
   its answers with the measured changes. Reports retain the request, rubric
   hash/version, state hash, timestamp, model, usage, and provider metadata. A
   provider model alias can change underneath the same name, so these are
   time-bound observations, not reproducibility proof. Snapshot reviews of each
   version remain useful for triage, but compare two snapshot reports only with the
   same rubric hash, provider, endpoint, protocol and returned model.
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

Rubric 1.1.0 passes all nine original expectations. A separately frozen eight-case
validation suite passes 15 of 16: useful nesting and simple-expression controls
pass, while an already-flat case produces a borderline flattening probability
above its declared negative-control limit. The checkout's
`notes/python-complexity/jev-improvement-2026-09-22.md` retains old/new evidence
and further independent results. Action probabilities require inspection; better
synthetic separation is not proof of production refactor value. Run validation
with `make eval-python-complexity EVAL_ARGS='--fixtures tests/fixtures/python-complexity-jev-validation.json'`.

An independent eight-case challenge passes 12 of 14 semantic expectations. It
distinguishes useful shared-policy helpers (abstraction 2.74/3) from forwarding
(0.56/3) despite identical static counts, using supplied boundary constraints.
Two transformation probabilities remain below their frozen expectations. All
three suites total 564 passing behavior examples and 36/39 semantic expectations;
the three failures stay visible. The source checkout's independent review also
records the forwarding category's near tie and a single HTTP 503 retry.

The paired change rubric has its own frozen suite: 15 before/after pairs and 129
labels written by a separate agent from the rubric's definitions, run with
`make eval-python-complexity-changes`. On one live run the paired `preferred`
answer matched 14 of 15 labels, against 7 for always choosing the most common
label and 10 for scoring each version with the snapshot rubric and subtracting;
no static census delta separated those labels. The directional questions found 12
of 13 labeled changes but raised 22 false alarms among 101 non-changes, and 23
repeat, reformat and swap controls failed their frozen tolerances. The checkout's
`notes/python-complexity/jev-changes-2026-09-22.md` records the freeze, every
response, the snapshot baseline's pre-declared rule, and the limits: one small
synthetic suite, one run, and no measurement of whether an agent decides better
with these answers.

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
