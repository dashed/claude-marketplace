# Progressive Disclosure

Guide to properly structuring information across the three levels of skill loading.

## The Three Levels

Skills use progressive disclosure to minimize context usage while maximizing discoverability.

### Level 1: Metadata (Always Loaded)

**What**: YAML frontmatter in SKILL.md
**When**: Always (loaded at startup)
**Token cost**: ~100 tokens per skill
**Purpose**: Skill discovery and triggering

```yaml
---
name: skill-name
description: What the skill does and when to use it. Be comprehensive - this is how Claude discovers your skill.
---
```

**Best practices**:
- Description should answer: "What does this do?" and "When should I use it?"
- Include trigger keywords users might mention
- Be specific but concise (max 1024 characters)
- No implementation details (those go in Level 2/3)

**Example** (good):
```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

**Example** (bad):
```yaml
description: PDF tool. Uses pdfplumber library with various configuration options for text extraction, table parsing, and form filling operations on PDF documents.
```

---

### Level 2: Instructions (Loaded When Triggered)

**What**: The markdown body of SKILL.md
**When**: When Claude triggers the skill
**Token cost**: Should be under 5k tokens
**Purpose**: Core instructions and workflow guidance

**What belongs here**:
- Quick start / getting started
- Core workflow steps
- Essential examples (minimal and representative)
- Links to Level 3 resources
- Common use cases
- Key concepts

**What doesn't belong here**:
- Detailed API documentation → references/api-reference.md
- Extensive examples → references/examples.md
- Configuration details → references/configuration.md
- Troubleshooting guides → references/troubleshooting.md
- Long reference material → references/

**Structure**:
```markdown
# Skill Name

## Quick Start
[Minimal getting started example]

## Core Workflow
[Essential steps for main use case]

## Common Tasks
[2-3 most common scenarios with brief examples]

## Advanced Usage
See [advanced-usage.md](references/advanced-usage.md)
```

**Keep it lean**:
- ❌ Walls of text
- ❌ Every possible parameter
- ❌ Exhaustive examples
- ✅ Core workflow
- ✅ Minimal examples
- ✅ Links to references

---

### Level 3: Resources (Loaded As Needed)

**What**: Files in references/, scripts/, assets/
**When**: When Claude determines they're needed
**Token cost**: Varies (can be large)
**Purpose**: Detailed documentation, code, assets

**Proper organization**:

```
skill-name/
├── SKILL.md (Level 2: Core instructions)
└── references/ (Level 3: Detailed resources)
    ├── api-reference.md (Complete API docs)
    ├── examples.md (Comprehensive examples)
    ├── configuration.md (All config options)
    ├── troubleshooting.md (Common issues)
    └── advanced-usage.md (Advanced patterns)
```

**When to create reference files**:
- Content > 1000 words → separate file
- Detailed specifications → separate file
- Comprehensive examples → separate file
- Reference tables/lists → separate file
- Specialized workflows → separate file

**How to link from SKILL.md**:
```markdown
For complete API documentation, see [api-reference.md](references/api-reference.md).
For all configuration options, see [configuration.md](references/configuration.md).
```

---

## Anti-Patterns

### ❌ Everything in SKILL.md

```markdown
# Skill Name

## Introduction
[500 words of background...]

## Complete API Reference
[5000 words of API docs...]

## Configuration
[1000 words of config options...]

## Examples
[50 examples...]

## Troubleshooting
[30 common issues...]
```

**Problem**: Loads 10k+ tokens every time skill is triggered, even for simple tasks.

**Fix**: Move sections to references/:
- api-reference.md
- configuration.md
- examples.md
- troubleshooting.md

Keep only quick start and core workflow in SKILL.md.

---

### ❌ Duplicate Content

SKILL.md:
```markdown
## Authentication
Set API_KEY environment variable.

