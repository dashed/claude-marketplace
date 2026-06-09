---
name: psql
description: psql — PostgreSQL's interactive terminal client and SQL script runner (the `psql` command). Covers connection strings/URIs, `~/.pgpass` & service files, invocation flags (`-c`/`-f`/`-1`/`--csv`/`-qAtX`/`-v`), the `\d`-family inspection meta-commands, `\copy`, `\watch`, `\gexec`/`\gset`, `\if` scripting, `\pset` output formats & `\x`, variables & `:'…'` interpolation, `.psqlrc`, exit codes/`ON_ERROR_STOP`, and extended-protocol/pipeline commands (`\bind`/`\parse`/`\startpipeline`). Use when connecting to or inspecting a Postgres database from a terminal, running SQL scripts or one-off queries in shells/CI/agents, formatting or capturing query output, or fixing psql connection/auth problems. Includes inline (pgNN+) version annotations (pg14–pg19). This is the psql CLIENT only — for SQL syntax/data types use postgres-sql; for EXPLAIN/indexes/vacuum use postgres-performance; for server config/auth/backup/replication use postgres-admin; for CREATE EXTENSION use postgres-extensions.
---

# psql — PostgreSQL Interactive Terminal

## Overview

`psql` is PostgreSQL's official **command-line client**: an interactive REPL *and* a SQL-script
runner built on **libpq**. You use it to connect to a server, type SQL, inspect the schema with
backslash **meta-commands** (`\d`, `\dt`, `\df`, …), format and capture output, and run scripts in
shells, CI, and agents. It is a thin client — the database engine, SQL semantics, and server
administration all live on the **server**, not in `psql`.

**Key characteristics:**
- **Client, not server** — `psql` connects to a running PostgreSQL server; it stores no data and
  runs no SQL itself. Almost everything is gated by the **`psql` (client) version**, independent of
  the server you reach.
