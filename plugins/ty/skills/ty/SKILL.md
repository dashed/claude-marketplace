---
name: ty
description: "ty — Astral's extremely fast (Rust) Python type checker and language server, currently in 0.0.x beta. Use when running or configuring `ty check`, reading ty diagnostics, setting rule levels in `[tool.ty]` or `ty.toml`, writing `# ty: ignore[rule]` suppressions, debugging environment/module-resolution failures (`environment.python`, `python-version`, `extra-paths`, `src.include`/`exclude`), wiring ty into CI (exit codes, `--output-format github`), or migrating a project from mypy or pyright. Triggers on `ty check`, `[tool.ty]`, `ty.toml`, `# ty: ignore`, `ty explain rule`, `error[unresolved-import]`, or 'Astral type checker'. This is **ty**, the type checker — NOT **ruff** (linter/formatter) or **uv** (packaging), which are separate Astral tools with their own skills here — and it is an alternative to mypy/pyright, not those tools themselves. A bare `ty` is not a trigger: it is a common shell alias and Python import alias (`import typing as ty`); require one of the specific triggers above."
---

# ty — Python Type Checker

## Overview

ty is Astral's **type checker and language server** for Python, written in Rust — 10–100x faster
than mypy and pyright. One binary does two jobs: `ty check` (CLI) and `ty server` (LSP).

