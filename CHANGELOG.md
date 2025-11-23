# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- git-absorb skill: Implemented progressive disclosure pattern with references/ directory
- git-absorb skill: Added comprehensive reference documentation (advanced-usage.md, configuration.md)
- git-absorb skill: Reduced SKILL.md size by 14% (269 → 232 lines) while improving discoverability

## [0.2.0] - 2025-11-23

### Added
- Static validation system with comprehensive checks for marketplace integrity
- JSON schemas for validation: plugin-schema.json, marketplace-schema.json, skill-frontmatter-schema.json
- Python validation scripts: validate_yaml.py, validate_json.py, validate_structure.py, validate_all.py
- Makefile with targets for validation, testing, linting, and formatting
- uv-based Python environment management with pyproject.toml
- Automated validation for YAML frontmatter in SKILL.md files
- Automated validation for JSON manifests (plugin.json, marketplace.json)
- File structure and naming convention validation
- git-absorb skill for automatically folding uncommitted changes into appropriate commits
- Comprehensive documentation analysis (ANALYSIS.md) for git-absorb skill comparing against official documentation
- tmux skill for remote controlling tmux sessions for interactive CLIs (python, gdb, etc.) from [mitsuhiko/agent-commands](https://github.com/mitsuhiko/agent-commands/tree/main/skills/tmux)
- tmux skill helper tools: find-sessions.sh and wait-for-text.sh for session management and synchronization
- Version metadata (v1.0.0) for both plugins
- Author information for plugin attribution
- License information (Apache-2.0 for skill-creator, MIT for git-absorb, Vibecoded for tmux)
- Keywords for better plugin discovery and categorization
- Python/uv/testing artifacts to .gitignore

### Changed
- Modernized validation workflow to use `uv run` pattern for all Python scripts
- Removed unnecessary shebang lines from validator scripts (scripts/validators/*.py)
- Cleaned up dependencies: removed yamllint, markdown-it-py, linkchecker, mypy, and types-pyyaml (27% reduction)
- git-absorb skill: Removed automatic installation attempts (now recommends manual installation only)
- git-absorb skill: Added important default behaviors section explaining author filtering and stack size limits
- git-absorb skill: Added configuration section with critical maxStack setting and other useful options
- git-absorb skill: Enhanced troubleshooting with stack limit warning solutions
- tmux skill: Enhanced description with "Use when..." clause and trigger terms for improved skill discovery

## [0.1.0] - 2025-11-22

### Added
- Initial marketplace structure with `.claude-plugin/marketplace.json`
- skill-creator skill from [Anthropic's skills repository](https://github.com/anthropics/skills/tree/main/skill-creator)
- README with instructions for adding marketplace locally
- Marketplace metadata and owner information
- Plugin entry with `skills` field for proper skill loading

[Unreleased]: https://github.com/dashed/claude-marketplace/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/dashed/claude-marketplace/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/dashed/claude-marketplace/releases/tag/v0.1.0
