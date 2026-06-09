---
name: postgres-admin
description: PostgreSQL server administration & operations — DBA work on a running cluster. Use when configuring a server (postgresql.conf, ALTER SYSTEM, reload vs restart, GUCs), managing roles & privileges (CREATE ROLE, GRANT/REVOKE, DEFAULT PRIVILEGES, predefined roles, membership), authentication (pg_hba.conf, scram-sha-256, peer/cert/ldap), backups & restore (pg_dump/pg_dumpall/pg_restore, pg_basebackup, incremental backups, PITR), replication & HA (streaming, logical publications/subscriptions, replication slots, failover, synchronous commit), pg_upgrade, or monitoring (pg_stat_activity, pg_stat_io, pg_stat_progress_*, log settings, checkpoints, connections). Server-side ops — for the psql client use `psql`, for SQL & query syntax `postgres-sql`, for query tuning & autovacuum mechanics `postgres-performance`, for contrib modules `postgres-extensions`. Features added in a release are tagged inline like `(pg16+)`; untagged items are bedrock (PostgreSQL 9.x or earlier). Verify with `SHOW server_version`.
---

# PostgreSQL Administration (DBA / Server Operations)

## Overview

This skill covers **operating a PostgreSQL server**: configuring it, securing access,
backing it up, replicating it, upgrading it, and watching it run. It is about the
**server and cluster**, not about writing application SQL.

**Mental model — the cluster hierarchy:**

```
PostgreSQL instance (one postmaster, one data directory $PGDATA, one port)
└── cluster = all databases managed by that instance
    ├── global objects: roles/users, tablespaces, replication slots  (shared, cluster-wide)
    └── database  →  schema  →  object (table/view/sequence/function)
```

- **One running server** (`postgres`/postmaster) serves **many databases**; roles and
  tablespaces are **cluster-global**, not per-database.
- Configuration lives in **`postgresql.conf`** + **`postgresql.auto.conf`** in `$PGDATA`;
  authentication in **`pg_hba.conf`**; runtime state in the **`pg_stat_*`** views.
- The server is a **long-running daemon**: most admin actions are *reload* (cheap, no
  downtime) or, for a minority of settings, *restart* (brief downtime).
- Write-ahead log (**WAL**) is the foundation of crash recovery, backups (PITR), and
  replication — almost everything operational ties back to it.

## Related skills (disambiguation)

| If you need… | Use skill |
|---|---|
| **Server config, roles/auth, backups, replication, upgrades, monitoring** | **postgres-admin** (this skill) |
| The `psql` client, meta-commands (`\d`, `\dt`), scripting the shell | `psql` |
| SQL syntax, DDL/DML, data types, functions, query writing | `postgres-sql` |
| Query tuning, `EXPLAIN`, indexes, **autovacuum mechanics/tuning** | `postgres-performance` |
| contrib extensions (`pg_stat_statements`, `postgis`, `pgcrypto`, …) | `postgres-extensions` |

> Overlap notes: this skill covers the **server-config / GUC** side of vacuum, checkpoints,
> and WAL (the knobs and what they mean operationally); deep autovacuum/query tuning lives in
> `postgres-performance`. `pg_stat_statements` is a contrib module — monitoring with it is in
> `postgres-extensions`; this skill points you at the built-in `pg_stat_*` views.

## Version awareness

PostgreSQL ships **one major version per year** (pg10 = 2017 … **pg18 = 2025 stable**,
**pg19 = 2026 beta**). This skill tags features added in **PostgreSQL 10 or later** inline as
`(pgNN+)` **only where a release note sources it**; anything from the **9.x era or earlier is
bedrock** and left untagged. Full sourced map: [references/version-features.md](references/version-features.md).

**Check what you're running** (annotations are a hard floor — a `(pg17+)` feature simply does
not exist on pg16):

