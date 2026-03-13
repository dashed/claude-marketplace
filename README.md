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
| **ai-friendly-cli** | Build and refactor CLIs for AI agent compatibility. Use when making CLI tools machine-readable with structured JSON output, input hardening, schema introspection, dry-run safety, and MCP surfaces. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/ai-friendly-cli) |
| **skill-creator** | Create new skills, modify and improve existing skills, and measure skill performance. Use when creating, updating, evaluating, or optimizing skills. | [Anthropic](https://github.com/anthropics/skills/tree/main/skill-creator) |
| **skill-reviewer** | Review and ensure skills maintain high quality standards. Use when creating new skills, updating existing skills, or auditing skill quality. Checks for progressive disclosure, mental model shift, appropriate scope, and documentation clarity. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/skill-reviewer) |
| **git-absorb** | Automatically fold uncommitted changes into appropriate commits. Use for applying review feedback and maintaining atomic commit history. Tool: [git-absorb](https://github.com/tummychow/git-absorb) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/git-absorb) |
| **tmux** | Remote control tmux sessions for interactive CLIs (python, gdb, etc.) by sending keystrokes and scraping pane output. Use when debugging applications, running interactive REPLs (Python, gdb, ipdb, psql, mysql, node), or automating terminal workflows. Works with stock tmux on Linux/macOS. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/tmux) |
| **ultrathink** | Invoke deep sequential thinking for complex problem-solving. Use when tackling problems that require careful step-by-step reasoning, planning, hypothesis generation, or multi-step analysis. Trigger with "use ultrathink". | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/ultrathink) |
| **conventional-commits** | Format git commit messages following the Conventional Commits 1.0.0 specification. Use when creating git commits for consistent, semantic commit messages that support automated changelog generation and semantic versioning. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/conventional-commits) |
| **git-chain** | Manage and rebase chains of dependent Git branches (stacked branches). Use when working with multiple dependent PRs, feature branches that build on each other, or maintaining clean branch hierarchies. Automates rebasing or merging entire branch chains. Tool: [git-chain](https://github.com/dashed/git-chain) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/git-chain) |
| **jj** | Jujutsu (jj) version control system - a Git-compatible VCS with automatic rebasing, first-class conflicts, and operation log. Use when working with jj repositories, stacked commits, revsets, or enhanced Git workflows. Tool: [jj](https://github.com/jj-vcs/jj) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/jj) |
| **fzf** | Command-line fuzzy finder for interactive filtering. Use when searching files, command history (CTRL-R), creating interactive menus, or integrating with ripgrep, fd, and git. Shell keybindings: CTRL-T, CTRL-R, ALT-C, `**` completion. Tool: [fzf](https://github.com/junegunn/fzf) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/fzf) |
| **playwright** | Browser automation with Playwright for Python. Use when testing websites, taking screenshots, filling forms, scraping web content, or automating browser interactions. Uses uv with PEP 723 inline scripts for self-contained automation. **Requires one-time browser setup** (see below). Tool: [Playwright](https://playwright.dev/python/) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/playwright) |
| **zellij** | Terminal workspace and multiplexer for interactive CLI sessions. Use when managing terminal sessions, running interactive REPLs, debugging, or automating terminal workflows. Simpler alternative to tmux with native session management. Tool: [Zellij](https://zellij.dev/) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/zellij) |
| **design-principles** | Guide AI-assisted UI generation toward enterprise-grade, intentional design. Use when building UIs, creating dashboards, designing SaaS applications, or generating styled frontend code. Enforces 4px grids, typography hierarchies, and consistent depth strategies. | [Dammyjay93](https://github.com/dashed/claude-marketplace/tree/master/plugins/design-principles) |
| **mermaid-cli** | Generate, validate, and fix diagrams from Mermaid markup using mmdc. Use when creating flowcharts, sequence diagrams, class diagrams, or converting .mmd files to images/SVG/PDF. Also validates and fixes Mermaid syntax. Tool: [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/mermaid-cli) |
| **walkthrough-to-obsidian** | Convert game walkthroughs and guides from plain text into structured, interlinked Obsidian markdown pages. Use when converting walkthroughs, FAQs, or reference documents into Obsidian vault pages. Supports agent team parallelization for large documents. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/walkthrough-to-obsidian) |
| **long-form-math** | Write mathematics in a long-form, understanding-focused style with detailed proofs and rich exposition. Three-phase proof workflow, motivation-first exposition, and rigorous writing conventions. Inspired by Cummings' Real Analysis and Chartrand's Mathematical Proofs. | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/long-form-math) |
| **chrome-cdp** | Interact with live Chrome browser sessions via Chrome DevTools Protocol. Use when inspecting, debugging, or interacting with pages open in Chrome — screenshots, accessibility trees, JS evaluation, clicking, navigating. Persistent per-tab daemon, works with 100+ tabs. Based on [pasky/chrome-cdp-skill](https://github.com/pasky/chrome-cdp-skill). **Requires Chrome remote debugging** (see below). | [dashed](https://github.com/dashed/claude-marketplace/tree/master/plugins/chrome-cdp) |
| **linear** | Managing Linear issues, projects, and teams. Use when working with Linear tasks, creating issues, updating status, querying projects, or managing team workflows. Tool: [Linear SDK](https://github.com/linear/linear) + MCP | [wrsmith108](https://github.com/wrsmith108/linear-claude-skill) |

### Chrome CDP Setup

The chrome-cdp skill requires Chrome with remote debugging enabled and Python 3.10+ with the `websockets` library:

```bash
# 1. Enable remote debugging in Chrome
#    Navigate to chrome://inspect/#remote-debugging and toggle the switch

# 2. Install the websockets dependency
uv pip install websockets
```

### Linear Setup

The linear skill requires Node.js dependencies and a Linear API key:

```bash
# 1. Install dependencies in the plugin cache directory
cd ~/.claude/plugins/cache/alberto-marketplace/linear/2.3.1
npm install

# 2. Create a Linear API key at https://linear.app/settings/api
# 3. Add to your shell profile (~/.zshrc or ~/.bashrc)
export LINEAR_API_KEY="lin_api_..."
```

Restart Claude Code after setup.

### Playwright Setup

The playwright skill requires a one-time browser installation (~200MB). Claude will suggest these commands but will not run them directly—run them manually:

```bash
# Install Chromium (recommended, ~200MB)
uv run --with playwright playwright install chromium

# Or install all browsers
uv run --with playwright playwright install
```

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

Current version: **0.9.0**

See [CHANGELOG.md](CHANGELOG.md) for version history.
