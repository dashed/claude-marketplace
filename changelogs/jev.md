# Changelog - jev

## [1.0.0] - 2026-09-22

### Added
- General-purpose Jev consultation skill for coding agents: frame a bounded decision, supply actual evidence, choose Boolean/Choice/Score questions, inspect distributions, and verify the result against source or tests.
- Standalone stdlib helper for Vercel AI Gateway, direct TypeSafe, and compatible custom providers. Provider/model/endpoint/protocol/key selection is configurable; absent credentials skip without blocking the task. Invalid input, transport errors, and invalid typed answers remain incomplete.
- Literal key-file parsing, no redirects or automatic retries, bounded requests, offline preview, normalized answers, retained raw response, provenance hashes, and a runnable plan-review example.
- Offline contract and failure tests through `make test-jev`, using uv, Ruff, and ty. Live example and evidence-review observations are recorded separately from correctness or general-value claims.
