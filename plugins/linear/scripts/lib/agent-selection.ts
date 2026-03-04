/**
 * Agent Selection for Issue Routing
 *
 * Determines which agents should handle issues based on their labels.
 * Enables agent self-selection and workload distribution.
 */

import type { AgentSelection, AgentId, DomainLabel, TaxonomyLabel } from './taxonomy';

import { LABEL_TAXONOMY, DOMAIN_LABEL_NAMES } from './taxonomy-data';

/**
 * Agent capability descriptions
 */
export const AGENT_DESCRIPTIONS: Record<AgentId, string> = {
  // Security agents
  'security-manager': 'Security analysis, vulnerability assessment, access control',
  'byzantine-coordinator': 'Byzantine fault tolerance, consensus security',

  // Performance agents
  'performance-benchmarker': 'Performance benchmarking, load testing',
  'perf-analyzer': 'Performance profiling, optimization analysis',

  // Infrastructure agents
  'swarm-init': 'Infrastructure initialization, deployment setup',
  'mesh-coordinator': 'Service mesh, distributed infrastructure',

  // Testing agents
  tester: 'General testing, test writing, coverage',
  'tdd-london-swarm': 'TDD, test-first development, London-style TDD',

  // Reliability agents
  'raft-manager': 'Raft consensus, distributed state management',
  'gossip-coordinator': 'Gossip protocols, eventual consistency',

  // Development agents
  coder: 'General coding, implementation',
  'sparc-coder': 'SPARC methodology coding',
  'frontend-dev': 'Frontend development, React, UI components',
  'ui-designer': 'UI/UX design, styling, accessibility',
  'backend-dev': 'Backend development, APIs, databases',
  'api-designer': 'API design, schema design, contracts',
  'integration-specialist': 'Third-party integrations, external APIs',
  'mcp-developer': 'MCP tool development, protocol implementation',
  'tool-builder': 'Tool creation, CLI development',
  'cli-developer': 'CLI applications, terminal interfaces',

  // AI/ML agents
  'safla-neural': 'Neural network components, ML models',
  'collective-intelligence': 'AI systems, multi-agent coordination',

  // Documentation agents
  researcher: 'Documentation, research, technical writing',

  // Review agents
  reviewer: 'Code review, quality assurance',
  planner: 'Planning, architecture, design',
};

/**
 * Select agents for an issue based on its labels
 *
 * Rules:
 * 1. Primary agent match takes priority
 * 2. Multi-label issues route to agent with broadest match
 * 3. Secondary agents as fallback
 * 4. No domain label = general pool
 */
export function selectAgentsForIssue(labels: string[]): AgentSelection {
  const normalizedLabels = labels.map((l) => l.toLowerCase().trim());

  // Extract domain labels
  const domainLabels = normalizedLabels.filter((l) =>
    DOMAIN_LABEL_NAMES.includes(l as DomainLabel),
  ) as DomainLabel[];

  // If no domain labels, return general agents
  if (domainLabels.length === 0) {
    return {
      primary: ['coder', 'sparc-coder'],
      secondary: ['reviewer', 'tester'],
      labels: normalizedLabels as TaxonomyLabel[],
      reasoning: 'No domain labels specified. Routing to general-purpose agents.',
    };
  }

  // Collect all primary and secondary agents from domain labels
  const primaryAgentCounts = new Map<AgentId, number>();
  const secondaryAgentSet = new Set<AgentId>();

  for (const domainLabel of domainLabels) {
    const definition = LABEL_TAXONOMY.domain[domainLabel];
    if (definition) {
      // Count primary agent occurrences (prefer agents that match multiple domains)
      for (const agent of definition.primaryAgents || []) {
        primaryAgentCounts.set(agent, (primaryAgentCounts.get(agent) || 0) + 1);
      }
      // Collect secondary agents
      for (const agent of definition.secondaryAgents || []) {
        secondaryAgentSet.add(agent);
      }
    }
  }

  // Sort primary agents by match count (most matches first)
  const primaryAgents = Array.from(primaryAgentCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([agent]) => agent);

  // Remove primary agents from secondary set
  for (const agent of primaryAgents) {
    secondaryAgentSet.delete(agent);
  }

  const secondaryAgents = Array.from(secondaryAgentSet);

  // Build reasoning
  let reasoning: string;
  if (domainLabels.length === 1) {
    reasoning = `Single domain "${domainLabels[0]}" routes to ${primaryAgents[0] || 'general'}.`;
  } else {
    const broadMatch = primaryAgents[0];
    const matchCount = primaryAgentCounts.get(broadMatch) || 0;
    if (matchCount > 1) {
      reasoning = `Multiple domains [${domainLabels.join(', ')}]. Agent "${broadMatch}" matches ${matchCount} domains.`;
    } else {
      reasoning = `Multiple domains [${domainLabels.join(', ')}]. Primary agent from first domain: "${broadMatch}".`;
    }
  }

  return {
    primary: primaryAgents,
    secondary: secondaryAgents,
    labels: normalizedLabels as TaxonomyLabel[],
    reasoning,
  };
}

