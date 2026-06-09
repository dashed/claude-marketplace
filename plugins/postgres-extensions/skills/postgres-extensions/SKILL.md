---
name: postgres-extensions
description: PostgreSQL extension management and the bundled `contrib` catalog. Use when running `CREATE EXTENSION` / `ALTER EXTENSION ... UPDATE` / `DROP EXTENSION`, listing extensions (`\dx`, `pg_available_extensions`), or choosing which contrib module enables a feature — FDWs (`postgres_fdw`, `dblink`, `file_fdw`), trigram/fuzzy search (`pg_trgm`, `fuzzystrmatch`), crypto/UUIDs (`pgcrypto`, `gen_random_uuid`), types `hstore`/`ltree`/`citext`/`cube`, query stats (`pg_stat_statements`, `auto_explain`), index helpers (`btree_gin`, `btree_gist`, `bloom`), or storage forensics (`pageinspect`, `amcheck`, `pg_surgery`). Also covers trusted (non-superuser) extensions, `shared_preload_libraries`, and `CASCADE`. Disambiguation — extension management plus the contrib catalog; use psql for the client, postgres-sql for core SQL, postgres-performance for tuning *with* these extensions, postgres-admin for server config. Version notes are inline `(pgNN+)`; bedrock modules are unannotated, see references/version-features.md.
---

# PostgreSQL Extensions & the contrib Catalog

## Overview

A PostgreSQL **extension** is a packaged bundle of SQL objects — functions, data
types, operators, index access methods, casts, even C libraries — that you install
into a database with a single `CREATE EXTENSION` command and remove just as cleanly
with `DROP EXTENSION`. PostgreSQL tracks every object an extension owns, so the whole
unit can be upgraded, relocated to another schema, or dumped/restored atomically.

**`contrib`** is the set of extensions and modules that ship *in the PostgreSQL source
tree itself* (under `contrib/`) and are packaged by most distributions as a
`postgresql-contrib` package. They are official, versioned with the server, and
maintained by the core project — but **not installed into a database until you ask**.
This skill is the map of that ecosystem plus the commands to manage it.

**Key mental model:**
- **An extension is a managed unit, not loose SQL.** `CREATE EXTENSION pg_trgm;` is not
  the same as running its SQL by hand — Postgres records membership in `pg_extension`
  so `DROP`/`ALTER ... UPDATE` work.
- **`contrib` ships with the server but is dormant.** The files live on disk (often a
  separate OS package); `CREATE EXTENSION` activates one *per database*.
