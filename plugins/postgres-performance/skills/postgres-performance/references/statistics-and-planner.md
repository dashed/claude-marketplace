# Statistics & the Planner

How the planner estimates, the statistics that drive it, and every GUC you'd tune to change its
mind. The planner's job is to **estimate row counts (selectivity) and costs**, then pick the cheapest
plan — so almost all planner tuning is really **making estimates accurate** or **making costs match
your hardware**.

## Contents

- [Single-column statistics & pg_stats](#single-column-statistics--pg_stats)
- [Tuning the statistics target](#tuning-the-statistics-target)
- [Extended statistics](#extended-statistics)
- [Cost GUCs](#cost-gucs)
- [Memory GUCs](#memory-gucs)
- [enable_* planner flags](#enable_-planner-flags)
- [Join order GUCs](#join-order-gucs)
- [Parallel query](#parallel-query)
- [JIT](#jit)

## Single-column statistics & pg_stats

Per-table size lives in `pg_class.reltuples` / `relpages` (updated by `VACUUM`, `ANALYZE`, and some
DDL). Per-column distribution lives in `pg_statistic`, best read through the **`pg_stats`** view:

```sql
SELECT attname, n_distinct, null_frac, avg_width, correlation,
       most_common_vals, most_common_freqs, histogram_bounds
FROM pg_stats WHERE tablename = 'orders' AND attname = 'status';
```

| Column | Meaning & why it matters |
|--------|--------------------------|
| `n_distinct` | Distinct values (positive = absolute count; **negative = ratio to row count**, e.g. `-1` = all unique). Drives group/join cardinality. |
| `null_frac` | Fraction NULL. |
| `most_common_vals` (MCV) + `most_common_freqs` | The frequent values and their frequencies — gives exact selectivity for `WHERE col = 'popular'`. |
| `histogram_bounds` | Equal-frequency buckets for the non-MCV values — selectivity for ranges `col < x`. |
| `correlation` | −1..1 physical/logical ordering correlation. **Near ±1 → index scans are cheap** (sequential heap access); near 0 → random fetches, planner favours bitmap/seq. |
| `avg_width` | Average bytes (affects width/memory estimates). |

`ANALYZE` (run manually or by autovacuum) refreshes these from a **random sample**; estimates are
always approximate. Stale stats after a bulk load/change are the #1 cause of bad plans:

```sql
ANALYZE orders;            -- one table
ANALYZE;                   -- whole database (e.g. right after a big import or pg_restore)
VACUUM (ANALYZE) orders;   -- reclaim + refresh together
```

## Tuning the statistics target

More samples → finer MCV/histogram → better estimates on **skewed** columns, at the cost of bigger
`pg_statistic` and slower `ANALYZE`:

```sql
SHOW default_statistics_target;                              -- global default: 100
SET default_statistics_target = 250;                          -- session, before ANALYZE
ALTER TABLE orders ALTER COLUMN status SET STATISTICS 500;     -- per-column, persistent (then ANALYZE)
ALTER TABLE orders ALTER COLUMN status SET STATISTICS -1;      -- revert to the global default
```

Raise it for columns with irregular distributions that the planner misestimates; leave simple columns
alone. Must `ANALYZE` afterward to recompute.

## Extended statistics

Single-column stats assume columns are **independent**. When they're correlated, the planner
multiplies selectivities and badly **underestimates** combined predicates. `CREATE STATISTICS`
(pg10+) fixes this for a named column set; data is collected by `ANALYZE`.

```sql
CREATE STATISTICS s_geo (dependencies, ndistinct, mcv) ON city, state, zip FROM addresses;
ANALYZE addresses;
```

| Kind | Since | Fixes | When to create |
|------|-------|-------|----------------|
| `dependencies` | pg10 | Underestimate of `WHERE a = ? AND b = ?` when `a` determines `b` (functional dependency) | Strongly correlated columns used together in equality/`IN` |
| `ndistinct` | pg10 | Wrong **group count** for `GROUP BY a, b` (and thus HashAgg vs sort, hash buckets) | Multi-column grouping where group count is misestimated |
| `mcv` | pg12 | Selectivity of specific frequent **combinations** (handles `=`, ranges, more) | Correlated columns where particular value pairs dominate |
| single **expression** | pg14 | Default estimates for an expression (e.g. `WHERE lower(name) = ?`) without an index | An expression repeatedly used in predicates/grouping |

Inspect them via `pg_stats_ext` / `pg_statistic_ext_data` (and `pg_mcv_list_items()` for MCV).
**Limitation:** extended statistics are not yet used for **join** selectivity — only single-relation
estimates. The single-expression form (`CREATE STATISTICS s ON (expr) FROM t`) gives expression-index-
quality estimates without index maintenance.

## Cost GUCs

These translate "work" into the planner's cost units. Defaults assume spinning disk; **SSDs and
well-cached working sets want lower random cost**.

| GUC | Default | What it does | Tuning |
|-----|---------|--------------|--------|
| `seq_page_cost` | 1.0 | Cost of a sequential page fetch (the unit) | Rarely changed (it's the baseline) |
| `random_page_cost` | 4.0 | Cost of a random page fetch | **Lower to ~1.1 on SSD / mostly-cached data** so index scans look cheaper; the single most impactful planner knob |
| `cpu_tuple_cost` | 0.01 | Per-row CPU cost | |
| `cpu_index_tuple_cost` | 0.005 | Per-index-entry CPU cost | |
| `cpu_operator_cost` | 0.0025 | Per-operator/function CPU cost | |
| `effective_cache_size` | 4GB | Planner's **estimate** of total cache (OS + shared_buffers) available for one query | Set to ~50–75% of RAM; **higher favours index scans**. Reserves no memory — it's purely an estimate |

`random_page_cost` and `effective_cache_size` together decide index-vs-seq for medium result sets.
Set them server-wide via **postgres-admin**; set per-session here to test a hypothesis.

## Memory GUCs

| GUC | Default | What it does | Tuning |
|-----|---------|--------------|--------|
| `work_mem` | 4MB | Memory **per sort/hash/Memoize node** before spilling to disk | Raise to stop `external merge Disk` sorts and hash `Batches > 1`. **Per node, per worker** — a complex parallel plan can use many multiples, so don't set it huge globally; raise per-session for the heavy query |
| `hash_mem_multiplier` | 2.0 | Multiplies `work_mem` for hash-based nodes | Raise to give hash aggregates/joins more memory without inflating sorts |
| `maintenance_work_mem` | 64MB | Memory for `CREATE INDEX`, `VACUUM`, `REINDEX` | Raise (e.g. 1GB) to speed index builds & vacuum |
| `temp_buffers` | 8MB | Per-session temp-table buffers | |

`work_mem` is the knob behind most "raise memory to stop the disk spill" fixes you'll find in
[reading-plans.md](reading-plans.md#diagnosable-plan-shape-problems).

## enable_* planner flags

These are **diagnostic toggles**, not production settings. Since pg18 a plan that uses a discouraged
node shows `Disabled: true` (the flags add a large cost penalty rather than truly forbidding the node,
so the planner can still produce a plan).

`enable_seqscan`, `enable_indexscan`, `enable_indexonlyscan`, `enable_bitmapscan`,
`enable_nestloop`, `enable_hashjoin`, `enable_mergejoin`, `enable_hashagg`, `enable_sort`,
`enable_incremental_sort` (pg13+), `enable_memoize` (pg14+), `enable_material`, `enable_gathermerge`,
`enable_parallel_append` / `enable_parallel_hash` (pg11+), `enable_partition_pruning`,
`enable_partitionwise_join` / `enable_partitionwise_aggregate`.

```sql
SET enable_nestloop = off;     -- "what would the planner do without a nested loop here?"
EXPLAIN ANALYZE <query>;
RESET enable_nestloop;          -- always reset; never leave these off in production
```

Use them to **confirm** that the plan you suspect is better actually is — then fix the root cause
(index/stats/rewrite) so the planner chooses it on its own.

## Join order GUCs

The planner explores join orders; for many tables this explodes combinatorially.

| GUC | Default | Effect |
|-----|---------|--------|
| `join_collapse_limit` | 8 | Max `FROM`/`JOIN` items flattened into one join-order search. **Set to 1** to force the planner to honour your explicit `JOIN` order (a manual override when you know better). |
| `from_collapse_limit` | 8 | Max items when flattening sub-queries into the parent. |
| `geqo` | on | Use the **genetic** join-order optimizer beyond `geqo_threshold` (default 12 tables) instead of exhaustive search — faster planning, possibly non-optimal plan. |
| `geqo_threshold` | 12 | Table count that switches to GEQO. |

If planning time is large for a many-table query, lowering `join_collapse_limit`/`from_collapse_limit`
cuts the search space; raising `geqo_threshold` forces exhaustive search (better plan, slower planning).

## Parallel query

The planner adds parallelism (a `Gather`/`Gather Merge` over `Parallel …` nodes) for large scans,
joins, and aggregates when the estimated win exceeds setup cost. Version split:
**9.6 (bedrock)** = Gather, Parallel Seq Scan, parallel nested-loop & hash join (per-worker copy),
two-stage parallel aggregation; **pg10** = Gather Merge, Parallel Index/Index-Only Scan (btree),
Parallel Bitmap Heap Scan, Parallel Merge Join; **pg11** = Parallel Hash (shared table), Parallel
Append, parallel `UNION`.

| GUC | Default | Effect |
|-----|---------|--------|
| `max_parallel_workers_per_gather` | 2 | Workers the planner may add per Gather; **`0` disables parallelism** for the session |
| `max_parallel_workers` | 8 | Cap on parallel-query workers cluster-wide |
| `max_worker_processes` | 8 | Cap on all background workers (parallel workers draw from this) |
| `min_parallel_table_scan_size` | 8MB | Table must exceed this to be considered for parallel scan |
| `min_parallel_index_scan_size` | 512kB | Index size threshold for parallel index scan |
| `parallel_setup_cost` | 1000 | Fixed cost of launching workers; **lower to encourage** parallel plans |
| `parallel_tuple_cost` | 0.1 | Per-row cost of shipping a tuple from worker to leader; **lower to encourage** |
| `parallel_leader_participation` | on | Leader also runs the parallel subplan (`loops = workers + 1`) |

A query **won't** parallelize if it writes data (most DML), uses a cursor / `DECLARE`, calls a
`PARALLEL UNSAFE` function (user functions default to unsafe), or runs inside another parallel query.
`Workers Launched < Planned` → raise `max_parallel_workers` / `max_worker_processes`.

## JIT

**JIT** (pg11+, LLVM-based; **on by default since pg12**) compiles expression evaluation and tuple
deforming for expensive plans, speeding long analytical queries. For high-throughput OLTP (many tiny
queries) the compile time can exceed the saving — a common reason to disable it.

| GUC | Default | Effect |
|-----|---------|--------|
| `jit` | on | Master switch |
| `jit_above_cost` | 100000 | Total plan cost above which JIT is considered |
| `jit_inline_above_cost` | 500000 | Cost above which functions are inlined |
| `jit_optimize_above_cost` | 500000 | Cost above which expensive LLVM optimizations run |

`EXPLAIN (ANALYZE)` shows a `JIT:` section (functions, timing) when it fired. If short queries got
slower after an upgrade, check whether JIT is compiling them — `SET jit = off` to test, then tune
`jit_above_cost` upward or disable globally via postgres-admin.
