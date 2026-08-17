# The Ruff Formatter

`ruff format` — a Black-compatible Python formatter. Verified against ruff 0.16.3.

## Table of contents

- [Basics](#basics)
- [Options](#options)
- [Formatter ↔ linter conflicts](#formatter--linter-conflicts)
- [Suppressing formatting](#suppressing-formatting)
- [Docstring code formatting](#docstring-code-formatting)
- [Markdown code formatting](#markdown-code-formatting)
- [Range formatting](#range-formatting)
- [Exit codes](#exit-codes)
- [Black compatibility](#black-compatibility)
- [Preview style](#preview-style)
- [Migrating from Black](#migrating-from-black)

## Basics

```bash
ruff format                  # format in place (default path: `.`)
ruff format --check          # exit 1 if anything would change; write nothing
ruff format --diff           # show the diff; write nothing
ruff format --check --output-format github .   # CI annotations (ruff 0.16+)
cat f.py | ruff format - --stdin-filename f.py # stdin
```

The formatter **does not sort imports** — that is the linter's `I` (isort) rules. The canonical
sequence is:

```bash
ruff check --select I --fix    # or just `ruff check --fix`, since I is in the 0.16 defaults
ruff format
```

A unified lint+format command is [planned upstream](https://github.com/astral-sh/ruff/issues/8232)
but does not exist yet.

## Options

The formatter is deliberately small. These are **all** of `[tool.ruff.format]`:

| Option | Values | Default | Notes |
|--------|--------|---------|-------|
| `quote-style` | `double` \| `single` \| `preserve` | `double` | `preserve` leaves quotes alone (for Black's `skip-string-normalization` users) |
| `indent-style` | `space` \| `tab` | `space` | |
| `line-ending` | `auto` \| `lf` \| `cr-lf` \| `native` | `auto` | |
| `skip-magic-trailing-comma` | bool | `false` | `true` = ignore a trailing comma as a "keep this exploded" signal |
| `docstring-code-format` | bool | `false` | format Python examples inside docstrings |
| `docstring-code-line-length` | `dynamic` \| int | `dynamic` | `dynamic` respects the surrounding indentation |
| `nested-string-quote-style` | `alternating` \| `preferred` | `alternating` | quotes for strings nested in f-string expressions; no effect below Python 3.12 |
| `preview` | bool | `false` | unstable formatter style |
| `exclude` | globs | — | formatter-only exclusions |

`line-length` and `indent-width` are **top-level** (shared with the linter), not under `format`:

```toml
[tool.ruff]
line-length = 100
indent-width = 4

[tool.ruff.format]
quote-style = "single"
docstring-code-format = true
```

CLI: `ruff format --line-length N` is the only format-specific value flag; everything else goes
through `--config "format.KEY = VALUE"`.

## Formatter ↔ linter conflicts

Some lint rules encode formatting opinions the formatter contradicts. Running the formatter should
never introduce new lint errors — provided these are off. **None are in ruff's default rule set**
(verified on 0.16.3), but selecting their category turns them on.

| Code | Rule |
|------|------|
| `W191` | tab-indentation |
| `E111` | indentation-with-invalid-multiple |
| `E114` | indentation-with-invalid-multiple-comment |
| `E117` | over-indented |
| `D203` | incorrect-blank-line-before-class |
| `D206` | docstring-tab-indentation |
| `D300` | triple-single-quotes |
| `Q000` | bad-quotes-inline-string |
| `Q001` | bad-quotes-multiline-string |
| `Q002` | bad-quotes-docstring |
| `Q003` | avoidable-escaped-quote |
| `Q004` | unnecessary-escaped-quote |
| `COM812` | missing-trailing-comma |
| `COM819` | prohibited-trailing-comma |
| `ISC002` | multi-line-implicit-string-concatenation — only when used *without* `ISC001` **and** `flake8-implicit-str-concat.allow-multiline = false` |

```toml
[tool.ruff.lint]
extend-select = ["Q", "COM", "D"]
ignore = ["Q000", "Q001", "Q002", "Q003", "Q004", "COM812", "COM819", "D203", "D206", "D300"]
```

**`E501` (line-too-long) is compatible but noisy.** The formatter only makes a *best effort* to wrap
at `line-length` — long string literals, URLs, and comments still overflow, so formatted code can
legitimately fail `E501`.

Also avoid these `lint.isort` settings at non-default values — they fight the formatter's treatment
of imports: `force-single-line`, `force-wrap-aliases`, `lines-after-imports`, `lines-between-types`,
`split-on-trailing-comma`.

**`ruff format` emits a warning whenever it detects an incompatible rule or setting.** A
warning-free `ruff format` run is the check that you are configured correctly.

## Suppressing formatting

```python
# fmt: off
matrix = [
    1, 0,
    0, 1,
]
# fmt: on

x = [1,  2]  # fmt: skip
```

- `# fmt: off` / `# fmt: on` work at **statement level**. Inside an expression they do nothing —
  the pair below still formats both entries:

  ```python
  [
      # fmt: off
      '1',
      # fmt: on
      '2',
  ]
  ```

  Apply the comment to the whole statement instead.
- `# fmt: skip` suppresses formatting for a single statement, case header, or decorator.
- YAPF's `# yapf: disable` / `# yapf: enable` are treated as `fmt: off` / `fmt: on`.
- These are **formatter** directives. Lint suppression uses `# noqa` / `# ruff: ignore[...]` — the
  two systems are unrelated.

## Docstring code formatting

`docstring-code-format = true` formats Python examples inside docstrings. Recognized formats:

- doctest blocks (`>>> `)
- CommonMark fenced code blocks with info string `python`, `py`, `python3`, `py3` — **and fences
  with no info string**, which are assumed to be Python
- reStructuredText literal blocks
- reStructuredText `code-block` / `sourcecode` directives with those language names

A block is silently skipped if it does not parse as Python, or if formatting it would produce
invalid Python. `docstring-code-line-length = "dynamic"` (the default) keeps the reformatted example
within the outer `line-length` *including* the docstring's indentation; set an integer to pin it.

## Markdown code formatting

**(ruff 0.16+, on by default.)** `ruff format` formats Python code blocks inside Markdown files.
Recognized info strings: `python`, `py`, `python3`, `py3`, `pyi`, `pycon`. `pyi` blocks are
formatted as stub files, `pycon` as REPL sessions, the rest as normal Python. Quarto-style
`{python}` fences are supported. Unparseable blocks are skipped.

This is a behavior change to be aware of when upgrading to 0.16 — `ruff format .` will now touch
`.md` files that it previously ignored. Opt out with a formatter-scoped exclusion:

```toml
[tool.ruff.format]
exclude = ["*.md"]
```

## Range formatting

For editor integrations — format only part of a file:

```bash
ruff format --range=1:1-10:1 file.py
ruff format --range=1-2 file.py     # columns optional
ruff format --range=2 file.py       # from line 2 to EOF
ruff format --range=-3 file.py      # first three lines
```

Line/column numbers are 1-based, the column counts unicode codepoints, and the end is exclusive.
Single file only; not supported for notebooks. Ruff may extend the range outward to enclose a full
logical line.

## Exit codes

`ruff format`:

- `0` — success, regardless of whether files changed
- `1` — files were formatted **and** `--exit-non-zero-on-format` was passed
- `2` — ruff failed (bad config or CLI options)

`ruff format --check`:

- `0` — nothing would change
- `1` — one or more files would change
- `2` — ruff failed

## Black compatibility

The formatter is a drop-in Black replacement, with documented **intentional** deviations:

- **Trailing end-of-line comments** are handled differently.
- **Pragma comments** (`# type:`, `# noqa`, `# pyright:`) are excluded when computing line width, so
  a line isn't split just because of a pragma.
- **Line width vs. line length** — ruff measures width (unicode-aware), not byte/char length.
- **Parenthesizing long nested expressions** differs.
- **Call expressions with a single multiline string argument** are laid out differently.
- **Blank lines at the start of a block** are handled differently.
- **F-strings** — ruff formats the *expression* parts inside `{...}` (stabilized in **ruff 0.9.0**);
  Black does not.
- **Implicit concatenated strings** and **`assert` statements** differ.

The full enumeration lives in the ruff repo at `docs/formatter/black.md` (published at
https://docs.astral.sh/ruff/formatter/black/). Unintentional deviations are bugs — report them.

Black option → ruff equivalent:

| Black | Ruff |
|-------|------|
| `line-length` | `line-length` (top level) |
| `skip-string-normalization` | `format.quote-style = "preserve"` |
| `skip-magic-trailing-comma` | `format.skip-magic-trailing-comma` |
| `target-version` | `target-version` (top level) |
| `preview` | `format.preview` |
| `--check` / `--diff` | `--check` / `--diff` |

## Preview style

`[tool.ruff.format] preview = true` (or `ruff format --preview`) enables unstable style, promoted to
stable in MINOR releases. Note that under ruff's versioning, **a stable style change is a MINOR
bump** — `ruff format` output can legitimately differ between 0.15 and 0.16 (0.15.0 shipped the
"2026 style guide"). Pin ruff in CI if byte-identical formatting matters.

One current preview example is **fluent layout for method chains**: preview breaks *before* the
first attribute preceding a call, stable (and Black) breaks *after* it.

```python
# preview                    # stable / Black
x = (                        x = (
    df                           df.filter(cond)
    .filter(cond)                .agg(func)
    .agg(func)                   .merge(other)
    .merge(other)            )
)
```

## Migrating from Black

1. Format the whole repo in **one isolated commit** with no other changes.
2. Record that commit in `.git-blame-ignore-revs` so `git blame` stays useful:
   ```bash
   git log -1 --format=%H >> .git-blame-ignore-revs
   git config blame.ignoreRevsFile .git-blame-ignore-revs
   ```
3. Remove `[tool.black]` and the Black pre-commit hook; add `ruff-format`.
4. Turn off the conflicting lint rules listed above, then run `ruff format` once more and confirm it
   prints **no warnings**.
5. Pin the ruff version (`required-version`, and a pre-commit `rev`) so a MINOR bump can't silently
   reformat the repo underneath you.
