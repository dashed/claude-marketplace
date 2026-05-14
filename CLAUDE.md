# Development Guide

This document contains conventions and guidelines for developing the claude-marketplace project.

## Versioning and Release Process

### Semantic Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/):

**Format**: `MAJOR.MINOR.PATCH` (e.g., `0.2.0`)

**When to bump each version**:
- **MAJOR** (X.0.0): Breaking changes that are not backward compatible
  - Changes to marketplace.json structure that break existing plugins
  - Removal of supported features
  - API changes that require plugin updates

- **MINOR** (0.X.0): New features that are backward compatible
  - Adding new validation systems
  - Adding new plugins to the marketplace
  - Adding new Makefile targets or tooling
  - New documentation or schemas

- **PATCH** (0.0.X): Bug fixes and minor improvements
  - Fixing validation bugs
  - Documentation corrections
  - Dependency updates (non-breaking)
  - Performance improvements

### Version Bump Checklist

When releasing a new version, follow these steps:

1. **Update CHANGELOG.md**
   - Document all changes under `## [Unreleased]` section
   - Categorize changes: Added, Changed, Deprecated, Removed, Fixed, Security
   - Move `## [Unreleased]` content to new version section with date
   - Format: `## [X.Y.Z] - YYYY-MM-DD`
   - Update version comparison links at bottom

2. **Update individual skill changelogs (if applicable)**
   - Update `./changelogs/<skill-name>.md` for any skills that were added, updated, or modified
   - Document skill-specific changes from marketplace perspective
   - Use skill version from marketplace.json
   - See "Individual Skill Changelogs" section below for details

3. **Update .claude-plugin/marketplace.json**
   - Update `metadata.version` field to new version number
   - Example: `"version": "0.2.0"`

4. **Update README.md**
   - Update version in the "Version" section to match marketplace version
   - Add new skills to "Available Skills" table if any were added
   - Ensure skill descriptions and links are accurate

5. **Run validation**
   ```bash
   make validate
   ```
   Ensure all checks pass before proceeding.

6. **Create git commit**
   ```bash
   git add CHANGELOG.md changelogs/ .claude-plugin/marketplace.json README.md
   git commit -m "chore: bump version to vX.Y.Z"
   ```
   Note: Add README.md to git add if it was updated in step 4

7. **Create git tag**
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   ```
   Note: Use `v` prefix for tags (e.g., `v0.2.0`)

8. **Push changes**
   ```bash
   git push origin master
   git push origin vX.Y.Z
   ```

### Changelog Conventions

Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format:

**Categories** (in order):
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security vulnerability fixes

**Writing good changelog entries**:
- Use present tense ("Add feature" not "Added feature")
- Be specific and concise
- Focus on user-facing changes
- Include tool/file names when relevant
- Group related changes together

**Example**:
```markdown
### Added
- Static validation system with comprehensive checks for marketplace integrity
- JSON schemas for validation: plugin-schema.json, marketplace-schema.json
- Makefile with targets for validation, testing, and linting

