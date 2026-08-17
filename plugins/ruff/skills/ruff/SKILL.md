---
name: ruff
description: "ruff — Astral's single, extremely fast (Rust) binary that is BOTH a Python linter (`ruff check`, ~970 rules replacing Flake8, isort, pyupgrade, bandit, pydocstyle, parts of Pylint) and a Black-compatible formatter (`ruff format`). Use when linting or formatting Python, configuring `[tool.ruff]` in `pyproject.toml` or a `ruff.toml`/`.ruff.toml`, choosing rules with `select`/`extend-select`/`ignore`, looking up a rule code like F401/E501/B008/UP006, applying autofixes (`--fix`, `--unsafe-fixes`, `--diff`), suppressing violations (`# noqa`, `# ruff: ignore[...]`, `--add-noqa`), enabling preview rules, adopting ruff in an existing codebase, or wiring it into pre-commit/CI. Triggers on mentions of ruff, `ruff check`, `ruff format`, `ruff.toml`, `[tool.ruff.lint]`, \"ruff rule\", `# noqa`, or migrating off flake8/black/isort. This is the **ruff linter/formatter by Astral** — NOT uv (packaging) or ty (type checker), separate Astral tools with their own skills, and NOT flake8/black/isort themselves."
---

# ruff - Python Linter & Formatter

## Overview

Ruff is **one binary that is two tools**, and keeping them apart is the whole mental model:

| | Command | Replaces | Config section |
|---|---------|----------|----------------|
| **Linter** | `ruff check` | Flake8 (+plugins), isort, pyupgrade, bandit, pydocstyle, parts of Pylint | `[tool.ruff.lint]` |
| **Formatter** | `ruff format` | Black | `[tool.ruff.format]` |

They share config discovery, file discovery, `line-length`, `indent-width`, and `target-version` —
nothing else. `ruff format` does **not** sort imports (that's the linter's `I` rules); `ruff check`
does **not** reformat. Run them in that order: `ruff check --fix && ruff format`.

### The four things that surprise people

1. **`select` REPLACES the default rule set — it does not add to it.** The #1 silent footgun
   (see below); `extend-select` is the additive one.
2. **Fix safety is first-class** (safe / unsafe / display-only), with no analog in flake8 —
   `--fix` applies *safe* fixes only.
3. **Preview gates rules independently of version** — a rule that ships in your build stays
   invisible unless it is stable *or* you turn on `preview`.
4. **Config does not cascade — it is "nearest file wins"**, with an explicit `extend` for reuse.

> **Disambiguation:** this skill is the **ruff linter/formatter**. **uv** (packaging/project
> manager) and **ty** (type checker) are *separate* Astral tools with their own skills. Ruff is a
> linter and formatter — it is not a type checker.

## Prerequisites

```bash
ruff --version        # e.g. "ruff 0.16.3"
uvx ruff@latest ...   # run without installing (recommended for one-offs)
uv tool install ruff  # or persist it on PATH
```

**Version policy.** Ruff uses a **custom versioning scheme**: **MINOR = breaking changes, PATCH =
bug fixes** — no stable API until 1.0. A `0.15 → 0.16` bump can change the stable formatter style,
the default rule set, or remove rules, so pin ruff (`required-version = "==0.16.3"`, or a
pre-commit `rev`) wherever reproducible output matters. This skill documents **0.16.3**;
version-specific behavior is tagged `(ruff 0.X+)` and mapped in
[references/version-features.md](references/version-features.md).

**Preview gating is a separate axis from version.** Of 969 rules in 0.16.3, **139 are preview-only**.
A preview rule is *not* enabled by `select = ["ALL"]`, by its category, or even by its exact code —
only by also setting `preview = true`. Anything marked **(preview)** below needs that flag. The
linter and formatter have **independent** switches — `[tool.ruff.lint] preview` turns on unstable
*rules*, `[tool.ruff.format] preview` turns on unstable *style*; `--preview` on the CLI does the
same per command.

