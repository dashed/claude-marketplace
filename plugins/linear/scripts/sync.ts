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

interface SyncOptions {
  issues: string[];
  state: string;
  comment?: string;
  dryRun: boolean;
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

  // Extract team key from first issue identifier
  const teamKey = options.issues[0]?.split('-')[0];
  if (!teamKey) {
    console.error('Error: Could not extract team key from issue identifier');
    process.exit(1);
  }

  // Find the target workflow state
  console.log(`🔎 Looking up workflow state "${options.state}" for team ${teamKey}...`);

  const team = await client.team(teamKey);
  const states = await team.states();
  const targetState = states.nodes.find(
    (s) => s.name.toLowerCase() === options.state.toLowerCase(),
  );

  if (!targetState) {
    console.error(`\n❌ Error: State "${options.state}" not found`);
    console.error('\nAvailable states:');
    states.nodes.forEach((s) => console.error(`  - ${s.name}`));
    process.exit(1);
  }

  console.log(`✅ Found state: ${targetState.name} (${targetState.id})\n`);

  // Process each issue
  const results: { identifier: string; success: boolean; error?: string }[] = [];

  for (const identifier of options.issues) {
    process.stdout.write(`  ${identifier}: `);

    try {
      // Fetch the issue by identifier
      const issueNumber = parseInt(identifier.split('-')[1] ?? '0', 10);
      const issuesResult = await client.issues({
        filter: {
          team: { key: { eq: teamKey } },
          number: { eq: issueNumber },
        },
      });

      const issue = issuesResult.nodes[0];
      if (!issue) {
        console.log('❌ Not found');
        results.push({ identifier, success: false, error: 'Not found' });
        continue;
      }

      if (options.dryRun) {
        const currentState = await issue.state;
        console.log(`Would update from "${currentState?.name}" → "${targetState.name}"`);
        results.push({ identifier, success: true });
        continue;
      }

      // Update the issue state
      await issue.update({ stateId: targetState.id });

      // Add comment if provided
      if (options.comment) {
        await client.createComment({ issueId: issue.id, body: options.comment });
      }

      console.log(`✅ Updated to "${targetState.name}"${options.comment ? ' + comment' : ''}`);
      results.push({ identifier, success: true });

      // Small delay to avoid rate limiting
      await new Promise((resolve) => setTimeout(resolve, 150));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.log(`❌ ${errorMessage}`);
      results.push({ identifier, success: false, error: errorMessage });
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
  console.error('Error:', error.message);
  process.exit(1);
});
