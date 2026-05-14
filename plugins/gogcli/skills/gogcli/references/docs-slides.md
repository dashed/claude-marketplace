# Docs and Slides — gogcli

Docs commands live under `gog docs` (alias `doc`). Slides commands live under `gog slides` (alias `slide`).

## Table of contents

- [Docs: inspect](#docs-inspect)
- [Docs: create / copy / export](#docs-create--copy--export)
- [Docs: append / insert / rewrite content](#docs-append--insert--rewrite-content)
- [Docs: find-replace](#docs-find-replace)
- [Docs: sed-style regex edits](#docs-sed-style-regex-edits)
- [Docs: comments](#docs-comments)
- [Docs: tab-aware editing](#docs-tab-aware-editing)
- [Slides: inspect](#slides-inspect)
- [Slides: create / copy / export](#slides-create--copy--export)
- [Slides: edit and generate content](#slides-edit-and-generate-content)

## Docs: inspect

```bash
gog docs info <docId> --json
gog docs cat  <docId>                       # Plain-text dump of the default tab.
gog docs cat  <docId> --tab "Agenda"
gog docs cat  <docId> --tab-id <tabId>
gog docs cat  <docId> --all-tabs --max-bytes 200000
gog docs list-tabs <docId> --json
```

`--tab-id` is the stable identifier. Tab-aware editing requires `--tab-id` (not `--tab`); see [Tab-aware editing](#docs-tab-aware-editing).

## Docs: create / copy / export

```bash
gog docs create "Design notes"                         # Empty doc.
gog docs create "Design notes" --file ./notes.md       # Import Markdown on create.
gog docs create "Design notes" --pageless               # Pageless view.

gog docs copy <docId> "New title"

gog docs export <docId> --format pdf  --out ./doc.pdf
gog docs export <docId> --format docx --out ./doc.docx
gog docs export <docId> --format txt  --out ./doc.txt
gog docs export <docId> --format md   --out ./doc.md
gog docs export <docId> --format html --out ./doc.html
```

## Docs: append / insert / rewrite content

Two complementary commands:

- `gog docs update` — targeted edit (append / insert at index / apply a patch).
- `gog docs write` — rewrite the entire tab contents from text or file.

```bash
# Append plain text.
gog docs update <docId> --text "New paragraph." --append

# Append from a file (e.g. Markdown).
gog docs update <docId> --file ./changes.md --append

# Insert at a specific character index.
gog docs update <docId> --text "Inserted sentence." --index 42

# Overwrite the tab with file contents.
gog docs write <docId> --file ./new-body.md

# Overwrite a specific tab.
gog docs write <docId> --tab-id <tabId> --file ./new-body.md

# Toggle pageless while writing.
gog docs write <docId> --file ./body.md --pageless
```

## Docs: find-replace

```bash
# Replace every occurrence.
gog docs find-replace <docId> "draft" "final"

# Replace only the first occurrence.
gog docs find-replace <docId> "TODO" "DONE" --first

# Replacement content from a file (supports Markdown + inline images).
gog docs find-replace <docId> "{{body}}" --content-file ./section.md

# Constrain to a tab.
gog docs find-replace <docId> "old" "new" --tab-id <tabId>
```

## Docs: sed-style regex edits

```bash
gog docs sed <docId> 's/v1/v2/g'
gog docs sed <docId> 's/Beta\\s+\\d+/Beta 9/i'
gog docs sed <docId> 's/(TODO)/**\\1**/g'             # Markdown bold around matches.
```

`sed` supports Markdown formatting in the replacement (e.g. `**bold**`, `*italic*`, `[link](url)`).

## Docs: comments

```bash
gog docs comments list    <docId> --json
gog docs comments create  <docId> --content "Please review §3"
gog docs comments resolve <docId> <commentId>
gog docs comments delete  <docId> <commentId>
```

## Docs: tab-aware editing

Tab-aware commands (`update`, `write`, `find-replace`) require `--tab-id`, not a tab name:

```bash
# Discover.
gog docs list-tabs <docId> --json

# Edit.
gog docs write <docId> --tab-id t.abc123 --file ./rewrite.md
```

Reason: tab IDs are stable, whereas names can be edited in the UI and collide.

## Slides: inspect

```bash
gog slides info <presentationId> --json
gog slides read <presentationId> --slide 1 --json
gog slides read <presentationId> --all --json
```

## Slides: create / copy / export

```bash
# Empty deck.
gog slides create "Q2 Kickoff"

# Generate from Markdown.
gog slides create "Q2 Kickoff" --file ./deck.md

# Generate from a template (copies the template then replaces placeholders).
gog slides create "Q2 Kickoff" --template <templatePresentationId>

gog slides copy <presentationId> "Q2 Kickoff (copy)"

gog slides export <presentationId> --format pdf  --out ./deck.pdf
gog slides export <presentationId> --format pptx --out ./deck.pptx
```

## Slides: edit and generate content

```bash
# Add a slide from a layout.
gog slides add-slide <presentationId> --layout TITLE_AND_BODY

# Add a slide from a Markdown block.
gog slides add-slide <presentationId> --markdown "# Title\n\n- Point 1\n- Point 2"

# Delete a slide by index (1-based) or object ID.
gog slides delete-slide <presentationId> --slide 3
gog slides delete-slide <presentationId> --slide-id g123abc

# Replace a slide's body.
gog slides replace-slide <presentationId> --slide 2 --markdown "# Updated\n\nNew bullets"

# Speaker notes.
gog slides update-notes <presentationId> --slide 2 --notes "Cover partnerships here."
gog slides read <presentationId> --slide 2 --json | jq '.notes'
```

Expect `add-slide`, `replace-slide`, and `update-notes` to accept Markdown input where the upstream documentation says so; use `--dry-run` where available before running batch edits.
