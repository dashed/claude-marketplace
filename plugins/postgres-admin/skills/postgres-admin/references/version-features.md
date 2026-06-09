# PostgreSQL Admin Feature → Minimum Version

A consolidated lookup of **which PostgreSQL major version introduced an administration
feature** this skill documents — server config/GUCs, roles & auth, backup/restore,
replication, monitoring, and the bundled CLI tools — so you know what works on an older (or
newer) server. Use it to answer "is my server new enough for X?" and "what do I need to
upgrade to?"

**How to read this:**

- These are **PostgreSQL major versions**. PostgreSQL ships **one major per year**
  (pg10 = Oct 2017, … **pg18 = Sep 2025 (current stable)**, **pg19 = 2026 (beta)**). A minor
  release (e.g. 18.1 → 18.2) never adds features — only fixes.
- The `(pgNN+)` form means "PostgreSQL NN and later." Each row is the **earliest major version
  in which the feature is documented as available**, taken from the official **postgresql.org
  release notes** (the per-version `release-NN` pages). **No version is guessed:** a feature
  with no clean "added in pgNN" source is treated as long-standing and left out.
- **Bedrock = PostgreSQL 9.x or earlier** (the 9.0–9.6 line and before). Anything bedrock is
  **left untagged** in the skill — it has been present for so long you can assume it. This
  includes: `postgresql.conf` + `SET`/`SHOW`/`RESET`/`pg_settings`, `ALTER SYSTEM` +
  `postgresql.auto.conf` (since **9.4**), `pg_ctl reload`/`restart`, `CREATE/ALTER ROLE`,
  `GRANT`/`REVOKE` + object privileges, `ALTER DEFAULT PRIVILEGES`, `pg_hba.conf` with
  `trust`/`peer`/`ident`/`md5`/`password`/`cert`/`ldap`/`gss`/`radius`, `pg_ident.conf`,
  `pg_dump`/`pg_dumpall`/`pg_restore` (all formats, `-j` parallel, `--section`), `pg_basebackup`,
  continuous archiving + PITR (`restore_command`, `recovery_target_*`), streaming replication
  (9.0), replication slots (9.4), `synchronous_standby_names` priority lists (9.1),
  `pg_stat_activity`/`pg_stat_database`/`pg_stat_replication`/`pg_stat_user_tables`,
  `pg_stat_progress_vacuum` (9.6), `pg_cancel_backend`/`pg_terminate_backend`,
  `pg_signal_backend` role (9.6), `checkpoint_timeout`/`max_wal_size` (9.5), `max_connections`,
  and `pg_upgrade` with `--link`/`--clone`/`--copy`.
- Rows marked **(breaking)** changed existing behavior or moved/renamed something — review the
  release notes before relying on or upgrading into them. Rows marked **(default)** changed a
  default value.
