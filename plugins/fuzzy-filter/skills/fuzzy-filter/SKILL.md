---
name: fuzzy-filter
description: The non-interactive `rg`/`fd`/`rga` → `fzf --filter` pipeline — scan with a regex tool, then fuzzy-rank the lines without opening a TUI. Use when you want fuzzy (not regex) matching of file paths, code lines, or document/PDF text from a script or one-shot command, when reproducing the fuzzy-search MCP's behavior on the bare command line, or when piping fuzzy-ranked results into xargs/an editor. This is the CLI technique; for the INTERACTIVE picker use the fzf skill, and for tool-call ergonomics use the fuzzy-search MCP server.
---

# fuzzy-filter — Non-Interactive Fuzzy Search Pipelines

## Overview

`fzf` is famous as an **interactive** picker, but it also has a batch mode:
`fzf --filter QUERY` reads lines on STDIN, fuzzy-ranks them against `QUERY`,
prints the matches to STDOUT, and exits — **no terminal UI, no keyboard, fully
scriptable**. Pair it with a fast scanner and you get a two-stage pipeline:

```
                regex / literal scan            fuzzy rank
  files/dirs ──────────────────────▶ lines ──────────────────▶ ranked matches
                rg · fd · rga                  fzf --filter QUERY
```

1. **Stage 1 — scan (regex):** `rg`, `fd`, or `rga` walks the tree and emits
   candidate lines (file paths, `file:line:content` rows, or document text).
   This stage is gitignore-aware and uses **regular expressions**.
