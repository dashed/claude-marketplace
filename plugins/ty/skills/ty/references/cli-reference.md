# ty CLI reference

Verified against **ty 0.0.72** (`62ebbecc7`, 2026-08-14) by capturing `--help` for every command.
ty is 0.0.x — re-check with `ty check --help` on your build before trusting any flag here.

## Contents

- [Commands](#commands)
- [`ty check` — arguments](#ty-check--arguments)
- [`ty check` — environment & resolution flags](#ty-check--environment--resolution-flags)
- [`ty check` — configuration flags](#ty-check--configuration-flags)
- [`ty check` — rule severity flags](#ty-check--rule-severity-flags)
- [`ty check` — file selection flags](#ty-check--file-selection-flags)
- [`ty check` — output, exit code & global flags](#ty-check--output-exit-code--global-flags)
- [Output formats](#output-formats)
- [Exit codes](#exit-codes)
- [`ty explain`](#ty-explain)
- [`ty server`, `ty version`, completions](#ty-server-ty-version-completions)
- [Environment variables](#environment-variables)
- [CI patterns](#ci-patterns)

## Commands

```
ty <COMMAND>

  check    Check a project for type errors
  server   Start the language server
  version  Display ty's version
  explain  Explain rules and other parts of ty
  help     Print this message or the help of the given subcommand(s)

  -h, --help     Print help
  -V, --version  Print version
```

`ty generate-shell-completion <SHELL>` also exists and works, but is **hidden** from the top-level
help listing.

## `ty check` — arguments

```
ty check [OPTIONS] [PATH]...
```

`[PATH]...` — files or directories to check. Default: the project root. Paths passed explicitly are
checked even if `exclude` patterns or ignore-files would otherwise skip them (override with
`--force-exclude`).

## `ty check` — environment & resolution flags

| Flag | Notes |
|---|---|
| `--project <PROJECT>` | Run within the given project directory. `pyproject.toml` and the project `.venv` are discovered by walking up from it. Other relative paths still resolve against the **current working directory**. |
| `--python <PATH>` | Path to the project's Python environment: an interpreter (`.venv/bin/python3`), a venv directory (`.venv`), or a `sys.prefix` directory (`/usr`). Usually unnecessary under `uv run` or an activated venv. |
| `--python-version <VERSION>` | One of `3.7 3.8 3.9 3.10 3.11 3.12 3.13 3.14 3.15`. Officially supported targets are 3.10+; 3.7–3.9 are selectable but may yield false positives/negatives for stdlib APIs. |
| `--python-platform <PLATFORM>` | Specializes `sys.platform`. `all` makes no assumption. Free-form string (not a validated enum) — unrecognized values are accepted silently. |
| `--typeshed <PATH>` | Custom directory for stdlib typeshed stubs. |
| `--extra-search-path <PATH>` | Extra module-resolution source; repeatable. Advanced — for code not installed conventionally. Config equivalent: `environment.extra-paths`. |

## `ty check` — configuration flags

| Flag | Notes |
|---|---|
| `-c, --config <CONFIG_OPTION>` | A TOML `<KEY> = <VALUE>` pair as it would appear in `ty.toml`, e.g. `-c 'environment.python-version="3.12"'`. Repeatable. **Takes precedence over all config files.** Also the quickest way to test whether a key exists — an unknown key errors with the list of accepted keys. |
| `--config-file <PATH>` | Path to a `ty.toml`. A `pyproject.toml` is *not* allowed here. Env: `TY_CONFIG_FILE`. |

## `ty check` — rule severity flags

Listed under "Enabling / disabling rules". All three are repeatable, later options override earlier
ones, and all accept the literal `all` to target every rule.

| Flag | Effect |
|---|---|
| `--error <RULE>` | Treat rule as severity `error`. |
| `--warn <RULE>` | Treat rule as severity `warn`. |
| `--ignore <RULE>` | Disable the rule. |

```bash
ty check --warn unused-ignore-comment --ignore redundant-cast --error possibly-missing-import
ty check --error all
```

## `ty check` — file selection flags

| Flag | Notes |
|---|---|
| `--respect-ignore-files` / `--no-respect-ignore-files` | Honor `.gitignore`/`.ignore`. On by default. |
| `--force-exclude` / `--no-force-exclude` | Apply exclusions even to paths passed directly on the command line. |
| `--exclude-scripts` / `--include-scripts` | Exclude files containing PEP 723 inline script metadata unless passed explicitly. |
| `--exclude <EXCLUDE>` | Gitignore-style glob to exclude, e.g. `tests/`, `*.tmp`, `**/__pycache__/**`. |

## `ty check` — output, exit code & global flags

| Flag | Notes |
|---|---|
| `--output-format <FMT>` | `full` (default), `concise`, `gitlab`, `github`, `junit`. Env: `TY_OUTPUT_FORMAT`. |
| `-W, --watch` | Recheck on change, including files that depend on the changed file. Uses fine-grained incrementality — far faster than re-running `ty check`. |
| `--fix` | Apply available fixes. Output reports `(N fixed, M remaining)`. Most type errors have no automatic fix. |
| `--add-ignore` | Insert `# ty: ignore[<rule>]` comments suppressing **all** current rule diagnostics, then exit 0. The standard way to baseline an existing codebase. |
| `--error-on-warning` | Exit 1 on `warning`-or-higher. Conflicts with `--exit-zero` / `--exit-zero-on-warning`. |
| `--exit-zero` | Always exit 0. |
| `--exit-zero-on-warning` | Exit 1 only for `error`-level. |
| `-v, --verbose` | Repeatable: `-v`, `-vv`, `-vvv`. `-v` prints module search paths — the first thing to run when imports won't resolve. |
| `-q, --quiet` | Repeatable: `-q`, `-qq` (silent). |
| `--no-progress` | Hide spinners/progress bars. |
| `--color <WHEN>` | `auto`, `always`, `never`. |

## Output formats

`full` (default) prints the source span plus contextual annotations:

```
error[invalid-argument-type]: Argument to function `greet` is incorrect
 --> main.py:4:7
  |
4 | greet(42)
  |       ^^ Expected `str`, found `Literal[42]`
info: Function defined here
 --> main.py:1:5
  |
1 | def greet(name: str) -> str:
  |     ^^^^^ --------- Parameter declared here

Found 3 diagnostics
```

`concise` — one line each, `path:line:col: severity[rule] message`. Best for grepping and for agents:

```
main.py:4:7: error[invalid-argument-type] Argument to function `greet` is incorrect: Expected `str`, found `Literal[42]`
main.py:7:1: warning[undefined-reveal] `reveal_type` used without importing it
main.py:7:13: info[revealed-type] Revealed type: `str`
```

`github` — workflow commands that annotate the PR diff inline; severities map to
`::error` / `::warning` / `::notice` (the last for `info`).

`gitlab` — a JSON array of Code Quality objects (`check_name`, `description`, `severity`,
`fingerprint`, `location`). `junit` — JUnit-style XML for test-report UIs.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | No `warning`-or-higher diagnostics |
| `1` | `warning`-or-higher diagnostics found |
| `2` | Invalid CLI options, invalid configuration, or IO error |
| `101` | Internal error |
| `130` | Interrupted (Ctrl-C). Added in 0.0.56; **not** listed in the upstream exit-code table. |

Verified behaviour on 0.0.72:

| Scenario | Exit |
|---|---|
| Clean file | 0 |
| `info`-only diagnostics | 0 |
| **Warning-only, default flags** | **1** |
| Warning-only + `--exit-zero-on-warning` | 0 |
| Warning-only + `--error-on-warning` | 1 |
| Error-level + `--exit-zero` | 0 |
| Error-level + `--exit-zero-on-warning` | 1 |
| Unknown flag | 2 |
| `--error-on-warning --exit-zero` together | 2 (mutually exclusive) |

> Note: `docs/rules.md` upstream states warnings exit 0 by default. That is **wrong** as of 0.0.72 —
> `docs/reference/exit-codes.md` and the binary agree that warnings exit 1. `--error-on-warning` is
> therefore the explicit spelling of the current default; `--exit-zero-on-warning` is the flag that
> actually changes warning behaviour.

## `ty explain`

```
ty explain rule [OPTIONS] [RULE]
      --output-format <text|json>   [default: text]
```

- `ty explain rule <name>` — full docs for one rule (what it does / why it's bad / example).
  Misspellings produce `Unknown rule ... Did you mean ...?`.
- `ty explain rule` with no argument — **all** rules.
- `ty explain rule --output-format json` — the machine-readable catalog. Each entry has `name`,
  `summary`, `documentation`, `default_level` (`error`|`warn`|`ignore`), and `status`
  (`{type, since}`).

```bash
ty explain rule --output-format json | jq -r '.[] | select(.default_level=="ignore") | .name'
ty explain rule --output-format json | jq 'length'    # 126 on 0.0.72
```

## `ty server`, `ty version`, completions

```
ty server                     # LSP over stdio; no options other than --help
ty version [--output-format text|json]
ty generate-shell-completion <bash|elvish|fish|nushell|powershell|zsh>
```

`ty version --output-format json` yields `{version, commit_info:{short_commit_hash, commit_hash,
commit_date, last_tag, commits_since_last_tag}}` — use it to assert a pinned version in CI.

Completions:

```bash
echo 'eval "$(ty generate-shell-completion zsh)"' >> ~/.zshrc
ty generate-shell-completion fish > ~/.config/fish/completions/ty.fish
```

## Environment variables

ty-defined:

| Variable | Effect |
|---|---|
| `TY_CONFIG_FILE` | Path to a `ty.toml`; equivalent to `--config-file`. |
| `TY_OUTPUT_FORMAT` | Default `--output-format`. |
| `TY_LOG` | Log filter for `--verbose` output (`tracing_subscriber` syntax). `TY_LOG=ty=debug` ≈ `-vv`. |
| `TY_LOG_PROFILE` | `1`/`true` writes `tracing.folded` for flamegraph profiling. |
| `TY_MAX_PARALLELISM` | Upper bound on parallel tasks (not a hard thread cap). |

Externally defined but respected: `VIRTUAL_ENV`, `CONDA_PREFIX`, `CONDA_DEFAULT_ENV`, `_CONDA_ROOT`,
`PYTHONPATH`, `RAYON_NUM_THREADS` (same effect as `TY_MAX_PARALLELISM`), `XDG_CONFIG_HOME`.

## CI patterns

```yaml
# GitHub Actions — inline PR annotations, warnings advisory
- uses: astral-sh/setup-uv@v6
- run: uv sync --dev
- run: uv run ty check --output-format github --exit-zero-on-warning
```

```yaml
# GitLab Code Quality
ty:
  script:
    - uvx ty@0.0.72 check --output-format gitlab > gl-code-quality-report.json
  artifacts:
    reports:
      codequality: gl-code-quality-report.json
```

```yaml
# pre-commit
repos:
  - repo: https://github.com/astral-sh/ty-pre-commit
    rev: v0.0.72
    hooks:
      - id: ty
```

**Always pin ty in CI** (`uv add --dev ty` + lockfile, or `uvx ty@0.0.72`). On a 0.0.x tool, a new
rule or a stricter default in the next patch release can turn a green pipeline red with no code
change.
