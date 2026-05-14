# Sheets — gogcli

All commands under `gog sheets` (alias `sheet`). Spreadsheet ID = the long path segment in the Google Sheets URL.

## Table of contents

- [Metadata and discovery](#metadata-and-discovery)
- [Read](#read)
- [Write (update / append / clear)](#write-update--append--clear)
- [Insert rows and columns](#insert-rows-and-columns)
- [Find and replace](#find-and-replace)
- [Named ranges](#named-ranges)
- [Tab management](#tab-management)
- [Formatting, merge, freeze](#formatting-merge-freeze)
- [Notes and links](#notes-and-links)
- [Create / copy / export](#create--copy--export)
- [Range syntax tips](#range-syntax-tips)

## Metadata and discovery

```bash
gog sheets metadata <spreadsheetId> --json
```

Returns the list of tabs (sheets), their IDs, sizes, and properties.

## Read

```bash
# A1 range.
gog sheets get <spreadsheetId> "Sheet1!A1:C10" --json

# Named range.
gog sheets get <spreadsheetId> "Roster"

# Project fields.
gog sheets get <spreadsheetId> "Data!A:F" --json --select "values[]" --results-only
```

## Write (update / append / clear)

```bash
# Update a range with a CSV-like positional value list.
gog sheets update <spreadsheetId> "Sheet1!A2:C2" "Alice,42,engineer"

# Update with structured JSON values (2D array).
gog sheets update <spreadsheetId> "Sheet1!A2:C3" \
    --values-json '[["Alice",42,"engineer"],["Bob",41,"manager"]]'

# Copy the validation rules from another range.
gog sheets update <spreadsheetId> "Sheet1!D2:D10" "x,x,x,x,x,x,x,x,x" \
    --copy-validation-from "Template!D2:D10"

# Append to the next empty row.
gog sheets append <spreadsheetId> "Sheet1!A:C" "Carol,38,designer"

# Clear contents (leaves formatting).
gog sheets clear <spreadsheetId> "Sheet1!A2:C100"
```

## Insert rows and columns

```bash
# Insert 2 rows before row 5.
gog sheets insert <spreadsheetId> Sheet1 rows 5 --count 2

# Insert 1 column after column 3.
gog sheets insert <spreadsheetId> Sheet1 cols 3 --count 1 --after
```

## Find and replace

```bash
gog sheets find-replace <spreadsheetId> "TODO" "DONE" --sheet "Tracking"

# Regex match.
gog sheets find-replace <spreadsheetId> "^draft$" "final" --regex --match-entire

# Match inside formulas too.
gog sheets find-replace <spreadsheetId> "=SUM" "=SUMPRODUCT" --formulas
```

| Flag | Effect |
|---|---|
| `--sheet <name>` | Limit to one tab. |
| `--match-entire` | Match only if the whole cell equals the pattern. |
| `--regex` | Treat `old` as a regex. |
| `--formulas` | Include cell formulas, not just displayed values. |

## Named ranges

```bash
gog sheets named-ranges list <spreadsheetId>
gog sheets named-ranges get  <spreadsheetId> "Roster"

# Create.
gog sheets named-ranges add    <spreadsheetId> "Roster" "Sheet1!A2:C100"

# Move / rename.
gog sheets named-ranges update <spreadsheetId> "Roster" --range "Sheet1!A2:C200"
gog sheets named-ranges update <spreadsheetId> "Roster" --name "TeamRoster"

# Delete.
gog sheets named-ranges delete <spreadsheetId> "Roster"
```

## Tab management

```bash
gog sheets add-tab    <spreadsheetId> "New Tab"
gog sheets rename-tab <spreadsheetId> "Old Name" "New Name"

# Delete a tab (honors --dry-run, confirms unless --force).
gog sheets delete-tab <spreadsheetId> "Old Tab"
gog sheets delete-tab <spreadsheetId> "Old Tab" --dry-run
gog sheets delete-tab <spreadsheetId> "Old Tab" --force
```

## Formatting, merge, freeze

```bash
# Bulk format via JSON payload + field mask.
gog sheets format <spreadsheetId> "Sheet1!A1:D1" \
    --format-json '{"backgroundColor":{"red":0.95,"green":0.95,"blue":0.95},"textFormat":{"bold":true}}' \
    --format-fields "backgroundColor,textFormat.bold"

# Merge / unmerge.
gog sheets merge   <spreadsheetId> "Sheet1!A1:D1"
gog sheets unmerge <spreadsheetId> "Sheet1!A1:D1"

# Number format.
gog sheets number-format <spreadsheetId> "Sheet1!B2:B" \
    --type NUMBER --pattern "#,##0.00"

# Freeze rows/columns.
gog sheets freeze <spreadsheetId> Sheet1 --rows 1 --cols 0

# Auto-resize columns / rows.
gog sheets resize-columns <spreadsheetId> "Sheet1!A:E"
gog sheets resize-rows    <spreadsheetId> "Sheet1!1:100"

# Read current formatting.
gog sheets read-format <spreadsheetId> "Sheet1!A1:D1" --json
gog sheets read-format <spreadsheetId> "Sheet1!A1:D1" --effective  # resolved values.
```

## Notes and links

```bash
gog sheets notes <spreadsheetId> "Sheet1!A1:D10" --json

# Set a note.
gog sheets update-note <spreadsheetId> "Sheet1!B2" --note "Verified 2026-04-15"
gog sheets set-note    <spreadsheetId> "Sheet1!B2" --note ""   # Clear note.

# Inspect hyperlinks.
gog sheets links <spreadsheetId> "Sheet1!A1:D" --json
```

## Create / copy / export

```bash
# Create a new spreadsheet.
gog sheets create "Q2 Metrics" --sheets "Summary,Data,Notes" --parent <folderId>

# Copy.
gog sheets copy <spreadsheetId> "Q2 Metrics (copy)"

# Export.
gog sheets export <spreadsheetId> --format pdf  --out ./q2.pdf
gog sheets export <spreadsheetId> --format xlsx --out ./q2.xlsx
```

## Range syntax tips

- `Sheet1!A1:C10` — explicit tab and A1 range.
- `A1:C10` — first tab by default.
- `Sheet1!A:C` — whole columns.
- `Sheet1!1:5` — whole rows.
- Named ranges are accepted wherever a range is accepted (`get`, `update`, `append`, `clear`).
- Quote ranges that contain spaces: `"Sales Data!A1:D10"`.