### Changed
- Modernized validation workflow to use `uv run` pattern
- Removed unnecessary shebang lines from validator scripts
```

### Individual Skill Changelogs

Each skill in the marketplace has its own changelog located in `./changelogs/`.

**Location**: `./changelogs/<skill-name>.md`
- File names match plugin names from marketplace.json (kebab-case)
- Examples: `skill-creator.md`, `git-absorb.md`, `tmux.md`

**Purpose**: Track marketplace-specific changes to individual skills
- When skills are added to the marketplace
- Version updates in marketplace.json
- Marketplace-specific modifications to skill configuration
- Metadata updates (author, license, keywords, etc.)
- **NOT** upstream plugin development (that stays with the plugin)

**Format**: Same as main CHANGELOG.md
- Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
- Version numbers match the skill's version in marketplace.json
- Dates when changes were made in the marketplace
- Categories: Added, Changed, Deprecated, Removed, Fixed, Security

**When to Update**:
- Adding a new skill to marketplace → Create new changelog file with initial version
- Updating skill version in marketplace.json → Add new version section
- Making marketplace-specific changes → Document in appropriate version section
- Removing a skill → Add "Removed" entry in main CHANGELOG.md

**Relationship to Main CHANGELOG.md**:
- `CHANGELOG.md`: Marketplace-level changes (validation system, tooling, infrastructure, patterns)
- `changelogs/*.md`: Individual skill changes from marketplace perspective
- **Both**: When skill changes establish/demonstrate marketplace patterns or organizational improvements

**When to Update Both**:

Update ONLY `changelogs/<skill-name>.md`:
- Bug fixes in skill documentation
- Minor wording improvements
- Version updates without structural changes

Update BOTH `CHANGELOG.md` AND `changelogs/<skill-name>.md`:
- Implementing new organizational patterns (e.g., progressive disclosure with references/)
- Structural improvements that serve as examples for other skills
- Significant skill enhancements that impact marketplace quality

Update ONLY `CHANGELOG.md`:
- Adding new validation rules
- Updating tooling (Makefile, schemas)
- Infrastructure changes
- Adding/removing skills (high-level only)

**Example of updating both**:

*CHANGELOG.md*:
```markdown
## [Unreleased]

### Changed
- git-absorb skill: Implemented progressive disclosure pattern with references/ directory
- git-absorb skill: Added comprehensive reference documentation
```

*changelogs/git-absorb.md*:
```markdown
## [Unreleased]

### Changed
- Implemented progressive disclosure pattern with references/ directory
- Added references/advanced-usage.md with comprehensive flag reference (13 flags, 7 patterns)
- Added references/configuration.md with all 7 configuration options
- Updated SKILL.md to be leaner (269 → 232 lines, 14% reduction)
```

**Example of individual skill change only**:

*changelogs/skill-name.md* (only):
```markdown
## [1.0.1] - 2025-11-24

### Changed
- Fixed typo in configuration example
- Updated installation instructions for clarity
```

No CHANGELOG.md entry needed for minor documentation fixes.

See `./changelogs/README.md` for complete documentation.

### Version Comparison Links

At the bottom of CHANGELOG.md, maintain comparison links:

```markdown
[Unreleased]: https://github.com/dashed/claude-marketplace/compare/vX.Y.Z...HEAD
[X.Y.Z]: https://github.com/dashed/claude-marketplace/compare/vX.Y.Z-1...vX.Y.Z
```

Replace `X.Y.Z` with actual version numbers.

### Examples from This Project

**0.1.0 → 0.2.0 (Minor bump)**:
- **Why**: Added Static Validation system (new feature)
- **Changed**:
  - `.claude-plugin/marketplace.json`: `"version": "0.1.0"` → `"version": "0.2.0"`
  - `CHANGELOG.md`: Created `## [0.2.0] - 2025-11-23` section
  - Updated comparison links

**Files to update**:
1. `CHANGELOG.md` - Document changes and create version section
2. `changelogs/<skill-name>.md` - Update if skill-specific changes (if applicable)
3. `.claude-plugin/marketplace.json` - Update metadata.version

**Validation**:
```bash
make validate  # Must pass before release
```

## Development Workflow

### Making Changes

1. Work on feature/fix
2. Update code and tests
3. Run validation: `make validate`
4. Document changes in CHANGELOG.md under `## [Unreleased]`
5. Commit changes

### Before Release

1. Review CHANGELOG.md for completeness
2. Determine version bump type (major/minor/patch)
3. Follow Version Bump Checklist above
4. Run full validation suite: `make validate-strict`
5. Create release commit and tag

## Creating a New Skill

This section documents the conventions for adding a new skill to the marketplace.

### Quick Reference Checklist

When adding a new skill:

1. [ ] Create `plugins/<skill-name>/` directory
2. [ ] Create `plugins/<skill-name>/skills/<skill-name>/SKILL.md` with YAML frontmatter
3. [ ] Create `references/` directory inside the skill directory (if needed for advanced docs)
4. [ ] Add plugin entry to `.claude-plugin/marketplace.json` (with `"skills": ["./skills"]`)
5. [ ] Create `changelogs/<skill-name>.md`
6. [ ] Update `CHANGELOG.md` under `## [Unreleased]`
7. [ ] Run `make validate`

### Plugin Directory Structure

```
plugins/<skill-name>/
└── skills/
    └── <skill-name>/
        ├── SKILL.md              (required)
        ├── references/           (optional - for detailed documentation)
        │   ├── advanced-usage.md
        │   └── configuration.md
        ├── scripts/              (optional - executable code)
        └── assets/               (optional - templates, images)
```

**Naming**: Use kebab-case for directory names (e.g., `git-chain`, `skill-creator`).

### SKILL.md Format

Every skill requires a `SKILL.md` file with YAML frontmatter and markdown body.

#### YAML Frontmatter (Required)

```yaml
---
name: skill-name
description: Brief description of what the skill does. Use when [specific triggers]. Include contexts that should activate this skill.
---
```

**Field requirements:**
- `name`: Required. Kebab-case, lowercase letters, numbers, hyphens only. Max 64 characters.
  - Pattern: `^[a-z0-9]+(-[a-z0-9]+)*$`
  - Examples: `git-chain`, `pdf-editor`, `skill-creator`
- `description`: Required. 20-1024 characters.
  - **Must include "Use when..." triggers** - This is the primary mechanism for skill activation
  - Claude reads only the frontmatter to decide when to use a skill
  - Be specific about contexts that should trigger the skill

**Good description example:**
```yaml
description: Manage and rebase chains of dependent Git branches (stacked branches). Use when working with multiple dependent PRs, feature branches that build on each other, or maintaining clean branch hierarchies. Automates rebasing or merging entire branch chains.
```

#### Markdown Body

The body is loaded only AFTER the skill triggers. Structure it for the task at hand:

**Recommended sections:**
1. Overview - What the skill does
2. When to Use - Specific scenarios (reinforces frontmatter)
3. Prerequisites - Required tools/setup
4. Basic Workflow - Common usage patterns
5. Core Commands/Reference - Quick reference table
6. Advanced Usage - Link to `references/` for details
7. Troubleshooting - Common issues and solutions

**Important guidelines:**
- Keep SKILL.md under 500 lines to minimize context bloat
- Use progressive disclosure - link to `references/` for advanced content
- Challenge each paragraph: "Does Claude really need this?"
- Prefer concise examples over verbose explanations

### Progressive Disclosure Pattern

Keep the main SKILL.md focused on common use cases. Move detailed documentation to `references/`:

```
plugins/git-chain/
└── skills/
    └── git-chain/
        ├── SKILL.md                      (common workflows, ~200 lines)
        └── references/
            ├── rebase-options.md         (all rebase flags and options)
            ├── merge-options.md          (all merge flags and strategies)
            └── chain-management.md       (advanced chain operations)
```

**In SKILL.md, link to references:**
```markdown
## Advanced Usage

For comprehensive coverage of all flags and advanced patterns, see:
- [references/rebase-options.md](references/rebase-options.md)
- [references/merge-options.md](references/merge-options.md)
```

**Guidelines:**
- Keep references one level deep from SKILL.md
- Include table of contents in longer reference files (>100 lines)
- Reference files should be self-contained and focused on one topic

### marketplace.json Plugin Entry

Add an entry to `.claude-plugin/marketplace.json` under the `plugins` array:

```json
{
  "name": "skill-name",
  "version": "1.0.0",
  "source": "./plugins/skill-name",
  "description": "Brief description with Use when triggers. Max 500 chars.",
  "author": {
    "name": "Author Name"
  },
  "repository": "https://github.com/dashed/claude-marketplace/tree/master/plugins/skill-name",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "strict": false,
  "skills": ["./skills"]
}
```

**Field reference:**

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Kebab-case identifier, must match directory name |
| `source` | Yes | Relative path starting with `./` |
| `version` | Recommended | Semantic version (e.g., `1.0.0`) |
| `description` | Recommended | 10-500 chars, include "Use when" triggers |
| `author.name` | Recommended | Author or maintainer name |
| `repository` | Recommended | URL to skill source in marketplace |
| `license` | Recommended | SPDX identifier (MIT, Apache-2.0, etc.) |
| `keywords` | Recommended | Array of discovery tags |
| `strict` | Recommended | Set to `false` for most skills |
| `skills` | Recommended | Array of skill directories, typically `["./"]` |

### Skill Changelog

Create `changelogs/<skill-name>.md` for each new skill:

```markdown
# Changelog - skill-name

All notable changes to the skill-name skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - YYYY-MM-DD

### Added
- Initial addition to marketplace
- Description of what the skill provides
- List key features and documentation included
```

### Main CHANGELOG.md Update

Add entries under `## [Unreleased]` in the main `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added
- skill-name skill: Brief description of the skill
- skill-name skill: Notable features or documentation
```

**Format:** Prefix each line with `skill-name skill:` to clearly identify skill-specific changes.

### Validation

Always run validation before committing:

```bash
make validate
```

This checks:
- File structure (plugin directories, required files)
- JSON manifest validity (marketplace.json schema compliance)
- YAML frontmatter (SKILL.md frontmatter schema compliance)

All checks must pass before the skill can be released.

### Example: Adding a New Skill

Complete example of adding a `pdf-editor` skill:

**1. Create directory structure:**
```bash
mkdir -p plugins/pdf-editor/skills/pdf-editor/references
```

**2. Create SKILL.md:**
Save to `plugins/pdf-editor/skills/pdf-editor/SKILL.md`:
```markdown
---
name: pdf-editor
description: Edit and manipulate PDF files. Use when rotating pages, extracting text, merging documents, or performing other PDF operations.
---

# PDF Editor

## Overview
...
```

**3. Add to marketplace.json:**
```json
{
  "name": "pdf-editor",
  "version": "1.0.0",
  "source": "./plugins/pdf-editor",
  "description": "Edit and manipulate PDF files. Use when rotating, extracting, merging, or modifying PDFs.",
  "author": { "name": "Your Name" },
  "repository": "https://github.com/dashed/claude-marketplace/tree/master/plugins/pdf-editor",
  "license": "MIT",
  "keywords": ["pdf", "document", "editing"],
  "strict": false,
  "skills": ["./skills"]
}
```

**4. Create changelogs/pdf-editor.md**

**5. Update CHANGELOG.md under [Unreleased]**

**6. Validate:**
```bash
make validate
```

## Repository Information

- **Repository**: https://github.com/dashed/claude-marketplace
- **Owner**: Alberto Leal (mail4alberto@gmail.com)
- **Primary Branch**: master
