# Monitoring & Observability

The built-in statistics views, logging knobs, and a triage playbook for a running server.
Version tags `(pgNN+)` mark features added in PostgreSQL 10+; untagged items are bedrock
(9.x or earlier). For `pg_stat_statements` (query-level stats), see `postgres-extensions`.

## Contents

- [pg_stat_activity (live sessions)](#pg_stat_activity-live-sessions)
- [Cancel & terminate backends](#cancel--terminate-backends)
- [pg_stat_database (per-database)](#pg_stat_database-per-database)
- [pg_stat_io (pg16+)](#pg_stat_io-pg16)
- [Table/index stats & bloat signals](#tableindex-stats--bloat-signals)
- [Progress-reporting views](#progress-reporting-views)
- [Replication monitoring](#replication-monitoring)
- [Checkpoints, WAL & bgwriter](#checkpoints-wal--bgwriter)
- [Locks](#locks)
- [Logging settings](#logging-settings)
- [Resetting statistics](#resetting-statistics)
- [Triage playbook](#triage-playbook)
- [What's new for monitoring in pg19](#whats-new-for-monitoring-in-pg19)

## pg_stat_activity (live sessions)

The single most useful operational view — one row per server process.

```sql
SELECT pid, usename, datname, application_name, client_addr,
       state, wait_event_type, wait_event,
       now() - xact_start  AS xact_age,
       now() - query_start AS query_age,
       left(query, 80)     AS query
  FROM pg_stat_activity
 WHERE state <> 'idle'
 ORDER BY query_age DESC NULLS LAST;
```

- `state`: `active`, `idle`, `idle in transaction`, `idle in transaction (aborted)`,
  `fastpath function call`. **`idle in transaction`** sessions hold locks and pin the xmin
  horizon — hunt them down (and set `idle_in_transaction_session_timeout`).
- `wait_event_type` / `wait_event` tell you *why* a backend is blocked (Lock, IO, LWLock,
  Client, …) — the basis of wait-event analysis.
- `backend_type` distinguishes client backends from `autovacuum worker`, `walwriter`,
  `checkpointer`, `logical replication worker`, etc.

## Cancel & terminate backends

```sql
SELECT pg_cancel_backend(pid);      -- cancel the current query, keep the connection
SELECT pg_terminate_backend(pid);   -- close the whole connection (rolls back its txn)
-- Kill sessions idle-in-transaction longer than 10 min:
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
 WHERE state = 'idle in transaction' AND now() - state_change > interval '10 min';
```

`pg_cancel_backend` is the gentle option; `pg_terminate_backend` is forceful. Non-superusers
can signal their own backends, or any backend if they have `pg_signal_backend`.

## pg_stat_database (per-database)

```sql
SELECT datname, numbackends, xact_commit, xact_rollback,
       blks_read, blks_hit,
       round(100.0*blks_hit/nullif(blks_hit+blks_read,0), 2) AS cache_hit_pct,
       tup_returned, tup_fetched, deadlocks, temp_files, temp_bytes,
       conflicts, stats_reset
  FROM pg_stat_database
 WHERE datname IS NOT NULL;
```

Watch: **cache hit ratio** (want high-90s%), `deadlocks` climbing, `temp_files`/`temp_bytes`
(work_mem spilling to disk), `xact_rollback` vs `xact_commit`, and `conflicts` (recovery
conflicts on standbys; details in `pg_stat_database_conflicts`).

## pg_stat_io (pg16+)

I/O broken down by **backend type × object × context** — pinpoints *who* does I/O and whether
it's hitting cache, evicting buffers, or extending files.

```sql
SELECT backend_type, object, context,
       reads, writes, extends, hits, evictions,
       read_bytes, write_bytes          -- *_bytes columns (pg18+)
  FROM pg_stat_io
 WHERE reads > 0 OR writes > 0
 ORDER BY reads + writes DESC;
```

- `context`: `normal`, `vacuum`, `bulkread`, `bulkwrite` — e.g. high `evictions` in `normal`
  context suggests `shared_buffers` pressure.
- pg18+ added `read_bytes`/`write_bytes`/`extend_bytes` and WAL rows (and removed `op_bytes`).
- pg17 moved `buffers_backend` / `buffers_backend_fsync` out of `pg_stat_bgwriter` into here.

## Table/index stats & bloat signals

```sql
-- Tables needing attention: dead tuples & last (auto)vacuum
SELECT relname, n_live_tup, n_dead_tup,
       round(100.0*n_dead_tup/nullif(n_live_tup+n_dead_tup,0),1) AS dead_pct,
       last_vacuum, last_autovacuum, last_analyze, last_autoanalyze
  FROM pg_stat_user_tables
 ORDER BY n_dead_tup DESC LIMIT 20;

-- Sequential vs index scans (candidates for indexing)
SELECT relname, seq_scan, idx_scan, n_live_tup
  FROM pg_stat_user_tables ORDER BY seq_scan DESC LIMIT 20;

-- Unused indexes (idx_scan = 0)
SELECT relname AS table, indexrelname AS index, idx_scan,
       pg_size_pretty(pg_relation_size(indexrelid)) AS size
  FROM pg_stat_user_indexes WHERE idx_scan = 0 ORDER BY pg_relation_size(indexrelid) DESC;
```

These point at *what* to investigate; the **why/how of vacuum and index tuning lives in
`postgres-performance`**. From an ops angle, watch `n_dead_tup` and `last_autovacuum` to spot
tables autovacuum isn't keeping up with.

## Progress-reporting views

Live progress of long-running maintenance commands:

| View | Tracks | Since |
|---|---|---|
| `pg_stat_progress_vacuum` | VACUUM | bedrock (9.6) |
| `pg_stat_progress_create_index` | CREATE INDEX / REINDEX | pg12+ |
| `pg_stat_progress_cluster` | CLUSTER / VACUUM FULL | pg12+ |
| `pg_stat_progress_analyze` | ANALYZE | pg13+ |
| `pg_stat_progress_basebackup` | base backups (`pg_basebackup`) | pg13+ |
| `pg_stat_progress_copy` | COPY | pg14+ |
| `pg_stat_progress_repack` | REPACK | pg19+ |

```sql
SELECT pid, phase, heap_blks_total, heap_blks_scanned, heap_blks_vacuumed
  FROM pg_stat_progress_vacuum;
```

## Replication monitoring

```sql
-- PRIMARY: connected standbys + lag (bytes and time)
SELECT application_name, state, sync_state,
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS replay_lag_bytes,
       write_lag, flush_lag, replay_lag
  FROM pg_stat_replication;

-- STANDBY: WAL receiver health
SELECT status, sender_host, slot_name, latest_end_lsn, latest_end_time
  FROM pg_stat_wal_receiver;

-- Slots (watch for inactive slots retaining WAL)
SELECT slot_name, slot_type, active, wal_status, safe_wal_size,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained
  FROM pg_replication_slots;

-- Logical subscription side
SELECT * FROM pg_stat_subscription;
SELECT * FROM pg_stat_subscription_stats;     -- apply/sync error counts
```

`write_lag`/`flush_lag`/`replay_lag` are time intervals — far easier to reason about than raw
LSNs for alerting.

## Checkpoints, WAL & bgwriter

```sql
-- pg17+: checkpoint stats live in their own view
SELECT num_timed, num_requested, write_time, sync_time, buffers_written, stats_reset
  FROM pg_stat_checkpointer;                  -- (pg17+)
SELECT * FROM pg_stat_bgwriter;               -- background writer (checkpoint cols moved out in pg17)
SELECT * FROM pg_stat_wal;                    -- WAL generation volume (pg14+)
```

- **Too-frequent checkpoints** (high `num_requested` relative to `num_timed`) → raise
  `max_wal_size` and/or `checkpoint_timeout`; enable `log_checkpoints` (on by default pg15+)
  to see timing.
- Pre-pg17 these counters were columns in `pg_stat_bgwriter`
  (`checkpoints_timed`/`checkpoints_req`/`buffers_checkpoint`/…) — monitoring queries broke on
  the pg17 split; adjust them to `pg_stat_checkpointer`.

## Locks

```sql
-- Blocking tree: who is waiting on whom
SELECT blocked.pid AS blocked_pid, blocked_act.query AS blocked_query,
       blocking.pid AS blocking_pid, blocking_act.query AS blocking_query
  FROM pg_locks blocked
  JOIN pg_stat_activity blocked_act ON blocked_act.pid = blocked.pid
  JOIN pg_locks blocking
    ON blocking.locktype = blocked.locktype
   AND blocking.database IS NOT DISTINCT FROM blocked.database
   AND blocking.relation IS NOT DISTINCT FROM blocked.relation
   AND blocking.pid <> blocked.pid AND blocking.granted
  JOIN pg_stat_activity blocking_act ON blocking_act.pid = blocking.pid
 WHERE NOT blocked.granted;

-- Simpler, since pg9.6:
SELECT pid, pg_blocking_pids(pid) AS blocked_by, wait_event, left(query,60)
  FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0;
```

Enable `log_lock_waits` (on by default pg19+) to log sessions that wait past
`deadlock_timeout`.

## Logging settings

| Parameter | Purpose | Default note |
|---|---|---|
| `log_destination` | `stderr`/`csvlog`/`jsonlog` (pg15+)/`syslog` | |
| `logging_collector` | write stderr to rotating files (restart) | |
| `log_min_duration_statement` | log statements slower than N ms (`0` = all) | great slow-query log |
| `log_line_prefix` | per-line metadata; `'%m [%p] %q%u@%d '` | |
| `log_connections` / `log_disconnections` | session lifecycle | pg18+: `log_connections` is multi-valued |
| `log_checkpoints` | one line per checkpoint | **on** since pg15 |
| `log_lock_waits` | log long lock waits | **on** pg19+ |
| `log_temp_files` | log temp files over N kB (work_mem spills) | |
| `log_autovacuum_min_duration` | log autovacuum actions over N ms | |
| `log_statement` | `none`/`ddl`/`mod`/`all` | audit DDL/writes |

All `log_*` are `sighup` (reload). pg19+ lets `log_min_messages` be set **per process type**.

## Resetting statistics

```sql
SELECT pg_stat_reset();                          -- this database's table/index/function stats
SELECT pg_stat_reset_shared('bgwriter');         -- shared counters: bgwriter
SELECT pg_stat_reset_shared('checkpointer');     -- (pg17+)
SELECT pg_stat_reset_shared('io');               -- pg_stat_io (pg16+)
SELECT pg_stat_reset_single_table_counters('orders'::regclass);
```

## Triage playbook

| Symptom | First look |
|---|---|
| "too many clients" | `SELECT state, count(*) FROM pg_stat_activity GROUP BY state;` → add a pooler |
| Slow right now | `pg_stat_activity` ordered by `query_age`; check `wait_event` |
| Something is blocked | `pg_blocking_pids()` / the blocking-tree query |
| Disk filling | inactive slots (`pg_replication_slots`), failing `archive_command`, bloat, temp files |
| Standby lagging | `write_lag`/`flush_lag`/`replay_lag`; long standby query? `hot_standby_feedback` |
| High I/O | `pg_stat_io` by `backend_type`/`context`; checkpoint frequency |
| Cache misses | `pg_stat_database` cache-hit %; `shared_buffers` sizing |
| Bloat / vacuum behind | `pg_stat_user_tables` `n_dead_tup` + `last_autovacuum` (tune in `postgres-performance`) |

## What's new for monitoring in pg19

The 19beta1 tree adds several views/columns (verify on your build): `pg_stat_recovery`
(recovery status), `pg_stat_lock` + `pg_stat_get_lock()` (per-lock-type stats),
`pg_stat_autovacuum_scores` (per-table autovacuum scoring), `pg_stat_progress_repack`,
`pg_stat_wal.wal_fpi_bytes`, and `slotsync_skip_reason` on `pg_replication_slots`. A column in
`pg_stat_subscription_stats` was renamed (`sync_error_count` → `sync_table_error_count`).
