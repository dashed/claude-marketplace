# Changelog - handoff

All notable changes to the handoff skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-11

### Added
- Initial addition to marketplace — ported from [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/productivity/handoff/SKILL.md) (`skills/productivity/handoff`, MIT)
- Compacts the current conversation into a handoff document a fresh agent can pick up: saved to the OS temp directory (not the workspace), includes a "suggested skills" section, references existing artifacts (PRDs, plans, ADRs, issues, commits, diffs) by path/URL instead of duplicating them, redacts secrets/PII, and tailors the doc to the optional argument describing what the next session is for (`argument-hint` supported)

### Changed
- Marketplace adaptation (only divergence from upstream): extended the frontmatter `description` with house-convention "Use when..." triggers (session handoff, context transfer, approaching context limits, explicit "handoff" phrasing); skill body kept verbatim
