# Linear Skill Troubleshooting

Common issues and solutions when working with Linear via MCP, CLI, or API.

---

## MCP Server Issues

### Which MCP Server to Use

**Always use the official Linear MCP server** at `mcp.linear.app` over native HTTP transport:

```bash
claude mcp add --transport http --scope user linear-server https://mcp.linear.app/mcp
```

Or in `.mcp.json`:

```json
{
  "mcpServers": {
    "linear-server": {
      "type": "http",
      "url": "https://mcp.linear.app/mcp"
    }
  }
}
```

Authentication is via OAuth: run `/mcp`, pick the server, and log in through the browser. The server does not read `LINEAR_API_KEY`.

> **WARNING**: The old `/sse` endpoint and the `npx mcp-remote https://mcp.linear.app/sse` shim are deprecated. A config still pointing at `/sse` fails OAuth with `SDK auth failed: Protected resource https://mcp.linear.app/mcp does not match expected https://mcp.linear.app/sse` — fix it by re-adding the server with the `/mcp` URL above. Do NOT use deprecated community servers (`linear-mcp-server` npm package, `jerhadf/linear-mcp-server`) either. They have critical bugs.

---

## Historical: Why Community MCP Servers Failed

> **Note**: These issues are **resolved** with the official Linear MCP server at `mcp.linear.app`. This section is preserved for reference when troubleshooting deprecated community server configurations.

### Issue 1: Status Update Schema Mismatch (FIXED in Official Server)

The deprecated `linear-mcp-server` (npm) had a critical bug:

| Community Server | Official Server |
|------------------|-----------------|
| `status: "Done"` → passed as `stateId` (UUID required) → ❌ Fails | `state: "Done"` → resolved internally → ✅ Works |

**The official server correctly resolves state names to UUIDs internally.**

### Issue 2: SSE Connection Timeouts

Both servers can experience SSE connection drops after extended idle periods. The official server has improved keep-alive handling, but for very long operations, helper scripts remain a reliable fallback.

**Best Practice**: Use the official MCP server for most operations. Fall back to helper scripts for bulk operations or timeout-prone scenarios.

---

## Helper Scripts Overview

When MCP is unavailable or unreliable, use the helper scripts.

### Linear API Wrapper (scripts/linear-api.mjs)

A complete API wrapper with proper JSON escaping and error handling:

```bash
# Create issue (replace <TEAM> with your team key, e.g., ENG, PROJ)
node scripts/linear-api.mjs create-issue \
  --team <TEAM> --title "New feature" --description "Details here" --priority 2

# Update status (replace <TEAM>-123 with your issue identifier)
node scripts/linear-api.mjs update-status \
  --issue <TEAM>-123 --status done

# Add comment
node scripts/linear-api.mjs add-comment \
  --issue <TEAM>-123 --body "Fixed in PR #25"

# Add project update
node scripts/linear-api.mjs add-project-update \
  --project <PROJECT_UUID> --body "## Status Update\n\nProgress details..." --health onTrack

# List issues
node scripts/linear-api.mjs list-issues \
  --team <TEAM> --status "In Progress" --limit 20

# List labels
node scripts/linear-api.mjs list-labels --team <TEAM>

# Help
node scripts/linear-api.mjs help
```

**Benefits over MCP:**
- Proper JSON escaping (no shell parsing issues)
- Reliable status updates (uses correct GraphQL types)
- Batch-friendly for scripting
- Can be imported as ES module for programmatic use

### Quick Comment

The interactive default is the MCP `save_comment` tool (resolves the issue for you — no UUID lookup needed). To attach a comment alongside a bulk state change, `scripts/sync.ts` takes a `--comment` flag:

```bash
# Comment while updating state (one command)
npx tsx scripts/sync.ts --issues PROJ-123 --state Done --comment "Fixed in PR #25"
```

For a comment on its own (multi-line, no state change), a short SDK call is the cleanest path:

```typescript
import { LinearClient } from '@linear/sdk'
const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY })

const issues = await client.issues({ filter: { number: { eq: 123 } } })
await client.createComment({
  issueId: issues.nodes[0].id,
  body: '## Resolved\n\nImplementation complete. All tests passing.',
})
```

**Pattern**: MCP tools are the interactive default (issue creation, single status updates, comments, and filtered searches via `list_issues`). Reach for SDK scripts for anything bulk, scripted, or multi-step — including typed `filter` searches. Raw GraphQL is a last-resort escape hatch via the SDK's `rawRequest`, not a separate toolchain.

---

## Common Errors

### "MCP tools not available"

This is NOT a blocker. Use the Linear CLI via Bash:

```bash
linear issues view ENG-123
linear issues create --title "Issue title"
linear issues update ENG-123 -s "STATE_ID"
```

### Status Update Fails with Schema Error

If using the official server, use `state: "Done"` (not `status: "Done"`).

If still failing, use the bundled SDK script (state name followed by issue identifiers; bare numbers work too, the prefix is stripped automatically):

```bash
npx tsx scripts/linear-ops.ts status Done ENG-123 ENG-124
```

### SSE Connection Timeout

For long-running operations, prefer the bulk sync script:

```bash
npx tsx scripts/sync.ts --issues PROJ-101,PROJ-102,PROJ-103 --state Done
```

### API Key Not Set

Verify your API key is configured:

```bash
varlock load 2>&1 | grep LINEAR
```

If not set, add to your environment:

```bash
export LINEAR_API_KEY="lin_api_your_key_here"
```

---

## Debugging

### Test Connection

```bash
npx tsx scripts/query.ts "query { viewer { name } }"
```

### Check MCP Configuration

Ensure `mcp.linear.app` (not a community server) is configured in your MCP settings.

### View Available States

```bash
npx tsx scripts/query.ts 'query { workflowStates(first: 50) { nodes { id name type } } }'
```

---

## See Also

- [api.md](api.md) - GraphQL API reference and timeout handling
- [sync.md](sync.md) - Bulk sync patterns
- [SKILL.md](SKILL.md) - Main skill documentation
