#!/usr/bin/env npx tsx

/**
 * Create a project update (status report) in Linear
 *
 * Looks up project by name, posts markdown content, and returns the update URL.
 *
 * Usage:
 *   LINEAR_API_KEY=lin_api_xxx npx tsx create-project-update.ts "Project Name" "## Update\n\nBody content" [health]
 *
 * Arguments:
 *   projectName - Name of the project (case-insensitive partial match)
 *   body        - Markdown content for the update
 *   health      - Optional: onTrack (default), atRisk, offTrack
 *
 * Examples:
 *   npx tsx create-project-update.ts "Phase 1" "## Progress\n\n- Feature A complete"
 *   npx tsx create-project-update.ts "Phase 1" "## At Risk\n\nBlocked on API" atRisk
 */

import { LinearClient } from '@linear/sdk';
import { EXIT_CODES } from './lib/exit-codes.js';
import {
  HealthStatus,
  VALID_HEALTH_VALUES,
  isValidHealth,
  getLinearClient,
  findProjectByName,
} from './lib/linear-utils.js';

function printUsage(): void {
  console.error('Usage:');
  console.error(
    '  LINEAR_API_KEY=lin_api_xxx npx tsx create-project-update.ts "Project Name" "Body content" [health]',
  );
  console.error('');
  console.error('Arguments:');
  console.error('  projectName - Name of the project (case-insensitive partial match)');
  console.error('  body        - Markdown content for the update');
  console.error('  health      - Optional: onTrack (default), atRisk, offTrack');
  console.error('');
  console.error('Examples:');
  console.error(
    '  npx tsx create-project-update.ts "Phase 1" "## Progress\\n\\n- Feature complete"',
  );
  console.error('  npx tsx create-project-update.ts "Phase 1" "## Blocked\\n\\nAPI issues" atRisk');
}

interface ProjectUpdateResult {
  success: boolean;
  projectUpdate?: {
    id: string;
    url: string;
    createdAt: string;
  };
}

async function createProjectUpdate(
  client: LinearClient,
  projectId: string,
  body: string,
  health: HealthStatus,
): Promise<ProjectUpdateResult> {
  // Use rawRequest since SDK may not have projectUpdateCreate typed
  const mutation = `
    mutation CreateProjectUpdate($projectId: String!, $body: String!, $health: ProjectUpdateHealthType!) {
      projectUpdateCreate(input: {
        projectId: $projectId,
        body: $body,
        health: $health
      }) {
        success
        projectUpdate {
          id
          url
          createdAt
        }
      }
    }
  `;

  const result = await client.client.rawRequest(mutation, {
    projectId,
    body,
    health,
  });

  return (result.data as { projectUpdateCreate: ProjectUpdateResult }).projectUpdateCreate;
}

async function main(): Promise<void> {
  const projectName = process.argv[2];
  const body = process.argv[3];
  const healthArg = process.argv[4] || 'onTrack';

  if (!projectName) {
    console.error('Error: Project name is required');
    console.error('');
    printUsage();
    process.exit(EXIT_CODES.INVALID_ARGUMENTS);
  }

  if (!body) {
    console.error('Error: Update body content is required');
    console.error('');
    printUsage();
    process.exit(EXIT_CODES.INVALID_ARGUMENTS);
  }

  if (!isValidHealth(healthArg)) {
    console.error(`Error: Invalid health value "${healthArg}"`);
    console.error(`Valid values: ${VALID_HEALTH_VALUES.join(', ')}`);
    process.exit(EXIT_CODES.VALIDATION_ERROR);
  }

  let client: LinearClient;
  try {
    client = getLinearClient();
  } catch (error) {
    console.error(`Error: ${(error as Error).message}`);
    console.error('');
    printUsage();
    process.exit(EXIT_CODES.MISSING_API_KEY);
  }

  // Step 1: Look up project by name
  console.log(`Looking up project: "${projectName}"...`);
  const project = await findProjectByName(client, projectName);

  if (!project) {
    console.error(`Error: Project not found matching "${projectName}"`);
    console.error('');
    console.error('Tip: Check project name spelling or use Linear CLI to list projects:');
    console.error('  linear projects list');
    process.exit(EXIT_CODES.RESOURCE_NOT_FOUND);
  }

  console.log(`Found project: ${project.name} (${project.id})`);

  // Step 2: Create the project update
  console.log(`Creating update with health: ${healthArg}...`);

  try {
    const result = await createProjectUpdate(client, project.id, body, healthArg);

    if (!result.success || !result.projectUpdate) {
      console.error('Error: Failed to create project update');
      console.error('The API returned success: false');
      process.exit(EXIT_CODES.API_ERROR);
    }

    // Step 3: Output success with URL
    console.log('');
    console.log('Project update created successfully!');
    console.log('');
    console.log(`URL: ${result.projectUpdate.url}`);
    console.log(`ID: ${result.projectUpdate.id}`);
    console.log(`Created: ${result.projectUpdate.createdAt}`);
    console.log(`Health: ${healthArg}`);

    // Also output as JSON for programmatic use
    console.log('');
    console.log('JSON Output:');
    console.log(
      JSON.stringify(
        {
          success: true,
          project: {
            id: project.id,
            name: project.name,
          },
          update: result.projectUpdate,
          health: healthArg,
        },
        null,
        2,
      ),
    );
  } catch (error) {
    console.error('Error creating project update:');
    if (error instanceof Error) {
      console.error(error.message);

      // Check for common GraphQL errors
      if ('errors' in error && Array.isArray((error as Record<string, unknown>).errors)) {
        console.error('\nGraphQL Errors:');
        console.error(JSON.stringify((error as Record<string, unknown>).errors, null, 2));
      }
    } else {
      console.error(error);
    }
    process.exit(EXIT_CODES.API_ERROR);
  }
}

main();
