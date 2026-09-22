# Independent Jev complexity challenge, 2026-09-22

An independent agent froze eight synthetic cases and fourteen semantic expectations before reading candidate outputs. The fixture is `tests/fixtures/python-complexity-jev-independent.json`, SHA-256 `a5fc9379ade7f8b93d839a8bf5e00e0167c0aeffa529c7460b4b8984a42e057c`. This is a small challenge suite, not a representative benchmark or a production acceptance gate.

Candidate rubric 1.1.0, question hash `f4651cc7e20fb0ab60a34588fd8fee3af9fa5a30651387d9752176b871187225`, ran through Vercel's Jev evaluation endpoint. Ruff 0.15.16 and complexipy 7.0.1 measured the code independently. All 56 behavioral examples passed. Twelve semantic expectations passed and two failed; no expectations or thresholds changed after seeing the results.

The first run returned HTTP 503 for `shared_policy`. Its two dependent expectations were initially skipped. A single manual retry used the saved identical state and frozen rubric and succeeded. The first report remains intact; no successful judgment was rerun or selected.

## Do layers benefit from semantic judgment?

This pair provides a concrete positive example beyond the static counts:

| Measurement | Shared policy | Forwarding chain |
| --- | ---: | ---: |
| Function definitions | 4 | 4 |
| Maximum cyclomatic complexity | 1 | 1 |
| Total decisions | 0 | 0 |
| Total cognitive complexity | 0 | 0 |
| Maximum cognitive complexity | 0 | 0 |
| Jev abstraction quality (0–3) | 2.74 | 0.56 |
| Jev simplicity (0–3) | 2.96 | 1.09 |
| Jev readability (0–3) | 2.99 | 2.56 |

`shared_policy` centralizes whitespace trimming and case folding in `canonical_name`, which is used by the independently called `lookup` and `contains` APIs. `probe` combines their results. Its supplied constraints explain that the public API boundaries and shared policy are intentional.

`forwarding_chain` implements the same tested lookup-and-presence behavior as `probe → _dispatch → _route → _read`. Its three intermediate functions only pass the same arguments onward. Its supplied constraints explicitly rule out framework hooks, alternative dispatchers, instrumentation, or private-helper consumers. Jev therefore receives evidence about each boundary's purpose; these are not identical contexts and the result does not prove Jev can infer omitted architectural requirements.

The abstraction-score distributions were:

| Score level | Shared policy | Forwarding chain |
| --- | ---: | ---: |
| 0 | 0.01 | 0.80 |
| 1 | 0.03 | 0.01 |
| 2 | 0.16 | 0.04 |
| 3 | 0.80 | 0.15 |

The predeclared abstraction delta was at least 0.50; observed delta was 2.18. The useful-boundary absolute expectation, at least 2.40, also passed.

The dominant-obstacle choice was less decisive for forwarding: `indirection` probability 0.52 versus `no_material_obstacle` 0.48. Shared policy received `no_material_obstacle` 0.98, `indirection` 0.01, and `insufficient_context` 0.01. The test checks the selected category, so it passed, but the near tie for forwarding should remain visible rather than being presented as strong certainty.

## Nesting, expressions, and preserved failures

| Predeclared expectation | Observed | Result |
| --- | ---: | --- |
| Guard ladder: flattening probability ≥ 0.70 | 0.55 | Failed |
| Grouped aggregation: flattening probability ≤ 0.30 | 0.10 | Passed |
| Transaction/lock cleanup: flattening probability ≤ 0.30 | 0.11 | Passed |
| Safe short-circuit division guard: expansion probability ≤ 0.30 | 0.13 | Passed |
| Nested status ternaries: expansion probability ≥ 0.70 | 0.54 | Failed |
| Explicit status branches: expansion probability ≤ 0.30 | 0.15 | Passed |
| Explicit minus dense status readability ≥ 0.25 | 1.05 | Passed |

The grouped-aggregation, cleanup-lifetime, short-circuit, and explicit-status controls all retained readability above 2.40: 2.99, 2.58, 3.00, and 2.61, respectively. The dense expression scored 1.56 and the avoidable guard ladder 1.12. The candidate distinguishes their reading burden while avoiding blanket penalties on useful compact or nested code.

The two action probabilities remain insufficiently decisive under the frozen expectations. Recognizing a readability problem and confidently endorsing a particular transformation are separate capabilities. These results support using Jev to surface review candidates and assess boundary purpose; they do not support treating these probabilities as refactor authorization or a correctness proof.

## Reproduction and evidence

```sh
uv run --no-config --locked scripts/eval_python_complexity.py \
  --offline --fixtures tests/fixtures/python-complexity-jev-independent.json

uv run --no-config --locked scripts/eval_python_complexity.py \
  --fixtures tests/fixtures/python-complexity-jev-independent.json \
  --output-dir /tmp/jev-independent-new-run
```

The recorded live run used `/tmp/jev-independent-20260922-candidate/` for source/state snapshots and raw provider reports. Durable copies are committed: [initial incomplete summary](jev-independent-first-2026-09-22.json), [the single HTTP 503 retry](jev-independent-retry-2026-09-22.json), and [all fourteen expectations with retry provenance](jev-independent-completed-2026-09-22.json). The original fixture hash and rubric hash allow these results to be tied to the exact inputs. Remote probabilities may differ on subsequent runs.

Behavior examples verify the fixture implementations against their stated outcomes; they do not establish exhaustive behavioral equivalence. The lifetime fixture demonstrates normal cleanup order but does not inject an exception. Static counts omit dependency topology; a path census can also expose redundant call depth, while the stated purpose of those boundaries requires context.
