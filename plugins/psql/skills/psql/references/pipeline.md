# psql Extended-Protocol & Pipeline Meta-Commands

`psql` normally uses the **simple query protocol** (send SQL text, get results). A small family of
meta-commands instead drives the **extended query protocol** — parameterized statements, named
prepared statements, and request *pipelining* — directly from the shell. These are useful for
binding `$1`-style parameters safely, for testing the extended protocol, and for measuring
pipeline round-trip behavior.

> **Version reality (verified against the versioned manuals):** `\bind` is **pg16+**. *Everything
> else here is pg18+* — `\parse`, `\bind_named`, `\close_prepared`, and the entire pipeline family
> were **absent from both the pg16 and pg17 psql manuals** and were added in **PostgreSQL 18**.
> There was never a shipped `\close`; the command is `\close_prepared`. (Earlier in-development
> pipeline patches existed but did not ship until 18.) See
> [version-features.md](version-features.md).

## Contents

- [Binding parameters (`\bind`)](#binding-parameters-bind-pg16)
- [Named prepared statements (`\parse`, `\bind_named`, `\close_prepared`)](#named-prepared-statements-pg18)
- [Pipelining](#pipelining-pg18)
- [Pipeline state variables & prompt](#pipeline-state-variables--prompt)
- [When to reach for these](#when-to-reach-for-these)

## Binding parameters (`\bind`) (pg16+)

`\bind` supplies positional parameters for the **next** query and forces the extended protocol for
just that query. Placeholders are `$1`, `$2`, … and the values follow `\bind` in order:

```sql
SELECT $1::int + $2::int \bind 3 4 \g
-- → 7
INSERT INTO tbl (a, b) VALUES ($1, $2) \bind 'first value' 'second value' \g
```

It also works with `\gx` and `\gset`. The extended protocol is used even with zero parameters
(useful purely to *exercise* the extended path). `\bind` affects only the next query; subsequent
queries revert to the simple protocol.

`\bind` is the closest `psql` gets to true server-side parameterization — values are sent
out-of-band, never textually interpolated, so it sidesteps the injection risk of `:'var'`
string-building.

## Named prepared statements (pg18+)

| Command | Action |
|---|---|
| `\parse name` | Parse the current query buffer into a prepared statement called `name` (empty string = the unnamed statement). Issues a Parse message |
| `\bind_named name [param ...]` | Like `\bind`, but executes the **already-prepared** statement `name` with the given parameters |
| `\close_prepared name` | Close (deallocate) prepared statement `name` (no-op if it doesn't exist) |

```sql
INSERT INTO tbl (a, b) VALUES ($1, $2) \parse stmt1
\bind_named stmt1 'first value' 'second value' \g
\bind_named stmt1 'third value' 'fourth value' \g     -- reuse the parsed plan
\close_prepared stmt1
```

All three force the extended protocol. They're the protocol-level analog of SQL `PREPARE`/
`EXECUTE`/`DEALLOCATE`, but driven through libpq's Parse/Bind/Close messages so you can test that
machinery from the shell.

## Pipelining (pg18+)

Pipeline mode sends multiple statements **without waiting** for each one's results, then collects
them — reducing round-trips on high-latency links. All queries inside a pipeline use the extended
protocol.

| Command | Action |
|---|---|
| `\startpipeline` | Begin a pipeline |
| `\sendpipeline` | Append the current query buffer to the pipeline (the in-pipeline replacement for `\g`) |
| `\syncpipeline` | Send a sync point without ending the pipeline or flushing the send buffer |
| `\flushrequest` | Append a flush request so results can be read with `\getresults` before a sync/end |
| `\flush` | Manually push unsent buffered data to the server |
| `\getresults [n]` | Read pending results — the first `n`, or all if `n` omitted/`0` |
| `\endpipeline` | End the pipeline |

Rules inside a pipeline:

- A statement is appended to the pipeline when it ends with a **semicolon**; use `\sendpipeline`
  to append the current buffer explicitly.
- `\bind`, `\bind_named`, `\close_prepared`, `\parse` are allowed inside a pipeline.
- `\g`, `\gx`, `\gdesc` are **not** allowed in pipeline mode; **`COPY` is not supported**.

```sql
\startpipeline
SELECT $1 \bind 1 \sendpipeline
SELECT $1 \bind 2 \sendpipeline
\flushrequest
\getresults
\endpipeline
```

## Pipeline state variables & prompt

While a pipeline is active these read-only variables track its state (all pg18+):

| Variable | Meaning |
|---|---|
| `PIPELINE_COMMAND_COUNT` | Commands queued in the pipeline |
| `PIPELINE_SYNC_COUNT` | Sync messages queued |
| `PIPELINE_RESULT_COUNT` | Results made available (by `\flushrequest` or `\syncpipeline`) and not yet read |

The `%P` prompt escape (pg18+) shows pipeline status in `PROMPT1`/`PROMPT2`. See also
`\set PROMPT1` and the Prompting section of the psql manual.

## When to reach for these

- **You need real parameter binding** (untrusted values, repeated execution of one plan):
  `\bind` / `\parse` + `\bind_named`. Safer than `:'var'` string interpolation.
- **You're testing or benchmarking the extended protocol / pipeline behavior** from a shell — the
  whole point of exposing these as meta-commands.
- **High-latency link, many small statements**: a pipeline cuts round-trips.

For ordinary scripting you rarely need these — a plain `-c`/`-f` with `:'…'`/`:"…"` interpolation
(see [scripting.md](scripting.md)) is simpler. Reach for the extended-protocol family when
parameter safety or protocol-level control specifically matters.
