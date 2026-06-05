# Properties (Frontmatter) Reference

Properties use YAML frontmatter at the start of a note:

```yaml
---
title: My Note Title
date: 2024-01-15
tags:
  - project
  - important
aliases:
  - My Note
  - Alternative Name
cssclasses:
  - custom-class
status: in-progress
rating: 4.5
completed: false
due: 2024-02-01T14:30:00
---
```

## Property Types

| Type | Example |
|------|---------|
| Text | `title: My Title` |
| Number | `rating: 4.5` |
| Checkbox | `completed: true` |
| Date | `date: 2024-01-15` |
| Date & Time | `due: 2024-01-15T14:30:00` |
| List | `tags: [one, two]` or YAML list |

These are the core property types. Links are **not** a separate type — store a wikilink inside a Text or List value, quoting it so YAML doesn't misparse the brackets: `related: "[[Other Note]]"`, or a YAML list of `"[[...]]"` entries.

## Default Properties

- `tags` - Note tags (searchable, shown in graph view)
- `aliases` - Alternative names for the note (used in link suggestions)
- `cssclasses` - CSS classes applied to the note in reading/editing view

## Tags

```markdown
#tag
#nested/tag
#tag-with-dashes
#tag_with_underscores
```

Tags can contain: letters (any language), numbers, underscores `_`, hyphens `-`, forward slashes `/` (for nesting), and most Unicode characters (including emoji). A tag must contain at least one non-numeric character (`#1984` is invalid; `#y1984` is valid).

In frontmatter:

```yaml
---
tags:
  - tag1
  - nested/tag2
---
```
