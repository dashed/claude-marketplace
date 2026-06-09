---
name: postgres-sql
description: The PostgreSQL SQL dialect and data types that set Postgres apart from generic SQL. Use when writing or debugging Postgres-specific SQL — upsert (`INSERT ... ON CONFLICT DO UPDATE/NOTHING`), `RETURNING` (incl. `OLD`/`NEW`), `MERGE`, CTEs (`WITH`/`MATERIALIZED`/recursive/data-modifying), window frames, `GROUPING SETS`/`CUBE`/`ROLLUP`, `DISTINCT ON`, `LATERAL`, `FILTER`, generated & identity columns, declarative partitioning, `jsonb` operators + jsonpath + SQL/JSON (`JSON_TABLE`/`IS JSON`), arrays, ranges & multiranges, composite/enum/domain types, and functions like `uuidv7()`/`gen_random_uuid()`/`ANY_VALUE()`. Triggers on `ON CONFLICT`, `MERGE`, `jsonb`, `@>`/`->>`, `GENERATED ... AS IDENTITY`, `PARTITION BY`. Disambiguation — this is the SQL dialect & types; for the `psql` client use psql, for tuning/EXPLAIN/indexes use postgres-performance, for config/auth/backup use postgres-admin, for contrib use postgres-extensions. Features carry inline `(pgNN+)` tags; unlisted = long-standing (bedrock since 9.x).
---

# PostgreSQL SQL Dialect & Data Types

## Overview

PostgreSQL is far more than "SQL with a server." It ships a rich, standards-leading **SQL
dialect** and a deep **type system** that together replace patterns you'd otherwise hand-roll in
application code: atomic upserts, set-based row transformations, recursive graph walks, JSON
documents queried in-place, array and range columns, and tables that physically split themselves
by key. This skill documents the **Postgres-specific SQL surface** — the constructs and types
that distinguish Postgres from generic ANSI SQL.

**The mental-model shift:** in Postgres, things you'd normally do in a loop in app code become a
single declarative statement. "Insert or update" is one `INSERT ... ON CONFLICT`. "For each
parent, fetch its children" is a `LATERAL` join. "Walk this tree" is a `WITH RECURSIVE`. "Pick
the latest row per group" is `DISTINCT ON`. A JSON blob is a first-class `jsonb` column you index
and query, not a `TEXT` you parse. Reaching for these instead of procedural code is the whole
point.

> **Disambiguation — what this skill is NOT:**
> - **Not the `psql` client** — `\d`, `\copy`, `\watch`, meta-commands, prompts → **psql** skill.
> - **Not query tuning** — `EXPLAIN`, index choice, `VACUUM`, planner stats → **postgres-performance** skill.
> - **Not administration** — `postgresql.conf`, roles/auth, backup, replication → **postgres-admin** skill.
> - **Not contrib/extensions** — PostGIS, `pg_trgm`, `pg_stat_statements`, etc. → **postgres-extensions** skill.
> - **Not a generic SQL tutorial** — assumes you know `SELECT`/`JOIN`/`GROUP BY`; covers only what's *Postgres-specific*.

## When to Use This Skill

| Reach for it when you need to… | Postgres construct |
|---|---|
| Insert a row, or update it if it already exists (atomic upsert) | `INSERT ... ON CONFLICT DO UPDATE` |
| Return the rows a write touched (ids, computed values, before/after) | `RETURNING` (+ `OLD`/`NEW`, pg18+) |
| Apply insert/update/delete in one set-based pass from a source | `MERGE` (pg15+) |
| Reuse a subquery, walk a hierarchy, or write-then-return in one statement | CTEs / `WITH RECURSIVE` / data-modifying `WITH` |
| Rank, run totals, lag/lead, per-partition windows | window functions + frame clause |
| Subtotals across multiple grouping dimensions in one scan | `GROUPING SETS` / `CUBE` / `ROLLUP` |
| One row per group (e.g. latest per user) | `DISTINCT ON` |
| Join each left row to a subquery that depends on it | `LATERAL` |
| Aggregate only a subset of rows without a `CASE` hack | `FILTER (WHERE ...)` |
| A column auto-computed from others, or an auto-increment key | generated columns / identity columns |
| A huge table split physically by range/list/hash | declarative partitioning |
| Store, index, and query JSON documents | `jsonb` + operators + jsonpath + SQL/JSON |
| Columns holding arrays, ranges, composites, enums, or constrained domains | array / range / composite / enum / domain types |

