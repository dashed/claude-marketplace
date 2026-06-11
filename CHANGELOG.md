# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.31.0] - 2026-06-11

### Added
- uv skill: new skill for **uv** — Astral's fast Python package & project manager (one binary replacing pip/pipx/pyenv/poetry/virtualenv) — authored against the uv source (dev tree past **0.11.20**; the repo's meticulous `CHANGELOG.md` as the primary version source) with every flag and workflow empirically verified on the installed **uv 0.11.2** (uv skill v1.0.0). Ships a `SKILL.md` spine (the four-surface mental model — projects/scripts/tools/python, install + self-update, six verified core workflows, quick-reference, troubleshooting) and four references: `projects.md` (`uv init/add/sync/lock/run/tree/export`, dependency groups (PEP 735) vs extras, `[tool.uv.sources]`, workspaces, `uv version` + bump, `uv build`/`uv publish` incl. trusted publishing, the universal-lockfile model), `scripts-tools-python.md` (PEP 723 inline-metadata scripts + script lockfiles, `uvx`/`uv tool`, `uv python` toolchain management, `uv venv`), `pip-config.md` (the `uv pip` interface + deviations from pip, caching, config discovery (`[tool.uv]` vs `uv.toml`) + `UV_*` env vars, named indexes + auth (`uv auth`), resolution strategies/overrides/constraints/`--exclude-newer`, `--torch-backend` where it actually lives), and `version-features.md` (37 source-cited `feature → minimum uv version` rows (0.4.x→0.11.x, preview features labeled) plus a "Breaking/renamed across 0.x minors" subsection — `uv version` repurposed 0.7.0, `--index-url` deprecation 0.4.23, `uv_build` default 0.8.0, TLS overhaul 0.11.0). Inline `(uv 0.X+)` annotations throughout; bedrock (≤0.4.0, Aug 2024) left unannotated ("unlisted = long-standing"). Writer verification against the live binary corrected several details over the research dossier (e.g. `uv auth` subcommands are `login/logout/token/dir`; `uv sync`/`uv run` have only `--no-dev`/`--only-dev`, not `--dev`; `uv tool upgrade` has no `--upgrade-package`), and the hidden 0.11.20-only `uv upgrade` command was deliberately left undocumented

## [0.30.0] - 2026-06-11

### Added
- kubernetes skill: new skill for **Kubernetes** — the `kubectl` CLI + core resource/manifest authoring layer — authored against the Kubernetes source (dev tree ~1.37; per-minor `CHANGELOG/CHANGELOG-1.x.md` + the feature-gate stage metadata in `pkg/features/kube_features.go`) with CLI items empirically verified on the installed kubectl **v1.28.2** (client-side; no cluster) (kubernetes skill v1.0.0). Ships a `SKILL.md` spine (declarative desired-state mental model, kubeconfig/contexts, six core workflows — deploy+expose, inspect a failing pod, apply/diff/rollout, exec/logs/port-forward, offline manifest generation with `--dry-run=client`, RBAC checks with `auth can-i` — plus quick-reference and a Pod-status troubleshooting table) and four references: `kubectl.md` (verbs, output formats/jsonpath, client vs server-side apply, rollout, debug with ephemeral containers, drain/taint, explain/api-resources, kustomize, scripting patterns — every flag verified against kubectl 1.28.2 `--help`; documents which `kubectl create` generators work offline and that `run`/`expose`/`autoscale`/`create role` contact the API server even under `--dry-run=client`), `workloads.md` (Pod spec essentials incl. native sidecars, Deployment/StatefulSet/DaemonSet, Job/CronJob incl. podFailurePolicy & successPolicy, HPA v2, PDB, scheduling/affinity/topology spread — field shapes verified against `staging/src/k8s.io/api/`), `cluster-resources.md` (Service/Ingress/NetworkPolicy, ConfigMap/Secret incl. update-propagation caveats, PV/PVC/StorageClass, RBAC, ServiceAccount bound tokens, DNS, downward API, kubeconfig structure), and `version-features.md` (41 source-cited `feature → minimum Kubernetes version` rows annotated by GA version with beta-on noted, plus explicitly-flagged not-yet-GA items). Inline `(k8s 1.X+)` annotations throughout; bedrock (GA ≤ ~1.20) left unannotated ("unlisted = long-standing"). Cross-linked with the k3s skill (k3s = the distribution/cluster layer; kubernetes = everything you run against it)

### Changed
- k3s skill: disambiguation note now points to the new sibling kubernetes skill for `kubectl`/resource usage instead of deferring to "Kubernetes documentation" (k3s skill v1.0.1)

## [0.29.1] - 2026-06-10

### Fixed
- sequential-thinking plugin (v1.0.3): audit fixes — corrected the README's advertised tool id to the plugin-namespaced `mcp__plugin_sequential-thinking_sequential-thinking__sequentialthinking` form (the README still showed the directly-configured form) and re-synced the README `.mcp.json` snippet with the real file (`--no-config`, added in 1.0.2); added `--no-config` to the script shebang so direct execution gets the same index isolation as the plugin launch path; bounded the `mcp` dependency to `>=1.9.4,<2` (was an unbounded `mcp>=0.1.0` silently floating to 1.27.x while code comments claimed "pinned mcp==1.9.4" — comments corrected, runtime behavior verified unchanged on the current SDK: all 58 tests pass and the stdio handshake succeeds); removed the nonstandard `[project.optional-dependencies]` table from the PEP 723 block. The server script now intentionally diverges from the verbatim `mcp-personal` copy — port upstream to re-converge
- ultrathink skill (v1.1.2): documented the interplay with Claude Code's native `ultrathink` extended-thinking keyword (both can trigger on the same prompt; the skill externalizes reasoning as visible tool calls), made the `DISABLE_THOUGHT_LOGGING` guidance actionable for plugin installs, and noted the server's `≥ 1` numeric parameter constraints
- Synced `.claude-plugin/plugin.json` versions with marketplace.json across all four MCP plugins (file-search → 1.0.1, fuzzy-search → 1.1.1, sqlite → 1.0.1, sequential-thinking → 1.0.3) — all were stuck at their initial 1.0.0

## [0.29.0] - 2026-06-09

