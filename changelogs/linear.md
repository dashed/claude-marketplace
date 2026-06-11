# Changelog - linear

All notable changes to the linear skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [2.4.1] - 2026-06-11

### Fixed
- `project-status` could land on a surprising status in workspaces that define several statuses of the same category type. Found by live end-to-end testing against a real workspace: it has two "To Do" statuses, one of them `started`-type at position 0, so `project-status X in-progress` resolved to "To Do" instead of "In Progress". `findProjectStatusByType` now accepts a preferred-name hint — a same-type status whose normalized name matches the user's input wins (e.g. `in-progress` → "In Progress"), falling back to lowest `position` as before

### Verified (live end-to-end, with cleanup)
- Exercised every refactored mutation path against a real workspace using clearly-marked, immediately-trashed test artifacts: `create-project`, `project-status` (statusId path, both before and after the fix), `create-issue` (team correctly resolved from the project, not the workspace-first team), `create-sub-issue`, `status`, `sync.ts` (`--dry-run` provably mutation-free; real run batched via one `updateIssueBatch` call + per-issue comments), `create-project-update` (typed payload), and `phase-complete --dry-run` (full pagination + the single-query state resolution). All test issues and the test project were trashed and verified gone

## [2.4.0] - 2026-06-11

SDK-first overhaul, authored by an agent team and verified against the official `linear/linear` monorepo (`packages/sdk` source, schema, and SDK 86 typings) plus live read-only API checks. All gates pass: `tsc --noEmit`, eslint, prettier, 66/66 vitest, `setup.ts`, marketplace `validate-strict`.