## Prerequisites

Confirm the server version — it governs which constructs below will parse. SQL is executed by the
**server**, so the server version (not the client) is what matters:

```sql
SELECT version();          -- full build string
SHOW server_version;       -- e.g. 18.0
SELECT current_setting('server_version_num')::int;  -- e.g. 180000 (easy to compare)
```

```bash
psql -tAc 'show server_version_num'   # from the shell; 170000 = v17.0
```

**Version note:** PostgreSQL adds SQL features on **major** versions (one per year: 10, 11, …,
18; **19 is currently in beta**). Features stable since the **9.x era** are **bedrock** and shown
here **unannotated** ("unlisted = long-standing"). Anything newer carries an inline `(pgNN+)`
tag — meaning "needs PostgreSQL NN or later" — and **only when sourced** (release notes /
command docs). The full feature → minimum-version map with citations is in
[references/version-features.md](references/version-features.md). When a statement errors with a
**syntax error** on an older server, check the tag.

## Core Workflows

Each section is runnable. Tags like `(pg15+)` mark the minimum server version; untagged = bedrock.

### 1. Upsert: `INSERT ... ON CONFLICT`

Insert, but on a unique/PK conflict either update the existing row or skip. The special
`excluded` row holds the values that *would* have been inserted.

```sql
-- Update on conflict ("upsert"): bump quantity, keep an audit timestamp
INSERT INTO inventory (sku, qty) VALUES ('A-1', 10)
ON CONFLICT (sku) DO UPDATE
  SET qty = inventory.qty + excluded.qty, updated_at = now()
RETURNING sku, qty;

-- Insert-or-ignore: do nothing if it already exists
INSERT INTO tags (name) VALUES ('postgres') ON CONFLICT DO NOTHING;

-- Conflict target can be a column list, a constraint name, or a partial-index predicate
INSERT INTO users (email, name) VALUES ('a@b.com', 'Ada')
ON CONFLICT (email) WHERE active DO UPDATE SET name = excluded.name;
```

`ON CONFLICT (cols)` infers the arbiter index by column(s)/expression; `ON CONFLICT ON CONSTRAINT
name` names it explicitly. A `DO UPDATE` may carry its own `WHERE`. (pg19+ adds `ON CONFLICT DO
SELECT ... RETURNING` to read/lock the conflicting row.) Full grammar:
[references/dml-returning.md](references/dml-returning.md).

### 2. `RETURNING` — get data back from writes

Every `INSERT`/`UPDATE`/`DELETE`/`MERGE` can return columns from affected rows — no follow-up
`SELECT`, no race.

```sql
INSERT INTO orders (cust_id, total) VALUES (42, 99.50) RETURNING id, created_at;
UPDATE accounts SET balance = balance - 100 WHERE id = 1 RETURNING balance;
DELETE FROM sessions WHERE expires < now() RETURNING id;

-- pg18+: reference both the OLD and NEW row explicitly
UPDATE accounts SET balance = balance + 50 WHERE id = 1
RETURNING old.balance AS before, new.balance AS after;
```

### 3. `MERGE` — set-based insert/update/delete (pg15+)

One statement reconciles a target table against a source, choosing an action per row.

```sql
MERGE INTO inventory AS t
USING shipments AS s ON t.sku = s.sku
WHEN MATCHED THEN UPDATE SET qty = t.qty + s.qty
WHEN NOT MATCHED THEN INSERT (sku, qty) VALUES (s.sku, s.qty);
```

