# Changelog - doc-quality

## [1.1.1] - 2026-09-22

### Fixed
- Fix the script crashing on import when uv runs it on Python 3.13 or newer, which uv chooses outside this repository wherever 3.13+ is installed. The pinned `github-slugger==0.0.3`, its latest release, has a docstring with lone surrogate escapes that CPython 3.13+ cannot compile. The script now requires Python `>=3.10,<3.13`, so uv selects a compatible interpreter.
- Add a test that runs the documented `uv run` command on the oldest and newest admitted CPython minor with a local anchor check. The other tests import the script under the repository's Python 3.10 and cannot see this failure.

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
