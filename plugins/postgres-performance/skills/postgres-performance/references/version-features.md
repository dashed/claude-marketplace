# PostgreSQL Performance Feature → Minimum Version

A consolidated lookup of **which PostgreSQL major version introduced** each EXPLAIN option,
index capability, statistics feature, planner/parallel feature, or VACUUM behavior this skill
documents — so you know what works on your server and what needs an upgrade.

## How to read this

- These are **PostgreSQL major versions** (one number since PG 10: `10, 11, … 18, 19`). `(pg12+)`
  means "PostgreSQL 12 and later." **PG18 is the current stable release; PG19 is in beta** (so
  `(pg19+, beta)` features are not in any production release yet).
- Each entry is the **earliest major version in which the feature is documented as available**,
  verified against the official **postgresql.org** docs (per-version manual pages) and **release
  notes**. The source PostgreSQL tree consulted while writing this skill is **19beta1**.
- **Bedrock = unannotated.** Anything present since the old **9.x** line carries **no tag** and is
  assumed everywhere. PostgreSQL 9.6 was the last 9.x release; everything at or before it (parallel
  query's debut, B-tree/GIN/GiST/SP-GiST/BRIN index types, plain `VACUUM`, `EXPLAIN ANALYZE`,
  `CREATE INDEX CONCURRENTLY`, the `BUFFERS` option, `pg_stats`, the cost GUCs, etc.) is bedrock and
  omitted here to stay signal-rich.
- **Verify, don't guess.** A feature with no clean "added in version N" source is treated as
  long-standing and left out of the table rather than annotated speculatively.
- Confirm your running server with `SELECT version();`, `SHOW server_version;`, or
  `SHOW server_version_num;` (e.g. `180000` = 18.0).

## Sources

Verified against the PostgreSQL documentation and release notes on postgresql.org:

- EXPLAIN reference (per version): <https://www.postgresql.org/docs/NN/sql-explain.html>
- Release notes index: <https://www.postgresql.org/docs/release/>
- PG17 release notes (EXPLAIN MEMORY/SERIALIZE): <https://www.postgresql.org/docs/17/release-17.html>
- PG18 release notes (BUFFERS-default, skip scan, Index Searches): <https://www.postgresql.org/docs/18/release-18.html>
- PG19 (beta) — REPACK, EXPLAIN IO, AIO: <https://www.postgresql.org/docs/19/release-19.html>
  and PostgreSQL 19 Beta 1 announcement (released 2026-06-04).
- Parallel plans (per version): <https://www.postgresql.org/docs/NN/parallel-plans.html>
- CREATE STATISTICS (per version): <https://www.postgresql.org/docs/NN/sql-createstatistics.html>

## EXPLAIN options (the matrix)

The PG19 synopsis order is `ANALYZE, VERBOSE, COSTS, SETTINGS, GENERIC_PLAN, BUFFERS, SERIALIZE,
WAL, TIMING, SUMMARY, MEMORY, IO, FORMAT`.

| Min version | Option / behavior | Notes |
|---|---|---|
| bedrock | `ANALYZE`, `VERBOSE`, `COSTS`, `TIMING`, `FORMAT {TEXT\|XML\|JSON\|YAML}` | `COSTS`/`TIMING` default on; the `BUFFERS` *option* also exists since 9.0 (bedrock) |
| `pg10+` | `SUMMARY` option | included by default with `ANALYZE` |
| `pg12+` | `SETTINGS` | shows non-default planner GUCs |
| `pg13+` | `WAL` | WAL records/bytes/FPIs; needs `ANALYZE` |
| `pg16+` | `GENERIC_PLAN` | plan a `$1`-parameterized query; cannot combine with `ANALYZE` |
| `pg17+` | `SERIALIZE [ NONE \| TEXT \| BINARY ]` | cost of converting output rows for the client |
| `pg17+` | `MEMORY` | planner memory consumption |
| `pg17+` | local I/O block read/write **timing** inside `BUFFERS` | |
| **`pg18+`** | **`BUFFERS` auto-enabled whenever `ANALYZE` is used** | disable with `(ANALYZE, BUFFERS OFF)` |
| `pg18+` | `WAL` also reports times WAL buffers became full | |
| **`pg19+, beta`** | **`IO` option** | asynchronous-I/O (AIO) stats per scan node; needs `ANALYZE` |

