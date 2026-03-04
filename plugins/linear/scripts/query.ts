#!/usr/bin/env npx tsx

/**
 * Execute ad-hoc GraphQL queries against the Linear API
 *
 * Usage:
 *   LINEAR_API_KEY=lin_api_xxx npx tsx query.ts "query { viewer { id name } }"
 *   LINEAR_API_KEY=lin_api_xxx npx tsx query.ts "query { viewer { id name } }" '{"var": "value"}'
 */

import { LinearClient } from '@linear/sdk';

interface GraphQLErrorResponse {
  errors: Array<{
    message: string;
    locations?: Array<{ line: number; column: number }>;
    path?: Array<string | number>;
  }>;
}

function hasGraphQLErrors(error: unknown): error is Error & GraphQLErrorResponse {
  return (
    error instanceof Error &&
    'errors' in error &&
    Array.isArray((error as Record<string, unknown>).errors)
  );
}

async function main() {
  const apiKey = process.env.LINEAR_API_KEY;

  if (!apiKey) {
    console.error('\n========================================');
    console.error('  LINEAR_API_KEY Not Found');
    console.error('========================================\n');
    console.error('To fix this:\n');
    console.error('  1. Go to Linear -> Settings -> Security & access -> Personal API keys');
    console.error('  2. Click "Create key" and copy the key (starts with lin_api_)');
    console.error('  3. Set it in your environment:\n');
    console.error('     # Option A: Export in current shell');
    console.error('     export LINEAR_API_KEY="lin_api_your_key_here"\n');
    console.error('     # Option B: Add to shell profile (~/.zshrc or ~/.bashrc)');
    console.error('     echo \'export LINEAR_API_KEY="lin_api_..."\' >> ~/.zshrc\n');
    console.error('     # Option C: Add to Claude Code environment');
    console.error("     echo 'LINEAR_API_KEY=lin_api_...' >> ~/.claude/.env\n");
    console.error('Or run the full setup check:');
    console.error('  npx tsx setup.ts\n');
    console.error('Usage once configured:');
    console.error('  npx tsx query.ts "query { viewer { id name } }"\n');
    process.exit(1);
  }

  // Validate key format
  if (!apiKey.startsWith('lin_api_')) {
    console.error('\n[WARNING] LINEAR_API_KEY has unexpected format');
    console.error('Expected format: lin_api_... (got: ' + apiKey.substring(0, 10) + '...)');
    console.error('This may cause authentication failures.\n');
  }

  const query = process.argv[2];
  const variablesArg = process.argv[3];

  if (!query) {
    console.error('Error: Query argument is required');
    console.error('');
    console.error('Usage:');
    console.error('  LINEAR_API_KEY=lin_api_xxx npx tsx query.ts "query { viewer { id name } }"');
    console.error(
      '  LINEAR_API_KEY=lin_api_xxx npx tsx query.ts "query($id: String!) { issue(id: $id) { title } }" \'{"id": "ISSUE_ID"}\'',
    );
    process.exit(1);
  }

  let variables = {};
  if (variablesArg) {
    try {
      variables = JSON.parse(variablesArg);
    } catch (_error) {
      console.error('Error: Variables must be valid JSON');
      console.error(`Received: ${variablesArg}`);
      process.exit(1);
    }
  }

  const client = new LinearClient({ apiKey });

  try {
    const result = await client.client.rawRequest(query, variables);
    console.log(JSON.stringify(result.data, null, 2));
  } catch (error) {
    console.error('Error executing query:');

    if (hasGraphQLErrors(error)) {
      console.error(error.message);
      console.error('\nGraphQL Errors:');
      console.error(JSON.stringify(error.errors, null, 2));
    } else if (error instanceof Error) {
      console.error(error.message);
    } else {
      console.error(error);
    }

    process.exit(1);
  }
}

main();
