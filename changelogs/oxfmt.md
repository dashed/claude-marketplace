# Changelog - oxfmt

All notable changes to the oxfmt skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-08-24

### Added

- Initial addition to marketplace
- SKILL.md documenting oxfmt 0.64.0, the JS/TS (and JSON/CSS/YAML/TOML/GraphQL/Markdown/Vue)
  formatter from the oxc project
- Prominent up-front warning that bare `oxfmt` rewrites files in place — inverted from `prettier`,
  which prints to stdout — with the three verified non-destructive preview modes (`--check`,
  `--list-different`, `--stdin-filepath`) and the fact that `--write` is mutually exclusive with them
- Single loud version pin for 0.64.0 rather than per-feature version tags, covering oxfmt's weekly
  minor cadence (58 releases in ~11 months) and the breaking changes shipped in 0.x minors
- Verified differences from Prettier that change output: `printWidth` defaults to 100 (not 80) and
  `sortPackageJson` defaults to `true`
- Verified list of file types oxfmt actually formats, split into native-Rust and Prettier-delegated
  tiers, plus the opt-in Svelte path and the hard-excluded lock files
- Verified exit-code table (`0` clean, `1` differences found, `2` operational failure) and the
  two-tier ignore model where `.gitignore` scopes discovery but `.prettierignore` excludes outright
- references/cli-reference.md with all 15 flags cross-checked against `--help`, exit codes, ignore
  semantics, and CI recipes
- references/configuration.md with all 27 top-level config keys validated against
  `configuration_schema.json`, their defaults and applicable languages, plus the `.editorconfig`
  override table
- references/prettier-migration.md covering `--migrate=prettier` / `--migrate=biome` behaviour, the
  Prettier option map, plugin replacements, and a staged adoption sequence

[1.0.0]: https://github.com/dashed/claude-marketplace/tree/master/plugins/oxfmt
