# PostgreSQL Extensions — Feature → Minimum Version

A consolidated lookup of **which PostgreSQL release first shipped a contrib module, an
extension-management feature, or a notable function/option** that this skill documents —
so you know what works on an older (or newer) server, and what to upgrade to.

## How to read this

- These are **PostgreSQL major release** numbers (`10`, `13`, `15`, `18`, `19`). The
  `18+` form means "PostgreSQL 18 and later." This skill targets **PG 18 (stable)** with
  notes for **PG 19 (beta)**; the source tree consulted is **19beta1**.
- Each row is the **earliest release in which the module/feature is documented as
  available**. Tags are sourced from the official **postgresql.org release notes** and the
  in-tree docs (`doc/src/sgml/*.sgml`, the per-module `.control` files), cross-checked
  against pgpedia where a precise commit was needed. **No version is guessed:** a feature
  with no clean "added in release N" source is treated as bedrock and left out of the table.
- **The extension version is NOT the PostgreSQL version — never conflate them.** Every
  contrib module carries its own `default_version` in its `.control` file (e.g.
  `pg_stat_statements` = `1.13`, `pageinspect` = `1.13`, `citext` = `1.8`). That number is
  the *extension's* internal object/schema version, bumped by its own upgrade scripts
  (`name--X--Y.sql`) and **independent of the server release**. A `1.13` extension can ship
  in PG 14, 15, 16, 17, 18… The `(pgNN+)` tags in this skill always mean the **server
  release**, never the `default_version`.
