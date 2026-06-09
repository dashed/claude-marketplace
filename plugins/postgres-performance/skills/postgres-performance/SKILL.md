---
name: postgres-performance
description: PostgreSQL query & performance tuning — reading EXPLAIN / EXPLAIN ANALYZE plans, choosing and designing indexes, fixing planner row-estimate errors with statistics, and diagnosing MVCC bloat / VACUUM. Use when a query is slow, when reading an EXPLAIN/EXPLAIN ANALYZE plan (seq vs index vs bitmap scan, nested-loop/hash/merge join, "Rows Removed by Filter", estimate-vs-actual skew), when choosing an index type or columns to index (btree/GIN/GiST/SP-GiST/BRIN/hash, multicolumn/partial/expression/covering), when ANALYZE/extended statistics give bad estimates, when tables bloat or autovacuum lags, or when tuning planner GUCs (random_page_cost, work_mem, effective_cache_size, enable_*). This is performance tuning — for the psql client see psql, for writing SQL/DDL see postgres-sql, for server config/replication & autovacuum GUC tuning see postgres-admin, for installing perf extensions (pg_stat_statements, auto_explain) see postgres-extensions. Newer features are tagged inline (pgNN+); PG18 is stable, PG19 is beta.
---

# PostgreSQL Performance — Query & Tuning

## Overview

PostgreSQL's planner is **cost-based**: for each query it estimates the cost of many
candidate plans (in arbitrary units where `1.0` ≈ one sequential page fetch) and runs the
cheapest. Tuning is the craft of (a) **seeing** what plan it chose and why, then (b) pulling the
**levers** that change its decision. There are four levers, and almost every fix is one of them:

1. **EXPLAIN** — the lens. Read the plan; compare the planner's **estimated** rows to the
   **actual** rows. Estimate errors are the root cause of most bad plans.
2. **Indexes** — give the planner a cheaper access path than scanning the whole table.
3. **Statistics** — `ANALYZE` and extended statistics fix the row estimates that drive plan choice.
4. **VACUUM / config** — keep dead tuples and bloat from inflating every scan; tune planner GUCs
   (`random_page_cost`, `work_mem`, `effective_cache_size`) so cost estimates match your hardware.

**Mental model:** a slow query is a symptom. Don't reach for hints (Postgres has none) — find the
*wrong estimate* or the *missing access path* and fix the cause. `EXPLAIN ANALYZE` tells you which.

> **Disambiguation.** This skill is **query & performance tuning**. For the **`psql`** client
> (`\timing`, `\x`, `\di`, running these commands) → **psql** skill. For **writing** the SQL/DDL
> itself (SELECT, CTEs, window functions, join syntax) → **postgres-sql**. For **server config,
> replication, and deep autovacuum GUC strategy** → **postgres-admin** (this skill covers VACUUM
> *mechanics & why* and *planner* GUCs; server-wide sizing lives there). For **installing** the
> profiling extensions named below → **postgres-extensions**.

### A note on version annotations

Inline `(pgNN+)` marks the **minimum major version** that supports a feature, verified against the
PostgreSQL docs/release notes. Anything unannotated is **bedrock** — present since the old 9.x line
— and safe to assume everywhere. **PG18 is current stable; PG19 is beta** (tagged `(pg19+, beta)`).
The full feature → version map with sources is in
[references/version-features.md](references/version-features.md). Confirm your server with
`SELECT version();` or `SHOW server_version;`.

## The slow-query loop

```
 ① FIND the slow query        pg_stat_statements (total/mean time) ─┐  → postgres-extensions
 ② SEE the plan               EXPLAIN (ANALYZE, BUFFERS) <query>    │
 ③ READ it                    estimate vs actual? scan? join? sort spill?
 ④ FIX the cause              index │ ANALYZE/stats │ rewrite │ VACUUM │ GUC
 ⑤ VERIFY                     re-run EXPLAIN ANALYZE; compare timing & rows
```

Always measure with `EXPLAIN (ANALYZE, BUFFERS)` on a realistic data volume — plans on a 100-row
toy table do not predict plans on 100M rows (the planner switches strategies with size).

## EXPLAIN and EXPLAIN ANALYZE

