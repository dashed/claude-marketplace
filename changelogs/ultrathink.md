# Changelog - ultrathink

All notable changes to the ultrathink skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.1.0] - 2026-05-30

### Changed
- Corrected the Sequential Thinking tool reference from underscores to hyphens (`mcp__sequential-thinking__sequentialthinking`), matching the live MCP server key `sequential-thinking`
- Documented the companion `sequential-thinking` MCP plugin as a prerequisite (the MCP server must be enabled for the tool to exist)
- Added optional mention of the `DISABLE_THOUGHT_LOGGING` environment variable

## [1.0.0] - 2025-11-24

### Added
- Initial addition to marketplace
- Skill that invokes Sequential Thinking MCP for deep problem-solving
- Triggers on "use ultrathink" or when complex reasoning is needed
- Version metadata (v1.0.0)
- Author information (Alberto Leal)
- License information (MIT)
- Keywords: thinking, reasoning, sequential, planning, analysis, problem-solving
- Plugin configuration with skills loading from root
- Comprehensive documentation including:
  - When to use ultrathink (explicit requests, complex problems, planning, analysis)
  - How to use sequential thinking tool with parameters
  - Parameter reference table (thought, nextThoughtNeeded, thoughtNumber, totalThoughts, etc.)
  - Key capabilities (dynamic adjustment, revision support, branching, hypothesis cycle)
  - Process pattern for effective sequential thinking
  - Example thought sequence demonstrating revision flow
  - Best practices for effective use
