# Linear SDK Automation Scripts

Reference for writing TypeScript automation scripts against `@linear/sdk`. This is the
**programmatic path** for the skill's bundled scripts: anything the Linear API supports,
fully typed, driven from a `.ts` file run with `npx tsx`.

## When to use this vs. other tools

- **MCP tools** — the interactive default. One issue, a quick lookup, a status change in
  conversation. No script, no API key.
- **SDK scripts (this file)** — the programmatic default. Loops, bulk updates, conditional
  logic, data export, multi-step flows, anything that needs typed models and N operations.
  The SDK is generated from Linear's GraphQL schema, so it exposes essentially the whole API.
- **Raw GraphQL via `client.client.rawRequest`** — a rare escape hatch, not a peer tier.
  Because the SDK is generated from the same schema, "the field isn't exposed by the SDK" is
  almost never true. Reach for it only for an operation the typed methods genuinely lack.

## Setup

```typescript
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY });
```

- Personal API key: `new LinearClient({ apiKey })` — the key is sent verbatim as the
  `Authorization` header (no `Bearer ` prefix).
- OAuth access token: `new LinearClient({ accessToken })` — the SDK adds the `Bearer ` prefix
  (and leaves it alone if you already included one). The token comes from the OAuth2 token
  endpoint; an app can act either as itself (`actor=app`) or on behalf of the authorizing user
  (`actor=user`). See https://linear.app/developers/oauth-2-0-authentication.
- `LinearClientOptions` extends `RequestInit`, so you can pass custom `headers`, and override
  `apiUrl` (defaults to `https://api.linear.app/graphql`).

Set `LINEAR_API_KEY` in the environment and run with `npx tsx script.ts`.

## Core querying + the lazy-relation trap

Top-level queries hang off the client. Single fetches resolve a model; plural fetches resolve
a **connection** (`{ nodes, pageInfo }`):

```typescript
const me = await client.viewer;                 // current user (a getter, still await it)
const issue = await client.issue("ISS-123");     // by id or identifier
const issues = await client.issues({ first: 50 }); // IssueConnection
const teams = await client.teams();
const projects = await client.projects({ first: 50 });
const states = await client.workflowStates({ filter: { team: { key: { eq: "ENG" } } } });
const labels = await client.issueLabels();
const initiatives = await client.initiatives();
const statuses = await client.projectStatuses();
```

There is **no field selection** at this layer — every model comes back with all its scalar
fields. You narrow results with pagination variables (`first`, `after`) and `filter`, not by
choosing fields.

### The #1 correctness trap: relation getters are lazy

On a model, **relation getters return a Promise and cost an extra API round-trip each time you
`await` them.** `issue.state`, `issue.assignee`, `issue.team`, `issue.project`, `issue.parent`,
`issue.cycle` are all lazy. Accessing `issue.state.type` synchronously is a bug — `issue.state`
is a `Promise`, not a `WorkflowState`.

For each lazy relation the SDK also exposes a **synchronous `<rel>Id` getter** that returns the
cached id with **no** round-trip. Prefer the id when the id is all you need:

```typescript
issue.stateId;     // synchronous string | undefined — no network call
issue.assigneeId;  // synchronous string | undefined
issue.teamId;      // synchronous string | undefined
issue.projectId;   // synchronous string | undefined

const state = await issue.state;   // one round-trip
console.log(state?.type);          // now safe: "started" | "completed" | ...
```

Doing this in a loop is a textbook N+1. Resolving `await issue.assignee` for 200 issues fires
200 extra requests. Avoid it by filtering server-side, comparing ids, or resolving relations
once into a lookup map:

```typescript
// GOOD: no per-issue round-trips — compare cached ids
const open = issues.nodes.filter(
  (i) => i.priority === 1 && i.stateId === targetStateId
);

// GOOD: resolve users once, then map by id
const users = await client.users();
const byId = new Map(users.nodes.map((u) => [u.id, u.name]));
const report = issues.nodes.map((i) => ({
  id: i.identifier,
  assignee: i.assigneeId ? byId.get(i.assigneeId) ?? "Unknown" : "Unassigned",
}));

// BAD: N+1 — one extra request per issue
// for (const i of issues.nodes) console.log((await i.assignee)?.name);
```