`EXPLAIN` shows the **estimated** plan (instant, no execution). `EXPLAIN ANALYZE` **runs the query**
and adds **actual** timings and row counts so you can check the planner's guesses.

```sql
EXPLAIN <query>;                          -- plan + cost estimates only
EXPLAIN ANALYZE <query>;                   -- actually executes; adds actual time/rows (+ BUFFERS in pg18+)
EXPLAIN (ANALYZE, BUFFERS) <query>;        -- the workhorse: plan + reality + I/O
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, SETTINGS, FORMAT JSON) <query>;
```

> ⚠️ `ANALYZE` **executes the statement** — for `INSERT/UPDATE/DELETE/MERGE` wrap it so it rolls back:
> `BEGIN; EXPLAIN ANALYZE <dml>; ROLLBACK;`

### Options (PG19 synopsis)

| Option | What it adds | Since |
|--------|--------------|-------|
| `ANALYZE` | Execute and show **actual** time, rows, loops | bedrock |
| `BUFFERS` | Shared/local/temp blocks hit/read/dirtied/written (I/O) | option bedrock; **auto-on with `ANALYZE` (pg18+)** |
| `VERBOSE` | Output columns, schema-qualified names, per-worker detail; +CPU/WAL/avg-read (pg18+) | bedrock |
| `COSTS` | Estimated startup/total cost, rows, width (on by default) | bedrock |
| `TIMING` | Per-node actual time (on with ANALYZE; turn **off** to cut clock overhead) | bedrock |
| `SETTINGS` | Non-default planner GUCs in effect | `(pg12+)` |
| `WAL` | WAL records/bytes/FPIs generated (needs ANALYZE) | `(pg13+)` |
| `GENERIC_PLAN` | Plan a parameterized query with `$1` placeholders (no ANALYZE) | `(pg16+)` |
| `SERIALIZE` | Cost of converting rows to text/binary for the client (`NONE`/`TEXT`/`BINARY`) | `(pg17+)` |
| `MEMORY` | Planner memory consumption | `(pg17+)` |
| `IO` | Asynchronous-I/O (AIO) stats per scan node (needs ANALYZE) | `(pg19+, beta)` |
| `FORMAT` | `TEXT` (default) / `JSON` / `XML` / `YAML` — JSON/YAML are machine-parseable | bedrock |

### Anatomy of an `EXPLAIN ANALYZE` line

```
Index Scan using tenk2_unique2 on tenk2 t2  (cost=0.29..7.90 rows=1 width=244) (actual time=0.003..0.003 rows=1.00 loops=10)
└── node type & target          ├ startup..total cost  ├ EST rows  ├ width   ├ first-row..all-rows ms  ├ ACTUAL rows  └ executions
```

- **cost=startup..total** — planner's estimate in cost units; a parent's cost includes its children.
- **rows** (in cost parens) = **estimated** rows; **rows=N.NN** in the actual parens = **actual**
  rows, shown to 2 decimals **(pg18+)**. The single most important comparison in the whole plan.
- **loops** — times the node ran. **actual time and actual rows are per-loop averages** → multiply
  by `loops` for totals (e.g. above: 0.003 ms × 10 = 0.03 ms total, 1 × 10 = 10 rows total).
- **Buffers: shared hit=… read=…** — `hit` = found in cache; `read` = fetched from OS/disk. High
  `read` on a hot query is a caching/index problem.

A worked, fully-annotated plan walkthrough is in [references/explain.md](references/explain.md).

## Reading a plan

Read **inside-out / bottom-up**: leaf scan nodes produce rows; join/sort/aggregate nodes above
combine them; the **top** line is the whole query's cost. Indentation = tree depth; `->` marks a child.

### Scan nodes (how a table/index is read)

| Node | Means | Good / bad sign |
|------|-------|-----------------|
| **Seq Scan** | Read every page of the table | Fine for small tables or when most rows match; **bad** when a selective `WHERE` should have used an index |
| **Index Scan** | Walk an index, then fetch each matching heap row | Good for **few** rows; random heap I/O makes it lose to Seq Scan for many rows |
| **Index Only Scan** | Answer entirely from the index (no heap visit) | Best case — needs a covering index **and** an all-visible page (`Heap Fetches: 0` is the win) |
| **Bitmap Heap Scan** + **Bitmap Index Scan** | Collect TIDs from index(es), sort by page, fetch in physical order | The middle ground for a medium row count; `BitmapAnd`/`BitmapOr` combine indexes |

