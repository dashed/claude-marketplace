# Changelog - conventional-commits

All notable changes to the conventional-commits skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.0.0] - 2025-11-24

### Added
- Initial addition to marketplace
- Skill for formatting git commits according to Conventional Commits 1.0.0 specification
- Triggers when user asks to commit changes, create git commits, or mentions committing code
- Version metadata (v1.0.0)
- Author information (Alberto Leal)
- License information (MIT)
- Keywords: git, commits, conventional-commits, changelog, semver, versioning
- Plugin configuration with skills loading from root
- Progressive disclosure structure with reference file:
  - references/full-spec.md: Complete Conventional Commits 1.0.0 specification
- SKILL.md includes:
  - Commit message format template
  - Type reference table (feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert)
  - Decision framework for determining commit type
  - Message best practices (50 char limit, imperative mood, 72 char body wrap)
  - Footer examples (Fixes, Co-authored-by, Refs)
  - Breaking change syntax (! suffix and BREAKING CHANGE footer)
  - Command execution guidelines (single quotes for shell escaping)
  - Quality checks checklist
  - Commit workflow steps
  - Multiple examples for different commit types
  - HEREDOC pattern for multi-line commit messages
