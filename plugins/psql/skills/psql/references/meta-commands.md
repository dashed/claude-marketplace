# psql Meta-Commands (Backslash Commands)

The complete catalog of `psql` backslash commands, grouped by purpose. Anything you type starting
with `\` is interpreted by `psql` itself (the client), not sent to the server. Version tags
`(pgNN+)` mark the **client** version that introduced a feature; untagged items are bedrock
(present in pg13 and earlier). See [version-features.md](version-features.md) for sourcing and the
bedrock rule, [connection.md](connection.md) for `\c`/connection details, [scripting.md](scripting.md)
for `\set`/variables in scripts, and [pipeline.md](pipeline.md) for the extended-protocol/pipeline
family.

> **Argument parsing.** Most meta-command arguments are whitespace-separated, with
> single-quote/`:'var'`/backtick expansion. A few take the **entire rest of the line literally**
> (no variable/backtick expansion): `\copy`, `\!`, `\g |cmd`, `\w |cmd`, `\sf`, `\sv`, `\help`.
> Backslash commands end at an **unquoted backslash or newline**; you can put a meta-command and
> SQL on one line, e.g. `\timing \\ SELECT 1;`.

## Contents

- [Informational / inspection (`\d` family, `\l`, `\sf`)](#informational--inspection)
- [Query execution (`\g`, `\gx`, `\gexec`, `\gset`, `\gdesc`, `\crosstabview`, `\watch`)](#query-execution)
- [Formatting & output (`\pset`, `\x`, `\a`, `\t`, `\f`, `\C`, `\o`)](#formatting--output)
- [Variables (`\set`, `\unset`, `\getenv`, `\prompt`)](#variables)
- [Conditionals (`\if` family)](#conditionals-pg10)
- [Input / editing / files (`\i`, `\ir`, `\e`, `\ef`, `\ev`, `\w`, `\copy`)](#input--editing--files)
- [Connection & session (`\c`, `\conninfo`, `\password`, `\encoding`)](#connection--session)
- [System / OS (`\!`, `\cd`, `\setenv`, `\echo`, `\qecho`, `\warn`)](#system--os)
- [Large objects](#large-objects)
- [Restricted mode (`\restrict` / `\unrestrict`)](#restricted-mode-security)
- [Help & exit](#help--exit)

## Informational / inspection

The signature feature of `psql`. Pattern matching follows
[psql patterns](https://www.postgresql.org/docs/current/app-psql.html#APP-PSQL-PATTERNS): names are
matched like SQL `LIKE` but `.` separates schema from name, `*`/`?` are wildcards. Suffix `S`
includes system objects; suffix `+` adds detail. Use `-E` (or `\set ECHO_HIDDEN on`) to see the
underlying catalog queries these run.

| Command | Lists / shows |
|---|---|
| `\d [pattern]` | A relation's columns, types, indexes, constraints, triggers; or (no pattern) all tables/views/matviews/sequences/foreign tables |
| `\d+ [pattern]` | As `\d` plus storage, replica identity, access method, comments, view definitions |
| `\dt` / `\dv` / `\dm` / `\di` / `\ds` | **t**ables / **v**iews / **m**aterialized views / **i**ndexes / **s**equences |
| `\df [pattern]` / `\df+` | Functions (with return & arg types); `+` adds source, volatility, leakproof |
| `\sf func` / `\sf+ func` | The `CREATE OR REPLACE FUNCTION` definition; `+` numbers the body lines |
| `\sv view` / `\sv+ view` | A view's `CREATE OR REPLACE VIEW` definition |
| `\dn [pattern]` | Schemas (**n**amespaces) |
| `\dx [pattern]` | Installed **extensions** (`+` lists member objects; shows `default_version` in pg18+) |
| `\l` / `\l+` | Databases (the `\list` command; also `psql -l`) |
| `\du` / `\dg` | Roles/users and groups |
| `\drg [pattern]` | Role membership/grants **(pg16+)** — the `Member of` column was dropped from `\du`/`\dg` |
| `\dp [pattern]` / `\z` | Access privileges on tables/views/sequences (`\dpS`/`\zS` add system objects, **pg16+**) |
| `\dconfig[+] [pattern]` | Server config parameters (pattern-aware `SHOW`) **(pg15+)** |
| `\dX [pattern]` | Extended-statistics objects **(pg14+)** |
| `\dT` / `\dD` / `\do` / `\dc` | Data **T**ypes / **D**omains / **o**perators / **c**onversions |
| `\dRp` / `\dRs` | Replication **p**ublications / **s**ubscriptions (`+` shows comments in pg19+) |
| `\db` / `\dF` / `\dy` / `\dl` | Tablespaces / text-search configs / event triggers / large objects |

In pg18+, appending an `x` (after `S`/`+`) to a **listing** command forces expanded output, e.g.
`\d+x`, `\dtx`. Note `\dx` remains "list extensions" — the `x` modifier can't be the first letter.

## Query execution

These act on the **current query buffer** (what you've typed but not yet ended with `;`). If the
buffer is empty, most re-run the most recent query.

| Command | Action |
|---|---|
| `\g [(opt=val ...)] [file\|\|cmd]` | Send the buffer (like `;`). Optional one-shot `\pset` options in `()`; redirect output to a `file` or `\| shell command` |
| `\gx [(opt=val ...)] [...]` | `\g` but forces **expanded** mode for this query (= `\pset expanded on`) **(pg10+)** |
| `\gexec` | Run the buffer, then execute **each returned cell as its own SQL statement** (NULLs skipped) **(pg9.6+)** |
| `\gset [prefix]` | Run the buffer (must return **exactly one row**); store each column into a `psql` variable named after the column (NULL → unset) |
| `\gdesc` | Show the result's column names and types **without executing** (syntax errors still reported) **(pg11+)** |
| `\crosstabview [colV [colH [colD [sortcolH]]]]` | Run the buffer and pivot ≥3 columns into a cross-tab grid **(pg9.6+)** |
| `\watch [i[nterval]=s] [c[ount]=n] [m[in_rows]=r] [secs]` | Re-run the buffer every `secs` (default 2) until interrupted/fails. `count=` cap & named forms **(pg16+)**; `min_rows=` stop **(pg17+)**; `WATCH_INTERVAL` default var **(pg18+)** |
| `\bind`, `\bind_named`, `\parse`, `\close_prepared`, pipelines | Extended-protocol / pipeline family → see [pipeline.md](pipeline.md) |

`\gexec` is the metaprogramming workhorse — generate DDL/DML with `format()` and run it:

```sql
SELECT format('ANALYZE %I;', tablename) FROM pg_tables WHERE schemaname='public' \gexec
```

`\gset` feeds query results back into the session (great with `\if` and interpolation):

```sql
SELECT count(*) AS n, now() AS t FROM orders \gset
\echo there are :n orders as of :t
```

## Formatting & output

`\pset OPTION [VALUE]` is the master switch; the short commands are convenience aliases.

| Command | Equivalent / effect |
|---|---|
| `\pset format X` | `aligned` (default), `unaligned`, `csv`, `wrapped`, `html`, `asciidoc`, `latex`, `latex-longtable`, `troff-ms` |
| `\a` | Toggle aligned ↔ unaligned (`\pset format`) |
| `\x [on\|off\|auto]` | Expanded (one column per line) — great for wide rows; `auto` decides by width |
| `\t` | Tuples-only: drop header & row-count footer (`\pset tuples_only`) |
| `\f [char]` | Field separator for unaligned output (`\pset fieldsep`) |
| `\C [title]` | Set/clear a table title (`\pset title`) |
| `\pset null 'X'` | String shown for NULLs (default empty) |
| `\pset border N` | 0/1/2 border style |
| `\pset pager X` | `on`/`off`/`always` — control the pager |
| `\pset csv_fieldsep X` | Field separator for `csv` format |
| `\pset xheader_width X` | Cap expanded-header width: `full`/`column`/`page`/N **(pg16+)** |
| `\pset display_true` / `display_false` | How booleans render **(pg19+)** |
| `\o [file\|\|cmd]` | Send **all** subsequent query output to a file/command; `\o` alone reverts to stdout |

For machine-readable output prefer `\pset format csv` (RFC-4180 quoting) or `unaligned` +
`tuples_only`. See [scripting.md](scripting.md) for the `-qAtX` / `--csv` shortcuts.

## Variables

`psql` variables are client-side string variables, distinct from SQL `SET`. See
[scripting.md](scripting.md) for the full special-variable list and interpolation rules.

| Command | Action |
|---|---|
| `\set [name [value ...]]` | Set a variable (multiple values are concatenated); no args lists all |
| `\unset name` | Delete a variable (control variables revert to default) |
| `\getenv psql_var env_var` | Copy an environment variable into a `psql` variable **(pg15+)** |
| `\prompt [text] name` | Interactively read a value into a variable |

Interpolate with `:name` (raw), `:'name'` (quoted **literal**), `:"name"` (quoted **identifier**),
and `:{?name}` (TRUE/FALSE if set). Always prefer the quoted forms for untrusted values — raw
`:name` is a SQL-injection footgun.

## Conditionals (pg10+)

`\if`, `\elif`, `\else`, `\endif` add scripting branches. Conditions are `psql`-evaluated booleans
(`true`/`false`/`on`/`off`/`1`/`0`); pair with `\gset` to branch on query results.

```sql
SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='deploy') AS have_role \gset
\if :have_role
    \echo role exists, skipping
