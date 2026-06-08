# DuckDB Feature → Minimum Version

A consolidated lookup of **which DuckDB release introduced a CLI option, SQL-dialect
construct, data-I/O capability, extension, or function** this skill documents, so you know what
works on an older (or newer) DuckDB. Use it to answer "is my DuckDB new enough for X?" and "what
do I need to upgrade to?"

**How to read this:**

- These are **DuckDB release versions** (`MAJOR.MINOR.PATCH`, e.g. `1.3.2`). The `1.1.0+` form
  means "the 1.1.0 release and later." DuckDB hit its stable **1.0.0 GA in June 2024**; before
  that was a long **pre-1.0 `0.x` era**. Treat everything at or before **1.0.0** as **bedrock**.
- Each version is the **earliest release in which the feature is documented as available**.
  Annotations are sourced from the official **duckdb.org release blogs**, cross-checked where
  possible against (a) the matching **git release tag** and (b) an **empirical test on the
  installed CLI (v1.3.2 "Ossivalis")** — a construct that runs on v1.3.2 is `≤ 1.3.2`; one that
  errors there is `> 1.3.2`. **No version is guessed:** a feature with no clean "added in vX"
  source is treated as long-standing and left out of the table.
- **Features not listed here are long-standing** — present at or before the **1.0.0 GA
  (June 2024)** and treated as bedrock, so they carry no version tag. This includes essentially
  all of the "Friendly SQL" surface: `FROM`-first queries, `SELECT * EXCLUDE/REPLACE`,
  `COLUMNS(regex)`, `GROUP BY ALL` / `ORDER BY ALL`, `QUALIFY`, `PIVOT`/`UNPIVOT`,
  `ASOF`/`POSITIONAL` joins, `UNION [ALL] BY NAME`, the LIST/STRUCT/MAP/UNION nested types, list
  comprehensions and 1-based slicing, `SUMMARIZE`, `DESCRIBE`, `USING SAMPLE`, dollar-quoting,
  underscores-in-numbers, trailing commas, `CREATE OR REPLACE`, CTAS, `PREPARE`/`EXECUTE`, named
  args (`:=`), `try_cast`, `INSERT … RETURNING`, replacement scans (`FROM 'file.{csv,parquet,json}'`),
  globs/Hive partitioning, `read_csv/parquet/json[_auto]`, `COPY … TO` (incl. `PARTITION_BY`),
  `EXPORT`/`IMPORT DATABASE`, `ATTACH` (duckdb/sqlite/postgres/mysql), `INSTALL`/`LOAD`/autoloading,
  `EXPLAIN`/`EXPLAIN ANALYZE`, `PRAGMA`/`SET`/`RESET`, and JSON `->`/`->>`. This file omits them to
  stay signal-rich.
- A few real features could **not** be pinned to a precise "added in vX" statement (e.g. the
  `-ui`/`ui` web interface, the granular `.highlight*` color dot-commands that predate the 1.5
  CLI rework, and the exact first versions of the `ducklake`/`motherduck`/`encodings`
  extensions). Rather than guess, they are **omitted** here and treated as long-standing.
