/**
 * Project status resolution
 *
 * Linear's modern project lifecycle is driven by workspace-defined
 * ProjectStatus rows (each with a `type` such as backlog/started/completed),
 * not the deprecated `Project.state` string. These helpers resolve a status by
 * its category type so callers can pass `{ statusId }` to `updateProject`.
 */
import { LinearClient, ProjectStatus, ProjectStatusType } from '@linear/sdk';

/** Lowercase and strip non-alphanumerics so "in-progress" matches "In Progress". */
function normalizeName(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]/g, '');
}

/**
 * Find the workspace ProjectStatus whose category matches the given type.
 *
 * A workspace may define several statuses of the same type — e.g. a kanban
 * setup where "To Do", "In Progress", and "Blocked" are all `started` — so a
 * bare type lookup can land on a surprising status. When `preferredName` is
 * given, a same-type status whose normalized name matches it wins; otherwise
 * the one with the lowest `position` (first in the workspace's configured
 * order) is picked deterministically. Returns null if the workspace has no
 * status of that type.
 */
export async function findProjectStatusByType(
  client: LinearClient,
  type: ProjectStatusType,
  preferredName?: string,
): Promise<ProjectStatus | null> {
  const statuses = await client.projectStatuses();
  const matching = statuses.nodes.filter((s) => s.type === type);
  if (matching.length === 0) {
    return null;
  }
  if (preferredName) {
    const wanted = normalizeName(preferredName);
    const byName = matching.find((s) => normalizeName(s.name) === wanted);
    if (byName) {
      return byName;
    }
  }
  matching.sort((a, b) => a.position - b.position);
  return matching[0];
}
