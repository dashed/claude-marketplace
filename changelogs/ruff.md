# Changelog - ruff

All notable changes to the ruff skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-08-16

### Added

- Initial addition to marketplace
- SKILL.md (300-line body) documenting ruff, Astral's Rust-based Python linter and formatter,
  verified against **ruff 0.16.3**
- Mental model framing: one binary, **two** tools (`ruff check` linter vs `ruff format` formatter),
  with their separate config sections and the correct run order
- The `select` **replaces** vs `extend-select` **adds** footgun, demonstrated with real captured
  0.16.3 output where `--select E` silently disables all 413 default rules
- Documented the **ruff 0.16.0 default rule set expansion** (59 → 413 rules), including the 18
  opinionated `E`/`F` rules dropped from the default set, so the skill does not repeat the
  pre-0.16 `["E4","E7","E9","F"]` assumption
- Two separate annotation axes kept distinct: version tags `(ruff 0.X+)` and explicit
  **preview gating** (139 of 969 rules at 0.16.3 require `preview = true`)
- Rule-prefix → upstream-tool table (59 prefixes) generated from `ruff linter`, plus the
  lookup-first workflow (`ruff rule`, `ruff rule --all --output-format json`, `ruff linter`,
  `ruff check --statistics`) instead of enumerating the ~800-rule catalog
- Fix-safety model (safe / unsafe / display) with `--fix`, `--unsafe-fixes`, `--fix-only`, `--diff`
- Config discovery and precedence (nearest-wins, not cascading), `pyproject.toml` vs
  `ruff.toml`/`.ruff.toml`, `extend`, and the dual-purpose `--config` flag
- Formatter ↔ linter conflicting-rules set, verified as absent from the 0.16.3 default rule set
- Full suppression surface: `# noqa`, `# noqa: CODE`, `# ruff: noqa`, `# ruff: ignore[...]`
  (0.16+), `# ruff: disable[...]`/`enable[...]` (0.15+), `# ruff: file-ignore[...]`, `RUF100`, and
  `--add-noqa`/`--add-ignore`
- Adoption recipe for existing codebases (statistics → free fixes → baseline → RUF100 ratchet), plus
  pre-commit (`ruff-check`/`ruff-format` hook ids) and GitHub Actions wiring
- Progressive disclosure via five reference files:
  - `references/rule-selection.md` — selectors, precedence, `ALL`, preview gating,
    `explicit-preview-rules`, per-file ignores, fix safety, suppression comments, recipes
  - `references/configuration.md` — discovery/precedence, `extend`, CLI overrides, argfiles, file
    and notebook discovery, `target-version` inference, option map cross-checked against
    `ruff.schema.json`, env vars, caching
  - `references/formatter.md` — all `[tool.ruff.format]` options, conflicting rules, `# fmt:`
    suppression, docstring and Markdown code formatting, range formatting, Black deviations
  - `references/cli-reference.md` — every subcommand and flag captured from `--help` on 0.16.3,
    output formats, exit codes
  - `references/version-features.md` — ruff's custom versioning scheme (MINOR = breaking,
    PATCH = fixes), breaking changes per release 0.7 → 0.16, preview-vs-version distinction
- Description with explicit "Use when..." triggers and disambiguation from **uv** (packaging) and
  **ty** (type checker), the sibling Astral tools with their own skills, and from flake8/black/isort
