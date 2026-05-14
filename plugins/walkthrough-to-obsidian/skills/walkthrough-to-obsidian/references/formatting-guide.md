# Formatting Guide

Detailed Obsidian markdown formatting rules for walkthrough conversions.

## YAML Frontmatter

Every page must have YAML frontmatter:

```yaml
---
Links: "[[Parent Page]]"
tags:
  - topic-tag
  - content-type-tag
---
```

- `Links:` — Required. Points to the parent/index page.
  - Single link: string format `Links: "[[Page]]"`
  - Multiple links: YAML list format
- `tags:` — Must be a YAML list (not a string). Lowercase, no `#` symbols.

## Headings

- `#` — Page title (one per page)
- `##` — Major sections
- `###` — Subsections
- `####` — Sub-subsections (use sparingly)
- Always leave a blank line before and after headings

## Text Formatting

| Markdown | Result |
|----------|--------|
| `**bold**` | Bold — use for emphasis, names, labels |
| `*italic*` | Italic — use for titles, terms |
| `==highlight==` | Highlighted text |
| `` `code` `` | Inline code — use for keys, commands |

## Tables

Convert tabular data to markdown tables:

```markdown
| Header 1 | Header 2 |
| :------- | -------: |
| Left     |    Right |
```

- Use `:` for column alignment (`:---` left, `:---:` center, `---:` right)
- Escape pipes inside table cells with `\|` (needed for wiki-links with aliases)
- Each row must be on a single line

### Converting Fixed-Width Tables

Source text often uses fixed-width columns:

```
NAME            : FIREBOLT
DESCRIPTION     : Fires a small bolt of flame...
SINISTER RATING : 5/5
```

Convert to structured markdown:

```markdown
### Firebolt

**Description:** Fires a small bolt of flame...

**Sinister Rating:** 5/5
```

## Lists

- Unordered lists: `- item` (use hyphens)
- Ordered lists: `1. item`
- Nested lists: indent with 2-4 spaces
- Task lists: `- [ ] unchecked` / `- [x] checked`

## Code Blocks

Use fenced code blocks for:

- ASCII art and maps
- Pre-formatted text that relies on spacing
- Code snippets

````markdown
```
   +---+---+
   | A | B |
   +---+---+
```
````

Always use code blocks for ASCII art — without them, spacing is lost.

## Callouts

Use Obsidian callouts for tips, warnings, and notes:

```markdown
> [!tip] Helpful Tip
> Content of the tip goes here.

> [!warning] Watch Out
> Warning content here.

> [!note]
> General note content.
```

Common callout types: `note`, `tip`, `warning`, `info`, `example`, `quote`

## Horizontal Rules

Use `---` on its own line to create section separators. Ensure a blank line before and after:

```markdown
Content above

---

Content below
```

## Wiki Links

Internal links use double brackets:

- Basic: `[[Page Name]]`
- With alias: `[[Page Name|Display Text]]`
- To heading: `[[Page Name#Heading]]`
- To heading with alias: `[[Page Name#Heading|Display Text]]`

## Blockquotes

Use `>` for attribution, copyright notices, and quoted text:

```markdown
> This walkthrough is copyrighted to Author Name (Year).
> Reproduced with credit to the original author.
```

## Special Characters

Preserve these from the source:

- Accent marks: è, é, ê, ë, à, á, â, etc.
- Em/en dashes: — –
- Emoticons/smileys: :) :( ;) =./
- Author-style punctuation: `!!`, `??`, spaces before `!` and `?`
- Self-censored words: `@rse`, `cr@p` (preserve as-is)

## Converting Common Source Patterns

### Section Headers with ASCII Borders

```
=============================================================================
¦                                 PART ONE                                  ¦
¦                          CHOOSING YOUR CHARACTER                          ¦
=============================================================================
```

Convert to a markdown heading:

```markdown
# Part 1 - Choosing Your Character
```

### Rating Tables

```
USEFULNESS      : 5 out of 5
ANNOYANCE LEVEL : 2 out of 5
```

Convert to a markdown table:

```markdown
| Rating | Score |
| :----- | ----: |
| Usefulness | 5/5 |
| Annoyance | 2/5 |
```

### Stat Blocks

```
Starting Strength:     30
Starting Magic:        10
Starting Dexterity:    20
Starting Vitality:     25
```

Convert to a markdown table:

```markdown
| Stat | Value |
| :--- | ----: |
| Starting Strength | 30 |
| Starting Magic | 10 |
| Starting Dexterity | 20 |
| Starting Vitality | 25 |
```

### Inline Emphasis

Source text often uses ALL CAPS for emphasis. Preserve the caps AND optionally add bold:

- `VERY important` → `**VERY** important` or keep as-is
- Be consistent within a page — pick one approach