### Added
- **PostgreSQL skill suite** — five focused, non-overlapping skills covering PostgreSQL, authored in parallel by an agent team against the PostgreSQL source tree (dev tree at **19beta1**, so the stable line is **PG 18** and **PG 19** is beta). Every skill mirrors the duckdb gold-standard pattern (a `SKILL.md` spine under 500 lines + a `references/` directory with a source-cited `version-features.md`), carries inline `(pgNN+)` version annotations, and leaves **bedrock** (features stable since the 9.x era) unannotated ("unlisted = long-standing"). All version pins were verified against the in-tree SGML docs (`doc/src/sgml/ref/`, topic SGML, and `release-19.sgml`) cross-checked with postgresql.org release notes — nothing guessed; unsourced features were treated as bedrock.
- psql skill: new skill for **psql**, PostgreSQL's interactive terminal client and SQL script runner (psql skill v1.0.0). `SKILL.md` (325 lines) + 5 references — `meta-commands.md` (the `\d`/`\copy`/`\watch`/`\gexec`/`\if` backslash catalog), `connection.md` (conninfo/URIs, `PG*` env, `~/.pgpass`, service files, SSL/multi-host, precedence), `scripting.md` (agent/CI patterns, `ON_ERROR_STOP`, exit codes, transactions, `FETCH_COUNT`, `.psqlrc`), `pipeline.md` (extended-protocol/pipeline family), and `version-features.md` (33 sourced rows, pg14→pg19). Corrected three commonly-mis-pinned facts via the versioned manuals: the pipeline family + `\parse`/`\bind_named`/`\close_prepared` are **pg18+** (not pg17; there is no `\close` — it is `\close_prepared`), `\getenv` is **pg15+** (pg14 added only `\dX`), and `\watch` sub-features split across pg16/pg17/pg18. Documents `\restrict`/`\unrestrict` as a CVE-2025-8714 security-minor backport (13.22/14.x/15.x/16.10/17.6/18+) rather than a clean major-version feature.
- postgres-sql skill: new skill for the **PostgreSQL SQL dialect & data types** (postgres-sql skill v1.0.0). `SKILL.md` (401 lines) + 6 references — `dml-returning.md`, `queries.md`, `json.md`, `data-types.md`, `partitioning.md`, `version-features.md` (32 sourced rows, pg10→pg19beta). Resolves the SQL/JSON **pg16-vs-pg17** split precisely: pg16 = `IS JSON` + the `JSON_ARRAY`/`JSON_ARRAYAGG`/`JSON_OBJECT`/`JSON_OBJECTAGG` constructors + `ANY_VALUE()`; pg17 = the `JSON_TABLE`/`JSON_QUERY`/`JSON_VALUE`/`JSON_EXISTS` query functions **and** `JSON()`/`JSON_SCALAR()`/`JSON_SERIALIZE()`. Other verified pins: `MERGE` base pg15 with `RETURNING`/`merge_action()`/`WHEN NOT MATCHED BY SOURCE` pg17; `RETURNING OLD/NEW` pg18; **VIRTUAL generated columns pg18 and now the default** (flagged to write `STORED` explicitly); multiranges + `DETACH … CONCURRENTLY` pg14; recursive-CTE `SEARCH`/`CYCLE` pg14; hash/`DEFAULT` partitions pg11; CTE `MATERIALIZED` + jsonpath pg12.
- postgres-performance skill: new skill for **PostgreSQL query & performance tuning** (postgres-performance skill v1.0.0). `SKILL.md` (362 lines) + 6 references — `explain.md`, `reading-plans.md`, `indexes.md`, `statistics-and-planner.md`, `vacuum-and-bloat.md`, `version-features.md` (~60 sourced rows). Verified EXPLAIN-options matrix: `SETTINGS` pg12, `WAL` pg13, `GENERIC_PLAN` pg16, `SERIALIZE`+`MEMORY` pg17, `BUFFERS` auto-on-with-`ANALYZE` pg18, and a new `IO` option (AIO stats) in **pg19 beta**. Corrects the parallel-query timeline (parallel aggregate + nested-loop/hash joins debuted in 9.6; only Parallel Hash + Parallel Append are pg11) and documents the **pg19 `REPACK`** command deprecating `VACUUM FULL` (with the pg18-and-earlier fallback). Covers the six index types (btree/GIN/GiST/SP-GiST/BRIN/hash), covering `INCLUDE` (pg11), `REINDEX CONCURRENTLY` (pg12), and extended statistics (`CREATE STATISTICS` pg10; MCV pg12).
- postgres-admin skill: new skill for **PostgreSQL server administration & operations** (postgres-admin skill v1.0.0). `SKILL.md` (372 lines) + 6 references — `config.md`, `auth-roles.md`, `backup-recovery.md`, `replication.md`, `monitoring.md`, `version-features.md` (84 sourced rows, pg10→pg19). Precisely pinned: incremental backup + `pg_combinebackup` + failover-slot sync (`sync_replication_slots`) pg17; `pg_stat_io` pg16; logical-replication row filters + column lists + `FOR TABLES IN SCHEMA` pg15; `scram-sha-256` available pg10 / default pg14; the predefined-roles timeline (`pg_read/write_all_data` pg14 → `pg_maintain` pg17 → `pg_signal_autovacuum_worker` pg18); `pg_stat_checkpointer` split pg17; `recovery.conf` removal pg12. Mines pg19-beta additions (`effective_wal_level`, `pg_hosts.conf`, `CHECKPOINT` options, non-text `pg_dumpall`, new stat views) from `release-19.sgml`.
- postgres-extensions skill: new skill for **PostgreSQL extension management + the bundled `contrib` catalog** (postgres-extensions skill v1.0.0). `SKILL.md` (319 lines) + 3 references — `contrib-catalog.md` (559 lines cataloging all ~44 `CREATE EXTENSION` modules plus the LOAD-only/preload modules and client programs), `management.md` (`CREATE`/`ALTER`/`DROP`, the file/`.control` model, catalogs, trusted mechanics, the preload matrix, dump/restore), and `version-features.md` (34 sourced rows, pg10→pg19beta). Key verified facts: `gen_random_uuid()` graduated to **core in pg13** (pgcrypto's copy is now a wrapper); `uuidv7()`/`uuidv4()` core in pg18; **trusted extensions (pg13)** with the 20-module default list taken verbatim from in-tree `contrib.sgml`; `auto_explain`/`pg_overexplain`/`pg_plan_advice` are LOAD-only (no `CREATE EXTENSION`); `adminpack` removed in **pg17**; `pg_surgery` pg14, `pg_walinspect` pg15, `pg_overexplain`/`pg_logicalinspect` pg18, `pg_plan_advice`/`pg_stash_advice` pg19-beta. Notes that a `.control` `default_version` is **not** the PostgreSQL version.

## [0.28.0] - 2026-06-08

### Added
- jq skill: new skill for **jq** — the command-line JSON processor and its filter language — scoped to the CLI + filter language + builtin library, authored against the jq source (jqlang/jq, dev tree past jq-1.8.2rc1) with every example verified on the installed CLI **jq-1.7.1** (jq skill v1.0.0). Ships a `SKILL.md` spine (the filter/stream mental model, install, invocation, seven runnable core workflows — extract with `-r`, `select`/`map`, reshape objects, `@csv`/`@tsv`, slurp+aggregate/`group_by`, `--arg`/`$ENV`, `-f` program file — plus agent usage, quick-reference, and troubleshooting) and four references: `cli.md` (every flag verified against `jq --help`, I/O & slurp modes, the full exit-code set, `$ARGS`/`$ENV`, modules, agent patterns), `language.md` (path expressions, pipe/comma, construction, operators, `//`, `if`/`try`/`?`, `reduce`/`foreach`, variables & destructuring + `?//`, `def`/recursion, `label`/`break`, string interpolation, assignment + path-expression semantics, modules), `builtins.md` (the function library grouped: types, arrays/objects, regex, format strings, math, dates, streaming, SQL-style, debug), and `version-features.md` (35 source-cited `feature → minimum jq version` rows for 1.7/1.7.1/1.8 + a labeled "Removed" subsection). Inline `(jq 1.X+)` version annotations throughout, sourced from the repo's `NEWS.md` cross-checked with the versioned manuals (`docs/content/manual/v1.6`→`v1.8`), git blame on `src/builtin.jq`, and empirical CLI boundary tests; bedrock (≤1.6, 2018) left unannotated ("unlisted = long-standing"). Documents three commonly-assumed features that do **not** exist in jq (`@base32`/`@base32d`, `toarray`, `dateadd`) and the 1.7 removals (`--argfile`, `leaf_paths`, `recurse_down`)

## [0.27.0] - 2026-06-05

### Added
- duckdb skill: new skill for **DuckDB** — the in-process, columnar, vectorized OLAP SQL engine shipped as a single zero-dependency binary ("SQLite for analytics") — scoped to the CLI + SQL authoring surface and authored against the DuckDB source (dev tree past v1.5.3) with every example verified on the installed CLI **v1.3.2** (duckdb skill v1.0.0). Ships a `SKILL.md` spine (mental model, when-to-use vs SQLite/Postgres, install, the `duckdb` CLI at a glance, six runnable core workflows — direct file query, persistent vs `:memory:`, CSV→Parquet via `COPY`, friendly-SQL exploration, httpfs/S3, `ATTACH` Postgres/SQLite — plus agent-usage, quick-reference, and troubleshooting) and four references: `cli.md` (every flag + dot-command verified against `duckdb -help`/`.help`, output modes, non-interactive/agent patterns), `sql-dialect.md` (friendly-SQL differentiators: FROM-first, `SELECT * EXCLUDE/REPLACE`, `COLUMNS()`, `GROUP BY/ORDER BY ALL`, `QUALIFY`, `PIVOT`/`UNPIVOT`, ASOF/positional joins, nested types + lambdas + comprehensions, `SUMMARIZE`, `USING SAMPLE`, `PREPARE`), `data-io.md` (replacement scans, `read_csv`/`read_parquet`/`read_json`, `COPY … TO` with partitioning, `EXPORT`/`IMPORT DATABASE`, `ATTACH` for duckdb/sqlite/postgres/mysql, the extension system + httpfs/S3 `CREATE SECRET`, and EXPLAIN/PRAGMA/SET ops), and `version-features.md` (47 source-cited `feature → minimum DuckDB version` rows, 1.1.0→1.5.0). Inline `(duckdb vX.Y+)` version annotations throughout, sourced from duckdb.org release blogs cross-checked with git tags and empirical CLI boundary tests (no in-repo CHANGELOG exists); bedrock (≤1.0 GA, June 2024) left unannotated ("unlisted = long-standing"). Documents the verified nuance that database encryption's `ENCRYPTION_KEY` option already works in 1.3.x though documented as a 1.4.0 feature, and the `-readonly`-needs-a-file-DB gotcha

## [0.26.0] - 2026-06-05

### Changed
- jj skill: expanded coverage of the "already-pushed / colocated-repo" reality that greenfield examples never exercised (jj skill v1.7.0) — every claim re-verified against live `jj` 0.41.0 before shipping:
  - **SKILL.md**: new "Colocated repos: Git sees `@` as uncommitted" pitfall (Git's `HEAD` tracks `@`'s parent, so `@`'s changes look uncommitted to Git; `git checkout`/`git switch` and git-based tooling can abort — *only* when the target branch touches the same files — fixed by parking `@` with `jj new <bookmark>`); a one-line "reorder a pushed/stacked branch" pointer in Pushing Changes; broadened the "Immutable commit error" note to include untracked remote bookmarks and to show `--ignore-immutable` in both global and subcommand position; refined the merge-commit pitfall to note empty/description-less `@` auto-abandons.
  - **references/github-workflow.md**: new "Reordering an Already-Pushed / Stacked Branch" recipe (`jj rebase --ignore-immutable -s … -d …` → `jj git push --bookmark …`, which is force-with-lease-safe by default; plain-git `git push --force-with-lease` alternative).
  - **references/commands.md**: documented that `jj squash --from <child> --into <parent>` relocates the child's bookmark onto the parent (with the `-m`/`--use-destination-message` non-interactive caveat), and that `--ignore-immutable` works in subcommand position.

### Fixed
- jj skill: corrected the immutable-commits default in `references/configuration.md` (two sites). The real default is `builtin_immutable_heads()` = `trunk() | tags() | untracked_remote_bookmarks()` — trunk, tags, and **untracked** remote bookmarks — not `trunk() | tags()` as previously labeled "the default". Branches pushed with `jj git push` are tracked (mutable); branches managed by external git tooling (git/gh/git-chain) arrive untracked (immutable). This aligns `configuration.md` with the already-correct `references/revsets.md`. (Note: the source improvement proposal's own wording — "any commit a remote bookmark points to" — was itself inaccurate; verification against jj 0.41.0 established the untracked-only rule, and the invalid `jj git push --force-with-lease` it suggested was dropped since `jj git push` is lease-safe by default.)

## [0.25.1] - 2026-06-05

### Added
- obsidian-bases skill: folded in four stable items from the current official Bases docs that the upstream port omitted (obsidian-bases skill v1.0.1) — each verified against help.obsidian.md before adding:
  - `random()` global function (`random(): number`, refreshes on each view load) in `references/FUNCTIONS_REFERENCE.md`. Source: https://help.obsidian.md/bases/functions
  - `file.file` property (the file object itself, only usable in specific functions) in the `SKILL.md` file-properties table. Source: https://help.obsidian.md/bases/syntax
  - an Arithmetic Operators table (`+` `-` `*` `/` `%` `( )`) under Formula Syntax in `SKILL.md`. Source: https://help.obsidian.md/bases/syntax
  - the inline `base` code-block embed method (define a base in a note via a fenced ` ```base ` block) in `SKILL.md`. Source: https://help.obsidian.md/bases/syntax
  - `SKILL.md` `## Credits` now notes these local additions.
- Deliberately NOT added (could not be confirmed against the official docs): a view-level `sort:` YAML key (docs show only `order`/`groupBy`; sorting is UI-only on the Views page) and Duration `.years`/`.months`/`.weeks` fields (the official functions page has no Duration field table at all). Left out to avoid shipping unverified syntax.

## [0.25.0] - 2026-06-05

### Added
- obsidian-bases skill: new skill for authoring **Obsidian Bases** (`.base` files) — the YAML format that turns notes into database-like table/cards/list/map views with filters, computed formulas, and summary aggregations — ported **verbatim** from the upstream [obsidian-bases](https://github.com/kepano/obsidian-skills/tree/main/skills/obsidian-bases) skill by Steph Ango (@kepano), MIT (obsidian-bases skill v1.0.0). Ships a `SKILL.md` spine (creation workflow; the `.base` schema; filter syntax + operators and recursive and/or/not; the three property types and the `file.*` properties table; the `this` keyword; formula syntax; key functions + the Duration `.days` caveat and date arithmetic; the four view types; default summary formulas; three complete worked examples — task tracker, reading list, daily-notes index; base embedding; YAML quoting rules; troubleshooting) plus `references/FUNCTIONS_REFERENCE.md` (the complete per-type function reference: global, Any, Date, Duration, String, Number, List, File, Link, Object, RegExp). The reference file is byte-identical to upstream; `SKILL.md` adds only a `## Credits` attribution block

## [0.24.1] - 2026-06-05

### Fixed
- obsidian-markdown skill: corrected three details to match the current official Obsidian docs (obsidian-markdown skill v1.0.1) — a first marketplace-local divergence from the verbatim upstream port:
  - **Tag rules**: removed the inaccurate "numbers (not first character)" restriction (in `SKILL.md` and `references/PROPERTIES.md`). The real rule is that a tag must contain at least one non-numeric character (`#1984` is invalid, `#y1984` is valid); also note that most Unicode characters, including emoji, are allowed. Source: https://help.obsidian.md/tags
  - **Property types** (`references/PROPERTIES.md`): removed "Links" from the property-type table — the core set is six types (Text, List, Number, Checkbox, Date, Date & time). Wikilinks are not a distinct type; they are stored inside a quoted Text or List value (the `related: "[[Other Note]]"` example is preserved as a note). Source: https://help.obsidian.md/properties
  - **Embeds** (`references/EMBEDS.md`): added the previously-omitted canvas embed (`![[My canvas.canvas]]`, which renders shapes but not card text). Source: https://help.obsidian.md/embeds
  - `SKILL.md` `## Credits` now notes these local corrections.

## [0.24.0] - 2026-06-05

### Added
- obsidian-markdown skill: new skill for authoring **Obsidian Flavored Markdown** — the Obsidian-specific extensions on top of CommonMark/GFM (wikilinks `[[Note]]`, block IDs `^id`, embeds `![[...]]`, callouts `> [!type]`, frontmatter properties, tags, `%%comments%%`, `==highlights==`, LaTeX math, Mermaid, footnotes) — ported **verbatim** from the upstream [obsidian-markdown](https://github.com/kepano/obsidian-skills/tree/main/skills/obsidian-markdown) skill by Steph Ango (@kepano), MIT (obsidian-markdown skill v1.0.0). Ships a `SKILL.md` spine (creating-a-note workflow, per-feature syntax sections, complete worked example) plus three `references/` files (`CALLOUTS.md` — the 13 callout types + aliases, foldable/nested/custom-CSS; `EMBEDS.md` — note/image/audio/PDF/list/search embeds; `PROPERTIES.md` — property types, default props, tag rules). Reference files are byte-identical to upstream; `SKILL.md` adds only a `## Credits` attribution block

### Changed
- README.md: added a prominent `> [!WARNING]` admonition clarifying that this is Alberto Leal's personal marketplace built solely for his own workflow — he is the only intended/supported user, the skills and MCP servers encode personal conventions and may change or break without notice, and anyone else uses it entirely at their own risk with no support, stability, or backward-compatibility guarantees

## [0.23.0] - 2026-06-04

### Added
- ansible skill: new skill for **ansible-core** (the agentless automation engine), authored against the ansible-core **2.22.0.dev0** source (latest released 2.21; ansible skill v1.0.0). Covers the ten `ansible*` CLIs (`ansible` ad-hoc, `ansible-playbook`, `ansible-galaxy`, `ansible-vault`, `ansible-inventory`, `ansible-doc`, `ansible-config`, `ansible-console`, `ansible-pull`, plus an `ansible-test` scope note) and the authoring surface. Ships a `SKILL.md` spine (overview, CLI map, mental model, seven core workflows, ansible.cfg essentials, troubleshooting), `references/cli.md` (shared option groups + per-binary flag reference), `references/playbooks.md` (inventory, playbook anatomy, the source-verified variable-precedence backbone, loops/conditionals/templating, roles, collections/FQCN, delegation, strategies, handlers, tags, check/diff/idempotency), `references/config-vault.md` (ansible.cfg precedence + per-section settings with `ANSIBLE_*` env vars, and the Ansible Vault deep dive), and `references/version-features.md` (37 source-verified `feature → minimum ansible-core version` rows, 2.15→2.21). Inline `(ansible-core X.Y+)` version annotations sourced from maintainer-declared `version_added:` metadata (bedrock left unannotated); documents FQCN (`ansible.builtin.*`), become methods (sudo/su/runas), strategies (linear/free/host_pinned/debug), and that ansible-core ships only `ansible.builtin` (everything else is collections)

## [0.22.0] - 2026-06-04

### Added
- teach skill: new skill that runs a Socratic teaching loop, quizzing you on a coding session until you have confirmed mastery of every concept (teach skill v1.0.0). Sources sessions from `~/.claude/projects/`, tracks a per-concept checklist (Problem / Solution / Broader Context), and never wraps up until every item is confirmed. Ported from the upstream `teach` skill by [alexknowshtml](https://github.com/alexknowshtml/claude-skills/tree/main/teach), itself based on a gist by ThariqS and a teaching concept by Suzanne. Ships a `SKILL.md` spine plus three `references/` files

## [0.21.0] - 2026-06-04

### Added
- k3s skill: new skill for the `k3s` lightweight CNCF-certified Kubernetes distribution, authored against the k3s **v1.35.0+k3s1** source (k3s skill v1.0.0). Covers the `k3s` multicall binary — `server` (~85 flags), `agent` (~45 flags), and the `token`/`etcd-snapshot`/`secrets-encrypt`/`certificate`/`check-config`/`completion` subcommands plus the `kubectl`/`crictl`/`ctr` passthroughs. Includes a `SKILL.md` spine (install, subcommand map, six core workflows: single-server, HA embedded etcd, external datastore, agent join, component disables, day-2 ops), `references/options.md` (exhaustive flag reference grouped by area, with K3S_* env equivalents and Hidden/Exp/Dep markers), `references/recipes.md` (HA bootstrap, airgap, private registries, CNI swap, secrets-encryption rotation, etcd snapshot + `cluster-reset` restore, cert rotation, remote kubeconfig, uninstall, upgrades), and `references/version-features.md` (21 source-verified `feature → minimum k3s version` rows, mirroring the git/fzf/fd/ripgrep skills). Inline `(k3s vX.Y+)` version annotations throughout (bedrock flags left unannotated); documents the `--disable` component set (coredns IS disable-able), token vs agent-token semantics, embedded-etcd odd-quorum, the config-file `.d` drop-ins + `+`-append semantics, and the disabled slice-flag comma-split quirk

## [0.20.1] - 2026-06-04

### Fixed
- file-search, fuzzy-search, sequential-thinking, and sqlite plugins (MCP): added `--no-config` to the `uv run` invocation in each plugin's `.mcp.json` so the server always resolves its pinned dependencies from the default PyPI index, independent of the *consuming* repo's uv configuration. Previously, launching Claude Code from a directory whose `pyproject.toml`/`uv.toml` declares a non-PyPI `[[tool.uv.index]]` with `default = true` (e.g. a private mirror) made `uv run --script` adopt that index; resolving `mcp>=0.1.0` (and PyMuPDF) then failed with "not found in the package registry" and every server reported `✘ failed` in `/mcp`. `--no-config` makes uv skip ambient project/user config and use PyPI (file-search 1.0.1, fuzzy-search 1.1.1, sequential-thinking 1.0.2, sqlite 1.0.1)

## [0.20.0] - 2026-06-04

### Added
- fuzzy-filter skill: new skill documenting the non-interactive `rg`/`fd`/`rga` → `fzf --filter` pipeline (the CLI technique behind the fuzzy-search MCP) — SKILL.md + references/pipelines.md (with the exact CLI equivalent of each fuzzy-search MCP tool) + references/pdf.md (fuzzy-search skill v1.0.0). Explicitly disambiguated from the interactive `fzf` skill and the `fuzzy-search` MCP; cross-linked from the fzf/ripgrep/fd skills

### Changed
- fuzzy-search plugin (MCP): hardened the rg→fzf pipeline (fuzzy-search MCP v1.1.0) — `fuzzy_search_content` now parses `rg --json` (fixes advertised-but-broken `-A`/`-B`/`-C` context, colons-in-paths, and encoding), `rg_flags` tokenized via `shlex.split` (quoted globs now work), subprocess timeouts on rg/rga/fzf, multiline skips binaries + avoids O(n²) buffering, PyMuPDF handles closed on error paths, and the stale fzf-ranking `xfail` test was fixed to pass for real. The bundled script now carries documented local patches (no longer byte-verbatim from `mcp-personal`)

## [0.19.0] - 2026-06-04

### Added
- ripgrep skill: new skill for the `ripgrep` (`rg`) command-line tool (a fast, gitignore-aware recursive `grep`), authored against ripgrep 15.x (ripgrep skill v1.0.0). Includes a `SKILL.md` spine, `references/options.md` (all 104 flags grouped by category), `references/recipes.md` (multiline/replace/custom-types/preprocessing/config/integration), and `references/version-features.md` (feature → minimum ripgrep version lookup, mirroring the git/fzf/fd skills). Inline `(rg X.Y+)` version annotations throughout (long-standing basics unannotated); documents that there is no bare `--hyperlink` flag (only `--hyperlink-format`), `--generate` replaced `--man`, and `--engine` replaced `--auto-hybrid-regex`

## [0.18.0] - 2026-06-04

### Added
- fd skill: new skill for the `fd` command-line tool (a fast `find` replacement), authored against fd v10.4.2 (fd skill v1.0.0). Includes a `SKILL.md` spine, `references/options.md` (exhaustive flag reference), `references/recipes.md` (command execution + tool integration), and `references/version-features.md` (feature → minimum fd version lookup, mirroring the git/fzf skills). Inline `(fd X.Y+)` version annotations throughout, with long-standing basics left unannotated; documents that fd has no `{n}`/positional placeholders and excludes master-only flags not in v10.4.2

## [0.17.0] - 2026-06-04

### Added
- fzf skill: `references/version-features.md` — a "feature → minimum fzf version" lookup (mirrors the git skill's version-features pattern), and inline `(fzf X.Y+)` version annotations across SKILL.md and all reference files. Versions verified against the fzf v0.73.1 CHANGELOG section headers (fzf skill v1.1.0)

### Changed
- fzf skill: full accuracy/currency refresh against fzf v0.73.1 — documented `--popup` (Zellij support) as primary with `--tmux` as alias, added `dashed` border, `--nushell`, `--preview-window=next`, `--id-nth`, `every(N)` event, footer actions, and the `toggle-wrap-word` default rebind; corrected the `ALT-R`/`toggle-raw` description; documented the smart-case default; hardened the git integration recipes and added a `transform` example; softened the actions.md "complete reference" claim

## [0.16.0] - 2026-06-04

### Added
- file-search plugin: new MCP-server plugin wrapping the upstream fd+fzf server (`mcp_fd_server.py`, ported verbatim from mcp-personal). Exposes `search_files` (fd regex/glob) and `filter_files` (fzf fuzzy) tools. Bundles the upstream test suite verbatim (`test_fd_server.py`, `test_simple.py`, `test_cli.py`, 49 cases, all passing against real fd/fzf) with a `pyproject.toml` dev extra and a `make test-file-search` target. Requires uv, fd, and fzf
- fuzzy-search plugin: new MCP-server plugin wrapping the upstream ripgrep+fzf server (`mcp_fuzzy_search.py`, ported verbatim). Exposes fuzzy content/file/document search (`fuzzy_search_files`, `fuzzy_search_content`, `fuzzy_search_documents`) plus PyMuPDF-backed PDF tools (`extract_pdf_pages`, `get_pdf_outline`, `get_pdf_page_count`, `get_pdf_page_labels`). Bundles the upstream test suite verbatim (`test_fuzzy_search.py`) with a `make test-fuzzy-search` target. Requires uv, ripgrep, and fzf (ripgrep-all for documents)
- sqlite plugin: new MCP-server plugin wrapping the upstream SQLite server (`mcp_sqlite_server.py`, ported verbatim). Exposes `query`, `execute`, `list_tables`, `describe_table`, `create_table`; read-only by default, writes opt-in via `--allow-writes` / `MCP_SQLITE_ALLOW_WRITES`. Bundles the upstream test suite verbatim (`test_sqlite_server.py`) with a `make test-sqlite` target. Requires only uv (sqlite3 is stdlib)
- Each new MCP plugin follows the established pattern (verbatim server under `scripts/`, `.mcp.json`, metadata-only `plugin.json`, `pyproject.toml` with `pythonpath=["scripts"]`, bundled tests via a `tests/conftest.py` path shim that keeps the upstream test modules verbatim)

## [0.15.2] - 2026-05-30

### Added
- sequential-thinking plugin: bundled the upstream test suite (`tests/test_sequential_thinking.py`, 58 cases) verbatim from `mcp-personal`, a `pyproject.toml` dev extra, and a `make test-sequential-thinking` target. All tests pass against the verbatim server copy, confirming the port is faithful. Establishes the per-plugin test pattern for MCP-server plugins (mirrors `chrome-cdp` / `react-best-practices`)

## [0.15.1] - 2026-05-30

### Fixed
- ultrathink skill: Corrected the Sequential Thinking tool reference to the plugin-namespaced id `mcp__plugin_sequential-thinking_sequential-thinking__sequentialthinking` (the form Claude Code registers when the server ships as a marketplace plugin). The previous `mcp__sequential-thinking__sequentialthinking` only applies to a directly-configured MCP server. Documented both forms and the `mcp__plugin_<plugin>_<server>__<tool>` naming pattern. Verified against the live installed plugin.

## [0.15.0] - 2026-05-30

### Added
- sequential-thinking plugin: the marketplace's first MCP-server plugin, bundling a Python port of the official `sequential-thinking` MCP server (`scripts/mcp_sequential_thinking.py`, a PEP 723 `uv run --script` script) that exposes one `sequentialthinking` tool (`mcp__sequential-thinking__sequentialthinking`) for dynamic, reflective, step-by-step problem-solving
- Establishes the MCP-server plugin pattern: server bundled under `scripts/`, registered via `.mcp.json`, referenced from the marketplace entry with `"mcpServers": "./.mcp.json"` instead of `"skills"`

### Changed
- ultrathink skill: Corrected the Sequential Thinking tool reference from underscores to hyphens (`mcp__sequential-thinking__sequentialthinking`), matching the live MCP server key `sequential-thinking`
- ultrathink skill: Documented the companion `sequential-thinking` MCP plugin as a prerequisite and noted the optional `DISABLE_THOUGHT_LOGGING` env var

## [0.14.0] - 2026-05-29

### Added
- git skill: references/version-features.md — consolidated "feature → minimum git version" lookup (git skill v1.1.0)

### Changed
- git skill: Add inline git-version-availability annotations ("(git X.Y+)") across SKILL.md and all reference files, with introduced/default-changed/removed notes

## [0.13.0] - 2026-05-29

### Added
- git skill: Advanced Git CLI mastery + recovery skill targeting git 2.54+ (v1.0.0)
- git skill: SKILL.md spine with object model, HEAD/index/worktree, three reset modes table, refspecs, an "Oh No" recovery quick-reference, safety/footgun rules, and a reference map
- git skill: 10 progressive-disclosure reference files (recovery, history-rewriting, branching-merging, inspection, refspecs-remotes, worktrees-stash, internals-plumbing, config-attributes-hooks, advanced-features, troubleshooting)
- git skill: Explicitly defers to conventional-commits, git-chain, git-absorb, and jj skills to avoid overlap
- hledger skill: Plain-text double-entry accounting with hledger (v1.0.0)
- hledger skill: Comprehensive SKILL.md with journal basics, commands, workflows, querying, multi-currency
- hledger skill: 6 reference files (commands, journal-format, queries, csv-import, reports, budgeting)
- style-extractor skill: Narrative construction layer for fiction with 10 structural dimensions
- style-extractor skill: references/narrative-dimensions.md with analysis guide and AI defaults table
- style-writer skill: Narrative authenticity guide with AI debiasing checklists and Claude-specific fingerprints
- style-writer skill: references/narrative-authenticity.md with 30 core features from StoryScope research
- style-writer skill: Narrative construction evaluation framework (5 dimensions, 1-5 scoring)

### Changed
- style-extractor skill: SKILL.md distinguishes surface style from narrative construction for fiction sources
- style-writer skill: SKILL.md adds fiction-specific workflow with narrative authenticity pre/post checks
- style-writer skill: evaluation-guide.md extended with narrative construction scoring and pitfalls

## [0.12.0] - 2026-05-25

### Added
- statusline skill: Configure Claude Code status line with VCS-aware scripts (v1.0.0)
- statusline skill: Reference script with git + jj support, complete JSON field documentation
- statusline skill: Dual VCS mode showing both jj and git status independently for colocated repos (v1.1.0)
- statusline skill: Ahead/behind remote tracking for jj bookmarks via commit_id
- jj skill: Add references/github-workflow.md for GitHub/GitLab PR workflows and fork patterns
- jj skill: Add references/faq-patterns.md with 14 common patterns (private commits, lost commits, megamerge, etc.)
- jj skill: Add references/conflicts.md with conflict resolution deep dive (marker styles, workflows, multi-sided)
- jj skill: Add missing commands (absorb, evolog, commit, parallelize, revert, simplify-parents, interdiff, fix, bisect, next/prev, sparse, sign, metaedit)
- jj skill: Add CLI revision options guide (-r/-s/-b/-f, -o/-A/-B/-t patterns)
- jj skill: Add megamerge pattern for parallel integration with jj absorb routing
- jj skill: Add `all:` prefix pattern and WIP batch rebase recipe to revsets
- jj skill: Add auto-rebase opt-out pattern to conflicts reference
- jj skill: Add `squash --from` with revset ranges and `describe -r` with revsets to commands
- jj skill: Add `active()`/`wip` custom alias examples and per-repo config isolation to revsets

### Changed
- jj skill: Bump to v1.6.0
- jj skill: Enhance commands.md with missing flags for squash, split, log, show, resolve, duplicate
- jj skill: Add conflict marker styles and multiple remotes to configuration reference
- statusline skill: Change from jj-priority if/elif to independent dual-VCS if/if blocks
- statusline skill: Fix comma-join bug in status formatting (IFS trick to printf)
- statusline skill: Fix git ahead/behind labels (were swapped)
- Update version bump checklist in CLAUDE.md with current examples

## [0.11.0] - 2026-05-23

### Changed
- jj skill: Update to cover jj 0.37.0-0.41.0 (new commands, revsets, config options, breaking changes)
- jj skill: Add `jj arrange`, `jj bookmark advance`, `jj file search`, `jj util snapshot` commands
- jj skill: Add new revset functions (`divergent()`, `remote_tags()`, `diff_lines()`, `diff_lines_added/removed()`)
- jj skill: Document `xyz/n` versioned change ID syntax, `--no-integrate-operation` flag
- jj skill: Update bookmark track/untrack syntax, push behavior, and configuration reference
- jj skill: Add references/templates.md - comprehensive template language reference
- jj skill: Add references/filesets.md - fileset language reference
- jj skill: Enhance references/revsets.md with 20+ missing functions, string/date patterns
- jj skill: Add minimum version requirements table and template/fileset sections to SKILL.md

### Added
- anki-flashcards skill: Create and manage Anki flashcards via the AnkiConnect API (v1.0.0)
- anki-flashcards skill: Comprehensive API reference covering all 100+ AnkiConnect actions
- anki-flashcards skill: Flashcard design best practices guide with effective card patterns
- style-writer skill: Write content using stored writing styles with smart context loading and self-evaluation (v1.0.0)
- style-writer skill: Reference documentation for self-scoring with common pitfalls and improvement strategies
- style-extractor skill: Extract and document writing styles from source texts into reusable style guides (v1.0.0)
- style-extractor skill: Four-phase workflow with 17 style dimensions for comprehensive voice analysis
- style-extractor skill: Reference documentation for style dimensions and deliverable templates
- pup skill: Datadog CLI (pup) for observability, monitoring, logs, APM, security, and infrastructure
- pup skill: Reference documentation for commands, workflows, query syntax, and advanced features

## [0.10.0] - 2026-04-16

### Added
- gogcli skill: Google Workspace CLI wrapper around the `gog` binary (gogcli v0.12.0, by Peter Steinberger) for Gmail, Calendar, Drive, Docs, Slides, Sheets, Chat, Tasks, Contacts, Classroom, Forms, Keep, Admin, and Cloud Identity Groups (v1.0.0)
- gogcli skill: Agent-mode documentation covering JSON output, `--select` projection, `--dry-run`/`--force`/`--no-input` safety rails, stable exit codes, `gog schema`, and the `--enable-commands` sandbox
- gogcli skill: Progressive disclosure with 7 references/ guides (auth, gmail, calendar, drive, sheets, docs-slides, other-surfaces)
- react-best-practices skill: React and Next.js performance optimization guidelines from Vercel Engineering (v1.0.0)
- react-best-practices skill: 62 rules across 8 categories (waterfalls, bundle size, server-side, client-side, re-renders, rendering, JS performance, advanced patterns)
- react-best-practices skill: Python build scripts for compiling, validating, and extracting test cases from rules
- react-best-practices skill: references/rule-authoring.md for rule creation and maintenance
- chrome-cdp skill: Lightweight Chrome DevTools Protocol CLI for interacting with live Chrome sessions (v1.0.0)
- chrome-cdp skill: 13 commands (list, snap, eval, shot, html, nav, net, click, clickxy, type, loadall, evalraw, stop)
- chrome-cdp skill: Per-tab persistent daemon architecture with Unix socket NDJSON protocol
- chrome-cdp skill: Python implementation adapted from original Node.js version by Petr Baudis
- chrome-cdp skill: references/coordinate-system.md with DPR detection and CSS pixel mapping
- chrome-cdp skill: references/daemon-ipc.md with socket protocol and request/response schema
- ai-friendly-cli skill: Build and refactor CLIs for AI agent compatibility (v1.0.0)
- ai-friendly-cli skill: 8 core principles with implementation priority checklist
- ai-friendly-cli skill: Reference documentation for output patterns, input hardening, safety patterns, and architecture
- linear skill: Linear issue, project, and team management (v2.3.1)
- linear skill: TypeScript SDK scripts, label taxonomy, reference documentation
- linear skill: Unit tests, ESLint linting, TypeScript type checking, Prettier formatting
- Makefile targets for TypeScript quality gates (lint-typescript, typecheck-typescript, format-typescript, test-linear)
- mermaid-cli skill: Generate diagrams and visualizations from Mermaid markup using mmdc command-line tool
- mermaid-cli skill: Comprehensive SKILL.md with prerequisites, basic workflow, common patterns, and troubleshooting
- mermaid-cli skill: Progressive disclosure structure with references/ directory
- mermaid-cli skill: references/cli-reference.md - Complete CLI flag reference with all options and examples
- mermaid-cli skill: references/configuration.md - Mermaid config, puppeteer config, themes, and CSS styling
- mermaid-cli skill: Diagram validation and fix patterns for verifying and correcting Mermaid syntax
- walkthrough-to-obsidian skill: Convert game walkthroughs and guides into structured, interlinked Obsidian markdown pages
- walkthrough-to-obsidian skill: 7-phase conversion workflow (Analyze, Plan, Stub+Index, Convert, Audit, Navigation, Cross-links)
- walkthrough-to-obsidian skill: references/formatting-guide.md for Obsidian markdown formatting rules
- walkthrough-to-obsidian skill: references/cross-linking-guide.md for wiki-link taxonomy and patterns
- walkthrough-to-obsidian skill: Agent team parallelization support for large documents
- long-form-math skill: Long-form, understanding-focused mathematical writing style inspired by Cummings and Chartrand
- long-form-math skill: Three-phase proof workflow (Pre-Proof Strategy, Proof, Post-Proof Analysis)
- long-form-math skill: references/proof-writing-guide.md - Proof templates for 8 techniques, worked examples, technique selection flowchart
- long-form-math skill: references/exposition-patterns.md - Definition introduction workflows, motivation-first patterns, historical storytelling, writing rules

### Changed
- linear skill: Bump @linear/sdk from ^68.1.0 to ^76.0.0 (align with official Linear SDK repo)
- skill-creator skill: Update to v2.0.0 matching upstream anthropic-skills repository
- skill-creator skill: Complete rewrite with eval framework, benchmarking, and description optimization
- skill-creator skill: Add agents/ directory for evaluation (grader, comparator, analyzer)
- skill-creator skill: Add eval-viewer/ for reviewing evaluation results
- skill-creator skill: Replace old references with comprehensive schemas documentation

## [0.9.0] - 2026-01-15

### Added
- design-principles skill: Guide AI-assisted UI generation toward enterprise-grade, intentional design
- design-principles skill: Based on [claude-design-skill](https://github.com/Dammyjay93/claude-design-skill) by Dammyjay93
- design-principles skill: 6 design directions (Precision & Density, Warmth & Approachability, Sophistication & Trust, etc.)
- design-principles skill: Core craft principles (4px grid, symmetrical padding, consistent depth strategies, typography hierarchy)
- jj skill: Editor Settings section in references/configuration.md (priority order, terminal/GUI editors, quick config commands)
- jj skill: Working copy snapshot trigger explanation (when snapshots occur, how to force them)
- jj skill: Binary file conflict resolution using `jj restore --from`
- jj skill: Multi-parent (merge) conflict resolution workflow
- jj skill: Colocated Mode Deep Dive section (git status interpretation, index sync issues)
- jj skill: Bookmark gotchas (--allow-backwards, * suffix meaning, create vs set)
- jj skill: Non-Interactive Workflows section (avoid editors with -m/-u flags, --tool for resolve)
- jj skill: Common Pitfalls section (push flag combinations, working copy on merges)
- jj skill: Advanced Revset Recipes in revsets.md (roots pattern for branch rebasing)
- jj skill: Push flag compatibility table in commands.md
- zellij skill: Terminal workspace and multiplexer for interactive CLI sessions
- zellij skill: Comprehensive SKILL.md with session management, programmatic control, common workflows
- zellij skill: references/actions.md - Complete action reference (50+ actions)
- zellij skill: references/layouts.md - KDL layout syntax and examples
- fzf skill: Command-line fuzzy finder for interactive filtering of any list
- tmux skill: Interactive git recipe for `git add -p`, `git stash -p`, `git checkout -p`, `git reset -p` workflows
- fzf skill: Comprehensive SKILL.md covering shell integration, search syntax, preview windows, event bindings
- fzf skill: references/actions.md - Complete list of bindable actions and events
- fzf skill: references/options.md - Full command-line options reference
- fzf skill: references/integrations.md - ripgrep, fd, bat, git, docker, kubernetes integration recipes
- jj skill: Jujutsu (jj) version control system - Git-compatible VCS with novel features
- jj skill: Comprehensive SKILL.md with key concepts, essential commands, workflows, troubleshooting
- jj skill: references/revsets.md - Complete revset language reference
- jj skill: references/commands.md - Full command reference organized by category
- jj skill: references/git-comparison.md - Git to jj command mapping and workflow comparisons
- jj skill: references/configuration.md - Configuration, templates, filesets, aliases reference
- git-chain skill: Manage and rebase chains of dependent Git branches (stacked branches)
- git-chain skill: Progressive disclosure structure with references/ directory
- git-chain skill: references/rebase-options.md with all rebase flags, conflict handling, recovery
- git-chain skill: references/merge-options.md with all merge flags, strategies, reporting
- git-chain skill: references/chain-management.md with setup, navigation, organization
- playwright skill: Browser automation with Playwright for Python using uv inline scripts
- playwright skill: Scripts for common operations (check_setup.py, screenshot.py, navigate.py, fill_form.py, evaluate.py)
- playwright skill: Comprehensive reference documentation (api-reference.md, selectors.md, custom-scripts.md, troubleshooting.md)
- playwright skill: Modern locator API patterns (get_by_role, get_by_label, etc.)
- playwright skill: PEP 723 inline script metadata for self-contained scripts

## [0.8.0] - 2025-11-23

### Added
- tmux skill: kill-session.sh tool for atomically killing tmux sessions and removing from registry
- tmux skill: Three operation modes for kill-session.sh: registry lookup (-s), explicit socket/target (-S/-t), auto-detect
- tmux skill: Comprehensive test suite for kill-session.sh (24 plugin-level tests, 17 marketplace-level tests)
- tmux skill: Dry-run mode (--dry-run) and verbose mode (-v) for kill-session.sh

### Fixed
- tmux skill: time_ago() function now properly handles empty/missing timestamps (returns "unknown" instead of incorrect negative values)

### Changed
- tmux skill: Version bumped to 1.4.0

## [0.7.1] - 2025-11-23

### Added
- tmux skill: Session lifecycle guide with practical day-to-day workflows (references/session-lifecycle.md)
- tmux skill: Common Workflows section in SKILL.md with decision trees and troubleshooting quick reference

### Changed
- tmux skill: Version bumped to 1.3.1

## [0.7.0] - 2025-11-23

### Added
- tmux skill: Multiline support for safe-send.sh (~10x speedup for code blocks)
- tmux skill: 8 new tests for multiline functionality (tests 30-37)

### Changed
- tmux skill: Enhanced safe-send.sh with --multiline flag for efficient code block sending via paste-buffer
- tmux skill: Updated SKILL.md with multiline mode documentation and examples
- tmux skill: Version bumped to 1.3.0

## [0.6.2] - 2025-11-23

### Changed
- tmux skill: Enhanced documentation to require session name conflict checking before creation
- tmux skill: Added IMPORTANT notes to check list-sessions.sh before creating new sessions
- tmux skill: Version bumped to 1.2.3

## [0.6.1] - 2025-11-23

### Added
- tmux skill: lib/time_utils.sh library for time utility functions (time_ago() for ISO 8601 to human-readable conversion)
- tmux skill: Comprehensive test suite for time_ago() function with 10 new tests covering UTC parsing, time intervals, and edge cases

### Fixed
- tmux skill: UTC timezone bug in time_ago() where 'Z' suffix was interpreted as local time instead of UTC on macOS
- tmux skill: Empty array bug in list-sessions.sh when using set -u with no registered sessions

### Changed
- tmux skill: Extracted time_ago() to lib/time_utils.sh for better testability and reusability
- tmux skill: Version bumped to 1.2.2

## [0.6.0] - 2025-11-23

### Changed
- tmux skill: Moved "Alternative" section to references/direct-socket-control.md (progressive disclosure pattern)
- tmux skill: Renamed "Alternative: Manual Socket Management" to "Advanced: Direct Socket Control" (mental model strengthening)
- tmux skill: Reduced SKILL.md by 8% for improved conciseness and focus
- tmux skill: Version bumped to 1.2.1
- skill-reviewer skill: Relaxed Ownership criterion from required to optional
- skill-reviewer skill: Updated quality standards to make SKILL.md version sections optional while marketplace changelogs remain required
- skill-reviewer skill: Enhanced quality-checklist.md with guidance on when to include/skip version metadata
- skill-reviewer skill: Version bumped to 1.1.0

## [0.5.0] - 2025-11-23

### Added
- skill-reviewer skill: Systematic quality review framework with 10-point checklist
- skill-reviewer skill: Review workflow for new skills, updates, and audits
- skill-reviewer skill: Ownership metadata pattern with Version section (version, date, maintainer, changelog link)
- skill-reviewer skill: Testing/verification guidance pattern with Quick Verification section
- skill-reviewer skill: Comprehensive references/examples.md with 4 sample reviews (1,460 words)
- skill-reviewer skill: Sample reviews demonstrating simple, complex, quick audit, and before/after improvement patterns
- skill-reviewer skill: Progressive disclosure structure with 5 reference documents (7,459 words total)

### Changed
- skill-reviewer skill: Enhanced SKILL.md with ownership and testing sections (718 → 888 words, 59% of budget)
- skill-reviewer skill: Restructured Examples section to reference both examples.md and quality-checklist.md
- skill-reviewer skill: Detailed Guidance section now includes Review Examples link

## [0.4.0] - 2025-11-23

### Added
- tmux skill: Session registry system for automatic session tracking (~80% boilerplate reduction)
- tmux skill: tools/lib/registry.sh library for session management (415 lines, 28/28 tests passing)
- tmux skill: Portable file locking (flock on Linux, mkdir-based on macOS)
- tmux skill: create-session.sh tool for creating and registering sessions (229 lines, 20/20 tests passing)
- tmux skill: list-sessions.sh tool for listing sessions with health status (297 lines, 20/20 tests passing)
- tmux skill: cleanup-sessions.sh tool for removing dead/stale sessions (233 lines, 15/15 tests passing)
- tmux skill: Session name lookup via `-s` flag (auto-detection when single session exists)
- tmux skill: Integration test suite (test-session-integration.sh, 12/12 tests passing)
- tmux skill: Comprehensive session registry reference documentation (references/session-registry.md, 530+ lines)
- tmux skill: Session registry architecture documentation in notes/tmux/README.md
- tmux skill: Makefile test targets for session registry (test-session-registry, test-create-session, test-list-sessions, test-cleanup-sessions, test-session-integration)
- tmux skill: Docker-based test infrastructure for all tmux tests (9 test suites total)
- tmux skill: Test grouping in Makefile with helper macros for consistent execution

### Changed
- tmux skill: safe-send.sh now supports `-s` flag for session name lookup
- tmux skill: wait-for-text.sh now supports `-s` flag for session name lookup
- tmux skill: pane-health.sh now supports `-s` flag for session name lookup
- tmux skill: All core tools now support 3-tier session resolution (explicit flags > session name > auto-detect)
- tmux skill: SKILL.md restructured to make session registry the default approach (553 lines)
- tmux skill: Removed "RECOMMENDED" and "NEW" terminology from SKILL.md (mental model shift to "this is the way")
- tmux skill: Added Quickstart section showing session registry as primary usage
- tmux skill: Moved manual socket management to "Alternative: Manual Socket Management" section
- tmux skill: Added Best Practices and Troubleshooting sections to SKILL.md
- tmux skill: Updated notes/tmux/README.md with session registry documentation (v1.2.0)
- tmux skill: Updated helper tools count from 4 to 7 in documentation
- tmux skill: Updated Related Documentation section with all new tools and library
- tmux skill: Removed create-session.sh and cleanup-sessions.sh from Future Enhancements (now implemented)
- tmux skill: Enhanced test-safe-send.sh with 8 unit tests for session registry features (29 total tests, all passing)
- tmux skill: Enhanced test-wait-for-text.sh with 8 unit tests for session registry features (21 total tests, all passing)
- tmux skill: Enhanced test-pane-health.sh with 8 unit tests for session registry features (26 total tests, all passing)
- tmux skill: Test coverage now includes -s flag validation, auto-detection, and priority resolution (24 new tests)
- tmux skill: Version bumped to 1.2.0

### Fixed
- tmux skill: Fixed bash syntax errors in test cleanup functions (replaced invalid glob pattern redirection with shopt -s nullglob)
- tmux skill: Fixed test logic in cleanup-sessions test for --older-than flag validation

## [0.3.0] - 2025-11-23

### Added
- tmux skill: safe-send.sh tool for reliable command sending with automatic retries and prompt waiting (367 lines, 21/21 tests passing)
- tmux skill: Automatic retry mechanism with exponential backoff (0.5s → 1s → 2s) for transient failures
- tmux skill: Integration with pane-health.sh for pre-flight readiness checks and wait-for-text.sh for prompt synchronization
- tmux skill: Dual-mode operation (normal mode executes commands, literal mode types text without Enter)
- tmux skill: Comprehensive test suite for safe-send.sh covering error handling, retries, modes, and control sequences
- tmux skill: pane-health.sh tool for comprehensive health checking (360 lines, 18/18 tests passing)
- tmux skill: Health checking with 5 exit codes (healthy, dead, missing, zombie, server not running)
- tmux skill: JSON and text output formats for pane-health.sh
- tmux skill: Comprehensive notes/tmux/README.md documentation (52 → 642 lines, 12x expansion)
- tmux skill: Detailed architecture documentation (socket isolation, session management, input/output handling)
- tmux skill: Interactive tool support recipes (Python REPL, gdb debugger, and others)
- tmux skill: Common usage patterns section with 4 real-world examples
- tmux skill: Limitations & gotchas documentation with security considerations

### Fixed
- tmux skill: wait-for-text.sh now supports custom sockets via -S/--socket parameter

### Changed
- git-absorb skill: Implemented progressive disclosure pattern with references/ directory
- git-absorb skill: Added comprehensive reference documentation (advanced-usage.md, configuration.md)
- git-absorb skill: Reduced SKILL.md size by 14% (269 → 232 lines) while improving discoverability
- tmux skill: Enhanced documentation emphasizing PYTHON_BASIC_REPL=1 as critical requirement
- tmux skill: Updated all Python REPL examples to include PYTHON_BASIC_REPL=1
- tmux skill: Enhanced SKILL.md with safe-send.sh and pane-health.sh documentation (+111 lines total)
- tmux skill: Updated "Sending input safely" section to recommend safe-send.sh as primary method
- tmux skill: Enhanced notes/tmux/README.md with safe-send.sh documentation and updated helper tools count to 4
- tmux skill: Updated "Input Handling" section to recommend safe-send.sh for production use
- tmux skill: Removed safe-send.sh from "Future Enhancements" section (now implemented)
- tmux skill: Version bumped to 1.1.0

## [0.2.0] - 2025-11-23

### Added
- Static validation system with comprehensive checks for marketplace integrity
- JSON schemas for validation: plugin-schema.json, marketplace-schema.json, skill-frontmatter-schema.json
- Python validation scripts: validate_yaml.py, validate_json.py, validate_structure.py, validate_all.py
- Makefile with targets for validation, testing, linting, and formatting
- uv-based Python environment management with pyproject.toml
- Automated validation for YAML frontmatter in SKILL.md files
- Automated validation for JSON manifests (plugin.json, marketplace.json)
- File structure and naming convention validation
- git-absorb skill for automatically folding uncommitted changes into appropriate commits
- Comprehensive documentation analysis (ANALYSIS.md) for git-absorb skill comparing against official documentation
- tmux skill for remote controlling tmux sessions for interactive CLIs (python, gdb, etc.) from [mitsuhiko/agent-commands](https://github.com/mitsuhiko/agent-commands/tree/main/skills/tmux)
- tmux skill helper tools: find-sessions.sh and wait-for-text.sh for session management and synchronization
- Version metadata (v1.0.0) for both plugins
- Author information for plugin attribution
- License information (Apache-2.0 for skill-creator, MIT for git-absorb, Vibecoded for tmux)
- Keywords for better plugin discovery and categorization
- Python/uv/testing artifacts to .gitignore

### Changed
- Modernized validation workflow to use `uv run` pattern for all Python scripts
- Removed unnecessary shebang lines from validator scripts (scripts/validators/*.py)
- Cleaned up dependencies: removed yamllint, markdown-it-py, linkchecker, mypy, and types-pyyaml (27% reduction)
- git-absorb skill: Removed automatic installation attempts (now recommends manual installation only)
- git-absorb skill: Added important default behaviors section explaining author filtering and stack size limits
- git-absorb skill: Added configuration section with critical maxStack setting and other useful options
- git-absorb skill: Enhanced troubleshooting with stack limit warning solutions
- tmux skill: Enhanced description with "Use when..." clause and trigger terms for improved skill discovery

## [0.1.0] - 2025-11-22

### Added
- Initial marketplace structure with `.claude-plugin/marketplace.json`
- skill-creator skill from [Anthropic's skills repository](https://github.com/anthropics/skills/tree/main/skill-creator)
- README with instructions for adding marketplace locally
- Marketplace metadata and owner information
- Plugin entry with `skills` field for proper skill loading

[Unreleased]: https://github.com/dashed/claude-marketplace/compare/v0.31.0...HEAD
[0.31.0]: https://github.com/dashed/claude-marketplace/compare/v0.30.0...v0.31.0
[0.30.0]: https://github.com/dashed/claude-marketplace/compare/v0.29.1...v0.30.0
[0.29.1]: https://github.com/dashed/claude-marketplace/compare/v0.29.0...v0.29.1
[0.29.0]: https://github.com/dashed/claude-marketplace/compare/v0.28.0...v0.29.0
[0.28.0]: https://github.com/dashed/claude-marketplace/compare/v0.27.0...v0.28.0
[0.27.0]: https://github.com/dashed/claude-marketplace/compare/v0.26.0...v0.27.0
[0.26.0]: https://github.com/dashed/claude-marketplace/compare/v0.25.1...v0.26.0
[0.25.1]: https://github.com/dashed/claude-marketplace/compare/v0.25.0...v0.25.1
[0.25.0]: https://github.com/dashed/claude-marketplace/compare/v0.24.1...v0.25.0
[0.24.1]: https://github.com/dashed/claude-marketplace/compare/v0.24.0...v0.24.1
[0.24.0]: https://github.com/dashed/claude-marketplace/compare/v0.23.0...v0.24.0
[0.23.0]: https://github.com/dashed/claude-marketplace/compare/v0.22.0...v0.23.0
[0.22.0]: https://github.com/dashed/claude-marketplace/compare/v0.21.0...v0.22.0
[0.21.0]: https://github.com/dashed/claude-marketplace/compare/v0.20.1...v0.21.0
[0.20.1]: https://github.com/dashed/claude-marketplace/compare/v0.20.0...v0.20.1
[0.20.0]: https://github.com/dashed/claude-marketplace/compare/v0.19.0...v0.20.0
[0.19.0]: https://github.com/dashed/claude-marketplace/compare/v0.18.0...v0.19.0
[0.18.0]: https://github.com/dashed/claude-marketplace/compare/v0.17.0...v0.18.0
[0.17.0]: https://github.com/dashed/claude-marketplace/compare/v0.16.0...v0.17.0
[0.16.0]: https://github.com/dashed/claude-marketplace/compare/v0.15.2...v0.16.0
[0.15.2]: https://github.com/dashed/claude-marketplace/compare/v0.15.1...v0.15.2
[0.15.1]: https://github.com/dashed/claude-marketplace/compare/v0.15.0...v0.15.1
[0.15.0]: https://github.com/dashed/claude-marketplace/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/dashed/claude-marketplace/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/dashed/claude-marketplace/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/dashed/claude-marketplace/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/dashed/claude-marketplace/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/dashed/claude-marketplace/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/dashed/claude-marketplace/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/dashed/claude-marketplace/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/dashed/claude-marketplace/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/dashed/claude-marketplace/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/dashed/claude-marketplace/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/dashed/claude-marketplace/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/dashed/claude-marketplace/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/dashed/claude-marketplace/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/dashed/claude-marketplace/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/dashed/claude-marketplace/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/dashed/claude-marketplace/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/dashed/claude-marketplace/releases/tag/v0.1.0
