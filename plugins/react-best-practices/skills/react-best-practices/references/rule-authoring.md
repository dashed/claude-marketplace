# Rule Authoring Guide

How to create, modify, and validate rules for the React Best Practices skill.

## Creating a New Rule

1. Copy `rules/_template.md` to `rules/area-description.md`
2. Choose the appropriate area prefix (see Section Prefixes below)
3. Fill in the frontmatter and content
4. Ensure you have clear examples with explanations
5. Run `python -m scripts build` to regenerate AGENTS.md and test-cases.json

## Rule File Structure

Each rule file follows this structure:

```markdown
---
title: Rule Title Here
impact: MEDIUM
impactDescription: Optional description of impact (e.g., "20-50% improvement")
tags: tag1, tag2
---

## Rule Title Here

**Impact: MEDIUM (optional impact description)**

Brief explanation of the rule and why it matters.

**Incorrect (description of what's wrong):**

\`\`\`typescript
// Bad code example here
\`\`\`

**Correct (description of what's right):**

\`\`\`typescript
// Good code example here
\`\`\`

Reference: [Link to documentation](https://example.com)
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Rule title, also used as the H2 heading |
| `impact` | Yes | Impact level (see below) |
| `impactDescription` | No | Quantitative description (e.g., "20-50% improvement") |
| `tags` | Yes | Comma-separated keywords for categorization |

## Section Prefixes

The filename prefix determines which section a rule belongs to:

| Prefix | Section | Impact |
|--------|---------|--------|
| `async-` | 1. Eliminating Waterfalls | CRITICAL |
| `bundle-` | 2. Bundle Size Optimization | CRITICAL |
| `server-` | 3. Server-Side Performance | HIGH |
| `client-` | 4. Client-Side Data Fetching | MEDIUM-HIGH |
| `rerender-` | 5. Re-render Optimization | MEDIUM |
| `rendering-` | 6. Rendering Performance | MEDIUM |
| `js-` | 7. JavaScript Performance | LOW-MEDIUM |
| `advanced-` | 8. Advanced Patterns | LOW |

## Impact Levels

- `CRITICAL` - Highest priority, major performance gains
- `HIGH` - Significant performance improvements
- `MEDIUM-HIGH` - Moderate-high gains
- `MEDIUM` - Moderate performance improvements
- `LOW-MEDIUM` - Low-medium gains
- `LOW` - Incremental improvements

## File Naming Convention

- Files starting with `_` are special (excluded from build): `_sections.md`, `_template.md`
- Rule files: `area-description.md` (e.g., `async-parallel.md`, `bundle-barrel-imports.md`)
- Section is automatically inferred from filename prefix
- Rules are sorted alphabetically by title within each section
- IDs (e.g., 1.1, 1.2) are auto-generated during build

## Build Scripts

```bash
python -m scripts build          # Compile rules into AGENTS.md
python -m scripts validate       # Validate all rule files
python -m scripts extract-tests  # Extract test cases for LLM evaluation
```

### What `build` Does

- Reads all rule files from `rules/` (excluding `_`-prefixed files)
- Groups rules by section prefix
- Sorts rules alphabetically by title within each section
- Generates numbered IDs (e.g., 1.1, 1.2)
- Compiles everything into `AGENTS.md` with metadata from `metadata.json`
- Generates `test-cases.json` with extracted examples

### What `validate` Does

- Checks all rule files have valid YAML frontmatter
- Verifies required fields (`title`, `impact`, `tags`)
- Validates impact level is one of the allowed values
- Checks filename prefix matches a known section
- Ensures consistent structure (heading, examples)

### What `extract-tests` Does

- Parses code examples from each rule
- Extracts "Incorrect" and "Correct" pairs
- Outputs structured JSON for LLM evaluation

## Contributing Guidelines

When adding or modifying rules:

1. Use the correct filename prefix for your section
2. Follow the `_template.md` structure
3. Include clear bad/good examples with explanations
4. Add appropriate tags
5. Run `python -m scripts build` to regenerate AGENTS.md
6. Rules are automatically sorted by title - no need to manage numbers
