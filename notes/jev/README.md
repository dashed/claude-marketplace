# General Jev skill verification

The standalone `jev` skill supports bounded typed second opinions during agent
work. Its provider defaults to Vercel, using the existing local key convention;
TypeSafe and compatible custom endpoints are configurable. No key means skipped.

## Verification on 2026-09-22

- `make test-jev`: 50 offline tests, Ruff lint/format, and ty via uv. Tests cover
  request schemas, both provider protocols, provider switching, missing keys,
  literal credential parsing, redirects, errors, invalid answers, and credential
  redaction including JSON-escaped quote/backslash cases.
- The bundled plan example ran live through Vercel: unsupported preservation
  claim probability 0.03, next step `verify_failure_paths` probability 1.0,
  evidence coverage 1.01 on a 0–3 scale (expected near level 1). All three
  primitive types returned valid responses. [Raw report](example-live-2026-09-22.json).
- The helper then checked claims about our actual complexity evaluation results:
  cautious synthetic-improvement claim probability 0.85; automatic production
  gate claim probability 0.04; next validation `blind_real_review` probability
  1.0. [Request, raw response, and normalized answers](evidence-review-2026-09-22.json).

The second consultation supported keeping the existing cautious conclusion and
identified a representative real-code comparison as the next evidence needed.
The agent independently checked those claims against the saved evaluation
summaries. Jev's agreement did not change test labels or establish their truth.
The earlier [design consultation](../python-complexity/jev-design-review-2026-09-22.json)
helped select matched-count boundary examples for independent validation.

These calls establish live Vercel connectivity and expected behavior on two
bounded examples. They do not establish general decision quality or live direct
TypeSafe authentication; the latter has offline adapter coverage. No key is
included in these synthetic evidence files.

```sh
make test-jev
uv run --no-config --no-project plugins/jev/skills/jev/scripts/jev.py \
  --request plugins/jev/skills/jev/examples/review-plan.json --dry-run
```