pg17+ adds three big pieces: a `RETURNING` clause (with `merge_action()` to see which branch
fired), `WHEN NOT MATCHED BY SOURCE` (act on target rows the source lacks — e.g. delete/flag),
and `MERGE` on updatable views.

```sql
MERGE INTO inventory AS t USING shipments AS s ON t.sku = s.sku
WHEN MATCHED THEN UPDATE SET qty = t.qty + s.qty
WHEN NOT MATCHED BY SOURCE THEN DELETE            -- pg17+
RETURNING merge_action(), t.sku, t.qty;           -- pg17+
```

**`MERGE` vs `ON CONFLICT`:** use `ON CONFLICT` for "insert these rows, resolve clashes" (needs a
unique constraint); use `MERGE` for "reconcile a whole source against a target" with arbitrary
match logic and deletes. More: [references/dml-returning.md](references/dml-returning.md).

### 4. CTEs: `WITH`, recursive, and data-modifying

A `WITH` clause names subqueries. Since pg12 a plain CTE is **inlined** when it's referenced once
and side-effect-free; use `MATERIALIZED` to force a one-time computed fence (an optimization
barrier) or `NOT MATERIALIZED` to force inlining.

```sql
WITH recent AS MATERIALIZED (        -- (pg12+ keyword) compute once, reuse
  SELECT * FROM events WHERE ts > now() - interval '1 day'
)
SELECT user_id, count(*) FROM recent GROUP BY user_id;
```

Recursive CTEs walk hierarchies/graphs (org charts, threads, BOMs):

```sql
WITH RECURSIVE subordinates AS (
  SELECT id, manager_id, name FROM emp WHERE id = 1     -- anchor
  UNION ALL
  SELECT e.id, e.manager_id, e.name
  FROM emp e JOIN subordinates s ON e.manager_id = s.id  -- recursive term
)
SELECT * FROM subordinates;
```

Data-modifying CTEs run writes inside `WITH` and pipe their `RETURNING` output downstream — e.g.
archive-then-delete atomically:

```sql
WITH moved AS (
  DELETE FROM events WHERE ts < now() - interval '1 year' RETURNING *
)
INSERT INTO events_archive SELECT * FROM moved;
```

Full treatment (`SEARCH`/`CYCLE` clauses, evaluation rules): [references/queries.md](references/queries.md).

### 5. Window functions & frames

Compute across a set of rows *related to the current row* without collapsing them.

```sql
SELECT
  user_id, amount, ts,
  row_number()  OVER w                                   AS seq,
  sum(amount)   OVER (PARTITION BY user_id ORDER BY ts)  AS running_total,
  lag(amount)   OVER w                                   AS prev_amount
FROM payments
WINDOW w AS (PARTITION BY user_id ORDER BY ts);
```

The **frame clause** controls which peer rows feed a window aggregate — `ROWS`/`RANGE` are
bedrock; `GROUPS` mode and frame `EXCLUDE` are pg11+:

```sql
avg(price) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)  -- 7-day moving avg
sum(x)     OVER (ORDER BY g GROUPS BETWEEN 1 PRECEDING AND CURRENT ROW)  -- (pg11+)
```

More (frame exclusion, all window fns): [references/queries.md](references/queries.md).

### 6. Grouping extensions, `DISTINCT ON`, `LATERAL`, `FILTER`

```sql
-- Subtotals + grand total in ONE scan (GROUPING SETS / ROLLUP / CUBE)
SELECT region, product, sum(sales)
FROM s GROUP BY ROLLUP (region, product);

-- One row per group: latest payment per user (ORDER BY must lead with the DISTINCT ON keys)
SELECT DISTINCT ON (user_id) user_id, amount, ts
FROM payments ORDER BY user_id, ts DESC;

-- LATERAL: the subquery sees columns from the left side (top-3 orders per customer)
SELECT c.id, o.*
FROM customers c
CROSS JOIN LATERAL (
  SELECT * FROM orders o WHERE o.cust_id = c.id ORDER BY o.total DESC LIMIT 3
) o;

-- FILTER: per-aggregate row subset, cleaner than sum(CASE WHEN ...)
SELECT count(*) AS total,
       count(*) FILTER (WHERE status = 'paid') AS paid
FROM orders;
```

