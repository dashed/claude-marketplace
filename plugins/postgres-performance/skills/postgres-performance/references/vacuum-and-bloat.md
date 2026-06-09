# VACUUM, MVCC & Bloat

Why PostgreSQL tables bloat, what `VACUUM` actually does, and how to diagnose and fix it. This skill
owns the **mechanics and the "is bloat my problem?" diagnosis**; tuning the **autovacuum daemon's
thresholds and cost limits server-wide is postgres-admin** — cross-linked below.

## Contents

- [MVCC: why dead tuples exist](#mvcc-why-dead-tuples-exist)
- [What VACUUM does](#what-vacuum-does)
- [VACUUM vs VACUUM FULL vs REPACK](#vacuum-vs-vacuum-full-vs-repack)
- [VACUUM options](#vacuum-options)
- [Freezing & transaction-ID wraparound](#freezing--transaction-id-wraparound)
- [Diagnosing bloat & vacuum lag](#diagnosing-bloat--vacuum-lag)
- [Monitoring a running vacuum](#monitoring-a-running-vacuum)
- [Autovacuum (pointer to postgres-admin)](#autovacuum-pointer-to-postgres-admin)

## MVCC: why dead tuples exist

PostgreSQL uses **Multi-Version Concurrency Control**. Each statement sees a **snapshot** of the data
as of some point in time, so readers never block writers and vice-versa. To make that work, the
storage engine **never overwrites a row in place**:

- An **`UPDATE`** writes a **new row version** and marks the old one obsolete.
- A **`DELETE`** marks the row obsolete (it stays on the page).
- Each tuple carries hidden system columns **`xmin`** (the transaction that created this version) and
  **`xmax`** (the transaction that deleted/superseded it). A version is visible to a snapshot if its
  `xmin` is committed-and-visible and its `xmax` is not.

A row version that is no longer visible to **any** running or future transaction is a **dead tuple**.
Dead tuples occupy space until cleaned up. That cleanup is `VACUUM`. (You can see the columns with
`SELECT xmin, xmax, ctid, * FROM t;`.)

**Bloat** = accumulated dead tuples and empty space in tables and indexes. Its symptom is the classic
"the query got slower and slower but the data didn't grow": every scan reads more pages because live
rows are diluted by dead ones.

## What VACUUM does

`VACUUM` (plain) on a table:

1. Scans the table for dead tuples and **marks their space free for reuse** (tracked in the
   **free space map**, FSM) — *within the same table*. It does **not** return space to the OS.
2. Removes dead index entries pointing at those tuples.
3. Updates the **visibility map** (VM): pages where all tuples are visible to everyone are marked
   *all-visible* (enabling **index-only scans** to skip the heap) and *all-frozen*.
4. Updates `pg_class.reltuples`/`relpages` and the table's stats counters.
5. **Freezes** old tuples to prevent transaction-ID wraparound (see below).

It runs **online** — no exclusive lock, concurrent reads and writes continue. This is the routine
maintenance you want, and **autovacuum** does it automatically. A manual run:

```sql
VACUUM (VERBOSE, ANALYZE) orders;   -- reclaim dead space, print a report, refresh planner stats
```

> In PG19 (beta), even ordinary table scans can mark pages all-visible in the VM (previously only
> `VACUUM` and `COPY … FREEZE` could), reducing the lag before index-only scans become effective.

## VACUUM vs VACUUM FULL vs REPACK

| | Lock | Returns space to OS | Rewrites table | Use |
|--|------|:------------------:|:--------------:|-----|
| **`VACUUM`** | none (online) | no (reuse in-table) | no | Routine; what autovacuum runs |
| **`VACUUM FULL`** | **`ACCESS EXCLUSIVE`** (blocks everything) | **yes** | yes (new file) | One-off heavy reclaim after deleting most of a table |
| **`CLUSTER`** | `ACCESS EXCLUSIVE` | yes | yes, **physically ordered by an index** | Reclaim + reorder by index |
| **`REPACK`** *(pg19+, beta)* | optional `CONCURRENTLY` (online) | yes | yes | The new unified, optionally-online rewrite |

- **`VACUUM FULL`** compacts a table by **rewriting it into a brand-new file** with no slack, then
  returning the old file's space to the OS. Because it holds `ACCESS EXCLUSIVE`, **it blocks all
  reads and writes** for the duration — never run it casually on a live table. Needs extra disk
  (a second copy) while running.
- **PG19 deprecates `VACUUM FULL`** in favour of **`REPACK`**, a single command that subsumes
  `VACUUM FULL` and `CLUSTER` (the docs now describe `VACUUM FULL` as "behave like `REPACK` without a
  `USING INDEX` clause"). Crucially, **`REPACK … CONCURRENTLY` (pg19+, beta)** rewrites the table
  **without** the access-exclusive lock (using logical decoding to capture concurrent changes),
  controlled by the new `max_repack_replication_slots` GUC. This is the in-core replacement for the
  external `pg_repack` / `pg_squeeze` tools.
- **On PG18 and earlier**: to reclaim OS space online, use the external **`pg_repack`** extension;
  otherwise schedule `VACUUM FULL`/`CLUSTER` in a maintenance window. **Rebuilding bloated *indexes*
  doesn't need any of this** — use `REINDEX INDEX CONCURRENTLY` (pg12+, see
  [indexes.md](indexes.md#building-and-rebuilding-without-downtime)).

## VACUUM options

`VACUUM [ ( option [, ...] ) ] [ table [ (columns) ] ]`. Key options (with version floors):

| Option | Purpose |
|--------|---------|
| `ANALYZE` | Also refresh planner statistics (= `VACUUM ANALYZE`). |
| `VERBOSE` | Print a per-table activity report at `INFO`. |
| `FREEZE` | Aggressively freeze tuples now (`vacuum_freeze_min_age`/`_table_age` → 0). |
| `FULL` | Rewrite the table (exclusive lock). **Deprecated pg19+** → prefer `REPACK`. |
| `INDEX_CLEANUP { AUTO \| ON \| OFF }` | Whether to vacuum indexes; `AUTO` (pg14+) skips when few dead tuples; `OFF` to finish fast under wraparound pressure. (pg12+) |
| `PARALLEL n` | Vacuum indexes with up to *n* parallel workers (not for `FULL`). (pg13+) |
| `TRUNCATE [bool]` | Truncate trailing empty pages back to the OS (needs a brief exclusive lock). (pg12+) |
| `PROCESS_TOAST [bool]` | Also process the TOAST table (default on). (pg14+) |
| `PROCESS_MAIN [bool]` | Process the main relation (default on; off = TOAST only). (pg16+) |
| `SKIP_LOCKED` | Skip tables that can't be locked immediately. |
| `DISABLE_PAGE_SKIPPING` | Ignore the visibility map (only when the VM is suspected corrupt). |
| `BUFFER_USAGE_LIMIT size` | Cap the vacuum ring-buffer (128kB–16GB); larger = faster but evicts more cache. (pg16+) |
| `SKIP_DATABASE_STATS` / `ONLY_DATABASE_STATS` | Manage the DB-wide oldest-unfrozen-XID stat across many VACUUMs. (pg16+) |

`VACUUM` cannot run inside a transaction block. Requires the `MAINTAIN` privilege (or table ownership).

## Freezing & transaction-ID wraparound

Transaction IDs are 32-bit and **wrap around**. To stop old committed rows from appearing to be "in
the future" after wraparound, VACUUM **freezes** them (marks them as unconditionally visible). If a
database goes too long without vacuuming, it approaches **wraparound** and Postgres will eventually
force aggressive *anti-wraparound* autovacuums (and, at the limit, refuse new write transactions).

You normally never touch this — autovacuum handles it — but it's why **you must not disable
autovacuum** and why a table that's never vacuumed is a latent outage. The `vacuum_failsafe_age` GUC
triggers an emergency fast vacuum (skipping index cleanup) before wraparound. Monitor headroom with:

```sql
SELECT datname, age(datfrozenxid) AS xid_age
FROM pg_database ORDER BY xid_age DESC;   -- compare against autovacuum_freeze_max_age (default 200M)
```

Deep wraparound/freeze tuning (`autovacuum_freeze_max_age`, `vacuum_freeze_*`) is **postgres-admin**.

## Diagnosing bloat & vacuum lag

`pg_stat_user_tables` (and `pg_stat_all_tables`) carry the live/dead counters and vacuum/analyze
timestamps:

```sql
SELECT relname,
       n_live_tup, n_dead_tup,
       round(n_dead_tup * 100.0 / nullif(n_live_tup + n_dead_tup, 0), 1) AS dead_pct,
       n_mod_since_analyze,
       last_autovacuum, last_autoanalyze,
       vacuum_count, autovacuum_count
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 20;
```

Key columns: `n_live_tup` / `n_dead_tup` (estimated live/dead rows), `n_mod_since_analyze` (rows
changed since last `ANALYZE` — drives autoanalyze), `n_ins_since_vacuum` (inserts since vacuum),
`last_vacuum` / `last_autovacuum` / `last_analyze` / `last_autoanalyze`, `vacuum_count` /
`autovacuum_count`. A high `dead_pct` with an old `last_autovacuum` = autovacuum can't keep up
(tune it in postgres-admin) — run a manual `VACUUM (VERBOSE, ANALYZE)` to recover now.

**Cache hit ratio** from `pg_statio_user_tables` (low ratio → undersized cache or bloat forcing reads):

```sql
SELECT relname,
       round(heap_blks_hit * 100.0 / nullif(heap_blks_hit + heap_blks_read, 0), 2) AS heap_hit_pct,
       round(idx_blks_hit  * 100.0 / nullif(idx_blks_hit  + idx_blks_read,  0), 2) AS idx_hit_pct
FROM pg_statio_user_tables
ORDER BY heap_blks_read DESC;
```

For **precise** bloat measurement (vs the estimates above), use the `pgstattuple` extension
(`pgstattuple('tbl')`, `pgstatindex('idx')`) — install it via the **postgres-extensions** skill.

## Monitoring a running vacuum

`pg_stat_progress_vacuum` shows live progress (one row per vacuuming backend, including autovacuum):

```sql
SELECT pid, relid::regclass, phase, mode, started_by,
       heap_blks_scanned, heap_blks_total,
       round(heap_blks_scanned * 100.0 / nullif(heap_blks_total, 0), 1) AS pct,
       index_vacuum_count, dead_tuple_bytes
FROM pg_stat_progress_vacuum;
```

`phase` cycles through `initializing` → `scanning heap` → `vacuuming indexes` → `vacuuming heap` →
`cleaning up indexes` → `truncating heap` → `performing final cleanup`. `mode` is
`normal`/`aggressive`/`failsafe`; `started_by` is `manual`/`autovacuum`/`autovacuum_wraparound`.
(`VACUUM FULL`/`REPACK` rewrites report via `pg_stat_progress_cluster` instead, since they rebuild the
table.) `pg_stat_progress_create_index` does the same for `CREATE INDEX`/`REINDEX`.

## Autovacuum (pointer to postgres-admin)

Autovacuum runs `VACUUM` and `ANALYZE` automatically when dead-tuple / modified-row thresholds are
crossed. The **mechanics above are this skill's scope**; the **tuning is postgres-admin's**:
`autovacuum_vacuum_scale_factor` / `_threshold`, `autovacuum_analyze_scale_factor` / `_threshold`,
`autovacuum_vacuum_cost_limit` / `_cost_delay`, `autovacuum_max_workers`, `autovacuum_naptime`, and
the per-table `ALTER TABLE … SET (autovacuum_…)` overrides. Rule of thumb for performance work: if
`dead_pct` is high and `last_autovacuum` is stale on a busy table, autovacuum is **too lazy for that
table** — lower its per-table scale factor (postgres-admin) and vacuum manually to recover now.