- **Two layers in one prompt** — **SQL** (sent to the server, terminated by `;`) and
  **meta-commands** (start with `\`, interpreted locally).
- **libpq under the hood** — same connection strings/URIs, `PG*` environment variables, `~/.pgpass`,
  and service files as every other PostgreSQL client.
- **Scriptable & pipeable** — `-c`/`-f`/heredoc input, machine-readable output (`--csv`, `-qAtX`),
  meaningful exit codes, and `ON_ERROR_STOP` make it a first-class scripting tool.

> **Disambiguation — this is the `psql` *client*.** This skill documents the `psql` program: its
> flags, connections, meta-commands, output formatting, variables, and scripting. It is **not** a
> SQL tutorial and does **not** cover server-side topics. For sibling concerns use:
> **`postgres-sql`** (SQL dialect, data types, DDL/DML), **`postgres-performance`** (`EXPLAIN`,
> indexes, `VACUUM`, planner), **`postgres-admin`** (`postgresql.conf`, roles/auth, backup,
> replication), **`postgres-extensions`** (`CREATE EXTENSION`, contrib modules). When in doubt: if
> it works the same in pgAdmin/DBeaver/a driver, it's *not* a `psql` topic — it belongs to a
> sibling skill.

## When to Use This Skill

| Use psql when… | Prefer a sibling when… |
|---|---|
| Connecting to / inspecting a database from a terminal (`\d`, `\l`, `\df`) | Designing tables or writing queries → **postgres-sql** |
| Running a SQL script or one-off query in a shell / CI / agent | Tuning a slow query, reading `EXPLAIN` → **postgres-performance** |
| Formatting or capturing output (CSV, expanded, redirect to file) | Configuring the server, roles, backups → **postgres-admin** |
| Debugging connection/auth (conninfo, `.pgpass`, services, SSL) | Installing/using an extension → **postgres-extensions** |
| Writing `.psqlrc`, scripting with `\set`/`\if`/`\gexec`/`\gset` | Authoring the SQL those scripts run → **postgres-sql** |

## Prerequisites & Version Note

```bash
psql --version        # e.g. "psql (PostgreSQL) 18.1"   (alias: psql -V)
```

This skill documents the `psql` surface as of the **PostgreSQL 19beta1** source tree, so the latest
*stable* line is **pg18** and **pg19 is beta**. Long-standing features (present in **pg13 and
earlier**) are **bedrock** and shown **unannotated**; features added later are tagged inline as
`(pgNN+)`, e.g. `(pg16+)`. Two pre-14 classics are tagged anyway because scripts hit them on old
clients: `\gexec` (pg9.6+) and the `\if` family (pg10+). Every tag is sourced — see
[references/version-features.md](references/version-features.md) for the full feature→version map.
Confirm what you're running with `psql --version` (client) and `\echo :SERVER_VERSION_NUM` (server).

`psql` ships with PostgreSQL (`postgresql-client` / `postgresql` packages, or
`brew install libpq`). A newer `psql` talks to older servers fine and vice-versa.

## The `psql` CLI at a Glance

These invocations cover ~90% of usage:

```bash
psql                                   # connect using PG* env vars / defaults, interactive REPL
psql -d "postgresql://user@host/mydb"  # connect via a URI (or conninfo string)
psql -h db -U me -d app                # connect via discrete flags
psql -c "SELECT version()"             # run one command and exit (great for scripts)
psql -f script.sql                     # run a SQL file and exit
psql -qAtX -c "SELECT count(*) FROM t" # quiet, unaligned, tuples-only, no .psqlrc → clean scalar
psql --csv -c "SELECT * FROM t"        # CSV output (safe quoting) for parsing
```

**Usage:** `psql [OPTION]... [DBNAME [USERNAME]]`. The first non-option argument is the database
(or a full conninfo/URI); a second is the username.

**Most useful flags** (full list in [references/scripting.md](references/scripting.md) &
[references/connection.md](references/connection.md)):

| Flag | Meaning |
|------|---------|
| `-c CMD` | Run one SQL string **or** one backslash command, then exit (repeatable; combine with `-f`) |
| `-f FILE` | Run a SQL file then exit (gives line-numbered errors) |
| `-1` / `--single-transaction` | Wrap all `-c`/`-f` work in one `BEGIN`/`COMMIT` (all-or-nothing) |
| `-X` / `--no-psqlrc` | Skip `~/.psqlrc` — **always use in scripts** for reproducibility |
| `-q` / `-A` / `-t` | Quiet / unaligned / tuples-only (combine as `-qAt` for clean parsing) |
| `--csv` | CSV output mode (= `\pset format csv`) |
| `-F SEP` / `-R SEP` / `-z` / `-0` | Field / record separators; `-z`/`-0` use NUL (for `xargs -0`) |
| `-v NAME=VAL` | Set a `psql` variable (e.g. `-v ON_ERROR_STOP=1`) |
| `-o FILE` / `-L FILE` | Send query output to a file / log all output to a file too |
| `-x` | Expanded output (one column per line) |
| `-E` | Echo the hidden catalog query behind each `\d` command |
| `-h`/`-p`/`-U`/`-d` · `-w`/`-W` | Host / port / user / dbname · never-prompt / force-prompt for password |

**Output formats** (`\pset format X` or a flag): `aligned` (default), `unaligned`, **`csv`**,
`wrapped`, `html`, `asciidoc`, `latex`, `latex-longtable`, `troff-ms`. Toggle expanded rows with
`\x`.

## Connecting

Four interchangeable mechanisms (mix freely; conninfo > flags > env > service > defaults):

```bash
psql -h db.example.com -p 5432 -U me -d app          # discrete flags
psql "host=db user=me dbname=app sslmode=require"    # conninfo string
psql postgresql://me@db.example.com:5432/app         # URI
PGHOST=db PGUSER=me PGDATABASE=app psql              # environment variables
psql service=prod                                    # a ~/.pg_service.conf entry
```

- **No password on the command line** (it leaks via `ps`). Use **`~/.pgpass`** (lines of
  `host:port:db:user:password`, `chmod 0600`), the `PGPASSWORD` env var, or an interactive prompt.
- **`~/.pg_service.conf`** names a bundle of parameters: connect with `service=NAME`.
- **`\c [conninfo]`** reconnects mid-session; **`\conninfo`** shows the current connection.
- For TLS use `sslmode=verify-full`; for HA list comma-separated hosts +
  `target_session_attrs=read-write`.

Full reference (flags, `.pgpass`, service files, SSL, multi-host, precedence):
[references/connection.md](references/connection.md).

## Core Workflows

### 1. Inspect the schema (the `\d` family)

```sql
\l                      -- list databases
\dt                     -- list tables (\dv views, \di indexes, \dm matviews, \ds sequences)
\d orders               -- one relation: columns, types, indexes, constraints, triggers
\d+ orders              -- + storage, replica identity, access method, comments
\df pg_catalog.now      -- functions; \sf func shows the CREATE OR REPLACE source
\dn                     -- schemas;  \dx  installed extensions;  \du / \drg (pg16+) roles/grants
\dconfig work_mem       -- server config parameters (pattern-aware SHOW)        (pg15+)
```

Suffixes: `S` includes system objects, `+` adds detail, and in **pg18+** a trailing `x` on a
*listing* command forces expanded output (`\dt+x`). Add `-E` (or `\set ECHO_HIDDEN on`) to see the
catalog query a `\d` command runs — a great way to learn the catalogs. Full catalog:
[references/meta-commands.md](references/meta-commands.md).

### 2. Format & capture output

```sql
\x on                            -- expanded: one column per line (wide rows)
\pset null '(null)'              -- show NULLs visibly
\pset format csv                 -- CSV for the session (or --csv on the CLI)
\timing on                       -- print how long each statement takes
\o results.txt                   -- send subsequent output to a file (\o alone reverts)
SELECT * FROM big \g out.csv     -- one-shot: send THIS query's output to a file
SELECT * FROM big \g |less       -- one-shot: pipe THIS query's output to a command
```

### 3. Variables & interpolation

```sql
\set tbl orders
SELECT count(*) FROM :"tbl";                      -- :"x" = quoted identifier
\set cutoff '2026-01-01'
SELECT * FROM orders WHERE created >= :'cutoff';  -- :'x' = quoted literal (injection-safe)
SELECT count(*) AS n FROM orders \gset            -- store result columns into variables
\echo there are :n orders
\getenv home HOME                                 -- env var → psql variable               (pg15+)
```

Use `:'var'` / `:"var"` for any untrusted value; raw `:var` is unquoted (injection risk). For true
server-side parameter binding, see `\bind` ([references/pipeline.md](references/pipeline.md)).

### 4. Power tools

```sql
-- \gexec (pg9.6+): run query, then execute each result cell as SQL — metaprogramming
SELECT format('ANALYZE %I;', tablename) FROM pg_tables WHERE schemaname='public' \gexec

-- \watch: re-run on an interval (count= & named forms pg16+, min_rows= pg17+)
SELECT count(*) FROM jobs WHERE state='running' \watch interval=5 count=12

-- \crosstabview (pg9.6+): pivot a 3-column result into a grid
SELECT category, region, sum(amt) FROM sales GROUP BY 1,2 \crosstabview

-- \if family (pg10+): branch in scripts (pair with \gset)
SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='deploy') AS ok \gset
\if :ok
    \echo role present
