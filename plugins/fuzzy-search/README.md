# fuzzy-search

An [MCP](https://modelcontextprotocol.io) server that exposes fuzzy
content/file/document search tools built on **ripgrep**, **fzf**, and
**ripgrep-all** (rga), plus a set of PDF inspection/extraction tools powered by
**PyMuPDF**.

It combines ripgrep's fast scanning with fzf's non-interactive fuzzy filtering,
so you can find code snippets, configuration, or any text pattern across a
codebase — and search inside PDFs and other documents.

## What it does

The server registers seven tools with the model:

| Tool | Description |
|------|-------------|
| `fuzzy_search_files` | Find file **paths** by fuzzy matching (fd/ripgrep file list → fzf). |
| `fuzzy_search_content` | Search file **contents**: ripgrep over all lines → fzf fuzzy filter. |
| `fuzzy_search_documents` | Search **PDFs and other document formats** with ripgrep-all (rga) → fzf. |
| `extract_pdf_pages` | Extract specific PDF pages and convert to various formats (PyMuPDF). |
| `get_pdf_outline` | Get a PDF's table of contents / bookmarks, with optional fuzzy filter. |
| `get_pdf_page_count` | Get the total number of pages in a PDF. |
| `get_pdf_page_labels` | Get a PDF's page labels (0-based index → label). |

> **`fuzzy_filter` is fzf fuzzy syntax, NOT regex.** The content/file/document
> tools fuzzy-match with fzf; they do not accept regular expressions. Use the
> `rg_flags` / pattern arguments for ripgrep-side filtering.

Once the plugin is enabled, the tools are available to Claude under the
plugin-namespaced ids, e.g.
`mcp__plugin_fuzzy-search_fuzzy-search__fuzzy_search_content`.

### Search query syntax (`fuzzy_filter`)

The `fuzzy_filter` argument is passed to `fzf --filter` and uses fzf's
extended-search syntax. Space-separated terms are ANDed; a bare term is a
fuzzy (subsequence) match:

| Token | Match type | Description |
|-------|------------|-------------|
| `sbtrkt` | fuzzy-match | Items that match `sbtrkt` |
| `'wild` | exact-match (quoted) | Items that include `wild` |
| `'wild'` | exact-boundary-match (quoted both ends) | Items that include `wild` at word boundaries (fzf 0.55+) |
| `^music` | prefix-exact-match | Items that start with `music` |
| `.mp3$` | suffix-exact-match | Items that end with `.mp3` |
| `!fire` | inverse-exact-match | Items that do not include `fire` |
| `!^music` | inverse-prefix-exact-match | Items that do not start with `music` |
| `!.mp3$` | inverse-suffix-exact-match | Items that do not end with `.mp3` |
| `def\ get` | escaped-space | A literal space inside one term: matches the contiguous phrase `def get` |

A single `|` term acts as an OR for the adjacent terms: `^core go$ | rb$ | py$`
matches items that start with `core` and end with `go`, `rb`, or `py`. Queries
are smart-case (all-lowercase → case-insensitive; any uppercase letter →
case-sensitive). `.`, `*`, `(`, `[` are literal characters, not regex
metacharacters.

Because a space separates terms (AND), a multi-word phrase must **backslash-escape
its spaces**: `'def\ parse_config` matches the contiguous string
`def parse_config`, while `'def 'parse_config` matches those two substrings
independently. The backslash is a literal character in the `fuzzy_filter` string
(no shell is involved — the value is passed straight to `fzf --filter`). A common
code-navigation idiom combines this with exclusions, e.g.
`'UserSession !tests/` (exact symbol, skip test paths).

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — the server is launched with
  `uv run --script`. The script is a PEP 723 inline-dependency script
  (`requires-python >=3.10`, deps `mcp>=0.1.0`, `PyMuPDF>=1.23.0`); uv resolves
  and caches dependencies automatically on first run.
- **[ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`)** and
  **[fzf](https://github.com/junegunn/fzf)** — required for the
  fuzzy file/content search tools. Tools that need a missing binary report a
  clear error instead of crashing.
- **[ripgrep-all](https://github.com/phiresky/ripgrep-all) (`rga`)** —
  required only for `fuzzy_search_documents` (PDFs, Office docs, archives).
- **PyMuPDF** — bundled via the script's PEP 723 header; powers the PDF tools.

## How it is wired

The plugin declares the server in `.mcp.json`:

```json
{
  "mcpServers": {
    "fuzzy-search": {
      "command": "uv",
      "args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_fuzzy_search.py"]
    }
  }
}
```

`${CLAUDE_PLUGIN_ROOT}` is expanded by Claude Code to the installed plugin
directory, so the server runs regardless of where the plugin is checked out.

## Bounded memory

The search tools cap how much candidate data they buffer so a search over a
large tree (or a few huge files) cannot exhaust RAM. The `limit` argument only
trims the number of *returned* rows — it does **not** bound peak memory, because
`fzf --filter` sorts its input and therefore reads all of it before emitting
results. The caps below are what actually bound memory; they are applied
*before* fzf.

| Environment variable | Default | What it caps |
|----------------------|---------|--------------|
| `MCP_FUZZY_MAX_LINES` | `100000` | Max candidate **lines** fed to fzf in the standard `fuzzy_search_content` and `fuzzy_search_documents` paths. |
| `MCP_FUZZY_MAX_BYTES` | `52428800` (50 MiB) | Max **total bytes** of candidate text (standard paths) or concatenated file contents (multiline paths) buffered before fzf. |
| `MCP_FUZZY_MAX_FILE_BYTES` | `1048576` (1 MiB) | Max bytes read from any **single file** in multiline modes. |
| `MCP_FUZZY_MAX_PDF_PAGES` | `500` | Max number of **pages** `extract_pdf_pages` will extract in a single call (bounds the per-page text/HTML it buffers). |

Set any of these to `0` (or a negative value) to disable that individual cap and
restore the historical unbounded behavior.

`MCP_FUZZY_MAX_PDF_PAGES` guards `extract_pdf_pages` specifically: a pathological
range like `pages="1-100000"` would otherwise expand to tens of thousands of page
indices and buffer every page's extracted text/HTML at once. The cap is applied
after deduplicating the requested indices and before extraction, so duplicate
pages collapse first and never consume the budget. The default of `500` is well
above any realistic "extract a chapter/section" request, so normal extractions are
unaffected; when the cap trips the result is trimmed to the first `500` pages and
gains the same additive `truncated` / `truncation_note` keys (described below).

### Choosing the caps

`MCP_FUZZY_MAX_BYTES` is the primary memory backstop. The two standard-path caps
are evaluated together and whichever is reached first wins; on a large or
long-line corpus the byte cap trips before the line cap (at the default
`100000` lines a corpus would need to average under ~520 bytes/line to hit the
line cap before the 50 MiB byte cap), so the byte cap is what actually bounds
peak in the worst case. The line cap mainly keeps the candidate *count* — and
therefore fzf's ranking work — sane.

Worst-case peak at the defaults is **roughly 150–200 MB** (measured), not
gigabytes. Two ways to reach it, both bounded:

- *Many short lines* — the line cap is a **count** cap, and each retained
  candidate costs ~1.5 KB of Python working set (the `file:line:content` string,
  its result-mapping entry, the joined fzf-input copy, and the JSON-derived
  intermediate). Measured: 5000 lines→7.4 MB, 20000→29.6 MB, 50000→75 MB
  (~1.5 KB/line, linear), so the default `100000` lines extrapolates to ~150 MB.
- *Few long lines* — once the average line is ≳500 bytes the byte cap trips
  first, holding the candidate text to ≤ 50 MiB, which lands peak in the same
  ~150–200 MB range after fzf's own sort buffer.

(The pre-fix code had **no** cap, so a ~20 MB corpus drove ~3 GB of Python-side
peak; see the changelog for the full before/after measurements.) ~150–200 MB is
acceptable for a developer tool, which is why the defaults are generous — they
also govern *when* truncation fires, so lowering them would start truncating
real searches that previously succeeded. Tune via the env vars for
memory-constrained deployments.

Tuning guidance:

- **Tighter memory:** lower `MCP_FUZZY_MAX_BYTES` (e.g. `26214400` for 25 MiB).
  This is the knob that moves the peak; lowering `MCP_FUZZY_MAX_LINES` alone has
  little effect on memory because each line is small.
- **More complete results:** raise `MCP_FUZZY_MAX_BYTES` / `MCP_FUZZY_MAX_LINES`,
  or set them to `0` to disable the caps entirely (accepting unbounded memory).
- **Large individual files in multiline mode:** raise `MCP_FUZZY_MAX_FILE_BYTES`
  if you need to search files bigger than 1 MiB in full.

Because truncation is surfaced (below), you can also just run the search and let
the `truncated` flag tell you whether a higher cap is warranted for that query.

**Known exception — `fuzzy_search_files` (non-multiline) is intentionally not
capped.** That path streams `rg --files | fzf` through a direct OS pipe with no
Python buffer in between, and it buffers only matched *paths* (tens to low
hundreds of bytes each), not file contents — so its memory is O(matched paths)
and bounded by the working tree / `.gitignore`, not by file sizes. Reaching a
concerning size would take a literal million-file repo (~200 MB of path text),
the same output `rg --files`/`fd` produce anyway. Adding a cap here would mean
inserting a Python read between `rg` and `fzf` (losing the direct pipe), which
isn't worth it for that case; the cap can be added later if million-file repos
become a target.

When a cap trips, the result is **not** silently shortened: the returned object
gains two additive keys alongside the unchanged `matches` array, and a warning is
logged:

```json
{
  "matches": [ ... ],
  "truncated": true,
  "truncation_note": "Candidate set capped at MCP_FUZZY_MAX_LINES=100000 lines / MCP_FUZZY_MAX_BYTES=52428800 bytes; ripgrep produced more matches. Results are ranked over the first 100000 candidates only — narrow the search or raise the caps."
}
```

The `truncated` / `truncation_note` keys are present **only** when truncation
occurred, so existing consumers that read `result["matches"]` are unaffected.

## Development / tests

The bundled test suite lives in `tests/` and exercises both the in-process MCP
interface and the CLI (including the PDF tools, which require PyMuPDF). Run it
with uv:

```bash
cd plugins/fuzzy-search
uv run --isolated --extra dev pytest tests/ -v
```

`tests/conftest.py` contains a small autouse fixture that runs each test with
its working directory set to `scripts/`, so the CLI subprocess tests — copied
verbatim from upstream, where the script sits at the repo root and is launched
as the bare filename `mcp_fuzzy_search.py` — resolve correctly from this
plugin's `scripts/` layout. The server script and the test module were
originally copied from the upstream `mcp-personal` repository and then patched
locally (see below).

## Local modifications (diverges from mcp-personal upstream)

`scripts/mcp_fuzzy_search.py` is no longer byte-verbatim from upstream. The
following audit fixes were applied locally and are candidates for upstreaming:

1. **`fuzzy_search_content` standard mode now parses `rg --json`** instead of
   splitting ripgrep's `file:line:content` text on `:`. The structured stream is
   parsed (path / line number / line text from both `match` **and** `context`
   records) into the same `file:line:content` lines fed to fzf — the existing
   `--delimiter ":"` / `--nth` field-scoping and the `{file, line, content}`
   result shape are unchanged. This fixes three defects at once:
   - advertised `-A`/`-B`/`-C` context records are now included (previously they
     were dropped/mangled by the text parser);
   - file paths containing `:` are no longer corrupted (no more colon-splitting
     or Windows-drive-letter heuristic);
   - non-UTF-8 / non-ASCII bytes survive (ripgrep's base64 `bytes` fallback is
     decoded with replacement).
2. **`rg_flags` is split with `shlex.split()`** rather than `str.split()`, so
   quoted flag values (e.g. `--glob '!node_modules'`) are tokenized correctly.
3. **Subprocess timeouts** on every `rg` / `rga` / `fzf` call (default 30s,
   configurable via the `MCP_FUZZY_SEARCH_TIMEOUT` env var); a timeout returns a
   structured `{"error": ...}` instead of hanging the server.
4. **Multiline mode** skips binary files (NUL-byte detection) and accumulates
   file contents in a list joined once with `b"".join(...)` instead of repeated
   `bytes +=` concatenation (avoids quadratic-time rebuilds).
5. **PyMuPDF documents are closed via `try`/`finally`** in every PDF tool
   (`extract_pdf_pages`, `get_pdf_page_labels`, `get_pdf_page_count`,
   `get_pdf_outline`) and in the document-search page-label cache, so error and
   early-return paths no longer leak document handles.
6. **Candidate-set caps** (`MCP_FUZZY_MAX_LINES` / `MCP_FUZZY_MAX_BYTES`) bound
   the data fed to fzf on the `fuzzy_search_content` standard path and the
   `fuzzy_search_documents` path, surfaced via additive `truncated` /
   `truncation_note` result keys (no silent caps). The standard content path now
   reads `rg --json` **incrementally** from the subprocess pipe instead of
   buffering the whole output, and stops as soon as a cap is hit. The
   `file:line:content` → `{file, line, content}` reconstruction mapping is kept
   (so the `rg --json` correctness fixes above are not regressed) but is now
   bounded by the line cap rather than the corpus.
7. **`fuzzy_search_files` multiline parity:** the file-list `subprocess.check_output`
   gained the same timeout as the rest of the file (it was the only subprocess
   call without one), the `bytes += record` accumulation became `b"".join(...)`
   (drops a quadratic-time rebuild), and it now skips binary files, applies a fzf
   timeout, and captures fzf stderr — matching the already-hardened multiline
   content path.
8. **Per-file (`MCP_FUZZY_MAX_FILE_BYTES`) and total (`MCP_FUZZY_MAX_BYTES`)
   read caps** on both multiline paths, so a single huge file (or many files)
   can no longer be read into memory unboundedly.
9. **Helpers** `_int_env` (shared integer-env reader, also adopted by
   `SUBPROCESS_TIMEOUT`), `_read_file_capped` (per-file capped read + binary
   skip), and `_with_truncation` (attaches the truncation keys + logs a warning).
10. **`extract_pdf_pages` page cap + label hoist.** A new
    `MCP_FUZZY_MAX_PDF_PAGES` cap (default `500`, `0` disables) bounds the number
    of pages extracted in a single call, applied after deduplication and before
    extraction, surfaced via the shared `_with_truncation` (additive `truncated`
    / `truncation_note`, original requested count named in the note). Separately,
    `doc.get_page_labels()` — which rebuilds the whole-document label list on each
    call — was hoisted out of the per-page range-mapping and extraction loops into
    a single cached call right after `fitz.open`, turning the previous
    O(pages × labels) label lookup into one O(1) fetch (extracted content and
    labels are byte-identical to before).

Constraints honored: the PEP 723 header and dependency set are unchanged (no new
deps), the new config is env-var-only to mirror `MCP_FUZZY_SEARCH_TIMEOUT`, tool
signatures and the `{"matches": [...]}` shape are unchanged, and the rest of the
verbatim-ported file is not reformatted. Items 6–10 are candidates for
upstreaming.

The test module (`tests/test_fuzzy_search.py`) was correspondingly updated: the
subprocess mocks for `fuzzy_search_content` now feed `rg --json` records, and an
over-specific fzf-ranking-dependent assertion in `test_fuzzy_search_content` was
loosened (its previous `xfail` in `tests/conftest.py` was removed — it now
passes for real). The standard-content mocks additionally expose the rg process
`stdout` as an iterable, matching the incremental-read change in item 6.
