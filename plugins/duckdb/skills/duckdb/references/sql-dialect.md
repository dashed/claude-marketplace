# DuckDB Friendly-SQL Field Guide

The practical reference for the **ergonomic SQL** that sets DuckDB apart from
standard/PostgreSQL SQL: FROM-first queries, star modifiers, `COLUMNS()`,
`GROUP BY ALL`, `QUALIFY`, `PIVOT`/`UNPIVOT`, advanced joins, nested types with
lambdas and comprehensions, exploration helpers (`SUMMARIZE`/`DESCRIBE`),
sampling, and DDL/DML niceties. For the shell and CLI flags, see
[cli.md](cli.md); for reading/writing files, `COPY`, `ATTACH`, and extensions,
see [data-io.md](data-io.md); for the feature→version lookup, see
[version-features.md](version-features.md).

> **Scope & version note:** DuckDB is broadly **PostgreSQL-compatible** and adds
> a layer of "**Friendly SQL**" on top. **Every example below was run on the
> installed `duckdb` CLI `v1.3.2` (Ossivalis)** and produced the output shown
> unless noted. The Friendly-SQL surface is **bedrock** — it shipped at or
> before the 1.0.0 GA (June 2024) and has been stable for years — so it carries
> **no version tag**. Only the genuinely post-1.0 additions are flagged inline
> as `(duckdb vX.Y+)`, citing the release; features newer than the installed
> 1.3.2 (e.g. `MERGE INTO`, `VARIANT`) could not be run-verified here and rely
> on the duckdb.org release blogs (see [version-features.md](version-features.md)).
> Confirm your build with `duckdb -version`.

## Table of Contents

