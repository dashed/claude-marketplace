---
name: duckdb
description: DuckDB — the in-process, columnar, vectorized OLAP SQL engine shipped as a single zero-dependency binary ("SQLite for analytics"). Use when querying Parquet/CSV/JSON files directly with SQL and no load step, doing in-process analytical/OLAP queries and aggregations, using the `duckdb` CLI shell (interactive REPL or `-c`/`-json` one-shots for scripts and agents), writing "friendly SQL" (FROM-first, `SELECT * EXCLUDE`, `GROUP BY ALL`, `SUMMARIZE`, `PIVOT`), converting CSV↔Parquet↔JSON with `COPY`, reading remote data over HTTP/S3 via the httpfs extension, or `ATTACH`-ing a live Postgres/MySQL/SQLite database. Triggers on mentions of duckdb, the `duckdb` command, `.duckdb` files, replacement scans, `read_parquet`/`read_csv`, httpfs/`CREATE SECRET`, or "embedded analytics database". This is the DuckDB CLI and SQL dialect, NOT a generic SQL tutorial and NOT the DuckDB client libraries (Python/Node/Java — defer those to duckdb.org).
---

# DuckDB - In-Process Analytical SQL Engine

## Overview

DuckDB is **"SQLite for analytics"**: an **in-process** (embedded — no server, no daemon, no
network) **OLAP** database that runs inside the `duckdb` process itself. It is **columnar and
vectorized** (it processes batches of column values rather than row-at-a-time), which makes
aggregations and scans over large tables fast. A database is **a single file** (`my.db`) or
purely **in-memory** (`:memory:`); it is **ACID** (MVCC transactions); and it ships as a
**single zero-dependency binary**. Its superpower for CLI and agent work: **files are tables** —
you can `SELECT` straight out of CSV / Parquet / JSON (local, globbed, or over HTTP/S3) with
**no import step**.

**Key characteristics:**
- **In-process / embedded** — runs in the `duckdb` process; no server to start, no port to open
- **Columnar + vectorized OLAP** — built for analytical scans and aggregations, not point lookups
- **Files are tables** — `FROM 'data.parquet'` queries the file directly (replacement scans)
- **Single binary, zero deps** — one executable is the whole engine; `:memory:` or a single `.db` file
- **ACID** — MVCC transactions, single-file storage; one read-write process at a time
- **Postgres-ish dialect + "friendly SQL"** — familiar SQL plus ergonomic extras (FROM-first, `EXCLUDE`, `GROUP BY ALL`, `SUMMARIZE`)

> **Disambiguation:** This skill documents the **`duckdb` CLI and its SQL dialect** — the shell,
> output modes, replacement scans, `COPY`, `ATTACH`, extensions, and friendly-SQL syntax. It is
> **not** a generic SQL course, and it does **not** cover the DuckDB **client libraries**
> (Python, Node.js, Java, R, Go, etc.) — for embedding DuckDB in an application, use the API docs
> at https://duckdb.org/docs/.

## When to Use This Skill

| Use DuckDB when… | Prefer something else when… |
|---|---|
| Ad-hoc analytical queries over CSV / Parquet / JSON files | Heavy **concurrent multi-writer OLTP** → Postgres/MySQL |
| Local data science, one-off aggregations, reshaping | You need a **shared network DB server** → Postgres/MySQL |
| ETL: convert CSV↔Parquet, repartition, clean | A tiny embedded **transactional** app store → SQLite is fine |
| Querying remote Parquet on S3/HTTP without downloading it | Row-by-row record lookups by primary key at scale |
| A fast SQL scratchpad in the terminal, scripts, or CI | |

- **vs SQLite:** same "embedded single-file" feel, but DuckDB is columnar/OLAP where SQLite is
  row-store/OLTP. DuckDB can read SQLite files via the `sqlite_scanner` extension.
- **vs Postgres:** no server, no roles, no network — but DuckDB speaks a Postgres-compatible-ish
  dialect *plus* friendly-SQL extras, and can `ATTACH` a live Postgres database.

## Prerequisites

**CRITICAL**: Before proceeding, verify DuckDB is installed and check the version:

```bash
duckdb -version        # prints e.g. "v1.3.2 (Ossivalis) 0b83e5d2f6"
```

**Version note:** This skill is documented against the DuckDB CLI surface as of **v1.3.x
"Ossivalis"** for the core examples; the current released line is **1.5.x** (1.4 is the LTS).
Long-standing SQL and CLI features (everything stable at or before the **1.0.0 GA**) are
"bedrock" and shown **unannotated**. Features added in a specific release are tagged inline as
`(duckdb vX.Y+)` **only where a duckdb.org release blog sources them** — see
[references/version-features.md](references/version-features.md) for the full feature → version
map with citations. Always confirm on the running build with `duckdb -version`.

