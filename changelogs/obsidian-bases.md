# Changelog - obsidian-bases

All notable changes to the obsidian-bases skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.1] - 2026-06-05

### Added
- Folded in four stable items from the current official Bases docs that the upstream port omitted (each verified against help.obsidian.md before adding):
  - `random()` global function (`random(): number`, refreshes on each view load) in `references/FUNCTIONS_REFERENCE.md`. Source: https://help.obsidian.md/bases/functions
  - `file.file` property (the file object itself, only usable in specific functions) in the `SKILL.md` file-properties table. Source: https://help.obsidian.md/bases/syntax
  - an Arithmetic Operators table (`+` `-` `*` `/` `%` `( )`) under Formula Syntax in `SKILL.md`. Source: https://help.obsidian.md/bases/syntax
  - the inline `base` code-block embed method (define a base in a note via a fenced ` ```base ` block) in `SKILL.md`. Source: https://help.obsidian.md/bases/syntax
- `SKILL.md` `## Credits` now records these local additions.

### Notes
- Deliberately left out (unverifiable against official docs): a view-level `sort:` YAML key (sorting is documented only as a UI interaction; the schema shows `order`/`groupBy`) and Duration `.years`/`.months`/`.weeks` fields (no Duration field table exists in the official functions docs). Omitted to avoid shipping unverified syntax.

## [1.0.0] - 2026-06-05

### Added
- Initial addition to the marketplace — a skill for authoring **Obsidian Bases** (`.base` files): the YAML format that turns notes into database-like views.
- Ported **verbatim** from the upstream [obsidian-bases](https://github.com/kepano/obsidian-skills/tree/main/skills/obsidian-bases) skill by Steph Ango (@kepano), licensed under MIT.
- `SKILL.md`: the creation workflow; the `.base` schema (`filters`/`formulas`/`properties`/`summaries`/`views`); filter syntax with the operator table and recursive `and`/`or`/`not`; the three property types (note/file/formula) and the `file.*` properties table; the `this` keyword; formula syntax; key functions plus the Duration `.days` caveat and date arithmetic; the four view types (`table`/`cards`/`list`/`map`); the default summary formulas table; three complete worked examples (task tracker, reading list, daily-notes index); base embedding (`![[MyBase.base#View]]`); YAML quoting rules; and troubleshooting.
- `references/FUNCTIONS_REFERENCE.md`: the complete per-type function reference — global, Any, Date, Duration, String, Number, List, File, Link, Object, and RegExp functions with signatures.
- The `references/FUNCTIONS_REFERENCE.md` file is byte-identical to upstream; `SKILL.md` differs only by an appended `## Credits` attribution block.
