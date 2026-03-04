/**
 * Label Taxonomy Data
 *
 * Complete label definitions for the domain-based taxonomy system.
 * Each label includes:
 * - Human-readable description (for Linear's Triage Intelligence)
 * - Color (for visual consistency)
 * - Agent mappings (for self-selection routing)
 */

import type {
  LabelTaxonomy,
  LabelDefinition,
  DomainLabel,
  TypeLabel,
  ScopeLabel,
  TaxonomyLabel,
} from './taxonomy';

/**
 * Domain Labels - Technical area for agent routing
 *
 * These labels drive which agents pick up work.
 * Each has primary agents (first choice) and secondary agents (backup).
 */
const DOMAIN_LABELS: Record<DomainLabel, LabelDefinition> = {
  security: {
    name: 'security',
    category: 'domain',
    description: 'Security vulnerabilities, authentication, encryption, access control',
    color: '#D73A4A',
    primaryAgents: ['security-manager', 'byzantine-coordinator'],
    secondaryAgents: ['reviewer', 'tester'],
  },
  performance: {
    name: 'performance',
    category: 'domain',
    description: 'Performance optimization, benchmarking, latency, profiling',
    color: '#FBCA04',
    primaryAgents: ['performance-benchmarker', 'perf-analyzer'],
    secondaryAgents: ['coder', 'reviewer'],
  },
  infrastructure: {
    name: 'infrastructure',
    category: 'domain',
    description: 'CI/CD, deployment, Docker, cloud, DevOps tooling',
    color: '#0E8A16',
    primaryAgents: ['swarm-init', 'mesh-coordinator'],
    secondaryAgents: ['coder', 'planner'],
  },
  testing: {
    name: 'testing',
    category: 'domain',
    description: 'Test coverage, test infrastructure, QA automation',
    color: '#1D76DB',
    primaryAgents: ['tester', 'tdd-london-swarm'],
    secondaryAgents: ['reviewer'],
  },
  reliability: {
    name: 'reliability',
    category: 'domain',
    description: 'Fault tolerance, consensus, distributed systems',
    color: '#5319E7',
    primaryAgents: ['raft-manager', 'gossip-coordinator'],
    secondaryAgents: ['tester'],
  },
  core: {
    name: 'core',
    category: 'domain',
    description: 'Core business logic and system functionality',
    color: '#0075CA',
    primaryAgents: ['coder', 'sparc-coder'],
    secondaryAgents: ['reviewer', 'tester'],
  },
  frontend: {
    name: 'frontend',
    category: 'domain',
    description: 'UI/UX, React, CSS, user-facing components',
    color: '#10B981',
    primaryAgents: ['frontend-dev', 'ui-designer'],
    secondaryAgents: ['reviewer', 'tester'],
  },
  backend: {
    name: 'backend',
    category: 'domain',
    description: 'Server-side logic, APIs, database operations',
    color: '#1D76DB',
    primaryAgents: ['backend-dev', 'api-designer'],
    secondaryAgents: ['reviewer', 'tester'],
  },
  integration: {
    name: 'integration',
    category: 'domain',
    description: 'Third-party APIs, external service integrations',
    color: '#7057FF',
    primaryAgents: ['integration-specialist'],
    secondaryAgents: ['coder', 'reviewer'],
  },
  documentation: {
    name: 'documentation',
    category: 'domain',
    description: 'Docs, guides, API documentation, comments',
    color: '#0075CA',
    primaryAgents: ['researcher'],
    secondaryAgents: ['reviewer'],
  },
  mcp: {
    name: 'mcp',
    category: 'domain',
    description: 'Model Context Protocol tools and servers',
    color: '#006B75',
    primaryAgents: ['mcp-developer', 'tool-builder'],
    secondaryAgents: ['coder', 'reviewer'],
  },
  cli: {
    name: 'cli',
    category: 'domain',
    description: 'Command-line interfaces and terminal tools',
    color: '#E99695',
    primaryAgents: ['cli-developer'],
    secondaryAgents: ['coder', 'tester'],
  },
  neural: {
    name: 'neural',
    category: 'domain',
    description: 'AI/ML components, neural networks, inference',
    color: '#D4C5F9',
    primaryAgents: ['safla-neural', 'collective-intelligence'],
    secondaryAgents: ['researcher', 'coder'],
  },
};

/**
 * Type Labels - Work classification
 *
 * Exactly one type label is required per issue.
 * These define the nature of the work being done.
 */
