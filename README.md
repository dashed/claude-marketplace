# Alberto's Claude Marketplace

> A local marketplace for personal Claude Code skills and plugins.

A curated collection of Agent Skills for extending Claude Code's capabilities. This marketplace is configured for local use and makes it easy to install and manage custom skills.

## Quick Start

```bash
# 1. Add the marketplace
/plugin marketplace add /path/to/claude-marketplace

# 2. Install skills
/plugin  # Browse and install plugins → alberto-marketplace

# 3. Restart Claude Code to load new skills
/exit
```

## Available Skills

| Skill | Description | Source |
|-------|-------------|--------|
| **skill-creator** | Guide for creating effective skills. Use when creating or updating skills that extend Claude's capabilities. | [Anthropic](https://github.com/anthropics/skills/tree/main/skill-creator) |
| **skill-reviewer** | Review and ensure skills maintain high quality standards. Use when creating new skills, updating existing skills, or auditing skill quality. Checks for progressive disclosure, mental model shift, appropriate scope, and documentation clarity. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/skill-reviewer) |
| **git-absorb** | Automatically fold uncommitted changes into appropriate commits. Use for applying review feedback and maintaining atomic commit history. Tool: [git-absorb](https://github.com/tummychow/git-absorb) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/git-absorb) |
| **tmux** | Remote control tmux sessions for interactive CLIs (python, gdb, etc.) by sending keystrokes and scraping pane output. Use when debugging applications, running interactive REPLs (Python, gdb, ipdb, psql, mysql, node), or automating terminal workflows. Works with stock tmux on Linux/macOS. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/tmux) |
| **ultrathink** | Invoke deep sequential thinking for complex problem-solving. Use when tackling problems that require careful step-by-step reasoning, planning, hypothesis generation, or multi-step analysis. Trigger with "use ultrathink". | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/ultrathink) |
| **conventional-commits** | Format git commit messages following the Conventional Commits 1.0.0 specification. Use when creating git commits for consistent, semantic commit messages that support automated changelog generation and semantic versioning. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/conventional-commits) |
| **git-chain** | Manage and rebase chains of dependent Git branches (stacked branches). Use when working with multiple dependent PRs, feature branches that build on each other, or maintaining clean branch hierarchies. Automates rebasing or merging entire branch chains. Tool: [git-chain](https://github.com/dashed/git-chain) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/git-chain) |

## Usage

### Add this marketplace locally

```bash
/plugin marketplace add /path/to/claude-marketplace
```

### Update the marketplace

```bash
/plugin marketplace update alberto-marketplace
```

### Install skills

1. Select `/plugin` and then `Browse and install plugins`
2. Select `alberto-marketplace`
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
claude-marketplace/
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

Current version: **0.8.0**

See [CHANGELOG.md](CHANGELOG.md) for version history.
