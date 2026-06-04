# Documents & PDFs on the Command Line

The CLI analog of the fuzzy-search MCP's document and PDF tools: scan documents
with `rga`, then **extract/inspect** the PDF you located with `pdftotext`
(poppler) or PyMuPDF.

Verified against **ripgrep-all 0.10.9** and **poppler 25.06** (`pdftotext`,
`pdfinfo`).

## Table of Contents

- [Why rga](#why-rga)
- [Fuzzy document search](#fuzzy-document-search)
- [rga adapters & config](#rga-adapters--config)
- [PDF page count & info](#pdf-page-count--info)
- [PDF outline / bookmarks](#pdf-outline--bookmarks)
- [Extract PDF pages](#extract-pdf-pages)
- [PyMuPDF one-liners](#pymupdf-one-liners)

## Why rga

Plain `rg` treats PDFs/Office docs as binary. `rga` (ripgrep-all) wraps rg with
**adapters** that extract text first (via `pdftotext`, `pandoc`, etc.), so the
same scan-then-fuzzy-rank pipeline works over documents. `(rga 0.10+)`

```bash
rga --version       # ripgrep-all + the rg it wraps
```

If `rga` is missing, stop and tell the user (install from
https://github.com/phiresky/ripgrep-all). Do not auto-install.

## Fuzzy document search

```bash
# Scan all supported documents → fuzzy-rank the extracted text
rga --no-heading --line-number --color=never . PATH \
  | fzf --filter 'QUERY' --delimiter : --nth=3..

# PDFs only
rga --no-heading --line-number --color=never --rga-adapters=+poppler . PATH \
  | fzf --filter 'QUERY' --delimiter : --nth=3..
```

This is the CLI equivalent of
`mcp__plugin_fuzzy-search_fuzzy-search__fuzzy_search_documents`. The MCP uses
`rga --json --no-heading QUERY PATH` and parses the JSON events; the flattened
`--no-heading --line-number` form above is simpler interactively. See
[pipelines.md](pipelines.md#replicate-the-mcp) for the JSON parsing detail.

## rga adapters & config

```bash
rga --rga-list-adapters                 # show every adapter and what it runs
rga --rga-adapters=+poppler …           # enable ONLY poppler (PDF)
rga --rga-adapters=+pandoc …            # docx / epub / odt via pandoc
rga --rga-adapters=-pandoc …            # disable an adapter
RGA_CACHE_MAX_BLOB_LEN=0 rga …          # disable extraction caching (debug)
```

The MCP's `file_types` argument maps to these adapters: `pdf→poppler`,
`docx`/`doc`/`epub→pandoc`, `zip→zip`, `tar→tar`, `sqlite`/`db→sqlite`.

## PDF page count & info

CLI analog of `get_pdf_page_count`:

```bash
pdfinfo file.pdf | rg '^Pages:'         # poppler
# or with PyMuPDF:
python3 -c 'import fitz,sys; print(fitz.open(sys.argv[1]).page_count)' file.pdf
```

`pdfinfo` also reports title, author, page size, and PDF version.

## PDF outline / bookmarks

CLI analog of `get_pdf_outline` (and its optional `fuzzy_filter`):

```bash
# Dump the table of contents (level, title, page)
python3 - file.pdf <<'PY'
import fitz, sys
for level, title, page in fitz.open(sys.argv[1]).get_toc():
    print(f"{'  '*(level-1)}{title}\t(p.{page})")
PY

# Fuzzy-filter the outline titles (mirrors the MCP's fuzzy_filter arg)
python3 -c 'import fitz,sys; [print(f"{t}\t{p}") for _,t,p in fitz.open(sys.argv[1]).get_toc()]' file.pdf \
  | fzf --filter 'QUERY'
```

## Extract PDF pages

CLI analog of `extract_pdf_pages` (pages are **1-based** for `pdftotext`):

```bash
# Plain text of pages 3–5
pdftotext -f 3 -l 5 file.pdf out.txt          # omit out.txt or use - for stdout
pdftotext -f 3 -l 5 file.pdf -                 # to stdout

# Preserve physical layout (columns/tables)
pdftotext -layout -f 3 -l 5 file.pdf -

# Simple HTML with metadata (closest to the MCP's html/markdown formats)
pdftotext -htmlmeta -f 1 -l 1 file.pdf -
```

For markdown output like the MCP's default, pipe extracted text through `pandoc`
(`… | pandoc -f html -t markdown`) or extract with PyMuPDF below.

## PyMuPDF one-liners

PyMuPDF (`fitz`) is what the MCP uses; it gives richer per-page extraction
including markdown and 0-based indexing.

```bash
# Page text (0-based index 2 == third page)
python3 -c 'import fitz,sys; print(fitz.open(sys.argv[1])[2].get_text())' file.pdf

# Page labels (0-based index → printed label, e.g. roman front-matter)
python3 -c 'import fitz,sys; d=fitz.open(sys.argv[1]); print(d.get_page_labels())' file.pdf

# Markdown for a page range (needs pymupdf4llm: pip install pymupdf4llm)
python3 -c 'import pymupdf4llm,sys; print(pymupdf4llm.to_markdown(sys.argv[1], pages=[2,3,4]))' file.pdf
```

> The MCP exposes `zero_based`/`one_based` page-spec modes and page **labels**
> (which can differ from indices when a PDF numbers front-matter with roman
> numerals). `pdftotext` is 1-based by physical page; PyMuPDF indexes 0-based and
> can report the human label via `get_page_labels()`.
