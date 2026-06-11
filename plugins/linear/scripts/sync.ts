#!/usr/bin/env npx tsx

/**
 * Bulk sync Linear issues to a target state
 *
 * Usage:
 *   LINEAR_API_KEY=lin_api_xxx npx tsx sync.ts --issues ENG-432,ENG-433,ENG-434 --state Done
 *   LINEAR_API_KEY=lin_api_xxx npx tsx sync.ts --issues ENG-432 --state "In Progress"
 *   LINEAR_API_KEY=lin_api_xxx npx tsx sync.ts --issues ENG-432,ENG-433 --state Done --comment "Completed in PR #42"
 *
 * Options:
 *   --issues    Comma-separated issue identifiers (e.g., ENG-432,ENG-433)
 *   --state     Target state name (e.g., Done, "In Progress", Backlog)
 *   --comment   Optional comment to add to each issue
 *   --dry-run   Preview changes without applying them
 */

import { LinearClient } from '@linear/sdk';
import { formatLinearError } from './lib/errors.js';

interface SyncOptions {
  issues: string[];
  state: string;
  comment?: string;
  dryRun: boolean;
}

interface ResolvedState {
  id: string;
  name: string;
}

function parseArgs(): SyncOptions {
  const args = process.argv.slice(2);
  const options: SyncOptions = {
    issues: [],
    state: '',
    comment: undefined,
    dryRun: false,
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--issues':
        options.issues = args[++i]?.split(',').map((s) => s.trim()) ?? [];
        break;
      case '--state':
        options.state = args[++i] ?? '';
        break;
      case '--comment':
        options.comment = args[++i];
        break;
      case '--dry-run':
        options.dryRun = true;
        break;
    }
  }

  return options;
}

function printUsage(): void {
  console.error('Usage:');
  console.error(
    '  LINEAR_API_KEY=lin_api_xxx npx tsx sync.ts --issues ENG-432,ENG-433 --state Done',
  );
  console.error('');
  console.error('Options:');
  console.error('  --issues    Comma-separated issue identifiers (required)');
  console.error('  --state     Target state name (required)');
  console.error('  --comment   Optional comment to add to each issue');
  console.error('  --dry-run   Preview changes without applying them');
}

