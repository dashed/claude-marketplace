# Changelog - psql

All notable changes to the psql skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-09

### Added
- Initial addition to marketplace
- `psql` skill documenting PostgreSQL's interactive terminal client and SQL script runner —
  scoped to the **`psql` client only** (not SQL authoring or server administration), with a
  one-line cross-skill disambiguation pointing to the sibling skills `postgres-sql`,
  `postgres-performance`, `postgres-admin`, and `postgres-extensions`.
- `SKILL.md` (325 lines): overview, when-to-use table, version note, CLI-at-a-glance + flags,
  connecting, core workflows (`\d` inspection family, output formatting, variables &
  interpolation, power tools `\gexec`/`\watch`/`\crosstabview`/`\if`, client-side `\copy`), a
  strong non-interactive/agent-usage section (`-qAtX`, `--csv`, `ON_ERROR_STOP`, exit codes,
  `-1`), extended-protocol/pipeline overview, quick reference, and troubleshooting.
- Progressive-disclosure references:
  - `references/meta-commands.md` — full backslash-command catalog, grouped, with inline `(pgNN+)` tags.
  - `references/connection.md` — conninfo strings & URIs, `PG*` env vars, `~/.pgpass`, connection
    service files, SSL/multi-host, `\c`, and precedence rules.
  - `references/scripting.md` — non-interactive/agent patterns, exit codes, transactions, special
    control variables, SQL interpolation, `FETCH_COUNT` streaming, `.psqlrc`, and psql env vars.
  - `references/pipeline.md` — extended-protocol & pipeline meta-commands (`\bind`, `\parse`,
    `\bind_named`, `\close_prepared`, `\startpipeline`/…).
  - `references/version-features.md` — sourced feature → minimum-version map (bedrock vs.
    pg14–pg19) plus the `\restrict`/`\unrestrict` cross-version security backport.
- **Version annotations**: inline `(pgNN+)` tags throughout, mirroring the `duckdb` skill's
  approach. Documented against the **PostgreSQL 19beta1** source tree (`doc/src/sgml/ref/psql-ref.sgml`
  for current syntax, `release-19.sgml` for pg19 additions); historical versions pinned against
  postgresql.org per-version manuals and release notes (the dev checkout has no tags/old release
  notes). Bedrock rule: features present in pg13 and earlier are left unannotated, except the two
  classic milestones `\gexec` (pg9.6+) and the `\if` family (pg10+).
- Notable verified version facts (corrected against the team-lead's initial hints):
  `\parse`/`\bind_named`/`\close_prepared` and the entire pipeline family are **pg18+** (absent from
  the pg16 and pg17 manuals; there was never a shipped `\close`); `\getenv` and `\dconfig` are
  **pg15+** (not pg14); `\bind` is **pg16+**; `\watch` named options `interval=`/`count=` are pg16+
  while `min_rows=` is pg17+; `WATCH_INTERVAL` is pg18+; `\restrict`/`\unrestrict` shipped via the
  2025-08 security minor releases (CVE-2025-8714) backpatched across 13–18.