- [Query Shape: FROM-First & Star Modifiers](#query-shape-from-first--star-modifiers)
- [COLUMNS() — Operate on Many Columns](#columns--operate-on-many-columns)
- [GROUP BY ALL / ORDER BY ALL](#group-by-all--order-by-all)
- [QUALIFY — Filter on Window Functions](#qualify--filter-on-window-functions)
- [PIVOT / UNPIVOT](#pivot--unpivot)
- [Set Operations: UNION BY NAME](#set-operations-union-by-name)
- [Joins: ASOF, POSITIONAL, USING](#joins-asof-positional-using)
- [Nested Types: LIST / STRUCT / MAP / UNION](#nested-types-list--struct--map--union)
- [Lambdas, List Comprehensions & UNNEST](#lambdas-list-comprehensions--unnest)
- [Exploration: SUMMARIZE & DESCRIBE](#exploration-summarize--describe)
- [Sampling: USING SAMPLE](#sampling-using-sample)
- [Literals & Expression Ergonomics](#literals--expression-ergonomics)
- [DDL / DML Ergonomics](#ddl--dml-ergonomics)
- [PREPARE / EXECUTE](#prepare--execute)
- [Friendly Aggregates](#friendly-aggregates)

## Query Shape: FROM-First & Star Modifiers

DuckDB lets the **`FROM` clause come first**, and even stand alone. This is the
single most distinctive Friendly-SQL feature: it reads top-to-bottom in pipeline
order and makes one-liners terse.

```sql
FROM range(3);                  -- bare FROM → implicit SELECT *
FROM my_table;                  -- whole table, no SELECT needed
FROM my_table SELECT name;      -- FROM then SELECT (any clause order)
FROM 'sales.parquet' WHERE region = 'EU';   -- files are tables (see data-io.md)
```

`FROM range(3)` returns a one-column `range` table of `0,1,2`. The classic
`SELECT … FROM …` order still works everywhere — FROM-first is additive.

### `SELECT * EXCLUDE` / `REPLACE`

Modify the `*` star instead of typing every column. Given a table `t(a, b, c)`:

```sql
SELECT * EXCLUDE (b) FROM t;            -- all columns except b → (a, c)
SELECT * REPLACE (a + 100 AS a) FROM t; -- keep all columns, rewrite a in place
```

`EXCLUDE` drops listed columns from the star; `REPLACE` swaps an expression in
for a starred column **without changing column position**. They compose:
`SELECT * EXCLUDE (b) REPLACE (a*2 AS a) FROM t`.

Two more star modifiers for renaming and name-filtering:

```sql
SELECT * RENAME (val AS amount) FROM t; -- rename a starred column (duckdb v1.2+)
SELECT * LIKE 'n%' FROM t;              -- only columns whose name matches (duckdb v1.2+)
```

## COLUMNS() — Operate on Many Columns

`COLUMNS(...)` expands to a set of columns and **applies one expression to every
one of them**. It accepts a regex string, a star, or a lambda predicate on the
column name.

```sql
-- Regex: select every column whose name matches
SELECT COLUMNS('a|b') FROM t;          -- → columns a, b

-- Apply an aggregate across all columns at once
SELECT max(COLUMNS(*)) FROM t;         -- max of a, max of b, max of c

-- Combine two passes (min and max of every column)
SELECT min(COLUMNS(*)), max(COLUMNS(*)) FROM t;

-- Lambda on the column name (duckdb v1.3+ python-style lambda)
SELECT max(COLUMNS(c -> c LIKE 'val')) FROM t;   -- only columns named like val
```

`*COLUMNS(...)` **unpacks** the expanded columns as function arguments rather
than separate output columns *(duckdb v1.1+)*; the `UNPACK(...)` keyword is the
explicit form *(duckdb v1.3+)*:

```sql
SELECT struct_pack(*COLUMNS('val\d'))  FROM t;   -- pack matching cols into a struct
```

## GROUP BY ALL / ORDER BY ALL

Stop hand-listing grouping/ordering keys — `ALL` infers them.

```sql
-- GROUP BY ALL: every non-aggregated SELECT expression becomes a grouping key
SELECT region, sum(amount)
FROM sales
GROUP BY ALL;                  -- == GROUP BY region

-- ORDER BY ALL: order by every selected column, left to right
SELECT * FROM t ORDER BY ALL;  -- ties broken by a, then b, then c
```

`GROUP BY ALL` reads the `SELECT` list, treats anything wrapped in an aggregate
(`sum`, `count`, …) as a measure, and groups by the rest. Add a `HAVING` /
`ORDER BY` as usual. `ORDER BY ALL DESC` and `ORDER BY ALL NULLS LAST` are valid.

## QUALIFY — Filter on Window Functions

`QUALIFY` is to window functions what `HAVING` is to `GROUP BY`: it filters rows
**after** window functions are computed, so you don't need a wrapping subquery.

```sql
-- Keep only the top row per the window's ordering
SELECT a, b, row_number() OVER (ORDER BY b DESC) AS rn
FROM t
QUALIFY rn = 1;

-- Reference the window inline (no alias needed)
SELECT *
FROM sales
QUALIFY rank() OVER (PARTITION BY region ORDER BY amount DESC) <= 3;
```

## PIVOT / UNPIVOT

Reshape long↔wide without the classic `CASE WHEN` boilerplate.

```sql
-- PIVOT: spread distinct values of `yr` into columns, aggregating amt
PIVOT sales ON yr USING sum(amt) GROUP BY region;
--  region │ 2023 │ 2024
--  US     │   20 │   25
--  EU     │   10 │   15
```

`ON` is the column whose values become new columns; `USING` is the aggregate;
`GROUP BY` lists the row keys to keep.

`UNPIVOT` is the inverse — collapse wide columns into name/value rows. Two
equivalent spellings:

```sql
-- Statement form
UNPIVOT wide ON q1, q2, q3 INTO NAME quarter VALUE amt;

-- In-query form (usable anywhere a table is expected)
SELECT * FROM wide
UNPIVOT (amt FOR quarter IN (q1, q2, q3));
--  id │ quarter │ amt
--   1 │ q1      │  10
--   1 │ q2      │  20
--   1 │ q3      │  30
```

Both `PIVOT` and `UNPIVOT` also have a SQL-standard `PIVOT … FOR … IN (…)` form;
the DuckDB-simplified syntax above auto-detects the `IN` list for `PIVOT`.

## Set Operations: UNION BY NAME

`UNION [ALL] BY NAME` aligns inputs by **column name** instead of position,
filling missing columns with `NULL` — ideal for stitching together files with
drifting schemas.

```sql
SELECT 1 AS a, 2 AS b
UNION ALL BY NAME
SELECT 3 AS b, 4 AS a;         -- aligned by name → (a,b) = (1,2) then (4,3)
```

Without `BY NAME`, the second row would line up positionally (`a=3, b=4`). Works
with `UNION`, `UNION ALL`, and across `read_csv`/`read_parquet` inputs that have
differing column orders.

## Joins: ASOF, POSITIONAL, USING

Beyond the standard inner/left/right/full/cross/natural/semi/anti and `LATERAL`
joins, DuckDB adds:

**`ASOF JOIN`** — "as of" / nearest-match join, the workhorse for time series.
For each left row it finds the **closest matching** right row under an
inequality (e.g. most recent quote at-or-before a trade):

```sql
SELECT t.ts, t.sym, q.price
FROM trades t
ASOF JOIN quotes q
  ON t.sym = q.sym AND t.ts >= q.ts;   -- nearest q.ts not after t.ts
```

The final inequality (`>=`, `>`, `<=`, `<`) picks the match direction; equality
predicates (`t.sym = q.sym`) partition the search. `ASOF LEFT JOIN` keeps
unmatched left rows.

**`POSITIONAL JOIN`** — zip two tables row-by-row by ordinal position (no key),
padding the shorter side with `NULL`:

```sql
SELECT * FROM x POSITIONAL JOIN y;     -- row 1↔row 1, row 2↔row 2, …
```

**`USING`** — the standard shorthand when both sides share the key column name;
the joined key appears once in the output:

```sql
SELECT * FROM l JOIN r USING (k);      -- one `k` column, not l.k + r.k
```

## Nested Types: LIST / STRUCT / MAP / UNION

DuckDB has first-class composite types with literal syntax and rich access.

**`LIST`** — ordered, same-type, **1-based** indexing, Python-style slicing:

```sql
SELECT [1, 2, 3, 4, 5]      AS l,
       [1, 2, 3, 4, 5][2]   AS idx,    -- → 2  (1-based!)
       [1, 2, 3, 4, 5][2:4] AS slice;  -- → [2, 3, 4]
-- trailing comma allowed: [1, 2, 3,]
```

**`STRUCT`** — named fields; access by dot or bracket; `.*` expands fields:

```sql
SELECT {'a': 1, 'b': 2}     AS s,
       {'a': 1, 'b': 2}.a   AS field,    -- → 1   (dot access)
       {'a': 1, 'b': 2}['b'] AS bracket; -- → 2   (bracket access)

SELECT s.* FROM (SELECT {'a': 1, 'b': 2} AS s);  -- expand to columns a, b
```

**`MAP`** — dynamic key→value pairs; bracket lookup returns the **value**:

```sql
SELECT map(['k1', 'k2'], [10, 20])        AS m,
       map(['k1', 'k2'], [10, 20])['k1']  AS v;   -- → 10
```

> `map['key']` returns the **value scalar** as of *(duckdb v1.2+)*; earlier
> versions returned a single-element list. Use `map_extract_value(m, 'k')` for
> the explicit form.

**`UNION`** — a tagged union that can hold one of several typed alternatives:

```sql
SELECT union_value(num := 2) AS u;                       -- tag `num` holds 2
SELECT union_extract(union_value(str := 'hi'), 'str');   -- → 'hi'
```

## Lambdas, List Comprehensions & UNNEST

**List comprehensions** read like Python and beat nested function calls for
clarity:

```sql
SELECT [x * 2 FOR x IN [1, 2, 3]]            AS doubled,  -- [2, 4, 6]
       [x FOR x IN [1, 2, 3, 4] IF x % 2 = 0] AS evens;   -- [2, 4]
```

**Lambda functions** power the `list_*` higher-order helpers. Prefer the
Python-style `lambda x: …` syntax *(duckdb v1.3+)*; the older arrow form
`x -> …` still works but emits a deprecation warning as of *(duckdb v1.5+)*.

```sql
SELECT list_transform([1, 2, 3], lambda x: x + 1)  AS r;  -- [2, 3, 4]
SELECT list_filter([1, 2, 3, 4], lambda x: x > 2)  AS r;  -- [3, 4]
SELECT apply([1, 2, 3], lambda x: x * 10)          AS r;  -- [10,20,30] (alias of list_transform)
SELECT reduce([1, 2, 3, 4], lambda acc, x: acc + x) AS total; -- 10
SELECT list_aggregate([1, 2, 3], 'sum')            AS s;  -- 6 (apply a named aggregate)
```

**`UNNEST`** flattens a list into rows (or expands a struct into columns):

```sql
SELECT unnest([1, 2, 3]) AS x;                  -- 3 rows: 1, 2, 3
SELECT unnest({'a': 1, 'b': 2});                -- one row, columns a, b
SELECT unnest([[1, 2], [3, 4]], recursive := true) AS x;  -- fully flatten → 1,2,3,4
```

## Exploration: SUMMARIZE & DESCRIBE

Two commands that make an unknown dataset legible instantly. Both accept a
table, a subquery, or a file (`SUMMARIZE FROM 'data.parquet'`).

```sql
DESCRIBE sales;        -- column_name, column_type, null, key, default, extra
DESCRIBE SELECT …;     -- describe the shape of any query without running it fully
```

```sql
SUMMARIZE sales;       -- per-column stats, one row per column:
-- column_name, column_type, min, max, approx_unique, avg, std,
-- q25, q50, q75, count, null_percentage
```

`SUMMARIZE` is the fastest way to profile a file: min/max ranges, approximate
cardinality, quartiles, and null density in a single pass.

## Sampling: USING SAMPLE

Pull a subset for quick exploration without a full scan. Attach `USING SAMPLE`
to a `FROM`:

```sql
SELECT * FROM t USING SAMPLE 10;             -- 10 rows (reservoir, exact count)
SELECT * FROM t USING SAMPLE 10%;            -- ~10% (system method — approximate)
SELECT * FROM t USING SAMPLE reservoir(10%); -- exact 10% via reservoir
SELECT * FROM t USING SAMPLE 20% (bernoulli);-- name the method (needs a percentage)
```

> **Gotcha (verified on 1.3.2):** a bare percentage like `USING SAMPLE 10%` uses
> the **system** method, which samples at *vector* (≈2048-row) granularity — on a
> small table it can return **0 rows or the whole table**. For a predictable
> count on small data, use a fixed row count (`USING SAMPLE 10`) or
> `reservoir(10%)`. The standard `TABLESAMPLE` spelling is also accepted.

## Literals & Expression Ergonomics

| Feature | Example | Result / note |
|---|---|---|
| **Dollar-quoting** | `SELECT $$a string with 'quotes'$$` | no escaping of inner quotes |
| **Underscores in numbers** | `SELECT 1_000_000` | → `1000000` (readability) |
| **Trailing commas** | `SELECT a, b, FROM t` ; `[1, 2, 3,]` | tolerated in lists/SELECT/VALUES |
| **Colon (prefix) aliases** | `SELECT 1+1 AS total, total*2 AS doubled` | alias reusable later in same SELECT |
| **Lateral column aliases** | `SELECT 10 AS base, base*3 AS triple` | reference an earlier alias in the same `SELECT` |
| **JSON arrows** | `'{"a":1}'->>'a'` (text) · `->` (json) | Postgres-style JSON extraction |

The `name: expr` colon form is an alias prefix *(duckdb v1.2+)*:
`SELECT total: 1 + 1, doubled: total * 2`.

> **Gotcha (verified on 1.3.2):** you **cannot** combine the colon prefix alias
> with a trailing `AS` — `SELECT total: 1+1 AS x` is a **Parser Error**. Pick one
> aliasing style per expression.

## DDL / DML Ergonomics

```sql
-- Idempotent (re)definition — no DROP needed
CREATE OR REPLACE TABLE t AS SELECT 1 AS x;
CREATE OR REPLACE VIEW v AS FROM t WHERE x > 0;

-- CTAS straight from a file (see data-io.md)
CREATE TABLE snapshot AS FROM 'raw.parquet';

-- RETURNING on INSERT/UPDATE/DELETE
INSERT INTO t VALUES (1), (2) RETURNING *;

-- Named function arguments with := (read_csv, read_parquet, …)
SELECT count(*) FROM read_csv('data.csv', header := true);

-- Error-tolerant expressions
SELECT TRY(log(-1));               -- → NULL instead of erroring (duckdb v1.3+)
SELECT try_cast('abc' AS INTEGER); -- → NULL instead of a cast error
```

Other DDL/DML niceties (see [version-features.md](version-features.md) for the
sourced versions):

| Feature | Example | Version |
|---|---|---|
| `SET VARIABLE` / `getvariable()` | `SET VARIABLE x = 5; SELECT getvariable('x')` | duckdb v1.1+ |
| Struct sub-column `ALTER` | `ALTER TABLE t ADD COLUMN s.k INT` | duckdb v1.3+ |
| `MERGE INTO` (upsert, no PK) | `MERGE INTO t USING s ON … WHEN MATCHED …` | duckdb v1.4+ |
| `VARIANT` type | self-describing semi-structured column | duckdb v1.5+ |

## PREPARE / EXECUTE

Parameterized statements with **positional** (`$1`, `$2`) or **named** (`$name`)
parameters — the safe way to template repeated queries.

```sql
-- Positional parameters
PREPARE p AS SELECT $1::int + $2::int AS s;
EXECUTE p(5, 7);              -- → 12

-- Named parameters
PREPARE q AS SELECT $x::int * 2 AS d;
EXECUTE q(x := 21);          -- → 42

DEALLOCATE p;                 -- drop a prepared statement
```

Cast the parameters (`$1::int`) so DuckDB knows their type. The same `$name`
placeholders feed client-library prepared statements too.

## Friendly Aggregates

DuckDB ships analytics-grade aggregates that standard SQL lacks. All confirmed on
1.3.2:

| Aggregate | Example | Returns |
|---|---|---|
| `arg_max(a, b)` / `arg_min(a, b)` | `arg_max(name, val)` | value of `a` at the max/min of `b` |
| `list(x)` | `list(val)` | all values gathered into a `LIST` |
| `string_agg(x, sep)` | `string_agg(name, ',')` | concatenated string |
| `mode(x)` | `mode(name)` | most frequent value |
| `first(x)` / `last(x)` / `any_value(x)` | `first(name)` | one representative value |
| `histogram(x)` | `histogram(name)` | `MAP` of value→count |

Every aggregate also accepts a **`FILTER`** clause to aggregate a subset without
a `CASE`:

```sql
SELECT sum(val) FILTER (WHERE name = 'foo') AS foo_total
FROM t;
```

`arg_max`/`arg_min` are especially handy for "the row with the max" patterns
without a self-join or window — e.g. `arg_max(user_id, score)` gives the top
scorer's id directly.
