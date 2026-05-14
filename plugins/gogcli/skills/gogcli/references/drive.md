# Drive — gogcli

All commands under `gog drive` (alias `drv`). Root-alias shortcuts: `gog ls`, `gog list`, `gog search`, `gog find`, `gog download`, `gog dl`, `gog upload`, `gog up`, `gog put`.

## Table of contents

- [Listing](#listing)
- [Searching](#searching)
- [Metadata and URLs](#metadata-and-urls)
- [Download](#download)
- [Upload (and Workspace conversion)](#upload-and-workspace-conversion)
- [Folders and organization](#folders-and-organization)
- [Delete and trash](#delete-and-trash)
- [Sharing and permissions](#sharing-and-permissions)
- [Shared drives](#shared-drives)
- [Copy](#copy)

## Listing

```bash
gog drive ls                          # Default: upcoming/recent items.
gog drive ls --all                    # All files you have access to.
gog drive ls --parent <folderId>      # Direct children of a folder.
gog drive ls --max 50 --page <TOKEN>
gog drive ls --query "mimeType='application/pdf'"
gog drive ls --no-all-drives          # Restrict to "My Drive" (default includes shared drives).
```

`--all` and `--parent` are **mutually exclusive**.

## Searching

```bash
gog drive search "quarterly report" --max 20 --json

# Pass a raw Drive API q= expression.
gog drive search --raw-query "mimeType = 'application/vnd.google-apps.spreadsheet' and modifiedTime > '2026-01-01T00:00:00Z'"
```

## Metadata and URLs

```bash
gog drive get <fileId>
gog drive url <fileId1> <fileId2>     # Print sharable web URLs for the given IDs.
```

## Download

```bash
# Binary / user-uploaded files.
gog drive download <fileId> --out ./file.pdf

# Workspace files — export format is required.
gog drive download <docId>   --format pdf  --out ./doc.pdf
gog drive download <docId>   --format docx --out ./doc.docx
gog drive download <docId>   --format md   --out ./doc.md
gog drive download <sheetId> --format xlsx --out ./sheet.xlsx
gog drive download <slidesId> --format pptx --out ./deck.pptx
```

`--format` is Workspace-only. Passing it for a binary/user file returns an error.

## Upload (and Workspace conversion)

```bash
# Plain upload.
gog drive upload ./report.pdf --parent <folderId>

# Rename on upload.
gog drive upload ./report.pdf --name "Q1 Report.pdf" --parent <folderId>

# Replace an existing file (same ID, new content).
gog drive upload ./updated.pdf --replace <fileId>

# Convert on upload (Markdown → Google Docs, XLSX → Sheets, PPTX → Slides).
gog drive upload ./spec.md    --convert-to doc
gog drive upload ./data.xlsx  --convert-to sheet
gog drive upload ./deck.pptx  --convert-to slides
gog drive upload ./doc.docx   --convert                 # auto-detect.
```

## Folders and organization

```bash
gog drive mkdir "Project X"                 # Create at My Drive root.
gog drive mkdir "Specs" --parent <folderId>

gog drive rename <fileId> "New Name"
gog drive move   <fileId> --parent <newFolderId>
```

## Delete and trash

```bash
gog drive delete <fileId>                # Trash. Reversible from the web UI.
gog drive delete <fileId> --permanent    # Hard delete. Irreversible.
gog drive delete <fileId> --dry-run      # Preview only.
```

## Sharing and permissions

```bash
# Share with a specific user.
gog drive share <fileId> --to user --email alice@example.com --role reader
gog drive share <fileId> --to user --email alice@example.com --role writer

# Share with a domain.
gog drive share <fileId> --to domain --domain example.com --role reader

# Public (anyone with the link). Even under --no-input, requires --force.
gog drive share <fileId> --to anyone --role reader --discoverable --force

# Inspect current permissions.
gog drive permissions <fileId> --json

# Remove a permission by ID.
gog drive unshare <fileId> <permissionId>
```

Roles accepted: `reader`, `writer`. `--discoverable` controls whether the file is findable via search for `--to anyone`.

## Shared drives

```bash
gog drive drives                         # List shared drives you can access.
gog drive drives --query "name contains 'Platform'"
```

Most operations accept files living in shared drives automatically. `--all-drives` is on by default; pass `--no-all-drives` to restrict to My Drive.

## Copy

```bash
gog drive copy <fileId> "New name"
```

Copies metadata and content, placing the copy next to the original unless you follow up with `gog drive move`.