### Join nodes

| Node | Best when | Watch for |
|------|-----------|-----------|
| **Nested Loop** | One side tiny, inner has an index | Disaster if both sides are big and **actual** loops ≫ estimated (a row underestimate) |
| **Hash Join** | Large, unsorted, equality join | Builds a hash of the smaller side; `Batches > 1` = spilled to disk → raise `work_mem` |
| **Merge Join** | Both inputs already sorted on the key | Pays for a Sort if inputs aren't pre-sorted |

### Other common nodes

`Sort` / **`Incremental Sort` (pg13+)** (uses a pre-sorted prefix; great with `LIMIT`) · `Hash`/
`HashAggregate`/`GroupAggregate` · `Partial Aggregate` + `Finalize Aggregate` (parallel two-stage) ·
`Gather` / **`Gather Merge` (pg10+)** (collect parallel-worker rows) · `Append`/`MergeAppend`
(partitions/UNION) · `Materialize` · `Memoize` (pg14+, caches inner results) · `Limit`.

### The three signals that explain almost every slow query

1. **Estimate vs actual rows.** `rows=10` estimated but `rows=10000` actual → the planner picked the
   plan for the wrong size (nested loop that should've been a hash join, no index used, etc.).
   **Fix:** `ANALYZE`, raise statistics target, or add **extended statistics** for correlated columns.
2. **`Rows Removed by Filter: N`.** The node read far more rows than it kept → a missing/partial
   index, or a predicate that isn't sargable. (`Rows Removed by Index Recheck` = a lossy index.)
3. **Spills & repeats.** Sort `Method: external merge Disk: …` or Hash `Batches > 1` → raise
   `work_mem`. A nested-loop inner node with huge `loops` → fix the outer-side estimate or index it.

Per-node-type depth and more patterns: [references/reading-plans.md](references/reading-plans.md).

## Indexes — types & strategies

An index is a cheaper access path. The planner uses one only when it estimates that's cheaper than a
Seq Scan — so an index can exist and still be (correctly) ignored for a non-selective query.

### Which index type

| Type | Use for | Notes |
|------|---------|-------|
| **B-tree** (default) | `=`, `<`, `<=`, `>=`, `>`, `BETWEEN`, `IN`, `IS NULL`, `LIKE 'prefix%'`, `ORDER BY` | The default; the only type for **unique** indexes and ordered scans; multicolumn & covering |
| **Hash** | `=` only | Crash-safe & WAL-logged `(pg10+)`; rarely beats B-tree — usually skip it |
| **GIN** | Multi-value columns: `jsonb`, arrays, full-text `tsvector`, trigram `LIKE '%x%'` | Use `jsonb_path_ops` for `@>`; `gin_trgm_ops` (pg_trgm) for substring/`ILIKE` |
| **GiST** | Geometric, ranges, nearest-neighbour (`ORDER BY geom <-> point`), full-text | Extensible; lossy (expect an Index Recheck) |
| **SP-GiST** | Non-balanced structures: quadtrees, IP/`inet`, text-prefix trees | Niche |
| **BRIN** | **Huge** tables physically correlated with a column (append-only time series) | Tiny index, stores per-block-range min/max; only wins on naturally-ordered data |

### Index strategies (mostly B-tree)

```sql
-- Multicolumn: order matters. Leftmost prefix is usable; equality cols first, then range.
CREATE INDEX ON orders (customer_id, created_at);   -- serves WHERE customer_id = ? [AND created_at > ?]

-- Partial: index only the rows you query → smaller, faster, cheaper to maintain.
CREATE INDEX ON orders (created_at) WHERE status = 'open';

-- Expression: index the transformed value used in WHERE (functions must be IMMUTABLE).
CREATE INDEX ON users (lower(email));                -- serves WHERE lower(email) = ?

-- Covering: add non-key payload columns so the query is answered index-only.  (pg11+)
CREATE INDEX ON orders (customer_id) INCLUDE (total);

-- Build/rebuild WITHOUT blocking writes (slower, two scans; cannot run in a txn block):
CREATE INDEX CONCURRENTLY ON big (col);
REINDEX INDEX CONCURRENTLY big_col_idx;              -- (pg12+); rebuilds a bloated/corrupt index online
```

- **Index-only scans** also need the **visibility map** to mark pages all-visible — keep the table
  vacuumed, or you'll see `Heap Fetches > 0` eating the benefit.
- **Multicolumn ordering:** put `=` columns first, the range/sort column last. **B-tree skip scan
  (pg18+)** can now use a multicolumn index even when a leading column is absent (best when the
  leading column has few distinct values) — visible as multiple `Index Searches`.
- A failed `CONCURRENTLY` build leaves an **`INVALID`** index — drop it and retry.

Operator classes, all build options, deduplication, fillfactor, and `REINDEX` mechanics:
[references/indexes.md](references/indexes.md).

## Statistics & the planner

The planner estimates selectivity from per-column stats in `pg_statistic` (readable via the
**`pg_stats`** view). Stale or missing stats → wrong row estimates → bad plans.

```sql
ANALYZE orders;                              -- refresh stats now (autovacuum also does this)
ANALYZE;                                     -- whole database
ALTER TABLE orders ALTER COLUMN status SET STATISTICS 500;  -- more histogram/MCV detail for a skewed column
SET default_statistics_target = 100;         -- global default (100); raise for irregular distributions
SELECT attname, n_distinct, most_common_vals FROM pg_stats WHERE tablename = 'orders';
```

**Extended statistics** fix the planner's "columns are independent" assumption when they aren't
(e.g. `city` and `state` are correlated → equality-on-both is badly underestimated):

```sql
CREATE STATISTICS s_geo (dependencies, ndistinct, mcv) ON city, state FROM addresses;  -- (pg10+; mcv pg12+)
ANALYZE addresses;
```

`dependencies` (functional deps, pg10+), `ndistinct` (multi-column distinct counts, pg10+),
`mcv` (most-common combinations, pg12+); single-**expression** stats `(pg14+)`. Note: extended stats
are **not** used for join selectivity yet.

### Key planner GUCs

| GUC | Default | Tune because | |
|-----|---------|-------------|---|
| `random_page_cost` | `4.0` | Lower toward `1.1` on **SSD/cached** data so index scans look cheaper | session/server |
| `effective_cache_size` | `4GB` | Planner's estimate of OS+PG cache; **higher → favours index scans** (no RAM reserved) | server |
| `work_mem` | `4MB` | Memory **per sort/hash node**; raise to stop external-merge/batch spills (×many nodes!) | session/server |
| `seq_page_cost` | `1.0` | The baseline cost unit | |
| `enable_seqscan`, `enable_nestloop`, … | `on` | **Diagnostic only:** set off to *discourage* a node and see the alternative; plan shows `Disabled: true` (pg18+) | session |
| `jit` | `on` | JIT compile expensive plans (pg11+); disable for many short OLTP queries | session/server |

Setting `effective_cache_size`/`work_mem` server-wide is **postgres-admin** territory; here we use
them per-session to fix a specific plan. Full GUC reference + `enable_*` flags:
[references/statistics-and-planner.md](references/statistics-and-planner.md).

## VACUUM, bloat & MVCC

PostgreSQL is **MVCC**: an `UPDATE` or `DELETE` doesn't overwrite a row — it leaves the old version
as a **dead tuple** so concurrent transactions keep a consistent snapshot. **VACUUM** reclaims that
dead space for reuse. If dead tuples accumulate faster than vacuum clears them, tables and indexes
**bloat** — every scan reads more pages, and plans slow down even when "nothing changed."

```sql
-- Find bloat candidates: lots of dead tuples, or autovacuum falling behind
SELECT relname, n_live_tup, n_dead_tup,
       round(n_dead_tup * 100.0 / nullif(n_live_tup + n_dead_tup, 0), 1) AS dead_pct,
       last_autovacuum, autovacuum_count
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
```

- **`VACUUM`** (plain) reclaims dead space **for reuse inside the table**, runs online (no exclusive
  lock), and updates the visibility map. It does **not** return space to the OS. This is what you
  want routinely; **autovacuum** does it automatically.
- **`VACUUM FULL`** rewrites the whole table into a new file (returns space to the OS) but takes an
  **`ACCESS EXCLUSIVE`** lock — it blocks all access. ⚠️ **In PG19 `VACUUM FULL` is deprecated** in
  favour of the new **`REPACK`** command, which unifies `VACUUM FULL` + `CLUSTER` and adds
  **`REPACK … CONCURRENTLY` (pg19+, beta)** to rewrite without the exclusive lock. On PG18 and
  earlier use `VACUUM FULL` / `CLUSTER` (or external `pg_repack`).
- **`ANALYZE`** (stats) is separate from **`VACUUM`** (space) though autovacuum runs both; `n_dead_tup`
  triggers vacuum, `n_mod_since_analyze` triggers analyze.

VACUUM is also how Postgres prevents **transaction-ID wraparound** (by *freezing* old rows).
**Tuning autovacuum thresholds/cost limits is server config → postgres-admin.** Here we diagnose
*whether* bloat is the problem and run a manual `VACUUM (VERBOSE, ANALYZE) tbl` to fix it. MVCC
internals (xmin/xmax), the visibility/free-space maps, `VACUUM` options, freezing, and bloat
measurement: [references/vacuum-and-bloat.md](references/vacuum-and-bloat.md).

## Parallel query & JIT

For big scans/joins/aggregates the planner may split work across **parallel workers** under a
**`Gather`** (or `Gather Merge`, pg10+) node; per-worker `actual` rows/time are averages (× `loops`).
Parallel query arrived in 9.6 (bedrock); **Parallel Hash and Parallel Append are pg11+**.

```sql
SET max_parallel_workers_per_gather = 4;   -- 0 disables parallelism for the session
-- Won't parallelize: writes (most DML), cursors, PARALLEL UNSAFE functions, already-parallel queries.
```

Knobs: `max_parallel_workers_per_gather`, `max_parallel_workers`, `min_parallel_table_scan_size`,
`parallel_setup_cost`, `parallel_tuple_cost`, `parallel_leader_participation`. **JIT** (pg11+,
on-by-default pg12) compiles expression evaluation for plans above `jit_above_cost` — a win for long
analytical queries, pure overhead for many tiny OLTP ones. Details:
[references/statistics-and-planner.md](references/statistics-and-planner.md).

## Performance extensions

These ship with PostgreSQL (contrib) — **install/setup via the `postgres-extensions` skill**; reach
for them when:

| Extension | Use it to | |
|-----------|-----------|---|
| **pg_stat_statements** | Find the *actually* slow/frequent queries (total & mean time, calls, rows) — **start here** | step ① |
| **auto_explain** | Auto-log plans of slow statements in production (`log_min_duration`, `log_analyze`, `log_io` pg19+) | step ② |
| **pageinspect** | Inspect raw index/heap page contents (deep index debugging) | |
| **pg_buffercache** | See what's actually in shared buffers | |
| **pgstattuple** | Measure real table/index bloat precisely | bloat |
| **amcheck** | Verify B-tree/index integrity | |

For ad-hoc plan logging without an extension, `pg_overexplain`'s `EXPLAIN (DEBUG)` / `(RANGE_TABLE)`
expose planner internals (pg17+).

## Quick reference

| Goal | Command |
|------|---------|
| Plan + reality + I/O | `EXPLAIN (ANALYZE, BUFFERS) <query>;` |
| Safe ANALYZE of DML | `BEGIN; EXPLAIN ANALYZE <dml>; ROLLBACK;` |
| Machine-readable plan | `EXPLAIN (ANALYZE, FORMAT JSON) <query>;` |
| Plan a `$1` query | `EXPLAIN (GENERIC_PLAN) <query>;` *(pg16+)* |
| Refresh stats | `ANALYZE [table];` |
| Correlated-column stats | `CREATE STATISTICS … ON a, b FROM t; ANALYZE t;` *(pg10+)* |
| Inspect column stats | `SELECT * FROM pg_stats WHERE tablename='t';` |
| Build index online | `CREATE INDEX CONCURRENTLY …;` |
| Rebuild bloated index online | `REINDEX INDEX CONCURRENTLY …;` *(pg12+)* |
| Find bloat / vacuum lag | `SELECT … FROM pg_stat_user_tables;` (query above) |
| Manual cleanup | `VACUUM (VERBOSE, ANALYZE) table;` |
| Favour index scans (SSD) | `SET random_page_cost = 1.1;` |
| Stop sort/hash spills | `SET work_mem = '64MB';` |
| List indexes (psql) | `\d table` · `\di+` |

## Troubleshooting

- **"It's slow but EXPLAIN looks fine."** You ran `EXPLAIN`, not `EXPLAIN ANALYZE` — estimates can be
  perfect while reality is awful. Always `ANALYZE` (with `BUFFERS`) to see actuals.
- **Estimated rows ≪ actual rows.** Stale stats (`ANALYZE`), a skewed column (raise `SET STATISTICS`),
  or correlated columns (`CREATE STATISTICS`). This is the #1 cause of bad plans.
- **Index exists but Seq Scan is used.** Often correct (query isn't selective / table tiny). If wrong:
  predicate not sargable (wrapped column in a function → use an **expression index**), type mismatch,
  or `random_page_cost` too high for your storage.
- **Nested Loop with millions of loops.** A row underestimate on the outer side; fix the estimate or
  add the inner-side index — don't just `SET enable_nestloop=off` in production.
- **`Batches > 1` / `external merge Disk`.** Sort/hash spilled to disk → raise `work_mem` (remember
  it's *per node*, so a complex plan multiplies it).
- **Index-only scan still hits the heap (`Heap Fetches` high).** Visibility map is stale → `VACUUM`
  the table.
- **Query slowed down over time, data unchanged.** Bloat — check `n_dead_tup` / `dead_pct`; `VACUUM`,
  and on PG19 consider `REPACK` (`VACUUM FULL`/`CLUSTER` before).
- **A newer option errors** (`EXPLAIN (MEMORY)`, `(SERIALIZE)`, `(IO)`…). Your server predates it —
  check `SELECT version();` against [references/version-features.md](references/version-features.md).

## References

- [references/explain.md](references/explain.md) — every `EXPLAIN` option in depth, all `FORMAT`s,
  per-worker/parallel output, `Index Searches`/`Disabled`/`Subplans Removed`, and a full
  line-by-line plan walkthrough.
- [references/reading-plans.md](references/reading-plans.md) — each scan/join/aggregate/sort node
  explained, the cost model, and a catalogue of diagnosable plan-shape problems.
- [references/indexes.md](references/indexes.md) — all six index types, operator classes
  (`gin_trgm_ops`, `jsonb_path_ops`, …), multicolumn/partial/expression/covering, `INCLUDE`,
  `CONCURRENTLY`, `REINDEX`, deduplication, fillfactor, index-only scans & the visibility map.
- [references/statistics-and-planner.md](references/statistics-and-planner.md) — `pg_stats` columns,
  `CREATE STATISTICS` kinds, every cost & `enable_*` GUC, parallel-query knobs, JIT, join-order GUCs.
- [references/vacuum-and-bloat.md](references/vacuum-and-bloat.md) — MVCC tuple versions, dead tuples,
  visibility/free-space maps, `VACUUM` vs `FULL` vs `REPACK` (pg19), all `VACUUM` options, freezing &
  wraparound, autovacuum monitoring, and bloat measurement.
- [references/version-features.md](references/version-features.md) — feature → minimum PostgreSQL
  version, with "how to read" and sources (EXPLAIN options matrix, index/stats/vacuum/parallel/JIT).

## Resources

- EXPLAIN: <https://www.postgresql.org/docs/current/sql-explain.html> ·
  Using EXPLAIN: <https://www.postgresql.org/docs/current/using-explain.html>
- Planner statistics: <https://www.postgresql.org/docs/current/planner-stats.html>
- Index types: <https://www.postgresql.org/docs/current/indexes-types.html>
- Routine vacuuming: <https://www.postgresql.org/docs/current/routine-vacuuming.html>
- Parallel query: <https://www.postgresql.org/docs/current/parallel-query.html>