\else
    CREATE ROLE deploy LOGIN;
\endif
```

### 5. Client-side `\copy` (no server file access)

```sql
\copy (SELECT * FROM orders WHERE created > now() - interval '1 day') TO 'recent.csv' WITH (FORMAT csv, HEADER)
\copy customers (id, name, email) FROM 'customers.csv' WITH (FORMAT csv, HEADER)
```

`\copy` streams the file through the **client**, so it uses *your* local paths/permissions — no
server superuser or `pg_read_server_files` needed (unlike SQL `COPY`).

## Non-Interactive / Agent Usage

Prefer one-shot, machine-readable invocations over the REPL. The canonical agent/CI pattern:

```bash
# Clean scalar: quiet, unaligned, tuples-only, ignore ~/.psqlrc
psql -qAtX -c "SELECT count(*) FROM orders"

# Structured output — CSV handles embedded commas/quotes/newlines safely
psql -X --csv -c "SELECT id, email FROM users WHERE active" > users.csv

# Fail fast with a detectable exit code (3) on any SQL error
psql -X -v ON_ERROR_STOP=1 -f migrate.sql

# All-or-nothing migration (single transaction, rolls back on error)
psql -X -1 -v ON_ERROR_STOP=1 -f migration.sql

# Multi-statement / mixed SQL + meta-commands via heredoc
psql -X <<'SQL'
\timing on
INSERT INTO t SELECT * FROM staging;
SELECT count(*) FROM t;
SQL