> ### ⚠️ Read this first: ty is beta
>
> **This skill is documented against `ty 0.0.72` (2026-08-14).** ty is **0.0.x**: CLI flags, rule
> names, and config keys change between *patch* releases. Always confirm the running build:
>
> ```bash
> ty --version                     # ty 0.0.72 (62ebbecc7 2026-08-14)
> ty version --output-format json  # machine-readable
> ```
>
> Because *everything* here is that new, this skill does **not** tag individual features with
> version numbers — instead see [Recently changed](#recently-changed-stale-knowledge-traps) for the
> handful of things where you may hold stale knowledge, and verify anything surprising against
> `ty check --help` and `ty explain rule <name>` on your build.

### Mental model (read this before configuring anything)

ty is **inference-first and adoption-oriented**, not annotation-gated. Four consequences that
surprise people arriving from mypy or pyright:

| Principle | What it means in practice |
|---|---|
| **Works on partially-typed code** | Unannotated symbols infer as `Unknown` (an implicit `Any`). ty follows the typing spec's *gradual guarantee*: adding types should not create new errors. It still checks unannotated function bodies — unconditionally, unlike mypy's `check_untyped_defs`. |
| **Redeclarations are legal** | The same name can be re-declared with a different type in a narrower scope. This exists so you can adopt ty incrementally. |
| **Rules have *levels*, not on/off** | Every rule is `error`, `warn`, or `ignore` — a three-state severity, set per-rule and (via `[[overrides]]`) per-file-pattern. |
| **Strict by default; no `--strict`** | ty has no strict mode because its defaults already subsume most of what mypy/pyright `--strict` turns on. You opt *into* the remaining checks rule-by-rule. |

`Unknown` is the type you will see most while adopting: it means "ty could not infer this", behaves
like `Any`, and is what keeps untyped code from erroring. (`@Todo` is different — it signals a gap
in *ty itself*, not in your code.)

> **Disambiguation — what this skill is NOT:**
> - **Not ruff** — Ruff is Astral's linter/formatter. ty does *no* linting or formatting; where a
>   check has no ty rule (e.g. "require annotations"), the answer is usually a Ruff rule.
> - **Not uv** — uv is Astral's packaging/project manager. It only appears here as the *delivery*
>   mechanism (`uvx ty`, `uv add --dev ty`).
> - **Not mypy or pyright** — ty is an alternative *to* them, with its own rule names, config keys,
>   and suppression syntax. See [Coming from mypy or pyright](#coming-from-mypy-or-pyright).
> - **No plugin system** — ty has none and plans none (so no mypy-plugin equivalent for
>   pydantic/django/SQLAlchemy; ty is adding such library support natively instead).

## When to Use This Skill

| Reach for it when you need to… | ty surface |
|---|---|
| Type check a project or file | `ty check [PATH]...` |
| Recheck on save, incrementally | `ty check --watch` |
| Look up what a rule means | `ty explain rule <name>` |
| Turn a rule up/down globally | `[tool.ty.rules]` / `--error`/`--warn`/`--ignore` |
| Relax rules for `tests/` only | `[[overrides]]` with `include`/`exclude` |
| Silence one line | `# ty: ignore[rule-name]` |
| Bulk-silence an existing codebase to adopt ty | `ty check --add-ignore` |
| Fix "cannot resolve import" | `environment.python`, `environment.root`, `extra-paths` |
| Target an older Python | `environment.python-version` / `--python-version` |
| Fail (or not fail) CI correctly | exit codes + `--error-on-warning` / `--exit-zero` |
| Annotate a GitHub Actions run | `--output-format github` |
| Get IDE hover/completions/navigation | `ty server` (LSP) via your editor |

## Install & run

```bash
uvx ty@latest check           # zero-install, pinned to a known version (recommended for one-offs)
uv add --dev ty && uv run ty check   # pin per-project so the whole team matches
uv tool install ty@latest     # global; `uv tool upgrade ty` to update
pipx install ty               # or: pip install ty
curl -LsSf https://astral.sh/ty/install.sh | sh   # standalone installer
```

In a project, run ty **inside the environment** (`uv run ty check`, or with `.venv` activated) so it
can see your dependencies. Docker: `COPY --from=ghcr.io/astral-sh/ty:latest /ty /bin/`.
Pre-commit hook: [`astral-sh/ty-pre-commit`](https://github.com/astral-sh/ty-pre-commit).

## Commands

| Command | Purpose |
|---|---|
| `ty check [PATH]...` | Check a project (default: the project root). The only command you'll use daily. |
| `ty server` | Start the language server (stdio). No options beyond `--help`; editors launch it. |
| `ty version [--output-format text\|json]` | Print version / build metadata. |
| `ty explain rule [RULE] [--output-format text\|json]` | Explain one rule, or **all** rules if `RULE` is omitted. |
| `ty generate-shell-completion <SHELL>` | Completions for `bash`, `elvish`, `fish`, `nushell`, `powershell`, `zsh`. (Works, but is hidden from top-level `--help`.) |

Full flag reference: [references/cli-reference.md](references/cli-reference.md).

## Configuration

ty reads `[tool.ty]` from `pyproject.toml`, **or** a `ty.toml` with the same shape minus the
`tool.ty.` prefix. **`ty.toml` wins** if both exist in a directory. There is also user-level config
at `~/.config/ty/ty.toml`; project config overrides it, and CLI flags override everything.

Six tables — `environment`, `src`, `rules`, `overrides`, `terminal`, `analysis`:

```toml
# pyproject.toml
[tool.ty.environment]
python = ".venv"                 # interpreter, venv dir, or sys.prefix dir
python-version = "3.12"          # else: requires-python lower bound → venv → latest supported
python-platform = "linux"        # or "all" to make no sys.platform assumption
root = ["./src"]                 # first-party search roots (NOT src.root — see below)
extra-paths = ["./stubs"]        # highest-priority module resolution (~ MYPYPATH / stubPath)

[tool.ty.src]
include = ["src", "tests"]
exclude = ["src/generated", "!**/build/"]   # leading `!` re-includes a default exclusion
respect-ignore-files = true      # honor .gitignore/.ignore

[tool.ty.rules]
possibly-unresolved-reference = "warn"
redundant-cast = "ignore"

[[tool.ty.overrides]]            # per-file-pattern rule levels
include = ["tests/**"]
rules = { possibly-missing-attribute = "ignore" }

[tool.ty.terminal]
output-format = "concise"        # full | concise | gitlab | github | junit
```

`include`/`exclude` use anchored gitignore-style globs: `src` means `<root>/src` only — use
`**/src` to match at any depth. Paths passed explicitly on the command line bypass `exclude`
(unless `--force-exclude`).

**Environment discovery is where type checkers actually fail.** ty finds third-party packages via
`VIRTUAL_ENV` → an activated Conda env → a `.venv` in the project root → `python3`/`python` on
`PATH`. If imports don't resolve, that chain is almost always the cause — see
[Troubleshooting](#troubleshooting).

Every key, its default, and all environment variables: [references/configuration.md](references/configuration.md).

## Rule levels & suppression

**Three levels, not on/off:** `error` (exit 1), `warn` (still exit 1 by default — see exit codes),
`ignore` (off). Of ty's **126** rules, 93 are `error`, 23 are `warn`, and 10 are `ignore`
(opt-in) by default.

Set them on the CLI (repeatable; later wins; `all` targets every rule):

```bash
ty check --warn unused-ignore-comment --ignore redundant-cast --error possibly-missing-import
ty check --error all          # everything at error — allowed, but not recommended
```

**Don't memorize the rule catalog — look rules up.** `ty explain rule <name>` prints the "what it
does / why it's bad / example" doc for the rule in the diagnostic you're staring at, and misspelled
names get a "did you mean" suggestion. `ty explain rule --output-format json` dumps every rule with
its `default_level` — that's the machine-readable catalog. Online: `docs/reference/rules.md`.

**Suppression** — ty's own syntax carries the rule code in brackets:

```python
a = 10 + "test"           # ty: ignore[unsupported-operator]
f(1, 2)                   # ty: ignore[missing-argument, invalid-argument-type]
x = g()                   # type: ignore[arg-type, ty:invalid-argument-type]  # shared with mypy
```

ty also honors bare PEP 484 `# type: ignore` (suppresses *everything* on the line), and
`# type: ignore[ty:<rule>]` behaves exactly like `# ty: ignore[<rule>]` — non-`ty:`-prefixed codes
are skipped, so one comment can serve two checkers. A `# ty: ignore[...]` on its own line **before
any Python code** applies file-wide. `@no_type_check` silences a whole function (not a class).

The `unused-ignore-comment` rule (warn by default) catches suppressions you no longer need — and it
can *only* be suppressed by `# ty: ignore[unused-ignore-comment]`, never by a bare `# ty: ignore`
or `# type: ignore`.

**Adopting ty on an existing codebase:** `ty check --add-ignore` writes `# ty: ignore[rule]`
comments for every current diagnostic, giving you a green baseline to burn down. It **rewrites
your source files in place and exits 0** — run it on a clean working tree and read the diff,
because it will just as happily suppress a real bug. It is *not* a fixer: `--fix` is the flag
that applies actual code fixes, and most type errors have none.

More: [references/rules-and-suppression.md](references/rules-and-suppression.md).

## Diagnostics & exit codes

Default `full` output shows the offending span plus contextual annotations (e.g. where the parameter
was declared); `--output-format concise` gives one line per diagnostic:

```
main.py:4:7: error[invalid-argument-type] Argument to function `greet` is incorrect: Expected `str`, found `Literal[42]`
```

Every diagnostic is `severity[rule-name]` — feed that rule name straight to `ty explain rule`.
`info`-level diagnostics (like `revealed-type`) never affect the exit code.

| Exit code | Meaning |
|---|---|
| `0` | No `warning`-or-higher diagnostics |
| `1` | `warning`-or-higher diagnostics found |
| `2` | Invalid CLI options, invalid configuration, or IO error |
| `101` | Internal error (panic) |
| `130` | Interrupted (Ctrl-C) — see [Recently changed](#recently-changed-stale-knowledge-traps) |

**Warnings fail the build by default** (verified on 0.0.72). Three flags adjust this, and
`--error-on-warning` is mutually exclusive with the other two:

- `--exit-zero-on-warning` — exit 1 only for `error`-level. *This* is what you want if warnings
  should be advisory.
- `--error-on-warning` — exit 1 for `warning`-or-higher (the current default, stated explicitly).
- `--exit-zero` — always exit 0; use to collect a report without failing.

### CI recipe (GitHub Actions)

```yaml
- uses: astral-sh/setup-uv@v6
- run: uv sync --dev
- run: uv run ty check --output-format github --exit-zero-on-warning
```

`--output-format github` emits `::error`/`::warning`/`::notice` workflow annotations that surface
inline on the PR diff. Use `gitlab` for Code Quality reports, `junit` for a JUnit XML artifact.
Pin ty (`uv add --dev ty`, or `uvx ty@0.0.72`) so a patch release can't turn CI red overnight.

## Coming from mypy or pyright

| Concept | mypy | pyright | ty |
|---|---|---|---|
| Suppress one line | `# type: ignore[code]` | `# pyright: ignore[reportX]` | `# ty: ignore[rule]` |
| Disable a check | `disable_error_code` | `reportX = "none"` | `<rule> = "ignore"` in `[tool.ty.rules]` |
| Severity levels | error / note | error / warning / information / hint | **`error` / `warn` / `ignore`** (map pyright's *information* and *hint* to `warn`) |
| Check unannotated bodies | `check_untyped_defs` (opt-in) | `analyzeUnannotatedFunctions` | **always on**, not configurable |
| Strict mode | `--strict` | `strict` | **none** — defaults are already strict; opt into extra rules |
| Require annotations | `disallow_untyped_defs` | `reportMissingParameterType` | **no ty rule** — use Ruff's `ANN` rules |
| Extra search path | `MYPYPATH` | `stubPath` | `environment.extra-paths` |
| Per-file overrides | `[[tool.mypy.overrides]]` | `executionEnvironments` | `[[tool.ty.overrides]]` |
| Plugins | supported | n/a | **not supported, by design** |

A ~90-row rule-to-`report*`/error-code mapping table lives in ty's own
`docs/coming-from-mypy-or-pyright.md`; the practical subset plus ready-to-paste strictness configs
are in [references/mypy-pyright-migration.md](references/mypy-pyright-migration.md).

## Editors & the language server

`ty server` speaks LSP over stdio and provides completions, hover, go-to-definition, auto-import,
inlay hints, code actions, and quick fixes, with fine-grained incremental recompute. Don't invoke it
by hand — install the integration: the official **VS Code** extension (`astral-sh.ty`), **Neovim**
via `nvim-lspconfig` (`vim.lsp.enable('ty')`), **Zed**, **PyCharm**, and **Emacs** are all covered in
ty's `docs/editors.md`. The VS Code extension sets `python.languageServer: "None"` to avoid running
two servers; set `ty.disableLanguageServices: true` to keep Pylance for IDE features and use ty only
for type checking.

## Troubleshooting

| Symptom | Cause & fix |
|---|---|
| `unresolved-import` for an installed package | ty isn't seeing your env. Run via `uv run ty check`, activate the venv, or set `--python .venv`. Confirm with `ty check -v` (prints search paths). |
| `unresolved-import` for your *own* code | Non-standard layout. Set `environment.root = ["./app"]`. (ty auto-detects only the project root and `src/`.) |
| Package resolves but has no types | Compiled-only distribution (`.so`/`.pyd`) — needs `.pyi` stubs; point `extra-paths` at them. |
| `unknown field \`root\`` under `[tool.ty.src]` | `src.root` was **removed**; it is now `environment.root`. |
| Errors from inside `.venv` | Pre-3.13 venvs lack a `.gitignore`. Run `echo "*" > .venv/.gitignore`. |
| Syntax/stdlib errors on valid code | Wrong `python-version` — ty defaults to your `requires-python` *lower* bound. |
| CI red on warnings only | Expected: warnings exit 1. Add `--exit-zero-on-warning`. |
| Diagnostics differ between CLI and editor | Different ty versions or a different resolved environment. Compare `ty --version` and the editor's interpreter setting. |
| Monorepo: cross-package imports resolve that shouldn't | `root = [...]` flattens packages into one project. Prefer `ty check --project packages/a` per package. |

### Recently changed (stale-knowledge traps)

Only the items where prior knowledge is likely *wrong* — verified against ty's CHANGELOG and the
0.0.72 binary:

| Change | Detail |
|---|---|
| `src.root` → `environment.root` | The deprecated `src.root` key was **removed in 0.0.67**. `[tool.ty.src]` now accepts only `include`, `exclude`, `exclude-scripts`, `respect-ignore-files`. |
| `isinstance` narrowing of generics relaxed | Since **0.0.69**, `isinstance(xs, list)` narrows to `list[Unknown]` rather than `Top[list[Unknown]]`, matching other checkers. Opt back in with `analysis.strict-generic-narrowing = true`. |
| `invalid-type-guard-call` removed | Removed in **0.0.60**, folded into `TypeGuard` keyword-argument narrowing. ty distinguishes `Removed rule` from `Unknown rule`, so `ty explain rule <name>` tells you which case you hit. |
| Script include/exclude flags | `--exclude-scripts` / `--include-scripts` (PEP 723 files) arrived in **0.0.64**; `src.exclude-scripts` is the config form. |
| Exit code `130` on interrupt | Added in **0.0.56** and still missing from the upstream exit-code table — Ctrl-C yields 130, not 1 or 2. |

## References

- [references/cli-reference.md](references/cli-reference.md) — every command and flag, output formats, exit-code matrix, environment variables.
- [references/configuration.md](references/configuration.md) — all six config tables, every key and default, `[[overrides]]`, discovery and precedence.
- [references/rules-and-suppression.md](references/rules-and-suppression.md) — rule levels, looking rules up, the opt-in rules, full suppression semantics.
- [references/mypy-pyright-migration.md](references/mypy-pyright-migration.md) — migration checklist, rule/error-code mapping, strictness configs.

Upstream: [ty docs](https://docs.astral.sh/ty/) · [repo](https://github.com/astral-sh/ty) ·
[playground](https://play.ty.dev) · rule catalog `ty explain rule --output-format json`.
