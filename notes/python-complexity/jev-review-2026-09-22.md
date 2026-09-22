# Jev integration review — 2026-09-22

Python-complexity v1.3.0 adds a Vercel Gateway judgment step to the existing censuses. The helper runs through uv and needs no third-party Python runtime packages. The credential stayed in the private user file; only the synthetic classifier below and its measurements were sent.

## Live evidence

One request per implementation, using `typesafe-ai/jev` and rubric 1.0.0. No retries or selection of better-scoring responses. All three returned successful, structurally valid evaluations; the Gateway reported cost `0` for each request. These are smoke observations, not a calibrated quality benchmark.

| Shape | Defs | Max cyclomatic | Sum cognitive | Readability (0–3) | Simplicity (0–3) | Abstraction (0–3) | Dominant cost | Seconds |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| nested | 1 | 6 | 15 | 2.93 | 2.56 | 2.94 | nesting | 0.927 |
| flat | 1 | 6 | 5 | 2.99 | 2.94 | 2.98 | no_material_obstacle | 0.322 |
| layered | 6 | 6 | 5 | 2.87 | 0.54 | 0.32 | indirection | 0.311 |

Ruff 0.15.16 (`C901`, threshold 0, isolated, ignore-noqa, JSON); complexipy 7.0.1 (`--no-ignore`, JSON). All three classifiers agreed on 119 inputs: `None`, empty string, `"7"`, `1.5`, empty dict/list, both booleans, and integers -5 through 105. There were no mismatches. This finite fixture check is not a general proof of equivalence.

Abstraction quality and simplicity distinguished redundant forwarding from a direct implementation. Readability scores remained close, including on the nested version. That limitation supports keeping separate dimensions and source-based explanations; this exercise does not establish a useful universal threshold or prove Jev prevents metric gaming.

Rubric SHA-256: `6ae7aebe17cfd6528d87d8ffda55f0d73bf46ac7fbc287c66a433f834bd82e62`.

| Shape | State SHA-256 | Gateway generation |
|---|---|---|
| nested | `e33ed457ef40e99d8a1d2a419133ba52a8f1f9e255a1b8bbdf13a78815724954` | `gen_01M34G6F9Y18CCVFYB7V1RRE15` |
| flat | `5415d2cdb06fec9a2da4b8d91ffb9c2737954b62ee7d22385a4b772ac9c548d4` | `gen_01M34G6GCZKKNP47FBZ7Q04S93` |
| layered | `a0dbe3b5cfa7cdc24ddd930ac21d25d360564fe70dc4ba5614f222dcb997c60f` | `gen_01M34G6GXTR36N4SRVQ4FWMGJG` |

The state used the same task and constraints for every shape: classify missing, not-integer, negative, too-large, odd, or accepted in that order; accept even integers from 0 through 100; Python booleans count as integers. Preserve the signature and all return values. No private-helper callers, external hooks, or additional invariants exist. Each request included the full shown source, actual static-tool output, the differential-test count, and an empty missing-context list.

Full request/response snapshots from this run were retained locally in:
`/var/folders/x_/y6n82vd54gg8ndjh8qby_1mr0000gn/T/python-complexity-jev-ysbf_vo6`

This temporary path is evidence for this session, not a permanent dependency. The rubric ships with the skill; the exact source fixtures follow.

### nested

```python
def classify(value):
    if value is not None:
        if isinstance(value, int):
            if value >= 0:
                if value <= 100:
                    if value % 2 == 0:
                        return "accepted"
                    return "odd"
                return "too_large"
            return "negative"
        return "not_integer"
    return "missing"
```

### flat

```python
def classify(value):
    if value is None:
        return "missing"
    if not isinstance(value, int):
        return "not_integer"
    if value < 0:
        return "negative"
    if value > 100:
        return "too_large"
    if value % 2:
        return "odd"
    return "accepted"
```

### layered

```python
def classify(value):
    return _dispatch(value)

def _dispatch(value):
    return _prepare(value)

def _prepare(value):
    return _route(value)

def _route(value):
    return _evaluate(value)

def _evaluate(value):
    return _classify_value(value)

def _classify_value(value):
    if value is None:
        return "missing"
    if not isinstance(value, int):
        return "not_integer"
    if value < 0:
        return "negative"
    if value > 100:
        return "too_large"
    if value % 2:
        return "odd"
    return "accepted"
```

## Provider configuration

The shipped helper defaults to Vercel and also supports direct TypeSafe and compatible custom endpoints. CLI flags or `~/.config/typesafe-ai/jev-review.json` select the provider, model, endpoint, protocol, and credential variable/file. It records normalized answers alongside the raw provider response and skips when the selected provider key is missing. Offline tests cover native protocol adaptation, configuration precedence, credential isolation, and invalid settings.

## Validation and skill review

- `make test-python-complexity` runs Ruff lint and format checks, ty, and 50 offline tests through `uv run --no-config --locked`. Tests exercise request preservation, secret handling, literal key-file parsing, previews, invalid inputs/answers, HTTP/network failures, and missing/empty credentials skipping semantic review without network access. Configured malformed credentials and API errors still report incomplete evaluations.
- `make validate-strict` passes the repository structure, JSON, skill frontmatter, and MCP-name checks.
- The generic skill-creator quick validator rejects the existing `when_to_use` frontmatter field. This repository explicitly supports that field in `schemas/skill-frontmatter-schema.json`; it was preserved.
- Full Codex manifest regeneration also changes cache hashes for 12 unrelated plugins in this checkout. Those unrelated refreshes were reverted; only python-complexity metadata was regenerated and checked for this change.

Checklist: ✅ progressive disclosure; ✅ task-specific mental model; ✅ appropriate freedom; ✅ concise addition to the entrypoint; ✅ failure handling; ✅ resource hygiene; ✅ terminology and score direction; ✅ behavioral validation; ✅ documented limitations; ✅ focused Python-complexity scope.

Follow-up suggestion: validate rubric usefulness on representative real functions and complete call paths before adopting prioritization cutoffs. The helper validates the API contract, not the truth of judgments or supplied static evidence. No automatic acceptance or numeric semantic gate is introduced.
