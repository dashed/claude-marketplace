# Ruff Versioning and Version Features

How to read ruff version numbers, what each breaking MINOR changed, and how preview status differs
from version. Sourced from ruff's `docs/versioning.md` and `BREAKING_CHANGES.md`; current release at
time of writing: **0.16.3 (2026-08-13)**.

## Table of contents

- [The versioning scheme](#the-versioning-scheme)
- [What lands in a MINOR vs a PATCH](#what-lands-in-a-minor-vs-a-patch)
- [Preview status is not a version](#preview-status-is-not-a-version)
- [Rule and fix lifecycle](#rule-and-fix-lifecycle)
- [Breaking changes by release](#breaking-changes-by-release)
- [Pinning ruff](#pinning-ruff)
- [Checking what your build actually does](#checking-what-your-build-actually-does)

## The versioning scheme

**Ruff does not use semver.** Its scheme is custom and documented upstream:

| Component | Meaning |
|-----------|---------|
| **MAJOR** | Unused until ruff 1.0. There is no stable API yet. |
| **MINOR** | **Breaking changes.** Stable style changes, default rule set changes, rule removals, dropped Python versions. |
| **PATCH** | Bug fixes, including behavior changes that fix bugs. |

The practical consequence: **`0.15 → 0.16` is a breaking upgrade** and should be treated like a
major version bump in any other tool. `0.16.2 → 0.16.3` is safe.

The published crates `ruff`, `ruff_linter`, and `ruff_wasm` follow this policy; all other crates are
versioned `0.0.x` and offer **no stability guarantees**.

## What lands in a MINOR vs a PATCH

**MINOR** (breaking):

- A deprecated option or feature is removed
- Configuration changes in a backwards-incompatible way
- Support for a new file type is promoted to stable
- Support for an end-of-life Python version is dropped
- Linter: a rule is promoted to stable; a stable rule's behavior changes (scope significantly
  increased, or intent changed); stable rules are **added to or removed from the default set**; a
  **safe** fix is promoted to stable; a rule is deprecated
- Formatter: **the stable style changed**
- Server: a capability or deprecated setting is removed

**PATCH**:

- Bug fixes, *including behavior changes that fix bugs*
- A new config option added backwards-compatibly (no formatting changes, no new lint errors)
- Support for a **new** Python version
- New file-type support **in preview**
- An option/feature is deprecated
- Linter: an **unsafe** fix is added; a safe fix added **in preview**; a rule's scope increased **in
  preview**; a fix's applicability **demoted**; a rule added **in preview**; a preview rule's
  behavior changes
- Formatter: stable style changed to prevent invalid syntax/semantic change/comment removal; **the
  preview style changed**
- Server: a new capability or setting

Read that list twice — it is why "we only bumped the patch version" does **not** mean "nothing about
our lint output changed." A bug fix can add diagnostics, and an unsafe fix can appear.

## Preview status is not a version

This is the distinction most commonly gotten wrong.

- **Version** answers: *is this rule present in my binary at all?*
- **Preview** answers: *will this rule actually run?*

A rule marked preview since 0.9.0 still does nothing on ruff 0.16.3 unless `preview = true`. And a
preview rule cannot be forced on by naming it — not by `select = ["ALL"]`, not by category, not by
exact code. Only `preview = true` (or `--preview`) enables it.

At 0.16.3: **969 rules total, 139 preview-only, 413 enabled by default.**

```bash
# Is this rule preview-gated in MY build?
ruff rule --all --output-format json | jq '.[] | select(.code=="FURB101") | {preview, status}'
```

The `status` field carries the version the rule reached its current state:
`{"Stable": {"since": "0.16.0"}}`, `{"Preview": {"since": "0.15.3"}}`, `{"Removed": {"since": "0.13.0"}}`.

Preview also changes non-rule behavior: rule *names* become valid selectors and valid inside
`# ruff: ignore[...]`; deprecated rules are **disabled**; `*.pyw` is discovered by default;
`--add-ignore` writes names instead of codes.

## Rule and fix lifecycle

**Rules**: new rules always land in preview; they stay there for at least one MINOR release before
promotion (a rule added in `0.6.1` is not eligible for stable until `0.8.0`); promotions may be
batched; not every preview rule gets promoted.

**Fixes** have three applicability levels — **Display** (never applied), **Unsafe** (opt-in via
`--unsafe-fixes`), **Safe** (applied by `--fix`). A fix can be introduced at a lower applicability
and promoted later; *demoting* applicability is explicitly **not** a breaking change, and the
applicability of a given fix can differ under preview.

## Breaking changes by release

### 0.16.0

- **The default rule set expanded from 59 rules to 413.** The old default was
  `["E4", "E7", "E9", "F"]`. Eighteen opinionated `E`/`F` rules were *removed* from the default set
  in the same change: `E401`, `E402`, `E701`, `E702`, `E703`, `E711`, `E712`, `E713`, `E714`,
  `E721`, `E731`, `E741`, `E742`, `E743`, `F403`, `F405`, `F406`, `F722`. **This is the single most
  consequential recent change** — any pre-0.16 guide describing ruff's defaults is wrong on 0.16.
- **Python code blocks in Markdown files are formatted by default.** `ruff format .` now touches
  `.md`.
- **`ruff: ignore` suppression comments** — `# ruff: ignore[F401]` at end of line or on the
  preceding line, plus `# ruff: file-ignore[...]`.
- **Fix diffs appear in `check` and `format --check` output.**
- **`format --check` supports the linter's output formats** (`github`, `gitlab`, `json`, …).
- **Some JSON output fields became optional** — `filename`, `location`, `end_location`, and
  `fix.edits[].location`/`end_location` may now be `null` rather than defaulting to `""` and row 1 /
  column 1.

### 0.15.0

- **2026 formatter style guide** — stable formatting output changed.
- **Block suppression comments**: `# ruff: disable[N803]` … `# ruff: enable[N803]`.
- `ruff:alpine` moved to Alpine 3.23; `ruff:debian`/`debian-slim` to Debian 13 "Trixie".
- `ppc64` binaries dropped from releases.
- All `extend`ed config files are resolved **before** falling back to a default Python version.

### 0.14.0

- **Default `target-version` is now `py310`** (was `py39`) when neither `target-version` nor
  `project.requires-python` is set.
- **Syntax errors default to the latest supported Python (3.14)** rather than the minimum; lint
  rules still use the minimum.

### 0.13.0

- `TC001`, `TC002`, `TC003`, `RUF013`, `UP037` can add `from __future__ import annotations` as part
  of their fix when `lint.future-annotations` is enabled.
- **Full module paths verify first-party imports** — ruff checks the path exists on disk, reducing
  false first-party classification.
- **Deprecated rules must be selected by exact code** — group/prefix selection no longer activates
  them.
- The deprecated macOS config fallback `~/Library/Application Support/ruff/ruff.toml` was removed.
- Removed rules: `PD901` (pandas-df-variable-name), `UP038` (non-pep604-isinstance).

### 0.12.0

- **Version-related syntax errors detected** (e.g. `match` before 3.10, irrefutable patterns before
  the final `case`).
- Syntax-error checks default to the newest supported Python (3.13 at that time).
- Multi-line f-strings with format specifiers no longer get a line break after the specifier
  (required by the Python 3.13.4 grammar change).
- `rust-toolchain.toml` removed from sdists.
- Removed rule: `S320` (suspicious-xmle-tree-usage).

### 0.11.0 / 0.10.0

- **`requires-python` inference reworked** (shipped in 0.11.0 due to a 0.10.0 release mistake): a
  `ruff.toml` without `target-version` now respects a sibling `pyproject.toml`'s `requires-python`
  even with no `[tool.ruff]` section; with a user-level config, the closest parent
  `pyproject.toml`'s `requires-python` wins; with no config at all, the closest parent
  `pyproject.toml` is consulted.
- `TYPE_CHECKING` detection now recognizes **any** local variable named `TYPE_CHECKING`; the legacy
  `if 0:` / `if False:` forms were removed.
- **More robust `noqa` parsing** — file-level and inline suppression syntax unified; mostly reads
  *more* comments, but a few previously-accepted forms now log an error.
- `RUF035` recoded to `S704`.

### 0.9.0

- **2025 formatter style guide**, and **f-string expression formatting stabilized**.

### 0.8.0

- Default `target-version` moved to `py39` (from `py38`).
- `pydoclint` diagnostics moved to the docstring's first line (may require moving `noqa` comments).
- Standalone installer switched to XDG (`~/.local/bin`) from `~/.cargo/bin`.
- New `unicode-width` version — rare `E501`/reformatting differences on Unicode-heavy lines.

### 0.7.0

- `PT001`/`PT023` default to omitting decorator parentheses when there are no arguments.
- `TRY302` recoded to `TRY203`.
- `lint.allow-unused-imports` removed in favor of `lint.pyflakes.allowed-unused-imports`.

## Pinning ruff

Because MINOR bumps are breaking, pin ruff wherever consistent output matters:

```toml
# pyproject.toml — ruff refuses to run if the binary doesn't match
[tool.ruff]
required-version = "==0.16.3"
```

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.16.3
  hooks:
    - id: ruff-check
      args: [--fix]
    - id: ruff-format
```

Also pin in whatever installs ruff (`uv.lock`, `requirements-dev.txt`, `uvx ruff@0.16.3`). When you
do bump a MINOR, read `BREAKING_CHANGES.md` for that release **before** running `--fix`.

## Checking what your build actually does

Don't infer behavior from the version number — ask the binary:

```bash
ruff --version                                  # or: ruff version --output-format json
ruff check --show-settings file.py              # fully resolved settings, incl. the enabled rule list
ruff rule CODE                                  # is it stable? does it have a fix?
ruff rule --all --output-format json | jq 'length'                              # total rules
ruff rule --all --output-format json | jq '[.[] | select(.preview)] | length'   # preview-only
ruff config KEY                                 # a config option's default + type
```

Counting the default rule set on your own build:

```bash
ruff check --show-settings some_file.py \
  | awk '/^linter\.rules\.enabled/,/^linter\.rules\.should_fix/' | grep -c '('
```