/**
 * Get all labels that an agent can handle
 */
export function getLabelsForAgent(agentId: AgentId): DomainLabel[] {
  const labels: DomainLabel[] = [];

  for (const [labelName, definition] of Object.entries(LABEL_TAXONOMY.domain)) {
    const isPrimary = definition.primaryAgents?.includes(agentId);
    const isSecondary = definition.secondaryAgents?.includes(agentId);

    if (isPrimary || isSecondary) {
      labels.push(labelName as DomainLabel);
    }
  }

  return labels;
}

/**
 * Check if an agent can handle a set of labels
 */
export function canAgentHandle(
  agentId: AgentId,
  labels: string[],
): {
  canHandle: boolean;
  asPrimary: boolean;
  matchedLabels: DomainLabel[];
} {
  const normalizedLabels = labels.map((l) => l.toLowerCase().trim());
  const domainLabels = normalizedLabels.filter((l) =>
    DOMAIN_LABEL_NAMES.includes(l as DomainLabel),
  ) as DomainLabel[];

  // No domain labels means any agent can handle
  if (domainLabels.length === 0) {
    return {
      canHandle: true,
      asPrimary: false,
      matchedLabels: [],
    };
  }

  const matchedLabels: DomainLabel[] = [];
  let isPrimary = false;

  for (const domainLabel of domainLabels) {
    const definition = LABEL_TAXONOMY.domain[domainLabel];
    if (definition) {
      if (definition.primaryAgents?.includes(agentId)) {
        matchedLabels.push(domainLabel);
        isPrimary = true;
      } else if (definition.secondaryAgents?.includes(agentId)) {
        matchedLabels.push(domainLabel);
      }
    }
  }

  return {
    canHandle: matchedLabels.length > 0,
    asPrimary: isPrimary,
    matchedLabels,
  };
}

/**
 * Build the complete agent-domain matrix
 * Shows which agents handle which domains
 */
export function buildAgentDomainMatrix(): Map<
  AgentId,
  {
    primary: DomainLabel[];
    secondary: DomainLabel[];
  }
> {
  const matrix = new Map<AgentId, { primary: DomainLabel[]; secondary: DomainLabel[] }>();

  for (const [labelName, definition] of Object.entries(LABEL_TAXONOMY.domain)) {
    const domainLabel = labelName as DomainLabel;

    // Add primary agents
    for (const agent of definition.primaryAgents || []) {
      if (!matrix.has(agent)) {
        matrix.set(agent, { primary: [], secondary: [] });
      }
      matrix.get(agent)!.primary.push(domainLabel);
    }

    // Add secondary agents
    for (const agent of definition.secondaryAgents || []) {
      if (!matrix.has(agent)) {
        matrix.set(agent, { primary: [], secondary: [] });
      }
      matrix.get(agent)!.secondary.push(domainLabel);
    }
  }

  return matrix;
}

/**
 * Format agent selection result as human-readable string
 */
export function formatAgentSelection(selection: AgentSelection): string {
  const lines: string[] = [];

  lines.push('Agent Selection:');
  lines.push('');

  lines.push('Primary Agents:');
  if (selection.primary.length === 0) {
    lines.push('  (none)');
  } else {
    for (const agent of selection.primary) {
      lines.push(`  • ${agent}`);
      const desc = AGENT_DESCRIPTIONS[agent];
      if (desc) {
        lines.push(`    ${desc}`);
      }
    }
  }

  lines.push('');
  lines.push('Secondary Agents:');
  if (selection.secondary.length === 0) {
    lines.push('  (none)');
  } else {
    for (const agent of selection.secondary) {
      lines.push(`  • ${agent}`);
    }
  }

  lines.push('');
  lines.push(`Reasoning: ${selection.reasoning}`);

  return lines.join('\n');
}

/**
 * Format the agent-domain matrix as a table
 */
export function formatAgentMatrix(): string {
  const matrix = buildAgentDomainMatrix();
  const lines: string[] = [];

  lines.push('Agent-Domain Matrix:');
  lines.push('');

  // Sort agents alphabetically
  const sortedAgents = Array.from(matrix.entries()).sort((a, b) => a[0].localeCompare(b[0]));

  for (const [agent, domains] of sortedAgents) {
    lines.push(`${agent}:`);
    if (domains.primary.length > 0) {
      lines.push(`  Primary:   ${domains.primary.join(', ')}`);
    }
    if (domains.secondary.length > 0) {
      lines.push(`  Secondary: ${domains.secondary.join(', ')}`);
    }
    lines.push('');
  }

  return lines.join('\n');
}