**If DuckDB is not installed:** it is a single self-contained binary with no dependencies.

## Install

DuckDB is **one file, no deps** — install the binary and you have the whole engine.

```bash
# macOS (Homebrew)
brew install duckdb

# Linux/macOS — official install script (installs to ~/.duckdb/cli, adds to PATH)
curl https://install.duckdb.org | sh

# Or download a static binary from https://duckdb.org/docs/installation
# Verify:
duckdb -version          # → v1.3.2 (Ossivalis) 0b83e5d2f6  (example)
```

## The `duckdb` CLI at a Glance

These six invocations cover ~90% of CLI usage:

```bash
duckdb                          # in-memory scratch REPL (nothing is persisted)
duckdb mydb.db                  # open/create a persistent database file
duckdb -c "FROM 'data.csv'"     # run one SQL command and exit (ideal for scripts/agents)
duckdb -json -c "SELECT 42"     # machine-readable output (best for parsing)
echo "SELECT 1" | duckdb        # pipe SQL in via stdin
duckdb data.parquet -c 'FROM data LIMIT 5'   # open a data FILE directly as the DB (duckdb v1.3+)
```

**Usage:** `duckdb [OPTIONS] [FILENAME] [SQL]`. `FILENAME` is a DuckDB database file (created if
absent); omit it (or pass `:memory:`) for an in-memory database. A trailing `SQL` argument runs
and then drops into the REPL.

**Most useful flags** (full list in [references/cli.md](references/cli.md)):

| Flag | Meaning |
|------|---------|
| `-c COMMAND` | Run COMMAND and **exit** (primary non-interactive entrypoint; `-s` is an alias) |
| `-f FILE` | Read/run a SQL file, then exit |
| `-init FILE` | Run a file on startup, then continue (default `~/.duckdbrc`) |
| `-readonly` | Open a **file** database read-only (safe for untrusted/agent queries; errors against `:memory:`) |
| `-json` / `-csv` / `-markdown` / `-box` | One-shot output mode (equivalent to `.mode <mode>`) |
| `-noheader` | Suppress column headers (cleaner parsing) |
| `-bail` | Stop after the first error (exit code is non-zero on error) |
| `-safe` | Safe-mode: restrict filesystem/external access (duckdb v1.2+) |

**Output modes** (set with a flag or `.mode MODE`): `duckbox` (default pretty box), **`json`**
(array of row objects — best for agents/scripts), `csv`, `markdown`, `table`, `line`,
`jsonlines`, `insert`, and more.

**Dot-commands** (SQLite-style, in the REPL): `.mode`, `.tables`, `.schema`, `.open FILE`,
`.read FILE`, `.output FILE`, `.timer on`, `.maxrows N`, `.help`, `.quit`. Full list in
[references/cli.md](references/cli.md).

## Core Workflows

### 1. Query a file without importing it

`FROM 'path'` auto-detects the format by extension and content — no `CREATE TABLE`, no load step.

```bash
duckdb -c "FROM 'sales.csv' WHERE region = 'EU' LIMIT 10"
duckdb -c "SELECT region, sum(amount) FROM 'sales.parquet' GROUP BY ALL"
duckdb -c "FROM 'logs/**/*.json'"          # recursive glob across many files
```

Note: `'single quotes'` = a **string literal / file path**; `"double quotes"` = an
**identifier** (column/table). So `FROM 'x.csv'` reads the file; `FROM x` references a table.

### 2. Persistent database vs. in-memory

```bash
# In-memory: fast scratchpad, everything is GONE on exit
duckdb -c "CREATE TABLE t AS FROM 'raw.parquet'; SELECT count(*) FROM t"

# Persistent: open a file path to keep the data
duckdb shop.db -c "CREATE TABLE orders AS FROM 'raw.parquet'"
duckdb shop.db -c "SELECT count(*) FROM orders"   # data is still there next run
```

Open the REPL on a file (`duckdb shop.db`) and use `.tables` / `.schema` to inspect it.

### 3. Convert formats with `COPY … TO`

```bash
# CSV → Parquet (zstd-compressed)
duckdb -c "COPY (FROM 'in.csv') TO 'out.parquet' (FORMAT parquet, COMPRESSION zstd)"

# Table → CSV with a header
duckdb shop.db -c "COPY orders TO 'orders.csv' (HEADER, DELIMITER ',')"

# Partitioned (Hive-layout) write
duckdb -c "COPY (FROM 'events.parquet') TO 'out_dir' (FORMAT parquet, PARTITION_BY (year, month))"
```

