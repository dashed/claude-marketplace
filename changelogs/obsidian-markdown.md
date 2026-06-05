# Changelog - obsidian-markdown

All notable changes to the obsidian-markdown skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-05

### Added
- Initial addition to the marketplace — a skill for authoring **Obsidian Flavored Markdown** (the Obsidian-specific extensions on top of CommonMark/GFM).
- Ported **verbatim** from the upstream [obsidian-markdown](https://github.com/kepano/obsidian-skills/tree/main/skills/obsidian-markdown) skill by Steph Ango (@kepano), licensed under MIT.
- `SKILL.md`: the creating-a-note workflow; per-feature syntax sections — internal links/wikilinks (`[[Note]]`, `[[Note#Heading]]`, `[[Note#^block-id]]`, block IDs), embeds (`![[...]]`), callouts (`> [!type]`), properties/frontmatter, tags, comments (`%%...%%`), highlights (`==...==`), LaTeX math (`$...$` / `$$...$$`), Mermaid diagrams (with `class NodeName internal-link;`), footnotes; and a complete worked example.
- `references/CALLOUTS.md`: basic/foldable/nested callouts, the full table of 13 callout types with aliases and colors/icons, and the custom-CSS `data-callout` pattern.
- `references/EMBEDS.md`: embedding notes, images (`|WxH` / `|width`), external images, audio, PDF (`#page=`, `#height=`), lists by block ID, and search-result `query` embeds.
- `references/PROPERTIES.md`: the property types table, default properties (`tags`/`aliases`/`cssclasses`), and tag character rules.
- The three `references/` files are byte-identical to upstream; `SKILL.md` differs only by an appended `## Credits` attribution block.