\else
    CREATE ROLE deploy LOGIN;
\endif
```

Branches not taken are parsed but not executed; backslash commands inside an untaken branch are
also skipped (except the `\if`-family commands themselves).

## Input / editing / files

| Command | Action |
|---|---|
| `\i file` | Read & execute SQL from `file` (like `psql -f`) |
| `\ir file` | Like `\i`, but a **relative** path resolves against the directory of the *including* script |
| `\e [file] [line]` | Edit the query buffer (or a file) in `$PSQL_EDITOR`/`$EDITOR`/`$VISUAL` (default `vi`) |
| `\ef [func [line]]` | Edit a function definition |
| `\ev [view [line]]` | Edit a view definition |
| `\w file` / `\w \|cmd` | Write the current query buffer to a file/command |
| `\p` / `\r` | Print / reset (clear) the query buffer |
| `\s [file]` | Print or save the command-line history |
| `\copy ...` | **Client-side** `COPY`: see below |

`\copy` runs a server `COPY` but streams the file through the **client**, so paths and permissions
are the local user's — no server superuser/`pg_read_server_files` needed. The whole rest of the
line is taken literally (no `:var`/backtick expansion).

```bash
# Export a query to a local CSV (header row, client-side):
\copy (SELECT * FROM orders WHERE created > now() - interval '1 day') TO 'recent.csv' WITH (FORMAT csv, HEADER)

