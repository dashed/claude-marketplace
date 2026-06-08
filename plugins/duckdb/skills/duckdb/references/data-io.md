# DuckDB Data I/O & Extensions Reference

How DuckDB reads and writes external data — querying files in place, `COPY`/`EXPORT`,
attaching other databases, Excel, the extension system (httpfs/S3, spatial, fts, …), and
plan/introspection ops. **Scope is the `duckdb` CLI + SQL surface**; client libraries are out
of scope (see duckdb.org/docs).

> **Version annotations.** Most of this reference is **bedrock** — present at or before the
> 1.0.0 GA — and is left unannotated. Features added later carry a `(duckdb vX.Y+)` tag sourced
> to a duckdb.org release blog (links at the bottom). Everything **unannotated was empirically
> confirmed on the installed `duckdb` CLI v1.3.2 "Ossivalis"** unless a note says otherwise.
> Confirm your build with `duckdb -version`, and never assume an option exists — check
> `duckdb -c "FROM duckdb_functions() WHERE function_name = '<fn>'"` or the docs.

## Contents

- [Files as tables (replacement scans)](#files-as-tables-replacement-scans)
- [Explicit readers and their options](#explicit-readers-and-their-options)
- [Globs, multi-file reads, Hive partitioning](#globs-multi-file-reads-hive-partitioning)
- [Writing data — `COPY … TO`](#writing-data--copy--to)
- [Whole-database snapshots — `EXPORT` / `IMPORT DATABASE`](#whole-database-snapshots--export--import-database)
- [`ATTACH` — query other databases live](#attach--query-other-databases-live)
- [Excel](#excel)
- [The extension system](#the-extension-system)
- [httpfs, S3/GCS/R2, and `CREATE SECRET`](#httpfs-s3gcsr2-and-create-secret)
- [Plans and introspection (ops)](#plans-and-introspection-ops)

---

## Files as tables (replacement scans)

DuckDB's headline feature: **files are tables**. `FROM 'path'` auto-detects the format from the
extension and content and reads it with **no load step**.

```sql
FROM 'data.csv';            -- dispatches to read_csv (auto-detect)
FROM 'data.parquet';        -- read_parquet
FROM 'data.json';           -- read_json (auto)
FROM 'data/*.parquet';      -- glob
FROM 'data/**/*.parquet';   -- recursive glob
```

`FROM 'file'` is shorthand for `SELECT * FROM 'file'` (DuckDB's FROM-first syntax). It works
anywhere a table does — in CTAS, subqueries, joins, `SUMMARIZE`, etc.:

```sql
CREATE TABLE sales AS FROM 'sales.csv';        -- import into a real table
SELECT region, sum(amt) FROM 'sales.csv' GROUP BY ALL;
SUMMARIZE FROM 'data.parquet';                  -- per-column stats without loading
```

> **Confirmed on 1.3.2:** `FROM 't.csv'`, `FROM 't.parquet'`, `FROM 't.json'`, and recursive
> globs all work. A bad path raises `IO Error: No files found that match the pattern …` — that
> is a path/glob problem, not a SQL problem.

You can also open a **data file directly as the database argument** *(duckdb v1.3+)*, which
exposes it as a view named `file` (and a view named after the file):

```bash
duckdb data.parquet -c 'FROM data LIMIT 5'
```

## Explicit readers and their options

Use the explicit table functions when you need control over parsing. Each has an `_auto`
variant that turns on full auto-detection; the base function lets you pin options.

| Reader | Purpose |
|---|---|
| `read_csv(path, …)` / `read_csv_auto(path)` | CSV/TSV; `_auto` sniffs delimiter, header, types |
| `read_parquet(path, …)` | Parquet (also `parquet_scan`) |
| `read_json(path, …)` / `read_json_auto(path)` | JSON / NDJSON (also `read_ndjson`, `read_ndjson_auto`) |

Named arguments use `:=` or `=` (both accepted in the CLI):

```sql
FROM read_csv('sales.csv',
    header = true,
    delim = ',',                       -- alias: sep
    columns = {'id': 'INT', 'amt': 'DOUBLE'},   -- explicit schema (skips sniffing)
    nullstr = ['NA', ''],
    ignore_errors = true,              -- skip malformed rows instead of failing
    sample_size = -1                   -- -1 = scan all rows when sniffing types
);

FROM read_parquet('events.parquet');
FROM read_json_auto('records.ndjson');
```

**Commonly used options** (do not invent others — check the docs for the full list):

| Option | Reader(s) | Effect |
|---|---|---|
| `header` | csv | first row is column names |
| `delim` / `sep` | csv | field delimiter |
| `quote`, `escape` | csv | quoting characters |
| `columns` / `types` | csv | pin column names/types explicitly |
| `nullstr` | csv | string(s) that mean NULL |
| `ignore_errors` | csv, json | skip rows that fail to parse |
| `sample_size` | csv | rows used for type sniffing (`-1` = all) |
| `union_by_name` | all | align multi-file schemas **by column name**, not position |
| `filename` | all | add a `filename` column tagging each row's source file |
| `hive_partitioning` | all | parse `key=value` directory names into columns |
| `compression` | csv, json | `gzip`/`zstd`/`auto` for compressed inputs |
| `encoding` | csv | input encoding, e.g. `latin-1`, `utf-16` *(duckdb v1.2+)* |
| `strict_mode` | csv | stricter RFC-4180 parsing toggle *(duckdb v1.2+)* |

> **Confirmed on 1.3.2:** `read_csv` with `header`/`delim`/`columns`, `read_json_auto` on
> NDJSON, and `union_by_name` + `filename` across a file list (see below).

## Globs, multi-file reads, Hive partitioning

Pass a glob, a brace pattern, or an explicit **list** of paths; all matching files are read as
one relation.

```sql
FROM 'logs/2024-*.csv';                          -- glob
FROM 'data/**/*.parquet';                        -- recursive glob
FROM read_csv(['jan.csv', 'feb.csv'], union_by_name = true, filename = true);
FROM 'data/file.{csv,parquet}';                  -- brace expansion
```

`union_by_name = true` reconciles differing schemas across files by column name (missing
columns become NULL); `filename = true` adds the source path:

```text
┌───────┬─────────┬─────────┬──────────┐
│  id   │    a    │    b    │ filename │
│ 1     │ x       │ NULL    │ f1.csv   │
│ 2     │ NULL    │ y       │ f2.csv   │
└───────┴─────────┴─────────┴──────────┘
```

**Hive partitioning** turns `key=value` directory names into queryable columns:

```sql
FROM read_parquet('events/**/*.parquet', hive_partitioning = true)
WHERE year = 2024 AND month = 1;     -- partition columns also enable pruning
```

> **Confirmed on 1.3.2:** recursive globs, `read_csv([...], union_by_name=true, filename=true)`,
> and `hive_partitioning=true` round-tripped through a partitioned write.

## Writing data — `COPY … TO`

`COPY` writes a table or query result to a file. The target format is inferred from the
extension or set explicitly with `FORMAT`.

```sql
COPY (FROM 'in.csv') TO 'out.parquet' (FORMAT parquet, COMPRESSION zstd);
COPY tbl TO 'out.csv'  (HEADER, DELIMITER ',');
COPY tbl TO 'out.json';                                  -- NDJSON by default
COPY tbl TO 'out.json' (FORMAT json, ARRAY true);        -- single JSON array
```

**Formats:** `parquet`, `csv`, `json`.

**Parquet options:** `COMPRESSION` (`snappy` default · `zstd` · `gzip` · `lz4` · `uncompressed`),
`ROW_GROUP_SIZE`, `FIELD_IDS`. *(duckdb v1.2+)* adds Bloom filters and DELTA/`BYTE_STREAM_SPLIT`
encodings on the Parquet writer.

**Partitioned writes** lay out a Hive directory tree, one file per partition:

```sql
COPY tbl TO 'out_dir' (FORMAT parquet, PARTITION_BY (year, month));
```

By default DuckDB refuses to write into a non-empty target directory. Control that with:

| Clause | Behavior |
|---|---|
| `OVERWRITE_OR_IGNORE` | write into an existing directory, leaving unrelated files |
| `OVERWRITE` | clear matching partition data before writing |
| `APPEND` | add files alongside existing ones |

```sql
COPY tbl TO 'out_dir' (FORMAT parquet, PARTITION_BY (region), OVERWRITE_OR_IGNORE);
```

> **Confirmed on 1.3.2:** `COPY (FROM 'sales.csv') TO 'out.parquet' (FORMAT parquet, COMPRESSION
> zstd)`; CSV with `HEADER`/`DELIMITER`; JSON output; and `PARTITION_BY (region)` produced
> `out_dir/region=EU/data_0.parquet`, `…/region=US/data_0.parquet`.

## Whole-database snapshots — `EXPORT` / `IMPORT DATABASE`

`EXPORT DATABASE` dumps an entire database (schema + data) to a directory; `IMPORT DATABASE`
recreates it.

```sql
EXPORT DATABASE 'target_dir' (FORMAT parquet);   -- also: (FORMAT csv), (FORMAT parquet, COMPRESSION zstd)
IMPORT DATABASE 'target_dir';
```

`EXPORT` writes three things into the directory: `schema.sql` (DDL), `load.sql` (the `COPY`
statements), and one data file per table.

> **Confirmed on 1.3.2:** `EXPORT DATABASE 'exp' (FORMAT parquet)` produced `schema.sql`,
> `load.sql`, and `t.parquet`; `IMPORT DATABASE 'exp'` rebuilt the table. **To restore, use
> `IMPORT DATABASE`** — running `.read load.sql` alone replays only the `COPY` half and skips the
> DDL in `schema.sql`.

## `ATTACH` — query other databases live

`ATTACH` mounts another database under a catalog alias so you can query (and often write to) it
inline. The `TYPE` selects the backend; the matching extension autoloads.

```sql
ATTACH 'other.duckdb' AS o;                          -- another DuckDB file
ATTACH 'other.duckdb' AS o (READ_ONLY);              -- mount read-only
ATTACH 'data.sqlite'  AS s (TYPE sqlite);            -- SQLite  (sqlite_scanner)
ATTACH 'host=localhost dbname=app' AS p (TYPE postgres);   -- Postgres (postgres_scanner)
ATTACH 'host=localhost database=app' AS m (TYPE mysql);    -- MySQL    (mysql_scanner)
DETACH o;
USE o;                                               -- set the default catalog
```

Reference cross-database objects as `catalog.schema.table` (or `catalog.table`). Reads and, for
most backends, writes pass through:

```sql
SELECT * FROM s.customers;                           -- read from attached SQLite
CREATE TABLE o.summary AS FROM p.public.orders;      -- DuckDB ← Postgres
INSERT INTO p.public.audit SELECT * FROM local_tbl;  -- write-through to Postgres
```

**Bulk copy a whole database between catalogs** *(duckdb v1.2+)*:

```sql
ATTACH 'src.duckdb' AS src (READ_ONLY);
ATTACH ':memory:'   AS dst;
COPY FROM DATABASE src TO dst;                        -- schema + data
```

**Storage / encryption options:**

| Option | Meaning | Version |
|---|---|---|
| `READ_ONLY` | mount without write access | bedrock |
| `STORAGE_VERSION 'v1.2.0'` | opt a new DB file into a newer storage format | *(duckdb v1.2+)* |
| `ENCRYPTION_KEY '…'` | AES-256 encrypted database file | see note below |
| `COMPRESS` | compressed in-memory database | *(duckdb v1.4+)* |

> **Confirmed on 1.3.2:** `ATTACH … (TYPE sqlite)`, cross-DB `CREATE TABLE o.t AS FROM …`,
> `COPY FROM DATABASE … TO …`, and `STORAGE_VERSION`.
>
> ⚠️ **`ENCRYPTION_KEY` works on 1.3.2** despite being announced as a 1.4.0 feature. Empirically,
> `ATTACH 'e.db' AS e (ENCRYPTION_KEY 'secret')` created a genuinely encrypted file (the on-disk
> magic is `DUCKA`, not `DUCK`; reopening without the key fails with *"Cannot open encrypted
> database … without a key"*). Treat **database encryption as officially `(duckdb v1.4+)`** (the
> documented/stable version) but be aware older 1.3.x builds already accept the option. By
> contrast, the in-memory `(COMPRESS)` option **does** fail on 1.3.2
> (`Binder Error: Unrecognized option for attach "compress"`), confirming it as 1.4.0.

## Excel

Two paths to spreadsheets:

```text
.excel              -- dot-command: open the NEXT query result in your spreadsheet app
```

```sql
-- the `excel` extension (autoloads on first use) provides:
FROM read_xlsx('book.xlsx', sheet = 'Sheet1');
COPY tbl TO 'out.xlsx' (FORMAT xlsx, HEADER true);
```

The legacy approach reads `.xlsx` via the `spatial` extension's `st_read` (GDAL); the dedicated
`excel` extension's `read_xlsx` / `FORMAT xlsx` is the modern path. (Network install needed —
not exercised on the offline 1.3.2 check.)

## The extension system

**Model:** `INSTALL name; LOAD name;`. Most **core** extensions **autoload** on first use, so you
rarely type these explicitly. Inspect state with `duckdb_extensions()`:

```sql
INSTALL httpfs; LOAD httpfs;
SELECT extension_name, installed, loaded, install_mode FROM duckdb_extensions()
ORDER BY loaded DESC;
```

Override where extensions are stored:

```sql
SET extension_directory = '/opt/duckdb_exts';     -- default: ~/.duckdb/extensions
```

**Core vs community:**

- **Core** extensions are built and signed by the DuckDB team, distributed from the core repo,
  trusted, and autoloadable.
- **Community** extensions are third-party — install explicitly and from the community repo:
  ```sql
  INSTALL h3 FROM community; LOAD h3;
  ```
- **Unsigned** extensions require launching with `duckdb -unsigned`.

> **On the 1.3.2 build, statically linked / always present:** `autocomplete`, `core_functions`,
> `icu`, `json`, `parquet`, `shell` (plus `tpch`/`tpcds`). **Autoloadable from the core repo**
> (shown `installed=false` until first use): `httpfs`, `sqlite_scanner`, `spatial`, `fts`,
> `excel`, `inet`, `postgres_scanner`, `mysql_scanner`, `vss`, `delta`, `iceberg`, `azure`,
> `aws`, and more. (Verified via `duckdb_extensions()` on 1.3.2.)

**Extensions this skill cares about:**

| Extension | Why | Key surface |
|---|---|---|
| **httpfs** | read/write over HTTP(S) and **S3/GCS/R2** | `FROM 's3://b/*.parquet'`; `CREATE SECRET` |
| **json** | JSON read/parse | `read_json[_auto]`, `->`/`->>`, `json_*()` (core, autoloads) |
| **parquet** | Parquet read/write | core, autoloads |
| **spatial** | GIS | `ST_*` functions, GeoParquet, `st_read`, R-Tree index *(duckdb v1.1+)* |
| **fts** | full-text search | `PRAGMA create_fts_index(...)`, `match_bm25()` |
| **icu** | collations, time zones, localized `current_*` | core, autoloads |
| **sqlite_scanner** / **postgres_scanner** / **mysql_scanner** | `ATTACH` external DBs | `TYPE sqlite\|postgres\|mysql` |
| **excel** | xlsx I/O | `read_xlsx()`, `COPY … (FORMAT xlsx)` |
| **autocomplete** | shell tab-completion | core |
| **vss** | vector similarity (HNSW) | `CREATE INDEX … USING HNSW` |

## httpfs, S3/GCS/R2, and `CREATE SECRET`

`httpfs` lets you query remote files directly. For cloud object stores, credentials go through
the **secrets manager** (`CREATE SECRET`) — the modern replacement for setting `s3_*` PRAGMA/SET
globals.

```sql
INSTALL httpfs; LOAD httpfs;

-- Plain HTTP(S): no credentials needed
FROM 'https://example.com/data.parquet';

-- S3 with explicit keys:
CREATE SECRET s3secret (
    TYPE s3,
    KEY_ID    'AKIA…',
    SECRET    '…',
    REGION    'us-east-1'
);

-- …or resolve from the environment / instance profile / SSO:
CREATE SECRET (TYPE s3, PROVIDER credential_chain);

FROM 's3://my-bucket/path/*.parquet';
```

**GCS and Cloudflare R2** use the same S3-compatible machinery:

```sql
CREATE SECRET gcs (TYPE gcs, KEY_ID '…', SECRET '…');           -- Google Cloud Storage
CREATE SECRET r2  (TYPE r2,  KEY_ID '…', SECRET '…', ACCOUNT_ID '…');  -- Cloudflare R2
FROM 'gcs://bucket/file.parquet';
FROM 'r2://bucket/file.parquet';
```

Inspect/scope secrets with `FROM duckdb_secrets();`. Add `SCOPE 's3://bucket/prefix'` to bind a
secret to specific paths. Persist a secret across sessions with
`CREATE PERSISTENT SECRET …` (stored under `~/.duckdb/stored_secrets`).

**Secret values may be expressions** *(duckdb v1.3+)* — handy for pulling creds from the
environment or a session variable instead of hardcoding:

```sql
CREATE SECRET e (TYPE s3, KEY_ID getenv('AWS_ACCESS_KEY_ID'),
                          SECRET getenv('AWS_SECRET_ACCESS_KEY'));
CREATE SECRET t (TYPE huggingface, TOKEN getvariable('hf_token'));
```

> **Confirmed on 1.3.2:** `INSTALL httpfs; LOAD httpfs;`, `CREATE SECRET … (TYPE s3, …)`,
> `CREATE SECRET (TYPE s3, PROVIDER credential_chain)`, and `getenv()` inside `CREATE SECRET` all
> succeed. (Remote fetches themselves weren't exercised offline.)

## Plans and introspection (ops)

| Tool | Example | Notes |
|---|---|---|
| `EXPLAIN` | `EXPLAIN SELECT …;` | logical + physical plan |
| `EXPLAIN ANALYZE` | `EXPLAIN ANALYZE SELECT …;` | runs the query; per-operator timing & cardinalities |
| `PRAGMA` | `PRAGMA version;` · `PRAGMA database_list;` · `PRAGMA table_info('t');` · `PRAGMA show_tables;` · `PRAGMA database_size;` | SQLite-style knobs/inspection |
| `SET` / `RESET` | `SET memory_limit='4GB';` · `SET threads=4;` · `RESET threads;` | session/global config |
| `current_setting()` | `SELECT current_setting('threads');` | read a setting's value |
| Profiling | `PRAGMA enable_profiling;` · `SET profiling_output='plan.json';` | write a profile to disk |
| `.timer on` | (dot-command) | wall/CPU time per query in the REPL |

**`duckdb_*` metadata functions** for programmatic introspection:

```sql
FROM duckdb_extensions();                -- installed/loaded extensions
FROM duckdb_settings();                  -- all settings + current values
FROM duckdb_functions();                 -- every function (verify before using one)
FROM duckdb_databases();                 -- attached databases
FROM duckdb_secrets();                   -- defined secrets
FROM duckdb_external_file_cache();       -- cached remote/file blocks (duckdb v1.3+)
```

> **Confirmed on 1.3.2:** `EXPLAIN ANALYZE`, `PRAGMA version` (→ `v1.3.2 / Ossivalis`),
> `SET memory_limit`/`SET threads` + `current_setting('threads')`, and the `duckdb_*` functions
> above.

---

### Source URLs (for version annotations)

- DuckDB 1.1.0: https://duckdb.org/2024/09/09/announcing-duckdb-110
- DuckDB 1.2.0: https://duckdb.org/2025/02/05/announcing-duckdb-120
- DuckDB 1.3.0: https://duckdb.org/2025/05/21/announcing-duckdb-130
- DuckDB 1.4.0: https://duckdb.org/2025/09/16/announcing-duckdb-140
- DuckDB 1.5.0: https://duckdb.org/2026/03/09/announcing-duckdb-150
- Docs — data import: https://duckdb.org/docs/stable/data/overview
- Docs — extensions: https://duckdb.org/docs/stable/extensions/overview
- Docs — secrets manager: https://duckdb.org/docs/stable/configuration/secrets_manager
