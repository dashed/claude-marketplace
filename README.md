# Personal Skills Marketplace

> A local marketplace for personal Claude Code skills and plugins.

A curated collection of Agent Skills for extending Claude Code's capabilities. This marketplace is configured for local use and makes it easy to install and manage custom skills.

## Quick Start

```bash
# 1. Add the marketplace
/plugin marketplace add /path/to/claude-skills

# 2. Install skills
/plugin  # Browse and install plugins → alberto-skills

# 3. Restart Claude Code to load new skills
/exit
```

## Available Skills

| Skill | Description | Source |
|-------|-------------|--------|
| **skill-creator** | Guide for creating effective skills. Use when creating or updating skills that extend Claude's capabilities. | [Anthropic](https://github.com/anthropics/skills/tree/main/skill-creator) |

## Usage

### Add this marketplace locally

```bash
/plugin marketplace add /path/to/claude-skills
```

### Update the marketplace

```bash
/plugin marketplace update alberto-skills
```

### Install skills

1. Select `/plugin` and then `Browse and install plugins`
2. Select `alberto-skills`
3. Choose the skills to install
4. Restart Claude Code

## Adding Skills to This Marketplace

### Method 1: Add to Marketplace (Recommended)

1. Add your skill directory to `plugins/`
2. Edit `.claude-plugin/marketplace.json` and add a new entry:

```json
{
  "name": "your-skill-name",
  "source": "./plugins/your-skill-name",
  "description": "Brief description of what the skill does",
  "strict": false,
  "skills": ["./"]
}
```

**Important:** The `skills` field is required to load skills from the marketplace. It tells Claude Code which directories contain SKILL.md files.

3. Update the CHANGELOG.md
4. Commit your changes

### Method 2: Direct Installation

Skills can also be installed directly without using the marketplace:

```bash
# Personal (available everywhere)
cp -r plugins/your-skill ~/.claude/skills/

# Project (shared with team)
cp -r plugins/your-skill .claude/skills/
```

## Structure

```
claude-skills/
├── .claude-plugin/
│   └── marketplace.json      # Marketplace manifest
├── plugins/
│   └── skill-creator/        # Skills directory
│       ├── SKILL.md          # Skill definition
│       ├── scripts/          # Optional scripts
│       └── references/       # Optional documentation
├── CHANGELOG.md              # Version history
└── README.md                 # This file
```

## Resources

- [Claude Code Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills)
- [Plugin Marketplaces Guide](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)

## Version

Current version: **0.1.0**

See [CHANGELOG.md](CHANGELOG.md) for version history.
