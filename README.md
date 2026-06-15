# Alberto's Claude Marketplace

> A local marketplace for personal Claude Code skills and Codex repo-local skills.

A curated collection of Agent Skills for extending Claude Code and Codex capabilities. This marketplace is configured for local use and makes it easy to install and manage custom skills.

> [!WARNING]
> **This is Alberto Leal's personal Claude Code plugin marketplace.** It is built solely for my own workflow, and I am the only intended and supported user. The skills and MCP servers here encode my personal conventions and assumptions, and may change, break, or disappear at any time without notice or migration path.
>
> You are welcome to read, fork, or borrow from it — but if you are not me, **use it entirely at your own risk.** There are no support, stability, or backward-compatibility guarantees for anyone else.

## Claude Code Quick Start

```bash
# 1. Add the marketplace
/plugin marketplace add /path/to/claude-marketplace

# 2. Install skills
/plugin  # Browse and install plugins → alberto-marketplace

# 3. Restart Claude Code to load new skills
/exit
```

## Codex Quick Start

Codex can read this repo as a local plugin marketplace. Generate Codex-native plugin manifests and the Codex marketplace file from the Claude marketplace metadata:

```bash
./scripts/sync_codex_plugins.py
# or
make sync-codex-plugins
```

Then restart Codex or start a new Codex thread from this repo root. Re-run the sync after editing `.claude-plugin/marketplace.json`, plugin skills, or MCP configs:

```bash
./scripts/sync_codex_plugins.py --check
# or
make check-codex-plugins
```

The sync writes `.agents/plugins/marketplace.json`, each plugin's `.codex-plugin/plugin.json`, and Codex-specific MCP configs when needed. Generated plugin versions include a content hash so Codex can see a new installable version after plugin files change.

The older direct skill symlink flow is still available when you want repo-local `.agents/skills` entries instead of installing plugins:

```bash
./scripts/install_codex_skills.py
```

For day-to-day toggling, use the interactive manager:

```bash
./scripts/manage_codex_skills.py
# or
make manage-codex-skills
```

Useful options:

```bash
# Preview changes without creating links
./scripts/install_codex_skills.py --dry-run

# Replace existing symlinks that point somewhere else
./scripts/install_codex_skills.py --force

# Install links into a personal Codex skills directory
./scripts/install_codex_skills.py --dest "$HOME/.agents/skills"

# List current Codex skill state
./scripts/manage_codex_skills.py --list

# Enable, disable, or uninstall individual skills
./scripts/manage_codex_skills.py --enable tmux
./scripts/manage_codex_skills.py --disable tmux
./scripts/manage_codex_skills.py --uninstall tmux
```

By default, the scripts manage `.agents/skills/<skill>` symlinks back to `plugins/<skill>`. `disable` removes only a managed repo symlink, and `uninstall` removes symlinked entries from the Codex skills directory. Real files and directories are reported as conflicts instead of being deleted.

To check and test the Codex scripts:

```bash
make test-codex-skills
```

## Available Skills