- **Modules present since the 9.x era (or earlier) are "bedrock" and carry no tag** — see
  [Bedrock modules](#bedrock-modules-unannotated). The table below lists only PG-10-and-later
  arrivals and notable later feature additions, to stay signal-rich.
- A handful of facts could not be pinned to a precise "added in vN" line (e.g. the exact
  intro patch-release of very old modules like `fuzzystrmatch`/`lo`). Rather than guess,
  they are treated as bedrock and omitted from the table.

## Sources

Primary: official PostgreSQL release notes, one page per major version:

- PG 10 — <https://www.postgresql.org/docs/release/10.0/>
- PG 11 — <https://www.postgresql.org/docs/release/11.0/>
- PG 13 — <https://www.postgresql.org/docs/release/13.0/>
- PG 14 — <https://www.postgresql.org/docs/release/14.0/>
- PG 15 — <https://www.postgresql.org/docs/release/15.0/>
- PG 16 — <https://www.postgresql.org/docs/release/16.0/>
- PG 17 — <https://www.postgresql.org/docs/release/17.0/>
- PG 18 — <https://www.postgresql.org/docs/release/18.0/>
- PG 19 (beta) — in-tree `doc/src/sgml/release-19.sgml` (19beta1) + <https://www.postgresql.org/docs/19/release-19.html>

In-tree (this 19beta1 checkout): `doc/src/sgml/contrib.sgml` (trusted-extensions list),
`pgcrypto.sgml` / `uuid-ossp.sgml` (`gen_random_uuid()` now in core), and each module's
`*.control` `default_version`. Commit-level cross-checks via <https://pgpedia.info/>.

## Versioned features (ascending by PostgreSQL release)

| Min version | Module / feature | Area |
|---|---|---|
| 10+ | `amcheck` module — B-tree index verification (`bt_index_check`, `bt_index_parent_check`) | module added |
| 11+ | `pg_prewarm` **autoprewarm** background worker (restore buffers after restart; needs `shared_preload_libraries`). Base `pg_prewarm()` is bedrock (9.4). | feature |
| 13+ | **`gen_random_uuid()` graduated to CORE** — no extension needed (previously required `pgcrypto`/`uuid-ossp`); `pgcrypto`'s copy is now an obsolete wrapper | core / extension |
| 13+ | **Trusted extensions** — the `trusted` control flag lets a non-superuser with `CREATE` on the database run `CREATE EXTENSION` | management |
| 13+ | `pg_stat_statements`: planning/execution time split + `wal_records`/`wal_bytes`/`wal_fpi` columns | feature |
| 14+ | `pg_surgery` module — forced tuple repair (`heap_force_kill`, `heap_force_freeze`) | module added |
| 14+ | `amcheck.verify_heapam()` — heap corruption check | feature |
| 14+ | `postgres_fdw`: bulk insert (`batch_size`) + asynchronous foreign scans (`async_capable`, "Async Append") | feature |
| 15+ | `pg_walinspect` module — SQL-level WAL decoding (`pg_get_wal_record_info`, `pg_get_wal_records_info`) | module added |
| 15+ | `basic_archive` module — example archive library (`archive_library`) | module added |
| 15+ | `basebackup_to_shell` module — custom `pg_basebackup` shell target | module added |
| 15+ | `pg_stat_statements`: JIT counters added | feature |
| 16+ | `fuzzystrmatch.daitch_mokotoff()` — Daitch-Mokotoff Soundex | feature |
| 17+ | `pg_buffercache_evict(bufferid)` — evict a single shared buffer (testing) | feature |
| 17+ | `pg_stat_statements`: `blk_*_time`→`shared_blk_*_time` rename; new `local_blk_read_time`/`local_blk_write_time`, `stats_since`/`minmax_stats_since` | feature |
| 17+ | `adminpack` module **removed** (had been deprecated; used only by old pgAdmin III) | module removed |
| 18+ | `pg_overexplain` module (**LOAD-only**, no `CREATE EXTENSION`) — extra EXPLAIN detail (`DEBUG`, `RANGE_TABLE`) | module added |
| 18+ | `pg_logicalinspect` module — inspect logical-decoding snapshot files | module added |
| 18+ | Core `uuidv7()` (time-ordered) and `uuidv4()` UUID-generation functions (built-in; `uuid-ossp` not required) | core |
| 18+ | `pg_buffercache`: NUMA view (`pg_buffercache_numa_pages()`, needs `--with-libnuma`) + `pg_buffercache_evict_relation()`/`pg_buffercache_evict_all()` | feature |
| 18+ | `amcheck.gin_index_check()` — GIN index verification | feature |
| 18+ | `pgcrypto`: `crypt()` gains `sha256crypt`/`sha512crypt`; CFB mode; `fips_mode()`; `builtin_crypto_enabled` GUC | feature |
| 18+ | `file_fdw`: `on_error`, `log_verbosity`, `reject_limit` options | feature |
| 18+ | `passwordcheck.min_password_length`; `isn` `weak` variable; `btree_gist` sorted index builds; `postgres_fdw`/`dblink` SCRAM passthrough | feature |
| 18+ | `pg_stat_statements`: `parallel_workers_to_launch`/`parallel_workers_launched`, `wal_buffers_full` | feature |
| 18+ | Extension-author APIs: custom EXPLAIN options, cumulative-stats API, `PG_MODULE_MAGIC_EXT`, `pg_get_loaded_modules()` | infrastructure |
| 19+ | `pg_plan_advice` module (**LOAD-only**) — capture & enforce planner decisions (plan stability) | module added (beta) |
| 19+ | `pg_stash_advice` module — stash & persist per-query-id plan advice (companion to `pg_plan_advice`) | module added (beta) |
| 19+ | `pg_available_extensions` / `pg_available_extension_versions` gain a `location` column (on-disk directory) | management |
| 19+ | `pg_buffercache`: `pg_buffercache_os_pages()` view + `pg_buffercache_mark_dirty()`/`_relation()`/`_all()` | feature |
| 19+ | `pg_stat_statements`: counters for generic vs. custom plans | feature |
| 19+ | `auto_explain.log_extension_options` GUC (let extensions add EXPLAIN options to the log) | feature |
| 19+ | `btree_gin`: cross-type comparison support | feature |
| 19+ | Casts allowed between `bytea` and `uuid`; extensions may replace set-returning functions in `FROM` with SQL | core/extension |

> **Beta caveat:** PG 19 rows are from 19beta1 — interfaces and module names may change
> before GA.

## Bedrock modules (unannotated)

Present since the 9.x era (or earlier) and therefore shown **without** a version tag
throughout this skill. (Approximate first-release per pgpedia, for reference only — you do
**not** need any of these tags in practice; assume they exist on any supported server.)

| Module | ~First | Module | ~First |
|---|---|---|---|
| `pgcrypto` | 7.1 | `cube` | 7.1 |
| `intarray` | 7.1 | `seg` | 7.1 |
| `ltree` | 7.3 | `tablefunc` | 7.3 |
| `dblink` | 7.3 | `intagg` | 7.3 (deprecated 8.4) |
| `earthdistance` | 6.4 | `xml2` | 8.0 |
| `fuzzystrmatch` | 8.x | `pg_freespacemap` | 8.2 |
| `hstore` | 8.2 | `isn` | 8.2 |
| `sslinfo` | 8.2 | `dict_int` / `dict_xsyn` | 8.3 |
| `uuid-ossp` | 8.3 | `citext` | 8.4 |
| `pg_stat_statements` | 8.4 | `auto_explain` | 8.4 |
| `unaccent` | 9.0 | `tcn` | 9.2 |
| `postgres_fdw` | 9.3 | `file_fdw` | 9.1 |
| `pg_prewarm` (base) | 9.4 | `tsm_system_rows` / `tsm_system_time` | 9.5 |
| `bloom` | 9.6 | `pg_visibility` | 9.6 |
| `pageinspect` · `pgstattuple` · `pgrowlocks` · `pg_buffercache` (base) · `btree_gin` · `btree_gist` · `lo` · the `spi` triggers (`autoinc`/`insert_username`/`moddatetime`/`refint`) · `passwordcheck` · `auth_delay` · `sepgsql` · `test_decoding` | 9.x or earlier | | |

**The `default_version` of any of these in PG18/19 is the extension's own number** (e.g.
`citext` 1.8, `hstore` 1.8, `pageinspect` 1.13) — again, not the server version.

## Checking your version

Server release (what every `(pgNN+)` tag refers to):

```sql
SELECT version();           -- e.g. PostgreSQL 18.0 ... / 19beta1 ...
SHOW server_version;        -- 18.0
SHOW server_version_num;    -- 180000  (integer: major*10000 + minor)
```

Per-extension versions (the numbers you must NOT confuse with the server release):

```sql
SELECT extname, extversion FROM pg_extension;                  -- installed extensions + their versions
SELECT name, default_version, installed_version
FROM pg_available_extensions ORDER BY name;                    -- what's on disk vs. installed
SELECT * FROM pg_available_extension_versions WHERE name = 'pg_trgm';  -- all versions + trusted/superuser flags
```

If a function or option errors as unknown, the module may be older on disk than the server,
or the feature may be newer than your server release — check both the `(pgNN+)` tag above
and `ALTER EXTENSION name UPDATE;` to pull the extension to its newest installed version.
