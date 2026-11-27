# Changelog - statechart

All notable changes to the statechart skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.2.0] - 2026-11-27

### Added
- `SKILL.md` adds guard provenance, per-variable writer lists, refusal probes for assumption guards, and re-auditing variables newly read by a fix.
- `Assume_*` sensitivity reruns: for every first-order `Assume_*` operator in the spec not already overridden in the config, the command generates `ChartAssume`, reruns TLC on base-holding rules with that operator overridden to `TRUE` (plus a combined rerun when two or more exist) behind the 100,000-state bound, and reports dependencies under `## Assumptions` in `report.md` without changing the exit code.
- Dogfooded on `statechart` itself in `notes/statechart/lifecycle/CommandRunAudited.tla` and `notes/statechart/assumptions/AssumeCheck.tla`.

### Fixed
- `scripts/statechart.py`: read `report.md` from `stage/done` before `_rename(done, dest)` and close/guard `devnull` in `_print()`, fixing a TOCTOU bug where a post-rename `OSError` could exit `2` after `--out` was already published (`test_report_is_read_before_dest_is_published`).

## [1.1.0] - 2026-11-26

### Changed
- `SKILL.md` has a "Write the labels" section: each state and step label is a clause of about 4 to 12 words that says who does what or what is true, names each actor and thing, and gives a result that the reader needs in parentheses ("TLC failed (exit 2)"). A step label has no comma, because the command joins the labels on one arrow with "or". A label states only what is true in every model state behind it, never a rule. The examples are full labels ("You are paying, and the card is not charged yet"), not one word ("Paying").
- To make a chart less busy, `SKILL.md` says to merge states or move a step that many states share to a parent state, never to shorten labels. Pele and Mermaid 11 wrap long labels; Mermaid 10 does not.
- `notes/statechart/lifecycle/view.py` uses full labels and puts the live states under "The command is alive", so a SIGKILL is one arrow: 14 arrows instead of 22 in the fixed model.

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
