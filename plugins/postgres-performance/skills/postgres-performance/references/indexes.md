# Indexes — Types, Strategies & Maintenance

Everything about choosing, designing, building, and maintaining indexes for performance. For *when
the planner uses* an index see [reading-plans.md](reading-plans.md); for version floors see
[version-features.md](version-features.md).

## Contents

- [The six index types](#the-six-index-types)
- [Operator classes](#operator-classes)
- [Index design strategies](#index-design-strategies)
- [Covering indexes & index-only scans](#covering-indexes--index-only-scans)
- [Building and rebuilding without downtime](#building-and-rebuilding-without-downtime)
- [Storage parameters](#storage-parameters)
- [Finding missing & unused indexes](#finding-missing--unused-indexes)

## The six index types

`CREATE INDEX [CONCURRENTLY] [name] ON table USING method (cols…)`. Default `method` is `btree`.

### B-tree (default)
Balanced tree; supports `=`, `<`, `<=`, `>=`, `>`, `BETWEEN`, `IN`, `IS [NOT] NULL`, and **prefix**
`LIKE 'abc%'` / `~ '^abc'` (with a `text_pattern_ops` opclass in non-C locales). The **only** type
that supports **unique** indexes, **ordered scans** (satisfies `ORDER BY`, including
`ASC/DESC/NULLS FIRST|LAST`), and is the workhorse for **multicolumn** and **covering** (`INCLUDE`,
pg11+) indexes. Has **deduplication** (pg13+, on by default) and **bottom-up deletion** (pg14+) to
resist bloat, and **skip scan** (pg18+). Use it unless you have a specific reason not to.

### Hash
Supports **`=` only**. WAL-logged & crash-safe since **pg10** (before that, unsafe). In practice a
B-tree on the same column handles equality about as well *and* does ranges/ordering, so hash indexes
are rarely worth it — consider one only for very large equality-only keys where its smaller size
matters. No multicolumn, no unique.

### GIN (Generalized Inverted Index)
For columns holding **many values per row**: `jsonb`, arrays, full-text `tsvector`, and **trigram**
search. The go-to for:
- `jsonb` containment `@>`, key existence `?`/`?|`/`?&` → `USING gin (col jsonb_path_ops)` for `@>`-only
  (smaller/faster) or default `jsonb_ops` for the full operator set.
- Array overlap/containment `&&`, `@>`, `<@`.
- Full-text `to_tsvector(col) @@ to_tsquery(...)`.
- Substring/`ILIKE '%x%'` and fuzzy matching via `pg_trgm`'s `gin_trgm_ops`.
GIN supports multicolumn indexes; `fastupdate` (on by default) buffers inserts in a pending list
(flushed by VACUUM / `gin_clean_pending_list()`).

### GiST (Generalized Search Tree)
Extensible, balanced tree for **ranges, geometry, and nearest-neighbour**. Use for:
- Range types (`int4range`, `tstzrange`) and **exclusion constraints** (`EXCLUDE USING gist`).
- PostGIS / geometric containment & overlap.
- **KNN / nearest-neighbour** ordering: `ORDER BY location <-> point` returns rows by distance.
- Full-text as an alternative to GIN (smaller, slower-to-search, faster-to-update).
GiST is **lossy** — expect a `Recheck Cond` / `Rows Removed by Index Recheck`. Supports `INCLUDE`
since pg12.

### SP-GiST (Space-Partitioned GiST)
For **non-balanced / partitioned** structures: quadtrees, k-d trees, radix trees. Best for
`inet`/`cidr` (IP ranges), `point`, and **text prefix** trees. Niche but excellent for those.
Supports `INCLUDE` since pg14.

### BRIN (Block Range INdex)
Stores **summary min/max per block range** (default 128 pages), not per row — so it's **tiny** (KB
for a table of GB). Only wins when the table is **physically correlated** with the indexed column:
append-only time-series where `created_at` rises with physical position, or naturally-clustered data.
On uncorrelated data it's useless. Tune `pages_per_range`; enable `autosummarize`. Supports
multicolumn. The right tool for huge, ordered, append-only tables where a B-tree would be enormous.

| Type | Operators | Unique | Ordered | Multicol | Lossy |
|------|-----------|:------:|:-------:|:--------:|:-----:|
| B-tree | `= < <= >= >` `BETWEEN` `IN` prefix-`LIKE` | ✅ | ✅ | ✅ | no |
| Hash | `=` | — | — | — | no |
| GIN | `@>` `?` `&&` `@@` trigram | — | — | ✅ | no* |
| GiST | range, geo, `<->` KNN, FTS | — | KNN | ✅ | yes |
| SP-GiST | prefix, `inet`, `point` | — | some | — | yes |
| BRIN | `= < <= >= >` on correlated data | — | — | ✅ | yes |

## Operator classes

An **operator class** tells an index *how* to handle a column's type/usage. The default opclass is
right for most columns; you specify one for special cases:

| Opclass | On | Enables |
|---------|----|---------|
| `text_pattern_ops` / `varchar_pattern_ops` / `bpchar_pattern_ops` | B-tree on text | Prefix `LIKE 'x%'` / `~ '^x'` in **non-C locales** (default opclass can't) |
| `jsonb_path_ops` | GIN on `jsonb` | Smaller/faster index for `@>` containment (drops `?` operators) |
| `gin_trgm_ops` / `gist_trgm_ops` | GIN/GiST on text (pg_trgm) | Substring `LIKE '%x%'`, `ILIKE`, similarity `%`, regex |
| `int4_ops`, etc. | default | Standard ordering for the type |

```sql
CREATE INDEX ON docs USING gin (data jsonb_path_ops);          -- WHERE data @> '{"k":1}'
CREATE INDEX ON items USING gin (name gin_trgm_ops);           -- WHERE name ILIKE '%foo%'
CREATE INDEX ON urls (path text_pattern_ops);                  -- WHERE path LIKE '/a/b%' in en_US locale
```

`pg_trgm` is an extension — enable it via the **postgres-extensions** skill (`CREATE EXTENSION pg_trgm`).

## Index design strategies

### Multicolumn — column order is everything
A B-tree on `(a, b, c)` efficiently serves predicates on a **leftmost prefix**: `a`, `a,b`, `a,b,c`.
Rules of thumb:
- **Equality columns first, the range/sort column last:** for `WHERE a = ? AND b > ?`, index `(a, b)`.
- Match `ORDER BY` to enable an ordered index scan (mind `ASC/DESC`/`NULLS` ordering).
- **B-tree skip scan (pg18+)** can now use the index even when a leading column is *not* in the
  predicate — efficient when that leading column has **few distinct values** (visible as multiple
  `Index Searches`). Before pg18, a query on only `b` couldn't use a `(a, b)` index.

### Partial indexes — index only what you query
```sql
CREATE INDEX ON orders (created_at) WHERE status = 'open';      -- only "open" rows are indexed
CREATE UNIQUE INDEX ON users (email) WHERE deleted_at IS NULL;  -- uniqueness over a subset
```
Smaller, faster to scan, cheaper to maintain. The planner uses a partial index only when it can prove
the query predicate implies the index predicate. Great for "hot" subsets (active/unprocessed rows).

### Expression indexes — index the transformed value
```sql
CREATE INDEX ON users (lower(email));         -- serves WHERE lower(email) = lower($1)
CREATE INDEX ON events ((payload->>'type'));  -- serves WHERE payload->>'type' = $1
```
Functions/operators in the definition must be **IMMUTABLE**. Equivalent expression statistics are
built automatically (like an [expression statistics object](statistics-and-planner.md#extended-statistics)).
This is the fix for "index exists but isn't used because the column is wrapped in a function."

## Covering indexes & index-only scans

An **index-only scan** answers a query entirely from the index, skipping the heap — but only for heap
pages marked **all-visible** in the visibility map (so `VACUUM` matters; `Heap Fetches: 0` is the win).
To make a query index-only, include every column it touches:

```sql
-- Key column drives the lookup; INCLUDE carries the payload needed by SELECT.  (pg11+, B-tree)
CREATE INDEX ON orders (customer_id) INCLUDE (status, total);
-- Now: SELECT status, total FROM orders WHERE customer_id = $1  → Index Only Scan
```

`INCLUDE` columns are **non-key**: not usable in the search condition, not part of uniqueness, but
returnable by an index-only scan. They keep the index smaller than adding them as key columns and
don't constrain ordering. Notes: `INCLUDE` disables B-tree deduplication for that index; expressions
can't be `INCLUDE`d; supported on B-tree (pg11+), GiST (pg12+), SP-GiST (pg14+). Don't over-include —
every payload column enlarges the index and slows writes.

## Building and rebuilding without downtime

```sql
CREATE INDEX CONCURRENTLY idx ON big (col);     -- no write lock; ~2× slower; CANNOT run in a txn block
REINDEX INDEX CONCURRENTLY idx;                 -- (pg12+) rebuild bloated/corrupt index online
REINDEX TABLE CONCURRENTLY big;                 -- (pg12+) all of a table's indexes
```

- **`CREATE INDEX` (plain)** locks out **writes** (not reads) until done — fine for maintenance
  windows, fatal for a live OLTP table.
- **`CONCURRENTLY`** does two table scans and waits for in-flight transactions, so it's slower and
  uses more total work, but doesn't block writers. **It cannot run inside a transaction block**, and
  is **not supported on partitioned tables directly** (build each partition concurrently, then the
  parent index non-concurrently). A failure leaves an **`INVALID`** index — `\d` shows it; drop it
  (`DROP INDEX`) and retry, or `REINDEX INDEX CONCURRENTLY` it.
- **`REINDEX`** rebuilds a **bloated** or corrupt index, or applies a changed `fillfactor`. Plain
  `REINDEX` takes `ACCESS EXCLUSIVE` on the index (blocks queries using it); `CONCURRENTLY` avoids
  that but leaves transient `*_ccnew`/`*_ccold` indexes on failure (drop them). `REINDEX SYSTEM`
  cannot be concurrent. On bloat generally, prefer `REINDEX CONCURRENTLY` over `VACUUM FULL`.

## Storage parameters

```sql
CREATE INDEX ON t (c) WITH (fillfactor = 90);
```

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `fillfactor` | B-tree/hash/GiST/SP-GiST | 90 (btree) | % of a page filled on build; lower (70–90) leaves room for updates, reducing page splits. `100` only for static tables. |
| `deduplicate_items` | B-tree | on (pg13+) | Combine duplicate keys to shrink the index. Off for `INCLUDE` indexes. |
| `fastupdate` | GIN | on | Buffer inserts in a pending list (faster writes, slower reads until flushed by VACUUM). |
| `gin_pending_list_limit` | GIN | 4MB | Pending-list flush threshold. |
| `pages_per_range` | BRIN | 128 | Block-range granularity (smaller = finer summaries, bigger index). |
| `autosummarize` | BRIN | off | Summarize new ranges automatically. |

`maintenance_work_mem` (and `max_parallel_maintenance_workers` for parallel B-tree/GIN/BRIN builds,
pg11+) govern build **speed** — raise them for large index builds.

## Finding missing & unused indexes

```sql
-- Tables taking lots of sequential scans relative to index scans (candidates for a new index):
SELECT relname, seq_scan, idx_scan, seq_tup_read, n_live_tup
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 20;

-- Indexes that are (almost) never scanned — candidates to DROP (write overhead with no read benefit):
SELECT s.relname AS table, s.indexrelname AS index, s.idx_scan,
       pg_size_pretty(pg_relation_size(s.indexrelid)) AS size
FROM pg_stat_user_indexes s
JOIN pg_index i ON i.indexrelid = s.indexrelid
WHERE s.idx_scan = 0 AND NOT i.indisunique
ORDER BY pg_relation_size(s.indexrelid) DESC;
```

Caveats: `idx_scan` accumulates since the last stats reset (a fresh cluster looks "unused"); never
drop indexes backing unique/PK constraints or used only by rare-but-critical queries. Every index
costs write throughput and bloat, so unused indexes are pure overhead. For *precise* index bloat use
`pgstattuple` (postgres-extensions skill).
