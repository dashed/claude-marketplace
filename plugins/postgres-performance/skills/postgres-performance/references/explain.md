# EXPLAIN — Complete Reference

Deep reference for `EXPLAIN` / `EXPLAIN ANALYZE`: every option, all output formats, parallel and
extra-statistics lines, and a line-by-line walkthrough of a real plan. For *what the nodes mean* see
[reading-plans.md](reading-plans.md); for the feature→version map see
[version-features.md](version-features.md).

## Contents

- [Syntax & every option](#syntax--every-option)
- [The cost model](#the-cost-model)
- [Reading an EXPLAIN ANALYZE line](#reading-an-explain-analyze-line)
- [Extra statistics lines](#extra-statistics-lines)
- [A full annotated walkthrough](#a-full-annotated-walkthrough)
- [Output formats](#output-formats)
- [Parallel plans in EXPLAIN](#parallel-plans-in-explain)
- [GENERIC_PLAN, prepared statements & custom vs generic plans](#generic_plan-prepared-statements--custom-vs-generic-plans)
- [Caveats](#caveats)
- [auto_explain & pg_overexplain](#auto_explain--pg_overexplain)

## Syntax & every option

```sql
EXPLAIN [ ( option [, ...] ) ] statement
```

Options (PG19 synopsis order). Boolean options accept `TRUE`/`ON`/`1` or `FALSE`/`OFF`/`0`, and the
value may be omitted (defaults to `TRUE`):

| Option | Default | Requires ANALYZE | What it does |
|--------|---------|------------------|--------------|
| `ANALYZE [bool]` | off | — | **Executes** the statement; adds actual time, rows, loops. |
| `VERBOSE [bool]` | off | no | Output column list per node, schema-qualified names, range-table aliases, trigger names, query identifier (if `compute_query_id` on). Pg18+ also surfaces per-worker CPU, WAL, and average-read stats. |
| `COSTS [bool]` | on | no | Estimated startup/total cost, estimated rows, estimated width. Turn off for diff-stable plans. |
| `SETTINGS [bool]` | off | no | Planner-affecting GUCs whose value differs from the built-in default. **(pg12+)** |
| `GENERIC_PLAN [bool]` | off | **incompatible** | Plan a statement containing `$1`-style placeholders without values. Cannot combine with ANALYZE. **(pg16+)** |
| `BUFFERS [bool]` | **on with ANALYZE (pg18+)**, else off | no | Buffer usage: shared/local/temp blocks hit/read/dirtied/written + I/O timing if `track_io_timing` on. Without ANALYZE, reports planning-phase buffers only. |
| `SERIALIZE [ NONE \| TEXT \| BINARY ]` | NONE | yes | Measure cost of converting output rows to text/binary for the client (catches expensive output functions / TOAST de-toasting). **(pg17+)** |
| `WAL [bool]` | off | yes | WAL records, full-page images (FPI), bytes generated, and (pg18+) times WAL buffers filled. **(pg13+)** |
| `TIMING [bool]` | on with ANALYZE | yes | Per-node actual timing. Set **off** on machines with slow `gettimeofday()` to measure row counts cheaply (total run time is still measured). |
| `SUMMARY [bool]` | on with ANALYZE | no | Planning/execution time footer. **(pg10+)** |
| `MEMORY [bool]` | off | no | Planner memory consumption (precise + with allocation overhead). **(pg17+)** |
| `IO [bool]` | off | yes | Asynchronous-I/O (AIO) statistics per supporting scan node. **(pg19+, beta)** |
| `FORMAT { TEXT \| XML \| JSON \| YAML }` | TEXT | no | Output format. JSON/YAML/XML carry identical info but are machine-parseable. |

The workhorse invocation is `EXPLAIN (ANALYZE, BUFFERS) <query>`. Add `VERBOSE, SETTINGS` when
sharing a plan for diagnosis, and `FORMAT JSON` when a tool will parse it.

> ⚠️ **`ANALYZE` executes the statement.** For data-modifying statements, run inside a transaction
> you roll back:
> ```sql
> BEGIN;
> EXPLAIN ANALYZE UPDATE t SET c = c + 1 WHERE id < 100;
> ROLLBACK;
> ```
> `EXPLAIN` (no `ANALYZE`) never executes, so it's always safe.

## The cost model

Costs are in **arbitrary units** anchored to `seq_page_cost = 1.0` (one sequential page fetch).
The planner computes, for each candidate node:

```
cost ≈ (pages read × seq_page_cost)            -- sequential I/O
     + (pages read × random_page_cost)          -- random I/O (index/heap fetches)
     + (rows × cpu_tuple_cost)                   -- per-row CPU
     + (rows × cpu_operator_cost × #operators)   -- per-WHERE-clause CPU
```

Example from the docs: a 10000-row table in 345 pages → Seq Scan cost
`(345 × 1.0) + (10000 × 0.01) = 445.00`. Two numbers are shown — **startup..total**:

- **startup cost** — work before the first row can be emitted (e.g. building a hash table, sorting).
- **total cost** — to return *all* rows. A parent that stops early (`LIMIT`, semi-join) pays a
  prorated fraction; the planner interpolates for `LIMIT`.

The planner minimizes the **top node's total cost** (or startup cost in `EXISTS`/`LIMIT 1` contexts).
Cost is *relative*, not milliseconds — never compare cost to actual time.

## Reading an EXPLAIN ANALYZE line

```
->  Index Scan using tenk2_unique2 on tenk2 t2  (cost=0.29..7.90 rows=1 width=244) (actual time=0.003..0.003 rows=1.00 loops=10)
```

| Token | Meaning |
|-------|---------|
| `->` + indentation | Position in the plan tree (child of the node above) |
| `Index Scan using … on …` | Node type, index, and target relation/alias |
| `cost=0.29..7.90` | **Estimated** startup..total cost |
| `rows=1` (in cost parens) | **Estimated** rows emitted **per loop** |
| `width=244` | Estimated average row width in bytes |
| `actual time=0.003..0.003` | **Actual** first-row..last-row ms **per loop** |
| `rows=1.00` (in actual parens) | **Actual** rows emitted **per loop** (2 decimals, pg18+) |
| `loops=10` | Times the node executed |

**Totals = per-loop × loops.** Above: total time `0.003 × 10 = 0.03 ms`, total rows `1 × 10 = 10`.
The comparison that matters most: **estimated rows vs actual rows** at each node.

Footer lines (with `ANALYZE`/`SUMMARY`):
- `Planning Time:` — time to generate & optimize the plan (excludes parse/rewrite). `Planning:` with
  `Buffers:` shows blocks touched during planning.
- `Execution Time:` — executor start + run + triggers + shutdown (excludes parse/rewrite/plan).

## Extra statistics lines

Nodes attach extra lines when relevant:

| Line | Meaning |
|------|---------|
| `Buffers: shared hit=H read=R dirtied=D written=W` | Cache hits / disk reads / pages dirtied / pages evicted. `local` = temp tables; `temp` = sort/hash spill files. Includes children. |
| `Filter: (cond)` + `Rows Removed by Filter: N` | A non-index predicate checked per row; `N` rows read then discarded. High `N` = wasted work. |
| `Index Cond: (cond)` | Predicate satisfied **by the index** (good — not a post-filter). |
| `Recheck Cond:` + `Rows Removed by Index Recheck: N` | Lossy index returned candidates that the recheck dropped (GiST/BRIN, or bitmap turned lossy under memory pressure). |
| `Heap Blocks: exact=E lossy=L` | Bitmap scan page accounting; `lossy` means `work_mem` was too small to track exact TIDs. |
| `Index Searches: N` | **(pg18+)** Number of index descents — exposes array scans and **B-tree skip scan**. |
| `Heap Fetches: N` | Index-Only Scan heap visits for visibility; **`0` is the goal** (else VACUUM). |
| `Sort Method: … Memory: nkB` / `Disk: nkB` | `quicksort`/`top-N heapsort` (in-memory) vs `external merge` (spilled → raise `work_mem`). |
| `Buckets: B Batches: N Memory Usage: nkB` | Hash node; **`Batches > 1` = spilled to disk** → raise `work_mem`. |
| `Workers Planned: P / Launched: L` | Parallelism; `Launched < Planned` means worker slots were exhausted (`max_parallel_workers`). |
| `Disabled: true` | **(pg18+)** Node used despite an `enable_*=off` penalty (no cheaper plan existed). |
| `Subplans Removed: N` | **(pg10+)** Partitions pruned at run time from an Append/MergeAppend. |
| `Worker N: actual time=…` | Per-worker breakdown (with `VERBOSE`) — check for uneven distribution. |

## A full annotated walkthrough

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM tenk1 t1, tenk2 t2
WHERE t1.unique1 < 10 AND t1.unique2 = t2.unique2;
```
```
 Nested Loop  (cost=4.65..118.50 rows=10 width=488) (actual time=0.017..0.051 rows=10.00 loops=1)
   Buffers: shared hit=36 read=6
   ->  Bitmap Heap Scan on tenk1 t1  (cost=4.36..39.38 rows=10 width=244) (actual time=0.009..0.017 rows=10.00 loops=1)
         Recheck Cond: (unique1 < 10)
         Heap Blocks: exact=10
         Buffers: shared hit=3 read=5 written=4
         ->  Bitmap Index Scan on tenk1_unique1  (cost=0.00..4.36 rows=10 width=0) (actual time=0.004..0.004 rows=10.00 loops=1)
               Index Cond: (unique1 < 10)
               Index Searches: 1
               Buffers: shared hit=2
   ->  Index Scan using tenk2_unique2 on tenk2 t2  (cost=0.29..7.90 rows=1 width=244) (actual time=0.003..0.003 rows=1.00 loops=10)
         Index Cond: (unique2 = t1.unique2)
         Index Searches: 10
         Buffers: shared hit=24 read=6
 Planning:
   Buffers: shared hit=15 dirtied=9
 Planning Time: 0.485 ms
 Execution Time: 0.073 ms
```

Reading bottom-up:
1. **Bitmap Index Scan on `tenk1_unique1`** — descends the index once (`Index Searches: 1`) for
   `unique1 < 10`, producing a bitmap of 10 TIDs. Estimated 10, actual 10 — perfect.
2. **Bitmap Heap Scan on `tenk1`** — fetches those 10 rows in physical page order (`Heap Blocks:
   exact=10`); `written=4` means 4 dirty pages were evicted during the scan.
3. **Nested Loop** — for **each** of the 10 outer rows, runs the inner side once → `loops=10` below.
4. **Index Scan on `tenk2_unique2`** — `loops=10`, `Index Searches: 10`, 1 row each. Total inner
   rows = `1 × 10 = 10`, total inner time = `0.003 × 10 = 0.03 ms`. A Nested Loop is correct here
   because the outer side is tiny and the inner has an index.

Every estimate matches actual → a healthy plan. The diagnostic alarm would be e.g.
`rows=1 … rows=5000.00 loops=10` on the inner node: a Nested Loop driven by a row **underestimate**,
which a hash join would have beaten.

## Output formats

```sql
EXPLAIN (FORMAT JSON) SELECT * FROM foo WHERE i = 4;
```
```json
[ { "Plan": { "Node Type": "Index Scan", "Relation Name": "foo", "Alias": "foo",
              "Startup Cost": 0.00, "Total Cost": 5.98, "Plan Rows": 1, "Plan Width": 4,
              "Index Cond": "(i = 4)" } } ]
```

- **TEXT** — human-readable; what you read interactively.
- **JSON / YAML** — same data, structured; feed to tools (pgMustard, explain.dalibo.com, `jq`).
- **XML** — structured; rarely used by hand.

For programmatic capture: `psql -At -c "EXPLAIN (ANALYZE, FORMAT JSON) <query>" | jq …`.

## Parallel plans in EXPLAIN

```
 Gather  (cost=4.65..70.96 rows=10 width=488) (actual time=1.161..11.655 rows=10.00 loops=1)
   Workers Planned: 2
   Workers Launched: 2
   ->  Nested Loop  (… rows=4 …) (actual time=0.247..0.317 rows=3.33 loops=3)
         ->  Parallel Bitmap Heap Scan on tenk1 t1  (… loops=3)
```

- Everything **below `Gather`** runs in parallel; the leader gathers worker output. `Gather Merge`
  (pg10+) preserves sort order.
- With `parallel_leader_participation = on` (default), the leader also runs the parallel subplan, so
  `loops = workers + 1` (here 3 = 2 workers + leader). **Per-worker `actual` rows/time are averages**
  — multiply by `loops` for totals (`3.33 × 3 ≈ 10`).
- `Workers Launched < Workers Planned` → no free worker slots (`max_parallel_workers` /
  `max_worker_processes` exhausted). Add `VERBOSE` to see each `Worker N:` line and check balance.

## GENERIC_PLAN, prepared statements & custom vs generic plans

A prepared statement starts with **custom** plans (re-planned per parameter values) and may switch
to a single **generic** plan (planned once with placeholders) after ~5 executions if that's not
estimated to be worse. To inspect the generic plan of a parameterized query without preparing it:

```sql
EXPLAIN (GENERIC_PLAN)                       -- (pg16+)
SELECT * FROM test WHERE id > $1 AND id < $2;
```

Cast placeholders (`$1::int`) if their type can't be inferred. Generic plans can't use
parameter-specific selectivity, so a generic plan over a skewed column may be much worse than the
custom plan — `GENERIC_PLAN` lets you see exactly what the cached generic plan would do. For a
prepared statement, `EXPLAIN [ANALYZE] EXECUTE name(args)` shows the plan actually chosen.

## Caveats

- **`EXPLAIN ANALYZE` adds measurement overhead** (per-node `gettimeofday()`), so its reported node
  times can exceed normal execution, especially for cheap nodes on slow-clock machines. Use
  `TIMING OFF` to keep just row counts. Measure your clock overhead with `pg_test_timing`.
- **Network & output conversion costs are excluded** unless you add `SERIALIZE`. A query that's slow
  to *return* (huge/TOASTed columns) can look fast in plain `EXPLAIN ANALYZE`.
- **Don't extrapolate from toy tables.** On a one-page table you'll always get a Seq Scan; plans flip
  with data volume because cost isn't linear.
- **`LIMIT` & merge-join artifacts:** a node stopped early by `LIMIT` shows full estimated cost but
  small actual rows (not an error). Merge joins may rescan the inner side on duplicate keys, inflating
  its actual row count. `BitmapAnd`/`BitmapOr` always report `rows=0` (implementation limitation).

## auto_explain & pg_overexplain

- **`auto_explain`** (contrib; set up via the **postgres-extensions** skill) logs plans of slow
  statements in production. Key settings: `auto_explain.log_min_duration` (ms threshold; `0`=all,
  `-1`=off), `log_analyze` (logs actuals — high overhead, forces timing on all statements),
  `log_buffers`, `log_wal`, `log_io` **(pg19+, beta)**, `log_timing` (on by default), `log_verbose`,
  `log_settings`, `log_format`, `log_nested_statements`, `sample_rate`.
- **`pg_overexplain`** (contrib, pg18+) adds debugging options `EXPLAIN (DEBUG)` (disabled-node
  counters, parallel-safety, plan-node IDs, params, plan flags) and `EXPLAIN (RANGE_TABLE)` (the
  query's range table) — for planner development, not routine tuning.
