# PostgreSQL SQL Feature → Minimum Version

A consolidated lookup of **which PostgreSQL major version introduced each SQL-dialect construct,
data type, or function** this skill documents — so you know what works on an older (or newer)
server. Use it to answer "is my server new enough for X?" and "what do I need to upgrade to?"

## How to read this

- These are **PostgreSQL major versions** (`10`, `11`, …, `18`; **`19` is currently in beta**).
  Since PostgreSQL 10, the first number *is* the major version (one major release per year);
  before that, majors looked like `9.4`, `9.5`, `9.6`. The `pg15+` form means "the PostgreSQL 15
  release and later."
- **SQL features ship on major versions only.** Minor releases (e.g. 16.1, 16.2) are
  bug/security fixes — they never add SQL syntax. So a feature tagged `pg17+` simply will not
  parse on any 16.x server; you must upgrade the major version.
- **Bedrock = stable since the 9.x era.** Anything present and stable at or before the **9.x**
  series (through 9.6, 2016) is treated as long-standing and carries **no version tag** in the
  skill ("unlisted = long-standing"). The interesting, taggable surface starts at **pg10**.
- **Verify, don't guess.** Every row below is sourced from the official PostgreSQL **release
  notes** (Appendix E) and/or the **SQL command reference**, cross-checked against the in-repo
  **19beta1** SGML docs (`doc/src/sgml/`). A feature without a clean "added in version N" source
  is treated as bedrock and **omitted** rather than guessed.
- The in-repo dev tree is **19beta1**; pg19 rows are **beta** and subject to change before GA.

### What's bedrock (intentionally untagged)

These are present since 9.x and appear in the skill **without** a tag:

- `INSERT ... ON CONFLICT DO UPDATE/NOTHING` + `excluded` (9.5) and `RETURNING` (8.2)
- `WITH` / `WITH RECURSIVE` CTEs and **data-modifying** CTEs (`WITH ... DELETE/UPDATE/INSERT ...
  RETURNING`) (9.1)
- Window functions with `PARTITION BY`/`ORDER BY` and `ROWS`/`RANGE` frames; the `WINDOW` clause
  (9.0)
- `GROUPING SETS` / `CUBE` / `ROLLUP` + `GROUPING()` (9.5)
- `DISTINCT ON` (very old); `LATERAL` joins (9.3); aggregate `FILTER (WHERE ...)` (9.4)
- `serial`/`bigserial`; exclusion constraints (`EXCLUDE USING gist`) (9.0–9.2)
- `json` (9.2) and `jsonb` (9.4) types; operators `->` `->>` `#>` `#>>` (9.3/9.4), `jsonb`
  containment/existence `@>` `<@` `?` `?|` `?&` and `||` `-` (9.4/9.5)
- Array types & operators (`@>`, `&&`, `ANY`/`ALL`, `unnest`, `array_agg`, subscripting/slicing)
- Range types (`int4range`, `tsrange`, …) and range operators (9.2)
- Composite/row types, `ENUM` types (8.3), `DOMAIN` types
- `gen_random_uuid()` via the `pgcrypto` extension (the **built-in** is pg13+, see below)

## Versioned features (ascending by PostgreSQL release)

Grouped within each release by **Area** (DML / queries / DDL & types / JSON / functions).

| Min version | Feature | Area |
|---|---|---|
| pg10+ | Identity columns `GENERATED { ALWAYS \| BY DEFAULT } AS IDENTITY` (SQL-standard auto-increment) | DDL & types |
| pg10+ | Declarative partitioning — `PARTITION BY RANGE` / `LIST`, `PARTITION OF`, `FOR VALUES` | DDL & types |
| pg11+ | Hash partitioning — `PARTITION BY HASH (...)` `FOR VALUES WITH (MODULUS m, REMAINDER r)` | DDL & types |
| pg11+ | `DEFAULT` partition (catch-all for unrouted rows) | DDL & types |
| pg11+ | Indexes/PKs declared on the partitioned (parent) table propagate to partitions | DDL & types |
| pg11+ | Window frame `GROUPS` mode | queries |
| pg11+ | Window frame `RANGE` with an *offset* distance (`offset PRECEDING`/`FOLLOWING`) — plain `RANGE UNBOUNDED/CURRENT ROW` is bedrock | queries |
| pg11+ | Window frame exclusion — `EXCLUDE CURRENT ROW` / `GROUP` / `TIES` / `NO OTHERS` | queries |
| pg12+ | CTE materialization control — `WITH x AS MATERIALIZED (...)` / `NOT MATERIALIZED` (CTEs auto-inline by default since 12) | queries |
| pg12+ | `jsonpath` type + SQL/JSON path language; operators `@@` / `@?`; `jsonb_path_query()` family | JSON |
| pg13+ | `gen_random_uuid()` as a **built-in** (no `pgcrypto` extension needed) | functions |
| pg14+ | CTE recursive `SEARCH` / `CYCLE` clauses | queries |
| pg14+ | **Multirange** types (`int4multirange`, `tstzmultirange`, …) — ordered sets of nonoverlapping ranges | DDL & types |
| pg14+ | `ALTER TABLE ... DETACH PARTITION ... CONCURRENTLY` (and `FINALIZE`) | DDL & types |
| pg15+ | `MERGE` — set-based `INSERT`/`UPDATE`/`DELETE` (`WHEN MATCHED` / `WHEN NOT MATCHED [BY TARGET]`, `DO NOTHING`) | DML |
| pg16+ | `IS JSON` predicate (value / scalar / object / array / `WITH UNIQUE KEYS`) | JSON |
| pg16+ | SQL/JSON constructors `JSON_ARRAY()`, `JSON_ARRAYAGG()`, `JSON_OBJECT()`, `JSON_OBJECTAGG()` | JSON |
| pg16+ | `ANY_VALUE()` aggregate | functions |
| pg17+ | SQL/JSON query functions `JSON_TABLE()`, `JSON_QUERY()`, `JSON_VALUE()`, `JSON_EXISTS()` | JSON |
| pg17+ | SQL/JSON constructors `JSON()`, `JSON_SCALAR()`, `JSON_SERIALIZE()` | JSON |
| pg17+ | `MERGE ... RETURNING` + `merge_action()` | DML |
| pg17+ | `MERGE ... WHEN NOT MATCHED BY SOURCE` | DML |
| pg17+ | `MERGE` on updatable views | DML |
| pg18+ | `RETURNING` can reference `OLD` and `NEW` rows (`RETURNING old.col, new.col`; aliasable via `WITH (OLD AS ..., NEW AS ...)`) | DML |
| pg18+ | **Virtual** generated columns `GENERATED ALWAYS AS (...) VIRTUAL` — and `VIRTUAL` becomes the **default** kind *(behavior change: a bare `GENERATED ALWAYS AS (...)` is virtual on 18+)* | DDL & types |
| pg18+ | `uuidv7()` (time-ordered UUID) and `uuidv4()` functions | functions |
| pg18+ | Temporal constraints — `PRIMARY KEY`/`UNIQUE ... WITHOUT OVERLAPS`, foreign keys with `PERIOD` | DDL & types |
| pg19+ (beta) | `INSERT ... ON CONFLICT DO SELECT [FOR UPDATE/SHARE] ... RETURNING` | DML |
| pg19+ (beta) | `ALTER TABLE ... MERGE PARTITIONS (...)` and `... SPLIT PARTITION ...` | DDL & types |
| pg19+ (beta) | `IS JSON` predicate works on `DOMAIN` types over supported base types | JSON |
| pg19+ (beta) | `range_minus_multi()` / `multirange_minus_multi()` (subtraction yielding gaps) | functions |
| pg19+ (beta) | `COPY TO` directly on a partitioned table | DML |

