# Changelog - model-routing

All notable changes to the model-routing skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-07-01

### Added
- Initial addition to marketplace
- Skill that installs and maintains a "model routing" section in a project's
  CLAUDE.md — a per-model cost/intelligence/taste rankings table plus
  application rules and mechanics — so the orchestrating Claude routes
  subagent and workflow tasks to the cheapest model that clears the quality
  bar (pattern adapted from Theo's multi-model CLAUDE.md workflow)
- `references/claude-md-template.md`: the customizable CLAUDE.md section
  template (rankings table, defaults-not-limits escalation rules, Codex CLI
  mechanics, thin-wrapper pattern for using GPT models inside workflows and
  subagents where the `model` parameter only accepts Claude models)
- `references/codex-cli.md`: verified `codex exec` non-interactive reference
  (sandbox modes, output capture, model override, session resume) sourced
  from the Codex CLI implementation