Supported formats: `parquet`, `csv`, `json`. See [references/data-io.md](references/data-io.md)
for all options, plus `EXPORT DATABASE` / `IMPORT DATABASE` for whole-database snapshots.

### 4. Explore unknown data with friendly SQL

```bash
# Per-column stats: min/max/approx_unique/avg/std/quartiles/null%
duckdb -c "SUMMARIZE FROM 'mystery.parquet'"

# Column names + types
duckdb -c "DESCRIBE FROM 'mystery.parquet'"

# Drop noisy columns from a star-select; FROM-first is valid too
duckdb -c "FROM 'mystery.parquet' SELECT * EXCLUDE (internal_id, raw_blob) LIMIT 20"
```

Friendly-SQL highlights (all bedrock): **FROM-first** (`FROM t SELECT …` or bare `FROM t`),
`SELECT * EXCLUDE (…)` / `REPLACE (…)`, `COLUMNS('regex')`, `GROUP BY ALL`, `ORDER BY ALL`,
`QUALIFY`, `PIVOT` / `UNPIVOT`, `USING SAMPLE`, and `UNION [ALL] BY NAME`. Full reference:
[references/sql-dialect.md](references/sql-dialect.md).

### 5. Query remote data over HTTP / S3 (httpfs)

```bash
duckdb <<'SQL'
INSTALL httpfs; LOAD httpfs;          -- most core extensions autoload, but this is explicit
CREATE SECRET s3 (TYPE s3, PROVIDER credential_chain, REGION 'us-east-1');
FROM 's3://my-bucket/year=2026/*.parquet' LIMIT 100;
SQL
```

`CREATE SECRET` is the modern auth path (it replaces the old `SET s3_*` settings); use
`PROVIDER credential_chain` to pick up the AWS default credential chain, or pass
`KEY_ID`/`SECRET` explicitly. You can also read plain `https://…/file.parquet` URLs directly.

### 6. `ATTACH` a live Postgres / SQLite database

```bash
# Read a SQLite file as a catalog (sqlite_scanner extension)
duckdb -c "ATTACH 'app.db' AS s (TYPE sqlite); FROM s.users LIMIT 10"

# Query a live Postgres database (postgres extension)
duckdb <<'SQL'
ATTACH 'host=db.example.com dbname=app user=me' AS pg (TYPE postgres);
SELECT count(*) FROM pg.public.orders;
-- copy a Postgres table into a local DuckDB table:
CREATE TABLE local_orders AS FROM pg.public.orders;
SQL
```

`TYPE sqlite | postgres | mysql` selects the scanner (each autoloads its extension). Use
`USE pg;` to set the default catalog and `DETACH pg;` when done. More in
[references/data-io.md](references/data-io.md).

## Non-Interactive / Agent Usage

DuckDB is excellent for scripts and agents — prefer one-shot, machine-readable invocations over
the REPL:

```bash
# One-shot, JSON out (the safest format to parse)
duckdb -json -c "SELECT count(*) AS n FROM 'events.parquet'"

# Multi-statement via heredoc
duckdb mydb.db <<'SQL'
CREATE TABLE t AS FROM 'in.csv';
COPY t TO 'out.parquet';
SQL

# Read-only guard when opening an existing database file (untrusted queries)
duckdb -readonly mydb.db -c "FROM orders LIMIT 100"
# (Reading external files like Parquet/CSV/JSON needs NO -readonly — and -readonly
#  requires a file DB; it errors against the default :memory: database.)

# CSV out (no header) piped to another tool
duckdb -csv -noheader -c "SELECT id FROM t" | sort -u
```

**Agent tips:** prefer `-json`; use `-readonly` when opening an existing **file** database to
guard against writes (it errors against `:memory:`, and isn't needed just to read external
files); use `-c`/`-f`/heredoc rather than the interactive REPL; use `:memory:` when no
persistence is needed; combine with `-bail` so the exit code is non-zero on error.

## Quick Reference

