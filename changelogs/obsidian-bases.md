# Changelog - obsidian-bases

All notable changes to the obsidian-bases skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-05

### Added
- Initial addition to the marketplace — a skill for authoring **Obsidian Bases** (`.base` files): the YAML format that turns notes into database-like views.
- Ported **verbatim** from the upstream [obsidian-bases](https://github.com/kepano/obsidian-skills/tree/main/skills/obsidian-bases) skill by Steph Ango (@kepano), licensed under MIT.
- `SKILL.md`: the creation workflow; the `.base` schema (`filters`/`formulas`/`properties`/`summaries`/`views`); filter syntax with the operator table and recursive `and`/`or`/`not`; the three property types (note/file/formula) and the `file.*` properties table; the `this` keyword; formula syntax; key functions plus the Duration `.days` caveat and date arithmetic; the four view types (`table`/`cards`/`list`/`map`); the default summary formulas table; three complete worked examples (task tracker, reading list, daily-notes index); base embedding (`![[MyBase.base#View]]`); YAML quoting rules; and troubleshooting.
- `references/FUNCTIONS_REFERENCE.md`: the complete per-type function reference — global, Any, Date, Duration, String, Number, List, File, Link, Object, and RegExp functions with signatures.
- The `references/FUNCTIONS_REFERENCE.md` file is byte-identical to upstream; `SKILL.md` differs only by an appended `## Credits` attribution block.