# Import a local CSV into a table:
\copy customers (id, name, email) FROM 'customers.csv' WITH (FORMAT csv, HEADER)
```

`\copy ... FROM 'file' PROGRAM 'cmd'`, `... FROM pstdin`, `... TO pstdout` are supported. For large
volumes, server-side `COPY` (`\copy`'s cousin) is faster but needs file access on the server. A
flexible alternative: `COPY (…) TO STDOUT \g out.csv` (allows multi-line + interpolation).

## Connection & session

Full details in [connection.md](connection.md).

| Command | Action |
|---|---|
| `\c [conninfo]` / `\connect` | Reconnect (positional `dbname user host port`, or a conninfo/URI). Reuses prior params in positional form |
| `\conninfo` | Show current connection info (tabular & richer in pg18+) |
| `\password [user]` | Change a role's password safely (hashes client-side; never hits history/logs) |
| `\encoding [enc]` | Show/set the client encoding |

## System / OS

| Command | Action |
|---|---|
| `\! [cmd]` | Run a shell command (or drop to a subshell). Whole line is literal |
| `\cd [dir]` | Change `psql`'s working directory |
| `\setenv name [value]` | Set/unset an environment variable for the `psql` process |
| `\echo text ...` | Print to **stdout** |
| `\qecho text ...` | Print to the **query output** channel (`\o` target) |
| `\warn text ...` | Print to **stderr** |
| `` \set x `cmd` `` | Backtick: capture a shell command's stdout into a variable |

After a shell call, `:SHELL_ERROR` (bool) and `:SHELL_EXIT_CODE` are set **(pg16+)** — useful for
checking external commands in scripts.

## Large objects

`\lo_import 'file'`, `\lo_export oid 'file'`, `\lo_list[+]`, `\lo_unlink oid` — manage server-side
large objects from the client. Rarely needed; `bytea` columns are usually simpler.

## Restricted mode (security)

| Command | Action |
|---|---|
| `\restrict KEY` | Enter restricted mode — only `\unrestrict KEY` is allowed until you exit (KEY is alphanumeric) |
| `\unrestrict KEY` | Leave restricted mode (KEY must match the one given to `\restrict`) |

These exist mainly so `pg_dump`/`pg_restore` can fence plain-text dumps against meta-command
injection from a hostile source server. **Not a clean major-version feature** — added in the
**2025-08 security minor releases (CVE-2025-8714)** and backpatched to 13.22 / 14.x / 15.x / 16.10 /
17.6 / 18+. If a modern dump's `\restrict` line errors on restore, your `psql` is older than the
`pg_dump` that wrote it — restore with a `psql` at least as new. See
[version-features.md](version-features.md#restrict--unrestrict--the-cross-version-security-backport).

## Help & exit

| Command | Action |
|---|---|
| `\?` | List all backslash commands (`\? variables` / `\? options` for those topics) |
| `\h [SQL command]` | SQL syntax help (`\h *` for everything) |
| `\q` / `Ctrl-D` | Quit (in a script, ends just that script) |
| `\copyright` / `\errverbose` | License text / re-show the last error verbosely |