### Changed
- Rewrote `sdk.md` (285 → ~490 lines) as a verified `@linear/sdk` 86 reference: the lazy-relation trap (async relation getters vs synchronous `<rel>Id` getters and its N+1 cost), a filtering cookbook (full comparator catalog, `and`/`or`, nested relation + collection filters, relative date durations like `-P2W1D`), pagination (`client.paginate`, `fetchNext`, the silent 50-item default), mutations (verb-first naming, payload shape, `labelIds`, required `teamId`, `updateIssueBatch`, project status via `statusId`), typed error handling (`LinearError` hierarchy, rate-limit headers/fields, retry helper — the SDK has no built-in retry), the `client.client.rawRequest` escape hatch, the 3-step file-upload + attachment flow, and webhooks (`@linear/sdk/webhooks`, `LinearWebhookClient`). Every snippet typechecks against the installed SDK; claims were adversarially re-verified against the monorepo source (3 discrepancies caught and fixed, e.g. collection filters have no `none` operator)
- Repositioned tool routing across `SKILL.md`, `api.md`, `troubleshooting.md`: MCP tools are the interactive default, SDK scripts the programmatic default, raw GraphQL a rare escape hatch reached through the SDK — it was previously presented as a peer toolchain ("GraphQL for searches and complex queries")
- Refactored all bundled scripts onto typed SDK calls, eliminating every unnecessary raw path (16 `rawRequest` calls and 5 hand-rolled `fetch`es; the only raw API use left is `query.ts`'s generic executor and the S3 upload PUT): `createEntityExternalLink`, `createProjectUpdate`, `createInitiativeUpdate`, `createInitiativeToProject`, `updateProject`, typed team/initiative/state/label lookups; removed all `(client as any)` casts. Three "SDK doesn't expose X" comments were false — all three operations are typed in SDK 86
- `sync.ts` now batches state changes through one `updateIssueBatch` call per target state (was: sequential per-issue updates with 150 ms sleeps) and resolves the team per identifier instead of once for the whole batch
- New `scripts/lib/errors.ts` (`formatLinearError`, `isRetryableLinearError`) surfaces the Linear error type, message, HTTP status, and rate-limit `retryAfter` in all refactored scripts' error paths
- New `scripts/lib/project-status.ts` resolves workspace project statuses by category type, deterministically (lowest `position`) when several share a type
- `setup.ts` now prints the official MCP config (`claude mcp add --transport http --scope user linear-server https://mcp.linear.app/mcp`, OAuth), detects the `linear-server` server name, and advertises a real quick command
- `sync.md` rewritten to match the real `sync.ts` CLI: `npx tsx` (was `npx ts-node` ×14 — ts-node is not a dependency), only the flags that exist (`--issues`, `--state`, `--comment`, `--dry-run`); removed 8 fictional flags and the swarm section that depended on them

### Fixed
- `create-issue` resolved the team as the workspace's first team — wrong team in multi-team workspaces; it now derives the team from the target project, and the project lookup paginates past 50 projects
- `project-status` wrote the deprecated `Project.state` string (and `phase-complete.ts` used a different mechanism); both now use the modern `updateProject(id, { statusId })` path via the shared helper, and the success message reports the real workspace status name
- Silent 50-item pagination truncation: `phase-complete.ts` issue counting (now fully paginated, with distinct states resolved in a single `workflowStates` query instead of an unbounded per-issue fan-out), `verify.ts` initiative verification, `lib/initiative.ts` project listing
- `sdk.md`'s example code was broken: synchronous access to the lazy `issue.state.type` relation, `labels: [...]` instead of `labelIds`, and a nonexistent `issue.addComment` method
- All references to the nonexistent `scripts/linear-helpers.mjs` (SKILL.md, troubleshooting.md, projects.md, setup.ts) replaced with real equivalents (`linear-ops.ts status`, MCP `save_comment`, `sync.ts --comment`, `client.createComment`)
- `api.md`'s project-lookup example selected the deprecated `state` field (now `status { id name }`), and its rate-limit stub now documents the two-budget model with the exact `x-ratelimit-*`/`retry-after` header names

## [2.3.2] - 2026-06-11

### Changed
- Bump `@linear/sdk` from ^68.1.0 to ^86.0.0 (matches the latest release in the official `linear/linear` monorepo). Verified on 86.0.0: `tsc --noEmit` clean, all 66 unit tests pass, `scripts/setup.ts` reports a valid setup, and a live read-only GraphQL query through the SDK succeeds. The only breaking schema removals between 76 and 86 (`TeamCreateInput.issueSharingPolicy`, `IssueToRelease.pullRequest`) are not used by the bundled scripts

### Fixed
- Replaced the deprecated MCP connection config (`npx mcp-remote https://mcp.linear.app/sse` with a `LINEAR_API_KEY` env var) in `SKILL.md` and `troubleshooting.md` with the current native HTTP transport: `claude mcp add --transport http linear-server https://mcp.linear.app/mcp`, authenticated via OAuth. The old `/sse` config now fails OAuth with "Protected resource https://mcp.linear.app/mcp does not match expected https://mcp.linear.app/sse" because Linear's protected-resource metadata advertises `/mcp` for every endpoint (verified live); the error and its fix are now documented in `troubleshooting.md`
- Corrected references to MCP tools that no longer exist on the official server: `update_issue` → `save_issue` (the server consolidates create/update into `save_*` tools) in `SKILL.md`, and `mcp__linear__linear_search_issues` (old community-server tool) → `list_issues` with namespacing notes in `api.md` and `projects.md`. Verified against the live official server's tool surface
- Removed the `SKILL.md` varlock step that wired `LINEAR_API_KEY` into the MCP server env — the official server uses OAuth and never reads the key; clarified the key is only for the skill's SDK/GraphQL scripts
- Added `mcp__linear-server` to `allowed-tools` (the server name Linear's docs use), alongside the existing `mcp__linear`

> Note: this diverges the vendored skill from upstream `wrsmith108/linear-claude-skill`, which still documents the deprecated `/sse` + `mcp-remote` setup and pins an older SDK.

## [2.3.1] - 2026-03-04

### Added
- Initial addition to marketplace
- Linear issue, project, and team management skill
- TypeScript SDK scripts for automation (14 main scripts + 11 lib modules)
- Reference documentation (api.md, sdk.md, sync.md, projects.md, troubleshooting.md)
- Label taxonomy system with 25 labels across 3 categories
- Unit tests for utility functions using vitest
- Prettier formatting configuration
- Makefile integration for linting, type checking, formatting, and tests
