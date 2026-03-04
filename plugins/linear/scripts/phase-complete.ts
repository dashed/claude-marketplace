#!/usr/bin/env npx tsx

/**
 * Phase Completion Workflow
 *
 * Automates the complete phase/project completion process:
 * 1. Looks up project by name (fuzzy matching)
 * 2. Verifies all issues are completed
 * 3. Updates project status to Completed
 * 4. Creates a completion summary project update
 * 5. Optionally archives the project
 *
 * Usage:
 *   LINEAR_API_KEY=lin_api_xxx npx tsx phase-complete.ts "Phase 1: Foundation"
 *   LINEAR_API_KEY=lin_api_xxx npx tsx phase-complete.ts "Phase 1" --archive
 *   LINEAR_API_KEY=lin_api_xxx npx tsx phase-complete.ts "Phase 1" --force
 *   LINEAR_API_KEY=lin_api_xxx npx tsx phase-complete.ts "Phase 1" --dry-run
 */

import { LinearClient } from '@linear/sdk';
import { EXIT_CODES } from './lib/exit-codes.js';
import { getLinearClient, findProjectByName as findProjectByNameBase } from './lib/linear-utils.js';

interface ProjectStatus {
  id: string;
  name: string;
  type: string;
}

interface IssueState {
  name: string;
  type: string;
}

interface Issue {
  identifier: string;
  title: string;
  state: IssueState;
}

interface Project {
  id: string;
  name: string;
  slugId: string;
  status: ProjectStatus | null;
  issues: {
    nodes: Issue[];
  };
}

interface Options {
  projectName: string;
  archive: boolean;
  force: boolean;
  dryRun: boolean;
}

function parseArgs(): Options {
  const args = process.argv.slice(2);
  const options: Options = {
    projectName: '',
    archive: false,
    force: false,
    dryRun: false,
  };

  for (const arg of args) {
    if (arg === '--archive') {
      options.archive = true;
    } else if (arg === '--force') {
      options.force = true;
    } else if (arg === '--dry-run') {
      options.dryRun = true;
    } else if (!arg.startsWith('-')) {
      options.projectName = arg;
    }
  }

  return options;
}

function printUsage(): void {
  console.error(`
Phase Completion Workflow - Automate project/phase completion

Usage:
  LINEAR_API_KEY=xxx npx tsx phase-complete.ts "<project-name>" [options]

Options:
  --archive    Archive the project after completion
  --force      Complete even if some issues aren't done
  --dry-run    Show what would happen without making changes

Examples:
  # Complete a phase
  npx tsx phase-complete.ts "Phase 1: Foundation"

  # Complete and archive
  npx tsx phase-complete.ts "Phase 1" --archive

  # Force complete with incomplete issues
  npx tsx phase-complete.ts "Phase 1" --force

  # Preview what would happen
  npx tsx phase-complete.ts "Phase 1" --dry-run
`);
}

async function findProjectByName(
  client: LinearClient,
  searchName: string,
): Promise<Project | null> {
  // Use shared utility for case-insensitive lookup with exact match preference
  const projectInfo = await findProjectByNameBase(client, searchName);

  if (!projectInfo) {
    return null;
  }

  // Fetch full project details with issues
  return fetchProjectDetails(client, projectInfo.id);
}

async function fetchProjectDetailsOptimized(
  client: LinearClient,
  projectId: string,
): Promise<Project> {
  // Single GraphQL query to fetch project + status + issues with states
  const result = await client.client.rawRequest<
    {
      project: {
        id: string;
        name: string;
        slugId: string;
        status: { id: string; name: string; type: string } | null;
        issues: {
          nodes: Array<{
            identifier: string;
            title: string;
            state: { name: string; type: string } | null;
          }>;
        };
      };
    },
    { projectId: string }
  >(
    `
    query GetProjectDetails($projectId: String!) {
      project(id: $projectId) {
        id
        name
        slugId
        status {
          id
          name
          type
        }
        issues {
          nodes {
            identifier
            title
            state {
              name
              type
            }
          }
        }
      }
    }
  `,
    { projectId },
  );

  const project = result.data?.project;
  if (!project) {
    throw new Error(`Project not found: ${projectId}`);
  }

  return {
    id: project.id,
    name: project.name,
    slugId: project.slugId,
    status: project.status
      ? {
          id: project.status.id,
          name: project.status.name,
          type: project.status.type,
        }
      : null,
    issues: {
      nodes: project.issues.nodes.map((issue) => ({
        identifier: issue.identifier,
        title: issue.title,
        state: issue.state
          ? { name: issue.state.name, type: issue.state.type }
          : { name: 'Unknown', type: 'unknown' },
      })),
    },
  };
}