- **Two version numbers, do not conflate them.** The extension's own version (e.g.
  `pg_stat_statements` 1.13, from its `.control` `default_version`) is independent of
  the PostgreSQL release (e.g. 18). See [Two version numbers](#two-version-numbers).
- **Some extensions need a server restart**, because they hook into the backend via
  `shared_preload_libraries` (e.g. `pg_stat_statements`, `auto_explain`). Most don't.

> **Disambiguation.** This skill = **extension management + the bundled contrib
> catalog**. For the **`psql`** client (`\dx`, meta-commands) use the **psql** skill;
> for **core SQL / dialect** use **postgres-sql**; for **using perf extensions to
> actually tune queries** use **postgres-performance** (this skill only points at
> them); for **server configuration** like editing `shared_preload_libraries` or
> `postgresql.conf` use **postgres-admin**. External extensions (PostGIS, pgvector,
> TimescaleDB) are **not** in contrib — see [External extensions](#external-not-in-contrib).

## Version annotations

This skill targets the contrib set shipped with **PostgreSQL 18 (stable)**, with notes
for **19 (beta)**. Inline `(pgNN+)` marks the **first PostgreSQL release** a module or
feature shipped in. Modules present since the **old 9.x era are "bedrock" and carry no
tag** (e.g. `pgcrypto`, `pg_trgm`, `hstore`, `pg_stat_statements`). A tag means
"requires PostgreSQL NN or newer." The full feature → minimum-version map with sources
is in [references/version-features.md](references/version-features.md). Always confirm
against the running server (`SELECT version();`).

## When to use which approach

| You want to… | Use |
|---|---|
| Turn on a packaged feature in a database | `CREATE EXTENSION name;` |
| See what's installed vs. available | `\dx` · `pg_available_extensions` |
| Upgrade an extension's objects after a server upgrade | `ALTER EXTENSION name UPDATE;` |
| Remove an extension and everything it owns | `DROP EXTENSION name CASCADE;` |
| Pull in dependencies automatically | `CREATE EXTENSION name CASCADE;` |
| Let a non-superuser install a safe extension | a **trusted** extension (pg13+) |
| Enable a backend hook (stats, logging) | add to `shared_preload_libraries` + restart |

## Managing extensions

### Install

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;              -- idempotent
CREATE EXTENSION hstore WITH SCHEMA extensions;      -- put its objects in a chosen schema
CREATE EXTENSION earthdistance CASCADE;              -- also installs its prereq (cube)
CREATE EXTENSION pg_stat_statements VERSION '1.13';  -- pin a specific extension version
```

- `IF NOT EXISTS` makes it safe to re-run in migrations.
- `WITH SCHEMA s` installs the objects into schema `s` (the schema must exist, or use
  `CASCADE` to create it for a relocatable extension). This matters for `search_path`:
  if you install `pg_trgm` into a schema not on the path, you must schema-qualify its
  operators/functions or add the schema to `search_path`.
- `CASCADE` (pg9.6+) auto-installs required extensions **and** creates a missing target
  schema. Great for `earthdistance` (needs `cube`).
- `VERSION 'x.y'` installs a specific version if multiple are available on disk.

### Discover

```sql
\dx                          -- (psql) installed extensions in this database
\dx+ pg_trgm                 -- (psql) list the objects an installed extension owns
SELECT * FROM pg_available_extensions;          -- everything installable on disk
SELECT * FROM pg_available_extension_versions;  -- per-version, incl. the `trusted` flag
SELECT extname, extversion FROM pg_extension;   -- catalog of what's installed
```

`pg_available_extensions.default_version` is what `CREATE EXTENSION` installs if you
don't pin a version; `installed_version` is NULL until you create it. (pg19+ adds a
`location` column reporting the on-disk directory.)

### Upgrade

```sql
ALTER EXTENSION pg_stat_statements UPDATE;            -- to the newest version on disk
ALTER EXTENSION postgres_fdw UPDATE TO '1.2';         -- to a specific version
```

Run `ALTER EXTENSION ... UPDATE` **after a major PostgreSQL upgrade** (or after
installing a newer contrib package) to apply the extension's upgrade scripts — a
`pg_upgrade` migrates data but does **not** bump extension versions for you. Check for
stragglers:

```sql
SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE installed_version IS DISTINCT FROM default_version
  AND installed_version IS NOT NULL;
```

### Relocate / modify / remove

```sql
ALTER EXTENSION hstore SET SCHEMA extensions;   -- move a relocatable extension's objects
DROP EXTENSION IF EXISTS hstore;                -- fails if other objects depend on it
DROP EXTENSION hstore CASCADE;                  -- also drops dependents (be careful!)
```

`CASCADE` on `DROP` removes everything that depends on the extension (columns of its
types, indexes using its operator classes, …) — powerful and destructive. Prefer the
non-cascade form first to see what would break.

### Two version numbers

| Number | Example | Where it comes from | Meaning |
|---|---|---|---|
| **PostgreSQL release** | `18`, `19beta1` | `SELECT version();` / `server_version` | The database server version |
| **Extension version** | `pg_stat_statements 1.13` | the module's `.control` `default_version` | The extension's own object/schema version |

These move independently. `pg_stat_statements` being version **1.13** says nothing about
which PostgreSQL release you run — it's the extension's internal version, bumped by its
own upgrade scripts (`pg_stat_statements--1.12--1.13.sql`). In this skill, `(pgNN+)` tags
always mean the **PostgreSQL release**, never the extension's own number.

### Trusted extensions (pg13+)

By default `CREATE EXTENSION` requires superuser. A **trusted** extension can instead be
installed by any role with `CREATE` privilege on the database — these are the modules
that "cannot provide access to outside-the-database functionality." The contrib
extensions trusted in a default install are:

> `btree_gin`, `btree_gist`, `citext`, `cube`, `dict_int`, `fuzzystrmatch`, `hstore`,
> `intarray`, `isn`, `lo`, `ltree`, `pgcrypto`, `pg_trgm`, `seg`, `tablefunc`, `tcn`,
> `tsm_system_rows`, `tsm_system_time`, `unaccent`, `uuid-ossp` (plus the PL transforms
> like `bool_plperl`, `jsonb_plperl`).

Notably **not** trusted: `postgres_fdw`, `dblink`, `file_fdw`, `pg_stat_statements`,
`adminpack`, and the forensic/inspection modules — they reach outside the database or
need superuser.

### Extensions that need `shared_preload_libraries` (restart required)

A few modules hook into the backend at startup and must be listed in
`shared_preload_libraries` in `postgresql.conf`, then the server **restarted**:

| Module | Why preload |
|---|---|
| `pg_stat_statements` | accumulates per-query stats in shared memory |
| `auto_explain` | hooks executor end to log plans (can also `LOAD` per session) |
| `pg_prewarm` | only the `autoprewarm` background worker needs preload (pg11+); the `pg_prewarm()` function does not |
| `passwordcheck`, `auth_delay`, `sepgsql`, `basic_archive`, `basebackup_to_shell` | server-side hooks/policies |

After preloading, you still run `CREATE EXTENSION pg_stat_statements;` to get the SQL
views. **For editing `shared_preload_libraries` and other server config, see the
postgres-admin skill.** `auto_explain` and `pg_overexplain` (pg18+) can alternatively be
loaded for one session with `LOAD 'auto_explain';`.

## The contrib catalog — highlights

One-liners and the most-used snippets. The **full catalog of every bundled module** —
grouped, with usage examples and version notes — is in
[references/contrib-catalog.md](references/contrib-catalog.md).

### Text, fuzzy & full-text search
```sql
CREATE EXTENSION pg_trgm;       -- trigram similarity + GIN/GiST index for LIKE/regex/typo search
SELECT similarity('postgres', 'postgers');                    -- 0.5
CREATE INDEX ON docs USING gin (body gin_trgm_ops);           -- fast ILIKE '%term%'

CREATE EXTENSION fuzzystrmatch; -- phonetic & edit-distance matching
SELECT levenshtein('kitten','sitting'), soundex('Robert');    -- 3 | R163

CREATE EXTENSION unaccent;      -- strip accents (also a FTS dictionary)
SELECT unaccent('café');                                      -- cafe
```

### Useful data types
```sql
CREATE EXTENSION citext;   -- case-insensitive text; use as a column type
CREATE EXTENSION hstore;   -- key/value in one column:  'a=>1, b=>2'::hstore ; index with GIN
CREATE EXTENSION ltree;    -- hierarchical label paths:  'Top.Science.Astronomy'::ltree ; @>, <@, ~
CREATE EXTENSION cube;     -- multidimensional cubes / points (prereq for earthdistance)
CREATE EXTENSION isn;      -- validated ISBN/ISSN/EAN13/UPC types
SELECT 'a=>1'::hstore -> 'a';                                 -- 1
```

### Foreign data & external access
```sql
CREATE EXTENSION postgres_fdw;          -- query tables in another PostgreSQL server
CREATE SERVER remote FOREIGN DATA WRAPPER postgres_fdw
  OPTIONS (host 'db2', dbname 'app');
CREATE USER MAPPING FOR CURRENT_USER SERVER remote OPTIONS (user 'app', password '...');
IMPORT FOREIGN SCHEMA public FROM SERVER remote INTO remote_public;

CREATE EXTENSION file_fdw;              -- read a CSV/text file as a table
CREATE EXTENSION dblink;                -- ad-hoc connections to other PG databases
```

### Crypto & UUIDs
```sql
CREATE EXTENSION pgcrypto;              -- hashing, encryption, HMAC, random bytes
SELECT crypt('secret', gen_salt('bf')); -- bcrypt password hash
-- gen_random_uuid() is BUILT INTO CORE since pg13 — no extension needed:
SELECT gen_random_uuid();
CREATE EXTENSION "uuid-ossp";           -- only for v1/v3/v5 UUID algorithms (quote the hyphen)
```

### Query statistics & plan logging (point to postgres-performance for tuning)
```sql
-- needs shared_preload_libraries = 'pg_stat_statements' + restart, then:
CREATE EXTENSION pg_stat_statements;
SELECT query, calls, total_exec_time FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 5;
```
```sql
-- auto_explain has NO CREATE EXTENSION — it is a LOAD-only module (logs slow query plans):
LOAD 'auto_explain';                    -- per session (superuser); or set in *_preload_libraries
SET auto_explain.log_min_duration = '500ms';
```
**These are diagnostic plumbing. For how to *interpret and act* on them to tune queries,
use the postgres-performance skill.**

### Indexing helpers
```sql
CREATE EXTENSION btree_gist;   -- B-tree ops in GiST → enables EXCLUDE constraints / range overlaps
CREATE EXTENSION btree_gin;    -- B-tree ops in GIN → combine scalar = with array/jsonb in one index
CREATE EXTENSION bloom;        -- bloom-filter index AM for multi-column equality filters
```

### Table functions & misc
```sql
CREATE EXTENSION tablefunc;    -- crosstab() pivot, connectby(), normal_rand()
CREATE EXTENSION earthdistance CASCADE;  -- great-circle distance (pulls in cube)
```

### Storage inspection & forensics (mostly superuser)
```sql
CREATE EXTENSION pageinspect;      -- raw page/tuple internals (heap_page_items, etc.)
CREATE EXTENSION pg_buffercache;   -- what's in shared_buffers; pg_buffercache_evict() (pg17+)
CREATE EXTENSION pgstattuple;      -- physical tuple/bloat stats: pgstattuple('t'), pgstatindex('i')
CREATE EXTENSION pg_visibility;    -- visibility-map state per page
CREATE EXTENSION amcheck;          -- verify index/heap integrity: bt_index_check('i') (pg10+)
CREATE EXTENSION pg_surgery;       -- LAST-RESORT corruption repair: heap_force_kill/heap_force_freeze (pg14+)
CREATE EXTENSION pg_walinspect;    -- decode WAL records in SQL: pg_get_wal_record_info(lsn) (pg15+)
CREATE EXTENSION pg_freespacemap;  -- free-space-map contents: pg_freespace('t')
CREATE EXTENSION pg_prewarm;       -- load a relation into cache: pg_prewarm('t')
CREATE EXTENSION pg_logicalinspect; -- inspect logical-decoding snapshots (pg18+)
LOAD 'pg_overexplain';             -- extra EXPLAIN detail; LOAD-only, no CREATE EXTENSION (pg18+)
```

### External (not in contrib)
These ubiquitous extensions are **not** bundled — install them separately from their own
projects/packages:
- **PostGIS** — full geospatial (geometry/geography, spatial indexing). For simple
  great-circle distance only, contrib `earthdistance` may suffice.
- **pgvector** — `vector` type + ANN indexes for embeddings/similarity search.
- **TimescaleDB** — time-series hypertables, continuous aggregates.

After installing the OS package/build, they still activate via `CREATE EXTENSION postgis;`
etc. — the management commands above are identical.

## Troubleshooting

- **`ERROR: could not open extension control file ".../name.control": No such file`** —
  the extension's files aren't installed on the server. Install the OS package (e.g.
  `postgresql-contrib`, or `postgresql18-contrib`) or build it; `CREATE EXTENSION` only
  registers files that already exist on disk.
- **`ERROR: permission denied to create extension "X" — Hint: Must have CREATE privilege
  ... or be superuser`** — it's not a trusted extension (or you lack `CREATE` on the DB).
  See [Trusted extensions](#trusted-extensions-pg13). Use a superuser, or pick a trusted
  alternative.
- **`ERROR: required extension "cube" is not installed`** — install the dependency first,
  or use `CREATE EXTENSION earthdistance CASCADE;`.
- **`pg_stat_statements` view is empty / "must be loaded via shared_preload_libraries"** —
  it wasn't preloaded. Add it to `shared_preload_libraries`, **restart**, then
  `CREATE EXTENSION`. (postgres-admin covers the config edit.)
- **Functions "do not exist" after install** — the extension was installed `WITH SCHEMA`
  a schema not on your `search_path`. Schema-qualify the call or add the schema to
  `search_path`.
- **A function/option errors on an older server** — it may be newer than your release.
  Check `SELECT version();` and the `(pgNN+)` tag / [references/version-features.md](references/version-features.md).
- **`DROP EXTENSION` fails with dependency errors** — other objects use its types/operators.
  Inspect with `\dx+ name`, then drop dependents or use `CASCADE` (destructive).
- **Confusing two version numbers** — `default_version` in a `.control` file is the
  *extension's* version, not the PostgreSQL release. See [Two version numbers](#two-version-numbers).

## References

- [references/management.md](references/management.md) — exhaustive `CREATE`/`ALTER`/`DROP
  EXTENSION` grammar, the `.control`/SQL upgrade-script file model, the system catalogs
  & views, relocatable schemas, dump/restore behavior, trusted-extension mechanics, and
  the `shared_preload_libraries` restart matrix.
- [references/contrib-catalog.md](references/contrib-catalog.md) — the complete catalog of
  every bundled `contrib` module, grouped by category, each with purpose, `CREATE
  EXTENSION` snippet, a tiny usage example, and version notes.
- [references/version-features.md](references/version-features.md) — extension/feature →
  minimum PostgreSQL version, the "how to read it" guide (incl. the `default_version` ≠
  PG-release distinction), the bedrock policy, and sources.

## Resources

- Additional Supplied Modules & Extensions (official): https://www.postgresql.org/docs/current/contrib.html
- `CREATE EXTENSION`: https://www.postgresql.org/docs/current/sql-createextension.html
- Packaging Related Objects into an Extension: https://www.postgresql.org/docs/current/extend-extensions.html