Details + `GROUPING()`: [references/queries.md](references/queries.md).

### 7. Generated & identity columns

```sql
CREATE TABLE people (
  id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- (pg10+) prefer over serial
  first     text,
  last      text,
  full_name text GENERATED ALWAYS AS (first || ' ' || last) STORED  -- (pg12+) STORED
);
```

- **Identity columns** `GENERATED { ALWAYS | BY DEFAULT } AS IDENTITY` (pg10+) are the SQL-standard
  auto-increment; prefer them over the old `serial`/`bigserial` (which leak a separate sequence and
  have ownership quirks). `ALWAYS` blocks manual inserts (override with `OVERRIDING SYSTEM VALUE`);
  `BY DEFAULT` allows them.
- **Generated columns** are computed from other columns. `STORED` (pg12+) materializes on write.
  **`VIRTUAL`** (computed on read) arrived in **pg18** and is now the **default** kind — so on pg18+
  a bare `GENERATED ALWAYS AS (...)` is virtual; **always write `STORED` explicitly** if you need
  the stored behavior and want version-portable DDL.

More (`serial` migration, `OVERRIDING`): [references/data-types.md](references/data-types.md).

### 8. Declarative partitioning

Split one logical table into physical partitions by **range**, **list** (pg10+), or **hash** (pg11+).

```sql
CREATE TABLE measurement (city_id int, logdate date, peaktemp int)
  PARTITION BY RANGE (logdate);

CREATE TABLE measurement_2026
  PARTITION OF measurement FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE TABLE measurement_default PARTITION OF measurement DEFAULT;  -- (pg11+) catch-all

-- Attach/detach existing tables as partitions (DETACH ... CONCURRENTLY is pg14+)
ALTER TABLE measurement ATTACH PARTITION m_old FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
ALTER TABLE measurement DETACH PARTITION m_old CONCURRENTLY;        -- (pg14+)
```

Routing, sub-partitioning, `ATTACH`/`DETACH`, partition-wise joins/aggregates, and pg19's
`MERGE`/`SPLIT PARTITIONS`: [references/partitioning.md](references/partitioning.md).

### 9. JSON / JSONB

`jsonb` (binary, indexable, deduped keys — the default choice) and `json` (text, preserves
formatting) are bedrock. Navigate and test with operators; query with jsonpath (pg12+); shred with
SQL/JSON (pg16/pg17).

```sql
SELECT data->'address'->>'city'  AS city,   -- -> keeps json, ->> returns text
       data#>>'{tags,0}'         AS first_tag
FROM docs
WHERE data @> '{"active": true}'             -- containment (jsonb), GIN-indexable
  AND data ? 'email'                         -- key exists
  AND data @@ '$.age > 18';                  -- jsonpath predicate (pg12+)

-- SQL/JSON query functions (pg17+): extract scalars / objects / a whole table
SELECT JSON_VALUE(data, '$.age' RETURNING int) FROM docs;          -- (pg17+)
SELECT * FROM JSON_TABLE(                                           -- (pg17+)
  (SELECT data FROM docs WHERE id = 1), '$.items[*]'
  COLUMNS (name text PATH '$.name', qty int PATH '$.qty'));
```

The SQL/JSON split matters: **`IS JSON`** + the `JSON_ARRAY`/`JSON_OBJECT` constructor family are
**pg16+**; the **query functions** `JSON_TABLE`/`JSON_QUERY`/`JSON_VALUE`/`JSON_EXISTS` and the
`JSON()`/`JSON_SCALAR()`/`JSON_SERIALIZE()` constructors are **pg17+**. Full operator/jsonpath/SQL-
JSON reference: [references/json.md](references/json.md).

### 10. Arrays, ranges/multiranges, composites, enums, domains