# Pass values safely as quoted literals/identifiers
psql -X -v tbl=orders -v d='2026-01-01' \
  -c "SELECT count(*) FROM :\"tbl\" WHERE created >= :'d'"
```

**Exit codes:** `0` ok · `1` fatal psql error (bad option, file not found) · `2` connection
failed/lost (non-interactive) · `3` SQL error **with** `ON_ERROR_STOP` set. So `ON_ERROR_STOP=1`
is what turns a failed statement into a non-zero exit.

**Agent tips:** always pass **`-X`** (ignore `~/.psqlrc`); use **`-qAt`** or **`--csv`** for
parseable output; set **`ON_ERROR_STOP=1`**; use `-1` for atomic multi-statement scripts; pass
external values via `-v` + `:'…'`/`:"…"` (never string-concatenate); set `FETCH_COUNT` for huge
result sets to bound memory. Full guide: [references/scripting.md](references/scripting.md).

## Extended Protocol & Pipelines

By default `psql` uses the simple query protocol. A small family drives the **extended** protocol
for safe parameter binding and request pipelining:

```sql
SELECT $1::int + $2::int \bind 3 4 \g          -- bind params, extended protocol      (pg16+)
SELECT $1 \parse stmt1                          -- named prepared statement            (pg18+)
\bind_named stmt1 'value' \g                    --   execute it with parameters        (pg18+)
```

`\bind` (pg16+) is the safest way to pass parameters from `psql`. The named-statement and
**pipeline** commands (`\startpipeline`/`\sendpipeline`/`\endpipeline`/`\getresults`/…) are
**pg18+** — they were absent from pg16 and pg17. Details and the full command list:
[references/pipeline.md](references/pipeline.md).

## Quick Reference

| Item | Purpose |
|------|---------|
| `psql -c "SQL"` / `psql -f f.sql` | Run one command / a file, then exit |
| `psql -qAtX -c "SQL"` | Quiet, unaligned, tuples-only, no `.psqlrc` — clean script output |
| `psql --csv -c "SQL"` | CSV output (RFC-4180 quoting) for parsing |
| `psql -X -1 -v ON_ERROR_STOP=1 -f m.sql` | Atomic, fail-fast migration |
| `\d` · `\dt` · `\d+ t` · `\df` · `\dn` · `\dx` · `\l` | Inspect: relation / tables / detail / functions / schemas / extensions / databases |
| `\dconfig` (pg15+) · `\drg` (pg16+) · `\dX` (pg14+) | Server config / role grants / extended stats |
| `\g [file\|\|cmd]` · `\gx` · `\o file` | Send query (redirect) / expanded / persistent output redirect |
| `\gexec` (pg9.6+) · `\gset` · `\gdesc` (pg11+) | Run results as SQL / capture into vars / describe columns |
| `\watch [i=][c=][m=]` · `\crosstabview` (pg9.6+) | Re-run on interval / pivot to a grid |
| `\if`/`\elif`/`\else`/`\endif` (pg10+) | Script conditionals (pair with `\gset`) |
| `\set` · `:var` / `:'var'` / `:"var"` | Variables / raw / quoted-literal / quoted-identifier interpolation |
| `\pset format csv\|unaligned` · `\x` · `\t` · `\a` · `\timing` | Output mode / expanded / tuples-only / align toggle / timings |
| `\copy … FROM\|TO 'file' (FORMAT csv, HEADER)` | Client-side import/export (local file perms) |
| `\c [conninfo]` · `\conninfo` · `\password` | Reconnect / show connection / change password safely |
| `\bind` (pg16+) · `\parse`/`\bind_named`/pipelines (pg18+) | Extended-protocol & pipeline commands |
| `\?` · `\h SQL` · `\q` | Backslash help / SQL syntax help / quit |
| `~/.pgpass` · `~/.pg_service.conf` · `~/.psqlrc` | Password file / connection services / startup script |

## Troubleshooting

- **`psql: command not found`** — install the client (`postgresql-client`, or `brew install
  libpq` and add it to `PATH`); it's separate from the server.
- **`could not connect to server` / `Connection refused`** — wrong host/port, server down, or
  `pg_hba.conf`/firewall. Check `-h`/`-p`, that the server listens, and try `psql -h localhost` vs
  the socket. (`pg_hba.conf` and `listen_addresses` are **postgres-admin** topics.)
- **`fe_sendauth: no password supplied`** — add a `~/.pgpass` entry (`chmod 0600`), set
  `PGPASSWORD`, or pass `-W` to prompt. A wrong-permissions `.pgpass` is silently ignored.
- **`-c` won't mix SQL and a backslash command** — one `-c` is *either* SQL *or* one meta-command.
  Use repeated `-c`, a heredoc, or `-f`.
- **A newer meta-command errors** (`invalid command \…`) — your **client** is too old. Check
  `psql --version` and [references/version-features.md](references/version-features.md). E.g.
  pipelines/`\parse`/`\close_prepared` are pg18+, `\getenv`/`\dconfig` pg15+, `\bind` pg16+.
- **`\restrict` errors when restoring a dump** — the dump was made by a newer `pg_dump`; restore
  with a `psql` at least as new (the 2025-08 security backport, see version-features.md).
- **Script keeps going after an error** — set `ON_ERROR_STOP=1` (default is to continue). Wrap with
  `-1` for atomicity.
- **Output is misaligned/garbled in a pipe** — the pager or alignment is interfering; use `-qAt` or
  `--csv`, and `-X` to ignore a personal `~/.psqlrc`.
- **`\d` shows less/more than expected** — server-version dependent; some columns only appear when
  the **server** is new enough, regardless of client version.

## References

For exhaustive detail, see the bundled reference files:

- [references/meta-commands.md](references/meta-commands.md) — every backslash command, grouped:
  the `\d` inspection family, query execution (`\g`/`\gexec`/`\gset`/`\watch`/`\crosstabview`),
  formatting (`\pset`/`\x`), variables, conditionals, `\copy`, connection & system commands, with
  inline `(pgNN+)` tags.
- [references/connection.md](references/connection.md) — conninfo strings & URIs, all `PG*`
  environment variables, `~/.pgpass`, connection service files, SSL/multi-host, `\c`, and
  precedence rules.
- [references/scripting.md](references/scripting.md) — non-interactive/agent patterns,
  `ON_ERROR_STOP`/exit codes, transactions (`-1`/`AUTOCOMMIT`/`ON_ERROR_ROLLBACK`), the special
  control variables, interpolation, `FETCH_COUNT` streaming, `.psqlrc`, and psql environment vars.
- [references/pipeline.md](references/pipeline.md) — the extended-protocol & pipeline meta-commands
  (`\bind`, `\parse`, `\bind_named`, `\close_prepared`, `\startpipeline`/…), with the pg16/pg18
  version story.
- [references/version-features.md](references/version-features.md) — feature → minimum-version map
  with postgresql.org sources (what's bedrock vs. added in pg14–pg19, plus the `\restrict` backport).

## Resources

- **Help**: `psql --help`, `\?` (meta-commands), `\? variables`, `\h` (SQL syntax)
- **psql reference**: https://www.postgresql.org/docs/current/app-psql.html
- **libpq connection strings**: https://www.postgresql.org/docs/current/libpq-connect.html
- **Release notes (per-version feature history)**: https://www.postgresql.org/docs/release/
