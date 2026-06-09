# The contrib Catalog — Every Bundled Module

The complete set of modules shipped in the PostgreSQL source tree under `contrib/`
(packaged by distributions as `postgresql-contrib` / `postgresqlNN-contrib`). Grouped by
purpose; each entry gives a one-line purpose, the activation command, a tiny usage
example, and version notes. `(pgNN+)` = first PostgreSQL release the module/feature
shipped in; **unannotated = bedrock** (present since the 9.x era). See
[version-features.md](version-features.md) for the sourced version map.

> **Three kinds of module.** Most are **`CREATE EXTENSION`** modules (they have a
> `.control` file and install SQL objects). A few are **`LOAD`-only / preload** modules
> (no `.control`, no SQL objects — configured via GUCs). Two are **client programs**
> (standalone binaries, not loaded into the server). Each entry is labeled.

## Contents

- [Text, fuzzy & full-text search](#text-fuzzy--full-text-search)
- [Data types](#data-types)
- [Indexing support](#indexing-support)
- [Foreign data & external connections](#foreign-data--external-connections)
- [Cryptography & UUIDs](#cryptography--uuids)
- [Query statistics & plan logging](#query-statistics--plan-logging)
- [Storage inspection & forensics](#storage-inspection--forensics)
- [Table functions & data utilities](#table-functions--data-utilities)
- [SPI trigger examples](#spi-trigger-examples)
- [PL transforms](#pl-transforms)
- [Server-side hooks & policies (LOAD/preload only)](#server-side-hooks--policies-loadpreload-only)
- [Client programs (binaries, not extensions)](#client-programs-binaries-not-extensions)
- [Deprecated / legacy](#deprecated--legacy)

---

## Text, fuzzy & full-text search

### `pg_trgm` — trigram similarity & index-accelerated fuzzy/LIKE/regex search *(trusted)*
```sql
CREATE EXTENSION pg_trgm;
SELECT similarity('postgres', 'postgers');         -- 0.5
SELECT 'cat' % 'cats';                              -- similarity above threshold → true
CREATE INDEX ON docs USING gin (body gin_trgm_ops); -- accelerates ILIKE '%term%', ~, %
```
Provides `similarity()`, `word_similarity()`, the `%`/`<->` operators, and the
`gin_trgm_ops` / `gist_trgm_ops` operator classes — the standard way to index
substring/`LIKE`/regex and typo-tolerant lookups. Bedrock.

### `fuzzystrmatch` — phonetic matching & edit distance *(trusted)*
```sql
CREATE EXTENSION fuzzystrmatch;
SELECT levenshtein('kitten', 'sitting');            -- 3
SELECT soundex('Robert'), metaphone('Thompson', 4); -- R163 | TMSN
SELECT daitch_mokotoff('Moskowitz');                -- modern phonetic codes
```
`levenshtein`, `levenshtein_less_equal`, `soundex`, `metaphone`, `dmetaphone`,
`dmetaphone_alt`, and `daitch_mokotoff`. Bedrock. (`daitch_mokotoff` added pg16+.)

### `unaccent` — accent-stripping function + FTS dictionary *(trusted)*
```sql
CREATE EXTENSION unaccent;
SELECT unaccent('Hôtel Crémé');                     -- Hotel Creme
-- Or as a full-text-search dictionary in a text-search configuration.
```
Bedrock.

### `dict_int` — full-text dictionary for integers *(trusted)*
```sql
CREATE EXTENSION dict_int;   -- controls how integers are normalized in FTS (maxlen, etc.)
```
A configurable text-search dictionary template for indexing numbers. Bedrock.

### `dict_xsyn` — extended-synonym FTS dictionary
```sql
CREATE EXTENSION dict_xsyn;  -- maps synonyms/derivations to a base word for FTS
```
Bedrock. (Not trusted.)

---

## Data types

### `citext` — case-insensitive text type *(trusted)*
```sql
CREATE EXTENSION citext;
CREATE TABLE users (email citext UNIQUE);
SELECT 'Foo@Example.com'::citext = 'foo@example.com';  -- true
```
A drop-in text type whose comparisons fold case. Bedrock.

### `hstore` — key/value pairs in a single column *(trusted)*
```sql
CREATE EXTENSION hstore;
SELECT 'a=>1, b=>2'::hstore -> 'a';                 -- 1
SELECT 'a=>1'::hstore || 'b=>2'::hstore;            -- concatenate
CREATE INDEX ON t USING gin (data);                 -- index hstore for @>, ?, ?& etc.
```
The original schemaless string→string store; for richer nesting use core `jsonb`. Bedrock.

### `ltree` — hierarchical tree-path labels *(trusted)*
```sql
CREATE EXTENSION ltree;
SELECT 'Top.Science.Astronomy'::ltree;
SELECT 'Top.Science.Astronomy'::ltree <@ 'Top.Science'::ltree;  -- descendant? → true
SELECT path FROM cat WHERE path ~ '*.Astronomy.*'::lquery;      -- lquery pattern
CREATE INDEX ON cat USING gist (path);
```
Materialized-path tree type with `@>`/`<@`, `lquery`/`ltxtquery` matching, and GiST/GIN
support. Bedrock.

### `cube` — multidimensional cubes & points *(trusted)*
```sql
CREATE EXTENSION cube;
SELECT cube(array[1,2,3]) <-> cube(array[4,5,6]);   -- Euclidean distance
```
N-dimensional float boxes/points with distance operators and GiST indexing; prerequisite
of `earthdistance`. Bedrock.

### `isn` — international product/standard number types *(trusted)*
```sql
CREATE EXTENSION isn;
SELECT '978-0-13-110362-7'::isbn13;                 -- validated ISBN-13
```
Validating types for ISBN, ISMN, ISSN, EAN13, UPC. Bedrock.

### `seg` — line-segment / float interval type *(trusted)*
```sql
CREATE EXTENSION seg;
SELECT '6.25 .. 6.50'::seg;                         -- value with measurement error
```
Represents one-dimensional intervals (laboratory measurements with uncertainty); GiST
indexable. Bedrock.

### `intarray` — extra integer-array operators & functions *(trusted)*
```sql
CREATE EXTENSION intarray;
SELECT '{1,2,3}'::int[] && '{3,4}'::int[];           -- overlaps? → true
CREATE INDEX ON posts USING gin (tag_ids gin__int_ops);
```
Fast set operators (`&&`, `@>`, `&`, `|`) and the `gin__int_ops` class for one-dimensional
`int[]`. Bedrock.

---

## Indexing support

### `btree_gist` — B-tree operator classes for GiST *(trusted)*
```sql
CREATE EXTENSION btree_gist;
-- Enables EXCLUDE constraints mixing equality with ranges/overlaps:
ALTER TABLE room_booking
  ADD CONSTRAINT no_overlap EXCLUDE USING gist (room_id WITH =, during WITH &&);
```
Adds B-tree-style equality/ordering to GiST so scalar columns can join range/geometry
columns in one GiST index or `EXCLUDE` constraint. Bedrock.

### `btree_gin` — B-tree operator classes for GIN *(trusted)*
```sql
CREATE EXTENSION btree_gin;
CREATE INDEX ON t USING gin (status, tags);   -- combine scalar = with array/jsonb in one GIN index
```
Lets GIN index scalar types so equality predicates on plain columns can share a GIN index
with array/`jsonb`/full-text columns. Bedrock. (pg19+ adds cross-type comparison support.)

### `bloom` — Bloom-filter index access method
```sql
CREATE EXTENSION bloom;
CREATE INDEX ON t USING bloom (c1, c2, c3);   -- compact index for arbitrary-column equality
```
A space-efficient index AM that answers multi-column equality filters with a small
false-positive rate — useful when many columns are each queried by `=`. Bedrock (9.6).
Not trusted.

---

## Foreign data & external connections

### `postgres_fdw` — query tables in another PostgreSQL server
```sql
CREATE EXTENSION postgres_fdw;
CREATE SERVER s FOREIGN DATA WRAPPER postgres_fdw OPTIONS (host 'db2', dbname 'app', port '5432');
CREATE USER MAPPING FOR CURRENT_USER SERVER s OPTIONS (user 'app', password '...');
IMPORT FOREIGN SCHEMA public LIMIT TO (orders) FROM SERVER s INTO ext;
SELECT * FROM ext.orders WHERE id = 42;        -- predicate/JOIN pushdown to remote
```
The standard remote-PostgreSQL FDW: predicate, join, and aggregate pushdown. Not trusted
(networks out). Bedrock (9.3). Notable later gains: batch insert (`batch_size`) and async
foreign-scan execution (pg14+).

### `dblink` — ad-hoc connections to other PostgreSQL databases
```sql
CREATE EXTENSION dblink;
SELECT * FROM dblink('dbname=remote', 'SELECT id, name FROM t') AS x(id int, name text);
```
Imperative cross-database queries (vs. `postgres_fdw`'s declarative tables); also supports
async calls. Not trusted. Bedrock.

### `file_fdw` — read a server-side file as a table
```sql
CREATE EXTENSION file_fdw;
CREATE SERVER files FOREIGN DATA WRAPPER file_fdw;
CREATE FOREIGN TABLE logs (ts timestamptz, msg text)
  SERVER files OPTIONS (filename '/var/log/app.csv', format 'csv', header 'true');
```
Exposes a CSV/text file (or a program's output) as a read-only table. Not trusted (reads
the filesystem). Bedrock (9.1).

---

## Cryptography & UUIDs

### `pgcrypto` — hashing, encryption, HMAC, random bytes *(trusted)*
```sql
CREATE EXTENSION pgcrypto;
SELECT crypt('secret', gen_salt('bf'));        -- bcrypt password hash
SELECT digest('data', 'sha256');               -- raw hash
SELECT encode(hmac('msg', 'key', 'sha256'), 'hex');
SELECT encode(gen_random_bytes(16), 'hex');    -- CSPRNG bytes
```
Cryptographic functions (digests, HMAC, PGP/raw symmetric encryption, bcrypt). Bedrock.
**`gen_random_uuid()` is no longer pgcrypto's job** — it graduated to **core** in pg13
(pgcrypto's copy now just calls the core function). For random UUIDs, no extension is
needed at all.

### `uuid-ossp` — classic UUID generation algorithms *(trusted)*
```sql
CREATE EXTENSION "uuid-ossp";                  -- quote the hyphenated name
SELECT uuid_generate_v1mc(), uuid_generate_v4();
SELECT uuid_generate_v5(uuid_ns_url(), 'https://example.com');
```
Only needed for algorithms beyond core: v1/v1mc (MAC+time), v3/v5 (namespace hashes), and
the special-constant helpers. **For a plain random UUID prefer core `gen_random_uuid()`
(pg13+).** Bedrock. (Core also gained `uuidv7()`/`uuidv4()` builtins in pg18+.)

---

## Query statistics & plan logging

> For *how to use these to actually tune queries*, see the **postgres-performance** skill;
> for editing `shared_preload_libraries`, see **postgres-admin**. This catalog only
> documents what each module is and how to turn it on.

### `pg_stat_statements` — aggregated per-statement execution stats
```sql
-- shared_preload_libraries = 'pg_stat_statements' in postgresql.conf, then RESTART, then:
CREATE EXTENSION pg_stat_statements;
SELECT query, calls, total_exec_time, mean_exec_time, rows
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;
SELECT pg_stat_statements_reset();
```
Normalizes queries (`$1`, `$2` …) and accumulates calls, timing, rows, buffer and WAL
usage. **Requires preload + restart.** Bedrock (8.4). The view has grown columns over
releases: planning/execution time split + `wal_records`/`wal_bytes`/`wal_fpi` (pg13+);
the shared/local block I/O timing split — `shared_blk_*` rename plus `local_blk_read_time`/
`local_blk_write_time` and `stats_since` (pg17+); `parallel_workers_to_launch`/
`parallel_workers_launched` and `wal_buffers_full` (pg18+); generic-vs-custom plan counters
(pg19+). The extension's own `default_version` is **1.13** in PG18/19 — that number is
unrelated to the PostgreSQL release.

---

## Storage inspection & forensics

> Most of these are **superuser-only** and read raw on-disk structures — invaluable for
> diagnosing corruption, bloat, and cache behavior, dangerous if misused.

### `pg_buffercache` — what's resident in `shared_buffers`
```sql
CREATE EXTENSION pg_buffercache;
SELECT c.relname, count(*) AS buffers
FROM pg_buffercache b JOIN pg_class c ON b.relfilenode = pg_relation_filenode(c.oid)
GROUP BY 1 ORDER BY 2 DESC LIMIT 10;
SELECT pg_buffercache_evict(123);              -- evict one buffer (pg17+, testing)
```
A view over the shared buffer pool. Bedrock. Newer helpers: `pg_buffercache_evict()`
(pg17+); NUMA reporting `pg_buffercache_numa_pages()` (pg18+); `pg_buffercache_os_pages()`
view and `pg_buffercache_mark_dirty*()` (pg19+).

### `pageinspect` — low-level page & tuple internals
```sql
CREATE EXTENSION pageinspect;
SELECT * FROM heap_page_items(get_raw_page('t', 0));   -- tuples on heap page 0
SELECT * FROM bt_page_stats('t_pkey', 1);              -- B-tree page metadata
```
Decodes the bytes of heap/index/GIN/BRIN pages. Superuser. Bedrock.

### `pgstattuple` — physical tuple-level / bloat statistics
```sql
CREATE EXTENSION pgstattuple;
SELECT * FROM pgstattuple('t');               -- live/dead tuple bytes, free space, bloat
SELECT * FROM pgstatindex('t_pkey');          -- B-tree leaf density / fragmentation
```
Scans a relation to report dead-tuple and free-space ratios (bloat). Bedrock.

### `pg_visibility` — visibility-map state per page
```sql
CREATE EXTENSION pg_visibility;
SELECT * FROM pg_visibility_map('t');         -- all_visible / all_frozen bits per block
SELECT pg_check_frozen('t');                  -- find pages wrongly marked all-frozen
```
Inspects and verifies the visibility map (relevant to index-only scans and freezing).
Superuser. Bedrock (9.6).

### `amcheck` — verify index & heap integrity
```sql
CREATE EXTENSION amcheck;
SELECT bt_index_check('t_pkey');                       -- structural B-tree check
SELECT bt_index_parent_check('t_pkey', heapallindexed => true);  -- thorough (stronger lock)
SELECT * FROM verify_heapam('t');                      -- heap corruption check (pg14+)
```
Detects on-disk corruption in B-tree (and, pg18+, GIN) indexes and in heaps. Superuser.
`(pg10+)`; `verify_heapam` `(pg14+)`; `gin_index_check` `(pg18+)`.

### `pg_surgery` — last-resort repair of corrupted heaps *(pg14+)*
```sql
CREATE EXTENSION pg_surgery;
SELECT heap_force_kill('t'::regclass, ARRAY['(0,1)']::tid[]);   -- mark a broken tuple dead
SELECT heap_force_freeze('t'::regclass, ARRAY['(0,3)']::tid[]); -- force-freeze a tuple
```
Forcibly fixes individual tuples after corruption. **Dangerous — can cause data loss /
worsen corruption; a recovery tool of last resort.** Superuser. `(pg14+)`.

### `pg_walinspect` — decode WAL records via SQL *(pg15+)*
```sql
CREATE EXTENSION pg_walinspect;
SELECT * FROM pg_get_wal_record_info('0/E419E28');
SELECT * FROM pg_get_wal_records_info('0/1E913618', '0/1E913740');
SELECT * FROM pg_get_wal_stats('0/1E913618', '0/1E913740', true);
```
SQL-level WAL forensics (what `pg_waldump` does, from inside the server). Superuser.
`(pg15+)`.

### `pg_freespacemap` — free-space-map contents
```sql
CREATE EXTENSION pg_freespacemap;
SELECT * FROM pg_freespace('t');              -- approx free bytes per page
```
Reports the FSM that tracks insertable free space per page. Superuser. Bedrock.

### `pg_prewarm` — load relations into the cache
```sql
CREATE EXTENSION pg_prewarm;
SELECT pg_prewarm('t');                       -- warm a table into shared_buffers / OS cache
```
Manual cache warming via the `pg_prewarm()` function (no preload needed). The
**`autoprewarm` background worker**, which restores buffer contents after restart, needs
`shared_preload_libraries` `(pg11+)`. Base function bedrock (9.4).

### `pg_logicalinspect` — inspect logical-decoding snapshots *(pg18+)*
```sql
CREATE EXTENSION pg_logicalinspect;
SELECT * FROM pg_get_logical_snapshot_meta('0-40796E18.snap');
SELECT * FROM pg_get_logical_snapshot_info('0-40796E18.snap');
```
Decodes on-disk logical-decoding snapshot files (replication debugging). Superuser.
`(pg18+)`.

### `pg_stash_advice` — stash per-query-id planner advice *(pg19+)*
```sql
CREATE EXTENSION pg_stash_advice;             -- companion to the pg_plan_advice LOAD module
```
New in PG19 (beta): lets per-query-id plan advice be specified and persisted; works with
the `pg_plan_advice` LOAD-only module below. `(pg19+)`. **Beta — interface may change.**

### `pgrowlocks` — show row-level lock information
```sql
CREATE EXTENSION pgrowlocks;
SELECT * FROM pgrowlocks('t');                -- locked rows, lock modes, holding xids
```
Reports currently-held row locks for a table. Bedrock.

---

## Table functions & data utilities

### `tablefunc` — crosstab (pivot), connectby, random generators *(trusted)*
```sql
CREATE EXTENSION tablefunc;
SELECT * FROM crosstab('SELECT row_id, category, value FROM t ORDER BY 1,2')
  AS ct(row_id int, cat_a int, cat_b int);    -- pivot rows → columns
SELECT * FROM connectby('org', 'id', 'parent_id', '1', 0)  -- hierarchy walk
  AS t(id int, parent int, level int);
SELECT normal_rand(100, 5, 2);               -- 100 normally-distributed samples
```
The classic pivot/crosstab toolkit plus tree-walking and random-data helpers. Bedrock.

### `earthdistance` — great-circle distance
```sql
CREATE EXTENSION earthdistance CASCADE;       -- pulls in its prerequisite, cube
SELECT earth_distance(ll_to_earth(40.7,-74.0), ll_to_earth(34.0,-118.2));  -- meters
```
Two implementations: a `cube`-based `earth` type (needs `cube`) and a simpler `point`-based
`<@>` operator. For real GIS use **PostGIS** (external). Bedrock.

### `lo` — large-object reference type + orphan-cleanup trigger *(trusted)*
```sql
CREATE EXTENSION lo;
CREATE TABLE img (id int, data lo);
CREATE TRIGGER t_lo BEFORE UPDATE OR DELETE ON img
  FOR EACH ROW EXECUTE FUNCTION lo_manage(data);   -- unlink LO when row changes
```
A managed `lo` domain over large-object OIDs whose trigger deletes orphaned large objects.
Bedrock.

### `tcn` — triggered change notifications *(trusted)*
```sql
CREATE EXTENSION tcn;
CREATE TRIGGER t_notify AFTER INSERT OR UPDATE OR DELETE ON t
  FOR EACH ROW EXECUTE FUNCTION triggered_change_notification();   -- NOTIFY on change
```
Emits `LISTEN`/`NOTIFY` events describing row changes. Bedrock.

### `tsm_system_rows` — `TABLESAMPLE` by row count *(trusted)*
```sql
CREATE EXTENSION tsm_system_rows;
SELECT * FROM t TABLESAMPLE SYSTEM_ROWS(100);   -- ~100 rows, block-sampled
```
A `TABLESAMPLE` method that returns approximately N rows. Bedrock (came with `TABLESAMPLE`
in 9.5).

### `tsm_system_time` — `TABLESAMPLE` by time budget *(trusted)*
```sql
CREATE EXTENSION tsm_system_time;
SELECT * FROM t TABLESAMPLE SYSTEM_TIME(1000);  -- sample for ~1000 ms
```
A `TABLESAMPLE` method bounded by milliseconds. Bedrock (9.5).

### `intagg` — integer aggregate & enumeration (legacy)
```sql
CREATE EXTENSION intagg;
```
Older `int_array_aggregate` / `int_array_enum` helpers — **superseded by core
`array_agg()` and `unnest()`**; kept for compatibility. Bedrock.

### `sslinfo` — TLS client-certificate information
```sql
CREATE EXTENSION sslinfo;
SELECT ssl_is_used(), ssl_client_dn();        -- info about the current SSL connection
```
Exposes details of the client's SSL/TLS connection and certificate. Bedrock.

---

## SPI trigger examples

The `spi/` directory ships four small **example trigger extensions** (also genuinely
useful). Each is `CREATE EXTENSION`-able:

```sql
CREATE EXTENSION moddatetime;     -- trigger to set a column to current_timestamp on update
CREATE EXTENSION insert_username; -- trigger to record the current user in a column
CREATE EXTENSION autoinc;         -- trigger-based auto-increment from a sequence
CREATE EXTENSION refint;          -- generic referential-integrity triggers (pre-FK style)
```
All bedrock. `moddatetime` and `insert_username` are the commonly-used pair.

---

## PL transforms

Transform extensions that map PostgreSQL types to a procedural language's native types so
PL functions receive/return them naturally. Install alongside the relevant PL:

```sql
CREATE EXTENSION hstore_plperl;      -- hstore  <-> Perl hash      (also hstore_plperlu)
CREATE EXTENSION hstore_plpython3u;  -- hstore  <-> Python dict
CREATE EXTENSION jsonb_plperl;       -- jsonb   <-> Perl           (also jsonb_plperlu)
CREATE EXTENSION jsonb_plpython3u;   -- jsonb   <-> Python objects
CREATE EXTENSION ltree_plpython3u;   -- ltree   <-> Python
CREATE EXTENSION bool_plperl;        -- bool    <-> Perl boolean    (also bool_plperlu)
```
Bedrock (the jsonb/bool transforms arrived alongside their type/PL support; treat as
long-standing). The `*u` variants pair with the untrusted PL (`plperlu`). Among these,
only **`bool_plperl`** and **`jsonb_plperl`** are marked trusted (per their `.control`
files); the rest need superuser.

---

## Server-side hooks & policies (LOAD/preload only)

**No `CREATE EXTENSION`** — these have no SQL objects. Configure via GUCs and (usually)
`shared_preload_libraries` + restart. See **postgres-admin** for the config mechanics.

### `auto_explain` — automatically log plans of slow statements
```sql
LOAD 'auto_explain';                          -- per session (superuser); or *_preload_libraries
SET auto_explain.log_min_duration = '500ms';
SET auto_explain.log_analyze = on;
```
Logs `EXPLAIN` (optionally `ANALYZE`) output for statements over a threshold. Bedrock (8.4).
For interpreting that output to tune, see **postgres-performance**. (pg19+ adds
`auto_explain.log_extension_options`.)

### `pg_overexplain` — extra low-level EXPLAIN detail *(pg18+)*
```sql
LOAD 'pg_overexplain';                        -- LOAD-only; no CREATE EXTENSION
EXPLAIN (DEBUG) SELECT ...;                   -- adds planner-internal detail
EXPLAIN (RANGE_TABLE) SELECT ...;
```
Adds `DEBUG`/`RANGE_TABLE` EXPLAIN options for planner development/debugging. `(pg18+)`.

### `pg_plan_advice` — generate & enforce planner "advice" *(pg19+)*
```sql
LOAD 'pg_plan_advice';                        -- LOAD-only; pairs with pg_stash_advice extension
```
A mini-language to capture planner decisions from a plan and re-enforce them later (plan
stability / experimentation). New in PG19 (beta). `(pg19+)`. **Beta — interface may change.**

### `passwordcheck` — reject weak passwords
```ini
# shared_preload_libraries = 'passwordcheck'  → restart
```
Hooks `CREATE/ALTER ROLE ... PASSWORD` to enforce password policy. Bedrock.

### `auth_delay` — pause after a failed login
```ini
# shared_preload_libraries = 'auth_delay'  → restart;  auth_delay.milliseconds = 500
```
Adds a delay after authentication failures to slow brute-force attacks. Bedrock.

### `basic_archive` — example WAL archive module *(pg15+)*
An archive-library example (`archive_library = 'basic_archive'`) showing the archive-module
API. `(pg15+, the archive-module API release).`

### `basebackup_to_shell` — stream base backups to a shell command *(pg15+)*
Adds a `shell` target to `pg_basebackup` server-side. `(pg15+).`

### `sepgsql` — SELinux label-based MAC
Mandatory access control integrating with SELinux; requires `shared_preload_libraries`,
a setup SQL script, and a labeled OS. Superuser/sysadmin. Bedrock.

### `test_decoding` — example logical-decoding output plugin
Not an extension you `CREATE`; selected as the output plugin when creating a logical
replication/decoding slot. Primarily a test/example. Bedrock.

---

## Client programs (binaries, not extensions)

These are standalone command-line tools built from `contrib/` — **not** loaded into the
server and **not** `CREATE EXTENSION`:

- **`oid2name`** — map filenode/OID numbers on disk to database/table names (storage
  debugging).
- **`vacuumlo`** — remove orphaned large objects from a database.

---

## Deprecated / legacy

### `xml2` — legacy XPath functions
```sql
CREATE EXTENSION xml2;
```
Provides `xpath_table()` and older XPath helpers. **Deprecated** — prefer the core
`xml` type and SQL/XML functions (`xpath()`, `XMLTABLE`). Kept only for migration. Bedrock.

### `adminpack` — pgAdmin server-file helper *(removed in pg17)*
Historically a `contrib` module of file-management functions for old pgAdmin III. **Removed
from contrib in PostgreSQL 17** (added 8.2) — it is not present in PG17+ source trees. If
`pg_upgrade` complains about `$libdir/adminpack`, `DROP EXTENSION adminpack;` in each
database first. (Listed here so you don't go looking for it.)
