# psql Connections

How `psql` finds a server and authenticates. `psql` is a thin wrapper over **libpq**, so it
understands the same connection strings, URIs, environment variables, password file, and service
files that every libpq client does. Almost none of this is version-gated — it's bedrock.

## Contents

- [The four ways to specify a connection](#the-four-ways-to-specify-a-connection)
- [Connection flags](#connection-flags)
- [conninfo strings & URIs](#conninfo-strings--uris)
- [Environment variables](#environment-variables)
- [The password file (`~/.pgpass`)](#the-password-file-pgpass)
- [Connection service files](#connection-service-files)
- [Reconnecting with `\c`](#reconnecting-with-c)
- [SSL / TLS & multi-host](#ssl--tls--multi-host)
- [Precedence](#precedence)

## The four ways to specify a connection

1. **Discrete flags**: `psql -h host -p 5432 -U user -d dbname`
2. **A conninfo string or URI** (as the `-d`/dbname argument):
   `psql "host=db user=me dbname=app sslmode=require"` or `psql postgresql://me@db/app`
3. **Environment variables**: `PGHOST`, `PGPORT`, `PGUSER`, `PGDATABASE`, `PGPASSWORD`, …
4. **A service entry**: `psql service=prod` (looked up in `~/.pg_service.conf`)

These can be mixed; see [Precedence](#precedence).

## Connection flags

| Flag | Meaning | Env default |
|---|---|---|
| `-h HOST` / `--host` | Host name, or a directory path → Unix socket | `PGHOST` |
| `-p PORT` / `--port` | TCP port or socket file extension | `PGPORT` (else 5432) |
| `-U USER` / `--username` | Role to connect as | `PGUSER` (else OS user) |
| `-d DBNAME` / `--dbname` | Database name **or a full conninfo/URI** | `PGDATABASE` (else username) |
| `-w` / `--no-password` | Never prompt for a password (fail instead) — for scripts/CI | |
| `-W` / `--password` | Force a password prompt up front | |
| `-l` / `--list` | List databases and exit (connects to `postgres`) | |

The first non-option argument is taken as the dbname; a second as the username. So
`psql mydb alice` ≡ `psql -d mydb -U alice`.

> **No password on the command line.** There is intentionally no `-P password` flag — a password
> in `argv` is visible in `ps`/shell history. Use `~/.pgpass`, the `PGPASSWORD` env var (only
> marginally better), or an interactive prompt.

## conninfo strings & URIs

Two interchangeable formats, accepted anywhere a dbname is expected (the `-d` value, the `\c`
argument, etc.).

**Keyword/value (conninfo):**

```bash
psql "host=db.example.com port=5432 dbname=app user=me sslmode=require connect_timeout=10"
psql "service=prod application_name=deploy"
```

**URI:**

```
postgresql://[user[:password]@][host][:port][/dbname][?param=value&...]
postgres://...        # both schemes are accepted
```

```bash
psql postgresql://me@db.example.com:5432/app?sslmode=require
psql "postgresql:///app?host=/var/run/postgresql"     # socket dir via query param
postgresql://user@host1:5432,host2:5432/app?target_session_attrs=primary   # multi-host
```

Common parameters: `host`, `hostaddr`, `port`, `dbname`, `user`, `password`, `passfile`,
`sslmode`, `connect_timeout`, `application_name`, `options`, `target_session_attrs`, `service`,
`channel_binding`. The full list is the libpq
[parameter keywords](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-PARAMKEYWORDS).

> **Lock down `search_path` for untrusted servers/databases:** add
> `options=-csearch_path=` to the conninfo (or run `SELECT pg_catalog.set_config('search_path','',false);`
> first) so a writable schema can't shadow catalog objects.

## Environment variables

`psql` honors all libpq environment variables. The ones you'll use most:

| Variable | Sets |
|---|---|
| `PGHOST` / `PGPORT` | Host (or socket dir) / port |
| `PGUSER` / `PGDATABASE` | Role / database |
| `PGPASSWORD` | Password (convenient in CI; prefer `~/.pgpass` — env vars leak via `/proc` & `ps -E`) |
| `PGPASSFILE` | Alternate password-file path (default `~/.pgpass`) |
| `PGSERVICE` / `PGSERVICEFILE` | Service name / alternate service file |
| `PGSSLMODE` / `PGSSLROOTCERT` | TLS mode / CA cert |
| `PGAPPNAME` | `application_name` (shows in `pg_stat_activity` & logs) |
| `PGOPTIONS` | Extra server options, e.g. `-c statement_timeout=5000` |
| `PGCLIENTENCODING` | Client encoding (else auto-detected from locale on a TTY) |

psql-specific environment variables (editor, pager, history) are covered in
[scripting.md](scripting.md#environment).

## The password file (`~/.pgpass`)

A per-user file of passwords, consulted when a password is needed and none was supplied. The
preferred approach for unattended scripts.

- **Path:** `~/.pgpass` (Unix) or `%APPDATA%\postgresql\pgpass.conf` (Windows); override with
  `PGPASSFILE`.
- **Permissions:** on Unix it **must** be `0600` (no group/world access) or it is silently
  ignored: `chmod 0600 ~/.pgpass`.
- **Format**, one entry per line:

  ```
  hostname:port:database:username:password
  ```

  Each of the first four fields may be `*` (matches anything); the **first matching line wins**, so
  put specific entries before wildcards. Escape a literal `:` or `\` with a backslash. The hostname
  is matched against `host` (or `hostaddr`, else `localhost`); a Unix-socket connection matches
  `localhost`. A `database` of `replication` matches replication connections.

  ```
  # host          port  db    user      password
  db.example.com  5432  app   deploy    s3cr3t
  *               5432  *     readonly  r0pass
  ```

## Connection service files

Name a bundle of connection parameters once, then connect with `service=NAME` (or `PGSERVICE`).

- **Per-user file:** `~/.pg_service.conf` (Windows `%APPDATA%\postgresql\.pg_service.conf`);
  override with `PGSERVICEFILE`.
- **System-wide:** `pg_service.conf` under `pg_config --sysconfdir` (override the *directory* with
  `PGSYSCONFDIR`). The user file wins on name conflicts.
- **Format:** INI — a `[service-name]` section header followed by libpq `key=value` parameters.

  ```ini
  # ~/.pg_service.conf
  [prod]
  host=db.prod.example.com
  port=5432
  dbname=app
  user=app_ro
  sslmode=require

  [local]
  host=/var/run/postgresql
  dbname=app
  ```

  ```bash
  psql service=prod
  PGSERVICE=prod psql -c '\conninfo'
  ```

In pg19+, the `SERVICEFILE` `psql` variable reports which service file is in effect.

## Reconnecting with `\c`

```
\c [ -reuse-previous=on|off ] [ dbname [ username [ host [ port ] ] ] | conninfo ]
```

- Positional form **reuses** unspecified parameters (incl. `sslmode`, password if user/host/port
  unchanged); a `conninfo`/URI form does **not** reuse by default. Override with
  `-reuse-previous=on|off`.
- Use `-` for any positional slot to mean "omit/default it".

```sql
\c otherdb                    -- same host/user/port, switch database
\c - readonly                 -- same db/host/port, switch user
\c "host=replica sslmode=require"
\c postgresql://tom@localhost/mydb?application_name=myapp
```

In a non-interactive script, a failed `\c` closes the old connection and reports an error
(deliberately, so a script can't silently keep acting on the wrong database); interactively, the
old connection is kept.

## SSL / TLS & multi-host

- `sslmode=` ladder: `disable` < `allow` < `prefer` (default) < `require` < `verify-ca` <
  `verify-full`. Use **`verify-full`** for real security (checks the cert chain *and* hostname).
- Provide trust material via `sslrootcert=`/`PGSSLROOTCERT`, client certs via
  `sslcert=`/`sslkey=`.
- **Multi-host failover:** list hosts/ports comma-separated and add
  `target_session_attrs=primary|read-write|read-only|standby|prefer-standby` to pick a node by role
  (handy with replicas/HA).

```bash
psql "host=node1,node2,node3 port=5432 dbname=app target_session_attrs=read-write"
```

`\conninfo` reports the negotiated host, port, user, database, and SSL status (tabular in pg18+).

## Precedence

When the same parameter is set multiple ways, the effective value is (highest first):

1. A **conninfo/URI** parameter (when given as the dbname) — overrides conflicting discrete flags.
2. **Discrete command-line flags** (`-h`/`-U`/…).
3. **Environment variables** (`PGHOST`/…).
4. **Service file** entries (`service=`).
5. Compiled-in **libpq defaults** (localhost socket, port 5432, OS user, etc.).

The psql docs note specifically: when a connection string is passed to `-d`, its parameters
**override** conflicting command-line options.