async function main() {
  const apiKey = process.env.LINEAR_API_KEY;

  if (!apiKey) {
    console.error('Error: LINEAR_API_KEY environment variable is required');
    console.error('');
    printUsage();
    process.exit(1);
  }

  const options = parseArgs();

  if (options.issues.length === 0) {
    console.error('Error: --issues is required');
    console.error('');
    printUsage();
    process.exit(1);
  }

  if (!options.state) {
    console.error('Error: --state is required');
    console.error('');
    printUsage();
    process.exit(1);
  }

  const client = new LinearClient({ apiKey });

  console.log(`\n📋 Syncing ${options.issues.length} issue(s) to "${options.state}"...`);
  if (options.dryRun) {
    console.log('🔍 DRY RUN - no changes will be applied\n');
  }

  // Caches keyed by team key so repeated lookups are cheap and the target
  // workflow state is resolved per team (states are team-scoped).
  const targetStateByTeam = new Map<string, ResolvedState | null>();

  async function resolveTargetState(teamKey: string): Promise<ResolvedState | null> {
    if (targetStateByTeam.has(teamKey)) {
      return targetStateByTeam.get(teamKey) ?? null;
    }

    let resolved: ResolvedState | null = null;
    try {
      const team = await client.team(teamKey);
      const states = await team.states();
      const match = states.nodes.find((s) => s.name.toLowerCase() === options.state.toLowerCase());
      if (match) {
        resolved = { id: match.id, name: match.name };
      } else {
        console.error(`\n❌ State "${options.state}" not found for team ${teamKey}`);
        console.error('   Available states:');
        states.nodes.forEach((s) => console.error(`     - ${s.name}`));
      }
    } catch (error) {
      console.error(`\n❌ Could not look up team ${teamKey}: ${formatLinearError(error)}`);
    }

    targetStateByTeam.set(teamKey, resolved);
    return resolved;
  }

  const results: { identifier: string; success: boolean; error?: string }[] = [];

  // Step 1: Resolve every issue to its id + target stateId (per-identifier team
  // key, so mixed-team batches are handled correctly).
  interface Resolved {
    identifier: string;
    issueId: string;
    currentStateName?: string;
    stateId: string;
  }
  const resolved: Resolved[] = [];

  for (const identifier of options.issues) {
    const teamKey = identifier.split('-')[0];
    const issueNumber = parseInt(identifier.split('-')[1] ?? '0', 10);

    if (!teamKey || !issueNumber) {
      console.log(`  ${identifier}: ❌ Invalid identifier`);
      results.push({ identifier, success: false, error: 'Invalid identifier' });
      continue;
    }

    const targetState = await resolveTargetState(teamKey);
    if (!targetState) {
      results.push({ identifier, success: false, error: `State "${options.state}" not found` });
      continue;
    }

    try {
      const issuesResult = await client.issues({
        filter: {
          team: { key: { eq: teamKey } },
          number: { eq: issueNumber },
        },
      });

      const issue = issuesResult.nodes[0];
      if (!issue) {
        console.log(`  ${identifier}: ❌ Not found`);
        results.push({ identifier, success: false, error: 'Not found' });
        continue;
      }

      if (options.dryRun) {
        const currentState = await issue.state;
        console.log(
          `  ${identifier}: Would update from "${currentState?.name}" → "${targetState.name}"`,
        );
        results.push({ identifier, success: true });
        continue;
      }

      resolved.push({
        identifier,
        issueId: issue.id,
        stateId: targetState.id,
      });
    } catch (error) {
      const message = formatLinearError(error);
      console.log(`  ${identifier}: ❌ ${message}`);
      results.push({ identifier, success: false, error: message });
    }
  }

  // Step 2: Apply state updates in batches grouped by target stateId (one
  // updateIssueBatch call per state instead of a per-issue update loop).
  if (!options.dryRun && resolved.length > 0) {
    const byStateId = new Map<string, Resolved[]>();
    for (const r of resolved) {
      const group = byStateId.get(r.stateId);
      if (group) {
        group.push(r);
      } else {
        byStateId.set(r.stateId, [r]);
      }
    }

    for (const [stateId, group] of byStateId) {
      try {
        await client.updateIssueBatch(
          group.map((r) => r.issueId),
          { stateId },
        );
        for (const r of group) {
          console.log(`  ${r.identifier}: ✅ Updated to "${options.state}"`);
          results.push({ identifier: r.identifier, success: true });
        }
      } catch (error) {
        const message = formatLinearError(error);
        for (const r of group) {
          console.log(`  ${r.identifier}: ❌ ${message}`);
          results.push({ identifier: r.identifier, success: false, error: message });
        }
      }
    }

    // Step 3: Add comments per-issue if requested (no batch API for comments).
    if (options.comment) {
      const succeeded = new Set(results.filter((r) => r.success).map((r) => r.identifier));
      for (const r of resolved) {
        if (!succeeded.has(r.identifier)) continue;
        try {
          await client.createComment({ issueId: r.issueId, body: options.comment });
          console.log(`  ${r.identifier}: 💬 comment added`);
        } catch (error) {
          console.log(`  ${r.identifier}: ⚠️  comment failed: ${formatLinearError(error)}`);
        }
      }
    }
  }

  // Summary
  const successful = results.filter((r) => r.success).length;
  const failed = results.filter((r) => !r.success).length;

  console.log(`\n${'─'.repeat(40)}`);
  console.log(`📊 Summary: ${successful} succeeded, ${failed} failed`);

  if (failed > 0) {
    console.log('\nFailed issues:');
    results.filter((r) => !r.success).forEach((r) => console.log(`  ${r.identifier}: ${r.error}`));
    process.exit(1);
  }

  console.log('');
}

main().catch((error) => {
  console.error('Error:', formatLinearError(error));
  process.exit(1);
});
