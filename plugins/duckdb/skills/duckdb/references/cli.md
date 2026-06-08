# DuckDB CLI (`duckdb` shell) Reference

Complete reference for the `duckdb` command-line shell: invocation, command-line flags,
output modes, the dot-command set, and non-interactive / agent usage patterns. The shell
descends from SQLite's shell, so the dot-commands and flag style will feel familiar if you
know `sqlite3`.

> **Verification & version annotations.** Every flag, dot-command, and output mode below was
> confirmed against the installed **`duckdb` CLI v1.3.2 "Ossivalis"** (`duckdb -help`, `.help`)
> and the shell source in `tools/shell/`. The **vast majority of the CLI is bedrock** (stable
> since the 1.0 GA) and is left unannotated. Only items with a real duckdb.org release-blog
> source carry a `(duckdb vX.Y+)` tag. Confirm your own build with `duckdb -version`
> (e.g. `v1.3.2 (Ossivalis) 0b83e5d2f6`), then `duckdb -help` and `.help`.

## Table of Contents

- [Invocation](#invocation)
- [Command-line flags](#command-line-flags)
- [Output modes](#output-modes)
- [Dot-commands](#dot-commands)
- [Non-interactive / agent usage](#non-interactive--agent-usage)
- [Gotchas](#gotchas)

---

## Invocation

```
duckdb [OPTIONS] FILENAME [SQL]
```

- **`FILENAME`** — a DuckDB database file. It is **created if it does not exist**. Omit it (or
  pass `:memory:`) to use a purely in-memory database that is discarded on exit.
- **`[SQL]`** — an optional trailing SQL string. It runs, then the shell **drops into the
  interactive REPL** (or exits immediately if combined with `-no-stdin`).
- As of **(duckdb v1.3+)** `FILENAME` may be a **data file** (`.csv` / `.parquet` / `.json`)
  rather than a database — it is exposed as a view named after the file (and `data`):
  `duckdb sales.parquet -c 'FROM sales LIMIT 5'`.

```bash
duckdb                         # in-memory scratch REPL (nothing persisted)
duckdb my.db                   # open/create a persistent database file
duckdb -c "SELECT 42"          # run one command and exit (the agent entrypoint)
duckdb my.db "SELECT 1"        # run trailing SQL, then enter the REPL
```

**Startup init file.** With no `-init`, the shell reads **`~/.duckdbrc`** on startup if present
(run dot-commands / SQL there to set your default mode, prompt, etc.), then continues
interactively. `-init FILE` overrides the path; `-f FILE` / `-c CMD` do **not** read it.

---

## Command-line flags

Confirmed verbatim from `duckdb -help` on v1.3.2.

### Execution & I/O control

| Flag | Meaning |
|------|---------|
| `-c COMMAND` | Run `COMMAND` and **exit** — the primary non-interactive entrypoint |
| `-s COMMAND` | Run `COMMAND` and exit (alias of `-c`) |
| `-cmd COMMAND` | Run `COMMAND` **before** reading stdin, then stay interactive |
| `-f FILENAME` | Read/process a SQL file, then **exit** |
| `-init FILENAME` | Read/process a file on startup, then continue (default: `~/.duckdbrc`) |
| `-readonly` | Open the database **read-only** (rejects writes; see gotcha — **requires a file DB**) |
| `-safe` | Enable **safe-mode**: restrict filesystem and external access `(duckdb v1.2+)` |
| `-no-stdin` | Exit after processing options instead of reading stdin |
| `-interactive` | Force interactive I/O |
| `-batch` | Force batch I/O |
| `-bail` | Stop after hitting the first error |
| `-echo` | Print each command before executing it |
| `-unsigned` | Allow loading **unsigned** extensions |
| `-unredacted` | Allow printing unredacted secrets |
| `-ui` | Launch the web interface via the `ui` extension (configurable with `.ui_command`) |
| `-version` | Print the DuckDB version and exit |
| `-help` | Show the help message |

### Output formatting

| Flag | Meaning |
|------|---------|
| `-[no]header` | Turn column headers on / off |
| `-nullvalue TEXT` | String to print for NULL values (default `NULL`) |
| `-separator SEP` | Column separator (default `\|`) |
| `-newline SEP` | Row separator (default `\n`) |

**Output-mode flags** — each is a one-shot equivalent of `.mode MODE`:
`-ascii  -box  -column  -csv  -html  -json  -line  -list  -markdown  -quote  -table`.

---

## Output modes

Set per session with a launch flag (`-json`) or at the prompt with `.mode MODE ?TABLE?`.
The full set accepted by v1.3.2 (`.mode` rejects anything else):

```
ascii  box  column  csv  duckbox  html  insert  json  jsonlines
latex  line  list  markdown  quote  table  tabs  tcl  trash
```

| Mode | Use it for |
|------|-----------|
| `duckbox` | **Default.** Pretty Unicode box with a column-type row; auto-pages >50 rows `(duckdb v1.5+)` |
| `box` | Box rendering without the type header line |
| `csv` | RFC-4180 CSV — pipe to files/tools (pairs well with `-noheader`) |
| `json` | **JSON array of row objects — best for agents/scripts** |
| `jsonlines` | Newline-delimited JSON (one object per line) |
| `line` | One `column = value` per line, blank line between rows |
| `markdown` | GitHub-style Markdown table (paste into docs/PRs) |
| `table` | ASCII-art table (MySQL `mysql`-style) |
| `column` | Left-aligned fixed-width columns |
| `list` | `\|`-separated values (the classic SQLite list mode) |
| `tabs` | Tab-separated values |
| `ascii` | Records separated by ASCII unit/record separators |
| `insert` | Emit `INSERT INTO` statements |
| `html` / `latex` / `tcl` | Export-friendly markup |
| `quote` | SQL-quoted values |
| `trash` | Discard output (use with `.timer on` for timing-only runs) |

Adjust rendering with the dot-commands below: `.nullvalue STR`, `.separator COL ?ROW?`,
`.headers on|off`, `.maxrows N`, `.maxwidth N`.

---

## Dot-commands

Shell meta-commands; type `.help` for the list or `.help PATTERN` for one command's detail.
All of the following are present in v1.3.2.

### Most useful

| Command | Purpose |
|---------|---------|
| `.help ?-all? ?PATTERN?` | Show help (optionally for commands matching `PATTERN`) |
| `.mode MODE ?TABLE?` | Set the output mode (see list above) |
| `.output ?FILE?` | Redirect **all** subsequent output to `FILE` (no arg = back to stdout) |
| `.once ?OPTIONS? ?FILE?` | Redirect only the **next** query's output to `FILE` |
| `.read FILE` | Execute SQL from `FILE` (run a script) |
| `.tables ?PATTERN?` | List tables matching a LIKE pattern; shows catalogs/schemas/columns `(duckdb v1.5+)` |
| `.schema ?PATTERN?` | Show the `CREATE` statements for matching objects |
| `.databases` | List names and files of attached databases |
| `.open ?OPTIONS? ?FILE?` | Close the current database and reopen `FILE` |
| `.import FILE TABLE` | Import data from `FILE` into `TABLE` (CSV by default) |
| `.timer on\|off` | Show wall/CPU time per query |
| `.explain ?on\|off\|auto?` | Change EXPLAIN formatting mode (default `auto`) |
| `.shell CMD` / `.system CMD` | Run a command in a system shell |
| `.cd DIRECTORY` | Change the shell's working directory |
| `.excel` | Open the next result in a spreadsheet application |
| `.print STRING...` | Print a literal string |
| `.quit` / `.exit ?CODE?` | Exit (optionally with a return code) |

`.once` options: `--bom` (write a UTF-8 BOM), `-e` (send to `$EDITOR`), `-x` (send as CSV to a
spreadsheet, same as `.excel`). If `FILE` begins with `\|` it is opened as a pipe.

### Rendering & formatting

`.columns`, `.rows`, `.width N1 N2 …`, `.maxrows N` (default 40, duckbox only),
`.maxwidth N` (0 = terminal width, duckbox only), `.large_number_rendering all|footer|off`,
`.decimal_sep SEP`, `.thousand_sep SEP`, `.nullvalue STRING`, `.separator COL ?ROW?`,
`.headers on|off` (also `.header`), `.binary on|off`, `.changes on|off`, `.prompt MAIN CONTINUE`.

### Syntax highlighting

`.highlight [on|off]`, `.highlight_colors [element] [color] [bold]`,
`.highlight_errors [on|off]`, `.highlight_results [on|off]`,
`.constant ?COLOR?` / `.constantcode ?CODE?`, `.keyword ?COLOR?` / `.keywordcode ?CODE?`.

### Schema & inspection

`.fullschema ?--indent?`, `.indexes ?TABLE?`, `.dump ?TABLE?` (render DB content as SQL),
`.show` (current settings).

### Logging, safety & misc

`.log FILE|off` (`FILE` may be `stdout`/`stderr`), `.safe_mode` (enable safe-mode at runtime),
`.bail on|off`, `.echo on|off`, `.edit` (edit a query in an external editor),
`.testcase NAME` / `.check GLOB` (the shell's test harness).

---

## Non-interactive / agent usage

This is the shell's primary mode for scripts, CI, and agents. Prefer `-c` / `-f` / a heredoc
over driving the REPL, and prefer `-json` output for anything that gets parsed.

```bash
# One-shot, machine-readable JSON  →  [{"n":42}]
duckdb -json -c "SELECT count(*) AS n FROM 'events.parquet'"

# Pipe SQL from stdin (heredoc for multiple statements)
duckdb my.db <<'SQL'
CREATE TABLE t AS FROM 'in.csv';
COPY t TO 'out.parquet';
SQL

# -cmd runs first, THEN stdin is read (stays interactive)
echo "SELECT * FROM t;" | duckdb my.db -cmd ".mode json"

# Run a script file and exit
duckdb -f build_report.sql

# CSV without headers, piped to a unix tool
duckdb -csv -noheader -c "SELECT id FROM 'users.parquet'" | sort -u

# Read-only guard against a database FILE (see gotcha below)
duckdb -readonly warehouse.db -c "SELECT * FROM sales LIMIT 100"

# Stop on the first error; the process exits non-zero on failure
duckdb -bail -f migration.sql
```

**Agent checklist:**

- **`-json`** is the safest output to parse; `-csv -noheader` is the lightweight alternative.
- **`-readonly`** to forbid writes — but only against a **file** database (it errors on `:memory:`).
- Use **`-c`**, **`-f`**, or a **heredoc**; avoid the REPL.
- Use **`:memory:`** (the default) when nothing needs to persist — including when you only *read*
  external files, which never touch the database.
- **Exit code is non-zero on error** even without `-bail`; add **`-bail`** to stop a multi-statement
  run at the first failure instead of continuing.

---

## Gotchas

- **`-readonly` needs a file database.** Against the default in-memory database it errors with
  `Cannot launch in-memory database in read-only mode!`. To sandbox queries against a DB, pass a
  file: `duckdb -readonly my.db -c "…"`. To safely *read external files* you don't need
  `-readonly` at all — the in-memory DB is never written.
- **`-c`/`-s` exit; `-cmd` does not.** `-c`/`-s` run and quit. `-cmd` runs *before* stdin and
  leaves you interactive. For multiple statements in one `-c`, separate them with `;`.
- **`-no-stdin` suppresses piped input.** With it, stdin is ignored even if you pipe SQL in —
  only `-c`/`-cmd`/trailing-SQL run.
- **Trailing `SQL` drops into the REPL.** `duckdb db "SELECT 1"` runs the query then waits for
  more input; add `-no-stdin` (or use `-c`) to make it exit.
- **Quoting:** `'…'` is a string literal / file path; `"…"` is an identifier (column/table).
  `FROM 'data.csv'` (a path) differs from `FROM data` (an identifier/view).
- **Missing-file errors are path issues, not SQL.** `FROM 'glob/*.parquet'` failing with
  `IO Error: No files found that match the pattern …` means the glob/path is wrong.
- **`-unsigned` is required for unsigned/community-built extensions**; core extensions are signed
  and autoload without it.
</content>
</invoke>
