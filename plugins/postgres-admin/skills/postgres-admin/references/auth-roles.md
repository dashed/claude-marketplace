# Roles, Privileges & Authentication

Who can connect (authentication) and what they can do once in (authorization). Version tags
`(pgNN+)` mark features added in PostgreSQL 10+; untagged items are bedrock (9.x or earlier).

## Contents

- [Roles vs users](#roles-vs-users)
- [Creating & altering roles](#creating--altering-roles)
- [Role attributes](#role-attributes)
- [Object privileges (GRANT / REVOKE)](#object-privileges-grant--revoke)
- [DEFAULT PRIVILEGES](#default-privileges)
- [Schema & the public-schema change](#schema--the-public-schema-change)
- [Role membership (groups)](#role-membership-groups)
- [Predefined (built-in) roles](#predefined-built-in-roles)
- [Authentication: pg_hba.conf](#authentication-pg_hbaconf)
- [Authentication methods](#authentication-methods)
- [SCRAM & password encryption](#scram--password-encryption)
- [pg_ident.conf (user name maps)](#pg_identconf-user-name-maps)
- [TLS / SSL](#tls--ssl)

## Roles vs users

PostgreSQL has **one concept: the role**. A "user" is a role with the `LOGIN` attribute; a
"group" is a role without it. Roles are **cluster-global** (shared across all databases).
`CREATE USER` is just `CREATE ROLE … LOGIN`.

## Creating & altering roles

```sql
CREATE ROLE app LOGIN PASSWORD 'secret';
CREATE ROLE readonly;                          -- NOLOGIN group role (the default)
CREATE ROLE ops LOGIN CREATEDB CREATEROLE VALID UNTIL '2027-01-01';

ALTER ROLE app PASSWORD 'newsecret';           -- rotate password (re-hashed per password_encryption)
ALTER ROLE app CONNECTION LIMIT 20;
ALTER ROLE app VALID UNTIL 'infinity';
ALTER ROLE app SET search_path = app, public;  -- per-role GUC default
ALTER ROLE app RENAME TO app_v2;
DROP ROLE app;                                 -- fails if the role still owns objects
REASSIGN OWNED BY app TO ops;                  -- hand off ownership before dropping
DROP OWNED BY app;                             -- drop objects/privs owned by the role
```

Never embed plaintext passwords in scripts/logs. To avoid the server logging the password,
let the client prompt (`psql`'s `\password`) which sends a pre-hashed SCRAM verifier.

## Role attributes

| Attribute | Grants |
|---|---|
| `LOGIN` / `NOLOGIN` | may connect / may not |
| `SUPERUSER` | bypasses all permission checks (use sparingly) |
| `CREATEDB` | create databases |
| `CREATEROLE` | create/alter/drop **non-superuser** roles (and grant them) |
| `REPLICATION` | connect in replication mode (for `pg_basebackup`, standbys) |
| `BYPASSRLS` | bypass row-level security policies |
| `INHERIT` / `NOINHERIT` | automatically use privileges of granted roles (default `INHERIT`) |
| `CONNECTION LIMIT n` | cap concurrent connections |
| `PASSWORD` / `VALID UNTIL` | password + expiry |

> `CREATEROLE` got safer in pg16: a `CREATEROLE` role can now only administer roles it
> created (it gets `ADMIN` on them), and can't hand out attributes it lacks.

## Object privileges (GRANT / REVOKE)

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON orders TO app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;   -- existing tables only
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app;
GRANT USAGE ON SCHEMA app TO app;                          -- needed to "see into" a schema
GRANT EXECUTE ON FUNCTION calc(int) TO app;
GRANT app TO deployer WITH ADMIN OPTION;                   -- can re-grant the role

REVOKE INSERT ON orders FROM app;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM readonly;

-- Inspect:
\dp orders            -- psql: access privileges (ACL) for a table
SELECT grantee, privilege_type FROM information_schema.role_table_grants
 WHERE table_name = 'orders';
SELECT has_table_privilege('app','orders','SELECT');       -- programmatic check
```

Common object privileges: `SELECT INSERT UPDATE DELETE TRUNCATE REFERENCES TRIGGER` (tables);
`USAGE SELECT UPDATE` (sequences); `USAGE CREATE` (schemas); `EXECUTE` (functions);
`CONNECT TEMPORARY CREATE` (databases); `MAINTAIN` (pg17+: VACUUM/ANALYZE/REINDEX/CLUSTER/
REFRESH MATVIEW/LOCK TABLE).

> **`GRANT … ON ALL TABLES IN SCHEMA` is a snapshot** — it affects tables that exist at that
> moment, not future ones. Use `ALTER DEFAULT PRIVILEGES` for objects created later.

## DEFAULT PRIVILEGES

Grants applied automatically to objects created **in the future**, scoped to the creating role:

```sql
-- For objects YOU create going forward in schema app:
ALTER DEFAULT PRIVILEGES IN SCHEMA app
  GRANT SELECT ON TABLES TO readonly;

-- For objects a specific role creates (run as superuser or that role):
ALTER DEFAULT PRIVILEGES FOR ROLE deployer IN SCHEMA app
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app;

ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT USAGE ON SEQUENCES TO app;

-- Inspect / undo:
\ddp                                  -- psql: list default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA app REVOKE SELECT ON TABLES FROM readonly;
```

Key gotcha: default privileges are **per grantor**. If `deployer` creates the tables but you
only set defaults `FOR ROLE postgres`, `deployer`'s tables won't be covered — set them
`FOR ROLE deployer`.

## Schema & the public-schema change

```sql
CREATE SCHEMA app AUTHORIZATION app;
GRANT USAGE ON SCHEMA app TO readonly;     -- USAGE = may reference objects inside
GRANT CREATE ON SCHEMA app TO deployer;    -- CREATE = may create objects inside
```

**`public` schema hardening (pg15+):** on **new** clusters/databases, `PUBLIC` no longer has
`CREATE` on the `public` schema (mitigates CVE-2018-1058). Upgraded/restored databases keep
their old permissions — so on legacy clusters, harden it yourself:

```sql
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```

## Role membership (groups)

```sql
GRANT readonly TO app;                  -- app is now a member of readonly
REVOKE readonly FROM app;
\du                                     -- psql: roles + their memberships
SET ROLE readonly;                      -- act as the group (if SET is allowed)
RESET ROLE;
```

**Membership options (pg16+)** — control each grant independently:

```sql
GRANT readonly TO app WITH INHERIT TRUE,  SET TRUE,  ADMIN FALSE;
GRANT wheel    TO ops WITH INHERIT FALSE, SET TRUE,  ADMIN FALSE;  -- can SET ROLE but not auto-inherit
```

- `INHERIT {TRUE|FALSE}` — automatically use the group's privileges (per-grant; pre-16 this
  followed the *member's* `INHERIT` attribute for all memberships).
- `SET {TRUE|FALSE}` — may `SET ROLE` to the group.
- `ADMIN {TRUE|FALSE}` — may grant the group to others (the old `WITH ADMIN OPTION`).

## Predefined (built-in) roles

Grant capabilities to non-superusers. `GRANT pg_monitor TO grafana;`

| Role | Allows | Since |
|---|---|---|
| `pg_read_all_settings` | read all GUCs (incl. restricted) | pg10 |
| `pg_read_all_stats` | read all `pg_stat_*` + stats functions | pg10 |
| `pg_stat_scan_tables` | run monitoring functions that may take ACCESS SHARE locks | pg10 |
| `pg_monitor` | umbrella of the three above | pg10 |
| `pg_signal_backend` | cancel/terminate other backends (non-superuser) | pg9.6 |
| `pg_read_server_files` / `pg_write_server_files` / `pg_execute_server_program` | server-side file/program access (e.g. `COPY`) | pg11 |
| `pg_read_all_data` / `pg_write_all_data` | read/write all tables, views, sequences (pg19+ also large objects) | **pg14+** |
| `pg_database_owner` | implicit membership = the current DB's owner | **pg14+** |
| `pg_checkpoint` | run `CHECKPOINT` | **pg15+** |
| `pg_use_reserved_connections` | use `reserved_connections` slots | **pg16+** |
| `pg_create_subscription` | create logical subscriptions | **pg16+** |
| `pg_maintain` | VACUUM/ANALYZE/REINDEX/CLUSTER/REFRESH MATVIEW/LOCK (the `MAINTAIN` priv) | **pg17+** |
| `pg_signal_autovacuum_worker` | signal autovacuum workers | **pg18+** |

`pg_read_all_data` + `pg_write_all_data` are the modern way to give a role enough to run
`pg_dump` (or a read-only reporting login) without superuser.

## Authentication: pg_hba.conf

**H**ost-**B**ased **A**uthentication. Rules are matched **top-to-bottom, first match wins** —
if the first matching line's method fails, the connection is **rejected** (no fall-through).

```
# TYPE      DATABASE   USER        ADDRESS              METHOD       [OPTIONS]
local       all        all                              peer
host        all        all         127.0.0.1/32         scram-sha-256
host        all        all         ::1/128              scram-sha-256
hostssl     app        app         10.0.0.0/8           scram-sha-256
hostssl     replication repl       10.0.0.0/8           scram-sha-256
host        all        all         0.0.0.0/0            reject
```

| Column | Values |
|---|---|
| `TYPE` | `local` (Unix socket), `host` (TCP, SSL or not), `hostssl` (TLS required), `hostnossl`, `hostgssenc`/`hostnogssenc` |
| `DATABASE` | `all`, a name, `replication` (physical/base-backup conns — **not** matched by `all`), `sameuser`, `@file`, comma list |
| `USER` | `all`, a role, `+groupname` (members of a role), `@file`, comma list |
| `ADDRESS` | CIDR (`10.0.0.0/8`), `samehost`, `samenet`, a hostname, `.domain` suffix |
| `METHOD` | see below |

```sql
TABLE pg_hba_file_rules;            -- parsed rules + line numbers + errors (pg10+)
SELECT pg_reload_conf();            -- apply pg_hba edits (RELOAD, not restart)
```

New in pg19: **`pg_hosts.conf`** for hostname/key pairs — see the v19 docs.

## Authentication methods

| Method | Use |
|---|---|
| `scram-sha-256` (pg10+) | **preferred** password method (challenge-response, salted) |
| `md5` | legacy password hashing — **deprecated pg18+** (emits warnings) |
| `password` | cleartext over the wire — only with TLS, rarely justified |
| `peer` | local socket: trust the OS user name (great for `local` admin) |
| `ident` | TCP analog of `peer` via an ident server (legacy) |
| `cert` | TLS client certificate (CN → role, via `pg_ident.conf`) |
| `gss` / `sspi` | Kerberos / Windows SSPI single sign-on |
| `ldap` | bind against an LDAP/AD server |
| `radius` | RADIUS server |
| `oauth` (pg18+) | OAuth 2.0 bearer tokens (needs a validator library) |
| `trust` | **no authentication** — dev/local only, never on a network interface |
| `reject` | always deny (useful as a catch-all) |

## SCRAM & password encryption

```sql
SHOW password_encryption;                 -- scram-sha-256 (default since pg14) or md5
ALTER SYSTEM SET password_encryption = 'scram-sha-256';
SELECT pg_reload_conf();
-- existing passwords keep their OLD hash until reset; re-hash by resetting:
ALTER ROLE app PASSWORD 'newsecret';
SELECT rolname, rolpassword FROM pg_authid WHERE rolname='app';  -- 'SCRAM-SHA-256$…'
```

Migration note: switching a `pg_hba` line to `scram-sha-256` **breaks logins whose stored
password is still md5-hashed** — flip `password_encryption` first, then have everyone reset
their password, then change the `pg_hba` method.

## pg_ident.conf (user name maps)

Maps an external/OS identity to a database role for `peer`, `cert`, `gss`, `sspi`, `ldap`,
`radius`. Reference the map name in `pg_hba.conf` with `map=NAME`:

```
# pg_hba.conf
local   all   all                       peer        map=admins
hostssl all   all   10.0.0.0/8          cert        map=certs

# pg_ident.conf:  MAPNAME   SYSTEM-USERNAME    PG-USERNAME
admins            alice               postgres
admins            /^(.*)@corp$        \1               # regex: capture group → \1
certs             "CN=app.example.com"  app
```

```sql
TABLE pg_ident_file_mappings;     -- parsed pg_ident.conf + errors (pg15+)
```

## TLS / SSL

```conf
# postgresql.conf
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file  = 'server.key'
ssl_ca_file   = 'root.crt'          # needed for client-cert (cert) auth
ssl_min_protocol_version = 'TLSv1.2'
ssl_groups = 'X25519:prime256v1'    # pg18+ (renamed from ssl_ecdh_curve; multi-value)
```

Force TLS for chosen connections with `hostssl` lines; require **and verify** client certs by
combining `hostssl … cert` with `ssl_ca_file`. Confirm a live connection's encryption with
`SELECT * FROM pg_stat_ssl;`.
