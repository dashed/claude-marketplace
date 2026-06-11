# Linear GraphQL API

Raw GraphQL is the **last-resort escape hatch** — reached *through* the SDK, not as a parallel toolchain. The typed `@linear/sdk` (see [sdk.md](sdk.md)) is generated from this same GraphQL schema, so anything the API supports is almost always reachable via a typed SDK call. Drop to raw GraphQL only for the rare query the SDK doesn't expose conveniently.

The SDK exposes raw GraphQL via `client.client.rawRequest`:

```typescript
import { LinearClient } from '@linear/sdk'
const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY })

const result = await client.client.rawRequest(`query { viewer { id name } }`)
console.log(result.data)
```

The bundled `scripts/query.ts` is exactly this — a thin CLI wrapper around `rawRequest` for ad-hoc queries:

```bash
npx tsx scripts/query.ts "query { viewer { id name } }"
# with variables:
npx tsx scripts/query.ts "query(\$id: String!) { issue(id: \$id) { title } }" '{"id": "ISSUE_ID"}'
```

This document covers the underlying GraphQL: auth, example queries/mutations, and shell-quoting/timeout concepts. Prefer the SDK (`sdk.md`) for real work.

## Authentication

**Endpoint**: `https://api.linear.app/graphql`

**Authentication Header**:
```
Authorization: <API_KEY>
```

Personal API keys are available in Linear under Security & access settings.

## Running Queries

For ad-hoc queries, use the bundled `scripts/query.ts` (the `rawRequest` CLI shown above). For anything beyond a one-off query — bulk, scripted, or multi-step — write a typed SDK script instead (see [sdk.md](sdk.md)).

**Environment Variable**: `query.ts` and any SDK script require `LINEAR_API_KEY` to be set. If it is not available to the Claude process, you cannot execute GraphQL queries automatically. (The MCP server does not use this key — it authenticates via OAuth.)

### Example Queries

**Get authenticated user:**
```graphql
query Me {
  viewer {
    id
    name
    email
  }
}
```

**Get team issues:**
```graphql
query Team($teamId: String!) {
  team(id: $teamId) {
    issues {
      nodes {
        id
        title
        state { name }
        assignee { name }
      }
    }
  }
}
```

**Get user's assigned issues:**
```graphql
query MyIssues {
  viewer {
    assignedIssues {
      nodes {
        id
        title
        state { name }
        team { key }
      }
    }
  }
}
```

### Mutations

**Create issue:**
```graphql
mutation CreateIssue($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
      id
      identifier
      title
    }
  }
}
```

With variables:
```json
{
  "input": {
    "teamId": "TEAM_ID",
    "title": "Issue title",
    "description": "Issue description",
    "stateId": "STATE_ID",
    "projectId": "PROJECT_ID"
  }
}
```

**Update issue:**
```graphql
mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) {
    success
    issue {
      id
      title
      state { name }
    }
  }
}
```

**Look up project by name:**
```graphql
query ProjectByName($filter: ProjectFilter!) {
  projects(filter: $filter, first: 10) {
    nodes {
      id
      name
      status { id name }   # the project `state` string is deprecated — use `status`
      slugId
    }
  }
}
```

With variables:
```json
{
  "filter": {
    "name": { "containsIgnoreCase": "Phase 6A" }
  }
}
```

## Rate Limiting

Linear enforces **two independent per-window budgets** — a request count and a query-complexity score — and a `429` response means you exhausted one of them. Read the budgets off the response headers:

- `retry-after` — seconds to wait before retrying
- `x-ratelimit-requests-limit` / `-remaining` / `-reset` — request budget (`-reset` is a Unix timestamp)
- `x-ratelimit-complexity-limit` / `-remaining` / `-reset` — query-complexity budget

The SDK parses all of these into `RatelimitedLinearError` (see [sdk.md](sdk.md)); over raw GraphQL you must read them yourself. The API does **not** retry for you — honor `retry-after`. For real-time updates, prefer webhooks over polling. See https://linear.app/developers/rate-limiting.

## Key Concepts

- **Team IDs**: Required for most operations involving issues and projects
- **State IDs**: Issues default to the team's first Backlog state unless specified
- **Archived Resources**: Hidden by default; use `includeArchived: true` to retrieve
- **Error Handling**: Always check the `errors` array in responses before assuming success

## Using the SDK Directly

For real automation, use the typed `@linear/sdk` client rather than raw GraphQL — it covers the same schema with full type hints. See **[sdk.md](sdk.md)** for complete patterns (fetching/filtering, bulk updates, pagination, reporting). Raw GraphQL via `rawRequest` is only for the rare field the typed client doesn't expose.

---

## Timeout Handling Patterns

When operations take longer than expected, use these patterns to maintain reliability.

### Progress Notifications

For bulk operations, notify the user of progress:

```javascript
const issues = ['PROJ-101', 'PROJ-102', 'PROJ-103'];
for (let i = 0; i < issues.length; i++) {
  console.log(`Processing ${i + 1}/${issues.length}: ${issues[i]}`);
  // ... operation
}
```

### Chunked Batch Operations

Break large batches into smaller chunks to avoid timeouts:

```javascript
const BATCH_SIZE = 10;
const DELAY_MS = 150; // Avoid rate limiting

for (let i = 0; i < issues.length; i += BATCH_SIZE) {
  const batch = issues.slice(i, i + BATCH_SIZE);
  console.log(`Batch ${Math.floor(i / BATCH_SIZE) + 1}: Processing ${batch.length} issues`);

  for (const issue of batch) {
    await processIssue(issue);
    await new Promise(r => setTimeout(r, DELAY_MS));
  }
}
```

### Fallback on Timeout

Detect timeouts and fall back to GraphQL:

```javascript
try {
  // Try MCP first (faster when it works). Pseudo-code: the official server's
  // search tool is list_issues, namespaced by the configured server name
  // (e.g. mcp__linear-server__list_issues).
  await list_issues({ query: "keyword" });
} catch (error) {
  if (error.message.includes('timeout') || error.message.includes('ETIMEDOUT')) {
    console.log('MCP timed out, falling back to the SDK...');
    // Re-run the same search via the typed SDK (preferred), e.g.
    //   await client.issues({ filter: { /* ... */ } });
    // or, for a raw query, scripts/query.ts / client.client.rawRequest.
  }
}
```

### Bulk Sync Script

Use `scripts/sync.ts` for reliable bulk state updates:

```bash
# Update multiple issues to Done state (replace PROJ with your team prefix)
LINEAR_API_KEY=lin_api_xxx npx tsx scripts/sync.ts --issues PROJ-101,PROJ-102,PROJ-103 --state Done

# Preview changes without applying
LINEAR_API_KEY=lin_api_xxx npx tsx scripts/sync.ts --issues PROJ-101,PROJ-102 --state Done --dry-run

# Add comment with state change
LINEAR_API_KEY=lin_api_xxx npx tsx scripts/sync.ts --issues PROJ-101 --state Done --comment "Completed in PR #42"
```

---

## When MCP Times Out

If an MCP call times out or fails, fall back to the **SDK** (typed `client.issues(...)`, `issue.update(...)`, `client.createComment(...)` — see [sdk.md](sdk.md)) for anything real, or to `scripts/query.ts` for a quick raw query. Don't hand-roll `fetch` calls against the GraphQL endpoint — `query.ts` already wraps `rawRequest` with auth and error handling, and the SDK covers the rest.

### Shell Quoting

`scripts/query.ts` takes the query as a single string argument, which sidesteps most quoting traps. When you do pass a raw GraphQL string through the shell, use **single quotes** so the shell leaves `$`, backticks, and `?` alone:

```bash
# ✅ Single-quote the whole query; no shell interpolation of $ or ?
npx tsx scripts/query.ts 'query { issues(first: 25, filter: { state: { type: { nin: ["completed","canceled"] } } }) { nodes { identifier title state { name } } } }'
```

If you must embed shell variables, pass them as GraphQL **variables** (second arg, JSON) rather than interpolating into the query string:

```bash
npx tsx scripts/query.ts 'query($num: Float!) { issues(filter: { number: { eq: $num } }) { nodes { id identifier } } }' '{"num": 123}'
```

### Fallback Examples (raw GraphQL via `query.ts`)

These show the *queries*; for real work prefer the typed SDK equivalents.

**Search issues:**
```bash
npx tsx scripts/query.ts 'query { issues(first: 25, filter: { team: { key: { eq: "TEAM" } }, state: { type: { nin: ["completed","canceled"] } } }) { nodes { identifier title state { name } priority } } }'
```

**Update issue status** — preferred path is the SDK (`await issue.update({ stateId })`) or the bundled `scripts/linear-ops.ts status Done ENG-123`. As raw GraphQL, look up the state ID then update:
```bash
# 1. Get the "Done" workflow state ID for the team
npx tsx scripts/query.ts 'query { workflowStates(filter: { team: { key: { eq: "TEAM" } }, name: { eq: "Done" } }) { nodes { id name } } }'

# 2. Update the issue (substitute the UUIDs)
npx tsx scripts/query.ts 'mutation { issueUpdate(id: "ISSUE_UUID", input: { stateId: "DONE_STATE_UUID" }) { success issue { identifier state { name } } } }'
```

**Add comment** — preferred path is the MCP `save_comment` tool or `client.createComment({ issueId, body })`. As raw GraphQL:
```bash
# Resolve identifier → UUID, then create the comment
npx tsx scripts/query.ts 'query { issues(filter: { number: { in: [123,124,125] } }) { nodes { id identifier } } }'
npx tsx scripts/query.ts 'mutation { commentCreate(input: { issueId: "ISSUE_UUID", body: "Implementation complete. See PR #42." }) { success } }'
```

**Pro Tip**: Store frequently-used IDs (team UUID, common state UUIDs) in your project's CLAUDE.md to avoid repeated lookups.

---

## Reference

- [Linear GraphQL Documentation](https://linear.app/developers/graphql)
- [Linear SDK](https://github.com/linear/linear/tree/master/packages/sdk)

Use GraphQL introspection to discover the API schema:

```bash
LINEAR_API_KEY=lin_api_xxx npx tsx scripts/query.ts "{ __schema { types { name description } } }"
```
