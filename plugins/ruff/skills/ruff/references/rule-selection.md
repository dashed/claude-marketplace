# Rule Selection, Preview Gating, and Fixes

Everything about deciding *which* ruff lint rules run, and *what* ruff is allowed to change.
Verified against ruff 0.16.3.

## Table of contents

- [Discovering rules](#discovering-rules)
- [Selectors](#selectors)
- [Precedence](#precedence)
- [The `ALL` selector](#the-all-selector)
- [Preview gating](#preview-gating)
- [Per-file ignores](#per-file-ignores)
- [Fix safety](#fix-safety)
- [Controlling which rules get fixed](#controlling-which-rules-get-fixed)
- [Suppression comments](#suppression-comments)
- [Recipes](#recipes)

## Discovering rules

Never memorize the catalog — ruff ships it as queryable data. There were **969 rules** in 0.16.3
(139 preview-only, 413 enabled by default).

| Goal | Command |
|------|---------|
| Explain one rule | `ruff rule F401` |
| Explain one rule as data | `ruff rule F401 --output-format json` |
| Whole catalog as data | `ruff rule --all --output-format json` |
| Prefix → upstream tool | `ruff linter` (or `--output-format json` → `{prefix, name, url}`) |
| What fires **here** | `ruff check --statistics` |
| Resolved rule set for a file | `ruff check --show-settings FILE` |

`ruff rule --all --output-format json` entries have these fields:

| Field | Values / meaning |
|-------|------------------|
| `code` | e.g. `F401` |
| `name` | kebab-case name, e.g. `unused-import` |
| `linter` | upstream tool, e.g. `Pyflakes` |
| `preview` | `true` ⇒ requires `preview = true` to run |
| `status` | `{"Stable": {"since": "..."}}`, `{"Preview": {...}}`, or `{"Removed": {...}}` |
| `fix_availability` | `"Always"` \| `"Sometimes"` \| `"None"` |
| `summary` | one-line diagnostic message template |
| `explanation` | full Markdown docs (what/why/example) |

```bash
# Every preview-only rule
ruff rule --all --output-format json | jq -r '.[] | select(.preview) | "\(.code)\t\(.name)"'

# Rules in a category that always have a fix
ruff rule --all --output-format json \
  | jq -r '.[] | select(.code|startswith("UP")) | select(.fix_availability=="Always") | .code'

# Which upstream tool owns a prefix
ruff linter --output-format json | jq -r '.[] | select(.prefix=="PT") | .name'
```

`ruff check --statistics` is the highest-value command for an unfamiliar codebase — a ranked count
of what actually fires, with `[*]` marking rules ruff can fix:

```
2  F401   [*] unused-import
1  F841   [ ] unused-variable
1  I001   [*] unsorted-imports
```

## Selectors

A selector is a full code (`F401`) or **any prefix** of one (`F`, `PL`, `PLC`, `PLC0`, `PLC0414`).

| Setting | CLI | Effect |
|---------|-----|--------|
| `lint.select` | `--select` | **Replaces** the enabled set |
| `lint.extend-select` | `--extend-select` | **Adds** to whatever `select` resolved to |
| `lint.ignore` | `--ignore` | Subtracts |
| `lint.extend-ignore` | — | Adds to `ignore` (deprecated alias kept in the schema) |

**The default set changed in ruff 0.16.0: 413 rules, up from 59.** Before 0.16 the default was
`["E4", "E7", "E9", "F"]`, and 18 opinionated `E`/`F` rules (`E401`, `E402`, `E701`–`E703`, `E711`–
`E714`, `E721`, `E731`, `E741`–`E743`, `F403`, `F405`, `F406`, `F722`) were *dropped* from the
default set as part of the expansion. Any config or tutorial written before 0.16 assumes the small
default; on 0.16+ writing `select = ["E", "F"]` disables ~400 rules that were on a moment earlier.

To see the resolved list for real:

```bash
ruff check --show-settings some_file.py | sed -n '/^linter.rules.enabled/,/^linter.rules.should_fix/p'
```

## Precedence

1. **CLI beats config files.** Ruff takes the *highest-priority* `select` as the basis for the rule
   set, then applies `extend-select` and `ignore` adjustments. CLI options outrank config files, and
   the current config file outranks anything it inherited.
2. **Closest config file wins.** Config does not cascade (see `configuration.md`); the nearest file
   supplies the base `select`.
3. **Within one priority level, `ignore` beats `select`** for the same prefix.
4. **More specific prefixes beat less specific ones.** `--select E --ignore E501` runs all of `E`
   except `E501`; `--select E501 --ignore E` still runs `E501`. (Both verified on 0.16.3.)

**A CLI `--select` throws away the config file's `ignore` list too** — this surprises people, and
upstream docs don't spell it out. Verified on 0.16.3 with `ruff.toml` containing
`select = ["E", "F"]`, `ignore = ["E501"]`:

| Command | Result |
|---------|--------|
| *(none)* | `E741`, `F401` — `E501` suppressed by the config `ignore` |
| `--select E` | `E501`, `E741` — **the config `ignore` is gone**, `E501` now fires |
| `--extend-select W` | `E741`, `F401` — config `ignore` still applied |

So `--extend-select` composes with your config; `--select` replaces that whole layer. With
`select = ["E", "F"]` + `ignore = ["F401"]`, `ruff check --select F401` reports **only** `F401`.

## The `ALL` selector

`select = ["ALL"]` enables every **stable** rule. Caveats:

- Preview rules are still excluded unless `preview = true`.
- Some rules genuinely contradict each other (e.g. `D203` *incorrect-blank-line-before-class* vs
  `D211` *blank-line-before-class*). Ruff auto-disables known conflicting pairs under `ALL`.
- It is **not upgrade-stable**: every new ruff release can add rules to your build. Ruff's own docs
  recommend using `ALL` "with discretion".
- Deprecated rules are never included via `ALL` or a prefix — they must be named by exact code (and
  are disabled outright under `preview`).

A saner default is the 0.16 built-in set plus a few categories:

```toml
[tool.ruff.lint]
extend-select = ["B", "SIM", "PTH", "RUF"]
```

## Preview gating

**This is orthogonal to the ruff version you run.** A preview rule that shipped in 0.14 is still
invisible on 0.16.3 unless preview is on.

Take a hypothetical preview rule `HYP001` (the placeholder ruff's own docs use — there is no real
`HYP` prefix). It is **not** enabled by:

- `select = ["ALL"]`
- its category (`select = ["HYP"]`) or any prefix
- even its exact code (`select = ["HYP001"]`)

It is enabled only when `preview = true` (or `--preview`) is *also* set:

```toml
[tool.ruff.lint]
preview = true
extend-select = ["FURB"]     # now includes FURB's preview rules
```

```toml
[tool.ruff.lint]
preview = true
explicit-preview-rules = true   # opt into preview rules ONE BY ONE
extend-select = ["FURB", "FURB101"]   # only FURB101's preview-ness is honored
```

With `explicit-preview-rules = true`, a category or prefix selector will *not* pull in preview
rules — each must be named by exact code. The setting is a no-op when `preview = false`.

Other preview effects on the linter:

- **Deprecated rules are disabled** under preview; selecting one explicitly is an error.
- **Rule *names* become valid selectors** — `--select unused-import` fails on stable with
  `Selecting rules by name requires preview mode`, and works with `--preview`.
- Rule names also become usable inside `# ruff: ignore[...]` / `file-ignore` / `disable` / `enable`
  comments, and `--add-ignore` writes names instead of codes.
- Preview can widen the *scope* of an existing stable rule and change a fix's applicability.

Formatter preview (`[tool.ruff.format] preview`) is a completely separate switch controlling
unstable *style*.

## Per-file ignores

Prefer this over a blanket `ignore` when a rule is only wrong in certain trees:

```toml
[tool.ruff.lint.per-file-ignores]
"__init__.py"      = ["F401"]        # re-exports
"tests/**"         = ["S101", "ARG"] # assert; unused fixture args
"migrations/*.py"  = ["ALL"]
"scripts/*.py"     = ["T201"]        # print() is the point
```

`lint.extend-per-file-ignores` adds to an inherited map instead of replacing it. CLI equivalents:
`--per-file-ignores` / `--extend-per-file-ignores`.

## Fix safety

Ruff classifies every fix by **applicability** — this is the concept flake8 has no analog for:

| Applicability | Behavior |
|---------------|----------|
| **Safe** | Applied by `--fix`. Preserves runtime behavior; only removes comments when deleting a whole statement/expression. |
| **Unsafe** | Applied only with `--unsafe-fixes`. May change runtime behavior or drop comments. |
| **Display** | Never applied — shown only. |

The canonical unsafe example is `RUF015` (`list(...)[0]` → `next(iter(...))`): a huge speedup, but
the exception on an empty collection changes from `IndexError` to `StopIteration`.

```bash
ruff check --unsafe-fixes           # surface them (doesn't write)
ruff check --fix --unsafe-fixes     # apply them
ruff check --no-unsafe-fixes        # silence the "N hidden fixes" hint
```

Re-classify per rule:

```toml
[tool.ruff.lint]
extend-safe-fixes   = ["F601"]   # promote unsafe → safe
extend-unsafe-fixes = ["UP034"]  # demote safe → unsafe
```

Prefixes work here too (`extend-safe-fixes = ["F"]`). In the `json` output format **all** fixes are
shown regardless of safety, with an `applicability` field.

Ruff's versioning treats fixes asymmetrically: adding an *unsafe* fix or *demoting* applicability is
a PATCH-level change; *promoting* a safe fix to stable is MINOR.

## Controlling which rules get fixed

| Setting | CLI | Effect |
|---------|-----|--------|
| `lint.fixable` | `--fixable` | Whitelist of rules eligible for fixing |
| `lint.extend-fixable` | `--extend-fixable` | Adds to `fixable` |
| `lint.unfixable` | `--unfixable` | Blacklist (wins over `fixable`) |

```toml
[tool.ruff.lint]
fixable = ["ALL"]
unfixable = ["F401"]   # report unused imports, never delete them automatically
```

These only matter when fixing is enabled at all (`--fix` / `fix = true`).

Fix-related CLI modes:

| Flag | Behavior |
|------|----------|
| `--fix` | Apply safe fixes, then report what's left; exit 1 if anything remains |
| `--no-fix` | Disable fixing (overrides `fix = true` in config) |
| `--fix-only` | Apply fixes, do **not** report or fail on leftovers |
| `--diff` | Print the fix diff to stdout, write nothing (implies `--fix-only`); exit 1 if there is a diff |
| `--show-fixes` | Enumerate every fix that was applied |
| `--exit-non-zero-on-fix` | Exit 1 even when everything was fixed (useful to fail CI on drift) |

## Suppression comments

| Form | Scope | Notes |
|------|-------|-------|
| `# noqa` | that line | blanket — avoid |
| `# noqa: F841` / `# noqa: E741, F841` | that line | preferred |
| `# ruff: ignore[F401]` *(0.16+)* | logical line if above, physical line if inline | bracket syntax, ruff-only |
| `# ruff: disable[E501]` … `# ruff: enable[E501]` *(0.15+)* | block | codes + indentation must match |
| `# ruff: noqa` | whole file | own line; `# flake8: noqa` equivalent |
| `# ruff: noqa: F841` | whole file, one rule | own line |
| `# ruff: file-ignore[F401, ARG001]` | whole file | bracket form, module scope |

Details worth knowing:

- On a **multi-line string / docstring**, put `# noqa: E501` *after* the closing triple quote — it
  covers the whole string.
- For **import sorting**, `# noqa: I001` goes at the end of the *first* line of the import block.
- A `# ruff: ignore[...]` on the line **above** covers the entire logical line (a whole signature or
  list literal); the same comment **inline** covers only that physical line.
- Ignore comments **stack**: consecutive `# ruff: ignore[...]` lines plus prose all attach to the
  next logical line.
- An unterminated `# ruff: disable[...]` becomes an *implicit* range running until a scope indented
  less than the comment, and raises `RUF104`. Always write the matching `enable`.
- Range suppressions cannot *enable* a rule that isn't already selected, and have no blanket form —
  at least one code is required.
- **`RUF100`** (`unused-noqa`) flags suppressions that suppress nothing:
  `ruff check --extend-select RUF100 --fix` removes them.
- **Bulk insertion:** `ruff check --add-noqa` or `--add-ignore`, each accepting an optional reason
  (`--add-noqa="legacy"`), appended after the codes. Both write codes on stable; `--add-ignore` with
  preview writes rule *names*.
- `--ignore-noqa` makes ruff disregard every `# noqa` for one run — good for auditing a baseline.
- **isort action comments** are respected: `# isort: skip_file`, `on`, `off`, `skip`, `split`, plus
  `# ruff: isort: ...` variants. Not honored inside docstrings.

## Recipes

**Add one category safely**

```bash
ruff check --extend-select B --statistics      # see the damage first
ruff check --extend-select B --diff            # see the fixes
```

**Find which rules are costing you the most**

```bash
ruff check --statistics | sort -rn | head -20
```

**Enumerate rules you're ignoring but that would now pass**

```bash
ruff check --extend-select RUF100 --statistics
```

**Machine-readable findings for a script or CI annotation**

```bash
ruff check --output-format json | jq -r '.[] | "\(.filename):\(.location.row) \(.code) \(.message)"'
```

Note that `filename`, `location`, `end_location`, and the per-edit locations **may be `null`** in
JSON output since ruff 0.16.0 — guard against it rather than assuming row 1/column 1.
