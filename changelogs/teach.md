# Changelog - teach

All notable changes to the teach skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-04

### Added
- Initial addition to the marketplace — a skill that runs a Socratic teaching loop, quizzing the human on a coding session until they have confirmed mastery of every concept. Ported from the upstream `teach` skill by [alexknowshtml](https://github.com/alexknowshtml/claude-skills/tree/main/teach).
- Upstream attribution preserved: original concept by Suzanne (Anthropic), shared by @trq212 (ThariqS) as a public gist (gender-neutral they/them variant contributed by gist commenter moamiwala); session sourcing + checklist tracking by alexknowshtml. Both upstream sources are unlicensed (no SPDX id to inherit), so this is a **credited verbatim port** — the upstream prompt text is reproduced unmodified with full attribution and is **not relicensed**; the marketplace entry's `license` field is set to `UNLICENSED`.
- `SKILL.md`: the teaching-loop spine — when-to-use, the four usage modes (`/teach <topic>`, `/teach <path/to/file>`, `/teach <topic> --student <name>`, and bare `/teach` for the 10 most recent sessions), the source-resolution → setup → teaching-loop flow, the solo and teaching-mode loops, the 100%-completion gate, and a key-rules table. Sources sessions from `~/.claude/projects/` and tracks a per-concept checklist (Problem / Solution / Broader Context).
- `references/teaching-prompt.md`: the behavioral source of truth — the verbatim original persona/quiz prompt in both variants (the gendered original from the ThariqS gist; the gender-neutral they/them variant by gist commenter moamiwala), under a "Provenance & license" note (sources unlicensed, credited port, reproduced unmodified, not relicensed).
- `references/checklist-and-workflow.md`: the dated checklist file format (`sessions/teaching/YYYY-MM-DD-<slug>.md`), the three sections with example items, the commit step, and the completion gate.
- `references/session-sourcing.md`: topic search across `~/.claude/projects/`, narrative synthesis, plus the direct-file and no-argument sourcing modes.
