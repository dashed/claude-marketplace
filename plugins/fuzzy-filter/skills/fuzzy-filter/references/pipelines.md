# Fuzzy-Filter Pipeline Recipes

A catalog of non-interactive `rg`/`fd`/`rga` → `fzf --filter` pipelines, plus the
**exact command equivalent of each fuzzy-search MCP tool** so you can replicate
the MCP on the bare command line.

All recipes verified against **ripgrep 14.1.1**, **fzf 0.55**, **fd 8.6**, and
**ripgrep-all 0.10.9**. Version-specific flags are annotated.

## Table of Contents

- [Mental model](#mental-model)
- [File search](#file-search)
- [Content search](#content-search)
- [Document & PDF search](#document--pdf-search)
- [NUL-safe end-to-end](#nul-safe-end-to-end)
- [Limiting, sorting, hand-off](#limiting-sorting-hand-off)
- [Replicate the MCP](#replicate-the-mcp)

## Mental model

```
scan (regex, gitignore-aware)        rank (fuzzy, fzf syntax)
  rg --files / fd                ──▶  fzf --filter QUERY                # files
  rg --line-number --no-heading  ──▶  fzf --filter QUERY --delimiter : --nth=…   # content
  rga --no-heading --line-number ──▶  fzf --filter QUERY --delimiter : --nth=3.. # documents
```

Stage 1 uses **regex**; Stage 2 uses **fzf fuzzy syntax** (not regex). A `.`
Stage-1 pattern hands every line to fzf; a real regex pre-narrows.

## File search

```bash
# ripgrep file list (gitignore-aware) → fuzzy by path
rg --files | fzf --filter 'src model user'

# include hidden files
rg --files --hidden | fzf --filter 'config'

# fd as the source (matches names by default; also gitignore-aware)
fd --type f | fzf --filter 'test util'

# bias ranking toward path components
rg --files | fzf --scheme=path --filter 'cmd main'        # (fzf 0.36+)

# multiline: match files by a combination of their CONTENT lines
#   (read whole files as NUL-separated records, fuzzy-match across lines)
rg --files --null | while IFS= read -r -d '' f; do
  printf '%s\0' "$(cat "$f")"
done | fzf --read0 --filter 'TODO license'
```

## Content search

```bash
# Default: match on path (field 1) + content (field 3..), skip line number (field 2)
rg --line-number --no-heading --color=never . PATH \
  | fzf --filter 'def test_ seer credit' --delimiter : --nth=1,3..

# Content-only: match ONLY the line text
rg --line-number --no-heading --color=never . PATH \
  | fzf --filter 'render widget' --delimiter : --nth=3..

# Pre-narrow Stage 1 with a real regex, then fuzzy-rank the survivors
rg --line-number --no-heading --color=never 'fn \w+' src \
  | fzf --filter 'handler request' --delimiter : --nth=3..

# Pass extra ripgrep flags (type filter, smart-case, etc.) in Stage 1
rg --line-number --no-heading --color=never -t py . . \
  | fzf --filter 'async def' --delimiter : --nth=3..

# Hide the file:line: prefix from the OUTPUT but still match content
rg --line-number --no-heading --color=never . PATH \
  | fzf --filter 'QUERY' --delimiter : --nth=3.. --with-nth=3..
```

> `--color=never` is mandatory before `--filter`: ANSI codes corrupt matching and
> field splitting. `--nth` chooses what fzf *matches*; `--with-nth` chooses what
> it *displays*; the full row is printed unless you set `--with-nth`.

## Document & PDF search

Requires `rga`. `(rga 0.10+)`

```bash
# Flattened rows (simplest CLI form) → fuzzy-rank the content
rga --no-heading --line-number --color=never . PATH \
  | fzf --filter 'invoice total' --delimiter : --nth=3..

# Restrict to specific formats via rga adapters
rga --no-heading --line-number --color=never --rga-adapters=+poppler . PATH \
  | fzf --filter 'QUERY' --delimiter : --nth=3..     # PDFs only
rga --no-heading --line-number --color=never --rga-adapters=+pandoc . PATH \
  | fzf --filter 'QUERY' --delimiter : --nth=3..     # docx/epub/odt

# JSON variant (what the MCP parses) — events are one JSON object per line
rga --json --no-heading 'PATTERN' PATH \
  | rg '"type":"match"'        # then parse data.lines.text / data.path.text
```

Adapter map used by the MCP's `file_types` argument: `pdf→poppler`,
`docx/doc/epub→pandoc`, `zip→zip`, `tar→tar`, `sqlite/db→sqlite`. See
[pdf.md](pdf.md) for PDF extraction/outline once you've located a hit.

## NUL-safe end-to-end

Newline-delimited pipes break on filenames containing spaces or newlines. Go
NUL-delimited the whole way:

```bash
# Files
rg --files --null | fzf --read0 --print0 --filter 'src model' | xargs -0 "$EDITOR"
fd --print0 --type f | fzf --read0 --print0 --filter 'report' | xargs -0 -n1 echo

# Content rows generally don't contain NULs, but you can still print0 the result
rg --line-number --no-heading --color=never . PATH \
  | fzf --filter 'QUERY' --delimiter : --nth=3.. --print0 \
  | xargs -0 -n1 echo
```

`--read0` = read NUL-separated input; `--print0` = emit NUL-separated output;
pair with `xargs -0`.

## Limiting, sorting, hand-off

```bash
# Cap to the top N matches (fzf prints best-first)
rg --files | fzf --filter 'QUERY' | head -n 20

# Open the single best content hit at its line in your editor (vim/nvim)
match=$(rg --line-number --no-heading --color=never . . \
  | fzf --filter 'QUERY' --delimiter : --nth=3.. | head -n1)
file=${match%%:*}; rest=${match#*:}; line=${rest%%:*}
"$EDITOR" "+$line" "$file"

# Feed fuzzy-selected files into a second ripgrep pass (NUL-safe)
rg --files --null | fzf --read0 --print0 --filter 'src' \
  | xargs -0 rg 'TODO'

# Count fuzzy matches
rg --line-number --no-heading --color=never . . \
  | fzf --filter 'QUERY' --delimiter : --nth=3.. | wc -l
```

> `fzf --filter` already ranks best-first, so `head -n N` is the idiomatic
> "limit" (the MCP's `limit` argument does the same truncation). For a stable
> alphabetical order instead of relevance, append `| sort`.

## Replicate the MCP

The exact pipeline behind each `mcp__plugin_fuzzy-search_fuzzy-search__*` tool.
`QUERY` is the tool's `fuzzy_filter` argument; `PATH` is `path`; `limit` maps to
a trailing `head -n N`.

### `fuzzy_search_files(fuzzy_filter, path, hidden, limit)`

```bash
rg --files PATH [--hidden] | fzf --filter QUERY | head -n LIMIT
```
The MCP runs `rg --files [--hidden] PATH | fzf --filter QUERY`. With
`multiline=true` it instead builds NUL-separated whole-file records and runs
`fzf --read0 --print0 --filter QUERY`.

### `fuzzy_search_content(fuzzy_filter, path, hidden, rg_flags, content_only, limit)`

```bash
# default (content_only=false): match path + content, skip line number
rg --line-number --no-heading --color=never [--hidden] [RG_FLAGS] . PATH \
  | fzf --filter QUERY --delimiter : --nth=1,3.. | head -n LIMIT

# content_only=true: match content only
rg --line-number --no-heading --color=never [--hidden] [RG_FLAGS] . PATH \
  | fzf --filter QUERY --delimiter : --nth=3.. | head -n LIMIT
```
When `PATH` is a single file the MCP adds `--with-filename` so the `file:` field
is still present. `rg_flags` is split on whitespace and inserted into Stage 1.

### `fuzzy_search_documents(fuzzy_filter, path, file_types, limit)`

```bash
rga --json --no-heading [--rga-adapters=+ADAPTERS] QUERY PATH \
  | <parse JSON 'match' events> | fzf --filter QUERY | head -n LIMIT
```
Note the quirk: the MCP passes `fuzzy_filter` to rga **as the initial regex
pattern** *and* again to `fzf --filter`. On the CLI the flattened form is simpler
and avoids the double meaning:
```bash
rga --no-heading --line-number --color=never [--rga-adapters=+ADAPTERS] . PATH \
  | fzf --filter QUERY --delimiter : --nth=3.. | head -n LIMIT
```

### PDF tools

`extract_pdf_pages`, `get_pdf_outline`, `get_pdf_page_count`,
`get_pdf_page_labels` are PyMuPDF/poppler operations, not fzf pipelines — their
CLI analogs (`pdftotext`, `pdfinfo`, PyMuPDF one-liners) are in [pdf.md](pdf.md).
`get_pdf_outline`'s optional `fuzzy_filter` is itself a
`printf '%s' titles | fzf --filter QUERY` pass.
