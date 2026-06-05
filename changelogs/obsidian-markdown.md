# Changelog - obsidian-markdown

All notable changes to the obsidian-markdown skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.1] - 2026-06-05

### Fixed
- Corrected three details to match the current official Obsidian docs (first local divergence from the verbatim upstream port):
  - **Tag rules** (`SKILL.md`, `references/PROPERTIES.md`): replaced the inaccurate "numbers (not first character)" restriction with the actual rule — a tag must contain at least one non-numeric character (`#1984` invalid, `#y1984` valid) — and noted that most Unicode characters, including emoji, are allowed. Source: https://help.obsidian.md/tags
  - **Property types** (`references/PROPERTIES.md`): removed "Links" from the type table (the core set is six types: Text, List, Number, Checkbox, Date, Date & time); wikilinks are stored inside a quoted Text/List value, preserved as an explanatory note. Source: https://help.obsidian.md/properties
  - **Embeds** (`references/EMBEDS.md`): added the omitted canvas embed `![[My canvas.canvas]]` (renders shapes but not card text). Source: https://help.obsidian.md/embeds
- `SKILL.md` `## Credits` now records that this copy carries minor local accuracy corrections.

## [1.0.0] - 2026-06-05

### Added
- Initial addition to the marketplace — a skill for authoring **Obsidian Flavored Markdown** (the Obsidian-specific extensions on top of CommonMark/GFM).
- Ported **verbatim** from the upstream [obsidian-markdown](https://github.com/kepano/obsidian-skills/tree/main/skills/obsidian-markdown) skill by Steph Ango (@kepano), licensed under MIT.
- `SKILL.md`: the creating-a-note workflow; per-feature syntax sections — internal links/wikilinks (`[[Note]]`, `[[Note#Heading]]`, `[[Note#^block-id]]`, block IDs), embeds (`![[...]]`), callouts (`> [!type]`), properties/frontmatter, tags, comments (`%%...%%`), highlights (`==...==`), LaTeX math (`$...$` / `$$...$$`), Mermaid diagrams (with `class NodeName internal-link;`), footnotes; and a complete worked example.
- `references/CALLOUTS.md`: basic/foldable/nested callouts, the full table of 13 callout types with aliases and colors/icons, and the custom-CSS `data-callout` pattern.
- `references/EMBEDS.md`: embedding notes, images (`|WxH` / `|width`), external images, audio, PDF (`#page=`, `#height=`), lists by block ID, and search-result `query` embeds.
- `references/PROPERTIES.md`: the property types table, default properties (`tags`/`aliases`/`cssclasses`), and tag character rules.
- The three `references/` files are byte-identical to upstream; `SKILL.md` differs only by an appended `## Credits` attribution block.
