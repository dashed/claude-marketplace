/**
 * Label Taxonomy Validation
 *
 * Validates labels against the taxonomy rules and suggests labels
 * based on issue title/description content.
 */

import type {
  ValidationResult,
  LabelSuggestion,
  DomainLabel,
  TypeLabel,
  ScopeLabel,
  TaxonomyLabel,
  LabelCategory,
} from './taxonomy';

// Re-export types for consumers
export type { ValidationResult, LabelSuggestion };

import { getLabelByName, DOMAIN_LABEL_NAMES, TYPE_LABEL_NAMES } from './taxonomy-data';

/**
 * Validate a set of labels against taxonomy rules
 *
 * Rules:
 * 1. Exactly one Type label is required
 * 2. 1-2 Domain labels recommended
 * 3. 0-2 Scope labels allowed
 * 4. No unknown labels
 */
export function validateLabels(labels: string[]): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const parsed: ValidationResult['parsed'] = {
    domain: [],
    type: [],
    scope: [],
    unknown: [],
  };

  // Normalize and categorize labels
  for (const label of labels) {
    const normalized = label.toLowerCase().trim();
    const definition = getLabelByName(normalized);

    if (!definition) {
      parsed.unknown.push(normalized);
      continue;
    }

    switch (definition.category) {
      case 'domain':
        parsed.domain.push(normalized as DomainLabel);
        break;
      case 'type':
        parsed.type.push(normalized as TypeLabel);
        break;
      case 'scope':
        parsed.scope.push(normalized as ScopeLabel);
        break;
    }
  }

  // Validation rules

  // Rule 1: Exactly one Type label required
  if (parsed.type.length === 0) {
    errors.push('Missing required Type label (feature, bug, refactor, chore, or spike)');
  } else if (parsed.type.length > 1) {
    errors.push(`Multiple Type labels not allowed: ${parsed.type.join(', ')}`);
  }

  // Rule 2: At least one Domain label recommended
  if (parsed.domain.length === 0) {
    warnings.push(
      'No Domain label specified. Consider adding one for agent routing (e.g., security, backend, frontend)',
    );
  } else if (parsed.domain.length > 2) {
    warnings.push(
      `More than 2 Domain labels may indicate scope creep: ${parsed.domain.join(', ')}`,
    );
  }

  // Rule 3: Scope labels are optional but limited
  if (parsed.scope.length > 2) {
    warnings.push(`More than 2 Scope labels may be excessive: ${parsed.scope.join(', ')}`);
  }

  // Rule 4: Unknown labels are errors
  if (parsed.unknown.length > 0) {
    errors.push(`Unknown labels not in taxonomy: ${parsed.unknown.join(', ')}`);
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
    parsed,
  };
}

/**
 * Keyword patterns for label suggestion
 */
