# DML: Upsert, RETURNING, MERGE, and Data-Modifying CTEs

Postgres-specific data-modification surface. Version tags: `(pgNN+)` = minimum server version;
untagged = bedrock (stable since 9.x). See [version-features.md](version-features.md).

## Contents

- [INSERT ... ON CONFLICT (upsert)](#insert--on-conflict-upsert)
- [RETURNING](#returning)
- [MERGE](#merge)
- [Data-modifying CTEs](#data-modifying-ctes)

## INSERT ... ON CONFLICT (upsert)

Grammar (current, 19beta1):

```
INSERT INTO table [ AS alias ] [ ( column [, ...] ) ]
    [ OVERRIDING { SYSTEM | USER } VALUE ]
    { DEFAULT VALUES | VALUES (...) [, ...] | query }
    [ ON CONFLICT [ conflict_target ] conflict_action ]
    [ RETURNING ... ]

conflict_target:
    ( { index_column | (index_expression) } [ COLLATE c ] [ opclass ] [, ...] ) [ WHERE index_predicate ]
    ON CONSTRAINT constraint_name

conflict_action:
    DO NOTHING
    DO SELECT [ FOR { UPDATE | NO KEY UPDATE | SHARE | KEY SHARE } ] [ WHERE condition ]   -- (pg19+)
    DO UPDATE SET { col = expr | (col, ...) = (...) } [, ...] [ WHERE condition ]
```

### The conflict target

`ON CONFLICT` needs to know **which** unique index/constraint defines a "conflict" (the *arbiter
index*):

- `ON CONFLICT (email)` — **index inference**: matches the unique index/constraint covering
  exactly column `email` (or an expression like `(lower(email))`).
- `ON CONFLICT (email) WHERE active` — inference against a **partial** unique index; the predicate
  must match.
- `ON CONFLICT ON CONSTRAINT users_email_key` — name a constraint explicitly. (Cannot name a
  non-constraint index this way; use inference for those.)
- `ON CONFLICT DO NOTHING` with **no** target — applies to a conflict on *any* unique constraint.
  `DO UPDATE` always requires a target.

A common error: **`there is no unique or exclusion constraint matching the ON CONFLICT
specification`** means the inferred columns don't line up with a real unique index. Add the
constraint, or match the column list/predicate exactly.

### The `excluded` pseudo-table

Inside `DO UPDATE`, `excluded.*` is the row that *would have been inserted*. Reference the
existing row by table name/alias.

```sql
INSERT INTO inventory AS i (sku, qty, last_seen) VALUES ('A-1', 5, now())
ON CONFLICT (sku) DO UPDATE
  SET qty       = i.qty + excluded.qty,   -- existing + proposed
      last_seen = excluded.last_seen
  WHERE i.qty < 1000;                     -- conditional update; skip if guard fails
```

If the `DO UPDATE ... WHERE` is false, the row is **left untouched** (and not returned by
`RETURNING`).

### Bulk upsert from a query

```sql
INSERT INTO dim_user (id, name)
SELECT id, name FROM staging_user
ON CONFLICT (id) DO UPDATE SET name = excluded.name;
```

### Caveats

- A single statement that tries to upsert **the same key twice** errors with `ON CONFLICT DO
  UPDATE command cannot affect row a second time` — de-duplicate the source first.
- `ON CONFLICT` only resolves **unique/exclusion** conflicts, not other constraint violations
  (NOT NULL, CHECK, FK still raise).
- `ON CONFLICT DO SELECT ... RETURNING` (pg19+, beta) lets you read/lock the conflicting row
  instead of updating it — useful for "insert if absent, otherwise return/lock the existing one."

## RETURNING

Any `INSERT`, `UPDATE`, `DELETE`, or `MERGE` can end with `RETURNING` to emit columns (or
arbitrary expressions) from affected rows — atomic, no separate `SELECT`, no race window.

```sql
INSERT INTO orders (cust_id, total) VALUES (42, 99.5) RETURNING id, created_at;
UPDATE accounts SET balance = balance - 100 WHERE id = 1 RETURNING id, balance;
DELETE FROM sessions WHERE expires < now() RETURNING id;          -- e.g. to enqueue cleanups
```

By default `RETURNING` sees the **resulting** row: new values for `INSERT`/`UPDATE`, the deleted
row for `DELETE`.

### OLD / NEW (pg18+)

pg18 lets the `RETURNING` list reference both the **old** and **new** version of each row via the
special `old` and `new` aliases — invaluable for audit logs and "what changed" diffs.

```sql
-- (pg18+) capture before & after in one statement
UPDATE accounts SET balance = balance + 50 WHERE id = 1
RETURNING old.balance AS before, new.balance AS after, new.balance - old.balance AS delta;
```

For rows that were **inserted**, `old.*` is NULL; for **deleted** rows, `new.*` is NULL. If your
table has actual columns named `old`/`new`, rename the aliases:

```sql
RETURNING WITH (OLD AS o, NEW AS n) o.balance, n.balance;   -- (pg18+)
```

## MERGE

`MERGE` (pg15+) reconciles a **target** table against a **source** in one set-based pass, picking
an action per row. Grammar (current, 19beta1):

```
[ WITH with_query [, ...] ]
MERGE INTO [ ONLY ] target [ * ] [ [ AS ] alias ]
    USING data_source ON join_condition
    when_clause [...]
    [ RETURNING [ WITH ( { OLD | NEW } AS alias [, ...] ) ] { * | expr [ AS name ] } [, ...] ]   -- (pg17+)

when_clause:
    WHEN MATCHED [ AND cond ]                THEN { UPDATE SET ... | DELETE | DO NOTHING }
    WHEN NOT MATCHED BY SOURCE [ AND cond ]  THEN { UPDATE SET ... | DELETE | DO NOTHING }   -- (pg17+)
    WHEN NOT MATCHED [ BY TARGET ] [ AND cond ] THEN { INSERT ... | DO NOTHING }
```

The three match categories:

| Clause | Fires for… | Allowed actions |
|---|---|---|
| `WHEN MATCHED` | rows present in **both** source and target | `UPDATE` / `DELETE` / `DO NOTHING` |
| `WHEN NOT MATCHED [BY TARGET]` | source rows with **no** target match | `INSERT` / `DO NOTHING` |
| `WHEN NOT MATCHED BY SOURCE` (pg17+) | target rows with **no** source match | `UPDATE` / `DELETE` / `DO NOTHING` |

Clauses are evaluated **top-down per row**; the first whose optional `AND condition` matches wins.
`DO NOTHING` skips the row.

### Examples

```sql
-- Basic upsert-style merge (pg15+)
MERGE INTO inventory AS t
USING shipments AS s ON t.sku = s.sku
WHEN MATCHED THEN UPDATE SET qty = t.qty + s.qty
WHEN NOT MATCHED THEN INSERT (sku, qty) VALUES (s.sku, s.qty);

-- Full three-way sync with conditions, deletes, and RETURNING (pg17+)
MERGE INTO target AS t
USING (SELECT * FROM source) AS s ON t.id = s.id
WHEN MATCHED AND s.deleted THEN DELETE
WHEN MATCHED               THEN UPDATE SET val = s.val
WHEN NOT MATCHED           THEN INSERT (id, val) VALUES (s.id, s.val)
WHEN NOT MATCHED BY SOURCE THEN DELETE                       -- prune target rows source dropped
RETURNING merge_action(), t.id, t.val;                       -- 'INSERT' | 'UPDATE' | 'DELETE'
```

- `merge_action()` (pg17+) returns the action that produced each `RETURNING` row.
- `WHEN NOT MATCHED BY SOURCE` clauses can only reference **target** columns (there's no matching
  source row); `WHEN NOT MATCHED [BY TARGET]` clauses can only reference **source** columns.
- `MERGE` can target an **updatable view** as of pg17.
- **`WHEN NOT MATCHED BY SOURCE`, the `DO NOTHING` action, and `RETURNING` are PostgreSQL
  extensions** to the SQL standard (per the command's Compatibility notes).

### MERGE vs ON CONFLICT

| | `INSERT ... ON CONFLICT` | `MERGE` (pg15+) |
|---|---|---|
| Mental model | "insert these rows, resolve clashes" | "reconcile a source against a target" |
| Requires a unique/exclusion constraint? | **Yes** (the arbiter index) | No — any join condition |
| Can DELETE target rows? | No | Yes (incl. `NOT MATCHED BY SOURCE`, pg17+) |
| Concurrency | designed to be safe under concurrent inserts | standard row locking; can raise serialization/`cardinality` errors under concurrency |
| Source-absent handling | n/a | `WHEN NOT MATCHED BY SOURCE` (pg17+) |

Prefer `ON CONFLICT` for high-concurrency idempotent inserts; prefer `MERGE` for batch ETL
reconciliation with deletes and rich per-row logic.

## Data-modifying CTEs

A `WITH` clause may contain `INSERT`/`UPDATE`/`DELETE`/`MERGE` (each typically with `RETURNING`),
and the top-level query reads their output. The whole statement is **one snapshot** — all
sub-statements see the same starting state — which makes it ideal for atomic "move" operations.

```sql
-- Archive-then-delete in one atomic statement
WITH moved AS (
  DELETE FROM events WHERE ts < now() - interval '1 year'
  RETURNING *
)
INSERT INTO events_archive SELECT * FROM moved;

-- Insert a parent and its children together, threading the generated id
WITH new_order AS (
  INSERT INTO orders (cust_id) VALUES (42) RETURNING id
)
INSERT INTO order_items (order_id, sku, qty)
SELECT new_order.id, x.sku, x.qty
FROM new_order, (VALUES ('A-1', 2), ('B-2', 1)) AS x(sku, qty);
```

Important semantics:

- All sub-statements run against the **same snapshot**, so a data-modifying CTE does **not** see
  the effects of a sibling CTE's changes. (To chain dependent writes, pass values via
  `RETURNING`, as above.)
- The execution **order** of multiple data-modifying CTEs is not guaranteed; don't rely on one
  running before another except through data flow (`RETURNING` → referenced).
- A `WITH` query that modifies data and is **not referenced** by the primary statement is still
  executed (run to completion). Recursion (`WITH RECURSIVE`) cannot be used with data-modifying
  statements.

## Sources

- `INSERT`: <https://www.postgresql.org/docs/current/sql-insert.html> · in-repo `ref/insert.sgml`
- `MERGE`: <https://www.postgresql.org/docs/current/sql-merge.html> · in-repo `ref/merge.sgml`
- `RETURNING`: <https://www.postgresql.org/docs/current/dml-returning.html>
- pg17 (`MERGE RETURNING`/`NOT MATCHED BY SOURCE`/views), pg18 (`RETURNING old`/`new`), pg19beta
  (`ON CONFLICT DO SELECT`) — Appendix E release notes (see [version-features.md](version-features.md)).