2. **Stage 2 — rank (fuzzy):** `fzf --filter` keeps only the lines that fuzzy-match
   `QUERY` and orders them best-first. This stage uses **fzf's fuzzy syntax — NOT
   regex** (see [Fuzzy filter syntax](#fuzzy-filter-syntax)).

The two query languages are different on purpose. Use a broad/empty Stage-1
pattern (`.` matches every line) to hand fzf the full candidate set, then let the
fuzzy query do the selective work — or pre-narrow with a real regex in Stage 1
when you know it, and fuzzy-rank the remainder.

> This is exactly how the **fuzzy-search MCP server** works internally; this
> skill documents the underlying commands so you can run them directly. See
> [references/pipelines.md](references/pipelines.md) for the exact
> MCP-equivalent command behind each tool.

## When to Use This Skill (and When Not To)

Use this **non-interactive** technique when you want fuzzy results from a script,
a single command, or to pipe ranked output onward — no TUI involved.

| You want to… | Use | Why |
|---|---|---|
| Fuzzy-rank lines in a script / one-shot, pipe to xargs or an editor | **this skill** (`… \| fzf --filter`) | Batch mode, deterministic STDOUT, no TTY needed |
| Interactively pick from a live, keystroke-updated list | **fzf skill** | `fzf` (no `--filter`), previews, `--bind`, live-grep |
| Get fuzzy results as a structured tool call (paths/line numbers/JSON) | **fuzzy-search MCP** (`mcp__plugin_fuzzy-search_fuzzy-search__*`) | Wraps these same pipelines with typed args + parsed output |
| Plain **regex** content search (no fuzzy ranking) | **ripgrep skill** | `rg` alone already does this; don't add fzf |
| Find files by **name/glob/metadata** (no fuzzy ranking) | **fd skill** | `fd` alone already does this |

Key distinctions:
- **vs. the fzf skill:** that skill covers *interactive* selection (previews,
  keybindings, `CTRL-T`/`CTRL-R`, live-grep frontends). Here `fzf` never draws a
  UI — `--filter` makes it a Unix filter.
- **vs. the fuzzy-search MCP:** the MCP exposes these pipelines as model tools
  with typed arguments and parsed results. Reach for it when you want tool-call
  ergonomics; reach for this skill when you're already in a shell.
- **vs. rg/fd alone:** if a **regex** answers the question, you don't need fzf.
  Add `fzf --filter` only when you specifically want **fuzzy** (typo-tolerant,
  subsequence) ranking.

## Prerequisites

```bash
rg --version      # ripgrep — Stage-1 scanner for files & content
fzf --version     # fzf     — Stage-2 fuzzy ranker (needs batch --filter)
```

Required for everything: **`rg`** and **`fzf`**. Optional, per use case:

- **`fd`** — ergonomic file-list source for fuzzy *file* search (alternative to `rg --files`).
- **`rga`** ([ripgrep-all](https://github.com/phiresky/ripgrep-all)) — for **document/PDF** content (PDFs, Office docs, ebooks, archives, sqlite). `(rga 0.10+)`
- **`pdftotext`** (poppler) or **PyMuPDF** — to extract/inspect PDF pages once you've located a hit. See [references/pdf.md](references/pdf.md).

If a required binary is missing, **stop and tell the user** — do not auto-install.
See the **ripgrep**, **fd**, and **fzf** skills for installation instructions.

## Fuzzy Filter Syntax

Stage 2 uses fzf's **extended-search syntax**, the same language as the
interactive prompt. A bare term is a **fuzzy** (subsequence) match; prefix/anchor
sigils make terms exact. Space-separated terms are **AND**ed.

| Token | Match | Example |
|---|---|---|
| `sbtrkt` | Fuzzy (subsequence) | matches `SubstringTracking` |
| `'wild` | Exact substring | contains `wild` literally |
| `'wild'` | Exact at word boundaries `(fzf 0.55+)` | `wild` as a whole word |
| `def\ get` | Literal space (one term) | the contiguous phrase `def get`, not two ANDed terms |
| `^core` | Prefix | starts with `core` |
| `.py$` | Suffix | ends with `.py` |
| `!fire` | Inverse | does **not** contain `fire` |
| `!^core` | Inverse prefix | does **not** start with `core` |
| `!.py$` | Inverse suffix | does **not** end with `.py` |
| `a$ \| b$ \| c$` | OR | ends with `a`, `b`, or `c` |

So `def test_ seer credit` means: fuzzy-`def test_` **AND** fuzzy-`seer` **AND**
fuzzy-`credit`, in any order. This is **not** a regex — `.`, `*`, `(`, `[` are
literal characters here, not metacharacters. (Same language as the **fzf
skill's "Search Syntax"** section — batch and interactive use the same matcher.)

**Space is the AND separator — backslash-escape it to match a literal space.**
Because a bare space splits terms, a multi-word phrase like a function signature
must escape its spaces: `'def\ parse_config` matches the *contiguous* string
`def parse_config`, whereas `'def 'parse_config` (two exact terms) matches
those two substrings independently anywhere on the line. Use `\ ` when adjacency
matters. The escape survives the shell inside double quotes
(`fzf --filter "'def\ parse_config"`), and through the fuzzy-search MCP it is
just a literal backslash in the `fuzzy_filter` string.

### Code-navigation idioms

These compose the operators above into the patterns you actually reach for when
moving around a codebase (a bare-fuzzy query is rarely precise enough on its own):

| Goal | Query | Reading |
|---|---|---|
| Jump to a definition | `'def\ parse_config` | exact, contiguous `def parse_config` |
| A symbol, but not its tests | `'UserSession !tests/` | exact `UserSession`, exclude any `tests/` path |
| Narrow by symbol + area + skip tests | `'HttpClient 'handlers/ !tests/` | three ANDed constraints |
| A class definition | `'class\ User` | contiguous `class User` (or `^class\ User` to anchor) |

The recurring shape is **exact term(s) (`'…`, with `\ ` for phrases) + `!path`
exclusions** — anchor on what you know literally, then subtract the noise.

> **Smart-case applies to the fuzzy query too:** an all-lowercase query is
> case-insensitive; any uppercase letter makes it case-sensitive — the same rule
> rg/fd use. `--exact` also works in batch mode (`fzf --exact --filter Q`): bare
> terms become exact substring matches, and the `'`-prefix flips to mean
> "unquote" (fuzzy).

## Fuzzy FILE Search

Feed fzf a list of paths and fuzzy-rank them by path.

```bash
# Source the file list with ripgrep (gitignore-aware), fuzzy-rank by path
rg --files | fzf --filter 'src model user'

# fd as the source instead (also gitignore-aware; matches names by default)
fd --type f | fzf --filter 'test util'

# Include hidden files in the candidate set
rg --files --hidden | fzf --filter 'config yaml'
```

**Bias ranking toward path structure** with fzf's path scheme — it weights
matches near path separators, which is what you usually want for filenames:

```bash
rg --files | fzf --scheme=path --filter 'cmd main'   # (fzf 0.36+)
```

### NUL-safety (paths with spaces/newlines)

A newline-delimited pipe breaks on filenames containing newlines. Make the whole
pipe NUL-delimited end-to-end:

```bash
rg --files --null | fzf --read0 --print0 --filter 'src model' \
  | xargs -0 -n1 echo            # hand off safely to the next tool

fd --print0 --type f | fzf --read0 --print0 --filter 'big report' \
  | xargs -0 "$EDITOR"
```

`--read0` makes fzf read NUL-separated input; `--print0` makes it emit
NUL-separated output. Always pair with `xargs -0`.

## Fuzzy CONTENT Search

Scan every line, then fuzzy-rank the `file:line:content` rows. This is the
workhorse pipeline.

```bash
rg --line-number --no-heading --color=never . PATH \
  | fzf --filter 'QUERY' --delimiter : --nth=1,3..
```

Stage 1 anatomy:
- `.` — match **every** line (hand the full set to fzf). Swap in a real regex to pre-narrow.
- `--line-number` — prefix each row with its line number (field 2).
- `--no-heading` — one self-contained `file:line:content` row per match (no grouped headers).
- `--color=never` — **mandatory**: ANSI color codes would corrupt fzf's matching and field splitting.

Stage 2 anatomy — the row is `FILE : LINE# : CONTENT`, so with `--delimiter :`:
- field **1** = file path, field **2** = line number, field **3..** = the line content (which may itself contain colons — `3..` captures all of it).
- `--nth=1,3..` — fuzzy-match against **path + content**, deliberately **skipping field 2 (the line number)** so digits in your query don't spuriously match line numbers.

### Content-only (ignore the path)

To match **only** the code/text and never the file path:

```bash
rg --line-number --no-heading --color=never . PATH \
  | fzf --filter 'QUERY' --delimiter : --nth=3..
```

`--nth=3..` restricts fuzzy matching to field 3 onward (content), ignoring both
the path (field 1) and the line number (field 2). Use this when a path component
keeps polluting your results.

> The full output row (including `file:line:`) is still **printed** — `--nth`
> only controls what fzf *matches on*, not what it emits. That's what lets you
> pipe the result into an editor at the right line. To emit only chosen fields,
> use `--accept-nth` `(fzf 0.60+)` — e.g. `--accept-nth='{1}:{2}'` prints
> `file:line` ready for `code --goto`.

## Field Scoping Deep-Dive

`--nth` is the lever that makes content search precise. It selects which
delimiter-separated fields fzf *searches*; `--with-nth` selects which fields it
*displays*.

| Flag | Controls | Typical value |
|---|---|---|
| `--delimiter :` | How a line splits into fields | `:` for `rg` rows; `\t` for `rga --json` once flattened |
| `--nth=1,3..` | Fields fzf **matches** on | path + content (skip line#) |
| `--nth=3..` | — | content only |
| `--accept-nth=3..` | Fields fzf **prints** `(fzf 0.60+)` | content only; `'{1}:{2}'` → `file:line` |
| `--with-nth=3..` | Fields fzf **displays** (interactive UI only — no effect on `--filter` output) | hide `file:line:` on screen |

Field ranges: `N` (one field), `N..` (N to end), `..N`, `N..M`, and comma-joined
lists like `1,3..`. Negative indices count from the end (`-1` = last field).
Default delimiter is AWK-style runs of whitespace; set `--delimiter` explicitly
whenever fields are colon- or tab-separated.

> **Why skip field 2?** ripgrep puts the line number there. If you matched on it,
> a query like `120` would rank every line *near line 120* across all files.
> `1,3..` / `3..` exclude it so numbers in your query match real content.

## Document & PDF Fuzzy Search

`rga` (ripgrep-all) extends rg to PDFs, Office docs, ebooks, archives, and sqlite
by transparently extracting their text. Scan with `rga`, then fuzzy-rank the
same way. `(rga 0.10+)`

```bash
# Plain rows — flatten to file:line:content, then fuzzy-rank the content
rga --no-heading --line-number --color=never . PATH \
  | fzf --filter 'QUERY' --delimiter : --nth=3..

# Restrict to PDFs only (rga adapter), still fuzzy-ranked
rga --no-heading --line-number --color=never --rga-adapters=+poppler . PATH \
  | fzf --filter 'QUERY' --delimiter : --nth=3..
```

The fuzzy-search MCP's `fuzzy_search_documents` uses `rga --json` and parses the
JSON events; on the CLI the flattened `--no-heading --line-number` form above is
the simpler equivalent. For the JSON variant, adapter list, and PDF
extraction/outline commands (the CLI analog of the MCP's PDF tools), see
[references/pdf.md](references/pdf.md).

## Gotchas

- **Fuzzy ≠ regex.** The Stage-2 query is fzf syntax. `.`/`*`/`[` are literals;
  there are no capture groups or quantifiers. Put real regexes in Stage 1 (rg/fd/rga).
- **`--color=never` before filtering.** Without it, ANSI escapes ride along inside
  field 3 and wreck both matching and any downstream parsing. (Interactive fzf uses
  `--ansi` to *render* color; in batch mode you strip it instead.)
- **Skip the line-number field.** Use `--nth=1,3..` or `--nth=3..` with
  `--delimiter :`; matching on field 2 lets stray digits match line numbers.
- **NUL-safety.** For paths that may contain spaces/newlines, go end-to-end NUL:
  `rg --files --null`/`fd --print0` → `fzf --read0 --print0` → `xargs -0`.
- **Empty query returns everything.** `fzf --filter ''` passes all input through
  (ranked as-is). Guard against an empty query in scripts if you don't want the
  whole tree.
- **Exit code 1 = no matches, not an error.** `fzf --filter` exits non-zero when
  nothing matches; handle it explicitly in `set -e` scripts.
- **fzf still reads everything.** `--filter` consumes all of STDIN before printing.
  For huge inputs, pre-narrow in Stage 1 (a real rg regex, `-t`/`-g` filters) so
  fzf ranks a smaller set.

## See Also

- **fzf skill** — the **interactive** counterpart: live pickers, previews,
  `--bind`, `CTRL-T`/`CTRL-R`, and the full Search Syntax reference.
- **ripgrep skill** — Stage-1 content scanning: regex, `-t`/`-g` filters,
  `--json`, gitignore behavior.
- **fd skill** — Stage-1 file-list source: name/glob/metadata filtering, `--print0`.
- **fuzzy-search MCP** (`mcp__plugin_fuzzy-search_fuzzy-search__*`) — these same
  pipelines as typed model tools (content/file/document search + PDF tools).

## References

- [references/pipelines.md](references/pipelines.md) — full recipe catalog
  (files/content/docs, NUL-safe, limiting, sorting, xargs/clipboard/editor
  hand-off — best hit → pbcopy or `code`/`cursor --goto file:line`) **plus the
  exact MCP-equivalent command for every fuzzy-search tool**.
- [references/pdf.md](references/pdf.md) — rga configuration and PDF page
  extraction/outline via `pdftotext`/PyMuPDF (CLI analog of the MCP's PDF tools).
