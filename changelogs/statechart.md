# Changelog - statechart

All notable changes to the statechart skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-11-26

### Added
- Initial addition to the marketplace: a skill that checks a TLA+ model with TLC and draws it as a Mermaid statechart in the reader's words. The agent writes the spec and a Python view module (`state()`, `step()`, `group()`, `colors`, `title`); the command marks each state that breaks a rule (`breaks`, `mayBreak`), gives the shortest path to each one, re-runs TLC with each broken rule removed until none breaks, and lists the rules it could not check.
- Adapted from the [statechart](https://github.com/cursor/plugins/tree/main/pstack/skills/statechart) skill in Lauren Tan's pstack plugin for Cursor (MIT), at commit `b7b93c36be`. Its MIT `LICENSE` is at the plugin root. This repository maintains its own version.
- The command (`scripts/statechart.py`) is Python 3.10 or later, standard library only, run with `uv run --script`; the original is TypeScript. `scripts/js.py` keeps the output's JavaScript rules for string order, whitespace, JSON text and object key order. Ported, it wrote byte-identical files to the TypeScript on the original 33-spec corpus (replayed and with real TLC 1.7.4), on 20,000 random charts, and on 30,000 random values, configs and Mermaid labels.
- `make test-statechart` runs ruff, ty, and `tests/test_statechart.py`: the corpus replayed with no TLC or Java (chart, report, exit code and TLC configs), real TLC on each spec when `TLA2TOOLS` is set, and the command's lifecycle paths.
- `SKILL.md` says to write a rule that must hold in the end as a PROPERTY with `~>` and weak fairness, not as an INVARIANT, which breaks between the event and the step that answers it.
- `SKILL.md` also covers splitting oversized models by layer, `SYMMETRY` caveats (unsound symmetry hides bugs; liveness `PROPERTY` checks are unsound under `SYMMETRY`), and checking clean runs for vacuous passes and stated assumptions.
- `notes/statechart/` holds a TLA+ model of the command's own lifecycle, checked with this skill, and what it found.
- `references/render.md` renders charts to SVG with the npm package `pele@1.9.0`.

### Changed
- A view is a Python module rather than JavaScript. It gets each state as JSON, as dicts and lists. `step()` hides a step by returning `None`. Names that the command does not read start with `_` or are left out of `__all__`, and the errors about a view name Python values.
- The lifecycle differs from the original's, after the model above: the janitor starts before the command makes its folders and learns the worker's pid after, the worker kills its own process group when the command's pipe closes, cleanup kills a worker that still runs, and a reader of stdout that goes away no longer changes the exit code. In the original, a SIGKILL in the 4 ms of startup could leave TLC running or folders behind; in the first Python port, a closed stdout made the command exit 120 after it wrote its files, and a janitor that failed to start left TLC running.
- `disable-model-invocation: true` is removed, because it blocks the Skill tool even when the user asks for the skill in a message. The `description` gains narrow "Use when" triggers (`/statechart`, model-checking a state machine or protocol with TLA+ or TLC, a bug as a path through states) and a "Not for" clause that sends plain Mermaid diagrams to mermaid-cli or show-me and explainer HTML files to code-walkthrough.
- `SKILL.md` ends with a `## Credits` section that records the source and these changes.