## API Reference
Full authentication documentation:
- Set API_KEY environment variable
- Obtain key from dashboard
- Key format: 32 hex characters
- Rotation: every 90 days
```

references/api-reference.md:
```markdown
## Authentication
Set API_KEY environment variable.
Obtain key from dashboard...
[same content repeated]
```

**Problem**: Same information in multiple places. Wastes tokens and creates maintenance burden.

**Fix**: Put detailed info in ONE place (references/), link from SKILL.md.

SKILL.md:
```markdown
## Quick Start

Set `API_KEY` environment variable:
```bash
export API_KEY="your-key-here"
```

For authentication details, see [api-reference.md](references/api-reference.md#authentication).
```

---

### ❌ Unclear Load Boundaries

```markdown
# Skill Name

Some stuff in SKILL.md...

[Inline 2000 words of detailed configuration]

...more stuff...

For additional examples, see examples.md.
```

**Problem**: Heavy content inline, light content in references. Backwards from ideal.

**Fix**: Keep SKILL.md lean, move heavy content to references.

---

## Implementation Guide

### Audit Existing Skill

1. **Measure SKILL.md size**:
   ```bash
   wc -w skill-name/SKILL.md
   ```
   Target: Under 1500 words (~5k tokens)

2. **Identify heavy sections**:
   - Complete API docs
   - Exhaustive examples
   - Configuration tables
   - Troubleshooting guides

3. **Extract to references**:
   ```bash
   mkdir -p skill-name/references
   # Move heavy sections to focused files
   ```

4. **Update links**:
   Replace inline content with links to references/

### Create New Skill

1. **Start with metadata**:
   ```yaml
   ---
   name: skill-name
   description: Clear description with trigger keywords
   ---
   ```

2. **Write lean SKILL.md**:
   - Quick start (1 example)
   - Core workflow (essential steps)
   - Links to references (for depth)

3. **Create references as needed**:
   - Only when content > 1000 words
   - One focused topic per file
   - Clear file names

4. **Link properly**:
   ```markdown
   For [topic], see [references/topic.md](references/topic.md).
   ```

---

## Verification Checklist

Progressive disclosure audit:

- [ ] SKILL.md under 1500 words (~5k tokens)
- [ ] Metadata (frontmatter) is concise and comprehensive
- [ ] SKILL.md contains only core workflow and essential examples
- [ ] Detailed content moved to references/
- [ ] No duplicate content between SKILL.md and references/
- [ ] Links from SKILL.md to references/ are clear and resolve correctly
- [ ] Reference file names indicate content
- [ ] Each reference file has one focused purpose

---

## Progressive Disclosure in Practice

### Example: tmux Skill

**Level 1** (Metadata - Always loaded):
```yaml
description: Remote control tmux sessions for interactive CLIs (python, gdb, etc.)
```

**Level 2** (SKILL.md - Loaded when triggered):
```markdown
# tmux Skill

## Quick Start
1. Create session: `create-session.sh -n my-session --python`
2. Send command: `safe-send.sh -s my-session -c "print('hello')"`
3. Wait for output: `wait-for-text.sh -s my-session -p ">>>"`

For session registry details, see [session-registry.md](references/session-registry.md).
```

**Level 3** (References - Loaded as needed):
- `references/session-registry.md` (530+ lines of comprehensive registry docs)
- Only loaded when Claude needs registry details

**Result**:
- Metadata: ~30 tokens (always)
- Core instructions: ~1k tokens (when triggered)
- Registry docs: ~2k tokens (only when needed for registry-specific questions)

Total context impact: 30 tokens idle, 1k tokens typical use, 3k tokens for deep dives.

Without progressive disclosure: 3k+ tokens always loaded.

---

## Summary

**Three levels, three loading times**:
1. **Metadata** (always): Name + description for discovery
2. **Instructions** (when triggered): Core workflow in SKILL.md
3. **Resources** (as needed): Detailed docs in references/

**Key principle**: Information loads when needed, not before.

**Target metrics**:
- Metadata: ~100 tokens
- SKILL.md: <5k tokens (preferably <3k)
- References: No limit (loaded selectively)
