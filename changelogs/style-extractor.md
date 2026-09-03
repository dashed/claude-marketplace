# Changelog - style-extractor

All notable changes to the style-extractor skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- references/narrative-dimensions.md with 10 narrative construction dimensions for fiction analysis
- Phase 2b (Narrative Construction) for fiction/creative writing source texts
- Fiction-specific guidance for deliverables (narrative sections in voice card, do/don't, rubric)
- Known AI narrative defaults table for identifying distinctively human authorial choices

### Changed
- SKILL.md now distinguishes surface style (17 dimensions) from narrative construction (10 dimensions)
- References section updated to include narrative-dimensions.md

## [1.0.1] - 2026-09-03

### Fixed
- Replaced the two stale bare-form `mcp__sequential-thinking__sequentialthinking` references with the plugin-namespaced `mcp__plugin_sequential-thinking_think__sequentialthinking` id (server key shortened from `sequential-thinking` to `think` to stay within the 64-character tool-name limit), per the rule that skills must reference the `mcp__plugin_...` form

## [1.0.0] - 2026-05-13

### Added
- Initial addition to marketplace
- Skill for extracting reusable writing styles from source texts (PDFs, documents, files)
- Four-phase workflow: Source Analysis, Dimension Extraction, Synthesis, Output
- 17 style dimensions for comprehensive voice analysis
- Four standardized deliverables: full style guide, voice card, do/don't checklist, scoring rubric
- Integration with writing-styles/ folder structure and templates
- References documentation:
  - references/style-dimensions.md with detailed analysis guide for all 17 dimensions
  - references/deliverable-templates.md with templates and embedded guidance
- Support for MCP tools: fuzzy search (PDF extraction), sequential thinking (analysis)
- Naming convention guidance for style directories
- Best practices for sampling strategy and cross-validation
- Anti-patterns to avoid during style extraction
