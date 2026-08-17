# Changelog - ty

All notable changes to the ty skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-08-16

### Added

- Initial addition to marketplace
- SKILL.md (283 lines) covering ty, Astral's Rust Python type checker and language server:
  beta/version warning pinned to ty 0.0.72, the inference-first mental model (gradual typing,
  redeclarations, three-level rule severities, no `--strict`), install/run, commands table,
  configuration, rule levels and suppression, diagnostic anatomy and exit codes, a
  mypy/pyright differences table, editor/LSP pointers, a CI recipe, and a troubleshooting table
- Disambiguation in the description and body: ty is the type checker, NOT ruff (linter/formatter)
  or uv (packaging) — both separate Astral tools with their own skills here — and is an
  alternative to mypy/pyright rather than either of them
- `references/cli-reference.md` — every command and flag captured from `--help`, the five output
  formats, an empirically verified exit-code matrix, environment variables, and CI patterns
- `references/configuration.md` — config discovery and precedence, all six tables
  (`environment`, `src`, `rules`, `overrides`, `terminal`, `analysis`) with every key validated
  against the binary, `[[overrides]]`, environment discovery, and anchored glob syntax
- `references/rules-and-suppression.md` — the three-level severity model, rule lookup via
  `ty explain rule`, rule categories by naming scheme, the 10 opt-in rules, full suppression
  semantics, and `--add-ignore` baselining
- `references/mypy-pyright-migration.md` — migration checklist, concept mapping, the strictness
  inversion, recommended strict configs, a high-traffic rule/error-code mapping table, and the
  checks that belong to Ruff rather than ty
- Version policy: a single pinned-version statement plus a "Recently changed" table of
  stale-knowledge traps, in place of per-feature version tags — ty's entire surface is 0.0.x, so
  blanket tagging would carry no signal
