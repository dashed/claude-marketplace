/**
 * Initiative Linking Utilities
 *
 * MANDATORY: Every project MUST be linked to an initiative.
 * This module ensures projects are properly connected.
 */
import { LinearClient } from '@linear/sdk';
import { fileURLToPath } from 'url';
import { formatLinearError } from './errors';

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY });

// Default initiative ID - set via environment or override in function calls
// Users should set LINEAR_DEFAULT_INITIATIVE_ID in their environment
export const DEFAULT_INITIATIVE_ID = process.env.LINEAR_DEFAULT_INITIATIVE_ID || '';

// Legacy export for backwards compatibility (deprecated)
export const INITIATIVES = {
  DEFAULT: DEFAULT_INITIATIVE_ID,
} as const;

/**
 * Link a project to an initiative using the typed createInitiativeToProject SDK call.
 *
 * This is the ONLY correct way to link projects. Do NOT use:
 * - projectUpdate with initiativeIds (doesn't exist)
 * - projectCreate with initiativeId (deprecated)
 */
export async function linkProjectToInitiative(
  projectId: string,
  initiativeId: string,
): Promise<{ success: boolean; error?: string }> {
  try {
    const payload = await client.createInitiativeToProject({ initiativeId, projectId });
    return { success: payload.success === true };
  } catch (error) {
    // Already-linked is not an error condition for our purposes.
    const message = formatLinearError(error);
    if (message.includes('already exists')) {
      return { success: true };
    }
    return { success: false, error: message };
  }
}

/**
 * Check if a project is linked to an initiative
 *
 * Note: Linear uses initiativeToProject edges, not a direct initiative field.
 * We query the project's linked initiatives to check membership.
 */
export async function isProjectLinkedToInitiative(
  projectId: string,
  initiativeId: string,
): Promise<boolean> {
  try {
    const project = await client.project(projectId);
    const initiatives = await project.initiatives();
    return initiatives.nodes.some((i) => i.id === initiativeId);
  } catch {
    return false;
  }
}

/**
 * Get all projects and their initiative links
 *
 * Paginates over every project so workspaces with more than one page of
 * projects are fully covered.
 */
export async function getProjectInitiativeStatus(): Promise<
  Array<{ id: string; name: string; initiative: string | null }>
> {
  const projects = await client.paginate((variables) => client.projects(variables), { first: 100 });

  const results: Array<{ id: string; name: string; initiative: string | null }> = [];
  for (const proj of projects) {
    const initiatives = await proj.initiatives();
    const initiative = initiatives.nodes[0];
    results.push({
      id: proj.id,
      name: proj.name,
      initiative: initiative?.name || null,
    });
  }

  return results;
}

/**
 * Link all projects matching a filter to an initiative
 *
 * @param initiativeId - The initiative to link projects to
 * @param projectFilter - Optional filter (e.g., { name: { contains: 'MyProject' } })
 */
export async function linkProjectsToInitiative(
  initiativeId: string,
  projectFilter?: { name?: { contains?: string; eq?: string } },
): Promise<{
  linked: string[];
  failed: string[];
  alreadyLinked: string[];
}> {
  if (!initiativeId) {
    throw new Error(
      'initiativeId is required. Set LINEAR_DEFAULT_INITIATIVE_ID or pass explicitly.',
    );
  }

  const projects = await client.projects(projectFilter ? { filter: projectFilter } : undefined);

  const linked: string[] = [];
  const failed: string[] = [];
  const alreadyLinked: string[] = [];

  for (const proj of projects.nodes) {
    // Check if already linked
    const isLinked = await isProjectLinkedToInitiative(proj.id, initiativeId);
    if (isLinked) {
      alreadyLinked.push(proj.name);
      continue;
    }

    // Link to initiative
    const result = await linkProjectToInitiative(proj.id, initiativeId);
    if (result.success) {
      linked.push(proj.name);
    } else {
      failed.push(`${proj.name}: ${result.error}`);
    }
  }

  return { linked, failed, alreadyLinked };
}

// CLI entry point
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  async function main() {
    const command = process.argv[2];
    const initiativeId = process.argv[3] || DEFAULT_INITIATIVE_ID;
    const projectFilter = process.argv[4];

    if (command === 'link') {
      if (!initiativeId) {
        console.log('Usage: initiative.ts link <initiativeId> [projectNameFilter]');
        console.log('Or set LINEAR_DEFAULT_INITIATIVE_ID environment variable');
        process.exit(1);
      }

      console.log(`=== Linking Projects to Initiative ${initiativeId} ===\n`);

      const filter = projectFilter ? { name: { contains: projectFilter } } : undefined;
      const result = await linkProjectsToInitiative(initiativeId, filter);

      if (result.alreadyLinked.length > 0) {
        console.log('Already linked:');
        result.alreadyLinked.forEach((p) => console.log(`  ✓ ${p}`));
      }

      if (result.linked.length > 0) {
        console.log('\nNewly linked:');
        result.linked.forEach((p) => console.log(`  ✅ ${p}`));
      }

      if (result.failed.length > 0) {
        console.log('\nFailed:');
        result.failed.forEach((p) => console.log(`  ❌ ${p}`));
      }

      console.log(
        `\nSummary: ${result.linked.length} linked, ${result.alreadyLinked.length} already linked, ${result.failed.length} failed`,
      );
    } else if (command === 'check') {
      const projectId = process.argv[3];
      const checkInitiativeId = process.argv[4] || DEFAULT_INITIATIVE_ID;

      if (!projectId || !checkInitiativeId) {
        console.log('Usage: initiative.ts check <projectId> <initiativeId>');
        process.exit(1);
      }

      const isLinked = await isProjectLinkedToInitiative(projectId, checkInitiativeId);
      console.log(`Project ${projectId} linked to initiative: ${isLinked ? '✓ Yes' : '✗ No'}`);
    } else {
      console.log('Usage:');
      console.log(
        '  initiative.ts link <initiativeId> [projectNameFilter]  - Link projects to initiative',
      );
      console.log(
        '  initiative.ts check <projectId> <initiativeId>         - Check if project is linked',
      );
      console.log('');
      console.log('Environment:');
      console.log('  LINEAR_DEFAULT_INITIATIVE_ID - Default initiative ID');
    }
  }

  main().catch(console.error);
}