const LABEL_KEYWORDS: Record<TaxonomyLabel, string[]> = {
  // Domain labels
  security: [
    'security',
    'auth',
    'authentication',
    'authorization',
    'encrypt',
    'vulnerability',
    'xss',
    'csrf',
    'sql injection',
    'owasp',
    'token',
    'jwt',
    'password',
    'access control',
  ],
  performance: [
    'performance',
    'speed',
    'slow',
    'fast',
    'latency',
    'benchmark',
    'profil',
    'optimi',
    'memory',
    'cpu',
    'cache',
  ],
  infrastructure: [
    'ci',
    'cd',
    'deploy',
    'docker',
    'kubernetes',
    'k8s',
    'devops',
    'pipeline',
    'github action',
    'workflow',
    'terraform',
    'aws',
    'gcp',
    'azure',
  ],
  testing: [
    'test',
    'spec',
    'coverage',
    'unit test',
    'integration test',
    'e2e',
    'playwright',
    'jest',
    'vitest',
    'qa',
    'assertion',
  ],
  reliability: [
    'reliability',
    'fault',
    'consensus',
    'distributed',
    'raft',
    'gossip',
    'failover',
    'redundan',
    'resilient',
  ],
  core: ['core', 'business logic', 'domain', 'model', 'service', 'entity'],
  frontend: [
    'ui',
    'ux',
    'react',
    'component',
    'css',
    'style',
    'button',
    'form',
    'modal',
    'layout',
    'responsive',
    'tailwind',
  ],
  backend: [
    'api',
    'endpoint',
    'server',
    'database',
    'db',
    'query',
    'migration',
    'graphql',
    'rest',
    'route',
    'middleware',
  ],
  integration: [
    'integration',
    'third-party',
    'external',
    'webhook',
    'oauth',
    'stripe',
    'slack',
    'discord',
  ],
  documentation: ['doc', 'readme', 'guide', 'tutorial', 'comment', 'jsdoc', 'markdown'],
  mcp: ['mcp', 'model context protocol', 'tool', 'server'],
  cli: ['cli', 'command', 'terminal', 'shell', 'argv', 'flag', 'argument'],
  neural: ['ai', 'ml', 'neural', 'model', 'inference', 'llm', 'embedding', 'vector'],

  // Type labels
  feature: ['feature', 'add', 'new', 'implement', 'create', 'introduce', 'support'],
  bug: ['bug', 'fix', 'broken', 'error', 'crash', 'fail', 'issue', 'problem', 'incorrect', 'wrong'],
  refactor: ['refactor', 'clean', 'reorganize', 'restructure', 'simplify', 'extract', 'rename'],
  chore: [
    'chore',
    'update',
    'upgrade',
    'dependency',
    'dependencies',
    'maintenance',
    'housekeeping',
    'bump',
  ],
  spike: [
    'spike',
    'research',
    'investigate',
    'explore',
    'prototype',
    'poc',
    'proof of concept',
    'experiment',
  ],

  // Scope labels
  'breaking-change': ['breaking', 'migration', 'incompatible', 'major change'],
  'tech-debt': ['tech debt', 'technical debt', 'debt', 'legacy', 'cleanup'],
  blocked: ['blocked', 'waiting', 'depends on', 'dependency', 'external'],
  'needs-split': ['large', 'complex', 'multiple', 'split', 'breakdown', 'epic'],
  'good-first-issue': ['beginner', 'starter', 'simple', 'easy', 'first issue', 'good first'],
  enterprise: ['enterprise', 'paid', 'premium', 'pro', 'team plan'],
  soc2: ['soc2', 'compliance', 'audit', 'security requirement'],
};

/**
 * Suggest labels based on issue title and description
 *
 * @param title - Issue title
 * @param description - Optional issue description
 * @returns Array of suggested labels with confidence scores
 */
export function suggestLabels(title: string, description?: string): LabelSuggestion[] {
  const text = `${title} ${description || ''}`.toLowerCase();
  const suggestions: LabelSuggestion[] = [];

  for (const [labelName, keywords] of Object.entries(LABEL_KEYWORDS)) {
    let matchCount = 0;
    const matchedKeywords: string[] = [];

    for (const keyword of keywords) {
      if (text.includes(keyword)) {
        matchCount++;
        matchedKeywords.push(keyword);
      }
    }

    if (matchCount > 0) {
      const definition = getLabelByName(labelName);
      if (definition) {
        // Calculate confidence based on match ratio and total matches
        const matchRatio = matchCount / keywords.length;
        const confidence = Math.min(0.95, matchRatio * 2 + (matchCount - 1) * 0.1);

        suggestions.push({
          label: labelName as TaxonomyLabel,
          category: definition.category,
          confidence,
          reason: `Matched keywords: ${matchedKeywords.slice(0, 3).join(', ')}${matchedKeywords.length > 3 ? '...' : ''}`,
        });
      }
    }
  }

  // Sort by confidence descending
  suggestions.sort((a, b) => b.confidence - a.confidence);

  // Apply category limits
  const result: LabelSuggestion[] = [];
  let typeCount = 0;
  let domainCount = 0;
  let scopeCount = 0;

  for (const suggestion of suggestions) {
    switch (suggestion.category) {
      case 'type':
        if (typeCount < 1) {
          result.push(suggestion);
          typeCount++;
        }
        break;
      case 'domain':
        if (domainCount < 2) {
          result.push(suggestion);
          domainCount++;
        }
        break;
      case 'scope':
        if (scopeCount < 2) {
          result.push(suggestion);
          scopeCount++;
        }
        break;
    }
  }

  return result;
}

