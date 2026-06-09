# psql Feature → Minimum Version

A consolidated lookup of **which PostgreSQL release introduced a `psql` command-line option,
meta-command, output option, or variable** this skill documents, so you know what works on an
older (or newer) `psql`. Use it to answer "is my `psql` new enough for X?" and "what do I need to
upgrade to?"

## How to read this

- These are **PostgreSQL major versions** (e.g. `16`, `17`, `18`). The `pg16+` form means "the 16
  release and later." `psql` ships as part of PostgreSQL and shares its major version.
- **`psql` is a *client*.** Almost every meta-command in this table is gated by the **`psql`
  (client) version**, *not* the server you connect to — a new `psql` talking to an old server
  still has `\if`, `\gexec`, pipelines, etc. The handful of features that additionally depend on
  the **server** version are flagged in the **Notes** column. A new `psql` can always talk to an
  old server and vice-versa; mismatches only limit which *introspection* details `\d`-family
  commands can show.
- **Bedrock rule (signal-rich tagging).** PostgreSQL has a very long history. To keep annotations
  useful, **features present in PostgreSQL 13 and earlier are treated as "bedrock" and left
  UNANNOTATED** in the skill — 13 is the oldest line still within recent memory of the currently
  supported window (14–18 supported as of 2026; 13 went EOL Nov 2025). The skill annotates
  features added in **pg14 and later**.
  - **Two deliberate exceptions** are tagged even though they predate 14, because they are the
    classic "why doesn't my script run on old `psql`?" gotchas: **`\gexec` (pg9.6+)** and the
    **`\if`/`\elif`/`\else`/`\endif` conditional family (pg10+)**. A short [pre-14 milestones](#pre-14-milestones-bedrock-shown-for-reference)
    list at the bottom records a few more for reference.
- **Verify, don't guess.** Every row below is sourced. The current syntax/behavior column is taken
  from the **psql reference page in the PostgreSQL 19beta1 source tree**
  (`doc/src/sgml/ref/psql-ref.sgml`); pg19 additions from `doc/src/sgml/release-19.sgml`. Because
  the dev checkout used here has **no historical release notes and no git tags**, every *historical*
  "added in pgNN" was pinned against **postgresql.org** — the per-version reference manuals
  (`/docs/NN/app-psql.html`) and the release notes (`/docs/release/NN.0/`), cross-checked. **No
  version is guessed:** a feature with no clean source is treated as bedrock and omitted.

## Sources

- psql reference (current syntax), PG 19beta1 source tree: `doc/src/sgml/ref/psql-ref.sgml`
- PG 19 beta changes: `doc/src/sgml/release-19.sgml`
- Release notes (per major version): <https://www.postgresql.org/docs/release/>
  (14.0, 15.0, 16.0, 17.0, 18.0, plus 9.6.0 / 10.0 / 11.0 for the milestone exceptions)
- Versioned psql manuals (presence/absence cross-check):
  <https://www.postgresql.org/docs/16/app-psql.html>, `/17/`, `/18/`
- `\restrict`/`\unrestrict` security backport (CVE-2025-8714, 2025-08 minor releases):
  PG release notes 13.22 / 16.10 / 17.6 and the commit "Restrict psql meta-commands in plain-text
  dumps."

## Contents

- [Versioned features (ascending by PostgreSQL release)](#versioned-features-ascending-by-postgresql-release)
- [`\restrict` / `\unrestrict` — the cross-version security backport](#restrict--unrestrict--the-cross-version-security-backport)
- [Pre-14 milestones (bedrock; shown for reference)](#pre-14-milestones-bedrock-shown-for-reference)
- [Checking your version](#checking-your-version)

## Versioned features (ascending by PostgreSQL release)

Sorted ascending by minimum `psql` version; within a release, grouped by **Area**
(meta-command / output / variable / prompt).

| Min version | Feature | Area | Notes |
|---|---|---|---|
| pg14+ | `\dX` — list extended-statistics objects | meta-command | server has extended stats since pg10 |
| pg15+ | `\dconfig[+] [pattern]` — show server config parameters (pattern-aware `SHOW`) | meta-command | |
| pg15+ | `\getenv psql_var env_var` — read an environment variable into a `psql` variable | meta-command | the script-safe way to pull env into SQL |
| pg15+ | `SHOW_ALL_RESULTS` variable — show every result of a `\;`-combined batch (default `on`) | variable | set `off` for the old last-result-only behavior |
| pg16+ | `\bind [param ...]` — bind parameters / force the **extended** query protocol for the next query | meta-command | foundation for `$1` params from `psql` |
| pg16+ | `\watch` **named** options `i[nterval]=`, `c[ount]=` + execution-count limit + zero-delay | meta-command | bare `\watch [secs]` itself is bedrock (pg9.3) |
| pg16+ | `\drg [pattern]` — role membership/grants (the `Member of` column was removed from `\du`/`\dg`) | meta-command | reads server role-membership catalogs |
| pg16+ | `\pset xheader_width` — cap expanded-header width (`full`/`column`/`page`/N) | output | |
| pg16+ | `\dpS` / `\zS` — include system objects in access-privilege listings | meta-command | |
| pg16+ | `SHELL_ERROR` / `SHELL_EXIT_CODE` variables — status of last `\!`/backtick/`\g`-pipe | variable | great for scripting around shell calls |
| pg17+ | `\watch m[in_rows]=rows` — stop once fewer than N rows are returned | meta-command | adds to the pg16 named-option set |
| pg17+ | Backslash `\d`-family commands honor `\pset null` | output | |
| pg17+ | `\dp` shows `(none)` for empty (vs. default) privileges | output | |
| pg17+ | `FETCH_COUNT` honored for non-`SELECT` queries too | variable | streams large result sets in chunks |
| pg17+ | Connection attempts cancelable with Ctrl-C | (interactive) | |
| pg18+ | `\parse name`, `\bind_named name [param ...]`, `\close_prepared name` — named prepared statements over the extended protocol | meta-command | `\close_prepared` is the shipped name (no `\close` ever shipped) |
| pg18+ | **Pipeline** family: `\startpipeline`, `\syncpipeline`, `\sendpipeline`, `\endpipeline`, `\flushrequest`, `\flush`, `\getresults [n]` | meta-command | see [references/pipeline.md](pipeline.md) |
| pg18+ | Expanded-mode **`x` suffix** on list commands (e.g. `\d+x`, `\dtx`) | output | applies to listing forms; `\dx` stays "list extensions" |
| pg18+ | `WATCH_INTERVAL` variable — default `\watch` wait, in seconds (default 2) | variable | per-command interval still overrides |
| pg18+ | `%P` prompt + `PIPELINE_SYNC_COUNT` / `PIPELINE_COMMAND_COUNT` / `PIPELINE_RESULT_COUNT` variables | prompt/variable | pipeline status |
| pg18+ | Connection **service name** available in the prompt / via a variable | prompt/variable | |
| pg18+ | `\conninfo` reworked into a tabular, more-detailed report | output | |
| pg18+ | `\df+`/`\do+`/`\dAo+`/`\dC+` show a **leakproof** indicator; `\dP+` shows partitioned access method; `\dx` shows `default_version` | output | |
| pg19+ | `%S` prompt — current `search_path` | prompt | needs server **v18+** |
| pg19+ | `%i` prompt — hot-standby status indicator | prompt | |
| pg19+ | `\pset display_true` / `display_false` — control how booleans render | output | |
| pg19+ | `SERVICEFILE` variable — the connection-service file in effect | variable | |
| pg19+ | `\dRp+` / `\dRs+` / `\dX+` show object comments | output | publications / subscriptions / extended stats |

> **pg19 is beta** in the source tree this skill is documented against (19beta1). pg19 rows are
> "what's coming"; treat them as not-yet-on-a-stable-release until 19.0 ships.

## `\restrict` / `\unrestrict` — the cross-version security backport

`\restrict <key>` enters a **restricted mode** in which the *only* permitted meta-command is
`\unrestrict <key>` (matching key required); everything else is blocked. It exists primarily so
that `pg_dump` / `pg_dumpall` / `pg_restore` can wrap plain-text dumps and stop a hostile source
server from smuggling `psql` meta-commands into a restore stream.

Unlike the rows above, **this is not a clean "added in one major version" feature.** It was
introduced as a **security fix (CVE-2025-8714)** in the **2025-08 minor releases** and
**backpatched across all then-supported branches** — it ships in **13.22, 14.x, 15.x, 16.10,
17.6, and 18+** (and in 19beta1). Practical consequences:

- Modern `pg_dump` output (16.10+/17.6+/18+) now contains `\restrict`/`\unrestrict` lines. Restoring
  such a dump with a **pre-fix `psql`** fails on the unknown command — always restore with a
  `psql` at least as new as the `pg_dump` that produced the file.
- Because it was backported, you cannot infer a server/client major version from its presence; key
  it to the **minor** release, not the major.

## Pre-14 milestones (bedrock; shown for reference)

These predate the pg14 tagging window and are therefore **left unannotated in the skill**, but are
recorded here (sourced) because they're commonly hit on older clients. `\gexec` and the `\if`
family are the two the skill *does* tag inline.

| Version | Feature | Source |
|---|---|---|
| pg9.6 | `\gexec` — run query, resubmit each result cell as a new query *(tagged inline)* | release notes 9.6.0 |
| pg9.6 | `\crosstabview` — pivot a query result into a cross-tab grid | release notes 9.6.0 |
| pg10 | `\if` / `\elif` / `\else` / `\endif` — conditional branching *(tagged inline)* | release notes 10.0 |
| pg10 | `\gx` — `\g` forcing expanded output | release notes 10.0 |
| pg11 | `\gdesc` — describe the result columns of the current query buffer | release notes 11.0 |

Other long-standing surface treated as bedrock (no version tag): `\g`, `\gset`, `\copy`, `\watch`
(basic repeat), the core `\d`/`\dt`/`\df`/`\dn`/`\di`/`\dv`/`\l`/`\dx` inspection family, `\set`/
`\unset`/variable interpolation (`:var`, `:'var'`, `:"var"`), `\pset`/`\x`/`\a`/`\t`/`\f`,
`\o`/`\i`/`\ir`/`\e`/`\ef`/`\ev`/`\sf`/`\sv`/`\w`, `\timing`, `\!`/`\cd`/`\setenv`,
`\c`/`\conninfo`/`\password`/`\encoding`, `ON_ERROR_STOP`/`AUTOCOMMIT`/`VERBOSITY`/`ECHO`/
`ON_ERROR_ROLLBACK`, conninfo strings & URIs, `PGHOST`/`PGPORT`/`PGUSER`/`PGDATABASE`/`PGPASSWORD`,
`~/.pgpass`, and connection service files. This file omits them to stay signal-rich.

## Checking your version

```bash
psql --version            # e.g. "psql (PostgreSQL) 18.1"  (alias: psql -V)
```

From inside a session:

```sql
\echo :VERSION                 -- verbose client version string
\echo :VERSION_NUM             -- numeric, e.g. 180001  (psql build)
\echo :SERVER_VERSION_NUM      -- the SERVER you're connected to, e.g. 170004
SELECT version();              -- server version, long form
SHOW server_version_num;       -- server version, numeric
```

`psql --version` reports the **client** major version this table is keyed on. The
`:SERVER_VERSION_NUM` / `SHOW server_version_num` values report the **server** — relevant only for
the few server-gated rows flagged in **Notes**. As of 2026 the supported lines are **14–18**;
**19 is in beta**.