- This skill's source of truth for *existence* is the in-repo dev tree **19beta1**; *version
  pinning* is from the postgresql.org release notes. Always confirm on the running server — see
  [Checking your version](#checking-your-version).

Release-notes sources, one per major line:

- pg10 (2017-10-05) — <https://www.postgresql.org/docs/10/release-10.html>
- pg11 (2018-10-18) — <https://www.postgresql.org/docs/11/release-11.html>
- pg12 (2019-10-03) — <https://www.postgresql.org/docs/12/release-12.html>
- pg13 (2020-09-24) — <https://www.postgresql.org/docs/13/release-13.html>
- pg14 (2021-09-30) — <https://www.postgresql.org/docs/14/release-14.html>
- pg15 (2022-10-13) — <https://www.postgresql.org/docs/15/release-15.html>
- pg16 (2023-09-14) — <https://www.postgresql.org/docs/16/release-16.html>
- pg17 (2024-09-26) — <https://www.postgresql.org/docs/17/release-17.html>
- pg18 (2025-09-25) — <https://www.postgresql.org/docs/18/release-18.html>
- pg19 (beta, 2026) — `doc/src/sgml/release-19.sgml` in the dev tree

## Contents

- [Versioned features (ascending by PostgreSQL release)](#versioned-features-ascending-by-postgresql-release)
- [Checking your version](#checking-your-version)

## Versioned features (ascending by PostgreSQL release)

Sorted ascending by minimum version; within a version, grouped by **Area** (Config / Roles &
Auth / Backup / Replication / Monitoring / Tooling).

| Min version | Feature | Area |
|---|---|---|
| pg10+ | `scram-sha-256` password authentication method (and `password_encryption` becomes an enum) | Roles & Auth |
| pg10+ | `pg_monitor`, `pg_read_all_settings`, `pg_read_all_stats`, `pg_stat_scan_tables` predefined roles | Roles & Auth |
| pg10+ | Logical replication: `CREATE PUBLICATION` / `CREATE SUBSCRIPTION` (publish/subscribe) | Replication |
| pg10+ | Quorum synchronous replication — `ANY n (…)` in `synchronous_standby_names` | Replication |
| pg10+ | `pg_hba_file_rules` view (parsed HBA rules + errors) | Roles & Auth |
| pg10+ | `pg_xlog`→`pg_wal`, `pg_clog`→`pg_xact`, and `xlog`→`wal` in functions/tools (`pg_receivexlog`→`pg_receivewal`, `pg_switch_xlog`→`pg_switch_wal`) *(breaking)* | Tooling |
| pg11+ | `pg_read_server_files`, `pg_write_server_files`, `pg_execute_server_program` predefined roles | Roles & Auth |
| pg12+ | `recovery.conf` removed → recovery settings in `postgresql.conf`, with `standby.signal` / `recovery.signal` files *(breaking)* | Replication |
| pg12+ | `pg_stat_progress_create_index` (CREATE INDEX / REINDEX) | Monitoring |
| pg12+ | `pg_stat_progress_cluster` (CLUSTER / VACUUM FULL) | Monitoring |
| pg12+ | Some recovery params changeable by reload (`restore_command` etc.) | Replication |
| pg13+ | Backup manifests written by `pg_basebackup` | Backup |
| pg13+ | `pg_verifybackup` utility | Backup |
| pg13+ | `wal_keep_segments` renamed to `wal_keep_size` (size-based) *(breaking)* | Config |
| pg13+ | `pg_stat_progress_basebackup` view | Monitoring |
| pg13+ | `pg_stat_progress_analyze` view | Monitoring |
| pg13+ | Logical replication of partitioned tables (publish the parent) | Replication |
| pg14+ | `scram-sha-256` becomes the **default** `password_encryption` (was `md5`) *(default)* | Roles & Auth |
| pg14+ | `pg_read_all_data` / `pg_write_all_data` predefined roles | Roles & Auth |
| pg14+ | `pg_database_owner` predefined role | Roles & Auth |
| pg14+ | `pg_stat_wal` view (WAL generation stats) | Monitoring |
| pg14+ | `pg_stat_progress_copy` view | Monitoring |
| pg15+ | Logical replication **row filters** — `WHERE (…)` on publication tables | Replication |
| pg15+ | Logical replication **column lists** on publications | Replication |
| pg15+ | `CREATE PUBLICATION … FOR TABLES IN SCHEMA` | Replication |
| pg15+ | `pg_checkpoint` predefined role (run `CHECKPOINT` as non-superuser) | Roles & Auth |
| pg15+ | `PUBLIC` loses `CREATE` on the `public` schema by default (CVE-2018-1058) *(breaking, new clusters)* | Roles & Auth |
| pg15+ | `jsonlog` value for `log_destination` | Config |
| pg15+ | `log_checkpoints` **on** by default *(default)* | Config |
| pg16+ | `pg_stat_io` view (I/O by backend type × object × context) | Monitoring |
| pg16+ | Role membership grant options: `GRANT … WITH ADMIN/INHERIT/SET {TRUE\|FALSE}` (per-grant inheritance) *(behavior change)* | Roles & Auth |
| pg16+ | `pg_create_subscription` predefined role | Roles & Auth |
| pg16+ | `pg_use_reserved_connections` role + `reserved_connections` GUC | Config |
| pg16+ | `CREATEROLE` may administer only roles it created *(behavior change)* | Roles & Auth |
| pg16+ | Logical decoding/replication **from a standby** | Replication |
| pg16+ | Parallel apply of large transactions (`streaming = parallel`, `max_parallel_apply_workers_per_subscription`) | Replication |
| pg17+ | Incremental base backup: `pg_basebackup --incremental=…` | Backup |
| pg17+ | `pg_combinebackup` (reconstruct a full backup from a chain) | Tooling |
| pg17+ | WAL summarizer: `summarize_wal`, `wal_summary_keep_time`, `pg_walsummary` | Config |
| pg17+ | Failover slot sync: `sync_replication_slots`, `synchronized_standby_slots`, `pg_sync_replication_slots()` | Replication |
| pg17+ | `pg_createsubscriber` (physical standby → logical subscriber) | Tooling |
| pg17+ | `pg_maintain` predefined role + the `MAINTAIN` privilege (VACUUM/ANALYZE/REINDEX/CLUSTER/REFRESH MATVIEW/LOCK) | Roles & Auth |
| pg17+ | `pg_stat_checkpointer` view (checkpoint counters moved out of `pg_stat_bgwriter`) *(breaking for monitoring)* | Monitoring |
| pg18+ | Asynchronous I/O subsystem: `io_method` (`sync`/`worker`/`io_uring`), `io_combine_limit`, `io_max_combine_limit`, `pg_aios` view | Config |
| pg18+ | MD5 password authentication **deprecated**; `md5_password_warnings` GUC | Roles & Auth |
| pg18+ | `oauth` authentication method + `oauth_validator_libraries` | Roles & Auth |
| pg18+ | Data checksums enabled by **default** in `initdb` (`--no-data-checksums` to disable) *(default)* | Tooling |
| pg18+ | `pg_upgrade --swap` (swap data dirs; often fastest) | Tooling |
| pg18+ | `pg_upgrade` carries over optimizer statistics (`--no-statistics` to skip) | Tooling |
| pg18+ | `pg_verifybackup` can verify tar-format backups | Backup |
| pg18+ | `pg_combinebackup -k/--link` (hard-link unchanged files) | Backup |
| pg18+ | `pg_createsubscriber --all` (all databases) | Tooling |
| pg18+ | `idle_replication_slot_timeout` (auto-invalidate idle slots) | Replication |
| pg18+ | `max_active_replication_origins` GUC | Replication |
| pg18+ | `publish_generated_columns` publication option | Replication |
| pg18+ | Subscription `streaming` default changes `off` → `parallel` *(default)* | Replication |
| pg18+ | `log_connections` becomes multi-valued (was boolean) *(breaking)* | Config |
| pg18+ | `pg_stat_io` gains `read_bytes`/`write_bytes`/`extend_bytes` + WAL rows; `op_bytes` removed *(breaking)* | Monitoring |
| pg18+ | `pg_signal_autovacuum_worker` predefined role | Roles & Auth |
| pg18+ | `autovacuum_worker_slots` (make `autovacuum_max_workers` runtime-adjustable) | Config |
| pg18+ | `ssl_ecdh_curve` renamed to `ssl_groups` (multi-value) *(breaking)* | Config |
| pg18+ | SCRAM passthrough for `postgres_fdw` / `dblink` | Roles & Auth |
| pg19+ | `effective_wal_level` GUC + auto-enable logical replication when `wal_level = replica` | Config |
| pg19+ | `pg_hosts.conf` configuration file (hostname/key pairs) | Roles & Auth |
| pg19+ | `CHECKPOINT` command accepts options (`MODE`, `FLUSH_UNLOGGED`) | Tooling |
| pg19+ | `pg_dumpall` non-text output formats (restore with `pg_restore`) | Backup |
| pg19+ | `pg_restore --no-globals` | Backup |
| pg19+ | `pg_dump`/`pg_restore` restorable extended statistics (`pg_restore_extended_stats()`) | Backup |
| pg19+ | `REPACK [CONCURRENTLY]` command + `max_repack_replication_slots` + `pg_stat_progress_repack` | Tooling |
| pg19+ | `pg_stat_recovery` view (recovery status) | Monitoring |
| pg19+ | `pg_stat_lock` view + `pg_stat_get_lock()` (per-lock-type stats) | Monitoring |
| pg19+ | `pg_stat_autovacuum_scores` view | Monitoring |
| pg19+ | `pg_dsm_registry_allocations` view | Monitoring |
| pg19+ | `log_lock_waits` **on** by default *(default)* | Config |
| pg19+ | `log_min_messages` settable per process type | Config |
| pg19+ | `password_expiration_warning_threshold` GUC | Roles & Auth |
| pg19+ | `wal_sender_shutdown_timeout` GUC | Replication |
| pg19+ | `wal_receiver_timeout` settable per-subscription/user | Replication |
| pg19+ | Subscription `retain_dead_tuples` + `max_retention_duration` (conflict resolution) | Replication |
| pg19+ | `pg_read_all_data` / `pg_write_all_data` extended to large objects (enables non-superuser `pg_dump`) | Roles & Auth |
| pg19+ | List-valued GUCs can be emptied by setting them to `NULL` | Config |
| pg19+ | CR/LF disallowed in database/role/tablespace names *(breaking, security)* | Roles & Auth |
| pg19+ | Warning emitted on successful MD5 password authentication | Roles & Auth |
| pg19+ | Autovacuum parallel workers (`autovacuum_max_parallel_workers`) | Config |

## Checking your version

```bash
psql -c "SHOW server_version"          # e.g. 18.1
psql -c "SHOW server_version_num"      # 180001 — integer, easy to compare in scripts
psql -c "SELECT version()"             # full build string
postgres --version                     # the server binary
pg_config --version                    # build/devel version (e.g. "PostgreSQL 19beta1")
```

The "Min version" column is a **hard floor**: PostgreSQL does not back-port features to older
release lines, so a `(pg17+)` feature simply does not exist on pg16 — to use it, upgrade the
server. Conversely, a few rows are **(breaking)**: upgrading *into* that version changes
behavior (e.g. `pg_stat_checkpointer` in pg17 moved checkpoint counters out of
`pg_stat_bgwriter`, breaking older monitoring queries) — read the linked release notes first.