| Skill | Description | Source |
|-------|-------------|--------|
| **ai-friendly-cli** | Build and refactor CLIs for AI agent compatibility. Use when making CLI tools machine-readable with structured JSON output, input hardening, schema introspection, dry-run safety, and MCP surfaces. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/ai-friendly-cli) |
| **skill-creator** | Create new skills, modify and improve existing skills, and measure skill performance. Use when creating, updating, evaluating, or optimizing skills. | [Anthropic](https://github.com/anthropics/skills/tree/main/skill-creator) |
| **skill-reviewer** | Review and ensure skills maintain high quality standards. Use when creating new skills, updating existing skills, or auditing skill quality. Checks for progressive disclosure, mental model shift, appropriate scope, and documentation clarity. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/skill-reviewer) |
| **git-absorb** | Automatically fold uncommitted changes into appropriate commits. Use for applying review feedback and maintaining atomic commit history. Tool: [git-absorb](https://github.com/tummychow/git-absorb) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/git-absorb) |
| **tmux** | Remote control tmux sessions for interactive CLIs (python, gdb, etc.) by sending keystrokes and scraping pane output. Use when debugging applications, running interactive REPLs (Python, gdb, ipdb, psql, mysql, node), or automating terminal workflows. Works with stock tmux on Linux/macOS. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/tmux) |
| **ultrathink** | Invoke deep sequential thinking for complex problem-solving. Use when tackling problems that require careful step-by-step reasoning, planning, hypothesis generation, or multi-step analysis. Trigger with "use ultrathink". | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/ultrathink) |
| **conventional-commits** | Format git commit messages following the Conventional Commits 1.0.0 specification. Use when creating git commits for consistent, semantic commit messages that support automated changelog generation and semantic versioning. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/conventional-commits) |
| **git-chain** | Manage and rebase chains of dependent Git branches (stacked branches). Use when working with multiple dependent PRs, feature branches that build on each other, or maintaining clean branch hierarchies. Automates rebasing or merging entire branch chains. Tool: [git-chain](https://github.com/dashed/git-chain) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/git-chain) |
| **jj** | Jujutsu (jj) version control system - a Git-compatible VCS with automatic rebasing, first-class conflicts, and operation log. Use when working with jj repositories, stacked commits, revsets, or enhanced Git workflows. Tool: [jj](https://github.com/jj-vcs/jj) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/jj) |
| **fzf** | Command-line fuzzy finder for interactive filtering. Use when searching files, command history (CTRL-R), creating interactive menus, or integrating with ripgrep, fd, and git. Shell keybindings: CTRL-T, CTRL-R, ALT-C, `**` completion. Tool: [fzf](https://github.com/junegunn/fzf) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/fzf) |
| **playwright** | Browser automation with Playwright for Python. Use when testing websites, taking screenshots, filling forms, scraping web content, or automating browser interactions. Uses uv with PEP 723 inline scripts for self-contained automation. **Requires one-time browser setup** (see below). Tool: [Playwright](https://playwright.dev/python/) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/playwright) |
| **zellij** | Terminal workspace and multiplexer for interactive CLI sessions. Use when managing terminal sessions, running interactive REPLs, debugging, or automating terminal workflows. Simpler alternative to tmux with native session management. Tool: [Zellij](https://zellij.dev/) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/zellij) |
| **design-principles** | Guide AI-assisted UI generation toward enterprise-grade, intentional design. Use when building UIs, creating dashboards, designing SaaS applications, or generating styled frontend code. Enforces 4px grids, typography hierarchies, and consistent depth strategies. | [Dammyjay93](https://github.com/dashed/claude-marketplace/tree/master/plugins/design-principles) |
| **mermaid-cli** | Generate, validate, and fix diagrams from Mermaid markup using mmdc. Use when creating flowcharts, sequence diagrams, class diagrams, or converting .mmd files to images/SVG/PDF. Also validates and fixes Mermaid syntax. Tool: [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/mermaid-cli) |
| **walkthrough-to-obsidian** | Convert game walkthroughs and guides from plain text into structured, interlinked Obsidian markdown pages. Use when converting walkthroughs, FAQs, or reference documents into Obsidian vault pages. Supports agent team parallelization for large documents. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/walkthrough-to-obsidian) |
| **long-form-math** | Write mathematics in a long-form, understanding-focused style with detailed proofs and rich exposition. Three-phase proof workflow, motivation-first exposition, and rigorous writing conventions. Inspired by Cummings' Real Analysis and Chartrand's Mathematical Proofs. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/long-form-math) |
| **chrome-cdp** | Interact with live Chrome browser sessions via Chrome DevTools Protocol. Use when inspecting, debugging, or interacting with pages open in Chrome — screenshots, accessibility trees, JS evaluation, clicking, navigating. Persistent per-tab daemon, works with 100+ tabs. Based on [pasky/chrome-cdp-skill](https://github.com/pasky/chrome-cdp-skill). **Requires Chrome remote debugging** (see below). | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/chrome-cdp) |
| **react-best-practices** | React and Next.js performance optimization guidelines from Vercel Engineering. 62 rules across 8 categories covering waterfalls, bundle size, server-side, re-renders, and rendering. Use when writing, reviewing, or refactoring React/Next.js code. Source: [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | [Vercel Engineering](https://github.com/dashed/claude-marketplace/tree/master/plugins/react-best-practices) |
| **linear** | Managing Linear issues, projects, and teams. Use when working with Linear tasks, creating issues, updating status, querying projects, or managing team workflows. Tool: [Linear SDK](https://github.com/linear/linear) + MCP | [wrsmith108](https://github.com/wrsmith108/linear-claude-skill) |
| **gogcli** | Drive Google Workspace from the terminal: Gmail, Calendar, Drive, Docs, Sheets, Slides, Chat, Tasks, Contacts, Admin, Keep, Forms, Classroom, Groups, Apps Script. JSON-first, multi-account, script-friendly. Use when sending mail, managing events, moving files, editing spreadsheets, or automating Workspace tasks. Tool: [gogcli](https://github.com/steipete/gogcli) | [steipete](https://github.com/dashed/claude-marketplace/tree/master/plugins/gogcli) |
| **pup** | Datadog CLI (pup) for observability, monitoring, logs, APM, security, and infrastructure. Use when querying Datadog metrics, searching logs, managing monitors, investigating incidents, or performing Datadog API operations. 49 command groups, 300+ subcommands. Tool: [pup](https://github.com/datadog-labs/pup) | [Datadog](https://github.com/dashed/claude-marketplace/tree/master/plugins/pup) |
| **style-extractor** | Extract and document writing styles from source texts into reusable style guides. Four-phase workflow analyzing 17 style dimensions, producing a full style guide, voice card, do/don't checklist, and scoring rubric. Works with PDFs, documents, and any readable text. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/style-extractor) |
| **style-writer** | Write content using stored writing styles from the writing-styles/ collection. Discovers available styles, loads the right guide into context, applies it during writing, and self-evaluates against the style rubric. Companion to style-extractor. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/style-writer) |
| **anki-flashcards** | Create and manage Anki flashcards via the AnkiConnect API. Use when creating flashcards, managing decks, reviewing statistics, or interacting with Anki. Comprehensive API reference covering 100+ actions, flashcard design best practices. Requires Anki with AnkiConnect add-on. Tool: [AnkiConnect](https://github.com/FooSoft/anki-connect) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/anki-flashcards) |
| **statusline** | Configure the Claude Code status line with VCS-aware scripts showing git branch, jj change ID, bookmarks, context usage, and costs. Use when setting up a statusline, customizing the status bar, or adding VCS info to the status line. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/statusline) |
| **hledger** | Plain-text double-entry accounting with hledger. Use when recording transactions, checking balances, generating financial reports, importing CSV bank statements, budgeting, tracking time, managing multiple currencies, or doing year-end closing. Tool: [hledger](https://hledger.org) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/hledger) |
| **git** | Advanced Git CLI mastery, recovery, and troubleshooting (git 2.54+). Use when recovering lost commits/branches/stashes (reflog, fsck), undoing a bad reset/merge/rebase, rewriting history (interactive rebase, filter-repo), resolving conflicts (rerere), or working with worktrees, bisect, cherry-pick, stash, refspecs, `--force-with-lease`, `.gitattributes`/hooks, git internals, or confusing git errors. Defers to conventional-commits, git-chain, git-absorb, and jj for their niches. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/git) |
| **sequential-thinking** | MCP server exposing a single `sequentialthinking` tool for dynamic, reflective, step-by-step problem-solving. Use when a task needs structured reasoning, planning, hypothesis generation, branching to explore alternatives, or revising earlier steps while keeping a running chain of thoughts. The marketplace's first MCP-server plugin. **Requires [uv](https://docs.astral.sh/uv/).** | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/sequential-thinking) |
| **file-search** | MCP server exposing `search_files` (fd regex/glob) and `filter_files` (fzf fuzzy matching) tools for fast file-NAME discovery. Use when locating files by name or partial path — not for searching file contents. **Requires [uv](https://docs.astral.sh/uv/), [fd](https://github.com/sharkdp/fd), and [fzf](https://github.com/junegunn/fzf).** | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/file-search) |
| **fuzzy-search** | MCP server exposing fuzzy content/file/document search tools (`fuzzy_search_files`, `fuzzy_search_content`, `fuzzy_search_documents`) built on ripgrep + fzf, plus PyMuPDF-backed PDF tools (`extract_pdf_pages`, `get_pdf_outline`, `get_pdf_page_count`, `get_pdf_page_labels`). Use when fuzzy-searching code/files/documents or inspecting/extracting PDF pages. **Requires [uv](https://docs.astral.sh/uv/); `rg`+`fzf` (and `rga` for documents).** | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/fuzzy-search) |
| **sqlite** | MCP server exposing SQLite database tools (`query`, `execute`, `list_tables`, `describe_table`, `create_table`). Read-only by default; writes are opt-in via `--allow-writes` or `MCP_SQLITE_ALLOW_WRITES=true`. Use when inspecting, querying, or (when enabled) modifying SQLite databases. **Requires [uv](https://docs.astral.sh/uv/).** | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/sqlite) |
| **fd** | Fast, user-friendly command-line file/directory search with the `fd` tool (a simpler, faster `find` replacement). Use when searching for files/directories by name or regex/glob, filtering by type/extension/size/modified-time, respecting `.gitignore`, or running a command per result with `-x`/`-X`. Includes `(fd X.Y+)` version annotations + a version-features lookup. Tool: [fd](https://github.com/sharkdp/fd) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/fd) |
| **ripgrep** | Fast, gitignore-aware recursive content search with the `ripgrep` (`rg`) tool — a smarter, faster `grep`. Use when searching code/text for a regex across a tree, filtering by file type/glob, listing/counting matches, search-and-replace previews, or gitignore-aware code search. Includes `(rg X.Y+)` version annotations + a version-features lookup. Tool: [ripgrep](https://github.com/BurntSushi/ripgrep) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/ripgrep) |
| **fuzzy-filter** | The non-interactive `rg`/`fd`/`rga` → `fzf --filter` pipeline — scan with a regex tool, then fuzzy-rank lines with no TUI (the CLI technique behind the fuzzy-search MCP). Use when fuzzy-matching paths, code lines, or PDF/document text from a script, or piping ranked results to xargs/an editor. Distinct from the **fzf** skill (interactive) and the **fuzzy-search** MCP (tool calls). Tools: [ripgrep](https://github.com/BurntSushi/ripgrep) + [fzf](https://github.com/junegunn/fzf) (+ [rga](https://github.com/phiresky/ripgrep-all) for documents). | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/fuzzy-filter) |
| **k3s** | The `k3s` lightweight CNCF-certified Kubernetes distribution as a single binary (bundles containerd, flannel, CoreDNS, Traefik, ServiceLB, local-path-provisioner, metrics-server). Use when installing/running a lightweight cluster, bootstrapping single-node or HA control planes, joining agent nodes, choosing embedded etcd vs an external datastore, managing tokens, rotating certs, taking/restoring etcd snapshots, secrets encryption, airgap/private-registry installs, disabling bundled components, or upgrading. Includes `(k3s vX.Y+)` version annotations + a version-features lookup. Tool: [k3s](https://github.com/k3s-io/k3s) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/k3s) |
| **teach** | Run a Socratic teaching loop that quizzes you on a coding session until you've confirmed mastery of every concept. Use when you want to learn or lock in a Claude Code session, understand a transcript/PR/design decision, be quizzed on recent work, or prepare to teach someone else — or when the user runs `/teach` or asks to be taught or quizzed on a topic. Sources sessions from `~/.claude/projects/` and tracks a per-concept checklist until every item is confirmed. | [alexknowshtml](https://github.com/alexknowshtml/claude-skills/tree/main/teach) |
| **ansible** | ansible-core — the agentless, push-based SSH automation engine that runs idempotent tasks from declarative YAML playbooks. Use when writing/running playbooks, issuing ad-hoc commands, managing inventory, authoring roles, installing collections with ansible-galaxy, encrypting secrets with Ansible Vault, tuning ansible.cfg, or looking up docs with ansible-doc. Covers the ten `ansible*` CLIs, FQCN, become, variable precedence, and check/diff mode. Includes `(ansible-core X.Y+)` version annotations + a version-features lookup. Tool: [ansible-core](https://github.com/ansible/ansible) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/ansible) |
| **obsidian-markdown** | Create and edit Obsidian Flavored Markdown — the Obsidian-specific extensions on top of CommonMark/GFM: wikilinks (`[[Note]]`), block IDs, embeds (`![[...]]`), callouts (`> [!type]`), frontmatter properties, tags, comments, highlights, LaTeX math, Mermaid, and footnotes. Use when working with `.md` files in an Obsidian vault, or when the user mentions wikilinks, callouts, frontmatter, tags, embeds, or Obsidian notes. Ported from kepano's obsidian-skills (with minor local accuracy fixes). |
| **obsidian-bases** | Create and edit Obsidian Bases (`.base` files) — the YAML format that turns notes into database-like table/cards/list/map views with filters, computed formulas, and summary aggregations. Use when working with `.base` files, building database-like views of notes, or when the user mentions Bases, table/card views, filters, or formulas in Obsidian. Ported from kepano's obsidian-skills (with minor local additions from the official docs); includes a complete per-type functions reference. | [kepano](https://github.com/kepano/obsidian-skills/tree/main/skills/obsidian-bases) |
| **duckdb** | DuckDB — the in-process, columnar OLAP SQL engine in a single zero-dependency binary ("SQLite for analytics"). Use when querying Parquet/CSV/JSON files directly with SQL, using the `duckdb` CLI shell (REPL or `-c`/`-json` one-shots for scripts/agents), writing friendly SQL (FROM-first, `SELECT * EXCLUDE`, `GROUP BY ALL`, `SUMMARIZE`, `PIVOT`), converting CSV↔Parquet↔JSON via `COPY`, reading HTTP/S3 data via httpfs, or `ATTACH`-ing a live Postgres/MySQL/SQLite database. Includes `(duckdb vX.Y+)` version annotations + a version-features lookup. Tool: [duckdb](https://github.com/duckdb/duckdb) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/duckdb) |
| **jq** | jq — the command-line JSON processor and its filter language for filtering, transforming, and reshaping JSON. Use when extracting fields/nested paths on the CLI, `select`-ing arrays of objects, building new JSON, emitting CSV/TSV with `@csv`/`@tsv`, getting raw strings with `jq -r`, slurping (`-s`) and aggregating (`add`, `group_by`), NDJSON pipelines (`-c`), or injecting shell values with `--arg`/`--argjson`. Includes `(jq 1.X+)` version annotations + a version-features lookup. Tool: [jq](https://github.com/jqlang/jq) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/jq) | [kepano](https://github.com/kepano/obsidian-skills/tree/main/skills/obsidian-markdown) |
| **psql** | psql — PostgreSQL's interactive terminal client and SQL script runner. Use when connecting to or inspecting a Postgres database from a terminal, running SQL scripts or one-off queries in shells/CI/agents (`-c`/`-f`/`-qAtX`/`--csv`), using meta-commands (`\d` family, `\copy`, `\watch`, `\gexec`, `\if` scripting, `\pset`/`\x`, variables), `.psqlrc`, or fixing connection/auth problems. Includes `(pgNN+)` version annotations + a version-features lookup. Tool: [PostgreSQL](https://github.com/postgres/postgres) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/psql) |
| **postgres-sql** | The PostgreSQL SQL dialect & data types that set Postgres apart from generic SQL. Use when writing or debugging Postgres-specific SQL — upsert (`ON CONFLICT`), `RETURNING` (incl. `OLD`/`NEW`), `MERGE`, CTEs, window frames, `GROUPING SETS`, `LATERAL`, generated/identity columns, declarative partitioning, `jsonb`/jsonpath/SQL-JSON (`JSON_TABLE`/`IS JSON`), arrays, ranges & multiranges, composite/enum/domain types, `uuidv7()`/`gen_random_uuid()`. Includes `(pgNN+)` version annotations + a version-features lookup. Tool: [PostgreSQL](https://github.com/postgres/postgres) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/postgres-sql) |
| **postgres-performance** | PostgreSQL query & performance tuning — reading `EXPLAIN`/`EXPLAIN ANALYZE` plans, choosing & designing indexes, fixing planner row-estimate errors with statistics, and diagnosing MVCC bloat/VACUUM. Use when a query is slow, choosing an index type (btree/GIN/GiST/SP-GiST/BRIN/hash) or strategy (partial/expression/covering), autovacuum lags, or tuning planner GUCs (`random_page_cost`, `work_mem`, `effective_cache_size`). Includes `(pgNN+)` version annotations + a version-features lookup. Tool: [PostgreSQL](https://github.com/postgres/postgres) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/postgres-performance) |
| **postgres-admin** | PostgreSQL server administration & operations (DBA work on a running cluster). Use when configuring a server (`postgresql.conf`, `ALTER SYSTEM`, GUCs), managing roles/privileges, authentication (`pg_hba.conf`, scram-sha-256), backup/restore (`pg_dump`, `pg_basebackup`, incremental, PITR), replication & HA (streaming, logical pub/sub, slots, failover), `pg_upgrade`, or monitoring (`pg_stat_activity`, `pg_stat_io`, `pg_stat_progress_*`). Includes `(pgNN+)` version annotations + a version-features lookup. Tool: [PostgreSQL](https://github.com/postgres/postgres) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/postgres-admin) |
| **postgres-extensions** | PostgreSQL extension management and the bundled `contrib` catalog. Use when running `CREATE EXTENSION`/`ALTER EXTENSION ... UPDATE`/`DROP EXTENSION`, listing extensions (`\dx`), or choosing which contrib module enables a feature — FDWs (`postgres_fdw`, `dblink`), trigram/fuzzy search (`pg_trgm`, `fuzzystrmatch`), crypto/UUIDs (`pgcrypto`), `hstore`/`ltree`/`citext`/`cube`, query stats (`pg_stat_statements`, `auto_explain`), storage forensics (`pageinspect`, `amcheck`, `pg_surgery`). Covers trusted extensions & `shared_preload_libraries`. Includes `(pgNN+)` version annotations + a version-features lookup. Tool: [PostgreSQL](https://github.com/postgres/postgres) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/postgres-extensions) |
| **kubernetes** | Author and operate Kubernetes workloads with kubectl and YAML manifests — the kubectl CLI plus core resource authoring (Deployments, StatefulSets, Jobs/CronJobs, Services, Ingress, ConfigMaps/Secrets, PV/PVC, RBAC). Use when writing/debugging manifests, running kubectl (apply/diff/rollout/logs/exec/debug), fixing CrashLoopBackOff/Pending pods, managing contexts/namespaces, generating manifests with `--dry-run=client`, or checking RBAC with `auth can-i`. Includes `(k8s 1.X+)` version annotations + a version-features lookup. For installing/running a lightweight cluster see the **k3s** skill. Tool: [kubernetes](https://github.com/kubernetes/kubernetes) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/kubernetes) |
| **uv** | uv — Astral's fast Python package & project manager, one binary replacing pip/pipx/pyenv/poetry/virtualenv. Use when managing Python projects with `pyproject.toml` + `uv.lock` (`uv init/add/sync/lock/run`), running PEP 723 inline-dependency scripts, running one-off tools with `uvx`, installing/pinning Python versions (`uv python`), migrating from pip (`uv pip`), building/publishing packages, or configuring indexes/resolution/cache. Includes `(uv 0.X+)` version annotations + a version-features lookup. Tool: [uv](https://github.com/astral-sh/uv) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/uv) |
| **handoff** | Compact the current conversation into a handoff document for another agent to pick up. Use when ending a session with unfinished work, transferring context to a fresh agent or a new session, or approaching context limits. Saves timestamped docs to the OS temp dir, the workspace root with `--workspace` (auto-ignored via `.git/info/exclude`), or git-visible with `--tracked` (staged, commit+push offered for cross-machine transfer); follows a section template (decisions & rationale, dead ends tried, verify-state commands), suggests skills for the next agent, references artifacts instead of duplicating them, redacts secrets, and announces the path with a next-session starter. | [mattpocock](https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff) |
| **pytest** | pytest — the Python testing framework and the idioms that set it apart from unittest. Use when writing, running, debugging, or configuring pytest tests — plain `assert` (rewritten for rich introspection), dependency-injected `@pytest.fixture` (scopes/autouse/yield/conftest), `@pytest.mark.parametrize`, `skip`/`skipif`/`xfail` + custom markers, `pytest.raises`/`warns`/`approx`, builtin fixtures (`tmp_path`/`monkeypatch`/`capsys`/`caplog`), the CLI (`-k`/`-m`/`-x`/`--lf`/`--pdb`/node ids), config (`pyproject.toml`/`pytest.ini`, `addopts`, `testpaths`, `--import-mode`), and plugins/hooks (`conftest.py`, xdist/cov/asyncio/mock). Includes `(pytest N.M+)` version annotations + a version-features lookup. Tool: [pytest](https://github.com/pytest-dev/pytest) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/pytest) |

### Chrome CDP Setup

The chrome-cdp skill requires Chrome with remote debugging enabled and Python 3.10+ with the `websockets` library:

```bash
# 1. Enable remote debugging in Chrome
#    Navigate to chrome://inspect/#remote-debugging and toggle the switch

# 2. Install the websockets dependency
uv pip install websockets
```

### Linear Setup

The linear skill requires Node.js dependencies and a Linear API key:

```bash
# 1. Install dependencies in the plugin cache directory
cd ~/.claude/plugins/cache/alberto-marketplace/linear/2.3.1
npm install

# 2. Create a Linear API key at https://linear.app/settings/api
# 3. Add to your shell profile (~/.zshrc or ~/.bashrc)
export LINEAR_API_KEY="lin_api_..."
```

Restart Claude Code after setup.

### Playwright Setup

The playwright skill requires a one-time browser installation (~200MB). Claude will suggest these commands but will not run them directly—run them manually:

```bash
# Install Chromium (recommended, ~200MB)
uv run --with playwright playwright install chromium

# Or install all browsers
uv run --with playwright playwright install
```

## Usage

### Add this marketplace locally

```bash
/plugin marketplace add /path/to/claude-marketplace
```

### Update the marketplace

```bash
/plugin marketplace update alberto-marketplace
```

### Install skills

1. Select `/plugin` and then `Browse and install plugins`
2. Select `alberto-marketplace`
3. Choose the skills to install
4. Restart Claude Code

### Install skills for Codex

```bash
./scripts/sync_codex_plugins.py
```

Codex can then discover the local plugin marketplace from `.agents/plugins/marketplace.json` when launched from this repository or one of its subdirectories.

For legacy direct skill links:

```bash
./scripts/install_codex_skills.py
```

To enable, disable, or uninstall skills interactively:

```bash
./scripts/manage_codex_skills.py
# or
make manage-codex-skills
```

## Adding Skills to This Marketplace

### Method 1: Add to Marketplace (Recommended)

1. Add your skill directory to `plugins/`
2. Edit `.claude-plugin/marketplace.json` and add a new entry:

```json
{
  "name": "your-skill-name",
  "source": "./plugins/your-skill-name",
  "description": "Brief description of what the skill does",
  "strict": false,
  "skills": ["./skills"]
}
```

**Important:** The `skills` field is required to load skills from the marketplace. It tells Claude Code which directories contain SKILL.md files.

3. Update the CHANGELOG.md
4. Commit your changes
5. Re-run `./scripts/sync_codex_plugins.py` if you use Codex with this repo.

### Method 2: Direct Installation

Skills can also be installed directly without using the Claude Code marketplace:

```bash
# Claude Code personal (available everywhere)
cp -r plugins/your-skill ~/.claude/skills/

# Claude Code project (shared with team)
cp -r plugins/your-skill .claude/skills/

# Codex repo-local links
./scripts/install_codex_skills.py

# Codex plugin marketplace metadata
./scripts/sync_codex_plugins.py

# Codex personal links
./scripts/install_codex_skills.py --dest "$HOME/.agents/skills"

# Codex interactive manager
./scripts/manage_codex_skills.py
```

## Structure

```
claude-marketplace/
├── .agents/
│   ├── plugins/
│   │   └── marketplace.json  # Generated Codex plugin marketplace
│   └── skills/               # Optional generated Codex symlinks
├── .claude-plugin/
│   └── marketplace.json      # Marketplace manifest
├── plugins/
│   └── skill-creator/        # Plugin directory
│       ├── .codex-plugin/
│       │   └── plugin.json   # Generated Codex plugin manifest
│       └── skills/
│           └── skill-creator/
│               ├── SKILL.md      # Skill definition
│               ├── scripts/      # Optional scripts
│               └── references/   # Optional documentation
├── scripts/
│   ├── install_codex_skills.py # Codex symlink installer
│   ├── manage_codex_skills.py  # Codex interactive manager
│   └── sync_codex_plugins.py   # Codex plugin metadata sync
├── CHANGELOG.md              # Version history
└── README.md                 # This file
```

## Resources

- [Claude Code Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills)
- [Plugin Marketplaces Guide](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- [OpenAI Codex Skills Documentation](https://developers.openai.com/codex/skills)
- [OpenAI Codex Plugins Documentation](https://developers.openai.com/codex/plugins)
- [OpenAI Skills Catalog](https://github.com/openai/skills)

## Version

Current version: **0.37.0**

See [CHANGELOG.md](CHANGELOG.md) for version history.