## Everyday commands

| Task | Command |
|------|---------|
| Lint | `ruff check [PATH]` (default `.`) |
| Lint + autofix (safe) | `ruff check --fix` |
| Include unsafe fixes | `ruff check --diff --unsafe-fixes` to preview, then `--fix --unsafe-fixes` |
| Preview fixes, write nothing | `ruff check --diff` (implies `--fix-only`) |
| What fires in this repo? | `ruff check --statistics` |
| Format | `ruff format [PATH]` |
| CI format gate | `ruff format --check` (exit 1 if any file would change) |
| Explain a rule / a config key | `ruff rule F401` / `ruff config lint.select` |
| Prefix → upstream tool | `ruff linter` |
| Resolved settings for a file | `ruff check --show-settings path.py` |
| Which files would run | `ruff check --show-files` |
| Watch mode / import graph | `ruff check --watch` / `ruff analyze graph` *(experimental)* |
| Language server / clear caches | `ruff server` / `ruff clean` |

**Exit codes** — `check`: `0` clean (or all fixed), `1` violations, `2` ruff itself failed (bad
config/flags). `--exit-zero` forces 0; `--exit-non-zero-on-fix` returns 1 even when all was fixed.
`format --check` / `check --diff`: `1` when changes are needed. **Never conflate exit 1 with exit
2** in CI — `2` means your config is broken, not your code.

## Rule selection (the big footgun)