Nested **connections** are methods, not getters — call them: `issue.comments()`,
`issue.children()`, `issue.attachments()`, `issue.labels()`. They return connections you
paginate like any other.

```typescript
const comments = await issue.comments();
for (const c of comments.nodes) console.log(c.body);
```

> Note: `client.team(id)` / `client.project(id)` take a **UUID**, not a human key like `"ENG"`.
> To resolve a team by its key, filter: `client.teams({ filter: { key: { eq: "ENG" } } })`.

## Filtering cookbook

`filter:` takes typed comparators. The common ones:

- **String** (`title`, `name`, …): `eq`, `neq`, `in`, `nin`, `contains`, `notContains`,
  `containsIgnoreCase`, `startsWith`, `endsWith`, `eqIgnoreCase`.
- **Number** (`priority`, `estimate`): `eq`, `neq`, `in`, `nin`, `gt`, `gte`, `lt`, `lte`.
- **Date** (`createdAt`, `updatedAt`, `dueDate`): the same comparators on a `DateTimeOrDuration`
  scalar, accepting either an ISO timestamp **or a relative ISO-8601 duration** added to *now* —
  e.g. `"-P2W1D"` (two weeks and a day ago), `"-P1D"`, `"-PT4H"`. (Per the GraphQL schema's
  `DateTimeOrDuration` scalar; see https://linear.app/developers/filtering.)
- **Id** (`id`): `eq`, `neq`, `in`, `nin`.
- **Nullable** variants add `null: true | false`.

```typescript
const recent = await client.issues({
  filter: {
    state: { type: { eq: "started" } },          // nested relation filter
    priority: { lte: 2 },                          // number comparator
    updatedAt: { gt: "-P2W" },                     // relative duration
    title: { containsIgnoreCase: "migration" },
  },
});
```

Logical `and:[...]` / `or:[...]` nest arbitrarily:

```typescript
filter: {
  or: [
    { priority: { eq: 1 } },
    { and: [{ priority: { eq: 2 } }, { dueDate: { lt: "-P0D" } }] },
  ],
}
```

Nested **relation filters** drill into related entities:

```typescript
filter: { team: { key: { eq: "ENG" } } }
filter: { team: { name: { eq: "Engineering" } } }
filter: { project: { name: { contains: "Q3" } } }
filter: { assignee: { email: { eq: "dev@example.com" } } }
filter: { state: { type: { eq: "completed" } } }
```

Collection filters on **to-many** relations (e.g. `labels`) use `every` / `some` / `length`:

```typescript
filter: { labels: { some: { name: { eq: "bug" } } } }   // has at least one "bug" label
filter: { labels: { every: { name: { neq: "wontfix" } } } } // every label is not "wontfix"
filter: { labels: { length: { eq: 0 } } }               // no labels at all
```

(There is no `none` operator on collection filters in this SDK; express "has none" with
`every: { ... neq ... }` or a `length` comparator.)

Filtering server-side is also how you sidestep the lazy-relation trap: prefer
`filter: { assignee: { isMe: { eq: true } } }` over fetching every issue and awaiting
`issue.assignee`.

## Pagination

**The default page size is 50, and an unpaginated call silently truncates** — `client.issues()`
returns at most 50 nodes with no error. Always paginate when a result set could exceed that.

`connection.pageInfo` carries `hasNextPage` and `endCursor`. Three ways to exhaust a connection:

```typescript
import { LinearDocument } from "@linear/sdk";

// 1. client.paginate — exhaustively pages and returns a flat array. Simplest.
const all = await client.paginate(client.issues, {
  filter: { team: { key: { eq: "ENG" } } },
  orderBy: LinearDocument.PaginationOrderBy.UpdatedAt,
});
console.log(`Total: ${all.length}`);

// 2. fetchNext — accumulates pages in place onto connection.nodes, returns the connection.
let conn = await client.issues({ first: 100 });
while (conn.pageInfo.hasNextPage) {
  conn = await conn.fetchNext();
}
console.log(`Total: ${conn.nodes.length}`); // nodes accumulate across fetchNext() calls

// 3. Manual cursor loop, if you need to process page-by-page.
let after: string | undefined;
do {
  const page = await client.issues({ first: 100, after });
  for (const issue of page.nodes) {
    /* ... */
  }
  after = page.pageInfo.hasNextPage ? page.pageInfo.endCursor ?? undefined : undefined;
} while (after);
```

`client.paginate(fn, args)` passes `fn` the connection query (e.g. `client.issues`) and the
query args; it returns `Promise<T[]>` of every node, managing `after` cursors for you. It
*does* honor a `first` you put in `args` (used as the per-page size; it defaults to 50 when you
omit one) — so pass a larger `first` (e.g. `100`) to page in bigger chunks and cut round-trips.

## Mutations

Mutations are **verb-first methods on the client**. Each returns a payload with `success`, a
numeric `lastSyncId`, and a **lazy** entity getter (a re-fetch) alongside a synchronous id:

```typescript
const payload = await client.createIssue({
  teamId: team.id,            // REQUIRED
  title: "Investigate flaky test",
  description: "Markdown body",
  assigneeId: user.id,        // flat string id
  stateId: stateId,           // flat string id
  projectId: projectId,       // flat string id
  parentId: parentId,         // flat string id (sub-issue)
  priority: 2,
  labelIds: ["<label-uuid-1>", "<label-uuid-2>"], // label UUIDs — NOT label names
});

console.log(payload.success, payload.lastSyncId);
const created = await payload.issue; // lazy re-fetch — costs a round-trip
console.log(created?.identifier);
```

`IssueCreateInput` essentials: **`teamId` is required**; id fields (`stateId`, `projectId`,
`parentId`, `assigneeId`, `cycleId`) are **flat strings**; labels are **`labelIds: string[]`**
of label UUIDs. There is no `labels: [...]` field — passing label names will not compile and
will not work. Resolve names to ids first (`client.issueLabels({ filter: { name: { eq } } })`).

Common mutations:

```typescript
await client.updateIssue(id, { stateId, priority: 1 });
await client.deleteIssue(id);                          // trashes the issue
await client.createComment({ issueId, body: "Looks good" });
await client.createProject({ name, teamIds: [teamId] });
await client.updateProject(id, { statusId });          // see status note below
await client.createProjectUpdate({ projectId, body, health: "onTrack" });
await client.createInitiativeUpdate({ initiativeId, body });
await client.createInitiativeToProject({ initiativeId, projectId });
await client.createEntityExternalLink({ url, label, projectId }); // links to project/initiative/release, not an issue
await client.createAttachment({ issueId, url, title });
await client.attachmentLinkURL(issueId, url);          // positional args
```

Batch update many issues in one request (ids are UUIDs):

```typescript
const batch = await client.updateIssueBatch(
  ["<uuid-1>", "<uuid-2>", "<uuid-3>"],
  { stateId: doneStateId }
);
console.log(batch.success);
for (const issue of batch.issues) {  // .issues is a synchronous Issue[] here
  console.log(issue.identifier);
}
```

Models also carry their own mutation methods: `await issue.update({ priority: 1 })`,
`await issue.archive()`, `await project.archive()`. (Note: the `Issue` model has **no**
`addComment` method — use `client.createComment({ issueId, body })`.)

> **Project status:** `Project.state` (a string) is **deprecated**. Use project statuses:
> read them from `client.projectStatuses()`, then `client.updateProject(id, { statusId })`.
> The current status on a project is `await project.status` (lazy) / `project.statusId` (sync).

## Error handling & rate limits

Every thrown error is a `LinearError` subclass: `InvalidInputLinearError`,
`AuthenticationLinearError`, `ForbiddenLinearError`, `RatelimitedLinearError`,
`NetworkLinearError`, `InternalLinearError`, `UsageLimitExceededLinearError`,
`FeatureNotAccessibleLinearError`, and others. A `LinearError` carries `type` (a
`LinearErrorType`), `errors[]` (each with `type` / `message` / `userError` / `path`),
`status`, `query`, and `variables`.

```typescript
import {
  LinearError,
  InvalidInputLinearError,
  RatelimitedLinearError,
} from "@linear/sdk";

try {
  await client.createIssue({ teamId, title: "x" });
} catch (error) {
  if (error instanceof InvalidInputLinearError) {
    console.error("Bad input:", error.errors?.map((e) => e.message).join("; "));
  } else if (error instanceof LinearError) {
    console.error(`Linear error (${error.type}, HTTP ${error.status}):`, error.message);
  } else {
    throw error;
  }
}
```

`RatelimitedLinearError` additionally exposes values parsed from the response headers. The API
enforces **two independent budgets** per window — a request count and a query-complexity score —
each surfaced through its own `x-ratelimit-*` headers:

| Field | Header | Meaning |
|-------|--------|---------|
| `retryAfter` | `retry-after` | Seconds to wait before retrying |
| `requestsLimit` / `requestsRemaining` | `x-ratelimit-requests-limit` / `-remaining` | Request budget for the window |
| `requestsResetAt` | `x-ratelimit-requests-reset` | **Unix timestamp** when the request budget resets |
| `complexityLimit` / `complexityRemaining` | `x-ratelimit-complexity-limit` / `-remaining` | Query-complexity budget |
| `complexityResetAt` | `x-ratelimit-complexity-reset` | **Unix timestamp** when the complexity budget resets |

(`*ResetAt` are Unix timestamps, not seconds-from-now like `retryAfter`.) **The SDK does not
retry for you** — honor `retryAfter` yourself:

```typescript
async function withRetry<T>(fn: () => Promise<T>, attempts = 3): Promise<T> {
  for (let i = 0; ; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error instanceof RatelimitedLinearError && i < attempts - 1) {
        const waitSec = error.retryAfter ?? 2 ** i;
        await new Promise((r) => setTimeout(r, waitSec * 1000));
        continue;
      }
      throw error;
    }
  }
}

const issue = await withRetry(() => client.issue("ISS-123"));
```

## Raw escape hatch

When (rarely) you need raw GraphQL, the underlying client is reachable at `client.client`:

Both `request` and `rawRequest` are generic over `<Data, Variables>` — when you supply a type
argument you must supply both:

```typescript
// request() returns just data; rawRequest() returns { data, headers, status, errors }
const data = await client.client.request<
  { viewer: { id: string; name: string } },
  Record<string, unknown>
>(`query { viewer { id name } }`);

const raw = await client.client.rawRequest<
  { viewer: { id: string } },
  Record<string, unknown>
>(`query { viewer { id } }`, {});
console.log(raw.status, raw.headers);

client.client.setHeader("x-custom", "value"); // persists on subsequent requests
```

Prefer the typed methods above; this exists for the genuine gaps only.

## File upload & attachments

Uploading a file is a 3-step flow: ask Linear for a pre-signed URL, PUT the bytes, then
reference the permanent `assetUrl`. `fileUpload(contentType, filename, size)` returns an
`UploadPayload` whose `uploadFile` carries `uploadUrl`, `assetUrl`, and a `headers: {key,value}[]`
list — **every one of those headers must be replayed on the PUT** (alongside the `Content-Type`
you passed), or the upload is rejected. See https://linear.app/developers/uploading-files.

```typescript
import { readFile } from "node:fs/promises";

async function uploadAsset(filePath: string, contentType: string, filename: string) {
  const bytes = await readFile(filePath);

  // 1. Request an upload slot.
  const payload = await client.fileUpload(contentType, filename, bytes.byteLength);
  const uploadFile = payload.uploadFile;
  if (!payload.success || !uploadFile) throw new Error("Upload prep failed");

  // 2. PUT the bytes to the pre-signed URL with the headers Linear returned.
  const headers: Record<string, string> = { "Content-Type": contentType };
  for (const h of uploadFile.headers) headers[h.key] = h.value;
  const res = await fetch(uploadFile.uploadUrl, { method: "PUT", body: bytes, headers });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);

  // 3. Use the permanent asset URL.
  return uploadFile.assetUrl;
}

const assetUrl = await uploadAsset("./diagram.png", "image/png", "diagram.png");

// Embed in markdown (e.g. an issue description/comment):
await client.createComment({ issueId, body: `![diagram](${assetUrl})` });

// Or attach it to an issue:
await client.createAttachment({ issueId, url: assetUrl, title: "diagram.png" });
```

## Webhooks (brief)

Verify and route webhooks with the dedicated subpath export `@linear/sdk/webhooks`. The
`LinearWebhookClient` recomputes the HMAC-SHA256 of the **raw request body** keyed by your
signing secret, compares it timing-safely against the `linear-signature` header, and enforces a
60-second replay window. (The top-level `LinearWebhooks` export is a deprecated alias.)

The timestamp it checks comes from the payload's own `webhookTimestamp` field (a Unix-ms number),
falling back to the `linear-timestamp` header when absent — pass whichever you have. Sign with
the **raw bytes**, never a re-serialized JSON string, or the HMAC won't match.

```typescript
import { LinearWebhookClient } from "@linear/sdk/webhooks";

const webhooks = new LinearWebhookClient(process.env.LINEAR_WEBHOOK_SECRET!);

// Manual verify/parse against a raw body Buffer + the `linear-signature` header.
// NOTE: both verify() and parseData() THROW on a bad signature or stale timestamp —
// verify() only ever returns `true` (it does not return `false`). Wrap in try/catch.
const ok = webhooks.verify(rawBody, signature, timestamp);     // true | throws
const payload = webhooks.parseData(rawBody, signature, timestamp); // verifies + parses, or throws

// Or build a handler that works for both Node http and Fetch-API runtimes:
const handler = webhooks.createHandler();
handler.on("Issue", (p) => console.log("issue event", p.action));
handler.on("*", (p) => console.log("any event", p.type));
// Node:   http.createServer((req, res) => handler(req, res))
// Fetch:  export default { fetch: (req) => handler(req) }
```

## Script template

```typescript
#!/usr/bin/env tsx
import { LinearClient, LinearDocument, LinearError, RatelimitedLinearError } from "@linear/sdk";

const LINEAR_API_KEY = process.env.LINEAR_API_KEY;
if (!LINEAR_API_KEY) {
  console.error("LINEAR_API_KEY environment variable required");
  process.exit(1);
}

const client = new LinearClient({ apiKey: LINEAR_API_KEY });

async function withRetry<T>(fn: () => Promise<T>, attempts = 3): Promise<T> {
  for (let i = 0; ; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error instanceof RatelimitedLinearError && i < attempts - 1) {
        await new Promise((r) => setTimeout(r, (error.retryAfter ?? 2 ** i) * 1000));
        continue;
      }
      throw error;
    }
  }
}

async function main() {
  const me = await client.viewer;
  console.log(`Running as: ${me.name}`);

  // Paginate exhaustively — never rely on the silent 50-item default.
  const myOpen = await client.paginate(client.issues, {
    filter: {
      assignee: { isMe: { eq: true } },
      state: { type: { eq: "started" } },
    },
    orderBy: LinearDocument.PaginationOrderBy.UpdatedAt,
  });

  console.log(`You have ${myOpen.length} in-progress issues`);
  for (const issue of myOpen) {
    // Use the synchronous id getters in loops — no N+1 round-trips.
    console.log(`- ${issue.identifier}: ${issue.title} [state ${issue.stateId}]`);
  }
}

main().catch((error) => {
  if (error instanceof LinearError) {
    console.error(`Linear error (${error.type}):`, error.message);
  } else {
    console.error("Error:", error instanceof Error ? error.message : error);
  }
  process.exit(1);
});
```

## Running scripts

```bash
npx tsx automation.ts                          # direct
LINEAR_API_KEY=lin_api_xxx npx tsx automation.ts  # with inline env
```

## Version note

Authored against **`@linear/sdk` 86.0.0** and verified against the official source at
https://github.com/linear/linear (`packages/sdk/src`). The SDK is auto-generated from Linear's
GraphQL API; method, model, and input shapes track the schema. Full reference:
https://linear.app/developers/sdk
