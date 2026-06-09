# Extension Management — Exhaustive Reference

Everything about installing, upgrading, relocating, inspecting, dumping, and removing
PostgreSQL extensions, plus the on-disk file model and the system catalogs. For the
catalog of *which* modules exist, see [contrib-catalog.md](contrib-catalog.md); for
version annotations see [version-features.md](version-features.md).

## Contents

- [CREATE EXTENSION](#create-extension)
- [ALTER EXTENSION](#alter-extension)
- [DROP EXTENSION](#drop-extension)
- [CASCADE — install vs. drop](#cascade--install-vs-drop)
- [The on-disk extension file model](#the-on-disk-extension-file-model)
- [Upgrade scripts & version paths](#upgrade-scripts--version-paths)
- [System catalogs & views](#system-catalogs--views)
- [Schemas, relocatability & search_path](#schemas-relocatability--search_path)
- [Trusted extensions](#trusted-extensions)
- [shared_preload_libraries & restart matrix](#shared_preload_libraries--restart-matrix)
- [Dump / restore & pg_upgrade](#dump--restore--pg_upgrade)
- [Configuration tables inside extensions](#configuration-tables-inside-extensions)

## CREATE EXTENSION

```
CREATE EXTENSION [ IF NOT EXISTS ] extension_name
    [ WITH ] [ SCHEMA schema_name ]
             [ VERSION version ]
             [ CASCADE ]
```

- **`IF NOT EXISTS`** — no error (a notice instead) if the extension is already installed.
  Essential for idempotent migrations.
- **`SCHEMA schema_name`** — install the extension's objects into this schema.
  - The schema must already exist, unless `CASCADE` is also given (then it's created).
  - Only meaningful for **relocatable** extensions, or for a non-relocatable extension that
    does not hard-code its schema. If the control file pins a `schema`, that wins.
  - Determines where the objects live for `search_path` purposes — a frequent gotcha.
- **`VERSION version`** — install a specific version present on disk (default:
  the control file's `default_version`). Quote non-identifier versions: `VERSION '1.2'`.
- **`CASCADE`** — automatically `CREATE EXTENSION` any **required** extensions (recursively),
  and create the target schema if missing. See [CASCADE](#cascade--install-vs-drop).

Requires **superuser**, unless the extension is [trusted](#trusted-extensions) (then any
role with `CREATE` on the current database may install it). The command runs the
extension's install script as the bootstrapping role and records every created object as a
member of the extension in `pg_depend`/`pg_extension`.

## ALTER EXTENSION

```
-- Upgrade to a new version (runs upgrade scripts on disk):
ALTER EXTENSION name UPDATE [ TO new_version ];

-- Move a relocatable extension's objects to another schema:
ALTER EXTENSION name SET SCHEMA new_schema;

-- Add/remove an existing object to/from extension membership (used by upgrade scripts,
-- and to adopt manually-created objects):
ALTER EXTENSION name ADD  member_object;
ALTER EXTENSION name DROP member_object;
```

- **`UPDATE`** runs the chain of upgrade scripts (`name--old--new.sql`) to bring the
  installed version up to `new_version` (or the newest available if `TO` is omitted). This
  changes the **extension's** version, never the server release.
- **`SET SCHEMA`** only works if the extension is relocatable and all its objects are in a
  single schema. Objects explicitly placed elsewhere block it.
- **`ADD`/`DROP`** change membership only; `DROP` here does **not** drop the object (unlike
  `DROP EXTENSION`). Mostly used internally by upgrade scripts.

## DROP EXTENSION

```
DROP EXTENSION [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

- Removes the extension **and all objects it owns** (its functions, types, operators,
  tables it created, etc.).
- **`RESTRICT`** (default) — refuse if any object *outside* the extension depends on one of
  its members (e.g. a user table column typed `hstore`, or an index using `gin_trgm_ops`).
- **`CASCADE`** — also drop those external dependents. **Destructive** — a column of an
  extension type, or every index built on its operator class, will be dropped. Always try
  `RESTRICT` first and read the dependency error.
- **`IF EXISTS`** — no error if it isn't installed.

## CASCADE — install vs. drop

`CASCADE` means opposite directions on the two commands:

| Command | `CASCADE` effect | Direction |
|---|---|---|
| `CREATE EXTENSION x CASCADE` | install x's **required** extensions (and create a missing schema) | pulls **dependencies in** |
| `DROP EXTENSION x CASCADE` | drop everything that **depends on** x | pushes **dependents out** |

Example where `CREATE … CASCADE` shines: `earthdistance` requires `cube`.
`CREATE EXTENSION earthdistance CASCADE;` installs `cube` first, then `earthdistance`.

## The on-disk extension file model

An extension is defined by files in the PostgreSQL **`SHAREDIR/extension/`** directory
(find it with `pg_config --sharedir`), installed by the OS package or `make install`:

- **`name.control`** — the manifest. Key fields:
  - `default_version` — the version `CREATE EXTENSION` installs absent an explicit `VERSION`
    (this is the **extension's** version, **not** the PostgreSQL release).
  - `comment` — shown in `\dx` / `pg_available_extensions.comment`.
  - `relocatable` (`true`/`false`) — may its schema be changed with `SET SCHEMA`.
  - `schema` — if set, the fixed schema the extension installs into.
  - `requires` — comma-separated prerequisite extensions (drives `CASCADE`).
  - `superuser` (default `true`) / `trusted` — who may install it (see
    [Trusted extensions](#trusted-extensions)).
  - `module_pathname` — `$libdir/...` for extensions with a C library.
- **`name--version.sql`** — the install script that creates the objects for that version.
- **`name--old--new.sql`** — upgrade scripts (see below).
- An optional compiled **`$libdir/name.so`** for C-language extensions.

`CREATE EXTENSION` never reads files outside this directory, which is why the error
"could not open extension control file" always means **the package isn't installed on the
server** — `CREATE EXTENSION` only registers what already exists on disk.

## Upgrade scripts & version paths

Extensions version their *own* schema independently of the server. Upgrades are expressed
as scripts named `name--FROM--TO.sql`. `ALTER EXTENSION name UPDATE TO 'X'` finds a path
(possibly multi-hop, e.g. `1.0→1.1→1.2`) from the installed version to `X` and runs each
script in order. There is no downgrade mechanism — paths are forward-only unless the author
ships explicit reverse scripts.

This is why, **after a major PostgreSQL upgrade or after installing a newer contrib
package**, you should run `ALTER EXTENSION … UPDATE` for each extension: the newer package
drops newer `--X--Y.sql` files on disk, but your databases keep the old `installed_version`
until you ask for the update. `pg_upgrade` migrates the *data* but does not bump extension
versions.

Find extensions lagging behind their newest on-disk version:

```sql
SELECT name, installed_version, default_version
FROM pg_available_extensions
WHERE installed_version IS NOT NULL
  AND installed_version IS DISTINCT FROM default_version;
```

## System catalogs & views

| Object | What it shows |
|---|---|
| `pg_extension` (catalog) | One row per **installed** extension: `extname`, `extversion`, `extnamespace` (schema), `extrelocatable`, `extconfig`/`extcondition` (config tables). |
| `pg_available_extensions` (view) | One row per extension **available on disk**: `name`, `default_version`, `installed_version` (NULL if not installed), `comment`. (pg19+ adds `location`.) |
| `pg_available_extension_versions` (view) | One row per **available version**: `name`, `version`, `installed`, `superuser`, `trusted`, `relocatable`, `schema`, `requires`, `comment`. The place to check the **`trusted`** flag. (pg19+ adds `location`.) |
| `pg_depend` / `pg_shdepend` | Dependency edges; how `DROP … RESTRICT` decides what blocks a drop. |

psql shortcuts: `\dx` (installed extensions), `\dx+ name` (the objects a given installed
extension owns).

```sql
-- Is extension X installed, and at what version?
SELECT extname, extversion FROM pg_extension WHERE extname = 'pg_trgm';

-- Which available extensions are trusted (installable by non-superusers)?
SELECT name, version, trusted, superuser
FROM pg_available_extension_versions WHERE trusted;
```

## Schemas, relocatability & search_path

- An extension's objects live in **one schema** (chosen at `CREATE` time via `SCHEMA`, or
  fixed by the control file's `schema`, or the first schema on `search_path`).
- **`search_path` gotcha:** if you install, say, `pg_trgm` `WITH SCHEMA ext` and `ext` is
  not on your `search_path`, then `similarity(...)`, the `%` operator, and `gin_trgm_ops`
  appear "not to exist." Fix by schema-qualifying, or `ALTER ROLE/DATABASE … SET search_path
  = "$user", public, ext;`.
- A common hardening pattern is a dedicated `extensions` schema kept on `search_path`, so
  application code need not qualify extension objects but they're isolated from `public`.
- **Relocatable** extensions (`relocatable = true`) can be moved later with
  `ALTER EXTENSION … SET SCHEMA`. Non-relocatable ones cannot (their scripts reference their
  schema explicitly).
- Note: types and operators are found via `search_path` like any other object, so moving an
  extension's schema can require updating clients' `search_path`.

## Trusted extensions

(pg13+.) Normally `CREATE EXTENSION` requires **superuser**. An extension whose control
file sets `trusted = true` can instead be installed by **any role with `CREATE` privilege
on the current database** — the role temporarily acts with the bootstrap superuser's rights
for the duration of the script, but only for these vetted modules that "cannot provide
access to outside-the-database functionality."

The contrib extensions trusted in a default installation (from in-tree
`doc/src/sgml/contrib.sgml`):

```
btree_gin  btree_gist  citext  cube  dict_int  fuzzystrmatch  hstore  intarray
isn  lo  ltree  pgcrypto  pg_trgm  seg  tablefunc  tcn  tsm_system_rows
tsm_system_time  unaccent  uuid-ossp
```

The PL transform extensions whose control files also set `trusted` (paired with the trusted
`plperl`): `bool_plperl` and `jsonb_plperl` only (the `*u` variants and the other transforms
such as `hstore_plperl` are **not** trusted — `*u` pair with the untrusted `plperlu`).

**Not trusted** (need superuser): `postgres_fdw`, `dblink`, `file_fdw`, `pg_stat_statements`,
and all the inspection/forensics modules (`pageinspect`, `pg_buffercache`, `pgstattuple`,
`amcheck`, `pg_surgery`, `pg_walinspect`, `pg_visibility`, `pg_freespacemap`,
`pg_logicalinspect`, …) — they read raw storage or reach outside the database. Verify per
server with `SELECT name, trusted FROM pg_available_extension_versions;`.

## shared_preload_libraries & restart matrix

Some modules hook into the backend at process start and **must** be loaded via
`shared_preload_libraries` in `postgresql.conf`, then the server **restarted**. (Editing
that GUC is **postgres-admin**'s territory; here is just which modules need it.)

| Module | Load requirement | `CREATE EXTENSION` too? |
|---|---|---|
| `pg_stat_statements` | `shared_preload_libraries` + **restart** | **Yes** — for the SQL views |
| `auto_explain` | `session_preload_libraries`/`shared_preload_libraries`, or `LOAD 'auto_explain'` per session | No — LOAD-only module |
| `pg_prewarm` (autoprewarm worker) | `shared_preload_libraries` + restart (pg11+) | The base `pg_prewarm()` function does **not** need preload |
| `passwordcheck` | `shared_preload_libraries` + restart | No |
| `auth_delay` | `shared_preload_libraries` + restart | No |
| `sepgsql` | `shared_preload_libraries` + setup script + labeled OS | No |
| `basic_archive` | `archive_library = 'basic_archive'` + restart (pg15+) | No |
| `basebackup_to_shell` | `shared_preload_libraries` (pg15+) | No |
| `pg_overexplain` | `LOAD 'pg_overexplain'` or `*_preload_libraries` (pg18+) | No — LOAD-only |
| `pg_plan_advice` | `LOAD 'pg_plan_advice'` (pg19+) | No — LOAD-only (pairs with `pg_stash_advice`) |

Most other contrib extensions (`pg_trgm`, `hstore`, `pageinspect`, `postgres_fdw`, …) need
**no** preload and **no** restart — just `CREATE EXTENSION`.

## Dump / restore & pg_upgrade

- `pg_dump` dumps **`CREATE EXTENSION name;`**, *not* the individual objects the extension
  owns. On restore, the extension's current install script recreates those objects. This
  keeps dumps portable across extension versions — but the target server must have the
  extension's files installed on disk.
- Data in **user tables that an extension marked as configuration** (e.g. a rules/dictionary
  table) **is** dumped — see [Configuration tables](#configuration-tables-inside-extensions).
- After `pg_upgrade` to a new major release, run `ALTER EXTENSION … UPDATE` to apply any new
  upgrade scripts the newer packages shipped.
- Removed modules bite here: e.g. `adminpack` (removed pg17) must be `DROP EXTENSION`-ed
  from every database before upgrading to a server that no longer ships it.

## Configuration tables inside extensions

An extension can designate a table it created as **user-configurable data** so its contents
are included in dumps (not just the table definition), via the C call
`pg_extension_config_dump('tablename', 'WHERE …')`. You inspect which tables are so marked
through `pg_extension.extconfig` (array of table OIDs) and `extcondition` (per-table dump
filters). This is how, for example, a custom dictionary or rules table belonging to an
extension survives `pg_dump`/restore. Relevant when authoring extensions or auditing what a
dump will carry.
