# Ruff CLI Reference

Every flag below was captured from `ruff <command> --help` on **ruff 0.16.3** and cross-checked
string-by-string. Confirm against your own build with `ruff <command> --help`.

## Table of contents

- [Subcommands](#subcommands)
- [Global options](#global-options)
- [`ruff check`](#ruff-check)
- [`ruff format`](#ruff-format)
- [`ruff rule`](#ruff-rule)
- [`ruff linter`](#ruff-linter)
- [`ruff config`](#ruff-config)
- [`ruff analyze graph`](#ruff-analyze-graph)
- [`ruff server`](#ruff-server)
- [`ruff clean` / `ruff version`](#ruff-clean--ruff-version)
- [Output formats](#output-formats)
- [Exit codes](#exit-codes)

## Subcommands

```
ruff [OPTIONS] <COMMAND>

check    Run Ruff on the given files or directories
rule     Explain a rule (or all rules)
config   List or describe the available configuration options
linter   List all supported upstream linters
clean    Clear any caches in the current directory and any subdirectories
format   Run the Ruff formatter on the given files or directories
server   Run the language server
analyze  Run analysis over Python source code
version  Display Ruff's version
help     Print this message or the help of the given subcommand(s)
```

Top-level: `-h/--help`, `-V/--version`. Per-command help: `ruff help <command>`.

## Global options

Available on **every** subcommand:

| Flag | Meaning |
|------|---------|
| `--config <CONFIG_OPTION>` | Path to a `pyproject.toml`/`ruff.toml`, **or** an inline `"<KEY> = <VALUE>"` TOML override. Inline overrides beat all config files. |
| `--isolated` | Ignore all configuration files |
| `--color <WHEN>` | `auto` \| `always` \| `never` |
| `-v, --verbose` | Verbose logging |
| `-q, --quiet` | Print diagnostics, nothing else |
| `-s, --silent` | Disable all logging (still exits 1 on diagnostics) |

## `ruff check`

```
ruff check [OPTIONS] [FILES]...     # default FILES: `.`; `-` reads stdin
```

**Fixing**

| Flag | Meaning |
|------|---------|
| `--fix` | Apply fixes. `--no-fix` disables; `--unsafe-fixes` widens |
| `--unsafe-fixes` | Include fixes that may not retain original intent. `--no-unsafe-fixes` disables |
| `--fix-only` | Fix, but don't report or exit non-zero for leftovers. Implies `--fix` |
| `--diff` | Write nothing; print a diff per changed file, exit 0 if no diffs. Implies `--fix-only` |
| `--show-fixes` | Enumerate all fixed violations. `--no-show-fixes` disables |

**Rule selection**

| Flag | Meaning |
|------|---------|
| `--select <RULE_CODE>` | Comma-separated codes to enable (or `ALL`). **Replaces** the default set |
| `--ignore <RULE_CODE>` | Comma-separated codes to disable |
| `--extend-select <RULE_CODE>` | Like `--select`, but additive |
| `--per-file-ignores <PER_FILE_IGNORES>` | file pattern → codes |
| `--extend-per-file-ignores <...>` | additive form |
| `--fixable <RULE_CODE>` | Codes eligible for fixing (only when fixing is enabled) |
| `--unfixable <RULE_CODE>` | Codes never fixed |
| `--extend-fixable <RULE_CODE>` | additive form of `--fixable` |

**File selection**

| Flag | Meaning |
|------|---------|
| `--exclude <FILE_PATTERN>` | Omit paths from analysis |
| `--extend-exclude <FILE_PATTERN>` | Additive form |
| `--respect-gitignore` | Honor `.gitignore` etc. `--no-respect-gitignore` disables |
| `--force-exclude` | Enforce excludes even for paths passed directly (needed under pre-commit). `--no-force-exclude` disables |

**Output & behavior**

| Flag | Meaning |
|------|---------|
| `--output-format <FMT>` | See [output formats](#output-formats). Env: `RUFF_OUTPUT_FORMAT` |
| `-o, --output-file <PATH>` | Write output to a file. Env: `RUFF_OUTPUT_FILE` |
| `--statistics` | Counts for every rule with ≥1 violation |
| `--target-version <V>` | `py37 py38 py39 py310 py311 py312 py313 py314 py315` |
| `--preview` | Enable preview rules/fixes. `--no-preview` disables |
| `--extension <EXT>` | Map an extension to a language: `--extension ipy:ipynb` (`python`/`ipynb`/`pyi`) |
| `-w, --watch` | Re-run whenever files change |
| `--ignore-noqa` | Ignore all `# noqa` comments |
| `--add-noqa[=<REASON>]` | Insert `noqa` directives on failing lines; optional reason appended after the codes |
| `--add-ignore[=<REASON>]` | Insert `ruff: ignore` comments; optional reason. Under preview, writes rule *names* instead of codes |
| `--show-files` | List the files ruff would run against |
| `--show-settings` | Show the resolved settings for a given file |
| `-n, --no-cache` | Disable cache reads. Env: `RUFF_NO_CACHE` |
| `--cache-dir <DIR>` | Env: `RUFF_CACHE_DIR` |
| `--stdin-filename <PATH>` | Name to use for a file piped via stdin |
| `-e, --exit-zero` | Exit 0 even with violations |
| `--exit-non-zero-on-fix` | Exit 1 even if all violations were fixed |

## `ruff format`

```
ruff format [OPTIONS] [FILES]...    # default `.`; `-` reads stdin
```

| Flag | Meaning |
|------|---------|
| `--check` | Write nothing; exit non-zero if any file would change |
| `--diff` | Write nothing; print the difference and exit non-zero |
| `--line-length <N>` | The only format-specific value flag |
| `--range <RANGE>` | `<start_line>:<start_col>-<end_line>:<end_col>`, 1-based, end exclusive. Parts optional (`1-2`, `2`, `-3`). Single file only; not for notebooks |
| `--preview` | Unstable formatting. `--no-preview` disables |
| `--target-version <V>` | Same value set as `check` |
| `--output-format <FMT>` | For `--check` output (ruff 0.16+) |
| `--extension <EXT>` | Extension → language mapping |
| `--exit-non-zero-on-format` | Exit non-zero if any file was modified |
| `--respect-gitignore` / `--exclude` / `--extend-exclude` / `--force-exclude` | As for `check` |
| `-n, --no-cache` / `--cache-dir` / `--stdin-filename` | As for `check` |

There is **no `--fix`** on `format` (it writes by default) and no rule-selection flags.

## `ruff rule`

```
ruff rule [OPTIONS] <RULE|--all>
```

| Flag | Meaning |
|------|---------|
| `--all` | Explain every rule |
| `--output-format <text\|json>` | Default `text` |

Text output gives the name, code, upstream linter, fix availability, "What it does", "Why is this
bad?", and examples. JSON fields: `code`, `name`, `linter`, `preview`, `status`, `fix`,
`fix_availability`, `message_formats`, `source_location`, `summary`, `explanation`.

## `ruff linter`

```
ruff linter [OPTIONS]
```

`--output-format <text|json>`. Text prints `PREFIX  Name` (59 entries at 0.16.3; pycodestyle appears
once as `E/W`). JSON gives `{prefix, name, url}` per entry — note pycodestyle's `prefix` is empty in
JSON because it owns two prefixes.

## `ruff config`

```
ruff config [OPTIONS] [OPTION]
```

No argument lists every option; with a key (`ruff config lint.select`, `ruff config
format.quote-style`) it prints the description, default value, type, and an example.
`--output-format <text|json>`.

## `ruff analyze graph`

```
ruff analyze graph [OPTIONS] [FILES]...    # default `.`
```

| Flag | Meaning |
|------|---------|
| `--direction <dependencies\|dependents>` | Default `dependencies` (module → what it imports) |
| `--detect-string-imports` | Treat string literals as possible imports |
| `--min-dots <N>` | Minimum dots for a string import to count |
| `--type-checking-imports` | Include `if TYPE_CHECKING:` imports (`--no-type-checking-imports` excludes) |
| `--python <PATH>` | Virtualenv to resolve additional dependencies against |
| `--target-version <V>` | Same value set as `check` |
| `--preview` | `--no-preview` disables |

Emits a JSON import map — useful for impact analysis ("what breaks if I change this module?"):

```bash
ruff analyze graph --direction dependents | jq -r '.["src/core/db.py"][]'
```

**`ruff analyze graph` prints `warning: ruff analyze graph is experimental and may change without
warning` on every run** (observed on 0.16.3). Don't build load-bearing tooling on its output shape.

## `ruff server`

```
ruff server [OPTIONS]
```

Only `--preview` (which turns on unstable server features **and** preview mode for the linter and
formatter). This is the LSP backing the VS Code / Zed / Neovim integrations; you normally don't
invoke it by hand.

## `ruff clean` / `ruff version`

`ruff clean` takes no options beyond the globals — it deletes caches in the current directory and
all subdirectories. `ruff version` accepts `--output-format <text|json>`.

## Output formats

`--output-format` accepts, on both `check` and (since 0.16) `format --check`:

```
concise  full  json  json-lines  junit  grouped  github  gitlab  pylint  rdjson  azure  sarif
```

Default is `full`. Practical picks:

- **`full`** — human review, with source context and fix diffs (fix diffs added in ruff 0.16).
- **`concise`** — one line per diagnostic; best for grepping.
- **`github`** — `::error` annotations that GitHub renders inline on the PR diff.
- **`gitlab`** — GitLab Code Quality report.
- **`json` / `json-lines`** — scripting. **Since ruff 0.16.0, `filename`, `location`, `end_location`,
  and `fix.edits[].location`/`end_location` may be `null`** instead of defaulting to `""` and
  row 1/col 1 — handle that in any consumer.
- **`junit` / `sarif` / `rdjson` / `azure` / `pylint`** — CI and code-scanning integrations.

## Exit codes

**`ruff check`**

| Code | Meaning |
|------|---------|
| `0` | No violations, or all were fixed |
| `1` | Violations found |
| `2` | Ruff terminated abnormally — invalid configuration, invalid CLI options, or an internal error |

`--exit-zero` forces `0`; `--exit-non-zero-on-fix` forces `1` even when everything was fixed.
`--diff` exits `1` when there is a diff and `0` when there isn't.

**`ruff format`**

| Code | Meaning |
|------|---------|
| `0` | Success, whether or not files changed |
| `1` | Files were formatted **and** `--exit-non-zero-on-format` was given |
| `2` | Abnormal termination |

**`ruff format --check`**

| Code | Meaning |
|------|---------|
| `0` | Nothing would be reformatted |
| `1` | One or more files would be reformatted |
| `2` | Abnormal termination |

In CI, **treat `2` differently from `1`**: `1` is a code finding, `2` means ruff could not run
(usually a broken config or a typo'd flag) and should not be reported as a lint failure.
