#!/usr/bin/env npx tsx

/**
 * Create a Linear issue with project assignment
 *
 * Looks up project by name and creates issue with projectId.
 *
 * Usage:
 *   LINEAR_API_KEY=xxx npx tsx scripts/create-issue-with-project.ts \
 *     --team "ENG" \
 *     --project "Phase 6A" \
 *     --title "Implement feature X" \
 *     --description "Details here"
 *
 * Arguments:
 *   --team        Team key (e.g., "ENG", "PRODUCT")
 *   --project     Project name (exact or partial match)
 *   --title       Issue title (required)
 *   --description Issue description (optional)
 *   --state       Issue state name (optional, defaults to "Backlog")
 *   --assignee    "me" to assign to self (optional)
 *   --priority    1-4 (optional, 1=urgent, 4=low)
 *   --labels      Comma-separated label names (optional)
 */

import { LinearClient } from '@linear/sdk';
import { EXIT_CODES } from './lib/exit-codes.js';
import { getLinearClient, findProjectByName, findTeamByKey } from './lib/linear-utils.js';
import { formatLinearError } from './lib/errors.js';

interface Args {
  team: string;
  project: string;
  title: string;
  description?: string;
  state?: string;
  assignee?: string;
  priority?: number;
  labels?: string[];
}

function parseArgs(): Args {
  const args = process.argv.slice(2);
  const result: Partial<Args> = {};

  for (let i = 0; i < args.length; i += 2) {
    const key = args[i]?.replace(/^--/, '');
    const value = args[i + 1];

    if (!key || value === undefined) continue;

    switch (key) {
      case 'team':
        result.team = value;
        break;
      case 'project':
        result.project = value;
        break;
      case 'title':
        result.title = value;
        break;
      case 'description':
        result.description = value;
        break;
      case 'state':
        result.state = value;
        break;
      case 'assignee':
        result.assignee = value;
        break;
      case 'priority':
        result.priority = parseInt(value, 10);
        break;
      case 'labels':
        result.labels = value.split(',').map((l) => l.trim());
        break;
    }
  }

  if (!result.team || !result.project || !result.title) {
    console.error('Error: --team, --project, and --title are required');
    console.error('');
    console.error('Usage:');
    console.error('  LINEAR_API_KEY=xxx npx tsx scripts/create-issue-with-project.ts \\');
    console.error('    --team "ENG" \\');
    console.error('    --project "Phase 6A" \\');
    console.error('    --title "Implement feature X"');
    process.exit(EXIT_CODES.INVALID_ARGUMENTS);
  }

  return result as Args;
}

async function lookupStateByName(
  client: LinearClient,
  teamId: string,
  stateName: string,
): Promise<string | null> {
  try {
    const states = await client.workflowStates({
      filter: {
        team: { id: { eq: teamId } },
        name: { eq: stateName },
      },
      first: 1,
    });

    return states.nodes[0]?.id || null;
  } catch (error) {
    console.error('Error looking up state:', formatLinearError(error));
    return null;
  }
}

async function lookupLabelIds(
  client: LinearClient,
  teamId: string,
  labelNames: string[],
): Promise<string[]> {
  try {
    const labels = await client.issueLabels({
      filter: {
        team: { id: { eq: teamId } },
        name: { in: labelNames },
      },
      first: 50,
    });

    const foundLabels = labels.nodes;
    const foundNames = foundLabels.map((l) => l.name.toLowerCase());
    const missingLabels = labelNames.filter((name) => !foundNames.includes(name.toLowerCase()));

    if (missingLabels.length > 0) {
      console.warn(`Warning: Labels not found: ${missingLabels.join(', ')}`);
    }

    return foundLabels.map((l) => l.id);
  } catch (error) {
    console.error('Error looking up labels:', formatLinearError(error));
    return [];
  }
}

async function main() {
  let client: LinearClient;
  try {
    client = getLinearClient();
  } catch (error) {
    console.error(`Error: ${(error as Error).message}`);
    process.exit(EXIT_CODES.MISSING_API_KEY);
  }

  const args = parseArgs();

  // Step 1: Look up team
  console.log(`Looking up team "${args.team}"...`);
  const team = await findTeamByKey(client, args.team);
  if (!team) {
    console.error(`Error: Team "${args.team}" not found`);
    process.exit(EXIT_CODES.RESOURCE_NOT_FOUND);
  }
  console.log(`  Found: ${team.name} (${team.key})`);

  // Step 2: Look up project
  console.log(`Looking up project "${args.project}"...`);
  const project = await findProjectByName(client, args.project);
  if (!project) {
    console.error(`Error: Project "${args.project}" not found`);
    console.error('');
    console.error('Available projects can be listed with:');
    console.error(
      '  LINEAR_API_KEY=xxx npx tsx scripts/query.ts "query { projects { nodes { id name } } }"',
    );
    process.exit(EXIT_CODES.RESOURCE_NOT_FOUND);
  }
  console.log(`  Found: ${project.name}`);

  // Step 3: Look up state (if specified)
  let stateId: string | undefined;
  if (args.state) {
    console.log(`Looking up state "${args.state}"...`);
    stateId = (await lookupStateByName(client, team.id, args.state)) || undefined;
    if (!stateId) {
      console.error(`Error: State "${args.state}" not found for team ${team.key}`);
      process.exit(EXIT_CODES.RESOURCE_NOT_FOUND);
    }
    console.log(`  Found state: ${args.state}`);
  }

  // Step 4: Look up labels (if specified)
  let labelIds: string[] | undefined;
  if (args.labels && args.labels.length > 0) {
    console.log(`Looking up labels: ${args.labels.join(', ')}...`);
    labelIds = await lookupLabelIds(client, team.id, args.labels);
    if (labelIds.length > 0) {
      console.log(`  Found ${labelIds.length} label(s)`);
    }
  }

  // Step 5: Get viewer ID if assigning to self
  let assigneeId: string | undefined;
  if (args.assignee === 'me') {
    const viewer = await client.viewer;
    assigneeId = viewer.id;
    console.log(`Assigning to: ${viewer.name}`);
  }

  // Step 6: Create the issue with projectId
  console.log('Creating issue...');

  try {
    const payload = await client.createIssue({
      teamId: team.id,
      title: args.title,
      projectId: project.id,
      ...(args.description && { description: args.description }),
      ...(stateId && { stateId }),
      ...(assigneeId && { assigneeId }),
      ...(args.priority && { priority: args.priority }),
      ...(labelIds && labelIds.length > 0 && { labelIds }),
    });

    const issue = await payload.issue;
    if (payload.success && issue) {
      const output = {
        id: issue.id,
        identifier: issue.identifier,
        title: issue.title,
        url: issue.url,
        // Use the matched project name; the project relation is unchanged here.
        project: { name: project.name },
      };

      console.log('');
      console.log('Issue created successfully!');
      console.log(`  Identifier: ${output.identifier}`);
      console.log(`  Title: ${output.title}`);
      console.log(`  Project: ${output.project.name}`);
      console.log(`  URL: ${output.url}`);
      console.log('');
      console.log(JSON.stringify(output, null, 2));
    } else {
      console.error('Error: Issue creation failed');
      process.exit(EXIT_CODES.API_ERROR);
    }
  } catch (error) {
    console.error('Error creating issue:', formatLinearError(error));
    process.exit(EXIT_CODES.API_ERROR);
  }
}

main();
