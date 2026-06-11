/**
 * Project status resolution
 *
 * Linear's modern project lifecycle is driven by workspace-defined
 * ProjectStatus rows (each with a `type` such as backlog/started/completed),
 * not the deprecated `Project.state` string. These helpers resolve a status by
 * its category type so callers can pass `{ statusId }` to `updateProject`.
 */
import { LinearClient, ProjectStatus, ProjectStatusType } from '@linear/sdk';

/**
 * Find the workspace ProjectStatus whose category matches the given type.
 *
 * A workspace may define several statuses of the same type (e.g. "Done" and
 * "Released", both `completed`); the one with the lowest `position` — first in
 * the workspace's configured order — is picked deterministically. Returns null
 * if the workspace has no status of that type.
 */
export async function findProjectStatusByType(
  client: LinearClient,
  type: ProjectStatusType,
): Promise<ProjectStatus | null> {
  const statuses = await client.projectStatuses();
  const matching = statuses.nodes.filter((s) => s.type === type);
  if (matching.length === 0) {
    return null;
  }
  matching.sort((a, b) => a.position - b.position);
  return matching[0];
}
