# Data Types & Type-Shaped DDL

Postgres's distinctive type system, plus the column-definition features tied to it (generated &
identity columns) and a few functions that shifted versions. JSON lives in
[json.md](json.md); partitioning in [partitioning.md](partitioning.md). Version tags `(pgNN+)` =
minimum server version; untagged = bedrock.

## Contents

- [Arrays](#arrays)
- [Ranges & multiranges](#ranges--multiranges)
- [Composite / row types](#composite--row-types)
- [Enums](#enums)
- [Domains](#domains)
- [Generated columns](#generated-columns)
- [Identity columns vs serial](#identity-columns-vs-serial)
- [Notable functions](#notable-functions)

## Arrays

Any type has an array variant (`int[]`, `text[]`, `jsonb[]`, multidimensional `int[][]`). Arrays
are bedrock.

```sql
CREATE TABLE post (id int, tags text[]);
INSERT INTO post VALUES (1, ARRAY['sql','postgres']), (2, '{db,oss}');  -- ARRAY[] or '{...}' literal
```

| Operation | Syntax |
|---|---|
| Element (1-based!) / slice | `tags[1]` · `tags[2:3]` |
| Contains / contained / overlaps | `a @> b` · `a <@ b` · `a && b` |
| Membership | `'sql' = ANY(tags)` · `'sql' <> ALL(tags)` |
| Length / append / concat | `array_length(tags,1)` · `array_append(tags,'x')` · `a \|\| b` |
| Expand to rows / collapse rows | `unnest(tags)` · `array_agg(x)` |
| Build / position / remove | `array[...]` · `array_position(a,'x')` · `array_remove(a,'x')` |

```sql
SELECT * FROM post WHERE tags @> ARRAY['sql'];           -- has the 'sql' tag (GIN-indexable)
SELECT id, t FROM post, LATERAL unnest(tags) AS t;       -- one row per tag
SELECT array_agg(DISTINCT tag ORDER BY tag) FROM ...;    -- rows → array, ordered & deduped
```

Note: array **subscripts are 1-based** (unlike JSON arrays, which are 0-based). `= ANY(array)`
is also the idiomatic replacement for a long `IN (...)` list, and accepts a parameter (`= ANY($1)`).

## Ranges & multiranges

Range types hold an interval of a base type with inclusive/exclusive bounds. Built-ins:
`int4range`, `int8range`, `numrange`, `tsrange`, `tstzrange`, `daterange` (all bedrock). Each has a
corresponding **multirange** type (pg14+): `int4multirange`, `tstzmultirange`, etc.

```sql
SELECT int4range(1, 10);                 -- '[1,10)'  lower-inclusive, upper-exclusive (default)
SELECT '[2026-01-01,2026-04-01)'::daterange @> '2026-02-15'::date;   -- containment → true
SELECT numrange(1,5) && numrange(4,8);   -- overlap → true
SELECT upper(r), lower(r), isempty(r) FROM ...;          -- bound accessors
```

Range operators: `@>` (contains element/range), `&&` (overlap), `-|-` (adjacent), `<<`/`>>`
(strictly left/right of), `+` `*` `-` (union/intersection/difference). The classic use is a
**no-overlap exclusion constraint**:

```sql
CREATE TABLE booking (
  room    int,
  during  tsrange,
  EXCLUDE USING gist (room WITH =, during WITH &&)   -- two bookings can't overlap the same room
);
```

**Multiranges** (pg14+) are ordered sets of nonoverlapping ranges — they let a single value model
"availability with gaps":

```sql
SELECT '{[1,5], [10,20]}'::int4multirange;                       -- (pg14+)
SELECT '{[1,5]}'::int4multirange + '{[10,20]}'::int4multirange;  -- (pg14+) union
SELECT multirange(numrange(1,5));                                -- (pg14+) construct from a range
-- pg19beta adds range_minus_multi()/multirange_minus_multi() for gap-producing subtraction
```

## Composite / row types

A composite type is a named row structure; every table also defines a composite type of its own
name. Useful for returning structured values and for functions.

```sql
CREATE TYPE addr AS (street text, city text, zip text);
CREATE TABLE person (id int, home addr);
INSERT INTO person VALUES (1, ROW('1 Main', 'NYC', '10001'));
SELECT (home).city FROM person;            -- parenthesize then .field
SELECT (p.home).* FROM person p;           -- expand all fields
```

Anonymous `ROW(...)` values, `(a, b) = (1, 2)` row comparisons, and `(col).*` expansion are all
bedrock. A composite column is distinct from a `jsonb` column: it's strongly typed with fixed
fields.

## Enums

```sql
CREATE TYPE mood AS ENUM ('sad', 'ok', 'happy');   -- ordering follows declaration order
ALTER TYPE mood ADD VALUE 'ecstatic' AFTER 'happy'; -- add a label (cannot remove labels)
SELECT 'sad'::mood < 'happy'::mood;                 -- true (ordered by definition)
```

Enums (bedrock since 8.3) are stored compactly and sort in declaration order. You can `ADD VALUE`
(optionally `BEFORE`/`AFTER`); you **cannot drop or reorder** labels. Prefer enums over a
`CHECK (x IN (...))` when the set is stable and you want type safety.

## Domains

A domain is a base type plus constraints/default — reusable, named validation.

```sql
CREATE DOMAIN positive_int AS int CHECK (VALUE > 0);
CREATE DOMAIN email AS text CHECK (VALUE ~ '^[^@]+@[^@]+$') NOT NULL;
CREATE TABLE acct (id positive_int, contact email);
```

`VALUE` is the placeholder for the checked value. Domain constraints are enforced on
insert/update/cast. (pg19beta lets `IS JSON` work on domains over supported base types.)

## Generated columns

A generated column is computed from other columns in the same row; it **cannot be written
directly**.

```sql
CREATE TABLE product (
  price     numeric,
  tax_rate  numeric,
  -- STORED: materialized on write, occupies storage, can be indexed normally
  total     numeric GENERATED ALWAYS AS (price * (1 + tax_rate)) STORED   -- (pg12+)
);
```

- **`STORED`** (pg12+) — value is computed and written to disk; behaves like a normal column for
  indexing.
- **`VIRTUAL`** (pg18+) — value is computed **on read**, occupies no storage (like a view column).
- **Behavior change in pg18:** `VIRTUAL` is now the **default** kind, so a bare `GENERATED ALWAYS
  AS (expr)` is *virtual* on pg18+ but was an error (no default) before. **Always write `STORED`
  explicitly** when you need stored semantics and want DDL that behaves identically across versions.
- The expression must be immutable and may only reference other columns of the same row (no
  subqueries, no other rows, no volatile functions).

## Identity columns vs serial

```sql
CREATE TABLE t (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   -- (pg10+) SQL-standard auto-increment
  ...
);
```

- `GENERATED ALWAYS AS IDENTITY` (pg10+) blocks user-supplied values (override with `INSERT ...
  OVERRIDING SYSTEM VALUE`). `GENERATED BY DEFAULT AS IDENTITY` (pg10+) allows them (handy for data
  loads / replication). Tune the backing sequence with `(START WITH ... INCREMENT BY ...)`.
- **Prefer identity over `serial`/`bigserial`.** `serial` is not a real type — it's sugar that
  creates a separate sequence with looser ownership semantics, doesn't enforce "no manual inserts,"
  and isn't SQL-standard. Identity columns are cleaner, standard, and the recommended default on
  pg10+.
- pg18+ also adds **temporal** uniqueness: `PRIMARY KEY`/`UNIQUE (... , period WITHOUT OVERLAPS)`
  and foreign keys with `PERIOD` — range-aware constraints (useful with the range types above).

## Notable functions

| Function | Returns | Notes |
|---|---|---|
| `gen_random_uuid()` | random v4 UUID | **built-in pg13+** (previously needed the `pgcrypto` extension) |
| `uuidv4()` | random v4 UUID | (pg18+) explicit alias |
| `uuidv7()` | time-ordered UUID | (pg18+) **temporally sortable** → far better index locality than v4 for PKs |
| `ANY_VALUE(expr)` | one arbitrary value from the group | (pg16+) lets you select a non-grouped column without a dummy aggregate |

```sql
SELECT gen_random_uuid();                         -- (pg13+ built-in) random UUID, no extension
INSERT INTO t (id) VALUES (uuidv7());             -- (pg18+) sortable UUID PK
SELECT dept, ANY_VALUE(manager), count(*)         -- (pg16+) manager need not be in GROUP BY
FROM staff GROUP BY dept;
```

For UUID **primary keys**, `uuidv7()` (pg18+) is strongly preferred over `gen_random_uuid()`/v4:
its leading timestamp keeps inserts roughly sequential, avoiding the index-fragmentation that
random v4 keys cause.

## Sources

- Data types chapter: <https://www.postgresql.org/docs/current/datatype.html> · in-repo `datatype.sgml`
- Arrays / ranges: <https://www.postgresql.org/docs/current/arrays.html> · `.../rangetypes.html` · in-repo `arrays.sgml`, `rangetypes.sgml`
- Generated & identity columns: <https://www.postgresql.org/docs/current/ddl-generated-columns.html> · `.../ddl-identity-columns.html` · in-repo `ddl.sgml`
- UUID / aggregate functions: <https://www.postgresql.org/docs/current/functions-uuid.html> · `.../functions-aggregate.html`
- pg10 (identity), pg12 (`STORED`), pg13 (built-in `gen_random_uuid`), pg14 (multiranges), pg16 (`ANY_VALUE`), pg18 (`VIRTUAL`+default, `uuidv7`/`uuidv4`, temporal) — Appendix E (see [version-features.md](version-features.md)).
