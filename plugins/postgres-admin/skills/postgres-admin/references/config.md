# Server Configuration (GUCs)

How PostgreSQL configuration works, how to change it safely, and the parameters a DBA touches
most. Settings are called **GUCs** (Grand Unified Configuration). Version tags `(pgNN+)` mark
features added in PostgreSQL 10+; untagged items are bedrock (9.x or earlier).

## Contents

- [The three configuration layers](#the-three-configuration-layers)
- [Inspecting settings: SHOW / pg_settings](#inspecting-settings-show--pg_settings)
- [Changing settings: SET / ALTER SYSTEM / ALTER ROLE / ALTER DATABASE](#changing-settings)
- [Reload vs restart (the context column)](#reload-vs-restart-the-context-column)
- [postgresql.conf syntax & includes](#postgresqlconf-syntax--includes)
- [Key parameters by area](#key-parameters-by-area)
- [Units & value formats](#units--value-formats)

## The three configuration layers

Effective value = the **highest-priority layer that sets it**, in this order (last wins):

1. **`postgresql.conf`** — the main hand-edited file in `$PGDATA` (or wherever the distro
   puts it; find it with `SHOW config_file`).
2. **`postgresql.auto.conf`** — machine-managed, in `$PGDATA`; written **only** by
   `ALTER SYSTEM` (since 9.4). Never hand-edit it. It overrides `postgresql.conf`.
3. **Session / role / database scope** — `SET` (current session), `ALTER ROLE … SET`,
   `ALTER DATABASE … SET` override the files for their scope.

```sql
SHOW config_file;        -- path to postgresql.conf
SHOW hba_file;           -- path to pg_hba.conf
SHOW data_directory;     -- $PGDATA
```

## Inspecting settings: SHOW / pg_settings

```sql
SHOW work_mem;                 -- one setting (human units)
SHOW ALL;                      -- every setting + short description
RESET work_mem;                -- back to the configured (non-session) value

-- pg_settings is the rich, queryable view:
SELECT name, setting, unit, context, vartype, min_val, max_val, boot_val, reset_val,
       source, sourcefile, sourceline, pending_restart
  FROM pg_settings WHERE name = 'max_wal_size';

-- Which settings are NOT at their default, and where they came from:
SELECT name, setting, source, sourcefile, sourceline
  FROM pg_settings
 WHERE source NOT IN ('default','override')
 ORDER BY source, name;

-- Settings that were changed but need a restart to take effect:
SELECT name, setting, pending_restart FROM pg_settings WHERE pending_restart;

-- See config files the server has loaded / any parse errors:
SELECT * FROM pg_file_settings;     -- per-line view of the conf files (pg9.5+)
```

`pg_file_settings` shows each line across all config files with an `applied` flag and an
`error` column — invaluable for spotting a setting that's overridden later in the file or
fails to parse.

## Changing settings

```sql
-- Cluster-wide, persistent (writes postgresql.auto.conf):
ALTER SYSTEM SET shared_buffers = '4GB';     -- needs RESTART (postmaster context)
ALTER SYSTEM SET log_min_duration_statement = '500ms';  -- needs only RELOAD
ALTER SYSTEM RESET log_min_duration_statement;          -- drop the override
ALTER SYSTEM RESET ALL;                       -- clear everything in auto.conf
SELECT pg_reload_conf();                       -- apply reloadable changes now

-- Narrower scopes:
SET work_mem = '256MB';                        -- this session only
SET LOCAL work_mem = '256MB';                  -- this transaction only
ALTER ROLE reporting SET work_mem = '512MB';   -- whenever this role connects
ALTER DATABASE analytics SET search_path = analytics, public;  -- per-database default
```

- `ALTER SYSTEM` is the modern, scriptable way to persist a change — no file editing, no
  risk of a typo breaking startup. It still **can't** override a setting given on the
  command line, and a handful of params can't be set this way (it warns).
- `SET LOCAL` is great inside a transaction/function for a temporary bump (e.g. raise
  `work_mem` for one heavy query) that auto-reverts at commit.

## Reload vs restart (the `context` column)

`pg_settings.context` tells you what's required to apply a change:

| `context` | Apply by | Notes / examples |
|---|---|---|
| `internal` | recompile / initdb | fixed at build (e.g. `block_size`) — read-only |
| `postmaster` | **server restart** | `shared_buffers`, `max_connections`, `listen_addresses`, `port`, `wal_level`, `max_wal_senders`, `shared_preload_libraries`, `max_worker_processes` |
| `sighup` | **reload** (`pg_reload_conf()` / `pg_ctl reload` / SIGHUP) | `log_*`, `autovacuum`, `checkpoint_timeout`, `max_wal_size`, `archive_command`, `work_mem` default |
| `superuser-backend` / `backend` | next connection | set at connection start |
| `superuser` | `SET` (superuser) or reload | |
| `user` | `SET` in any session | `statement_timeout`, `work_mem`, `search_path` |

```bash
pg_ctl reload  -D "$PGDATA"     # SIGHUP — no downtime; applies sighup-context settings
pg_ctl restart -D "$PGDATA" -m fast   # required for postmaster-context settings
# systemd equivalents:
systemctl reload postgresql       # or: systemctl restart postgresql
```

Rule of thumb: **memory/WAL sizing and anything affecting shared memory or process slots
needs a restart**; logging, autovacuum, planner, and statement-level knobs are reload-only.

## postgresql.conf syntax & includes

```conf
# name = value     (quotes optional unless the value has spaces/special chars)
shared_buffers = 4GB
log_line_prefix = '%m [%p] %q%u@%d '     # spaces → quote it
search_path = '"$user", public'

include 'extra.conf'                 # pull in another file (relative to this one)
include_if_exists 'local.conf'       # optional include
include_dir 'conf.d'                 # all *.conf in a directory (sorted)
```

`include_dir 'conf.d'` is the clean way to drop in package- or role-specific overrides.
Later settings win, so put overrides after the include — or use `ALTER SYSTEM`
(`postgresql.auto.conf` is read last regardless).

## Key parameters by area

### Memory
| Parameter | Meaning | Context |
|---|---|---|
| `shared_buffers` | shared cache of data pages (often ~25% RAM) | restart |
| `work_mem` | per-sort/hash operation memory (×many per query!) | reload/SET |
| `maintenance_work_mem` | memory for VACUUM, CREATE INDEX, etc. | reload/SET |
| `effective_cache_size` | planner's estimate of OS+DB cache (planning only) | reload/SET |
| `huge_pages` | use OS huge pages for shared memory | restart |

### WAL & checkpoints
| Parameter | Meaning | Context |
|---|---|---|
| `wal_level` | `minimal`/`replica`/`logical` — how much WAL detail | restart |
| `max_wal_size` / `min_wal_size` | soft ceiling/floor that drives checkpoint frequency | reload |
| `checkpoint_timeout` | max time between checkpoints | reload |
| `checkpoint_completion_target` | spread checkpoint I/O over this fraction of the interval | reload |
| `wal_compression` | compress full-page images in WAL | reload |
| `wal_keep_size` | WAL to retain for standbys (MB) — renamed from `wal_keep_segments` (pg13+) | reload |
| `archive_mode` / `archive_command` / `archive_library` | continuous WAL archiving for PITR | restart / reload |
| `summarize_wal` (pg17+) | enable WAL summarizer (prereq for incremental backups) | reload |
| `effective_wal_level` (pg19+) | read-only: the WAL level actually in effect | — |

### Connections
| Parameter | Meaning | Context |
|---|---|---|
| `max_connections` | hard cap on backends (each costs a process + memory) | restart |
| `superuser_reserved_connections` | slots held back for superusers | restart |
| `reserved_connections` (pg16+) | slots for `pg_use_reserved_connections` members | restart |
| `listen_addresses` | interfaces to listen on (`'*'` = all) | restart |
| `port` | TCP port | restart |
| `idle_in_transaction_session_timeout` | kill sessions idle in a transaction | reload/SET |
| `statement_timeout` | abort queries over this duration | reload/SET |
| `tcp_keepalives_*` | detect dead clients | reload |

### Autovacuum (config side — mechanics live in `postgres-performance`)
| Parameter | Meaning | Context |
|---|---|---|
| `autovacuum` | master on/off (leave **on**) | reload |
| `autovacuum_max_workers` | concurrent autovacuum workers | restart |
| `autovacuum_worker_slots` (pg18+) | worker slots so `max_workers` is runtime-adjustable | restart |
| `autovacuum_naptime` | sleep between autovacuum rounds | reload |
| `autovacuum_vacuum_scale_factor` / `_threshold` | when a table becomes eligible | reload |
| `autovacuum_max_parallel_workers` (pg19+) | parallel workers for autovacuum | reload |

### Logging (all `sighup` → reload)
| Parameter | Meaning |
|---|---|
| `log_destination` | `stderr`/`csvlog`/`jsonlog` (pg15+)/`syslog` |
| `logging_collector` | capture stderr to rotating log files (restart) |
| `log_min_duration_statement` | log statements slower than N (ms); `0` logs all |
| `log_line_prefix` | per-line metadata (`%m %p %u %d %a` …) |
| `log_connections` / `log_disconnections` | session lifecycle (pg18+: `log_connections` is multi-valued) |
| `log_checkpoints` | log each checkpoint (**on by default since pg15**) |
| `log_lock_waits` | log long lock waits (**on by default pg19+**) |
| `log_statement` | `none`/`ddl`/`mod`/`all` |
| `log_autovacuum_min_duration` | log autovacuum actions over N ms |

## Units & value formats

- **Memory/size:** `B`, `kB`, `MB`, `GB`, `TB` (e.g. `'4GB'`). Bare integers use the
  setting's base unit (see `pg_settings.unit`).
- **Time:** `us`, `ms`, `s`, `min`, `h`, `d` (e.g. `'500ms'`, `'30min'`).
- **Booleans:** `on`/`off`, `true`/`false`, `yes`/`no`, `1`/`0`.
- **Lists:** comma-separated (e.g. `shared_preload_libraries = 'pg_stat_statements,auto_explain'`).
  A list GUC can be emptied by setting it to `NULL` (pg19+).
- Always confirm the accepted unit and bounds via `pg_settings` (`unit`, `min_val`,
  `max_val`, `enumvals`).
