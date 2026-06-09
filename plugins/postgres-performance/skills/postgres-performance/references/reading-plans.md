# Reading Query Plans — Node Reference

Every plan node you're likely to meet, what it costs, what good and bad versions look like, and a
catalogue of plan-shape problems with fixes. Pair with [explain.md](explain.md) (the EXPLAIN options
and output lines) and [indexes.md](indexes.md) / [statistics-and-planner.md](statistics-and-planner.md)
(the fixes).

## Contents

- [How to read a tree](#how-to-read-a-tree)
- [Scan nodes](#scan-nodes)
- [Join nodes](#join-nodes)
- [Aggregation & grouping](#aggregation--grouping)
- [Sort, Limit & friends](#sort-limit--friends)
- [Set, subquery & misc nodes](#set-subquery--misc-nodes)
- [Parallel nodes](#parallel-nodes)
- [Diagnosable plan-shape problems](#diagnosable-plan-shape-problems)

## How to read a tree

A plan is a **tree of nodes**. Leaves are **scan nodes** (produce raw rows); above them sit join,
sort, aggregate, and other nodes. Read **bottom-up** (data flows up): each `->` child feeds its
parent; indentation = depth; the top line is the whole query. A parent's cost and time **include**
its children. Rows and time on a node are **per execution (loop/worker)** — multiply by `loops`.

The first question at every node: **does estimated `rows` match actual `rows`?** Plan choice is
driven by estimates; a wrong estimate is the usual root cause of a wrong plan.

## Scan nodes

### Seq Scan
Reads every page of the table, applying any `Filter`. **Cost** ≈ `relpages × seq_page_cost + rows ×
cpu_tuple_cost`. **Good** when most rows match, the table is small, or no useful index exists.
**Bad** when a selective `WHERE` with `Rows Removed by Filter: <large>` should have used an index —
check stats and `random_page_cost`.

### Index Scan
Walks an index to find matching entries, then fetches each heap row (random I/O), returning rows in
index order. **Good** for retrieving **few** rows or satisfying `ORDER BY` for free. **Bad** for many
rows: random heap fetches make it lose to a Seq Scan or Bitmap scan. `Index Cond` = handled by the
index; a `Filter` underneath = checked after fetching (less selective).

### Index Only Scan
Answers entirely from the index, skipping the heap **when the page is marked all-visible** in the
visibility map. The win shows as **`Heap Fetches: 0`**. Needs every referenced column in the index
(key or `INCLUDE` payload, pg11+). `Heap Fetches` climbing → the table needs `VACUUM` to refresh the
visibility map.

### Bitmap Index Scan + Bitmap Heap Scan
Two-step: the **Bitmap Index Scan** builds an in-memory bitmap of matching TIDs; the **Bitmap Heap
Scan** sorts them by physical page and fetches each page **once**, in order. The sweet spot for a
**medium** number of matching rows — more than an Index Scan wants (avoids repeated random fetches)
but fewer than a Seq Scan. `BitmapAnd` / `BitmapOr` combine several index bitmaps (multi-index plans).
`Heap Blocks: lossy=N` means `work_mem` was too small to keep exact TIDs (it fell back to whole-page
bits) → a `Recheck Cond` re-filters those pages.

### Tid Scan / Tid Range Scan / Function Scan / Values Scan / Result
`Tid Scan` fetches by `ctid`. `Function Scan` reads a set-returning function in `FROM`. `Values Scan`
reads a `VALUES` list. `Result` evaluates a constant/one-time expression (e.g. a scalar with no
table). These are cheap and rarely the problem.

## Join nodes

PostgreSQL joins **two inputs at a time**; multi-table joins are a tree of binary joins whose
**order** the planner chooses (see [statistics-and-planner.md](statistics-and-planner.md#join-order-gucs)).

### Nested Loop
For each outer row, scan the inner side. **Cost** ≈ `outer_rows × inner_scan_cost`. **Excellent** when
the outer side is tiny and the inner side has an index (the inner scan is cheap and indexed).
**Catastrophic** when the outer side is large or, worse, **underestimated**: `loops` explodes and an
indexed inner scan runs millions of times. The classic "query fell off a cliff after data grew" plan.
A `Materialize` may sit on the inner side to cache its rows across loops; `Memoize` (pg14+) caches
inner results keyed by parameters (great for skewed/repeated keys).

### Hash Join
Builds an in-memory **hash table** from the smaller input (the `Hash` child), then probes it while
scanning the other input. **Cost** ≈ build + probe, mostly CPU. **Best** for large, unsorted,
equality (`=`) joins. The `Hash` node shows `Buckets`, `Batches`, `Memory Usage`. **`Batches > 1`
means the hash spilled to disk** — raise `work_mem`. Only works for equality conditions.

### Merge Join
Requires **both inputs sorted** on the join key; walks them in lockstep. **Best** when inputs are
already sorted (e.g. both come from index scans on the join column) or for `>`/range merge joins.
If inputs aren't sorted, it pays for explicit `Sort` nodes — often making a Hash Join cheaper. On
duplicate outer keys it rescans part of the inner side, which can inflate the inner node's reported
actual row count (a measurement artifact, not a bug).

## Aggregation & grouping

| Node | How | Notes |
|------|-----|-------|
| **Aggregate** | Single aggregate over all rows (no GROUP BY) | e.g. `SELECT count(*)` |
| **HashAggregate** | Hash rows by grouping key, aggregate per bucket | No input order needed; can spill (pg13+ accounts disk) — watch memory |
| **GroupAggregate** | Aggregate over **sorted** input, one group at a time | Needs a Sort or ordered index; streams, low memory |
| **Partial Aggregate** → **Finalize Aggregate** | Two-stage parallel aggregation | Workers produce partials; leader combines |
| **MixedAggregate** / `GroupingSets` | `GROUPING SETS` / `ROLLUP` / `CUBE` | |

The planner picks HashAggregate vs GroupAggregate by group count and available memory. A
HashAggregate that spills, or a GroupAggregate forced into an expensive Sort, is a `work_mem` or
index-ordering opportunity.

## Sort, Limit & friends

- **Sort** — `Sort Method: quicksort Memory: nkB` (in-memory) / `top-N heapsort` (sort + `LIMIT`) /
  **`external merge Disk: nkB`** (spilled → raise `work_mem`). `Sort Key:` lists the columns.
- **Incremental Sort (pg13+)** — input is already sorted on a **prefix** of the sort keys
  (`Presorted Key:`); it only sorts within each prefix group. Cheaper memory, and lets `LIMIT` return
  early. Controlled by `enable_incremental_sort`.
- **Limit** — stops pulling rows once the count is met; pushes a fractional cost down to its child
  (which still *reports* its full estimated cost). The reason a `LIMIT` query can pick a totally
  different plan than the same query without it.
- **Unique** / **WindowAgg** / **SetOp** — duplicate removal / window functions / `INTERSECT`/`EXCEPT`.

## Set, subquery & misc nodes

- **Append** / **MergeAppend** — concatenate child scans (partitioned tables, `UNION ALL`);
  MergeAppend preserves order. `Subplans Removed: N` (pg10+) = partitions pruned at run time.
- **SubPlan** — a correlated sub-SELECT run per outer row (expensive; shown as `SubPlan N`).
  A **hashed SubPlan** runs once into a hash table (good); an **InitPlan** runs once and caches a
  scalar (cheap). Uncorrelated subqueries often get hashed or turned into joins.
- **Materialize** — buffers a child's rows in memory for repeated reads (nested-loop inner side).
- **Memoize (pg14+)** — caches inner results keyed by the loop parameters; big win when outer keys
  repeat, neutral-to-bad when they're all distinct.
- **Gather / Gather Merge** — collect parallel-worker output (see below).

## Parallel nodes

`Gather` / **`Gather Merge` (pg10+)** sit atop the parallel region; below them, `Parallel`-prefixed
scans (`Parallel Seq Scan`, `Parallel Index Scan` (btree, pg10+), `Parallel Bitmap Heap Scan`),
`Parallel Hash` (shared hash table, pg11+) and `Parallel Append` (pg11+) divide work. With
`parallel_leader_participation=on`, `loops = workers + 1` and per-worker rows/time are **averages**.
A query won't parallelize if it writes data, uses a cursor, calls a `PARALLEL UNSAFE` function, or is
already inside a parallel query. Knobs and the version split are in
[statistics-and-planner.md](statistics-and-planner.md#parallel-query) and
[version-features.md](version-features.md#parallel-query).

## Diagnosable plan-shape problems

| Symptom in the plan | Likely cause | Fix |
|---------------------|--------------|-----|
| `rows=10` est vs `rows=100000.00` actual | Stale/insufficient stats; correlated columns | `ANALYZE`; `ALTER … SET STATISTICS`; `CREATE STATISTICS` |
| Nested Loop, inner `loops` huge | Outer-side **underestimate** | Fix the estimate; ensure inner index; *not* `enable_nestloop=off` in prod |
| Seq Scan + `Rows Removed by Filter: <huge>` | No usable index / non-sargable predicate | Add index; rewrite predicate (don't wrap the column in a function — use an expression index) |
| Index exists but Seq Scan chosen | Query not selective (often correct), or `random_page_cost` too high, or type mismatch | Verify selectivity; on SSD `SET random_page_cost=1.1`; cast to match index type |
| Hash node `Batches > 1` | Hash spilled to disk | Raise `work_mem` |
| `Sort Method: external merge Disk` | Sort spilled to disk | Raise `work_mem`; or add an index providing the order |
| Index-Only Scan with `Heap Fetches` high | Visibility map stale | `VACUUM` the table |
| `Rows Removed by Index Recheck` | Lossy index (GiST/BRIN) or bitmap went lossy | Expected for lossy AMs; for bitmap raise `work_mem` |
| `Workers Launched < Workers Planned` | No free parallel worker slots | Raise `max_parallel_workers` / `max_worker_processes` |
| `Disabled: true` (pg18+) on a node | An `enable_*=off` is forcing a worse plan | Re-enable it; it's a diagnostic, not a production setting |
| Plan flips with `LIMIT` | Startup-vs-total cost tradeoff | Usually correct; ensure an index supplies `ORDER BY` so `LIMIT` can stop early |
| Huge planning time, many tables | Exhaustive join search | Lower `join_collapse_limit`/`from_collapse_limit`, or `geqo` kicks in past `geqo_threshold` |

**Golden rule:** the `enable_*` flags and `SET random_page_cost`/`work_mem` at session scope are for
*diagnosis* — to discover what the planner *would* do and confirm a hypothesis. The durable fix is
almost always a better index, fresher/more statistics, or a query rewrite — not a forced plan.
