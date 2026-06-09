# Declarative Table Partitioning

Splitting one logical table into physical child tables by key. This file covers the **SQL/DDL** of
partitioning; for *whether and how* partitioning helps performance (pruning costs, planner
behavior, index strategy) see the **postgres-performance** skill. Version tags `(pgNN+)` = minimum
server version; untagged = bedrock for the partitioning feature set, which itself starts at pg10.

## Contents

- [Partitioning methods](#partitioning-methods)
- [Creating a partitioned table](#creating-a-partitioned-table)
- [DEFAULT partition](#default-partition)
- [ATTACH / DETACH](#attach--detach)
- [Sub-partitioning](#sub-partitioning)
- [Indexes & constraints on partitioned tables](#indexes--constraints-on-partitioned-tables)
- [Partition-wise joins & aggregates](#partition-wise-joins--aggregates)
- [pg19 beta: MERGE / SPLIT partitions](#pg19-beta-merge--split-partitions)

## Partitioning methods

| Method | `PARTITION BY` | Since | Use for |
|---|---|---|---|
| Range | `RANGE (col [, ...])` | pg10+ | time series, sequential ids (per-month/year partitions) |
| List | `LIST (col)` | pg10+ | discrete categories (region, tenant, status) |
| Hash | `HASH (col)` | pg11+ | even spread when no natural range/list key |

Declarative partitioning (a real partitioned-table object with automatic tuple routing) is **pg10+**.
The old "partitioning by table inheritance + CHECK constraints + triggers" still works but is
superseded; use declarative partitioning on pg10+.

## Creating a partitioned table

The parent declares the strategy and key; **partitions hold the data** and define their bounds.

```sql
-- RANGE (pg10+): one partition per year. Bounds are [FROM, TO) — lower-inclusive, upper-exclusive
CREATE TABLE measurement (city_id int, logdate date, peaktemp int)
  PARTITION BY RANGE (logdate);

CREATE TABLE measurement_2025 PARTITION OF measurement
  FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE measurement_2026 PARTITION OF measurement
  FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- LIST (pg10+)
CREATE TABLE customers (id int, region text) PARTITION BY LIST (region);
CREATE TABLE customers_emea PARTITION OF customers FOR VALUES IN ('EU', 'UK', 'ME');

-- HASH (pg11+): modulus = number of partitions, remainder = this partition's slot
CREATE TABLE events (id bigint, payload jsonb) PARTITION BY HASH (id);
CREATE TABLE events_p0 PARTITION OF events FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE events_p1 PARTITION OF events FOR VALUES WITH (MODULUS 4, REMAINDER 1);
-- ... remainders 2 and 3
```

Inserts into the parent are **routed** to the right partition automatically. An insert that
matches no partition **errors** unless a `DEFAULT` partition exists.

## DEFAULT partition

A `DEFAULT` partition (pg11+) catches rows that fit no other partition's bounds.

```sql
CREATE TABLE measurement_default PARTITION OF measurement DEFAULT;   -- (pg11+)
```

Caveat: attaching a *new* explicit partition whose range would overlap rows already sitting in the
`DEFAULT` partition forces a scan of the default to verify no conflicts (and fails if any exist).

## ATTACH / DETACH

Manage partitions as standalone tables — the basis of fast bulk load and roll-off:

```sql
-- Build/load a table separately, then attach it (bounds validated, brief lock)
CREATE TABLE measurement_2024 (LIKE measurement INCLUDING DEFAULTS INCLUDING CONSTRAINTS);
-- ... bulk-load measurement_2024 ...
ALTER TABLE measurement ATTACH PARTITION measurement_2024
  FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- Roll off old data without dropping it
ALTER TABLE measurement DETACH PARTITION measurement_2024;               -- ACCESS EXCLUSIVE lock
ALTER TABLE measurement DETACH PARTITION measurement_2024 CONCURRENTLY;  -- (pg14+) weaker lock
```

`DETACH ... CONCURRENTLY` (pg14+) takes only a `SHARE UPDATE EXCLUSIVE` lock on the parent
(vs `ACCESS EXCLUSIVE` for the plain form), so reads/writes against other partitions keep flowing.
If a concurrent detach is interrupted, finish it with `ALTER TABLE ... DETACH PARTITION ...
FINALIZE`. Adding a matching `CHECK` constraint to the table before `ATTACH` lets Postgres skip the
full validation scan.

## Sub-partitioning

A partition can itself be partitioned, giving a tree (e.g. range-by-month, then list-by-region):

```sql
CREATE TABLE sales (sold_at date, region text, amt numeric) PARTITION BY RANGE (sold_at);
CREATE TABLE sales_2026 PARTITION OF sales
  FOR VALUES FROM ('2026-01-01') TO ('2027-01-01')
  PARTITION BY LIST (region);                          -- this partition is itself partitioned
CREATE TABLE sales_2026_emea PARTITION OF sales_2026 FOR VALUES IN ('EU','UK');
```

Keep partition trees shallow; deep multi-level trees multiply planning cost.

## Indexes & constraints on partitioned tables

- An index created on the **parent** (pg11+) is a *template*: Postgres creates a matching index on
  every existing and future partition. A `UNIQUE` constraint/PK on the parent is allowed **only if
  the partition key is included** in its columns (so uniqueness can be enforced per-partition).
- Foreign keys **referencing** a partitioned table, and FKs **from** a partitioned table, are
  supported on modern versions.
- Identity columns are inherited by partitions from the partitioned parent; partitions can't
  declare their own.

## Partition-wise joins & aggregates

When two partitioned tables share a compatible partitioning scheme, the planner can join/aggregate
partition-by-partition. These are **off by default** (they raise planning cost); enable per-session
or in config:

```sql
SET enable_partitionwise_join = on;        -- join matching partitions pairwise
SET enable_partitionwise_aggregate = on;   -- aggregate within each partition, then combine
```

(Whether to enable them, and their planning trade-offs, is **postgres-performance** territory —
this is just where the dials live.)

## pg19 beta: MERGE / SPLIT partitions

PostgreSQL 19 (currently **beta**) adds DDL to reshape partitions in place:

```sql
-- (pg19+, beta) combine several partitions into one
ALTER TABLE measurement MERGE PARTITIONS (measurement_2024, measurement_2025) INTO measurement_old;

-- (pg19+, beta) split one partition into several by new bounds
ALTER TABLE measurement SPLIT PARTITION measurement_old INTO (
  PARTITION measurement_2024 FOR VALUES FROM ('2024-01-01') TO ('2025-01-01'),
  PARTITION measurement_2025 FOR VALUES FROM ('2025-01-01') TO ('2026-01-01')
);
```

pg19 also allows `COPY table TO` directly on a partitioned table (previously you had to `COPY
(SELECT ...) TO`). Both are beta and may change before GA.

## Sources

- Partitioning chapter: <https://www.postgresql.org/docs/current/ddl-partitioning.html> · in-repo `ddl.sgml`
- `CREATE TABLE ... PARTITION` / `ALTER TABLE ... ATTACH|DETACH|MERGE|SPLIT`: <https://www.postgresql.org/docs/current/sql-altertable.html> · in-repo `ref/create_table.sgml`, `ref/alter_table.sgml`
- pg10 (range/list), pg11 (hash, default, partitioned indexes), pg14 (`DETACH CONCURRENTLY`), pg19beta (`MERGE`/`SPLIT PARTITIONS`, `COPY TO`) — Appendix E + `release-19.sgml` (see [version-features.md](version-features.md)).
