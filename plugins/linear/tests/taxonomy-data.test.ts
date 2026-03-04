import { describe, it, expect } from 'vitest';
import {
  LABEL_TAXONOMY,
  getAllLabels,
  getAllLabelNames,
  getLabelByName,
  isValidLabel,
  getLabelsByCategory,
  getLabelColor,
  buildColorMap,
  DOMAIN_LABEL_NAMES,
  TYPE_LABEL_NAMES,
  SCOPE_LABEL_NAMES,
} from '../scripts/lib/taxonomy-data';

describe('LABEL_TAXONOMY', () => {
  it('has domain, type, and scope categories', () => {
    expect(LABEL_TAXONOMY).toHaveProperty('domain');
    expect(LABEL_TAXONOMY).toHaveProperty('type');
    expect(LABEL_TAXONOMY).toHaveProperty('scope');
  });

  it('has domain labels', () => {
    expect(Object.keys(LABEL_TAXONOMY.domain).length).toBeGreaterThan(0);
  });

  it('has type labels', () => {
    expect(Object.keys(LABEL_TAXONOMY.type).length).toBeGreaterThan(0);
  });

  it('has scope labels', () => {
    expect(Object.keys(LABEL_TAXONOMY.scope).length).toBeGreaterThan(0);
  });
});

describe('LabelDefinition structure', () => {
  it('every label has required fields', () => {
    for (const label of getAllLabels()) {
      expect(label.name).toBeTruthy();
      expect(typeof label.name).toBe('string');
      expect(label.category).toBeTruthy();
      expect(['domain', 'type', 'scope']).toContain(label.category);
      expect(label.description).toBeTruthy();
      expect(typeof label.description).toBe('string');
      expect(label.color).toBeTruthy();
      expect(label.color).toMatch(/^#[0-9A-Fa-f]{6}$/);
    }
  });

  it('domain labels have agent mappings', () => {
    for (const label of getLabelsByCategory('domain')) {
      expect(label.primaryAgents).toBeDefined();
      expect(Array.isArray(label.primaryAgents)).toBe(true);
      expect(label.primaryAgents!.length).toBeGreaterThan(0);
    }
  });

  it('has no duplicate label names', () => {
    const names = getAllLabelNames();
    const uniqueNames = new Set(names);
    expect(uniqueNames.size).toBe(names.length);
  });

  it('label names are non-empty lowercase strings', () => {
    for (const name of getAllLabelNames()) {
      expect(name.length).toBeGreaterThan(0);
      expect(name).toBe(name.toLowerCase());
    }
  });
});

describe('getAllLabels', () => {
  it('returns all labels from all categories', () => {
    const all = getAllLabels();
    const domainCount = Object.keys(LABEL_TAXONOMY.domain).length;
    const typeCount = Object.keys(LABEL_TAXONOMY.type).length;
    const scopeCount = Object.keys(LABEL_TAXONOMY.scope).length;
    expect(all.length).toBe(domainCount + typeCount + scopeCount);
  });
});

describe('getAllLabelNames', () => {
  it('returns string names for all labels', () => {
    const names = getAllLabelNames();
    expect(names.length).toBe(getAllLabels().length);
    for (const name of names) {
      expect(typeof name).toBe('string');
    }
  });
});

describe('getLabelByName', () => {
  it('finds existing labels', () => {
    const label = getLabelByName('security');
    expect(label).toBeDefined();
    expect(label!.name).toBe('security');
    expect(label!.category).toBe('domain');
  });

  it('finds labels case-insensitively', () => {
    const label = getLabelByName('SECURITY');
    expect(label).toBeDefined();
    expect(label!.name).toBe('security');
  });

  it('trims whitespace', () => {
    const label = getLabelByName('  bug  ');
    expect(label).toBeDefined();
    expect(label!.name).toBe('bug');
  });

  it('returns undefined for unknown labels', () => {
    expect(getLabelByName('nonexistent')).toBeUndefined();
  });
});

describe('isValidLabel', () => {
  it('returns true for valid labels', () => {
    expect(isValidLabel('feature')).toBe(true);
    expect(isValidLabel('security')).toBe(true);
    expect(isValidLabel('blocked')).toBe(true);
  });

  it('returns false for invalid labels', () => {
    expect(isValidLabel('not-a-label')).toBe(false);
    expect(isValidLabel('')).toBe(false);
  });
});

describe('getLabelsByCategory', () => {
  it('returns only domain labels for domain category', () => {
    const labels = getLabelsByCategory('domain');
    for (const label of labels) {
      expect(label.category).toBe('domain');
    }
    expect(labels.length).toBe(DOMAIN_LABEL_NAMES.length);
  });

  it('returns only type labels for type category', () => {
    const labels = getLabelsByCategory('type');
    for (const label of labels) {
      expect(label.category).toBe('type');
    }
    expect(labels.length).toBe(TYPE_LABEL_NAMES.length);
  });

  it('returns only scope labels for scope category', () => {
    const labels = getLabelsByCategory('scope');
    for (const label of labels) {
      expect(label.category).toBe('scope');
    }
    expect(labels.length).toBe(SCOPE_LABEL_NAMES.length);
  });
});

describe('getLabelColor', () => {
  it('returns the color for a valid label', () => {
    const color = getLabelColor('security');
    expect(color).toMatch(/^#[0-9A-Fa-f]{6}$/);
  });

  it('returns fallback gray for unknown labels', () => {
    expect(getLabelColor('nonexistent')).toBe('#6B7280');
  });
});

describe('buildColorMap', () => {
  it('returns a map with all labels', () => {
    const map = buildColorMap();
    const names = getAllLabelNames();
    for (const name of names) {
      expect(map[name]).toBeDefined();
      expect(map[name]).toMatch(/^#[0-9A-Fa-f]{6}$/);
    }
  });
});

describe('exported label name arrays', () => {
  it('DOMAIN_LABEL_NAMES matches taxonomy domain keys', () => {
    expect(DOMAIN_LABEL_NAMES).toEqual(Object.keys(LABEL_TAXONOMY.domain));
  });

  it('TYPE_LABEL_NAMES matches taxonomy type keys', () => {
    expect(TYPE_LABEL_NAMES).toEqual(Object.keys(LABEL_TAXONOMY.type));
  });

  it('SCOPE_LABEL_NAMES matches taxonomy scope keys', () => {
    expect(SCOPE_LABEL_NAMES).toEqual(Object.keys(LABEL_TAXONOMY.scope));
  });
});
