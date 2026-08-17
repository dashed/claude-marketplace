# ty configuration reference

Every key below was validated against **ty 0.0.72** by feeding it to the binary via
`ty check -c '<table>.<key>=<value>'` — an unknown key errors and prints the accepted set, which
makes this a mechanical check you can repeat on your own build:

```bash
ty check -c 'environment.zzz=true'   # → unknown field `zzz`, expected one of `root`, `python-version`, ...
```

## Contents

- [Config file discovery & precedence](#config-file-discovery--precedence)
- [The six tables](#the-six-tables)
- [`environment`](#environment)
- [`src`](#src)
- [`rules`](#rules)
- [`overrides`](#overrides)
- [`terminal`](#terminal)
- [`analysis`](#analysis)
- [Environment discovery in practice](#environment-discovery-in-practice)
- [Glob syntax](#glob-syntax)

## Config file discovery & precedence

ty searches the current directory then each parent for a `pyproject.toml` or `ty.toml`.

- **`pyproject.toml`** → the `[tool.ty]` table. If there is no `tool.ty` table, the file is skipped
  and the search continues upward.
- **`ty.toml`** → identical structure with the `tool.ty.` prefix dropped (`[rules]`, `[environment]`,
  `[[overrides]]`).
- **`ty.toml` wins** when both are present in the same directory — the `[tool.ty]` section of the
  neighbouring `pyproject.toml` is then ignored entirely.
- **User-level config**: `~/.config/ty/ty.toml` (or `$XDG_CONFIG_HOME/ty/ty.toml`); on Windows
  `%APPDATA%\ty\ty.toml`. Must be `ty.toml` format. Merged with project config, project wins.
  Scalars are replaced; **arrays are merged**, with project entries appended last (so they take
  precedence for "later wins" settings).

Precedence, lowest to highest: user config → project config → `--config-file` → `-c KEY=VALUE` →
dedicated CLI flags.

## The six tables

```
environment  src  rules  overrides  terminal  analysis
```

Anything else is a hard error. Note there is **no** `[tool.ty]` top-level scalar — every setting
lives inside one of these six.

## `environment`

Accepted keys: `root`, `python-version`, `python-platform`, `extra-paths`, `typeshed`, `python`.

| Key | Type | Default | Purpose |
|---|---|---|---|
| `python` | str | `null` | Path to the project's Python environment: an interpreter (`.venv/bin/python3`), a venv dir (`.venv`), or a `sys.prefix` dir (`/usr`). Used to find `site-packages`. CLI: `--python`. |
| `python-version` | str `"M.m"` | `"3.14"` (fallback) | Target version. Resolution order: explicit setting → `project.requires-python` **lower bound** → inferred from the venv → latest supported. CLI: `--python-version`. |
| `python-platform` | str | current platform | Specializes `sys.platform`. `all` = no assumption. Values ty names: `win32`, `darwin`, `android`, `ios`, `linux`. Not validated as an enum — typos are accepted silently. CLI: `--python-platform`. |
| `root` | list[str] | auto-detected | **First-party** source roots, searched in order. Set this when your code is not at the project root or in `src/`. A `./python` directory is added automatically if it exists and is not itself a package. |
| `extra-paths` | list[str] | `[]` | Highest-priority module resolution paths. Analogous to mypy's `MYPYPATH` and pyright's `stubPath`. CLI: `--extra-search-path` (repeatable). |
| `typeshed` | str | `null` | Custom stdlib typeshed stubs directory. CLI: `--typeshed`. |

```toml
[tool.ty.environment]
python = ".venv"
python-version = "3.12"
python-platform = "linux"
root = ["./app", "./libs"]
extra-paths = ["./stubs"]
```

> **`src.root` was removed in ty 0.0.67** in favour of `environment.root`. If you see
> ``unknown field `root`, expected one of `respect-ignore-files`, `exclude-scripts`, `include`,
> `exclude` ``, you have the old key under the wrong table.

Module search order: `extra-paths` → first-party `root`s → stdlib typeshed → existing `PYTHONPATH`
directories → the environment's `site-packages`.

## `src`

Accepted keys: `include`, `exclude`, `exclude-scripts`, `respect-ignore-files`. This table controls
**which files are checked**, not where modules resolve from.

| Key | Type | Default | Purpose |
|---|---|---|---|
| `include` | list[str] | `null` (everything) | Directories/globs to check. |
| `exclude` | list[str] | `null` (defaults only) | Additional exclusions; **added to** the built-in set, not replacing it. Prefix `!` to re-include. |
| `exclude-scripts` | bool | `false` | Skip files with PEP 723 inline script metadata unless passed explicitly. CLI: `--exclude-scripts` / `--include-scripts`. |
| `respect-ignore-files` | bool | `true` | Honor `.gitignore` / `.ignore`. CLI: `--respect-ignore-files` / `--no-respect-ignore-files`. |

Built-in default exclusions (all `**/…/`): `.bzr`, `.direnv`, `.eggs`, `.git`, `.git-rewrite`,
`.hg`, `.mypy_cache`, `.nox`, `.pants.d`, `.pytype`, `.ruff_cache`, `.svn`, `.tox`, `.venv`,
`__pypackages__`, `_build`, `buck-out`, `dist`, `node_modules`, `venv`.

```toml
[tool.ty.src]
include = ["src", "tests"]
exclude = ["src/generated", "*.proto", "!**/build/"]   # `!` re-includes `build/`
```

Paths given as positional arguments to `ty check` are checked even when excluded — pass
`--force-exclude` to enforce exclusions against explicit paths too.

## `rules`

Keys are rule names, or the literal `all`. Values are `"error"`, `"warn"`, `"ignore"`.

```toml
[tool.ty.rules]
all = "error"                     # set a baseline for every rule…
redundant-cast = "ignore"         # …then carve out exceptions
possibly-missing-import = "warn"
```

An unrecognized rule name is **not** a hard error — it emits `warning[unknown-rule]` and checking
continues. That is a footgun after a rule rename: a stale entry silently stops doing anything, so
keep `unknown-rule` visible rather than ignoring it.

## `overrides`

An **array of tables** (`[[tool.ty.overrides]]`) applying rule levels — and a subset of `analysis`
settings — to files matching a pattern. Later matching overrides win.

| Key | Purpose |
|---|---|
| `include` | Patterns this override applies to. |
| `exclude` | Patterns carved back out of this override. |
| `rules` | Rule-level map for matching files. |
| `analysis` | `analysis` settings scoped to matching files. |

```toml
[[tool.ty.overrides]]
include = ["tests/**"]
rules = { possibly-missing-attribute = "ignore", possibly-unresolved-reference = "ignore" }

[[tool.ty.overrides]]
include = ["src/legacy/**"]
exclude = ["src/legacy/new/**"]
[tool.ty.overrides.analysis]
respect-type-ignore-comments = false
```

Verified: with the first override in place, a `possibly-missing-attribute` violation in
`tests/t.py` is suppressed while the identical code in `app.py` still errors.

This is the right tool for "strict in `src/`, lenient in `tests/`" — it is ty's answer to mypy's
`[[tool.mypy.overrides]]` and pyright's `executionEnvironments`.

## `terminal`

Accepted keys: `output-format`, `error-on-warning` — nothing else.

| Key | Type | Default | Purpose |
|---|---|---|---|
| `output-format` | enum | `full` | `full`, `concise`, `gitlab`, `github`, `junit`. |
| `error-on-warning` | bool | **`true`** | Whether `warning`-level diagnostics cause exit code 1. |

The `true` default is why warning-only runs exit 1. Set it to `false` (or pass
`--exit-zero-on-warning`) to make warnings advisory.

## `analysis`

Accepted keys on 0.0.72: `strict-generic-narrowing`, `strict-equality-semantics`,
`strict-literal-narrowing`, `respect-type-ignore-comments`, `allowed-unresolved-imports`,
`replace-imports-with-any`.

| Key | Type | Default | Purpose |
|---|---|---|---|
| `respect-type-ignore-comments` | bool | `true` | Whether bare PEP 484 `# type: ignore` comments suppress ty diagnostics. Set `false` to require ty's own `# ty: ignore[...]`. |
| `allowed-unresolved-imports` | list[str] | `[]` | Module glob patterns whose `unresolved-import` diagnostics are suppressed. |
| `replace-imports-with-any` | list[str] | `[]` | Module glob patterns whose imports become `typing.Any` — applies **even if the module resolves**, and suppresses import diagnostics unconditionally. |
| `strict-equality-semantics` | bool | `false` | Stricter `==`/`!=` analysis. |
| `strict-generic-narrowing` | bool | `false` | Restores the pre-0.0.69 strictly-correct `isinstance` narrowing of generics (`Top[list[Unknown]]` rather than `list[Unknown]`). |
| `strict-literal-narrowing` | bool | `false` | Stricter narrowing of literal types. **Accepted by the 0.0.72 binary but absent from `ty.schema.json` and `reference/configuration.md`** — treat as newer than the published schema and re-verify on your build. |

Module glob syntax for the two import lists differs from file globs: `*` matches within one module
component (not across `.`), `**` matches any number of components (`foo.**`), and `!` negates.
Later entries win.

```toml
[tool.ty.analysis]
allowed-unresolved-imports = ["legacy_vendor.**", "*test*.**"]
replace-imports-with-any = ["some_untyped_c_ext"]
```

`allowed-unresolved-imports` vs `replace-imports-with-any`: the first only silences the *import*
diagnostic (uses of the module still infer from whatever ty can find); the second additionally
throws away the module's type information. Reach for the first by default.

## Environment discovery in practice

This is where type checkers actually fail. ty resolves the Python environment in this order:

1. `VIRTUAL_ENV`
2. An activated Conda environment (`CONDA_PREFIX`; `VIRTUAL_ENV` wins if both are set)
3. A `.venv` directory in the project root or working directory
4. A `python3` / `python` binary on `PATH`

Explicit override: `environment.python` or `--python`. Only *virtual* environments are auto-discovered;
non-virtual environments must be configured explicitly.

`PYTHONPATH` is honored: each existing directory is inserted after `extra-paths` and before
`site-packages`, mirroring CPython's own resolution order.

Under uv or Poetry, `uv run ty check` / `poetry run ty check` set `VIRTUAL_ENV` for you — that is the
simplest correct invocation. When imports still fail, `ty check -v` prints the search paths actually
in use.

PEP 723 scripts use *their own* environment and their own `requires-python`; they do not inherit the
enclosing project's venv or Python version, and do not fall back to `.venv`.

## Glob syntax

`src.include` / `src.exclude` / `overrides.include` / `overrides.exclude` use gitignore-style globs
with one critical twist — **all patterns are anchored to the project root**:

| Pattern | Matches |
|---|---|
| `src/` | the directory `<root>/src` and its contents |
| `src` | a file *or* directory named `<root>/src` |
| `**/src` | any directory named `src` at any depth (**slow** — it defeats fast file discovery) |
| `*` | any run of characters except `/` |
| `**` | zero or more path components; must be its own component (`./**a`, `b**/` are errors) |
| `?` | any single character except `/` |
| `[abc]`, `[0-9]` | character class / range |
| `!pattern` | negation — re-includes something a previous pattern (or a built-in default) excluded |

So `exclude = ["src"]` does **not** exclude `tests/src`. Use `**/src` if you truly mean any depth,
and accept the discovery slowdown.
