# Changelog - agent-skill-init

All notable changes to the agent-skill-init skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.0.0] - 2026-06-19

### Added
- Initial addition to marketplace
- Lightweight scaffolder for creating repo-local Agent Skills following the open [agentskills.io](https://agentskills.io) specification (distinct from skill-creator and skill-reviewer)
- Scaffolds the skill directory and writes a spec-compliant `SKILL.md` with valid `name`/`description` frontmatter under `.agents/skills/` (or `.claude/skills/`)
- Validates the generated skill with `skills-ref`
- Bundles the official `skills-ref` validator vendored verbatim (Apache-2.0, commit `5d4c1fd`) under `vendor/skills-ref/`, so validation runs via `uv`/`uvx` with no separate install (provenance in `vendor/VENDOR.md`); a global `skills-ref` install remains a documented fallback
- Reference docs: `references/spec-reference.md`, `references/examples.md`, `references/placement.md`, and an `assets/SKILL.md.template` starter
- Author information (Alberto Leal)
- License information (MIT)
- Keywords: skills, agentskills, scaffold, spec, repo-local, skill-md
- Plugin configuration with skills loading from `./skills`