const TYPE_LABELS: Record<TypeLabel, LabelDefinition> = {
  feature: {
    name: 'feature',
    category: 'type',
    description: 'New functionality or capability being added',
    color: '#A2EEEF',
  },
  bug: {
    name: 'bug',
    category: 'type',
    description: 'Defect causing incorrect behavior that needs fixing',
    color: '#D73A4A',
  },
  refactor: {
    name: 'refactor',
    category: 'type',
    description: 'Code improvement without changing external behavior',
    color: '#D4C5F9',
  },
  chore: {
    name: 'chore',
    category: 'type',
    description: 'Maintenance, dependencies, tooling updates',
    color: '#FEF2C0',
  },
  spike: {
    name: 'spike',
    category: 'type',
    description: 'Research, investigation, or prototyping task',
    color: '#FBCA04',
  },
};

/**
 * Scope Labels - Impact flags
 *
 * Optional labels (0-2 per issue) that flag special conditions.
 */
const SCOPE_LABELS: Record<ScopeLabel, LabelDefinition> = {
  'breaking-change': {
    name: 'breaking-change',
    category: 'scope',
    description: 'Changes that break backward compatibility',
    color: '#B60205',
  },
  'tech-debt': {
    name: 'tech-debt',
    category: 'scope',
    description: 'Technical debt that should be addressed',
    color: '#5319E7',
  },
  blocked: {
    name: 'blocked',
    category: 'scope',
    description: 'Work blocked by external dependency',
    color: '#D73A4A',
  },
  'needs-split': {
    name: 'needs-split',
    category: 'scope',
    description: 'Issue too large and needs breakdown',
    color: '#FBCA04',
  },
  'good-first-issue': {
    name: 'good-first-issue',
    category: 'scope',
    description: 'Suitable for newcomers to the codebase',
    color: '#7057FF',
  },
  enterprise: {
    name: 'enterprise',
    category: 'scope',
    description: 'Enterprise-tier specific feature',
    color: '#7057FF',
  },
  soc2: {
    name: 'soc2',
    category: 'scope',
    description: 'SOC2 compliance requirement',
    color: '#0052CC',
  },
};

/**
 * Complete Label Taxonomy
 *
 * The authoritative source for all taxonomy labels.
 */
export const LABEL_TAXONOMY: LabelTaxonomy = {
  domain: DOMAIN_LABELS,
  type: TYPE_LABELS,
  scope: SCOPE_LABELS,
};

/**
 * Get all taxonomy labels as a flat array
 */
export function getAllLabels(): LabelDefinition[] {
  return [
    ...Object.values(DOMAIN_LABELS),
    ...Object.values(TYPE_LABELS),
    ...Object.values(SCOPE_LABELS),
  ];
}

/**
 * Get all taxonomy label names
 */
export function getAllLabelNames(): TaxonomyLabel[] {
  return getAllLabels().map((l) => l.name);
}

/**
 * Get a label by name (case-insensitive)
 */
export function getLabelByName(name: string): LabelDefinition | undefined {
  const normalizedName = name.toLowerCase().trim();
  return getAllLabels().find((l) => l.name === normalizedName);
}

/**
 * Check if a label name is in the taxonomy
 */
export function isValidLabel(name: string): boolean {
  return getLabelByName(name) !== undefined;
}

/**
 * Get labels by category
 */
export function getLabelsByCategory(category: 'domain' | 'type' | 'scope'): LabelDefinition[] {
  switch (category) {
    case 'domain':
      return Object.values(DOMAIN_LABELS);
    case 'type':
      return Object.values(TYPE_LABELS);
    case 'scope':
      return Object.values(SCOPE_LABELS);
  }
}

/**
 * Get color for a label (for creating in Linear)
 * Falls back to default gray if not found
 */
export function getLabelColor(name: string): string {
  const label = getLabelByName(name);
  return label?.color || '#6B7280';
}

/**
 * Build a lookup map of label name -> color
 * Useful for batch operations
 */
export function buildColorMap(): Record<string, string> {
  const map: Record<string, string> = {};
  for (const label of getAllLabels()) {
    map[label.name] = label.color;
  }
  return map;
}

/**
 * Domain label names (exported for convenience)
 */
export const DOMAIN_LABEL_NAMES: DomainLabel[] = Object.keys(DOMAIN_LABELS) as DomainLabel[];

/**
 * Type label names (exported for convenience)
 */
export const TYPE_LABEL_NAMES: TypeLabel[] = Object.keys(TYPE_LABELS) as TypeLabel[];

/**
 * Scope label names (exported for convenience)
 */
export const SCOPE_LABEL_NAMES: ScopeLabel[] = Object.keys(SCOPE_LABELS) as ScopeLabel[];
