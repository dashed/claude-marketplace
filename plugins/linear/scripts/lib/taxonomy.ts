/**
 * Label Taxonomy Type Definitions
 *
 * TypeScript interfaces for the domain-based label taxonomy system.
 * These types ensure consistent label definitions across the codebase.
 */

/**
 * Label categories (groups in Linear)
 */
export type LabelCategory = 'domain' | 'type' | 'scope';

/**
 * Domain labels for agent self-selection
 */
export type DomainLabel =
  | 'security'
  | 'performance'
  | 'infrastructure'
  | 'testing'
  | 'reliability'
  | 'core'
  | 'frontend'
  | 'backend'
  | 'integration'
  | 'documentation'
  | 'mcp'
  | 'cli'
  | 'neural';

/**
 * Type labels for work classification (exactly one required per issue)
 */
export type TypeLabel = 'feature' | 'bug' | 'refactor' | 'chore' | 'spike';

/**
 * Scope labels for impact flags (0-2 per issue)
 */
export type ScopeLabel =
  | 'breaking-change'
  | 'tech-debt'
  | 'blocked'
  | 'needs-split'
  | 'good-first-issue'
  | 'enterprise'
  | 'soc2';

/**
 * All taxonomy label names
 */
export type TaxonomyLabel = DomainLabel | TypeLabel | ScopeLabel;

/**
 * Agent identifiers for routing
 */
export type AgentId =
  // Security agents
  | 'security-manager'
  | 'byzantine-coordinator'
  // Performance agents
  | 'performance-benchmarker'
  | 'perf-analyzer'
  // Infrastructure agents
  | 'swarm-init'
  | 'mesh-coordinator'
  // Testing agents
  | 'tester'
  | 'tdd-london-swarm'
  // Reliability agents
  | 'raft-manager'
  | 'gossip-coordinator'
  // Development agents
  | 'coder'
  | 'sparc-coder'
  | 'frontend-dev'
  | 'ui-designer'
  | 'backend-dev'
  | 'api-designer'
  | 'integration-specialist'
  | 'mcp-developer'
  | 'tool-builder'
  | 'cli-developer'
  // AI/ML agents
  | 'safla-neural'
  | 'collective-intelligence'
  // Documentation agents
  | 'researcher'
  // Review agents
  | 'reviewer'
  | 'planner';

/**
 * Definition of a single label in the taxonomy
 */
export interface LabelDefinition {
  /** Label name (lowercase, hyphenated) */
  name: TaxonomyLabel;
  /** Category this label belongs to */
  category: LabelCategory;
  /** Human-readable description for Linear AI triage */
  description: string;
  /** Hex color code (with #) */
  color: string;
  /** Primary agents that should handle this label (first choice) */
  primaryAgents?: AgentId[];
  /** Secondary agents as fallback */
  secondaryAgents?: AgentId[];
}

/**
 * Complete taxonomy structure
 */
export interface LabelTaxonomy {
  /** Domain labels for technical area routing */
  domain: Record<DomainLabel, LabelDefinition>;
  /** Type labels for work classification */
  type: Record<TypeLabel, LabelDefinition>;
  /** Scope labels for impact flags */
  scope: Record<ScopeLabel, LabelDefinition>;
}

/**
 * Validation result for a set of labels
 */
export interface ValidationResult {
  /** Whether the label set is valid */
  valid: boolean;
  /** Error messages if invalid */
  errors: string[];
  /** Warning messages (valid but suboptimal) */
  warnings: string[];
  /** Parsed labels by category */
  parsed: {
    domain: DomainLabel[];
    type: TypeLabel[];
    scope: ScopeLabel[];
    unknown: string[];
  };
}

/**
 * Label suggestion result
 */
export interface LabelSuggestion {
  /** Suggested label */
  label: TaxonomyLabel;
  /** Category of the label */
  category: LabelCategory;
  /** Confidence score (0-1) */
  confidence: number;
  /** Reason for the suggestion */
  reason: string;
}

/**
 * Agent selection result
 */
export interface AgentSelection {
  /** Primary agents recommended for this work */
  primary: AgentId[];
  /** Secondary/fallback agents */
  secondary: AgentId[];
  /** All labels considered in selection */
  labels: TaxonomyLabel[];
  /** Reasoning for selection */
  reasoning: string;
}