```bash
psql -c "SHOW server_version"          # e.g. 18.1
psql -c "SELECT version()"             # full build string
postgres --version                     # the server binary
pg_config --version                    # build/devel version
psql -c "SHOW server_version_num"      # 180001 → easy to compare numerically
```

## 1. Server configuration

Settings are **GUCs** (Grand Unified Configuration). Three layers, last-wins:
`postgresql.conf` → `postgresql.auto.conf` (written by `ALTER SYSTEM`) → per-session `SET`.

```sql
SHOW shared_buffers;                       -- one setting
SHOW all;                                  -- everything
SELECT name, setting, unit, context, pending_restart
  FROM pg_settings WHERE name = 'work_mem';
SELECT name, setting, source, sourcefile, sourceline   -- where did this value come from?
  FROM pg_settings WHERE source NOT IN ('default','override');

ALTER SYSTEM SET work_mem = '64MB';        -- persists to postgresql.auto.conf (since 9.4)
ALTER SYSTEM RESET work_mem;               -- remove the override
SELECT pg_reload_conf();                   -- apply reload-able changes, no downtime
SET work_mem = '128MB';                    -- this session only
RESET work_mem;                            -- back to the configured value
```

```bash
pg_ctl reload   -D $PGDATA     # SIGHUP — apply reloadable settings (also: systemctl reload)
pg_ctl restart  -D $PGDATA     # required for some settings (see below)
```

**Reload vs restart** — a setting's `context` in `pg_settings` tells you:

| `context` | How to apply | Examples |
|---|---|---|
| `user` / `superuser` | `SET` in-session, or reload | `work_mem`, `statement_timeout` |
| `sighup` | **reload** (`pg_reload_conf()`) | `log_*`, `autovacuum`, `archive_command`, `checkpoint_timeout`, `max_wal_size` |
| `postmaster` | **restart** | `shared_buffers`, `max_connections`, `listen_addresses`, `port`, `wal_level`, `shared_preload_libraries` |

After editing, `pending_restart = true` in `pg_settings` flags settings that need a restart.
`ALTER SYSTEM` **cannot** set a few bootstrap params (e.g. it warns on settings that have no
effect post-start). Full GUC tour, key parameters, and units: [references/config.md](references/config.md).

## 2. Roles & privileges

Roles are **cluster-global**. A "user" is just a role `WITH LOGIN`.

```sql
CREATE ROLE app LOGIN PASSWORD 'secret';                 -- a login user
CREATE ROLE readonly NOLOGIN;                            -- a group role
CREATE ROLE deployer LOGIN CREATEDB CREATEROLE;
ALTER ROLE app VALID UNTIL '2027-01-01' CONNECTION LIMIT 20;
ALTER ROLE app SET search_path = app, public;            -- per-role GUC default

GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly; -- existing tables only
ALTER DEFAULT PRIVILEGES IN SCHEMA public                -- future tables too
  GRANT SELECT ON TABLES TO readonly;
GRANT readonly TO app;                                   -- role membership

REVOKE INSERT ON orders FROM app;
```