## EXPLAIN ANALYZE output / plan display

| Min version | Feature | Notes |
|---|---|---|
| `pg10+` | `Subplans Removed: N` (run-time partition pruning) | |
| `pg13+` | `Incremental Sort` node + `Presorted Key` line | `enable_incremental_sort` |
| `pg14+` | `Memoize` node (caches inner side of a nested loop) | `enable_memoize` |
| `pg17+` | Improved SubPlan / output-parameter display; JIT `deform_counter` | |
| `pg18+` | **`Index Searches: N`** line on index/bitmap/index-only scans | exposes B-tree skip scan & array searches |
| `pg18+` | **Actual rows shown to two decimals** (`rows=10.00`) | formatting change |
| `pg18+` | **`Disabled: true`** line for nodes chosen despite `enable_*=off` | |
| `pg18+` | `VERBOSE` adds per-worker CPU, WAL, and average-read stats | |
| `pg18+` | Parallel Bitmap Heap Scan worker-cache stats | |

## Indexes

| Min version | Feature | Notes |
|---|---|---|
| bedrock | B-tree, hash, GiST, GIN index types; `CREATE INDEX CONCURRENTLY`; multicolumn/partial/expression indexes | hash & GIN/GiST long-standing |
| bedrock | SP-GiST (9.2), BRIN (9.5) index types | both predate PG 10 → unannotated |
| `pg10+` | Hash indexes are **WAL-logged & crash-safe** (before 10 they were not) | makes hash indexes replication-safe |
| `pg11+` | **Covering indexes**: `INCLUDE (cols)` non-key payload (B-tree) | enables more index-only scans |
| `pg11+` | Parallel B-tree index build | `max_parallel_maintenance_workers` |
| `pg12+` | `REINDEX CONCURRENTLY` | rebuild an index online |
| `pg12+` | `INCLUDE` extended to **GiST** indexes | |
| `pg12+` | B-tree space optimizations / lower bloat | |
| `pg13+` | **B-tree deduplication** (`deduplicate_items`, on by default) | shrinks indexes with duplicate keys |
| `pg14+` | B-tree bottom-up index deletion (reduces bloat from updates) | |
| `pg14+` | `INCLUDE` extended to **SP-GiST** | |
| `pg15+` | `NULLS [NOT] DISTINCT` on unique indexes/constraints | |
| **`pg18+`** | **B-tree skip scan** — use a multicolumn index when a leading column is absent | best when leading column has few distinct values; shows extra `Index Searches` |

## Statistics & planner

| Min version | Feature | Notes |
|---|---|---|
| bedrock | `pg_statistic`/`pg_stats`, `ANALYZE`, `default_statistics_target`, `ALTER … SET STATISTICS` | |
| bedrock | Cost GUCs (`random_page_cost`, `seq_page_cost`, `cpu_tuple_cost`, `effective_cache_size`, `work_mem`) and `enable_*` flags | |
| `pg10+` | **Extended statistics** `CREATE STATISTICS` with `ndistinct` and `dependencies` kinds | for correlated columns |
| `pg11+` | **JIT** compilation of expressions (requires LLVM) | off by default in 11 |
| `pg12+` | JIT **on by default** | `jit = on`, `jit_above_cost` |
| `pg12+` | `mcv` (most-common-values) extended-statistics kind | multi-column MCV lists |
| `pg13+` | `enable_incremental_sort` | drives the Incremental Sort node |
| `pg14+` | Single-**expression** extended statistics; `enable_memoize` | expression stats ≈ expression index without maintenance |
| `pg19+, beta` | Planner/executor: eager aggregation, new anti-join optimizations, broader incremental-sort use, faster parallel-seq-scan reads | from PG19 beta release notes |
| `pg19+, beta` | Plain table scans can mark pages **all-visible** in the visibility map | previously only `VACUUM` / `COPY … FREEZE` |

