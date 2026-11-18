# Changelog - show-me

All notable changes to the show-me skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.2.0] - 2026-11-18

### Changed
- A request for an explainer HTML file or a walkthrough document goes to code-walkthrough. The `description` excludes it, and one new body bullet after the HTML-file bullet says to use code-walkthrough, which has the template, prose rules, and browser checks an explainer needs. The Credits section names the added bullet.

## [1.1.0] - 2026-10-21

### Fixed
- Asking for the skill in a message ("use show-me", "show me the call tree") no longer fails with "Skill show-me cannot be used with Skill tool due to disable-model-invocation". That flag blocks the Skill tool outright, so only a typed `/show-me` worked.

### Changed
- Remove upstream's `disable-model-invocation: true` from `SKILL.md` and its Codex `agents/openai.yaml` (`allow_implicit_invocation: false`), so the skill behaves the same on both hosts.
- Rewrite the `description` triggers to fire only when the user asks to see the topic ("show me", "/show-me", "diagram this", "visualize this", a call tree, file tree, Mermaid diagram, diff, or one HTML page), and not for ordinary explanations. This replaces the gate the removed flag provided.

## [1.0.0] - 2026-10-21

### Added
- Initial addition to the marketplace: a manual-only `/show-me` skill that explains the current topic with the smallest view that makes the point — pseudocode, a call tree, a component tree, a shallow file tree, a Mermaid diagram, a `diff` of the shape that changes, a whole code block, or one focused HTML page opened with `open`.
- Ported from the upstream [show-me](https://github.com/humanlayer/skills/tree/main/plugins/show-me/skills/show-me) skill by HumanLayer (MIT), at upstream commit `bba9d13ab3` (upstream plugin version 1.0.1).
- `SKILL.md` keeps upstream's `disable-model-invocation: true`, so Claude never loads it on its own. The body is unchanged; the `description` gains a "Use when" clause and the file ends with a `## Credits` section.
- `agents/openai.yaml` is byte-identical to upstream (`allow_implicit_invocation: false`), the Codex counterpart of `disable-model-invocation`.
