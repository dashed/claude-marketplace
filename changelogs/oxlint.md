# Changelog - oxlint

All notable changes to the oxlint skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-08-24

### Added

- Initial addition to marketplace
- SKILL.md (320-line body) documenting oxlint, the Rust JavaScript/TypeScript linter from the
  **oxc** project, verified against **oxlint 1.79.0**
- Mental model framing: **plugins × categories × rules** — a rule fires only when its plugin *and*
  its category are enabled, with the resolved default quantified as **111 rules** (the
  `correctness` rules of the four default-on plugins `eslint`/`typescript`/`unicorn`/`oxc`) out of
  **870 rules** across **15 plugins** and **7 categories**
- The `plugins` **overwrite** footgun as the headline, demonstrated with captured 1.79.0 output:
  `{"plugins":["react"]}` silently drops `typescript`, `unicorn` and `oxc` (111 → 88 rules). The
  default set is exactly `UNICORN | TYPESCRIPT | OXC` (`impl Default for LintPlugins`); `eslint` is
  not a member of it but is always on and cannot be removed even by `"plugins": []`
- The sharper form of that footgun: dropping a plugin **silently discards a rule named explicitly
  in `rules` at `"error"`** — no warning, no error, exit 0 — and the CLI `-D <rule>` form is
  equally silent, even though a *misspelled* rule name is a hard config error. Documented with the
  verified `unicorn/catch-error-name` reproduction, plus the asymmetry that makes it escape review
  (core `eslint` rules keep firing, so the build is red either way and the missing rule is never
  mentioned)
- The only working detection for that bug, validated on six configs (3 broken, 3 working, one with
  an aliased key, zero false positives): no flag warns, but `--print-config` omits the discarded
  rule, so a `comm` of config rule names against resolved rule names — matched on the bare rule
  name so plugin aliases do not false-alarm — names it every time
- The CI trap that oxlint's default severity is `warn` and **warnings exit 0**, with a verified
  exit-code matrix (`-D correctness`, `--deny-warnings`, `--max-warnings`, `--quiet`,
  unmatched-pattern), plus the finding that oxlint has **only exit 0 and 1** — no exit 2, so
  config errors and lint findings are indistinguishable by exit code
- Config discovery semantics distinguishing the two merge models: a nested `.oxlintrc.json`
  **replaces** the parent config (resetting to defaults plus its own contents), while `overrides`
  inside one config **merge** — both verified experimentally, with `extends` as the opt-in
  inheritance mechanism
- All **12** top-level config keys validated against `npm/oxlint/configuration_schema.json`, plus
  the exactly **six** `options` keys, 43 `env` names, 6 `settings` sections, and the
  `allow|off|warn|error|deny`/`0|1|2` severity values
- Fix-safety taxonomy mapped to the `{Fix, Suggestion, Dangerous}` bitmask that backs `--fix`,
  `--fix-suggestions` and `--fix-dangerously`, tested on planted bugs, and the safety finding that
  oxlint has **no dry-run** (no `--diff`, `--check`, `--dry-run` or stdin) and does not change its
  exit code after rewriting files
- Destructive-behavior warning that **`--init` silently overwrites an existing `.oxlintrc.json`**,
  verified by clobbering a hand-written config
- Honest limits of `--report-unused-disable-directives`: verified that it reports only *dead*
  directives and stays silent about one actively hiding a real `no-dupe-keys` violation, so it is
  documented as hygiene rather than as a safety net
- Type-aware linting: **16 of the 111 default rules are type-aware** and are silent no-ops without
  the separate `oxlint-tsgolint` package, even though they appear in `--print-config`
- Agent-relevant finding that oxlint auto-detects `CLAUDECODE`/`CLAUDE_CODE`/`AI_AGENT` and other
  agent environments and switches to the `agent` output format, with the consequence that
  **`oxlint --rules` prints zero bytes** under an agent unless `--format json` is passed
- Lookup-first workflow (`--print-config`, `--rules --format json`, `--debug files`) instead of
  enumerating the 870-rule catalog, with `jq` recipes over the catalog's
  `scope`/`value`/`category`/`type_aware`/`fix`/`default`/`docs_url` fields
- Progressive disclosure via four reference files:
  - `references/configuration.md` — all 12 keys, `options`, `overrides` vs nested configs,
    `extends`, discovery order, `.gitignore`-driven ignore precedence, `settings`, `jsPlugins`,
    and config-error messages
  - `references/rules-and-categories.md` — the composition model, per-plugin rule counts, the 7
    categories with counts cross-checked two ways, plugin-name aliases, catalog queries,
    fix-safety taxonomy, type-aware rules, suppression comments, recipes
  - `references/eslint-migration.md` — config-shape translation, why there are no presets, rule and
    plugin alias tables, gap-filling via `oxlint-plugin-eslint` and `jsPlugins`, a phased migration,
    CI recipes, and ten behaviour differences that bite
  - `references/cli-reference.md` — every flag verified against `--help` on 1.79.0, all ten output
    formats, the exit-code model, agent auto-detection, and what oxlint deliberately does not have
- Description with explicit "Use when..." triggers and disambiguation from **oxfmt** (oxc's sibling
  formatter, a separate skill here), from ESLint/Biome themselves, and from **ruff** (the Python
  linter, also a separate skill here)