- This skill is documented against the installed CLI **v1.3.2 "Ossivalis"** (source tree past
  v1.5.3, 2026-06-07). Always confirm on the running system — see
  [Checking your version](#checking-your-version).

Rows marked **(breaking)** changed existing behavior in that release; review the linked blog
before upgrading. Release-blog sources, one per minor line:

- 1.1.0 — <https://duckdb.org/2024/09/09/announcing-duckdb-110>
- 1.2.0 — <https://duckdb.org/2025/02/05/announcing-duckdb-120>
- 1.3.0 — <https://duckdb.org/2025/05/21/announcing-duckdb-130>
- 1.4.0 — <https://duckdb.org/2025/09/16/announcing-duckdb-140>
- 1.5.0 — <https://duckdb.org/2026/03/09/announcing-duckdb-150>

## Contents

- [Versioned features (ascending by DuckDB release)](#versioned-features-ascending-by-duckdb-release)
- [Checking your version](#checking-your-version)

## Versioned features (ascending by DuckDB release)

Sorted ascending by minimum DuckDB release; within a release, grouped by **Area**
(CLI / SQL dialect / data I/O / extensions / functions).

| Min version | Feature | Area |
|---|---|---|
| 1.1.0+ | `SET VARIABLE` / `getvariable()` — session variables of any type | SQL dialect |
| 1.1.0+ | `*COLUMNS(...)` — unpack a star-expression into a function call | SQL dialect |
| 1.1.0+ | `array(SELECT …)` — subquery-to-list conversion | SQL dialect |
| 1.1.0+ | IEEE-754 div-by-zero returns `inf` (was NULL); `ieee_floating_point_ops` setting *(breaking)* | SQL dialect |
| 1.1.0+ | Scalar subquery now errors on multiple rows *(breaking)* | SQL dialect |
| 1.1.0+ | Spatial R-Tree index (`USING RTREE`); GeoParquet auto-convert | extensions |
| 1.1.0+ | `query()` / `query_table()` — run a SQL string as a table function | functions |
| 1.1.0+ | `histogram()` with `bin_count :=` | functions |
| 1.2.0+ | `-safe` flag / `.safe_mode` dot-command — restrict filesystem access | CLI |
| 1.2.0+ | Prefix (colon) aliases `name: expr` | SQL dialect |
| 1.2.0+ | `SELECT * RENAME (a AS b)` | SQL dialect |
| 1.2.0+ | `SELECT * LIKE 'pat%'` — column-name filter | SQL dialect |
| 1.2.0+ | `ALTER TABLE … ADD PRIMARY KEY` | SQL dialect |
| 1.2.0+ | Column `USING COMPRESSION 'zstd'`; zstd string compression | SQL dialect |
| 1.2.0+ | `map['key']` returns the **value** (was a list); `map_extract_value()` *(breaking)* | SQL dialect |
| 1.2.0+ | `ATTACH … (STORAGE_VERSION 'v1.2.0')` — opt into newer storage | data I/O |
| 1.2.0+ | `COPY FROM DATABASE src TO dst` | data I/O |
| 1.2.0+ | CSV `encoding` (latin-1/utf-16), multi-byte delimiter, `strict_mode`, unlimited row length | data I/O |
| 1.2.0+ | Parquet writer: Bloom filters + DELTA / BYTE_STREAM_SPLIT encodings | data I/O |
| 1.2.0+ | `current_time` / `current_date` / `today()` use local timezone (ICU) *(breaking)* | functions |
| 1.3.0+ | Open a **data file** as the DB argument (`duckdb f.parquet`) → `file`/`<name>` views | CLI |
| 1.3.0+ | Python-style `lambda x: …` syntax; `LAMBDA` reserved; `lambda_syntax` setting | SQL dialect |
| 1.3.0+ | `TRY(expr)` — return NULL instead of raising on error | SQL dialect |
| 1.3.0+ | Struct sub-column `ALTER TABLE … ADD/DROP/RENAME COLUMN s.k` | SQL dialect |
| 1.3.0+ | `UNPACK(...)` keyword | SQL dialect |
| 1.3.0+ | `ATTACH OR REPLACE` | data I/O |
| 1.3.0+ | Expressions in `CREATE SECRET` (`getvariable`, `getenv`) | data I/O |
| 1.3.0+ | External file cache (`enable_external_file_cache`, `duckdb_external_file_cache()`) | data I/O |
| 1.3.0+ | Spatial `SPATIAL_JOIN` operator (auto R-Tree) | extensions |
| 1.3.0+ | `uuidv7()`, `uuid_extract_version()` / `uuid_extract_timestamp()` | functions |
| 1.4.0+ | CLI progress-bar ETA (Kalman filter) | CLI |
| 1.4.0+ | `MERGE INTO` — upsert with no PK required (`WHEN MATCHED/NOT MATCHED`, `merge_action`) | SQL dialect |
| 1.4.0+ | Database **encryption** `ATTACH … (ENCRYPTION_KEY …)` (AES-256-GCM) — documented in 1.4.0, but the `ENCRYPTION_KEY` option already works in 1.3.x | data I/O |
| 1.4.0+ | Compressed in-memory `ATTACH ':memory:' (COMPRESS)` | data I/O |
| 1.4.0+ | Iceberg **writes** + `COPY FROM DATABASE` to Iceberg | extensions |
| 1.4.0+ | `FILL()` window function (interpolation) | functions |
| 1.5.0+ | CLI rework: pager (>50 rows), dynamic prompts, `_` last-result, color scheme, `.highlight_colors`, compact `DESCRIBE`/`.tables` | CLI |
| 1.5.0+ | `VARIANT` type — self-describing semi-structured column | SQL dialect |
| 1.5.0+ | `GEOMETRY` type moved into core (WKB, shredding, `&&`) | SQL dialect |
| 1.5.0+ | Lambda arrow `->` syntax now emits a deprecation warning | SQL dialect |
| 1.5.0+ | PEG parser preview (`CALL enable_peg_parser()`) | SQL dialect |
| 1.5.0+ | `read_duckdb()` — query DuckDB files without `ATTACH` (supports globs) | data I/O |
| 1.5.0+ | Azure **writes** (`COPY TO 'az://…'` / `'abfss://…'`) | extensions |
| 1.5.0+ | `odbc_scanner` extension (`odbc_connect` / `odbc_query`) | extensions |
| 1.5.0+ | `httpfs` default backend switched to curl | extensions |
| 1.5.0+ | `variant_typeof()` / `variant_extract()` (with the `VARIANT` type) | functions |
| 1.5.0+ | `date_trunc` on a DATE now returns TIMESTAMP *(breaking)* | functions |

## Checking your version

Check what you are running:

```
duckdb --version       # e.g. v1.3.2 "Ossivalis"  (also: duckdb -version)
```

From inside a session you can also ask the engine directly:

```sql
SELECT version();      -- e.g. 'v1.3.2'
PRAGMA version;        -- library_version + source_id (git hash)
```

`duckdb --version` and `SELECT version()` report the **release** number this table is keyed on.
The current released line is **1.5.x** (with **1.4 designated the LTS line**); v2.0 is expected
around September 2026. Because DuckDB ships features on the main release line (no cross-line
backports the way some distros do), the "Min version" column is a hard floor: a feature tagged
`1.4.0+` simply is not present on 1.3.x — upgrade the binary to pick it up.

Release codenames, for cross-referencing blogs: 1.0 *Snow Duck* · 1.1 *Eatoni* ·
1.2 *Histrionicus* · 1.3 *Ossivalis* · 1.4 *Andium* · 1.5 *Variegata*.