## The precise SQL/JSON split (pg16 vs pg17)

This trips people up, so it is spelled out. The SQL/JSON standard features were famously reverted
from PostgreSQL 15 before release, then landed across two majors:

- **pg16** added the **`IS JSON` predicate** and the **constructor functions** `JSON_ARRAY()`,
  `JSON_ARRAYAGG()`, `JSON_OBJECT()`, `JSON_OBJECTAGG()`.
- **pg17** added the **query functions** `JSON_TABLE()`, `JSON_QUERY()`, `JSON_VALUE()`,
  `JSON_EXISTS()` **and** the constructors `JSON()`, `JSON_SCALAR()`, `JSON_SERIALIZE()`.

So `JSON()`/`JSON_SCALAR()`/`JSON_SERIALIZE()` are **pg17**, not pg16 — a common mis-pin. The
older `jsonpath` language and its `@@`/`@?` operators are separate and date to **pg12**.

## Checking your version

```sql
SELECT version();                                     -- full build string
SHOW server_version;                                  -- e.g. 18.0
SELECT current_setting('server_version_num')::int;    -- e.g. 180000 — easy numeric compare
```

```bash
psql -tAc 'show server_version_num'                   -- 170000 = v17.0, 160000 = v16.0, ...
```

`server_version_num` encodes the version as `MMmm00` (major·minor): `180000` = 18.0, `170004` =
17.4. SQL syntax depends only on the **major** (the first one/two digits), so compare against the
floor in the table — e.g. `MERGE` needs `>= 150000`, the SQL/JSON query functions need
`>= 170000`.

## Sources

- **PostgreSQL release notes (Appendix E)**, per major version:
  - pg10 — <https://www.postgresql.org/docs/10/release-10.html> (identity columns, declarative partitioning)
  - pg11 — <https://www.postgresql.org/docs/11/release-11.html> (hash partitioning, default partition, partitioned indexes, `GROUPS`/frame exclusion)
  - pg12 — <https://www.postgresql.org/docs/12/release-12.html> (CTE inlining + `MATERIALIZED`, `jsonpath`)
  - pg13 — <https://www.postgresql.org/docs/13/release-13.html> (built-in `gen_random_uuid()`)
  - pg14 — <https://www.postgresql.org/docs/14/release-14.html> (multirange types, `DETACH PARTITION CONCURRENTLY`)
  - pg15 — <https://www.postgresql.org/docs/15/release-15.html> (`MERGE`)
  - pg16 — <https://www.postgresql.org/docs/16/release-16.html> (`IS JSON`, JSON constructors, `ANY_VALUE()`)
  - pg17 — <https://www.postgresql.org/docs/17/release-17.html> (SQL/JSON query funcs, `JSON()`/`JSON_SCALAR()`/`JSON_SERIALIZE()`, `MERGE` `RETURNING`/`WHEN NOT MATCHED BY SOURCE`/views)
  - pg18 — <https://www.postgresql.org/docs/18/release-18.html> (`RETURNING old`/`new`, virtual generated columns + new default, `uuidv7()`/`uuidv4()`, temporal constraints)
- **SQL command reference** (current grammar): <https://www.postgresql.org/docs/current/sql-commands.html>
- **In-repo SGML docs** at **19beta1** (`doc/src/sgml/release-19.sgml`, `ref/{merge,insert,select,create_table}.sgml`, `func/func-json.sgml`, `json.sgml`, `ddl.sgml`, `queries.sgml`, `datatype.sgml`, `rangetypes.sgml`) — used to confirm current grammar and the pg19-beta additions.
