/**
 * Shared Linear API utilities
 *
 * Common patterns extracted from Linear scripts for consistent
 * API key validation, entity lookups, and type definitions.
 */

import { LinearClient } from '@linear/sdk';

// ============================================================================
// Types
// ============================================================================

/**
 * Health status for project and initiative updates
 */
export type HealthStatus = 'onTrack' | 'atRisk' | 'offTrack';

/**
 * Valid health status values
 */
export const VALID_HEALTH_VALUES: readonly HealthStatus[] = [
  'onTrack',
  'atRisk',
  'offTrack',
] as const;

/**
 * Project information returned by findProjectByName
 */
export interface ProjectInfo {
  id: string;
  name: string;
  slugId: string;
}

/**
 * Initiative information returned by findInitiativeByName
 */
export interface InitiativeInfo {
  id: string;
  name: string;
  description?: string;
}

/**
 * Team information returned by findTeamByKey
 */
export interface TeamInfo {
  id: string;
  key: string;
  name: string;
}

// ============================================================================
// Type Guards
// ============================================================================

/**
 * Type guard to check if a string is a valid health status
 */
export function isValidHealth(value: string): value is HealthStatus {
  return VALID_HEALTH_VALUES.includes(value as HealthStatus);
}

// ============================================================================
// Client Initialization
// ============================================================================

/**
 * Create a LinearClient instance with the provided API key
 *
 * @param apiKey Linear API key
 * @returns LinearClient instance
 */
export function createLinearClient(apiKey: string): LinearClient {
  return new LinearClient({ apiKey });
}

/**
 * Get a LinearClient instance with API key validation
 *
 * Reads the API key from LINEAR_API_KEY environment variable.
 *
 * @throws Error if LINEAR_API_KEY environment variable is not set
 * @returns LinearClient instance
 */
export function getLinearClient(): LinearClient {
  const apiKey = process.env.LINEAR_API_KEY;

  if (!apiKey) {
    throw new Error('LINEAR_API_KEY environment variable is required');
  }

  return createLinearClient(apiKey);
}

// ============================================================================
// Entity Lookups
// ============================================================================

/**
 * Find a project by name with exact-match preference
 *
 * Searches for projects with case-insensitive partial matching.
 * If multiple matches are found, prefers exact match (case-insensitive).
 *
 * @param client LinearClient instance
 * @param name Project name to search for
 * @returns ProjectInfo or null if not found
 */
export async function findProjectByName(
  client: LinearClient,
  name: string,
): Promise<ProjectInfo | null> {
  const projects = await client.projects({
    filter: {
      name: { containsIgnoreCase: name },
    },
    first: 10,
  });

  if (projects.nodes.length === 0) {
    return null;
  }

  // Prefer exact match (case-insensitive)
  const exactMatch = projects.nodes.find((p) => p.name.toLowerCase() === name.toLowerCase());

  const project = exactMatch || projects.nodes[0];
  return {
    id: project.id,
    name: project.name,
    slugId: project.slugId,
  };
}

/**
 * Find an initiative by name with exact-match preference
 *
 * Searches for initiatives with case-insensitive partial matching.
 * If multiple matches are found, prefers exact match (case-insensitive).
 *
 * @param client LinearClient instance
 * @param name Initiative name to search for
 * @returns InitiativeInfo or null if not found
 */
export async function findInitiativeByName(
  client: LinearClient,
  name: string,
): Promise<InitiativeInfo | null> {
  const initiatives = await client.initiatives({
    filter: {
      name: { containsIgnoreCase: name },
    },
    first: 10,
  });

  if (initiatives.nodes.length === 0) {
    return null;
  }

  // Prefer exact match (case-insensitive)
  const match =
    initiatives.nodes.find((i) => i.name.toLowerCase() === name.toLowerCase()) ||
    initiatives.nodes[0];

  return {
    id: match.id,
    name: match.name,
    description: match.description ?? undefined,
  };
}

/**
 * Find a team by its key (e.g., "ENG", "PRODUCT")
 *
 * @param client LinearClient instance
 * @param key Team key to search for (case-insensitive)
 * @returns TeamInfo or null if not found
 */
export async function findTeamByKey(client: LinearClient, key: string): Promise<TeamInfo | null> {
  const teams = await client.teams({
    filter: {
      key: { eq: key.toUpperCase() },
    },
    first: 1,
  });

  const team = teams.nodes[0];
  if (!team) {
    return null;
  }

  return { id: team.id, key: team.key, name: team.name };
}

/**
 * Find a team by name with case-insensitive matching
 *
 * Searches for teams with case-insensitive partial matching.
 * If multiple matches are found, prefers exact match (case-insensitive).
 *
 * @param client LinearClient instance
 * @param name Team name to search for
 * @returns TeamInfo or null if not found
 */
export async function findTeamByName(client: LinearClient, name: string): Promise<TeamInfo | null> {
  const teams = await client.teams({
    filter: {
      name: { containsIgnoreCase: name },
    },
    first: 10,
  });

  if (teams.nodes.length === 0) {
    return null;
  }

  // Prefer exact match (case-insensitive)
  const match =
    teams.nodes.find((t) => t.name.toLowerCase() === name.toLowerCase()) || teams.nodes[0];

  return { id: match.id, key: match.key, name: match.name };
}
