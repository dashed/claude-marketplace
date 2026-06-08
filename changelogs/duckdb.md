# Changelog - duckdb

All notable changes to the duckdb skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-05

### Added
- Initial addition to the marketplace — a skill for **DuckDB**, the in-process columnar OLAP SQL engine ("SQLite for analytics"), scoped to the CLI + SQL authoring surface (client libraries deferred to duckdb.org). Authored against the DuckDB source (dev tree past v1.5.3); every example verified on the installed CLI **v1.3.2**.
- `SKILL.md`: mental model (in-process, columnar, files-as-tables, persistent vs `:memory:`); when-to-use vs SQLite/Postgres; install; the `duckdb` CLI at a glance; six runnable core workflows (direct file query, persistent vs in-memory, CSV→Parquet via `COPY`, friendly-SQL exploration, httpfs/S3, `ATTACH` Postgres/SQLite); agent-usage patterns; quick-reference; troubleshooting.
- `references/cli.md`: the `duckdb` shell — command-line flags, the full dot-command set (verified against `duckdb -help` and `.help`), output modes, and non-interactive/agent patterns.
- `references/sql-dialect.md`: DuckDB's "friendly SQL" — FROM-first, `SELECT * EXCLUDE/REPLACE/RENAME/LIKE`, `COLUMNS()`, `GROUP BY/ORDER BY ALL`, `QUALIFY`, `PIVOT`/`UNPIVOT`, ASOF/positional/`USING` joins, nested types (LIST/STRUCT/MAP/UNION) with access/slicing, lambdas + list comprehensions + `UNNEST`, `SUMMARIZE`/`DESCRIBE`, `USING SAMPLE`, `CREATE OR REPLACE`, `RETURNING`, `TRY`, `PREPARE`/`EXECUTE`, and friendly aggregates. Includes two empirically-found gotchas (`USING SAMPLE` vector-granularity behavior; colon-alias vs trailing `AS`).
- `references/data-io.md`: replacement scans (`FROM 'file'`), `read_csv`/`read_parquet`/`read_json` (+ `_auto`) with options, globs/Hive partitioning, `COPY … TO` (partitioned, compression), `EXPORT`/`IMPORT DATABASE`, `ATTACH` for duckdb/sqlite/postgres/mysql + cross-database queries, Excel, the extension system (`INSTALL`/`LOAD`, autoload, httpfs/S3 + `CREATE SECRET`, parquet, json, spatial, fts, icu, `*_scanner`), and EXPLAIN/PRAGMA/SET ops.
- `references/version-features.md`: 47 source-cited `feature → minimum DuckDB version` rows (1.1.0→1.5.0), grouped by area, mirroring the k3s/ansible/fd/ripgrep skills.
- Inline `(duckdb vX.Y+)` version annotations sourced from duckdb.org release blogs cross-checked with git tags and empirical CLI boundary tests (DuckDB has no in-repo CHANGELOG); bedrock (≤1.0 GA, June 2024) left unannotated ("unlisted = long-standing").
- Documents the verified nuance that the `ENCRYPTION_KEY` `ATTACH` option already works in 1.3.x even though database encryption was a documented 1.4.0 feature, and the `-readonly`-requires-a-file-database (errors against `:memory:`) gotcha.
