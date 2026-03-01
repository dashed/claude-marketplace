---
name: walkthrough-to-obsidian
description: "Convert game walkthroughs and guides from plain text into structured, interlinked Obsidian markdown pages. Use when the user wants to convert a walkthrough, FAQ, guide, or reference document into Obsidian vault pages. Triggers on mentions of converting walkthroughs, guides, or FAQs to Obsidian, or splitting a large text file into Obsidian pages."
license: MIT
---

# Walkthrough to Obsidian

Convert plain-text walkthroughs, guides, and reference documents into a structured set of interlinked Obsidian markdown pages. Preserves ALL content from the source while organizing it into navigable, cross-referenced pages.

## When to Use

- User wants to convert a walkthrough or guide (`.txt`, `.md`, or other text) into Obsidian pages
- User wants to split a large document into multiple interlinked Obsidian pages
- User mentions converting a FAQ, reference guide, or game walkthrough for their Obsidian vault

## Workflow Overview

The conversion follows 7 phases. Use agent teams for phases 4-7 when the source document is large.

```
Phase 1: Analyze Source → Phase 2: Plan Breakdown → Phase 3: Create Stub + Index
    → Phase 4: Convert Pages → Phase 5: Audit → Phase 6: Navigation → Phase 7: Cross-links
```

## Phase 1: Analyze Source

1. Read the entire source file
2. Identify the document structure:
   - Title and author/attribution
   - Table of contents or part listings
   - Major sections and subsections
   - Special content: tables, ASCII art, maps, stat blocks
   - Dedication/acknowledgements
3. Count sections and estimate page count

## Phase 2: Plan Page Breakdown

1. Use sequential thinking to plan the page structure
2. Decide how to split content into pages:
   - Each major section (Part/Chapter) becomes its own page
   - Group related small sections if they'd be too short alone
   - Keep large sections (e.g., quest guides, item lists) as single pages even if long
3. Define the page order and naming convention
4. Plan the directory structure:
   ```
   parent_topic/
   ├── Topic Name.md              (stub/parent page)
   └── topic_walkthrough/
       ├── Topic Walkthrough Index.md  (index/hub page)
       ├── Topic - Section 1.md
       ├── Topic - Section 2.md
       └── ...
   ```

## Phase 3: Create Stub + Index Pages

### Parent Stub Page

Create or update the parent topic page:

```markdown
---
Links: "[[Parent Index]]"
tags:
  - relevant-tag
---
# Topic Name

Brief description of the topic.

# Walkthroughs

- [[Walkthrough Index|Author's Walkthrough (Year)]] - brief description

## See also

- [[Related Topic 1]]
- [[Related Topic 2]]
```

### Index Page

Create the walkthrough index/hub page with:

- YAML frontmatter with `Links:` back to parent and `tags:`
- Copyright/attribution notice (blockquote)
- Full introductory text from source (do NOT condense)
- Controls/key reference table (if applicable)
- Numbered list linking to all content pages
- Structure overview (if applicable)
- Acknowledgements (if present in source)

## Phase 4: Convert Content Pages

For each content page:

1. **Frontmatter**: Add YAML with `Links: "[[Index Page]]"` and `tags:`
2. **Content**: Convert ALL source text to Obsidian markdown:
   - Preserve every paragraph, sentence, and detail
   - Do NOT summarize, condense, or omit anything
   - See [references/formatting-guide.md](references/formatting-guide.md) for formatting rules
3. **Structure**: Use proper heading hierarchy (`##` for sections, `###` for subsections)

### Parallelization with Agent Teams

For large documents, split the conversion work across multiple agents:

- Assign ~3-5 pages per agent
- Each agent reads the source file sections and creates the Obsidian pages
- Agents work in parallel for efficiency
- Each agent should use the formatting guide for consistency

### Critical Rules

- **Never omit content.** Every sentence from the source must appear in the output.
- **Preserve the author's voice.** Keep original wording, humor, emphasis, and style.
- **Preserve special characters.** Accent marks (è, à, ê), emoticons, and unicode.
- **Preserve ASCII art.** Wrap in code blocks (` ``` `) to maintain formatting.
- **Preserve original typos.** Only fix typos that would cause confusion. Note corrections.
- **Keep double punctuation.** If the author uses `!!` or `??`, preserve it.
- **Keep spaces before punctuation.** If the author's style uses `word !` or `word ?`, preserve it.

## Phase 5: Audit

Verify every page against the original source:

1. Read each Obsidian page alongside its source section
2. Compare paragraph by paragraph
3. Check for:
   - Missing paragraphs or sentences
   - Altered wording or lost emphasis
   - Missing special characters or accents
   - Lost ASCII art or table formatting
   - Wrong names, numbers, or statistics
   - Missing entries in lists or tables
4. Fix any issues found directly
5. Report findings with severity ratings

### Parallelization

Split audit across multiple agents, ~4 pages per agent. Each agent reads the source AND the page, compares, and fixes issues in-place.

## Phase 6: Add Navigation

Add a navigation footer to every content page (not the index):

```markdown

---
**Navigation:** [[Prev Page|← Part N: Title]] | [[Index Page|Index]] | [[Next Page|Part N: Title →]]
```

Rules:
- First page: no previous link, just Index and Next
- Last page: no next link, just Previous and Index
- Blank line before `---` so it renders as horizontal rule
- Use wiki-link aliases for clean display

## Phase 7: Add Cross-links

Add contextual wiki-links between related pages. See [references/cross-linking-guide.md](references/cross-linking-guide.md) for the full taxonomy.

### High-Value Cross-links

| Link Type | Example |
|-----------|---------|
| NPC/Character → Quest references | `[[Quests#Quest Name\|"Quest Name"]]` |
| Quest rewards → Item pages | `[[Items#Item Name\|Item Name]]` |
| Level/area pages ↔ Quest pages | Bidirectional area references |
| Spell/ability mentions → Spell page | `[[Spells#Spell Name\|Spell Name]]` |
| Boss/enemy mentions → Bestiary | `[[Bestiary\|Boss Name]]` |

### Cross-linking Rules

- Link the **first meaningful mention** only, not every occurrence
- Use **aliases** to keep visible text natural
- Read target pages first to verify exact heading names for anchors
- Add **"See also"** cross-references between related reference pages
- Don't overlink — if it feels cluttered, skip it

## Quality Checklist

Before declaring the conversion complete:

- [ ] Every section from the source has a corresponding page
- [ ] All content preserved — nothing omitted or summarized
- [ ] YAML frontmatter on every page with `Links:` and `tags:`
- [ ] Index page links to all content pages
- [ ] Parent stub page links to the index
- [ ] Navigation footers on all content pages (prev/next/index)
- [ ] Cross-links between related pages
- [ ] ASCII art preserved in code blocks
- [ ] Tables properly formatted with pipes and alignment
- [ ] Special characters and accents preserved
- [ ] Attribution/copyright notice on index page
