# psql Scripting & Non-Interactive Use

How to drive `psql` from scripts, CI, and agents — predictable output, correct error handling,
useful exit codes. This is the most important reference for automated callers.

## Contents

- [The agent/CI invocation](#the-agentci-invocation)
- [Getting clean, parseable output](#getting-clean-parseable-output)
- [Error handling & exit codes](#error-handling--exit-codes)
- [Transactions in scripts](#transactions-in-scripts)
- [Special control variables](#special-control-variables)
- [SQL interpolation (variables in queries)](#sql-interpolation-variables-in-queries)
- [Streaming large result sets](#streaming-large-result-sets)
- [`.psqlrc` and `-X`](#psqlrc-and--x)
- [Environment](#environment)

## The agent/CI invocation

The single most useful pattern — quiet, unaligned, tuples-only, no startup file:

```bash
psql -qAtX -c "SELECT count(*) FROM orders"
```

- **`-q`** quiet (suppress "CREATE TABLE"-style chatter and the banner)
- **`-A`** unaligned (no column-alignment padding)
- **`-t`** tuples-only (no header, no row-count footer)
- **`-X`** ignore `~/.psqlrc` (so a developer's personal settings can't change behavior — **always
  use `-X` in scripts**)
- **`-c`** run one command and exit

For structured output, prefer **CSV** (handles embedded delimiters/quotes/newlines via RFC-4180):

```bash
psql -X --csv -c "SELECT id, email FROM users WHERE active" > users.csv
```

`-c` vs `-f` vs stdin:

```bash
psql -X -c "SQL"                       # one command (a single backslash cmd OR one SQL string)
psql -X -f script.sql                  # run a file, then exit (gives line numbers on error)
psql -X -c '\x' -c 'SELECT * FROM t'   # multiple -c (and -f) run in sequence
psql -X <<'SQL'                        # heredoc: mix SQL and meta-commands freely
\timing on
SELECT now();
SQL
```

A single `-c` string is sent to the server as **one request** (hence one implicit transaction
unless it contains explicit `BEGIN`/`COMMIT`). It may contain **either** SQL **or** one backslash
command, not both — split across multiple `-c`, or pipe via stdin/heredoc, to mix them.

## Getting clean, parseable output

| Goal | How |
|---|---|
| One scalar value, nothing else | `psql -qAtX -c "SELECT version()"` |
| CSV (safe quoting) | `psql -X --csv -c "..."` (= `\pset format csv`) |
| Custom field/record separators | `-F','` / `-R'\n'`; or NUL-separated `-z` (fields) / `-0` (records) for `xargs -0` |
| Tab-separated | `-At -F$'\t'` |
| Suppress just the footer | `\pset footer off` |
| Expanded (one field per line) | `-x` or `\x` — easy to grep field-by-field |

NUL separators are the robust choice when values may contain commas/newlines and you're piping to
`xargs`:

```bash
psql -X -tz -c "SELECT datname FROM pg_database WHERE NOT datistemplate" | xargs -0 -I{} echo db={}
```

## Error handling & exit codes

By default `psql` **keeps going after an error**. In scripts you almost always want the opposite:

```bash
psql -X -v ON_ERROR_STOP=1 -f migrate.sql
```

- **`ON_ERROR_STOP=1`** (set via `-v` or `\set`) makes `psql` stop at the first error and exit
  non-zero — essential for migrations and CI.

**Exit status** (`psql` → shell):

| Code | Meaning |
|---|---|
| `0` | Finished normally |
| `1` | Fatal `psql`-side error (out of memory, file not found, bad option) |
| `2` | Connection to the server was lost / could not connect (non-interactive) |
| `3` | An SQL/script error occurred **and** `ON_ERROR_STOP` was set |

So `ON_ERROR_STOP=1` is what turns a failed statement into a detectable non-zero exit (code 3),
distinct from connection failures (2) and `psql` bugs (1).

Within a session, the result of the last statement is also exposed in variables: `:ERROR`
(bool), `:SQLSTATE`, `:ROW_COUNT`, `:LAST_ERROR_MESSAGE`, `:LAST_ERROR_SQLSTATE`.

## Transactions in scripts

- **`-1` / `--single-transaction`**: wrap all the `-c`/`-f` work in one `BEGIN`/`COMMIT` (rolls
  back on error if `ON_ERROR_STOP` is set). Use it so a multi-statement migration is all-or-nothing:

  ```bash
  psql -X -1 -v ON_ERROR_STOP=1 -f migration.sql
  ```

  Caveats: it has no effect if the script issues its own `BEGIN`/`COMMIT`, and a statement that
  can't run inside a transaction block (e.g. `CREATE DATABASE`, `VACUUM`, `CREATE INDEX
  CONCURRENTLY`, most `ALTER TYPE … ADD VALUE`) will fail under `-1`.
- **`AUTOCOMMIT`** (default `on`): when `off`, `psql` opens an implicit transaction before the next
  command, so you must `COMMIT` explicitly — and an unclean exit loses the work.
- **`ON_ERROR_ROLLBACK`** (`on`/`interactive`/`off`): when `on`, `psql` brackets each statement in
  an implicit `SAVEPOINT` so one failing statement doesn't abort the whole transaction. Convenient
  interactively; usually leave `off` in scripts.

## Special control variables

Set with `-v NAME=value` on the command line or `\set NAME value` in a script. Booleans accept
`on`/`off`/`1`/`0`.

| Variable | Purpose |
|---|---|
| `ON_ERROR_STOP` | Stop & exit non-zero on the first error (set in every script) |
| `ON_ERROR_ROLLBACK` | `on`/`interactive`/`off` — savepoint each statement so a failure doesn't kill the txn |
| `AUTOCOMMIT` | `on` (default) commits each statement; `off` requires explicit `COMMIT` |
| `ECHO` | `none` (default) / `queries` (= `-e`) / `all` (= `-a`) / `errors` (= `-b`) — echo statements |
| `ECHO_HIDDEN` | `on`/`noexec` — show the catalog query behind a `\d` command (= `-E`) |
| `VERBOSITY` | `default` / `verbose` / `terse` / `sqlstate` — error-message detail |
| `SHOW_CONTEXT` | `never`/`errors`/`always` — whether server `CONTEXT:` lines show |
| `QUIET` | Suppress informational output (= `-q`) |
| `FETCH_COUNT` | If > 0, fetch/display in chunks of N rows (bounds memory) |
| `SHOW_ALL_RESULTS` | `on` (pg15+ default) shows every result of a `\;` batch; `off` = last only |
| `HISTCONTROL` / `HISTFILE` / `HISTSIZE` | History behavior, file, size |
| `SHELL_ERROR` / `SHELL_EXIT_CODE` | Status of the last `\!`/backtick/`\g`-pipe (pg16+) |
| `VERSION_NUM` / `SERVER_VERSION_NUM` | Client / server numeric version (for `\if` gating) |

Read-only state variables also exist: `DBNAME`, `USER`, `HOST`, `PORT`, `ENCODING`,
`ERROR`, `SQLSTATE`, `ROW_COUNT`, `LAST_ERROR_MESSAGE`. Pipeline counters
(`PIPELINE_*`) are pg18+. See [pipeline.md](pipeline.md).

## SQL interpolation (variables in queries)

`psql` variables substitute into SQL and into meta-command arguments:

| Form | Substitutes as | Use for |
|---|---|---|
| `:name` | raw text (no quoting) | identifiers you control, numbers, SQL fragments |
| `:'name'` | a quoted **string literal** | untrusted string values (injection-safe) |
| `:"name"` | a quoted **identifier** | table/column names from variables (injection-safe) |
| `:{?name}` | `TRUE`/`FALSE` if the var exists | `\if` guards |

```bash
psql -X -v tbl=orders -v cutoff="2026-01-01" \
  -c "SELECT count(*) FROM :\"tbl\" WHERE created >= :'cutoff'"
```

Interpolation does **not** happen inside literal SQL quotes (`':name'` is the literal text
`:name`), and an unset variable's `:name` is left untouched. Prefer `:'…'`/`:"…"` for anything
that came from outside — raw `:name` is a SQL-injection vector. (For truly safe parameter passing
to the server, see `\bind` and the extended protocol in [pipeline.md](pipeline.md).)

## Streaming large result sets

By default `psql` buffers the **entire** result before printing. For huge results that risk OOM:

```bash
psql -X -v FETCH_COUNT=1000 --csv -c "SELECT * FROM big_table" > dump.csv
```

`FETCH_COUNT` makes `psql` fetch/print in batches of N rows. Note a query can then **fail
mid-output** (after some rows are printed), and the default `aligned` format looks ragged per batch
— use `csv`/`unaligned`. In pg17+, `FETCH_COUNT` also applies to non-`SELECT` queries. For one-pass
bulk export, server-side `COPY (…) TO STDOUT` / `\copy` is usually faster.

## `.psqlrc` and `-X`

On startup (unless `-X` is given) `psql` runs the system-wide `psqlrc` then the user's `~/.psqlrc`,
**after** connecting but before accepting input. Typical contents: `\set` defaults, `\pset` styles,
`\timing on`, handy query shortcuts via `\set`.

```psqlrc
\set ON_ERROR_ROLLBACK interactive
\set COMP_KEYWORD_CASE upper
\timing on
\pset null '(null)'
\set HISTFILE ~/.psql_history-:DBNAME
```

Version-specific variants are honored: `~/.psqlrc-18`, `~/.psqlrc-18.1` (most specific wins).
Override the path with `PSQLRC`.

> **Scripts must pass `-X`.** Otherwise a developer's `~/.psqlrc` (custom `\pset`, `\timing`,
> aliases) can silently change your output and break parsing. Make `-qAtX` muscle memory.

## Environment

psql-specific environment variables (libpq connection vars are in
[connection.md](connection.md#environment-variables)):

| Variable | Effect |
|---|---|
| `PSQL_EDITOR` / `EDITOR` / `VISUAL` | Editor for `\e`/`\ef`/`\ev` (first set wins; default `vi`) |
| `PSQL_EDITOR_LINENUMBER_ARG` | How to pass a starting line to the editor (e.g. `+`) |
| `PSQL_PAGER` / `PAGER` | Pager for long output (`less`, `more`); set empty to disable |
| `PSQL_WATCH_PAGER` | Pager for `\watch` output (e.g. `pspg --stream`); off by default |
| `PSQL_HISTORY` | Alternate history-file path |
| `PSQLRC` | Alternate `~/.psqlrc` path |
| `PSQL_PAGE_*` / `COLUMNS` | Width hints for `wrapped`/expanded-auto formatting |
| `PG_COLOR` | `always`/`auto`/`never` — colorize diagnostics |

The pager only kicks in for an interactive TTY; in scripts (output not a terminal) it's bypassed,
so you rarely need to disable it — but exporting `PAGER=` (empty) guarantees it.
