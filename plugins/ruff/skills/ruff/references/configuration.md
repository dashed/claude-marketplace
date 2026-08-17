# Configuring Ruff

Config file discovery, precedence, the CLI override surface, file discovery, and the option map.
Every key listed here was cross-checked against `ruff.schema.json` at ruff 0.16.3.

## Table of contents

- [The three config files](#the-three-config-files)
- [Discovery and precedence](#discovery-and-precedence)
- [`extend`](#extend)
- [User-level configuration](#user-level-configuration)
- [CLI overrides](#cli-overrides)
- [Argfiles](#argfiles)
- [Python file discovery](#python-file-discovery)
- [Notebooks](#notebooks)
- [`target-version` inference](#target-version-inference)
- [Option map](#option-map)
- [Environment variables](#environment-variables)
- [Caching](#caching)

## The three config files

`pyproject.toml`, `ruff.toml`, and `.ruff.toml` are **functionally equivalent** and share one
schema. The only difference is the table prefix:

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
[tool.ruff.lint.pydocstyle]
convention = "google"
```

```toml
# ruff.toml / .ruff.toml
line-length = 88
[lint.pydocstyle]
convention = "google"
```

INI files (`setup.cfg`, `tox.ini`) are **not** supported.

The default configuration, if you write nothing at all:

```toml
[tool.ruff]
line-length = 88
indent-width = 4
target-version = "py310"     # ruff 0.14+ (was py39)
exclude = [ ".git", ".venv", ".mypy_cache", ".ruff_cache", "build", "dist",
            "node_modules", "site-packages", "__pypackages__", … ]   # ~25 common dirs

[tool.ruff.lint]
# 413 rules enabled by default as of ruff 0.16.0 (59 before that)
ignore = []
fixable = ["ALL"]
unfixable = []
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

## Discovery and precedence

Ruff uses **hierarchical, nearest-wins** resolution — *not* a cascade:

1. For each analyzed file, ruff walks up the directory tree and uses the **closest** config file.
   All relative paths in that file (`exclude` globs, `src`) resolve **relative to that file's
   directory**.
2. **Parent config files are ignored entirely.** Ruff does not merge across files. Use
   [`extend`](#extend) to inherit deliberately.
3. A `pyproject.toml` **without a `[tool.ruff]` section does not count** as a config file — ruff
   keeps walking up. This is the single most common "ruff is ignoring my config" cause.
4. Within one directory: **`.ruff.toml` > `ruff.toml` > `pyproject.toml`**.
5. A file passed via `--config PATH` applies to **all** analyzed files, and its relative paths
   resolve against the **current working directory**, not the config file's directory.
6. Any config-backed setting given on the CLI (`--select`, `--line-length`, …) overrides that
   setting in **every** resolved config file.

Diagnose with:

```bash
ruff check --show-settings path/to/file.py   # the fully resolved settings ruff will use
ruff check --show-files                      # which files would be analyzed
```

## `extend`

```toml
# packages/api/ruff.toml
extend = "../../ruff.toml"   # inherit everything...
line-length = 100            # ...then override
```

`extend` works across all three file formats and is the supported way to share settings in a
monorepo. As of ruff 0.15.0, all `extend`ed files are resolved **before** falling back to a default
Python version.

## User-level configuration

If **no** config file is found in the hierarchy, ruff falls back to a user-level file:

- macOS / Linux: `~/.config/ruff/ruff.toml` (respects `XDG_CONFIG_HOME`)
- Windows: `~\AppData\Roaming\ruff\ruff.toml`

The old macOS path `~/Library/Application Support/ruff/ruff.toml` was deprecated in 0.5 and
**removed in ruff 0.13.0**.

## CLI overrides

`--config` has **two** modes:

```bash
# 1. point at a file
ruff check src --config path/to/ruff.toml

# 2. inline TOML key=value override — beats every config file
ruff check src --config "lint.dummy-variable-rgx = '__.*'"
ruff check src --config "lint.per-file-ignores = {'some_file.py' = ['F841']}"
ruff format src --config "format.quote-style = 'single'"
```

Inline overrides are parsed exactly like `ruff.toml` content, so **linter options need the `lint.`
prefix and formatter options the `format.` prefix**. If both a dedicated flag and `--config` set the
same option, **the dedicated flag wins**:

```bash
ruff format f.py --line-length=90 --config "line-length=100"   # → 90
```

`--isolated` ignores every config file (useful for reproducible examples and for asking "what does
ruff do out of the box?").

Global flags available on every subcommand: `--config`, `--isolated`, `--color <auto|always|never>`,
`-v/--verbose`, `-q/--quiet`, `-s/--silent`.

## Argfiles

For very large file lists (beyond the shell's `ARG_MAX`):

```bash
ruff check @path/to/args.txt
```

One argument per line:

```text
--select
F401
--quiet
path/to/code1/
path/to/code2/
```

## Python file discovery

Default inclusions: `*.py`, `*.pyi`, `*.ipynb`, and `pyproject.toml`. In **preview**, `*.pyw` is
also discovered by default.

| Setting | Meaning |
|---------|---------|
| `include` | Replace the default inclusion globs. Must match **files**, not directories — `include = ["src"]` errors. |
| `extend-include` | Add extensions/globs to the defaults |
| `exclude` | Replace the default exclusion list |
| `extend-exclude` | Add to the default exclusion list (usually what you want) |
| `respect-gitignore` | Honor `.gitignore`, `.ignore`, `.git/info/exclude`, global gitignore (default on) |
| `force-exclude` | Apply excludes even to paths passed explicitly on the command line |

`exclude` can be scoped per tool, so one tree can be linted but not formatted:

```toml
[tool.ruff.format]
exclude = ["*.pyi"]      # lint .pyi files, don't format them
```

**Explicitly-passed paths bypass excludes** unless `force-exclude` is set. Pre-commit passes
filenames directly, so `force-exclude` is what makes your `exclude` list apply there.

Map unusual extensions to a language with `--extension`:

```bash
ruff check --extension ipy:ipynb .     # values: python | ipynb | pyi
```

## Notebooks

Jupyter notebooks are linted **and** formatted by default (since ruff 0.6.0). Opt out of one side
with a scoped `exclude`:

```toml
[tool.ruff.format]
exclude = ["*.ipynb"]    # lint notebooks only
```

In editors, use the `notebook.`-prefixed code actions (`notebook.source.organizeImports`,
`notebook.source.fixAll`) rather than the plain `source.*` ones — ruff needs a whole-notebook view,
and per-cell parallel fixing produces wrong results.

## `target-version` inference

`target-version` drives which syntax rules and rewrites apply. Resolution order:

1. An explicit `target-version` in the resolved config.
2. Otherwise, the `project.requires-python` lower bound from a nearby `pyproject.toml`. If a config
   file was *found* in the hierarchy, ruff reads `requires-python` from a `pyproject.toml` in **that
   same directory**; if none was found, from the first `pyproject.toml` in an ancestor of the CWD.
3. Otherwise **`py310`** (ruff 0.14+; it was `py39` before).

Two exceptions:

- A config passed via `--config` disables inference entirely.
- For **syntax errors**, ruff assumes the *newest* supported version (3.14 in the 0.14+ line) rather
  than the minimum, to avoid false positives in unconfigured projects.

Accepted values at 0.16.3: `py37 py38 py39 py310 py311 py312 py313 py314 py315`.
`per-file-target-version` overrides it for specific globs.

## Option map

Top-level keys (`[tool.ruff]` / bare in `ruff.toml`) — from `ruff.schema.json`:

```
allowed-confusables  analyze  builtins  cache-dir  dummy-variable-rgx  exclude
explicit-preview-rules  extend  extend-exclude  extend-include  extend-fixable
extend-ignore  extend-per-file-ignores  extend-safe-fixes  extend-select
extend-unfixable  extend-unsafe-fixes  extension  external  fix  fix-only  fixable
force-exclude  format  ignore  ignore-init-module-imports  include  indent-width
line-length  lint  logger-objects  namespace-packages  output-format
output-prefer-rule-codes  per-file-ignores  per-file-target-version  preview
required-version  respect-gitignore  select  show-fixes  src  target-version
task-tags  typing-modules  unfixable  unsafe-fixes
```

Plus per-plugin tables that exist at both top level and under `lint.`: `flake8-annotations`,
`flake8-bandit`, `flake8-boolean-trap`, `flake8-bugbear`, `flake8-builtins`,
`flake8-comprehensions`, `flake8-copyright`, `flake8-errmsg`, `flake8-gettext`,
`flake8-implicit-str-concat`, `flake8-import-conventions`, `flake8-pytest-style`, `flake8-quotes`,
`flake8-self`, `flake8-tidy-imports`, `flake8-type-checking`, `flake8-unused-arguments`, `isort`,
`mccabe`, `pep8-naming`, `pycodestyle`, `pydocstyle`, `pyflakes`, `pylint`, `pyupgrade`.

`[tool.ruff.lint]` keys:

```
allowed-confusables  dummy-variable-rgx  exclude  explicit-preview-rules  extend-fixable
extend-ignore  extend-per-file-ignores  extend-safe-fixes  extend-select  extend-unfixable
extend-unsafe-fixes  external  fixable  future-annotations  ignore  ignore-init-module-imports
isort  logger-objects  mccabe  per-file-ignores  preview  ruff  select  task-tags
typing-extensions  typing-modules  unfixable   (+ the per-plugin tables above,
                                                plus pydoclint, pydocstyle, pyflakes, pylint,
                                                pyupgrade, pep8-naming, pycodestyle)
```

`[tool.ruff.format]` keys (the complete list — the formatter is deliberately small):

```
docstring-code-format  docstring-code-line-length  exclude  indent-style  line-ending
nested-string-quote-style  preview  quote-style  skip-magic-trailing-comma
```

Note the asymmetry: **`unsafe-fixes`, `fix`, `fix-only`, `show-fixes`, `output-format`, and
`required-version` are top-level, not under `lint`** — a frequent source of "unknown field" errors.

Look any key up without leaving the terminal:

```bash
ruff config                       # list every option
ruff config lint.select           # docs, type, default, example for one option
ruff config --output-format json  # machine-readable
```

Useful non-obvious keys:

- **`required-version`** — a PEP 440 specifier (`"==0.16.3"`, `">=0.16"`). Ruff exits with an error
  if the running binary doesn't match. The cheapest guard against version drift across a team.
- **`src`** — roots used for first-party import detection (drives `I` and `TC` accuracy). Since ruff
  0.13.0 ruff verifies the full module path exists on disk before calling an import first-party.
- **`external`** — codes from *other* tools that appear in `# noqa` comments, so `RUF100` doesn't
  delete them.
- **`builtins`** / **`typing-modules`** / **`logger-objects`** — teach ruff about project-specific
  globals, typing re-exports, and logger singletons.
- **`output-prefer-rule-codes`** — keep `F401` in output even under preview, which otherwise prefers
  human-readable names.

## Environment variables

| Variable | Equivalent |
|----------|------------|
| `RUFF_OUTPUT_FORMAT` | `--output-format` |
| `RUFF_OUTPUT_FILE` | `-o` / `--output-file` |
| `RUFF_CACHE_DIR` | `--cache-dir` |
| `RUFF_NO_CACHE` | `-n` / `--no-cache` |
| `NO_COLOR` / `FORCE_COLOR` | force color off / on |
| `CLICOLOR` / `CLICOLOR_FORCE` | also honored |

## Caching

Ruff caches per-file results in `.ruff_cache` (override with `cache-dir` / `RUFF_CACHE_DIR`).

```bash
ruff check --no-cache     # bypass cache reads for one run
ruff clean                # delete caches in this directory and all subdirectories
```

Add `.ruff_cache/` to `.gitignore`. In CI, persisting the cache directory between runs is a cheap
speedup; ruff is fast enough that it is rarely necessary.