async function fetchProjectDetails(client: LinearClient, projectId: string): Promise<Project> {
  return fetchProjectDetailsOptimized(client, projectId);
}

async function getCompletedStatus(client: LinearClient): Promise<ProjectStatus | null> {
  // Fetch all project statuses and find "Completed"
  const result = await client.client.rawRequest<
    {
      projectStatuses: { nodes: ProjectStatus[] };
    },
    Record<string, never>
  >(`
    query {
      projectStatuses {
        nodes {
          id
          name
          type
        }
      }
    }
  `);

  const statuses = result.data?.projectStatuses?.nodes || [];
  return statuses.find((s) => s.type === 'completed') || null;
}

async function updateProjectStatus(
  client: LinearClient,
  projectId: string,
  statusId: string,
): Promise<boolean> {
  const result = await client.client.rawRequest<
    {
      projectUpdate: { success: boolean };
    },
    { id: string; statusId: string }
  >(
    `
    mutation UpdateProjectStatus($id: String!, $statusId: String!) {
      projectUpdate(id: $id, input: { statusId: $statusId }) {
        success
        project {
          name
          status { name }
        }
      }
    }
  `,
    { id: projectId, statusId },
  );

  return result.data?.projectUpdate?.success || false;
}

async function createProjectUpdate(
  client: LinearClient,
  projectId: string,
  body: string,
): Promise<string | null> {
  const result = await client.client.rawRequest<
    {
      projectUpdateCreate: {
        success: boolean;
        projectUpdate: { id: string; url: string };
      };
    },
    { projectId: string; body: string }
  >(
    `
    mutation CreateProjectUpdate($projectId: String!, $body: String!) {
      projectUpdateCreate(input: {
        projectId: $projectId,
        body: $body,
        health: onTrack
      }) {
        success
        projectUpdate {
          id
          url
        }
      }
    }
  `,
    { projectId, body },
  );

  return result.data?.projectUpdateCreate?.projectUpdate?.url || null;
}

async function archiveProject(client: LinearClient, projectId: string): Promise<boolean> {
  const result = await client.client.rawRequest<
    {
      projectArchive: { success: boolean };
    },
    { id: string }
  >(
    `
    mutation ArchiveProject($id: String!) {
      projectArchive(id: $id) {
        success
      }
    }
  `,
    { id: projectId },
  );

  return result.data?.projectArchive?.success || false;
}

function generateCompletionSummary(project: Project): string {
  const issues = project.issues.nodes;
  const completed = issues.filter((i) => i.state.type === 'completed');
  const cancelled = issues.filter((i) => i.state.type === 'canceled');
  const remaining = issues.filter(
    (i) => i.state.type !== 'completed' && i.state.type !== 'canceled',
  );

  const completedList = completed.map((i) => `- ${i.identifier}: ${i.title}`).join('\n');

  const cancelledList =
    cancelled.length > 0
      ? `\n\n### Cancelled\n${cancelled.map((i) => `- ${i.identifier}: ${i.title}`).join('\n')}`
      : '';

  const remainingList =
    remaining.length > 0
      ? `\n\n### Not Completed\n${remaining.map((i) => `- ${i.identifier}: ${i.title} [${i.state.name}]`).join('\n')}`
      : '';

  return `## Phase Completed

**${project.name}** has been marked as completed.

### Summary
- **Total Issues**: ${issues.length}
- **Completed**: ${completed.length}
- **Cancelled**: ${cancelled.length}
${remaining.length > 0 ? `- **Remaining**: ${remaining.length} (force-completed)` : ''}

### Completed Issues
${completedList || '_No issues_'}${cancelledList}${remainingList}

---
_Completed on ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}_`;
}

