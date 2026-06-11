#!/usr/bin/env npx tsx

/**
 * Create an initiative update (status report) in Linear
 *
 * Looks up initiative by name, posts markdown content, and returns the update URL.
 *
 * Usage:
 *   LINEAR_API_KEY=lin_api_xxx npx tsx create-initiative-update.ts "Initiative Name" "## Update\n\nBody content" [health]
 *
 * Arguments:
 *   initiativeName - Name of the initiative (case-insensitive partial match)
 *   body           - Markdown content for the update
 *   health         - Optional: onTrack (default), atRisk, offTrack
 *
 * Examples:
 *   npx tsx create-initiative-update.ts "Q1 Goals" "## Progress\n\n- 3/5 projects complete"
 *   npx tsx create-initiative-update.ts "Product Launch" "## At Risk\n\nBlocked on dependency" atRisk
 */

import { LinearClient, InitiativeUpdateHealthType } from '@linear/sdk';
import { EXIT_CODES } from './lib/exit-codes.js';
import {
  HealthStatus,
  VALID_HEALTH_VALUES,
  isValidHealth,
  getLinearClient,
  findInitiativeByName,
} from './lib/linear-utils.js';
import { formatLinearError } from './lib/errors.js';

/**
 * Map our user-facing health vocabulary to the SDK's InitiativeUpdateHealthType
 * enum. The enum's values are identical strings, so this is a safe lookup.
 */
const HEALTH_TYPE_MAP: Record<HealthStatus, InitiativeUpdateHealthType> = {
  onTrack: InitiativeUpdateHealthType.OnTrack,
  atRisk: InitiativeUpdateHealthType.AtRisk,
  offTrack: InitiativeUpdateHealthType.OffTrack,
};

function printUsage(): void {
  console.error('Usage:');
  console.error(
    '  LINEAR_API_KEY=lin_api_xxx npx tsx create-initiative-update.ts "Initiative Name" "Body content" [health]',
  );
  console.error('');
  console.error('Arguments:');
  console.error('  initiativeName - Name of the initiative (case-insensitive partial match)');
  console.error('  body           - Markdown content for the update');
  console.error('  health         - Optional: onTrack (default), atRisk, offTrack');
  console.error('');
  console.error('Examples:');
  console.error(
    '  npx tsx create-initiative-update.ts "Q1 Goals" "## Progress\\n\\n- 3/5 projects done"',
  );
  console.error(
    '  npx tsx create-initiative-update.ts "Product Launch" "## Blocked\\n\\nDependency issue" atRisk',
  );
}

interface InitiativeUpdateResult {
  success: boolean;
  initiativeUpdate?: {
    id: string;
    url: string;
    createdAt: string;
  };
}

async function createInitiativeUpdate(
  client: LinearClient,
  initiativeId: string,
  body: string,
  health: HealthStatus,
): Promise<InitiativeUpdateResult> {
  const payload = await client.createInitiativeUpdate({
    initiativeId,
    body,
    health: HEALTH_TYPE_MAP[health],
  });

  const update = await payload.initiativeUpdate;
  return {
    success: payload.success,
    initiativeUpdate: update
      ? {
          id: update.id,
          url: update.url,
          createdAt: update.createdAt.toISOString(),
        }
      : undefined,
  };
}

async function main(): Promise<void> {
  const initiativeName = process.argv[2];
  const body = process.argv[3];
  const healthArg = process.argv[4] || 'onTrack';

  if (!initiativeName) {
    console.error('Error: Initiative name is required');
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

  // Step 1: Look up initiative by name
  console.log(`Looking up initiative: "${initiativeName}"...`);
  const initiative = await findInitiativeByName(client, initiativeName);

  if (!initiative) {
    console.error(`Error: Initiative not found matching "${initiativeName}"`);
    console.error('');
    console.error('Tip: List all initiatives with:');
    console.error(
      '  LINEAR_API_KEY=xxx npx tsx scripts/query.ts "query { initiatives { nodes { id name } } }"',
    );
    process.exit(EXIT_CODES.RESOURCE_NOT_FOUND);
  }

  console.log(`Found initiative: ${initiative.name} (${initiative.id})`);

  // Step 2: Create the initiative update
  console.log(`Creating update with health: ${healthArg}...`);

  try {
    const result = await createInitiativeUpdate(client, initiative.id, body, healthArg);

    if (!result.success || !result.initiativeUpdate) {
      console.error('Error: Failed to create initiative update');
      console.error('The API returned success: false');
      process.exit(EXIT_CODES.API_ERROR);
    }

    // Step 3: Output success with URL
    console.log('');
    console.log('Initiative update created successfully!');
    console.log('');
    console.log(`URL: ${result.initiativeUpdate.url}`);
    console.log(`ID: ${result.initiativeUpdate.id}`);
    console.log(`Created: ${result.initiativeUpdate.createdAt}`);
    console.log(`Health: ${healthArg}`);

    // Also output as JSON for programmatic use
    console.log('');
    console.log('JSON Output:');
    console.log(
      JSON.stringify(
        {
          success: true,
          initiative: {
            id: initiative.id,
            name: initiative.name,
          },
          update: result.initiativeUpdate,
          health: healthArg,
        },
        null,
        2,
      ),
    );
  } catch (error) {
    console.error('Error creating initiative update:');
    console.error(formatLinearError(error));
    process.exit(EXIT_CODES.API_ERROR);
  }
}

main();
