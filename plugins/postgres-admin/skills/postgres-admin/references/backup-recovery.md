# Backup, Recovery & Upgrades

Two backup families plus recovery and version upgrades. Version tags `(pgNN+)` mark features
added in PostgreSQL 10+; untagged items are bedrock (9.x or earlier).

## Contents

- [Logical vs physical (choosing)](#logical-vs-physical-choosing)
- [pg_dump (one database)](#pg_dump-one-database)
- [pg_dumpall (whole cluster + globals)](#pg_dumpall-whole-cluster--globals)
- [pg_restore](#pg_restore)
- [pg_basebackup (physical)](#pg_basebackup-physical)
- [Incremental backups (pg17+)](#incremental-backups-pg17)
- [Backup manifests & pg_verifybackup (pg13+)](#backup-manifests--pg_verifybackup-pg13)
- [Continuous archiving & PITR](#continuous-archiving--pitr)
- [Major-version upgrades (pg_upgrade)](#major-version-upgrades-pg_upgrade)
- [Minor-version upgrades](#minor-version-upgrades)

## Logical vs physical (choosing)

| | Logical (`pg_dump`/`pg_dumpall`) | Physical (`pg_basebackup`) |
|---|---|---|
| Granularity | a database, schema, or table | the **whole cluster** (byte-for-byte) |
| Output | SQL or an archive of SQL+data | data-directory files |
| Cross-version | **yes** (restore into a newer major) | no (same major only) |
| Enables PITR | no | **yes** (with WAL archiving) |
| Basis for replicas | no | **yes** |
| Speed on big DBs | slower (logical replay) | fast (file copy) |
| Captures roles/tablespaces | only `pg_dumpall` | yes (cluster-wide) |

Rule of thumb: **logical** for portability, per-object restores, and major upgrades;
**physical + WAL archiving** for whole-cluster DR, PITR, and seeding standbys.

## pg_dump (one database)

```bash
pg_dump -Fc -f app.dump app                 # custom format (compressed, selective restore)
pg_dump -Fd -j4 -f app_dir app              # directory format + 4 parallel workers (fastest dump)
pg_dump -Fp -f app.sql app                  # plain SQL script (restore with psql)
pg_dump -Ft -f app.tar app                  # tar archive

# Scope:
pg_dump -n app -N audit app                 # include schema app, exclude schema audit
pg_dump -t orders -t 'public.audit_*' app   # selected tables (patterns OK)
pg_dump --schema-only app                   # DDL only  (--data-only for data only)
pg_dump --section=pre-data  app             # pre-data | data | post-data (indexes/FKs)

# Useful flags:
pg_dump --no-owner --no-privileges app      # portable dump (drop ownership/ACLs)
pg_dump -Z 9 -Fc app                        # compression level
```

**Formats:** `-Fp` plain (text, restore via `psql`), `-Fc` custom, `-Fd` directory, `-Ft`
tar. Only **custom** and **directory** support selective and **parallel** (`-j`) restore;
**directory** is the only format you can *write* in parallel. `--section` splits a dump into
`pre-data` (DDL), `data`, `post-data` (constraints/indexes) for staged loads.

## pg_dumpall (whole cluster + globals)

`pg_dump` does **not** capture roles, tablespaces, or other databases. `pg_dumpall` does:

```bash
pg_dumpall --globals-only > globals.sql     # roles + tablespaces only (pair with pg_dump)
pg_dumpall -f cluster.sql                    # every database + globals (plain SQL)
pg_dumpall -Fd -f cluster_dir                # non-text formats (pg19+) → restore with pg_restore
psql -f globals.sql                          # restore globals
```

Common pattern: `pg_dumpall --globals-only` for roles/tablespaces **plus** a per-database
`pg_dump -Fc` for each DB (so you get parallel, selective restores per database). Before
pg19, `pg_dumpall` only emitted plain SQL.

## pg_restore

Restores custom/directory/tar archives (not plain SQL — that's `psql -f`):

```bash
pg_restore -d app app.dump                  # restore into existing DB app
pg_restore -d app -j4 app.dump              # parallel restore (custom/dir only)
createdb app2 && pg_restore -d app2 app.dump
pg_restore -l app.dump > toc.list           # list contents (table of contents)
pg_restore -L toc.list -d app app.dump      # restore a filtered/reordered subset
pg_restore --no-owner --role=app -d app app.dump
pg_restore --data-only -t orders -d app app.dump
pg_restore --clean --if-exists -d app app.dump   # drop objects first
pg_restore --no-globals -d app cluster_dir  # (pg19+) skip globals from a pg_dumpall archive
```

The `-l`/`-L` TOC workflow is the precise way to restore exactly the objects you want, in a
chosen order.

## pg_basebackup (physical)

Takes a consistent file-level copy of the **entire cluster** — the basis for standbys, PITR,
and incremental backups. The role needs `REPLICATION` (or superuser) and a matching
`pg_hba` `replication` line.

```bash
pg_basebackup -D /backup/base -Ft -z -P             # tar + gzip, with progress
pg_basebackup -D /backup/base -Fp -X stream -c fast # plain files, stream WAL, fast checkpoint
pg_basebackup -D /standby -R -X stream              # -R writes primary_conninfo + standby.signal
pg_basebackup -D /backup/base --checkpoint=spread   # gentler I/O
```

- `-Ft` tar (one file per tablespace) vs `-Fp` plain (a ready-to-run data dir).
- `-X stream` (default) opens a second connection to stream WAL so the backup is
  self-consistent without relying on archiving; `-X none` requires WAL archiving.
- `-R` (pg9.3+ for recovery.conf; pg12+ writes `postgresql.auto.conf` + `standby.signal`)
  makes the copy immediately usable as a standby.
- `-c fast` forces an immediate checkpoint so the backup starts right away.

## Incremental backups (pg17+)

Back up only blocks changed since a prior backup, then reconstruct a full backup offline.

```bash
# Prereq: enable the WAL summarizer on the server
ALTER SYSTEM SET summarize_wal = on;  SELECT pg_reload_conf();   -- (pg17+)

# 1) a full base backup (with its backup_manifest)
pg_basebackup -D /backup/full -X stream

# 2) later, an incremental relative to the previous manifest
pg_basebackup -D /backup/incr1 --incremental=/backup/full/backup_manifest

# 3) reconstruct a usable full backup by combining the chain (pg17+)
pg_combinebackup /backup/full /backup/incr1 -o /restore/full
pg_combinebackup … -k          # (pg18+) hard-link unchanged files (saves space/time)
```

You **must keep the whole chain** (full + every incremental in between) and combine them with
`pg_combinebackup` before the result is restorable. `summarize_wal` must be on (and the
summarizer caught up) or the incremental backup fails. `pg_walsummary` (pg17+) inspects the
summary files.

## Backup manifests & pg_verifybackup (pg13+)

`pg_basebackup` writes a `backup_manifest` (checksums + WAL range) automatically.

```bash
pg_verifybackup /backup/base                 # verify files + checksums against the manifest
pg_verifybackup -n /backup/base              # skip WAL verification
pg_verifybackup /backup/base.tar             # verify tar-format backups (pg18+)
```

Verify backups routinely — a backup you've never restored or verified is a hope, not a backup.

## Continuous archiving & PITR

Physical backup **+ archived WAL** lets you restore to any point in time.

```conf
# postgresql.conf (on the primary) — set up archiving
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /archive/%f && cp %p /archive/%f'   # %p=path %f=filename
```

**Restore to a point in time:**

```conf
# postgresql.conf in the restored data dir
restore_command = 'cp /archive/%f %p'
recovery_target_time = '2026-06-09 14:30:00'    # or _name / _xid / _lsn / 'immediate'
recovery_target_action = 'promote'              # promote | pause | shutdown
```

```bash
# 1) restore the base backup into a fresh data dir
# 2) write the recovery settings above
# 3) drop a recovery.signal file, then start the server
touch "$PGDATA/recovery.signal"
pg_ctl start -D "$PGDATA"
```

> **recovery.conf was removed in pg12.** Recovery settings now live in `postgresql.conf`;
> `standby.signal` puts the server in standby (streaming) mode, `recovery.signal` puts it in
> targeted recovery (PITR) mode. The server **refuses to start** if a `recovery.conf` exists.
> Targets: `recovery_target_time`, `_name` (a `pg_create_restore_point()` label), `_xid`,
> `_lsn`, or `recovery_target = 'immediate'`. `recovery_target_inclusive` controls boundary.

## Major-version upgrades (pg_upgrade)

In-place upgrade between major versions (e.g. 17 → 18). Run as the OS owner with **both
clusters stopped**; always back up first and `--check` first.

```bash
pg_upgrade \
  --old-datadir=/data/17 --new-datadir=/data/18 \
  --old-bindir=/usr/lib/postgresql/17/bin \
  --new-bindir=/usr/lib/postgresql/18/bin \
  --check                                   # read-only validation, changes nothing

# then re-run without --check, picking a transfer mode:
pg_upgrade … --link        # hard-link files: fastest, but the OLD cluster is then unusable
pg_upgrade … --clone       # reflink/CoW clone where the filesystem supports it
pg_upgrade … --copy        # copy files (default): old cluster stays intact
pg_upgrade … --swap        # (pg18+) swap directories — often the fastest mode
pg_upgrade … -j $(nproc)   # parallelize across databases/tablespaces
```

- **Mode trade-off:** `--copy` is safe (old cluster untouched) but slow on big clusters;
  `--link`/`--clone`/`--swap` are fast but make rollback to the old cluster harder/impossible
  once the new one starts.
- After a successful upgrade, run the generated `analyze_new_cluster` / `vacuumdb
  --analyze-in-stages` to rebuild statistics, then delete the old cluster
  (`delete_old_cluster.sh`). pg18+ `pg_upgrade` can carry over optimizer statistics
  (`--no-statistics` to skip).
- Logical replication / `pg_createsubscriber` is an alternative for **near-zero-downtime**
  major upgrades.

## Minor-version upgrades

Minor releases (e.g. 18.1 → 18.2) are **binary-compatible**: install the new packages and
**restart** the server — no `pg_upgrade`, no dump/restore. Always read the release notes;
a few minor releases require a post-restart `REINDEX` for specific bugs.
