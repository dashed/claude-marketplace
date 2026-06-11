# Linear Sync Patterns

Synchronize code changes with Linear issues. Keeps Linear reflecting implementation progress as work lands.

## When to Use

Invoke sync when:
- Completing implementation of Linear issues (ENG-XXX)
- Finishing bug fixes referenced in commits
- Closing out a phase with multiple issues
- Before creating PRs (ensure Linear reflects current state)

## The Sync Script

`scripts/sync.ts` is an SDK script (`@linear/sdk`) for bulk issue **state** updates. Run it with `npx tsx` — `tsx` is the bundled runner (there is no `ts-node` dependency).

```bash
npx tsx scripts/sync.ts --issues ENG-432,ENG-433,ENG-434 --state Done
```

### Flags

The script supports exactly these flags (see `scripts/sync.ts`):

| Flag | Required | Description |
|------|----------|-------------|
| `--issues` | Yes | Comma-separated issue identifiers, e.g. `ENG-432,ENG-433` |
| `--state` | Yes | Target workflow state name, e.g. `Done`, `"In Progress"`, `Backlog` |
| `--comment` | No | Comment to add to each issue alongside the state change |
| `--dry-run` | No | Preview changes without applying them |

The team key is inferred from the first issue identifier (`ENG-432` → team `ENG`), and the state name is resolved to its UUID for that team automatically.

> **Scope**: `sync.ts` updates issue *state* only. To change a **project's** status, use `scripts/linear-ops.ts project-status` (see below). To **verify** results, query the issues (see Verification).

## Sync Modes

### Mode 1: Bulk Issue Sync

Update multiple issues to a target state:

```bash
# Update issues to Done
npx tsx scripts/sync.ts --issues ENG-432,ENG-433,ENG-434,ENG-435 --state Done

# Output:
#   ENG-432: ✅ Updated to "Done"
#   ENG-433: ✅ Updated to "Done"
#   ...
#   📊 Summary: 4 succeeded, 0 failed

# Preview first (no changes applied)
npx tsx scripts/sync.ts --issues ENG-432,ENG-433 --state Done --dry-run

# Update with a comment on each issue
npx tsx scripts/sync.ts --issues ENG-432 --state Done --comment "Completed in PR #42"
```

For a single issue or a quick interactive update, the MCP `save_issue` tool (with `state: "Done"`) is the simpler path. Use `sync.ts` when updating several issues at once.

### Mode 2: Agent-Spawned Sync

Spawn a parallel agent via the Task tool for autonomous sync:

```javascript
Task({
  description: "Sync Current Phase to Linear",
  prompt: `
    Update these Linear issues to Done:
    ENG-432, ENG-433, ENG-434, ENG-435, ENG-436, ENG-437

    Use: npx tsx scripts/sync.ts --issues ENG-432,...,ENG-437 --state Done
    Then mark project "Current Phase" completed:
      npx tsx scripts/linear-ops.ts project-status "Current Phase" completed
    Report success/failure counts.
  `,
  subagent_type: "Linear-specialist"
})
```

### Mode 3: Hook-Triggered Sync

Auto-suggest sync after code edits (requires hook setup).

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "bash ~/.claude/skills/linear/hooks/post-edit.sh"
      }]
    }]
  }
}
```

The hook detects Linear issue references in changed files and outputs context for Claude to consider syncing.

## Updating Project Status

`sync.ts` does not touch projects. Update a project's status with `linear-ops.ts`:

```bash
# By project name (partial match works)
npx tsx scripts/linear-ops.ts project-status "Current Phase" completed

# Other states: backlog, planned, in-progress, paused, canceled
npx tsx scripts/linear-ops.ts project-status "Current Phase" in-progress
```

See [projects.md](projects.md) for the full project lifecycle.

## Parallel Agent Pattern

Spawn multiple sync agents for independent issue batches (single message, multiple Task calls):

```javascript
[
  Task({
    description: "Sync ENG-432-437",
    prompt: "Run: npx tsx scripts/sync.ts --issues ENG-432,ENG-433,ENG-434,ENG-435,ENG-436,ENG-437 --state Done",
    subagent_type: "Linear-specialist"
  }),
  Task({
    description: "Sync ENG-441-448",
    prompt: "Run: npx tsx scripts/sync.ts --issues ENG-441,ENG-442,ENG-443,ENG-444,ENG-446,ENG-447,ENG-448 --state Done",
    subagent_type: "Linear-specialist"
  }),
  Task({
    description: "Update project status",
    prompt: "Run: npx tsx scripts/linear-ops.ts project-status \"Current Phase\" completed",
    subagent_type: "Linear-specialist"
  })
]
```

## Verification

`sync.ts` prints a per-issue result and a final `📊 Summary` line (and exits non-zero if any issue failed), so the run itself is the first check. To verify independently, query the issues:

```bash
npx tsx scripts/query.ts 'query { issues(filter: { number: { in: [432,433,434] } }) { nodes { identifier state { name } } } }'
```

Or, for typed verification in a script, use the SDK (`client.issues({ filter: { ... } })` — see [sdk.md](sdk.md)).

## Error Handling

`sync.ts` is resilient by design:

- **Rate limiting**: 150ms delay between issue mutations
- **Partial failure**: reports each issue individually and summarizes succeeded/failed counts
- **Not found**: a missing identifier is reported and counted as failed, not fatal
- **`--dry-run`**: shows the current → target state transition without writing

## Common Workflows

### Post-Implementation Sync

After completing a feature:

```bash
# 1. Identify issues from git commits
git log --oneline -10 | grep -oE 'ENG-[0-9]+'

# 2. Preview, then bulk update to Done
npx tsx scripts/sync.ts --issues ENG-432,ENG-433,ENG-434 --state Done --dry-run
npx tsx scripts/sync.ts --issues ENG-432,ENG-433,ENG-434 --state Done

# 3. Update project status
npx tsx scripts/linear-ops.ts project-status "Current Phase" completed
```

### Phase Completion Sync

When closing out a phase:

```bash
# Review issues still open in the phase
npx tsx scripts/linear-ops.ts list-projects
# (then inspect the project in Linear to see which issues remain)

# Bulk update implemented issues
npx tsx scripts/sync.ts --issues ENG-432,ENG-433,ENG-472 --state Done

# Mark the project completed
npx tsx scripts/linear-ops.ts project-status "Current Phase" completed
```

### PR Preparation Sync

Before creating a PR, move the referenced issues to your review state:

```bash
npx tsx scripts/sync.ts --issues ENG-432,ENG-433 --state "In Review"
```

## Reference

- **SKILL.md**: Main Linear skill documentation
- **api.md**: GraphQL API reference (raw GraphQL via the SDK's `rawRequest`)
- **sdk.md**: SDK automation patterns
- **projects.md**: Project & initiative management (including `project-status`)
- **scripts/sync.ts**: Sync script implementation