| Item | Purpose |
|------|---------|
| `duckdb` / `duckdb file.db` | In-memory REPL / open-or-create a persistent database |
| `duckdb -c "SQL"` | Run one command and exit (`-s` is an alias) |
| `duckdb -json -c "SQL"` | Run and emit a JSON array of rows (best for parsing) |
| `duckdb -f FILE` / `duckdb -readonly file.db` | Run a SQL file / open a file DB read-only (not `:memory:`) |
| `FROM 'f.csv'` · `FROM 'f.parquet'` · `FROM 'd/**/*.json'` | Replacement scans — query files directly (globs OK) |
| `read_csv` / `read_parquet` / `read_json[_auto]` | Explicit readers with params (`header :=`, `types :=`, `hive_partitioning :=`) |
| `COPY (…) TO 'f.parquet' (FORMAT parquet)` | Write query results to a file (`parquet`/`csv`/`json`) |
| `EXPORT DATABASE 'dir'` / `IMPORT DATABASE 'dir'` | Snapshot / restore an entire database |
| `ATTACH 'x' AS a (TYPE sqlite\|postgres\|mysql)` | Query another database live; `USE a;` / `DETACH a;` |
| `INSTALL httpfs; LOAD httpfs;` | Read/write over HTTP(S) and S3 (most core extensions autoload) |
| `CREATE SECRET (…)` | Store credentials for S3/HTTP and other providers |
| `SUMMARIZE t` / `DESCRIBE t` | Per-column stats / column names + types |
| `FROM t SELECT * EXCLUDE (c)` · `GROUP BY ALL` | Friendly-SQL ergonomics |
| `.mode json` · `.tables` · `.schema` · `.read f.sql` | Common REPL dot-commands |
| `PRAGMA version;` · `SET memory_limit='4GB';` · `SET threads=4;` | Introspection / resource limits |
| `EXPLAIN` / `EXPLAIN ANALYZE` | Query plan / profiled plan with timings |

## Troubleshooting

- **`:memory:` loses everything on exit** — open a **file path** (`duckdb my.db`) to persist data.
- **`-c` runs one statement set then exits** — for multiple statements, separate with `;`, or use
  a heredoc, `-f script.sql`, or `.read script.sql`.
- **Single vs double quotes** — `'…'` is a string literal / file path; `"…"` is an identifier
  (column/table). `FROM 'x.csv'` (read file) vs `FROM x` (table named `x`).
- **`IO Error: No files found that match the pattern …`** — it's a path/glob problem, not SQL.
  Check the working directory and the glob (`*.parquet` vs `**/*.parquet`).
- **`Catalog Error: … does not exist`** — usually an unloaded extension; run `INSTALL ext; LOAD
  ext;` (though most core extensions autoload on first use). Inspect with
  `SELECT extension_name, installed, loaded FROM duckdb_extensions();`.
- **A newer feature errors out** (`Parser`/`Binder`/`Catalog Error`) — your build may be too old.
  Check `duckdb -version` and see [references/version-features.md](references/version-features.md)
  for the minimum version of each feature. `MERGE INTO` (duckdb v1.4+), `VARIANT` (duckdb v1.5+),
  and `ATTACH … (COMPRESS …)` (duckdb v1.4+), for example, won't run on 1.3.x. (Database
  encryption is a documented 1.4 feature, but the `ENCRYPTION_KEY` option already works in 1.3.x.)
- **Lambda arrow deprecation** — `x -> x+1` warns on newer builds (duckdb v1.5+); prefer the
  Python-style `lambda x: x+1` (duckdb v1.3+).
- **One writer at a time** — a DB file opened read-write by one process blocks others. Use
  `-readonly` to allow concurrent readers.

## References

For exhaustive detail, see the bundled reference files:

- [references/cli.md](references/cli.md) — the `duckdb` shell: every command-line flag, all output
  modes, the full dot-command list, and non-interactive/agent patterns.
- [references/sql-dialect.md](references/sql-dialect.md) — "friendly SQL": FROM-first, `EXCLUDE`/
  `REPLACE`/`COLUMNS`, `GROUP BY ALL`, `QUALIFY`, `PIVOT`/`UNPIVOT`, joins (`ASOF`/`POSITIONAL`),
  nested types, lambdas, and DDL/DML ergonomics.
- [references/data-io.md](references/data-io.md) — replacement scans, `read_*` readers, `COPY`,
  `EXPORT`/`IMPORT DATABASE`, `ATTACH`, extensions, and httpfs/S3 secrets.
- [references/version-features.md](references/version-features.md) — feature → minimum-version map
  with duckdb.org release-blog citations (what's bedrock vs. added in 1.1–1.5).

## Resources

- **Help**: `duckdb -help`, `.help` in the REPL, `.help -all`
- **Official docs**: https://duckdb.org/docs/
- **Friendly SQL**: https://duckdb.org/docs/stable/sql/dialect/friendly_sql
- **Extensions**: https://duckdb.org/docs/stable/extensions/overview