```sql
-- Arrays: literal, contains (@>), overlaps (&&), membership, unnest
SELECT * FROM posts WHERE tags @> ARRAY['sql'] AND 'postgres' = ANY(tags);
SELECT id, unnest(tags) AS tag FROM posts;

-- Ranges + multiranges (multirange types: pg14+)
SELECT int4range(1, 10) @> 5;                         -- range containment → true
SELECT '{[1,5], [10,20]}'::int4multirange;            -- (pg14+) noncontiguous set of ranges
CREATE TABLE booking (room int, during tsrange,
  EXCLUDE USING gist (room WITH =, during WITH &&));  -- no double-booking

-- Enums and domains
CREATE TYPE mood AS ENUM ('sad', 'ok', 'happy');
CREATE DOMAIN positive_int AS int CHECK (VALUE > 0);

-- Composite / row types and uuid generation
SELECT ROW(1, 'a')::my_type;
SELECT gen_random_uuid();   -- (pg13+ built-in; was pgcrypto-only before)
SELECT uuidv7();            -- (pg18+) time-ordered UUID, index-friendly
```

Operator tables, subscripting/slicing, `array_agg`, range bounds & functions, `ANY_VALUE()`
(pg16+): [references/data-types.md](references/data-types.md).

## Quick Reference

| Construct | Purpose | Since |
|---|---|---|
| `INSERT ... ON CONFLICT (c) DO UPDATE SET ... = excluded....` | Atomic upsert | 9.5 (bedrock) |
| `INSERT ... ON CONFLICT DO NOTHING` | Insert-or-ignore | bedrock |
| `... RETURNING col, ...` | Get rows back from a write | bedrock |
| `RETURNING old.col, new.col` | Before/after values | pg18+ |
| `MERGE INTO ... USING ... WHEN MATCHED/NOT MATCHED THEN ...` | Set-based reconcile | pg15+ |
| `MERGE ... WHEN NOT MATCHED BY SOURCE` · `... RETURNING merge_action()` | Source-absent action · returning | pg17+ |
| `WITH cte AS [NOT] MATERIALIZED (...)` | Inlining control | pg12+ |
| `WITH RECURSIVE ...` | Hierarchy/graph traversal | bedrock |
| `WITH x AS (DELETE ... RETURNING) INSERT ...` | Data-modifying CTE | bedrock |
| `func() OVER (PARTITION BY ... ORDER BY ... ROWS/RANGE ...)` | Window function + frame | bedrock |
| `... GROUPS ...` · `EXCLUDE CURRENT ROW/GROUP/TIES` | Frame mode / exclusion | pg11+ |
| `GROUP BY ROLLUP/CUBE/GROUPING SETS (...)` | Multi-level subtotals | bedrock |
| `DISTINCT ON (cols)` | One row per group | bedrock |
| `CROSS JOIN LATERAL (subquery using left cols)` | Correlated join | bedrock |
| `agg(...) FILTER (WHERE ...)` | Per-aggregate filtering | bedrock |
| `GENERATED { ALWAYS \| BY DEFAULT } AS IDENTITY` | SQL-standard auto-increment | pg10+ |
| `GENERATED ALWAYS AS (expr) STORED` · `... VIRTUAL` | Computed column (virtual default) | STORED pg12+ · VIRTUAL pg18+ |
| `PARTITION BY RANGE/LIST` · `... HASH` · `... DEFAULT` | Declarative partitioning | range/list pg10+ · hash/default pg11+ |
| `->` `->>` `#>` `#>>` · `@>` `?` `\|\|` · `@@` `@?` | JSON navigate / test / jsonpath | jsonpath pg12+ |
| `IS JSON` · `JSON_ARRAY/JSON_OBJECT(...)` · `ANY_VALUE()` | JSON predicate / constructors / agg | pg16+ |
| `JSON_TABLE/JSON_QUERY/JSON_VALUE/JSON_EXISTS` · `JSON()/JSON_SCALAR/JSON_SERIALIZE` | SQL/JSON query + constructors | pg17+ |
| `int4multirange`, `'{[1,5],[8,9]}'::...` | Multirange types | pg14+ |
| `gen_random_uuid()` · `uuidv7()`/`uuidv4()` | UUID generation | builtin pg13+ · v7/v4 pg18+ |