/**
 * Get the category of a label
 */
export function getLabelCategory(name: string): LabelCategory | undefined {
  const definition = getLabelByName(name);
  return definition?.category;
}

/**
 * Check if labels include exactly one Type label
 */
export function hasValidTypeLabel(labels: string[]): boolean {
  const typeLabels = labels
    .map((l) => l.toLowerCase().trim())
    .filter((l) => TYPE_LABEL_NAMES.includes(l as TypeLabel));
  return typeLabels.length === 1;
}

/**
 * Check if labels include at least one Domain label
 */
export function hasDomainLabel(labels: string[]): boolean {
  const domainLabels = labels
    .map((l) => l.toLowerCase().trim())
    .filter((l) => DOMAIN_LABEL_NAMES.includes(l as DomainLabel));
  return domainLabels.length > 0;
}

/**
 * Filter labels to only taxonomy labels (removes unknown)
 */
export function filterToTaxonomy(labels: string[]): TaxonomyLabel[] {
  return labels
    .map((l) => l.toLowerCase().trim())
    .filter((l) => getLabelByName(l) !== undefined) as TaxonomyLabel[];
}

/**
 * Format validation result as human-readable string
 */
export function formatValidationResult(result: ValidationResult): string {
  const lines: string[] = [];

  if (result.valid) {
    lines.push('✓ Labels are valid');
  } else {
    lines.push('✗ Labels have errors');
  }

  lines.push('');
  lines.push('Parsed labels:');
  lines.push(`  Type:   ${result.parsed.type.join(', ') || '(none)'}`);
  lines.push(`  Domain: ${result.parsed.domain.join(', ') || '(none)'}`);
  lines.push(`  Scope:  ${result.parsed.scope.join(', ') || '(none)'}`);

  if (result.parsed.unknown.length > 0) {
    lines.push(`  Unknown: ${result.parsed.unknown.join(', ')}`);
  }

  if (result.errors.length > 0) {
    lines.push('');
    lines.push('Errors:');
    for (const error of result.errors) {
      lines.push(`  ✗ ${error}`);
    }
  }

  if (result.warnings.length > 0) {
    lines.push('');
    lines.push('Warnings:');
    for (const warning of result.warnings) {
      lines.push(`  ⚠ ${warning}`);
    }
  }

  return lines.join('\n');
}

/**
 * Format label suggestions as human-readable string
 */
export function formatSuggestions(suggestions: LabelSuggestion[]): string {
  if (suggestions.length === 0) {
    return 'No label suggestions found.';
  }

  const lines: string[] = ['Suggested labels:', ''];

  // Group by category
  const byCategory: Record<string, LabelSuggestion[]> = {
    type: [],
    domain: [],
    scope: [],
  };

  for (const s of suggestions) {
    byCategory[s.category].push(s);
  }

  for (const [category, items] of Object.entries(byCategory)) {
    if (items.length > 0) {
      lines.push(`${category.charAt(0).toUpperCase() + category.slice(1)}:`);
      for (const item of items) {
        const confidence = Math.round(item.confidence * 100);
        lines.push(`  • ${item.label} (${confidence}%)`);
        lines.push(`    ${item.reason}`);
      }
      lines.push('');
    }
  }

  return lines.join('\n');
}
