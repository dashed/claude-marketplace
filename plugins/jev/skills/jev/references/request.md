# Request and provider reference

## Input

The request file contains exactly `state` and `questions`; provider settings are
separate. State and instructions accept a nonempty string, object, or array.

```json
{
  "state": {
    "claim": "The change preserves timeout behavior.",
    "evidence": ["The success-path unit test passes."],
    "missing": ["Timeout-path test result"]
  },
  "questions": {
    "claim_supported": {
      "type": "boolean",
      "instructions": "Does the supplied evidence establish the claim, without assuming unobserved test results?",
      "criteria": {
        "true": "Evidence directly checks the claimed behavior.",
        "false": "The claim is contradicted or its necessary evidence is missing."
      }
    }
  }
}
```

The helper accepts `boolean` and `noul` as aliases and converts to the provider's
wire format. Boolean criteria are optional; when supplied they describe both
`true` and `false`. `choice` criteria map 2-255 named options to descriptions or
null. `score` criteria contain 2-10 ordered descriptions; its value ranges from
zero to the last level index. Descriptions may be strings, objects, or arrays.

Use stable IDs of 1-80 ASCII letters, digits, underscores, or hyphens. Each call
allows 1-32 questions and at most 100,000 UTF-8 request bytes. These are local
bounds, not claims about the provider's context capacity. Unknown fields,
non-finite numbers, and invalid question shapes fail before network access.

## Provider configuration

Defaults live in `~/.config/typesafe-ai/jev.json` when present. Override with
`--config /path/provider.json`. Neither file contains a key:

```json
{
  "provider": "typesafe",
  "env_file": "~/.config/typesafe-ai/env"
}
```

| Preset | Endpoint | Model | Key environment variable |
|---|---|---|---|
| `vercel` (default) | `https://ai-gateway.vercel.sh/v1/evaluate` | `typesafe-ai/jev` | `AI_GATEWAY_API_KEY` |
| `typesafe` | `https://api.typesafe.ai/v1/systemone` | `jev-latest` | `TYPESAFE_API_KEY` |

CLI overrides: `--provider`, `--endpoint`, `--model`, `--protocol`,
`--api-key-env`, and `--env-file`. Protocol is `gateway` or `typesafe`.
Changing provider on the CLI discards overrides from the other preset, including
its credential file. Pass any desired overrides explicitly with the new provider.

For another compatible service, select `custom` and specify all four fields:

```json
{
  "provider": "custom",
  "endpoint": "https://example.org/v1/evaluate",
  "model": "provider-specific-jev-id",
  "protocol": "gateway",
  "api_key_env": "CUSTOM_JEV_API_KEY"
}
```

Custom means compatible with one of these evaluation protocols, not arbitrary
OpenAI chat completion APIs. Endpoints require HTTPS without URL credentials,
query strings, or fragments. Changing a preset's host requires an explicit key
variable so its default credential is not silently sent elsewhere. Redirects
are refused. Literal env files accept `KEY='value'` with optional `export` and
comments; shell interpolation is not evaluated.

The TypeSafe adapter follows the [HTTP API](https://docs.typesafe.ai/api).
Recheck the chosen provider's current documentation when adding a protocol or
changing models. A compatible mocked response does not prove live provider access.

## Output and failure behavior

Stdout is one JSON object. Exit 0 is `preview`, `skipped`, or `evaluated`;
inspect the status rather than using the exit code as a quality gate. Exit 2 is
`incomplete`, including invalid input/configuration, HTTP/network errors, and
malformed answers. There are no automatic retries; the request timeout is 30s.

Successful reports include `advisory: true`, the exact outbound `request`,
`state_sha256`, `questions_sha256`, provider/protocol/endpoint, raw `response`,
normalized `answers`, `evaluated_at`, and elapsed seconds. The raw provider
response retains usage/cost/model metadata when supplied. Normalized yes/no
answers use `{"type":"boolean","probability":...}` for either protocol.

The helper validates answer IDs, types, finite bounds, and distributions. Its
contract checks do not guarantee calibrated probabilities or correct judgments.
Reports contain the submitted state: choose an appropriate destination and avoid
committing sensitive request evidence. The loaded credential is redacted from
output; provider error bodies are never printed.