async function main(): Promise<void> {
  const options = parseArgs();

  if (!options.projectName) {
    console.error('Error: Project name is required');
    printUsage();
    process.exit(EXIT_CODES.INVALID_ARGUMENTS);
  }

  let client: LinearClient;
  try {
    client = getLinearClient();
  } catch (error) {
    console.error(`Error: ${(error as Error).message}`);
    printUsage();
    process.exit(EXIT_CODES.MISSING_API_KEY);
  }

  console.log(`\nSearching for project: "${options.projectName}"...`);

  // Step 1: Find project by name
  const project = await findProjectByName(client, options.projectName);

  if (!project) {
    console.error(`\nError: No project found matching "${options.projectName}"`);
    console.error('\nTip: Use partial name matching, e.g., "Phase 1" instead of full name');
    process.exit(EXIT_CODES.RESOURCE_NOT_FOUND);
  }

  console.log(`\nFound project: ${project.name}`);
  console.log(`  ID: ${project.id}`);
  console.log(`  Current status: ${project.status?.name || 'None'}`);
  console.log(`  Issues: ${project.issues.nodes.length}`);

  // Step 2: Check issue completion status
  const issues = project.issues.nodes;
  const completedIssues = issues.filter(
    (i) => i.state.type === 'completed' || i.state.type === 'canceled',
  );
  const incompleteIssues = issues.filter(
    (i) => i.state.type !== 'completed' && i.state.type !== 'canceled',
  );

  console.log(`\nIssue Status:`);
  console.log(`  Completed/Cancelled: ${completedIssues.length}/${issues.length}`);

  if (incompleteIssues.length > 0) {
    console.log(`\n  Incomplete issues:`);
    for (const issue of incompleteIssues) {
      console.log(`    - ${issue.identifier}: ${issue.title} [${issue.state.name}]`);
    }

    if (!options.force) {
      console.error(`\nError: ${incompleteIssues.length} issues are not completed.`);
      console.error('Use --force to complete anyway, or finish the issues first.');
      process.exit(EXIT_CODES.VALIDATION_ERROR);
    }

    console.log('\n  --force flag set, continuing with incomplete issues...');
  }

  // Step 3: Get Completed status
  const completedStatus = await getCompletedStatus(client);

  if (!completedStatus) {
    console.error('\nError: Could not find "Completed" status in workspace');
    process.exit(EXIT_CODES.RESOURCE_NOT_FOUND);
  }

  console.log(`\nCompleted status ID: ${completedStatus.id}`);

  // Step 4: Generate completion summary
  const summary = generateCompletionSummary(project);

  if (options.dryRun) {
    console.log('\n--- DRY RUN MODE ---');
    console.log('\nWould perform:');
    console.log(`  1. Update project status to "${completedStatus.name}"`);
    console.log('  2. Create project update with summary:');
    console.log(
      '\n' +
        summary
          .split('\n')
          .map((l) => '     ' + l)
          .join('\n'),
    );
    if (options.archive) {
      console.log('  3. Archive the project');
    }
    console.log('\nNo changes made.');
    process.exit(0);
  }

  // Step 5: Update project status
  console.log(`\nUpdating project status to "${completedStatus.name}"...`);
  const statusUpdated = await updateProjectStatus(client, project.id, completedStatus.id);

  if (!statusUpdated) {
    console.error('Error: Failed to update project status');
    process.exit(EXIT_CODES.API_ERROR);
  }
  console.log('  Status updated successfully');

  // Step 6: Create project update
  console.log('\nCreating completion summary...');
  const updateUrl = await createProjectUpdate(client, project.id, summary);

  if (updateUrl) {
    console.log(`  Project update created: ${updateUrl}`);
  } else {
    console.log('  Project update created (no URL returned)');
  }

  // Step 7: Archive if requested
  if (options.archive) {
    console.log('\nArchiving project...');
    const archived = await archiveProject(client, project.id);

    if (archived) {
      console.log('  Project archived successfully');
    } else {
      console.error('  Warning: Failed to archive project');
    }
  }

  console.log('\n--- Phase Completion Successful ---');
  console.log(`Project "${project.name}" is now marked as Completed.`);
}

main().catch((error) => {
  console.error('Error:', error.message);
  if (error.errors) {
    console.error('GraphQL Errors:', JSON.stringify(error.errors, null, 2));
  }
  process.exit(EXIT_CODES.API_ERROR);
});