## Parallel query

Parallel query **debuted in 9.6 (bedrock)**: `Gather`, Parallel Seq Scan, parallel nested-loop &
hash joins (each worker builds its own hash copy), and two-stage parallel aggregation
(`Partial Aggregate` → `Finalize Aggregate`).

| Min version | Feature | Notes |
|---|---|---|
| `pg10+` | **`Gather Merge`** (order-preserving gather); Parallel **Index** / Index-Only Scan (B-tree only); Parallel **Bitmap Heap Scan**; Parallel **Merge Join** | |
| `pg11+` | **Parallel Hash** (shared hash table, not per-worker copies); **Parallel Append**; parallel `UNION` | |

GUCs (all bedrock unless noted): `max_parallel_workers_per_gather`, `max_parallel_workers`,
`max_worker_processes`, `min_parallel_table_scan_size`, `min_parallel_index_scan_size`,
`parallel_setup_cost`, `parallel_tuple_cost`, `parallel_leader_participation`,
`enable_parallel_append`, `enable_parallel_hash`.

## VACUUM, bloat & maintenance

| Min version | Feature | Notes |
|---|---|---|
| bedrock | `VACUUM`, `VACUUM FULL`, `ANALYZE`, autovacuum, `CLUSTER`, freezing/anti-wraparound | |
| `pg12+` | `VACUUM` options `INDEX_CLEANUP`, `TRUNCATE` | |
| `pg13+` | `VACUUM (PARALLEL n)` (parallel index vacuuming) | `max_parallel_maintenance_workers` |
| `pg14+` | `INDEX_CLEANUP { AUTO \| ON \| OFF }` (enum); `PROCESS_TOAST` option; `pg_stat_progress_vacuum` improvements | |
| `pg16+` | `VACUUM` options `BUFFER_USAGE_LIMIT`, `PROCESS_MAIN`, `SKIP_DATABASE_STATS`, `ONLY_DATABASE_STATS` | |
| `pg17+` | Faster vacuum dead-tuple storage (TID store) — less memory, fewer index passes | internal; no syntax change |
| **`pg19+, beta`** | **`REPACK` command** unifies `VACUUM FULL` + `CLUSTER`; **`VACUUM FULL` deprecated** ("behaves like `REPACK` without a `USING INDEX` clause") | contributed by Antonin Houska |
| **`pg19+, beta`** | **`REPACK … CONCURRENTLY`** — online table rewrite without `ACCESS EXCLUSIVE` (logical decoding); new GUC `max_repack_replication_slots` | the in-core answer to `pg_repack`/`pg_squeeze` |

## Profiling extensions (ship with PostgreSQL — see the postgres-extensions skill)

| Min version | Feature | Notes |
|---|---|---|
| bedrock | `pg_stat_statements`, `auto_explain`, `pageinspect`, `pg_buffercache`, `pgstattuple` | long-standing contrib |
| `pg11+` | `amcheck` index-verification extension in core contrib | (heap verification added pg14) |
| `pg18+` | `pg_overexplain` contrib (`EXPLAIN (DEBUG)`, `(RANGE_TABLE)`) | planner-internals debugging; usable via `auto_explain.log_extension_options` |
| `pg19+, beta` | `auto_explain.log_io` (mirror of `EXPLAIN (IO)`); AIO worker GUCs (`io_min_workers`, `io_max_workers`, …) | |

## Checking your version

```sql
SELECT version();              -- full string, e.g. 'PostgreSQL 18.0 on x86_64-…'
SHOW server_version;           -- '18.0'
SHOW server_version_num;       -- 180000  (MMmmpp: 18.00.00)
```

From the shell: `psql -c 'SHOW server_version;'` or `postgres --version`. A feature tagged `(pgNN+)`
simply does not exist on older majors — PostgreSQL does not backport features across major versions,
so the "Min version" column is a hard floor; upgrade the server to gain it.