- **Privileges don't apply retroactively** — `GRANT … ON ALL TABLES` covers tables that exist
  *now*; use `ALTER DEFAULT PRIVILEGES` for objects created *later* (and it's per-creator).
- **`public` schema hardening (pg15+):** new clusters **no longer grant `CREATE` on `public`
  to `PUBLIC`** (CVE-2018-1058 mitigation). On upgraded clusters, consider
  `REVOKE CREATE ON SCHEMA public FROM PUBLIC` yourself.
- **Predefined roles** grant capabilities without superuser: `pg_monitor`,
  `pg_read_all_settings`, `pg_read_all_stats`, `pg_signal_backend`, `pg_read_all_data` /
  `pg_write_all_data` (pg14+), `pg_database_owner` (pg14+), `pg_checkpoint` (pg15+),
  `pg_use_reserved_connections` (pg16+), `pg_create_subscription` (pg16+), `pg_maintain`
  (pg17+, with the `MAINTAIN` privilege), `pg_signal_autovacuum_worker` (pg18+).
- **Role membership options (pg16+):** `GRANT g TO u WITH INHERIT {TRUE|FALSE}, SET
  {TRUE|FALSE}, ADMIN {TRUE|FALSE}` — membership inheritance is now per-grant, not just the
  member's `INHERIT` attribute. (Pre-16, new memberships always inherited per the member role.)

Full role attribute / GRANT / object-privilege reference: [references/auth-roles.md](references/auth-roles.md).

## 3. Authentication (`pg_hba.conf`)

`pg_hba.conf` is matched **top-to-bottom, first match wins** (no fall-through). Format:

```
# TYPE   DATABASE  USER       ADDRESS            METHOD
local    all       all                           peer            # Unix socket, OS-user match
host     all       all        127.0.0.1/32       scram-sha-256    # TCP, localhost
hostssl  app       app        10.0.0.0/8         scram-sha-256    # require TLS
host     all       all        0.0.0.0/0          reject           # deny the rest
```

```bash
psql -c "SELECT pg_reload_conf()"          # pg_hba changes apply on RELOAD, not restart
psql -c "TABLE pg_hba_file_rules"          # see parsed rules + any errors (pg10+)
psql -c "TABLE pg_ident_file_mappings"     # parsed pg_ident.conf (pg15+)
```

- **Methods:** `scram-sha-256` (pg10+, the modern default — set `password_encryption =
  scram-sha-256`, the **default since pg14**), `md5` (legacy, **deprecated pg18+**), `peer`
  (local OS user), `cert` (TLS client cert), `ldap`, `gss`/`sspi`, `radius`, `trust` (no
  auth — dev only), `reject`, and `oauth` (pg18+). `pg_ident.conf` maps OS/external names to
  DB roles for `peer`/`cert`/`gss`/`ldap`.
- Order matters: put **specific rules above general ones**. A leading `trust` line shadows
  everything below it.

Methods, TLS setup, and `pg_ident.conf` mapping: [references/auth-roles.md](references/auth-roles.md).

## 4. Backup & recovery

Two families: **logical** (SQL/dump, portable, per-DB) and **physical** (file/block-level,
whole cluster, enables PITR).

```bash
# Logical — pg_dump (one database). Custom/dir formats are compressed + allow selective,
# parallel restore; plain text is a .sql script.
pg_dump -Fc -f app.dump app                 # custom format (restore with pg_restore)
pg_dump -Fd -j4 -f app_dir app              # directory format, 4 parallel workers
pg_dump --section=pre-data -f schema.sql app
pg_restore -d app -j4 app.dump              # parallel restore
pg_dump -t orders -t 'audit_*' app          # selected tables
pg_dumpall --globals-only > globals.sql     # roles + tablespaces (NOT in pg_dump)
pg_dumpall -f whole_cluster.sql             # every DB + globals (text; non-text formats pg19+)

# Physical — pg_basebackup (whole cluster, byte-exact; basis for replicas & PITR)
pg_basebackup -D /backup/base -Ft -z -P     # tar + gzip, with progress
pg_basebackup -D /backup/base -X stream -c fast   # include WAL via a 2nd stream

# Incremental backup (pg17+) — needs summarize_wal=on; combine to restore
pg_basebackup -D /backup/incr --incremental=/backup/base/backup_manifest
pg_combinebackup /backup/base /backup/incr -o /restore/full   # (pg17+)

# Verify (pg13+): manifests are written automatically by pg_basebackup
pg_verifybackup /backup/base
```

**Point-in-time recovery (PITR):** restore a base backup, then provide a `restore_command`
and a `recovery_target_*`, drop a `recovery.signal` file, and start the server. The old
`recovery.conf` was **removed in pg12** — recovery settings now live in `postgresql.conf` with
`standby.signal` / `recovery.signal` controlling the mode. Full PITR + upgrade procedures:
[references/backup-recovery.md](references/backup-recovery.md).

## 5. WAL & replication

```sql
SHOW wal_level;            -- minimal | replica (default) | logical
SHOW synchronous_commit;   -- on | remote_apply | remote_write | local | off
SELECT * FROM pg_stat_replication;          -- on the primary: connected standbys + lag
SELECT * FROM pg_replication_slots;         -- slots (prevent WAL removal until consumed)
SELECT pg_create_physical_replication_slot('standby1');
```

**Physical / streaming replication** (whole-cluster, binary): a standby connects via
`primary_conninfo`, replays WAL, optionally serves read-only queries (hot standby). Set up
the standby from `pg_basebackup -R` (writes `primary_conninfo` + `standby.signal`).

**Logical replication (pg10+)** — selective, table-level, cross-version, via publish/subscribe:

```sql
-- on the publisher (needs wal_level = logical)
CREATE PUBLICATION pub FOR TABLE orders, customers;
CREATE PUBLICATION pub2 FOR TABLES IN SCHEMA sales;             -- (pg15+)
CREATE PUBLICATION pub3 FOR TABLE orders (id, total) WHERE (total > 0);  -- column list + row filter (pg15+)

-- on the subscriber
CREATE SUBSCRIPTION sub CONNECTION 'host=pub dbname=app' PUBLICATION pub;
```

- **Replication slots** guarantee the primary keeps WAL until a consumer has it — an
  abandoned slot can **fill the disk**; monitor and drop stale slots.
- **Synchronous replication:** list standbys in `synchronous_standby_names`;
  `synchronous_commit` controls the durability/latency trade-off.
- **Failover slot sync (pg17+):** `sync_replication_slots = on` plus `synchronized_standby_slots`
  let logical slots survive a failover to a physical standby (so subscribers don't break).
- **`pg_createsubscriber` (pg17+)** converts a physical standby into a logical subscriber;
  **`effective_wal_level` (pg19+)** auto-raises the effective WAL level for logical use.

Streaming setup, slots, logical replication, conflicts, and HA: [references/replication.md](references/replication.md).

## 6. Major-version upgrades (`pg_upgrade`)

```bash
# Run as the OS owner, both clusters stopped. --check first (read-only validation).
pg_upgrade --old-datadir=/data/17 --new-datadir=/data/18 \
           --old-bindir=/usr/lib/postgresql/17/bin \
           --new-bindir=/usr/lib/postgresql/18/bin --check
pg_upgrade … --link        # hard-link files: fast, but old cluster becomes unusable
pg_upgrade … --clone       # CoW clone (where the FS supports it)
pg_upgrade … --swap        # (pg18+) swap data dirs — often the fastest
```

`--link`/`--clone`/`--copy`/`--swap` trade speed vs. keeping the old cluster recoverable.
Always have a **backup** and run `--check` first. Minor upgrades (e.g. 18.1→18.2) are just a
binary swap + restart — no `pg_upgrade`. Details: [references/backup-recovery.md](references/backup-recovery.md).

## 7. Monitoring & observability

```sql
-- Who's connected / what's running (kill runaway queries here)
SELECT pid, usename, state, wait_event_type, wait_event,
       now() - query_start AS runtime, left(query,60) AS query
  FROM pg_stat_activity WHERE state <> 'idle' ORDER BY runtime DESC;
SELECT pg_cancel_backend(pid);     -- cancel current query (gentle)
SELECT pg_terminate_backend(pid);  -- drop the whole connection (forceful)

-- Per-database health: commits/rollbacks, cache hit ratio, deadlocks, conflicts
SELECT datname, xact_commit, xact_rollback, blks_hit, blks_read, deadlocks
  FROM pg_stat_database WHERE datname IS NOT NULL;

-- I/O by backend type / object (pg16+): reads, writes, hits, evictions
SELECT backend_type, object, context, reads, writes, hits FROM pg_stat_io;

-- Long-running maintenance progress
SELECT * FROM pg_stat_progress_vacuum;       -- VACUUM (bedrock)
SELECT * FROM pg_stat_progress_basebackup;   -- base backup (pg13+)
SELECT * FROM pg_stat_progress_copy;         -- COPY (pg14+)

-- Replication lag (primary side) and WAL receiver (standby side)
SELECT application_name, state, sent_lsn, replay_lsn,
       write_lag, flush_lag, replay_lag FROM pg_stat_replication;
```

- **`pg_stat_activity`** is your live console: states, `wait_event`, and the cancel/terminate
  functions. **`pg_stat_database`** gives per-DB throughput and a cache-hit ratio
  (`blks_hit / (blks_hit + blks_read)`). **`pg_stat_io` (pg16+)** breaks I/O down by source.
- **Progress views:** `vacuum` (bedrock), `create_index`/`cluster` (pg12+), `analyze` &
  `basebackup` (pg13+), `copy` (pg14+).
- **Logging:** `log_destination`, `logging_collector`, `log_min_duration_statement` (log slow
  queries), `log_connections`/`log_disconnections`, `log_checkpoints` (on by default since
  pg15), `log_lock_waits` (on by default pg19+). All `log_*` are `sighup` → reload.
- **Checkpoints:** tune with `checkpoint_timeout`, `max_wal_size`, `checkpoint_completion_target`;
  watch `log_checkpoints` output / `pg_stat_checkpointer` (pg17+) for too-frequent checkpoints.
- **Connections:** `max_connections` is a **restart** setting; the practical fix for "too many
  clients" is a **pooler** (PgBouncer / pgcat / built-in pooling in clients) rather than ever
  raising `max_connections` unbounded. `superuser_reserved_connections` (and
  `reserved_connections` + `pg_use_reserved_connections`, pg16+) keep headroom for admins.

Views, columns, logging knobs, and a monitoring playbook: [references/monitoring.md](references/monitoring.md).

## Quick reference

| Task | Command / query |
|---|---|
| Show / change a setting | `SHOW x;` · `ALTER SYSTEM SET x = v;` then `SELECT pg_reload_conf();` |
| Does a change need restart? | `SELECT name,context,pending_restart FROM pg_settings WHERE name='x';` |
| Reload vs restart | `pg_ctl reload -D $PGDATA` · `pg_ctl restart -D $PGDATA` |
| Create login user / group | `CREATE ROLE u LOGIN PASSWORD '…';` · `CREATE ROLE g NOLOGIN;` |
| Grant on future objects | `ALTER DEFAULT PRIVILEGES IN SCHEMA s GRANT … TO r;` |
| Inspect parsed HBA rules | `TABLE pg_hba_file_rules;` (pg10+) |
| Logical dump / restore | `pg_dump -Fc -f a.dump db` · `pg_restore -d db -j4 a.dump` |
| Dump roles + tablespaces | `pg_dumpall --globals-only` |
| Physical base backup | `pg_basebackup -D dir -Ft -z -X stream -P` |
| Incremental backup (pg17+) | `pg_basebackup --incremental=…/backup_manifest` + `pg_combinebackup` |
| Verify a backup (pg13+) | `pg_verifybackup /backup/base` |
| Replication status | `TABLE pg_stat_replication;` · `TABLE pg_replication_slots;` |
| Create publication / subscription | `CREATE PUBLICATION p FOR TABLE t;` · `CREATE SUBSCRIPTION s …;` |
| Live queries / kill one | `TABLE pg_stat_activity;` · `SELECT pg_terminate_backend(pid);` |
| I/O stats (pg16+) | `TABLE pg_stat_io;` |
| Upgrade major version | `pg_upgrade --old-* --new-* --check` then without `--check` |
| Current version | `SHOW server_version;` · `SHOW server_version_num;` |

## Troubleshooting

- **"FATAL: sorry, too many clients already"** — at `max_connections`. Don't reflexively raise
  it (each connection costs memory + a process); add a **connection pooler**. Check current use:
  `SELECT count(*), state FROM pg_stat_activity GROUP BY state;`
- **Config change "didn't take"** — it's probably a `postmaster`-context setting needing a
  **restart**, or you reloaded but the value is overridden in `postgresql.auto.conf`. Check
  `SELECT name,setting,source,pending_restart FROM pg_settings WHERE name='…';`.
- **Can't connect / "no pg_hba.conf entry"** — a rule is missing or a broader rule above it
  matched first (and `reject`ed). Inspect `TABLE pg_hba_file_rules;` and remember **first match
  wins**. After editing, **reload** (not restart).
- **Password auth fails after enabling SCRAM** — passwords stored under `md5` aren't usable by
  `scram-sha-256` rules. Set `password_encryption = scram-sha-256` and have users **reset their
  password** so it's re-hashed.
- **Disk filling up / WAL won't recycle** — usually an **inactive replication slot** or a
  failing `archive_command`. Check `SELECT slot_name, active, wal_status FROM
  pg_replication_slots;` and drop abandoned slots with `pg_drop_replication_slot('…')`.
- **Standby falling behind** — inspect `write_lag`/`flush_lag`/`replay_lag` in
  `pg_stat_replication`; a long-running query on the standby can pause replay (see
  `hot_standby_feedback` / `max_standby_streaming_delay`).
- **`pg_dump` ≠ full backup** — it does **not** capture roles, tablespaces, or other databases.
  Pair it with `pg_dumpall --globals-only`, or use physical backups for whole-cluster DR.
- **A feature errors as unknown syntax / missing view** — your server may predate it. Check
  `SHOW server_version` against [references/version-features.md](references/version-features.md)
  (e.g. `pg_stat_io` needs pg16, `--incremental` needs pg17).

## References

- [references/config.md](references/config.md) — GUCs in depth: the three config layers,
  `ALTER SYSTEM`, reload vs restart by `context`, key memory/WAL/checkpoint/connection/logging
  parameters with units, and `include` directives.
- [references/auth-roles.md](references/auth-roles.md) — roles & attributes, `GRANT`/`REVOKE`,
  object privileges, `DEFAULT PRIVILEGES`, predefined roles, role membership (pg16+ options),
  and authentication: `pg_hba.conf` methods, SCRAM, TLS, `pg_ident.conf`.
- [references/backup-recovery.md](references/backup-recovery.md) — logical (`pg_dump`/
  `pg_dumpall`/`pg_restore`) and physical (`pg_basebackup`, incremental + `pg_combinebackup`,
  manifests + `pg_verifybackup`), continuous archiving, PITR, and `pg_upgrade`.
- [references/replication.md](references/replication.md) — WAL, streaming/physical replication,
  replication slots, hot standby, synchronous commit, logical replication (publications/
  subscriptions, row filters, column lists), failover slot sync, `pg_createsubscriber`.
- [references/monitoring.md](references/monitoring.md) — the `pg_stat_*` views, `pg_stat_io`,
  progress views, replication monitoring, logging settings, checkpoint tuning, and a
  triage playbook.
- [references/version-features.md](references/version-features.md) — sourced
  feature → minimum-PostgreSQL-version map (pg10 → pg19), with how-to-read notes and citations.

## Resources

- **Official docs:** https://www.postgresql.org/docs/current/
- **Server admin:** https://www.postgresql.org/docs/current/admin.html
- **Config (GUCs):** https://www.postgresql.org/docs/current/runtime-config.html
- **Client auth:** https://www.postgresql.org/docs/current/client-authentication.html
- **Backup & restore:** https://www.postgresql.org/docs/current/backup.html
- **High availability:** https://www.postgresql.org/docs/current/high-availability.html
- **Monitoring:** https://www.postgresql.org/docs/current/monitoring-stats.html
