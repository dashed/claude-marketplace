# JSON / JSONB, jsonpath, and SQL/JSON

Postgres's JSON surface: the `json`/`jsonb` types, the operator zoo, the jsonpath language
(pg12+), and the SQL/JSON standard functions (pg16/pg17). Version tags `(pgNN+)` = minimum server
version; untagged = bedrock.

## Contents

- [json vs jsonb](#json-vs-jsonb)
- [Navigation & extraction operators](#navigation--extraction-operators)
- [jsonb test/modify operators](#jsonb-testmodify-operators)
- [jsonpath (pg12+)](#jsonpath-pg12)
- [Processing & construction functions](#processing--construction-functions)
- [SQL/JSON (pg16 / pg17)](#sqljson-pg16--pg17)
- [Indexing note](#indexing-note)

## json vs jsonb

| | `json` | `jsonb` |
|---|---|---|
| Storage | exact text copy | decomposed binary |
| Preserves whitespace / key order / dup keys | **yes** | no (keys deduped, last wins; reordered) |
| Operators (`@>`, `?`, jsonpath), GIN indexing | limited | **full** |
| Per-access parse cost | re-parses each time | parsed once on input |
| Use when | you must round-trip the original text verbatim | **almost always** — you query/index it |

**Default to `jsonb`.** Use `json` only when you need to store and return the document byte-for-byte
(audit of exact input, preserving key order). Both are bedrock (`json` since 9.2, `jsonb` since 9.4).

## Navigation & extraction operators

These apply to both `json` and `jsonb` (result type follows the input type for `->`/`#>`):

| Operator | Meaning | Example → result |
|---|---|---|
| `-> int` / `-> text` | element by index / field by key → **json(b)** | `data -> 'addr'` → `{"city":"NYC"}` |
| `->> int` / `->> text` | same, but result as **text** | `data ->> 'name'` → `Ada` |
| `#> text[]` | element at **path** → json(b) | `data #> '{a,b,1}'` → `"bar"` |
| `#>> text[]` | element at path → **text** | `data #>> '{a,b,1}'` → `bar` |

The cardinal rule: **`->` keeps json(b); `->>` returns text.** Comparing `data->'age'` (jsonb) to
an integer fails or surprises you — use `(data->>'age')::int`, or jsonpath. Array indexes are
**0-based**; negative counts from the end.

```sql
SELECT data->'address'->>'city'  AS city,    -- chain: ->  then ->>
       data#>>'{tags,0}'         AS first_tag,
       (data->>'age')::int       AS age
FROM docs;
```

## jsonb test/modify operators

These are **`jsonb`-only** (they don't exist for `json`) and are the reason to store queryable
documents as `jsonb`:

| Operator | Meaning | Example |
|---|---|---|
| `@>` / `<@` | left contains right / is contained by | `data @> '{"active":true}'` |
| `?` | top-level key (or array string) exists | `data ? 'email'` |
| `?\|` (array) | **any** of these keys exist | `data ?\| array['a','b']` |
| `?&` (array) | **all** of these keys exist | `data ?& array['a','b']` |
| `\|\|` | concatenate / merge (shallow) | `data \|\| '{"seen":true}'` |
| `-` (text / int / text[]) | delete key / element / path-less keys | `data - 'tmp'` |
| `#-` (text[]) | delete at path | `data #- '{a,0}'` |

`@>` (containment) is the workhorse filter and is **GIN-indexable** — the idiomatic "documents
matching this shape" query.

```sql
SELECT * FROM docs
WHERE data @> '{"status":"active","plan":{"tier":"pro"}}'   -- nested containment
  AND data ? 'verified_at';
```

## jsonpath (pg12+)

The SQL/JSON **path language** (type `jsonpath`, pg12+) expresses rich queries over a document.
Two operators apply a path to `jsonb`:

| Operator | Meaning |
|---|---|
| `jsonb @? jsonpath` | does the path **match** anything? → boolean |
| `jsonb @@ jsonpath` | does the path **predicate** evaluate true? → boolean |

```sql
SELECT * FROM docs
WHERE data @? '$.items[*] ? (@.qty > 100)'    -- (pg12+) any item with qty > 100 exists
  AND data @@ '$.active == true';             -- (pg12+) predicate is true
```

Path-querying functions (pg12+) return the matched values:

```sql
SELECT jsonb_path_query(data, '$.items[*].sku')          FROM docs;  -- set of matches
SELECT jsonb_path_query_array(data, '$.items[*].price')  FROM docs;  -- as a jsonb array
SELECT jsonb_path_exists(data, '$.items[*] ? (@.qty > 0)') FROM docs;
```

Path syntax highlights: `$` (root), `@` (current, in filters), `.key`, `[*]` / `[0]` / `[1 to 3]`,
filter `? (@.x > 1)`, methods `.type()`, `.size()`, `.double()`, `.keyvalue()`, and the strict/lax
mode prefix (`strict $...` errors on structural mismatch; default `lax` is forgiving). `_tz`-suffixed
functions (e.g. `jsonb_path_query_tz`) handle timezone-aware comparisons.

## Processing & construction functions

A representative slice (all bedrock unless tagged):

- **Build**: `to_jsonb(anyelement)`, `jsonb_build_object('k', v, ...)`, `jsonb_build_array(...)`,
  `row_to_json(row)`, `jsonb_agg(expr)` / `jsonb_object_agg(k, v)` (aggregate rows into a doc).
- **Modify**: `jsonb_set(target, path, new_value [, create_if_missing])`,
  `jsonb_insert(...)`, `jsonb_strip_nulls(...)`.
- **Expand**: `jsonb_array_elements(j)` / `_text`, `jsonb_each(j)` / `_text`,
  `jsonb_object_keys(j)`, `jsonb_array_length(j)`, `jsonb_typeof(j)`. These are set-returning —
  pair them with `LATERAL` to fan a column of documents out into rows.
- **Pretty/format**: `jsonb_pretty(j)`.

```sql
-- Aggregate rows into one JSON document
SELECT jsonb_build_object('users', jsonb_agg(jsonb_build_object('id', id, 'name', name)))
FROM users;

-- Fan a documents column out into rows (LATERAL + set-returning expander)
SELECT d.id, e->>'sku' AS sku, (e->>'qty')::int AS qty
FROM docs d, LATERAL jsonb_array_elements(d.data->'items') AS e;
```

## SQL/JSON (pg16 / pg17)

The SQL-standard JSON features landed across **two** major versions — getting the split right
matters (these are common mis-pins):

### pg16+

- **`IS JSON` predicate** — `expr IS [NOT] JSON [ VALUE | SCALAR | ARRAY | OBJECT ]
  [ WITH | WITHOUT UNIQUE KEYS ]`. (pg19beta extends it to work on `DOMAIN` types.)
- **Constructor functions** `JSON_ARRAY(...)`, `JSON_ARRAYAGG(...)`, `JSON_OBJECT(...)`,
  `JSON_OBJECTAGG(...)`.

```sql
SELECT col IS JSON OBJECT AS looks_like_obj FROM raw;                 -- (pg16+)
SELECT JSON_OBJECT('id': id, 'name': name) FROM users;               -- (pg16+)
SELECT JSON_ARRAYAGG(name ORDER BY name) FROM users;                 -- (pg16+)
```

### pg17+

- **Query functions** `JSON_EXISTS()`, `JSON_QUERY()`, `JSON_VALUE()`, and **`JSON_TABLE()`**.
- **Constructors** `JSON()`, `JSON_SCALAR()`, `JSON_SERIALIZE()` — note these three are **pg17**,
  *not* pg16.

```sql
-- Extract a scalar with a target type (pg17+)
SELECT JSON_VALUE(data, '$.age' RETURNING int DEFAULT 0 ON EMPTY) FROM docs;       -- (pg17+)

-- Extract a JSON fragment (object/array), optionally wrapping/quoting (pg17+)
SELECT JSON_QUERY(data, '$.address' WITH CONDITIONAL WRAPPER) FROM docs;           -- (pg17+)

-- Test existence via a path (pg17+)
SELECT id FROM docs WHERE JSON_EXISTS(data, '$.items[*] ? (@.qty > 100)');         -- (pg17+)

-- JSON_TABLE: shred a document into relational rows/columns (pg17+)
SELECT jt.*
FROM docs d,
     JSON_TABLE(d.data, '$.items[*]'
       COLUMNS (
         idx FOR ORDINALITY,
         sku  text PATH '$.sku',
         qty  int  PATH '$.qty' DEFAULT 0 ON EMPTY,
         tags jsonb PATH '$.tags' WITH WRAPPER,
         NESTED PATH '$.variants[*]' COLUMNS (variant text PATH '$.name')
       )) AS jt;                                                                   -- (pg17+)
```

`JSON_VALUE` returns a single **scalar** (errors/NULLs if the path yields an object/array — use
`JSON_QUERY` for those). `JSON_TABLE` is laterally joined to its input and supports `FOR
ORDINALITY`, per-column `PATH`, `DEFAULT ... ON EMPTY/ON ERROR`, and `NESTED PATH` for
one-to-many shredding.

> **Why the split?** SQL/JSON was reverted from pg15 pre-release, then shipped in two waves: the
> `IS JSON` predicate + `JSON_ARRAY`/`JSON_OBJECT` constructor family in **pg16**, and the query
> functions (`JSON_TABLE`/`JSON_QUERY`/`JSON_VALUE`/`JSON_EXISTS`) plus `JSON()`/`JSON_SCALAR()`/
> `JSON_SERIALIZE()` in **pg17**. See [version-features.md](version-features.md#the-precise-sqljson-split-pg16-vs-pg17).

## Indexing note

`jsonb` containment/existence/jsonpath queries can use a **GIN index** (`CREATE INDEX ... USING
gin (data)` for `@>`/`?`, or `USING gin (data jsonb_path_ops)` for a smaller `@>`-only index).
Choosing and tuning indexes is the **postgres-performance** skill's domain; this is only a pointer
so you know the operators above are indexable.

## Sources

- JSON types: <https://www.postgresql.org/docs/current/datatype-json.html> · in-repo `json.sgml`
- JSON functions & operators, jsonpath, SQL/JSON: <https://www.postgresql.org/docs/current/functions-json.html> · in-repo `func/func-json.sgml`
- pg12 (jsonpath), pg16 (`IS JSON`, constructors, `ANY_VALUE`), pg17 (query functions + `JSON()`/`JSON_SCALAR()`/`JSON_SERIALIZE()`) — Appendix E (see [version-features.md](version-features.md)).
