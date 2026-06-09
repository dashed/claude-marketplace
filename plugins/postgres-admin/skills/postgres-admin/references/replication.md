# WAL, Replication & High Availability

WAL fundamentals, physical/streaming replication, replication slots, synchronous commit, and
logical replication. Version tags `(pgNN+)` mark features added in PostgreSQL 10+; untagged
items are bedrock (9.x or earlier).

## Contents

- [WAL fundamentals](#wal-fundamentals)
- [Physical / streaming replication](#physical--streaming-replication)
- [Replication slots](#replication-slots)
- [Synchronous replication](#synchronous-replication)
- [Hot standby](#hot-standby)
- [Logical replication (pg10+)](#logical-replication-pg10)
- [Publications](#publications)
- [Subscriptions](#subscriptions)
- [Failover slot synchronization (pg17+)](#failover-slot-synchronization-pg17)
- [pg_createsubscriber (pg17+)](#pg_createsubscriber-pg17)
- [Physical vs logical: choosing](#physical-vs-logical-choosing)

## WAL fundamentals

The **Write-Ahead Log** records every change before it touches data files. It underpins crash
recovery, replication, and PITR.

```sql
SHOW wal_level;     -- minimal | replica (default) | logical
SELECT pg_current_wal_lsn();              -- current write position (primary)
SELECT pg_last_wal_replay_lsn();          -- last replayed position (standby)
SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS lag_bytes
  FROM pg_stat_replication;               -- bytes a standby is behind
```

- `wal_level = replica` (the default) supports streaming replication and base backups;
  `logical` adds the extra info logical replication needs. Changing it needs a **restart**.
- pg19+: `effective_wal_level` reports the level actually in effect, and with
  `wal_level = replica` the server can **auto-enable logical** when a publication needs it.

## Physical / streaming replication

A standby replays the primary's WAL stream byte-for-byte. Setup:

```conf
# PRIMARY postgresql.conf
wal_level = replica
max_wal_senders = 10
wal_keep_size = '1GB'                  # WAL to retain if no slot (renamed from wal_keep_segments, pg13+)
# pg_hba.conf: allow the replication connection
# host  replication  repl  10.0.0.0/8  scram-sha-256
```

```bash
# STANDBY: clone the primary, writing connection info + standby.signal
pg_basebackup -h primary -U repl -D "$PGDATA" -R -X stream -c fast
# -R writes primary_conninfo to postgresql.auto.conf and creates standby.signal (pg12+)
pg_ctl start -D "$PGDATA"
```

```conf
# what -R writes (postgresql.auto.conf) / set manually:
primary_conninfo = 'host=primary user=repl application_name=standby1'
primary_slot_name = 'standby1'          # use a replication slot (recommended)
```

```sql
-- on the PRIMARY: watch connected standbys
SELECT application_name, client_addr, state, sync_state,
       sent_lsn, write_lsn, flush_lsn, replay_lsn,
       write_lag, flush_lag, replay_lag
  FROM pg_stat_replication;
-- on the STANDBY:
SELECT status, sender_host, latest_end_lsn FROM pg_stat_wal_receiver;
SELECT pg_is_in_recovery();             -- true on a standby
SELECT pg_promote();                    -- promote standby to primary (pg12+)
```

## Replication slots

Slots make the primary **retain WAL** (and, for logical, decoding state) until the consumer
has confirmed receipt — so a disconnected standby can catch up. The danger: an **inactive
slot retains WAL forever and can fill the disk**.

```sql
SELECT pg_create_physical_replication_slot('standby1');
SELECT pg_create_logical_replication_slot('sub1', 'pgoutput');
SELECT slot_name, slot_type, active, wal_status, safe_wal_size,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained
  FROM pg_replication_slots;
SELECT pg_drop_replication_slot('standby1');     -- reclaim WAL from an abandoned slot
```

- `wal_status`: `reserved` / `extended` / `unreserved` / `lost` — `lost` means required WAL
  was already removed and the slot is broken.
- `max_replication_slots` and `max_wal_senders` cap slots/senders (restart).
- pg18+: `idle_replication_slot_timeout` auto-invalidates slots idle too long — a guard
  against disk-filling abandoned slots.

## Synchronous replication

Make the primary wait for standby acknowledgement before reporting commit success:

```conf
synchronous_standby_names = 'ANY 1 (standby1, standby2)'   # quorum: any 1 of these (pg10+)
# or: 'FIRST 2 (s1, s2, s3)'  or  's1, s2'  (priority order)
```

```sql
SHOW synchronous_commit;   -- on | remote_apply | remote_write | local | off
```

| `synchronous_commit` | Waits until WAL is… |
|---|---|
| `off` | not even flushed locally before returning (fastest, async durability) |
| `local` | flushed to the local disk only |
| `remote_write` | received + written (not fsynced) by sync standbys |
| `on` (default) | flushed to disk on local **and** sync standbys |
| `remote_apply` | flushed **and replayed** on sync standbys (read-your-writes on standbys) |

Quorum commit (`ANY n`, pg10+) waits for any *n* of the listed standbys regardless of order;
`FIRST n` follows priority order. Set `synchronous_commit` per-transaction for hot paths that
can tolerate weaker durability.

## Hot standby

A standby can serve **read-only** queries while replaying (`hot_standby = on`, default).
Tension: a long read query on the standby can conflict with replay of changes that remove
rows it needs.

```conf
hot_standby = on
hot_standby_feedback = on            # standby tells primary about its oldest snapshot (less bloat-free, fewer conflicts)
max_standby_streaming_delay = '30s'  # how long replay may pause for a standby query before cancelling it
```

`hot_standby_feedback = on` reduces query cancellations at the cost of slightly delayed
vacuum/bloat cleanup on the primary.

## Logical replication (pg10+)

Replicates **selected tables** at the row level via decode-and-apply — works **across major
versions** and across differing schemas, and the subscriber is fully read-write. Requires
`wal_level = logical` on the publisher.

```
publisher: CREATE PUBLICATION  →  WAL decoded via slot  →  subscriber: CREATE SUBSCRIPTION applies
```

## Publications

```sql
CREATE PUBLICATION pub FOR TABLE orders, customers;
CREATE PUBLICATION pub_all FOR ALL TABLES;                       -- everything (needs privilege)
CREATE PUBLICATION pub_sales FOR TABLES IN SCHEMA sales;         -- whole schema (pg15+)

-- Row filter + column list (pg15+):
CREATE PUBLICATION pub_eu
  FOR TABLE orders (id, customer_id, total) WHERE (region = 'EU');

ALTER PUBLICATION pub ADD TABLE shipments;
ALTER PUBLICATION pub SET (publish = 'insert,update');           -- which DML to publish
-- pg18+: publish_generated_columns; pg13+: partitioned tables publish their partitions
```

- **Row filters** (`WHERE`, pg15+): only matching rows replicate. The filter may only use
  columns in the replica identity for UPDATE/DELETE.
- **Column lists** (pg15+): only the named columns replicate; can't combine with
  `FOR TABLES IN SCHEMA`.
- `publish_via_partition_root` controls whether partitioned tables replicate as the root or
  as individual partitions.

## Subscriptions

```sql
CREATE SUBSCRIPTION sub
  CONNECTION 'host=publisher dbname=app user=repl'
  PUBLICATION pub
  WITH (copy_data = true, streaming = 'parallel');   -- streaming parallel apply (pg16+; default pg18+)

ALTER SUBSCRIPTION sub REFRESH PUBLICATION;          -- pick up newly added tables
ALTER SUBSCRIPTION sub DISABLE;                      -- pause
ALTER SUBSCRIPTION sub SET (slot_name = 'sub_slot');
DROP SUBSCRIPTION sub;                               -- also drops the remote slot if reachable

SELECT * FROM pg_stat_subscription;          -- apply progress / last message
SELECT * FROM pg_stat_subscription_stats;    -- error counts (conflicts, etc.)
```

- A subscription creates a logical **slot on the publisher** automatically — dropping the
  subscription while the publisher is unreachable leaves an orphan slot to clean up.
- **Initial sync** copies existing data (`copy_data`), then streams changes.
- pg16+: parallel apply of large in-progress transactions
  (`max_parallel_apply_workers_per_subscription`); logical decoding from a **standby**.
- pg18+: `streaming = parallel` is the default; conflict detection columns added.

## Failover slot synchronization (pg17+)

Without help, logical slots live only on the primary — a failover to a physical standby
**breaks subscribers**. pg17+ synchronizes logical slots to standbys:

```conf
# on the standby that should carry the slots:
sync_replication_slots = on            # (pg17+) keep logical slots in sync from the primary
# on the primary:
synchronized_standby_slots = 'standby1'  # (pg17+) don't advance logical slots past these physical standbys
```

```sql
SELECT pg_sync_replication_slots();    -- (pg17+) one-shot manual sync
SELECT slot_name, failover, synced FROM pg_replication_slots;   -- failover/synced flags
```

Create the slot/subscription with `failover = true` so it's eligible for syncing. After
promotion, subscribers reconnect to the new primary and resume from the synced slot.

## pg_createsubscriber (pg17+)

Convert a physical standby into a logical subscriber in place — much faster than a fresh
initial copy for large databases (handy for near-zero-downtime major upgrades).

```bash
pg_createsubscriber -D /standby -P 'host=primary dbname=app' -d app
pg_createsubscriber … --all     # (pg18+) all databases at once
```

## Physical vs logical: choosing

| Need | Use |
|---|---|
| Full DR replica, identical cluster, read scaling | **physical / streaming** |
| HA with automatic-ish failover | physical + failover tooling (Patroni, repmgr, pg_auto_failover) |
| Replicate a subset of tables | **logical** |
| Replicate across major versions / different schemas | **logical** |
| Near-zero-downtime major upgrade | logical / `pg_createsubscriber` |
| Aggregate many DBs into one, or fan-out | **logical** |

PostgreSQL ships the replication primitives, not a built-in cluster manager — pair physical
replication with an external HA tool for automated failover, fencing, and VIP management.