## Troubleshooting

- **`syntax error at or near "MERGE"` / `"JSON_TABLE"` / `"MATERIALIZED"`** — the server is older
  than the feature. Check `SHOW server_version` against the `(pgNN+)` tag and
  [references/version-features.md](references/version-features.md). The parser rejects the keyword,
  so it's a version problem, not a typo.
- **`ON CONFLICT` → `there is no unique or exclusion constraint matching the ON CONFLICT
  specification`** — the conflict target must match an actual unique index / constraint (or a
  partial-index predicate). Add the constraint or fix the column list.
- **A `GENERATED AS (...)` column behaves as virtual on pg18 but errored on pg17** — pg18 made
  `VIRTUAL` the default; older servers only support `STORED`. Write `STORED` explicitly for
  portable DDL.
- **`->>` vs `->`** — `->` returns `json`/`jsonb`; `->>` returns `text`. Comparing the result of
  `->` to a string fails or misbehaves; use `->>` (or cast) when you want text.
- **`@>` does nothing useful on a `json` (not `jsonb`) column** — containment/existence operators
  and GIN indexing are `jsonb` features. Store documents you query as `jsonb`.
- **`DISTINCT ON` returns unexpected rows** — the leading `ORDER BY` expressions must start with
  the `DISTINCT ON` columns; otherwise "which row per group" is undefined.
- **Inserting into an `IDENTITY ... GENERATED ALWAYS` column fails** — that's intended; use
  `OVERRIDING SYSTEM VALUE`, or define the column `BY DEFAULT` instead.
- **A row "doesn't fit any partition"** — without a `DEFAULT` partition (pg11+) an out-of-range
  insert errors. Add a default partition or the right range/list partition.

## References

- [references/dml-returning.md](references/dml-returning.md) — `INSERT ... ON CONFLICT` (full
  conflict-target & action grammar, `excluded`, partial-index inference, `DO SELECT` pg19+),
  `RETURNING` incl. `OLD`/`NEW`, the complete `MERGE` grammar with per-version notes, and
  data-modifying CTEs.
- [references/queries.md](references/queries.md) — CTEs (`MATERIALIZED`, recursive, `SEARCH`/
  `CYCLE`), window functions + the full frame-clause grammar, `GROUPING SETS`/`CUBE`/`ROLLUP` +
  `GROUPING()`, `DISTINCT ON`, `LATERAL`, and `FILTER`.
- [references/json.md](references/json.md) — `json` vs `jsonb`, every operator, the jsonpath
  language (pg12+), and the SQL/JSON functions with the precise pg16-vs-pg17 split.
- [references/data-types.md](references/data-types.md) — arrays, ranges & multiranges (pg14+),
  composite/row types, enums, domains, generated & identity columns, and notable functions
  (`gen_random_uuid`, `uuidv7`, `ANY_VALUE`).
- [references/partitioning.md](references/partitioning.md) — declarative partitioning end to end:
  range/list/hash, `DEFAULT`, `ATTACH`/`DETACH`, sub-partitioning, partition-wise plans, pg19
  `MERGE`/`SPLIT`.
- [references/version-features.md](references/version-features.md) — the sourced feature →
  minimum-version table, how to read the `(pgNN+)` tags, and citations.

## Resources

- **SQL command reference**: https://www.postgresql.org/docs/current/sql-commands.html
- **Queries (CTEs, window, grouping)**: https://www.postgresql.org/docs/current/queries.html
- **Data types**: https://www.postgresql.org/docs/current/datatype.html
- **JSON functions & SQL/JSON**: https://www.postgresql.org/docs/current/functions-json.html
- **Release notes (per-version "what's new")**: https://www.postgresql.org/docs/release/