The default rule set in **ruff 0.16+ is 413 rules** (it was 59 — `["E4","E7","E9","F"]` — before
0.16.0; older tutorials, older configs, and most people's memory still carry that number). The
expansion was **not a superset**: the same change *dropped* 18 opinionated `E`/`F` rules from the
defaults — `E401`, `E402`, `E701`–`E703`, `E711`–`E714`, `E721`, `E731`, `E741`–`E743`, `F403`,
`F405`, `F406`, `F722` — so a few checks you had on 0.15 are now **off** unless you re-select them.
Writing `select` throws the whole set away:

```bash
$ ruff check --isolated --statistics demo.py    # real 0.16.3 output
2  F401   [*] unused-import
1  F841   [ ] unused-variable
1  I001   [*] unsorted-imports
1  UP006  [*] non-pep585-annotation
1  UP035  [ ] deprecated-import

$ ruff check --isolated --select E --statistics demo.py
                  # ← nothing. The F/I/UP hits above are no longer enabled at all:
                  #   `select` replaced all 413 defaults with pycodestyle-E alone.
```

- **`select`** — *replaces* the enabled set; explicit and reproducible, for a locked-down list.
- **`extend-select`** — *adds* on top of whatever `select` resolved to; bolts a category onto the defaults.
- **`ignore`** / **`extend-ignore`** — subtract. `ignore` beats `select` for the same prefix, and
  more specific prefixes beat less specific ones.
- **`ALL`** — every stable rule, including mutually contradictory ones (ruff auto-disables known
  conflicts like `D203` vs `D211`). It also opts you into new rules on every upgrade.

CLI beats config file; closest config file beats an inherited one. A CLI `--select` also **discards
the config's `ignore`** — `--extend-select` keeps it ([references/rule-selection.md](references/rule-selection.md)).

## Rule prefixes → upstream tool

Generated from `ruff linter` (0.16.3). Codes are `PREFIX` + digits (`F401`); any prefix length is a
valid selector (`PL`, `PLC`, `PLC0414`).

| Prefix | Tool | Prefix | Tool |
|---|---|---|---|
| `AIR` | Airflow | `ERA` | eradicate |
| `FAST` | FastAPI | `YTT` | flake8-2020 |
| `ANN` | flake8-annotations | `ASYNC` | flake8-async |
| `S` | flake8-bandit | `BLE` | flake8-blind-except |
| `FBT` | flake8-boolean-trap | `B` | flake8-bugbear |
| `A` | flake8-builtins | `COM` | flake8-commas |
| `C4` | flake8-comprehensions | `CPY` | flake8-copyright |
| `DTZ` | flake8-datetimez | `T10` | flake8-debugger |
| `DJ` | flake8-django | `EM` | flake8-errmsg |
| `EXE` | flake8-executable | `FIX` | flake8-fixme |
| `FA` | flake8-future-annotations | `INT` | flake8-gettext |
| `ISC` | flake8-implicit-str-concat | `ICN` | flake8-import-conventions |
| `LOG` | flake8-logging | `G` | flake8-logging-format |
| `INP` | flake8-no-pep420 | `PIE` | flake8-pie |
| `T20` | flake8-print | `PYI` | flake8-pyi |
| `PT` | flake8-pytest-style | `Q` | flake8-quotes |
| `RSE` | flake8-raise | `RET` | flake8-return |
| `SLF` | flake8-self | `SIM` | flake8-simplify |
| `SLOT` | flake8-slots | `TID` | flake8-tidy-imports |
| `TD` | flake8-todos | `TC` | flake8-type-checking |
| `ARG` | flake8-unused-arguments | `PTH` | flake8-use-pathlib |
| `FLY` | flynt | `I` | isort |
| `C90` | mccabe | `NPY` | NumPy-specific rules |
| `PD` | pandas-vet | `N` | pep8-naming |
| `PERF` | Perflint | `E`/`W` | pycodestyle |
| `DOC` | pydoclint | `D` | pydocstyle |
| `F` | Pyflakes | `PGH` | pygrep-hooks |
| `PL` | Pylint | `UP` | pyupgrade |
| `FURB` | refurb | `RUF` | Ruff-specific rules |
| `TRY` | tryceratops | | |

**Never guess what a code means — look it up.** `ruff rule F401` prints the rationale, fix
availability, and examples. `ruff rule --all --output-format json` is the machine-readable catalog
(fields `code`, `name`, `linter`, `preview`, `status`, `fix_availability`, `summary`, `explanation`):

```bash
ruff rule --all --output-format json | jq -r '.[] | select(.preview) | .code'   # preview-only rules
```

## Configuration

Ruff reads **`pyproject.toml` (`[tool.ruff]`)**, **`ruff.toml`**, or **`.ruff.toml`** — identical
schemas; the `.toml` files just drop the `tool.ruff` prefix.

```toml
[tool.ruff]
line-length = 88                   # defaults: line-length 88, indent-width 4
target-version = "py310"           # else inferred from requires-python, else py310 (ruff 0.14+)
required-version = "==0.16.3"      # fail loudly on a different ruff

[tool.ruff.lint]
extend-select = ["B", "I", "UP"]   # ADD to the defaults (`select` would replace them)
ignore = ["E501"]
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]              # `assert` is fine in tests

[tool.ruff.format]
quote-style = "double"             # double | single | preserve
docstring-code-format = true
```

**Discovery is nearest-wins, not cascading.** Each file uses the *closest* config and **parent
configs are ignored entirely** (a `pyproject.toml` without `[tool.ruff]` doesn't count). Within one
directory: `.ruff.toml` > `ruff.toml` > `pyproject.toml`. To share settings, opt in explicitly:

```toml
extend = "../ruff.toml"     # inherit, then override below
```

`--config` does double duty: a path (`--config path/to/ruff.toml`) **or** an inline override
(`--config "lint.dummy-variable-rgx = '__.*'"`) that beats every config file — though a dedicated
flag beats `--config`. `--isolated` ignores all config files, and `ruff config <KEY>` documents any
key; full map in [references/configuration.md](references/configuration.md).

## Formatter ↔ linter conflicts

Some lint rules fight the formatter. **None are in ruff's default set** (verified on 0.16.3), but
they arrive the moment you select their category (`Q`, `COM`, `D`, `W`, `E`, `ISC`) — add to `lint.ignore`:

```
W191, E111, E114, E117, D203, D206, D300, Q000, Q001, Q002, Q003, Q004, COM812, COM819
ISC002 — only if used without ISC001 and flake8-implicit-str-concat.allow-multiline = false
```

`E501` (line-too-long) is *compatible* but noisy — the formatter only makes a best effort at
`line-length`, so long strings/URLs still trip it. Also avoid non-default `lint.isort` settings
`force-single-line`, `force-wrap-aliases`, `lines-after-imports`, `lines-between-types`,
`split-on-trailing-comma`. **`ruff format` warns on any incompatible rule or setting — a
warning-free `ruff format` means you're clean.** ([references/formatter.md](references/formatter.md))

**`ruff format` is not `.py`-only.** It also formats Jupyter notebooks (ruff 0.6+) and Python code
blocks inside Markdown files (**ruff 0.16+, on by default**) — so on 0.16 `ruff format .` rewrites
your README. Opt out per tool with a scoped exclude: `[tool.ruff.format] exclude = ["*.md"]`.

## Suppressing violations

```python
x = 1            # noqa: F841          one code (preferred)
i = 1            # noqa: E741, F841    several
x = 1            # noqa                blanket — avoid
import math      # ruff: ignore[F401]  (ruff 0.16+) same job, ruff-only spelling
```

- **File-level:** `# ruff: noqa` (everything) or `# ruff: noqa: F841` (one rule), on its own line;
  `# flake8: noqa` is honored, and `# ruff: file-ignore[F401, ARG001]` is the bracket form.
- **Logical-line:** `# ruff: ignore[CODE]` on the line *above* covers the whole multi-line statement
  or signature; *inline* it covers only that physical line.
- **Block-level (ruff 0.15+):** `# ruff: disable[E501]` … `# ruff: enable[E501]` — codes and
  indentation must match. An unterminated `disable` runs to the end of the enclosing scope and
  raises `RUF104`; always close the range.
- **Rule *names*** (`# ruff: ignore[unused-import]`) work in the bracket forms — **preview-gated,
  not version-gated**: needs `preview = true` however new your ruff is.
- **`RUF100`** flags suppressions that no longer suppress anything —
  `ruff check --extend-select RUF100 --fix` deletes the dead ones.
- **Bulk-annotate:** `ruff check --add-noqa` or `--add-ignore`, both accepting an optional reason
  (`--add-noqa="legacy import"`) appended after the codes. **These rewrite your source in place
  and exit 0** — they are baselining tools, *not* fixers (`--fix` is). Run on a clean tree and
  read the resulting `git diff` code-by-code — there is **no preview mode** (`--add-noqa` is
  rejected when combined with `--diff`). They will just as happily suppress a real bug, after which
  `ruff check` reports "All checks passed!". **The `RUF100` ratchet does not catch that** — it flags
  only suppressions that suppress *nothing*, so a `# noqa` hiding a live bug stays green forever
  (verified on 0.16.3: `# noqa: F821` over an undefined name is invisible to `RUF100`).
- Formatter suppression is separate: `# fmt: off` / `# fmt: on` / `# fmt: skip` (statement-level).

## Adopting ruff in an existing codebase

Do not start from `select = ["ALL"]` — measure, baseline, then ratchet.

```bash
ruff check --statistics    # 1. MEASURE — ranked list of what actually fires; your real backlog
ruff check --diff          # 2. FREE WINS — dry run first, then apply safe fixes
ruff check --fix
ruff format                #    formatter as ONE isolated commit (add its SHA to .git-blame-ignore-revs)
ruff check --add-noqa      # 3. BASELINE the rest (or --add-ignore) — REWRITES IN PLACE, exits 0
ruff check --extend-select RUF100   # 4. RATCHET — fails once a suppression is obsolete
```

Add categories one at a time (`extend-select = ["B"]`, then `["B", "SIM"]`, …), re-running
`--statistics` after each. Prefer `per-file-ignores` over blanket `ignore` when a rule is only
wrong for tests, migrations, or `__init__.py`.

## CI and pre-commit

```yaml
# .pre-commit-config.yaml — hook ids are `ruff-check` and `ruff-format`
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.16.3                 # pin; ruff MINOR bumps are breaking
  hooks:
    - id: ruff-check
      args: [--fix]
    - id: ruff-format
```

```yaml
# GitHub Actions — the `github` format renders inline annotations
- run: ruff check --output-format=github .
- run: ruff format --check .
```

`--output-format` accepts `concise`, `full`, `json`, `json-lines`, `junit`, `grouped`, `github`,
`gitlab`, `pylint`, `rdjson`, `azure`, `sarif` (also `RUFF_OUTPUT_FORMAT`); `ruff format --check`
takes the same set **(ruff 0.16+)**. Other env vars: `RUFF_OUTPUT_FILE`, `RUFF_CACHE_DIR`,
`RUFF_NO_CACHE`, `NO_COLOR`/`FORCE_COLOR`.

## Troubleshooting

- **"My rules stopped firing after I added `select`."** `select` replaced the defaults — use
  `extend-select`. Confirm the resolved set with `ruff check --show-settings FILE`.
- **"I selected the rule and nothing happens."** Probably preview-gated: check the `preview` field
  (`ruff rule CODE`), then set `preview = true`. Deprecated rules are the mirror image — preview
  mode *disables* them.
- **"Ruff ignores my config."** Discovery is nearest-wins, not cascading: a parent config is
  invisible unless you `extend` it, and a `pyproject.toml` without `[tool.ruff]` is skipped.
- **"A fix broke my code."** `--fix` applies safe fixes only — suspect `--unsafe-fixes`. Narrow it
  with `lint.unfixable`, or re-classify via `lint.extend-safe-fixes`/`extend-unsafe-fixes`. A *safe*
  fix that breaks code is a bug; report it.
- **"Violations remain after `--fix`."** Not every rule has one (`fix_availability` is `Always` /
  `Sometimes` / `None`) and unsafe fixes are withheld; `--statistics` marks fixable rules `[*]`.
- **"Formatter and linter disagree."** You enabled a conflicting rule (list above) — `ruff format`
  warns about them. **"Exit code 2 in CI"** means invalid config or CLI options, not lint findings.
- **"Ruff won't check my file."** Likely excluded — `ruff check --show-files` lists what runs. Paths
  passed explicitly bypass excludes unless `--force-exclude` is set (pre-commit needs it).
- **Wrong Python target** — set `target-version` or `project.requires-python`; with neither, ruff
  assumes **py310** for lint rules (ruff 0.14+) but the *newest* supported version for syntax errors.

## References

- [references/rule-selection.md](references/rule-selection.md) — selector precedence, `ALL`, preview
  gating & `explicit-preview-rules`, per-file ignores, rule discovery, fix safety & fixability.
- [references/configuration.md](references/configuration.md) — config & file discovery, `extend`,
  `--config`/`--isolated`/argfiles, `target-version` inference, key map, env vars, caching.
- [references/formatter.md](references/formatter.md) — formatter options, Black deviations, docstring
  & Markdown code formatting, `# fmt:` suppression, range formatting, conflict rationale.
- [references/cli-reference.md](references/cli-reference.md) — every subcommand & flag, verified
  against `--help` on 0.16.3, plus output formats and exit codes.
- [references/version-features.md](references/version-features.md) — what each breaking MINOR
  (0.12 → 0.16) changed, and how to read ruff's versioning scheme.

## Resources

- **Help**: `ruff help`, `ruff <command> --help`, `ruff rule <CODE>`, `ruff config <KEY>`
- **Docs**: https://docs.astral.sh/ruff/ (rules: https://docs.astral.sh/ruff/rules/) —
  **source/releases**: https://github.com/astral-sh/ruff
