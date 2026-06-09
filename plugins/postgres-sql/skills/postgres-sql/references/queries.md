# Query Constructs: CTEs, Windows, Grouping, LATERAL, FILTER, DISTINCT ON

Postgres-specific query syntax (not tuning — for `EXPLAIN`/indexes see the **postgres-performance**
skill). Version tags `(pgNN+)` = minimum server version; untagged = bedrock.

## Contents

- [CTEs (WITH)](#ctes-with)
- [Recursive CTEs](#recursive-ctes)
- [Window functions & frame clauses](#window-functions--frame-clauses)
- [GROUPING SETS / ROLLUP / CUBE](#grouping-sets--rollup--cube)
- [DISTINCT ON](#distinct-on)
- [LATERAL](#lateral)
- [FILTER](#filter)

## CTEs (WITH)

A `WITH` clause defines named subqueries (CTEs) usable in the main statement. Beyond readability,
Postgres CTEs have a specific **materialization** behavior worth understanding:

- **pg12+**: a CTE is **inlined** (folded into the outer query, so the planner can optimize across
  the boundary) when it is **non-recursive, side-effect-free, and referenced exactly once**.
  Before pg12, CTEs were *always* an optimization fence (computed once, separately).
- `MATERIALIZED` (pg12+) forces the old behavior: compute the CTE once into a temporary result —
  an **optimization barrier**. Useful to (a) reuse an expensive subquery referenced many times, or
  (b) deliberately stop the planner from pushing predicates down (e.g. to force evaluation order,
  or guard a volatile function).
- `NOT MATERIALIZED` (pg12+) forces inlining even when referenced multiple times.

```sql
WITH regional AS MATERIALIZED (                 -- compute once, scan twice below
  SELECT region, sum(amount) AS total FROM sales GROUP BY region
)
SELECT * FROM regional WHERE total > 1000
UNION ALL
SELECT 'TOTAL', sum(total) FROM regional;
```

Rule of thumb: reach for `MATERIALIZED` when a CTE is expensive **and** reused, or when inlining
changes results/performance for the worse; reach for `NOT MATERIALIZED` when a single-use fence is
hurting the plan on an older mindset. Default (unannotated) behavior is usually right on pg12+.

## Recursive CTEs

`WITH RECURSIVE` walks hierarchies and graphs: an **anchor** term `UNION [ALL]` a **recursive**
term that references the CTE itself.

```sql
WITH RECURSIVE tree AS (
  SELECT id, parent_id, name, 1 AS depth          -- anchor: roots
  FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.parent_id, c.name, t.depth + 1   -- recursive term
  FROM categories c JOIN tree t ON c.parent_id = t.id
)
SELECT * FROM tree ORDER BY depth;
```

For **graphs with cycles**, use the `SEARCH` and `CYCLE` clauses (pg14+) instead of hand-rolling a
visited-path array:

```sql
WITH RECURSIVE g AS (
  SELECT id, next_id FROM edges WHERE id = 1
  UNION ALL
  SELECT e.id, e.next_id FROM edges e JOIN g ON e.id = g.next_id
)
SEARCH DEPTH FIRST BY id SET ordercol            -- (pg14+) adds an ordering column
CYCLE id SET is_cycle USING path                 -- (pg14+) stop + flag cycles
SELECT * FROM g;
```

- `SEARCH DEPTH FIRST BY col SET seqcol` / `SEARCH BREADTH FIRST BY col SET seqcol` add a column
  you can `ORDER BY` to get a true depth/breadth traversal order.
- `CYCLE col SET flag_col USING path_col` detects cycles on `col`: stops recursing when a row
  repeats, sets `flag_col` true, and exposes the visited `path_col` array.
- `UNION` (vs `UNION ALL`) deduplicates and can itself prevent infinite loops on simple graphs,
  but `CYCLE` is the robust tool.

## Window functions & frame clauses

Window functions compute over a set of rows related to the current row **without collapsing** them
(unlike `GROUP BY`). Define the window inline with `OVER (...)` or name it in a `WINDOW` clause.

```sql
SELECT
  dept, employee, salary,
  rank()        OVER w                              AS dept_rank,
  salary - avg(salary) OVER w                       AS diff_from_avg,
  lag(salary, 1) OVER (PARTITION BY dept ORDER BY hired) AS prev_hire_salary
FROM staff
WINDOW w AS (PARTITION BY dept ORDER BY salary DESC);
```

Common window functions: ranking `row_number()`, `rank()`, `dense_rank()`, `ntile(n)`,
`percent_rank()`, `cume_dist()`; navigation `lag()`, `lead()`, `first_value()`, `last_value()`,
`nth_value()`; plus any aggregate used as a window (`sum`, `avg`, `count`, …).

### The frame clause

The frame restricts which peer rows an aggregate/`first_value`/`last_value` sees. Grammar (current):

```
{ RANGE | ROWS | GROUPS } frame_start [ frame_exclusion ]
{ RANGE | ROWS | GROUPS } BETWEEN frame_start AND frame_end [ frame_exclusion ]

frame_start / frame_end:
    UNBOUNDED PRECEDING | offset PRECEDING | CURRENT ROW | offset FOLLOWING | UNBOUNDED FOLLOWING

frame_exclusion:                                 -- (pg11+)
    EXCLUDE CURRENT ROW | EXCLUDE GROUP | EXCLUDE TIES | EXCLUDE NO OTHERS
```

- **`ROWS`** counts physical rows; **`RANGE`** groups by the `ORDER BY` *value* (peers with the
  same value share a frame edge); **`GROUPS`** (pg11+) counts *peer groups*.
- Frame **exclusion** (`EXCLUDE ...`, pg11+) removes the current row / its peers from an otherwise
  matching frame.
- Default frame (no clause) with an `ORDER BY` is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT
  ROW`; with no `ORDER BY`, the frame is the whole partition.

```sql
-- 7-row moving average (physical rows) — ROWS frames are bedrock
avg(price) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)

-- value-based running window: all rows within the last 7 days of the current row's day.
-- RANGE with an *offset* distance (PRECEDING/FOLLOWING) is pg11+; plain RANGE UNBOUNDED/CURRENT ROW is bedrock.
sum(amount) OVER (ORDER BY day RANGE BETWEEN '7 days' PRECEDING AND CURRENT ROW)  -- (pg11+)

-- peer-group window excluding the current row's ties (pg11+)
sum(x) OVER (ORDER BY g GROUPS BETWEEN 1 PRECEDING AND 1 FOLLOWING EXCLUDE CURRENT ROW)  -- (pg11+)
```

`RANGE`/`GROUPS` with an `offset PRECEDING/FOLLOWING` (pg11+) require a single `ORDER BY` column of
a type that supports addition (numeric, date/time + `interval`, etc.). Note the full SQL:2011 frame
surface — `GROUPS` mode, frame exclusion, **and** `RANGE` offset distances — all arrived together in
**pg11**; before that, `RANGE` supported only `UNBOUNDED PRECEDING/FOLLOWING` and `CURRENT ROW`.

## GROUPING SETS / ROLLUP / CUBE

Produce multiple grouping levels (subtotals/grand totals) in a single pass, instead of `UNION
ALL`-ing several `GROUP BY` queries.

```sql
SELECT region, product, sum(sales) AS total
FROM sales
GROUP BY GROUPING SETS ((region, product), (region), ());   -- detail, per-region, grand total
```

- `ROLLUP (a, b, c)` ≡ the grouping sets `(a,b,c), (a,b), (a), ()` — hierarchical subtotals.
- `CUBE (a, b)` ≡ `(a,b), (a), (b), ()` — all combinations.
- Combine/nest: `GROUP BY a, ROLLUP(b, c)`, `GROUP BY CUBE(a,b), GROUPING SETS(...)`, etc.

The `GROUPING(col, ...)` function disambiguates real NULLs from "aggregated away" NULLs in
subtotal rows (it returns a bitmask; `1` = the column was rolled up):

```sql
SELECT
  CASE WHEN GROUPING(region) = 1 THEN 'ALL REGIONS' ELSE region END AS region,
  sum(sales)
FROM sales GROUP BY ROLLUP (region);
```

## DISTINCT ON

`SELECT DISTINCT ON (expr, ...)` keeps the **first row of each group** defined by `expr` — the
canonical "latest/best row per key" idiom. The `ORDER BY` **must begin** with the same `DISTINCT
ON` expressions; subsequent `ORDER BY` keys decide *which* row wins.

```sql
-- Most recent payment per user
SELECT DISTINCT ON (user_id) user_id, amount, ts
FROM payments
ORDER BY user_id, ts DESC;        -- ts DESC → "latest" wins within each user_id
```

If `ORDER BY` doesn't lead with the `DISTINCT ON` keys, *which* row survives is arbitrary —
Postgres will error or return an unpredictable row. `DISTINCT ON` is a PostgreSQL extension (not
standard SQL); the standard-portable alternative is a window-function/`row_number()` filter.

## LATERAL

A `LATERAL` subquery (or set-returning function) in `FROM` may reference columns of preceding
`FROM` items — a **correlated join**. Without `LATERAL`, a subquery in `FROM` cannot see sibling
tables. (Set-returning functions in `FROM` are implicitly lateral.)

```sql
-- Top-3 orders per customer (a "lateral top-N")
SELECT c.id, c.name, o.total, o.placed_at
FROM customers c
CROSS JOIN LATERAL (
  SELECT total, placed_at FROM orders o
  WHERE o.cust_id = c.id
  ORDER BY total DESC LIMIT 3
) o;

-- LEFT JOIN LATERAL keeps customers with zero orders
SELECT c.id, o.total
FROM customers c
LEFT JOIN LATERAL (SELECT total FROM orders WHERE cust_id = c.id ORDER BY placed_at DESC LIMIT 1) o
  ON true;                         -- ON true is the usual join condition for LATERAL
```

`LATERAL` shines for per-row top-N, unnesting correlated arrays, and calling table functions with
arguments drawn from the outer row (e.g. `... , LATERAL jsonb_array_elements(t.doc) e`).

## FILTER

`FILTER (WHERE condition)` restricts which rows feed a **single aggregate** — cleaner and often
faster than `sum(CASE WHEN cond THEN 1 ELSE 0 END)`. Works for any aggregate, including as a window.

```sql
SELECT
  count(*)                              AS total,
  count(*) FILTER (WHERE status = 'paid')   AS paid,
  count(*) FILTER (WHERE status = 'refunded') AS refunded,
  avg(amount) FILTER (WHERE amount > 0)     AS avg_positive
FROM orders;
```

`FILTER` composes with `GROUP BY`, `GROUPING SETS`, and `OVER (...)` windows.

## Sources

- Queries chapter (CTEs, window, grouping): <https://www.postgresql.org/docs/current/queries.html>
- `SELECT` (frame clause, `DISTINCT ON`, `LATERAL`): <https://www.postgresql.org/docs/current/sql-select.html> · in-repo `ref/select.sgml`, `queries.sgml`
- pg11 (`GROUPS`/frame exclusion), pg12 (CTE inlining + `MATERIALIZED`), pg14 (`SEARCH`/`CYCLE`) — Appendix E (see [version-features.md](version-features.md)).
