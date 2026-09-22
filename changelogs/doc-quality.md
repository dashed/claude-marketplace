# Changelog - doc-quality

## [1.1.0] - 2026-09-22

### Added
- Opt-in bounded local link and anchor checks, including snapshot comparisons at a common logical document path. External URLs and unsupported renderer behavior remain explicitly unchecked.
- Independently frozen repository-excerpt rewrite challenges, coverage for all four quality profiles, and an unassisted second-pass control alongside assisted agent review.

### Changed
- Rubric 1.1.0 explicitly considers reductions in unnecessary reading effort when facts are preserved; retains equivalent and missing-context outcomes and prioritizes technical fidelity.
- Retain original evaluation evidence and all follow-up failures. No automatic acceptance or universal probability thresholds.

## [1.0.0] - 2026-09-22

### Added
- Section-aware engineering Markdown review for designs, analyses, implementation plans, and ADRs; the agent edits targeted sections while the helper remains read-only.
- CommonMark/table parsing, source line ranges, heuristic English readability metrics, and protected inventories for code, links, metadata, quantities, requirement strength, and negation.
- Optional Jev quality profiles and paired preservation judgments through the general provider-configurable helper. Missing helper/key skips; service errors remain incomplete.
- Separate original/revised quality requests use identical questions/context. No probability threshold, improved readability, or unchanged inventory automatically accepts a rewrite.
- Frozen independent safe/harmful rewrite evaluations and offline tests with uv, Ruff, and ty. Evaluation evidence is recorded under notes/doc-quality.
