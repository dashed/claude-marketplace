# pytest Configuration

How pytest finds its configuration, the file formats it accepts, the `rootdir`/`configfile`
discovery algorithm, the high-value ini options, the import machinery (`--import-mode`,
`pythonpath`, src-layout), and `conftest.py` layering.

Version tags like `(pytest 9.0+)` mark the minimum version an option/behavior requires; **untagged
= bedrock** (present and stable since pytest 6.x or earlier). Sources are cited inline as
`doc/en/...`.

> **Scope — what this file is NOT:**
> - **Not CLI runtime flags** (`-k`, `-x`, `-m`, `--lf`, `-p`, reporting flags) — see `cli-usage.md`.
>   This file owns **ini options** and the `addopts` default-argument mechanism.
> - **Not marker / skip / xfail *semantics*** — see `markers-skip-xfail.md`. This file covers only
>   the `markers`, `strict_markers`, `strict_xfail`, and `empty_parameter_set_mark` ini *options*.
> - **Not fixture authoring** — see `fixtures.md`.

## Contents

- [Configuration file formats & precedence](#configuration-file-formats--precedence)
- [Value syntax: TOML vs INI](#value-syntax-toml-vs-ini)
- [Initialization: rootdir & configfile discovery](#initialization-rootdir--configfile-discovery)
- [Key ini options](#key-ini-options)
  - [Collection](#collection)
  - [Invocation & defaults (`addopts`, `minversion`, `required_plugins`)](#invocation--defaults)
  - [Markers & strict mode](#markers--strict-mode)
  - [Warnings](#warnings)
  - [Logging (capture + live logs)](#logging)
  - [Temp dirs, output & misc](#temp-dirs-output--misc)
- [Import modes & `sys.path`](#import-modes--syspath)
- [`conftest.py` layering](#conftestpy-layering)
- [Troubleshooting](#troubleshooting)

## Configuration file formats & precedence

Most settings can live in a *configuration file* in the repo root. pytest looks for these files, in
**descending precedence** — the **first match wins, options are never merged across files**
(`doc/en/reference/customize.rst`):

| # | File | Section header | Notes |
|---|------|----------------|-------|
| 1 | `pytest.toml` / `.pytest.toml` | `[pytest]` | **(pytest 9.0+)** Highest precedence; matches **even when empty**. |
| 2 | `pytest.ini` / `.pytest.ini` | `[pytest]` | Matches even when empty. Dedicated pytest file; recommended for non-packaging projects. (Hidden `.pytest.ini` variant: **pytest 7.2+**.) |
| 3 | `pyproject.toml` | `[tool.pytest]` **(pytest 9.0+)** or `[tool.pytest.ini_options]` | The modern home for most projects (config lives beside build metadata). |
| 4 | `tox.ini` | `[pytest]` | Reuse tox's file if you already have one. |
| 5 | `setup.cfg` | `[tool:pytest]` | **Discouraged** — `.cfg` uses a different parser that causes hard-to-track bugs. |

`pyproject.toml` is *also* accepted as the `configfile` even when it contains **no** pytest table
(since pytest 9.0 for `[tool.pytest]`; since 8.1 for `[tool.pytest.ini_options]`), so a project with
a bare `pyproject.toml` still gets a stable `rootdir`.

Equivalent minimal config in each format:

```toml
# pytest.toml or .pytest.toml  (pytest 9.0+)
[pytest]
minversion = "9.0"
addopts = ["-ra", "-q"]
testpaths = ["tests", "integration"]
```

```toml
# pyproject.toml — native TOML types  (pytest 9.0+)
[tool.pytest]
minversion = "9.0"
addopts = ["-ra", "-q"]
testpaths = ["tests", "integration"]
```

```toml
# pyproject.toml — INI-style values inside TOML  (the long-standing form, all supported pytest)
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q"                       # a single string, not a list
testpaths = ["tests", "integration"]     # list-typed options still take arrays
```

```ini
# pytest.ini / tox.ini  (tox.ini reuses the [pytest] section)
[pytest]
minversion = 6.0
addopts = -ra -q
testpaths =
    tests
    integration
```

```ini
# setup.cfg  (note the different [tool:pytest] header)
[tool:pytest]
addopts = -ra -q
```

**Picking a format:** prefer `pyproject.toml` (`[tool.pytest]` if you can require pytest 9, else
`[tool.pytest.ini_options]`) so config sits with the rest of your project metadata. Use a dedicated
`pytest.ini`/`pytest.toml` if you want config independent of packaging. Avoid `setup.cfg`.

## Value syntax: TOML vs INI

The same option is written differently depending on file type — this is the most common source of
confusion (`doc/en/reference/reference.rst`):

| Option type | TOML (`pytest.toml` / `[tool.pytest]`) | INI (`pytest.ini` / `tox.ini` / `[tool.pytest.ini_options]`) |
|---|---|---|
| `list[str]` (`addopts`, `testpaths`, `markers`, `filterwarnings`, `python_files`) | TOML array: `["a", "b"]` | space- or newline-separated string |
| `bool` | `true` / `false` | `true`/`True`/`1` |
| `str` numeric levels (`log_cli_level`) | **must be quoted**: `"INFO"`, `"10"` | bare: `INFO` / `10` |

> In `[tool.pytest.ini_options]` (the long-standing table), values follow **INI** conventions even
> though the file is TOML — e.g. `addopts` is a single string `"-ra -q"`. In the native
> `[tool.pytest]` table **(pytest 9.0+)** and `pytest.toml`, `addopts` is a real list
> `["-ra", "-q"]`.

## Initialization: rootdir & configfile discovery

pytest computes a **`rootdir`** (a stable reference directory) and a **`configfile`** at startup,
both printed in the run header. `rootdir` is used to build test **nodeids** and as the anchor for
relative paths (e.g. `.pytest_cache`, `pythonpath`, `testpaths`). It is **not** used to modify
`sys.path` (`doc/en/reference/customize.rst`).

**Algorithm** (from the command-line `args`):

1. If `-c FILE` is passed, use that as `configfile` and its directory as `rootdir`. (`-c` cannot be
   set in `addopts` — the config file must be found *before* `addopts` is read.)
2. Determine the **common ancestor** directory of the `args` that exist on disk. With no path args,
   this is the current working directory.
3. From that ancestor **upward**, look for `pytest.toml`, `.pytest.toml`, `pytest.ini`,
   `.pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`. First match (in precedence order, only
   counting files that actually contain the relevant section) → `configfile`; its dir → `rootdir`.
4. If none matched, look **upward** for `setup.py`; if found, its dir → `rootdir`.
5. If still nothing, repeat step 3 starting from each `arg` and going upward.
6. If no config file is found at all, use the common ancestor as `rootdir` (allows running pytest in
   unconfigured trees).

Override with `--rootdir=PATH`. After startup the `Config` object exposes
`config.rootpath` and `config.inipath` (`pathlib.Path`; `inipath` is `None` when no config file was
found — it keeps the `ini` name for historical reasons); the older
`config.rootdir`/`config.inifile` (`py.path.local`) remain for back-compat.

```console
$ pytest
======================== test session starts ========================
rootdir: /home/me/project
configfile: pyproject.toml
testpaths: tests, integration
```

> **Gotcha:** a custom plugin option that takes a path (e.g. `pytest --log-output ../x.log tests/`)
> can confuse ancestor detection if you omit the test path `args`. Always pass an explicit path, or
> `.` for the cwd (`doc/en/reference/customize.rst`, `:issue:1435`).

## Key ini options

Set any of these in the `[pytest]` / `[tool.pytest(.ini_options)]` / `[tool:pytest]` section. Full
catalog: `doc/en/reference/reference.rst` (search `confval`). The high-value ones:

### Collection

| Option | Default | Purpose |
|---|---|---|
| `testpaths` | — | Directories searched when no path args are given **and** pytest runs from `rootdir`. Supports shell wildcards incl. recursive `**` **(pytest 7.2+)**. Speeds up collection and avoids stray tests. |
| `python_files` | `["test_*.py", "*_test.py"]` | Glob patterns for test module filenames. |
| `python_classes` | `["Test"]` | Name prefixes / glob patterns for test classes. |
| `python_functions` | `["test"]` | Name prefixes / glob patterns for test functions/methods. |
| `norecursedirs` | `["*.egg", ".*", "_darcs", "build", "CVS", "dist", "node_modules", "venv", "{arch}"]` | fnmatch patterns of dir *basenames* to skip. **Setting it replaces the default** — re-add the defaults you still want. |
| `consider_namespace_packages` | `false` | **(pytest 8.1+)** Resolve native PEP-420 namespace packages during collection. |
| `collect_imported_tests` | `true` | **(pytest 8.4+)** Set `false` so a test file only contributes classes/functions **defined in it**, not ones it imports (avoids collecting a production `Testament` class imported into a test). |

```toml
[tool.pytest]
testpaths = ["tests"]
python_files = ["test_*.py", "check_*.py"]
python_classes = ["Test", "*Suite"]
python_functions = ["test", "*_test"]
norecursedirs = [".*", "build", "dist", "node_modules", "fixtures"]
```

`unittest.TestCase` subclasses are always collected regardless of `python_classes`/`python_functions`
(unittest's own collector handles them). See `change naming conventions` in the docs.

### Invocation & defaults

`addopts` — prepend arguments to **every** invocation, as if typed on the command line. The single
most useful option:

```toml
[tool.pytest]
addopts = ["-ra", "--strict-markers", "--strict-config"]
```

```ini
[pytest]
addopts = -ra --strict-markers --strict-config
```

`pytest tests/test_x.py` then behaves like `pytest -ra --strict-markers --strict-config
tests/test_x.py`. The `PYTEST_ADDOPTS` environment variable appends *further* args at runtime (handy
for CI overrides without editing the file).

| Option | Purpose |
|---|---|
| `minversion` | Refuse to run on an older pytest (`minversion = "9.0"`). |
| `required_plugins` | Space-separated plugins that must be installed (with optional version specs); error if missing. E.g. `["pytest-xdist>=3.0", "pytest-cov"]`. Version specs must have no internal whitespace. |

### Markers & strict mode

| Option | Default | Purpose |
|---|---|---|
| `markers` | — | Register custom markers so they show in `--markers` and don't warn. List form. |
| `strict_markers` | `false` | **(pytest 9.0+)** ini option: unregistered markers raise errors. (The `--strict-markers` *flag* is bedrock — use it on older pytest.) |
| `strict_config` | `false` | **(pytest 9.0+)** ini option: any warning while parsing the config section becomes an error. (The `--strict-config` *flag* is bedrock.) |
| `strict_parametrization_ids` | `false` | **(pytest 9.0+)** Error on non-unique parametrize IDs instead of auto-suffixing. |
| `strict_xfail` | `false` | **(pytest 9.0+)** An `xfail`-marked test that *passes* fails the suite. Renamed from `xfail_strict`; the old name still works as an alias. |
| `strict` | `false` | **(pytest 9.0+)** Master switch enabling all four `strict_*` options above. An explicit individual option overrides it. Only enable on a pinned pytest, since future strictness options auto-enable under it. |
| `empty_parameter_set_mark` | `"skip"` | What to do when `parametrize` gets an empty set: `skip`, `xfail`, or `fail_at_collect`. |

```toml
[tool.pytest]
strict = true                                  # pytest 9.0+: markers + config + ids + xfail
markers = [
    "slow: marks tests as slow",
    "serial: must not run in parallel",
]
```

> Before pytest 9.0, enable strictness via flags/options individually: `--strict-markers`,
> `--strict-config`, and `xfail_strict = true`.

### Warnings

```toml
[tool.pytest]
filterwarnings = [
    "error",                                            # turn warnings into errors
    "ignore::DeprecationWarning",                       # except these
    "ignore:function ham\\(\\) should not be used:UserWarning",
]
max_warnings = 50                                       # pytest 9.1+
```

- `filterwarnings` — list of `action:message:category:module:lineno` filters (same grammar as the
  stdlib `-W` flag), applied in order; later test-level `@pytest.mark.filterwarnings` wins. `"error"`
  first is the recommended strict baseline.
- `max_warnings` **(pytest 9.1+)** — if all tests pass but total (non-filtered) warnings exceed this,
  pytest exits with `ExitCode.MAX_WARNINGS_ERROR` (code `6`). Also `--max-warnings`.

### Logging

pytest has two logging channels: **captured** logs (shown only on failure) and **live** logs
(streamed during the run). Both are configured purely via ini options:

```toml
[tool.pytest]
log_cli = true                                          # enable live logging
log_cli_level = "INFO"                                  # quote numeric/level in TOML
log_cli_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
log_cli_date_format = "%Y-%m-%d %H:%M:%S"

log_file = "logs/pytest.log"
log_file_level = "DEBUG"
log_file_mode = "w"                                     # "w" recreate (default) or "a" append
log_format = "%(levelname)-8s %(name)s:%(filename)s:%(lineno)d %(message)s"
log_level = "WARNING"
```

| Option | Role |
|---|---|
| `log_cli` | Master switch for live logging. |
| `log_level` | Min level captured for the failure report. |
| `log_cli_level` / `log_cli_format` / `log_cli_date_format` | Live-log level/format; fall back to `log_level`/`log_format`/`log_date_format`. |
| `log_file` / `log_file_level` / `log_file_format` / `log_file_date_format` / `log_file_mode` | Write logs to a file in addition to other handlers. (`log_file_mode`, `"w"`/`"a"`: **pytest 8.1+**.) |
| `log_auto_indent` | Auto-indent multiline log messages (`true`/`false`/integer spaces). |

### Temp dirs, output & misc

| Option | Default | Purpose |
|---|---|---|
| `tmp_path_retention_count` | `"3"` | **(pytest 7.3+)** How many sessions' `tmp_path` dirs to keep. |
| `tmp_path_retention_policy` | `"all"` | **(pytest 7.3+)** Which to keep by outcome: `all`, `failed`, or `none`. |
| `cache_dir` | `".pytest_cache"` | Cache location (relative to `rootdir`; env vars expanded). |
| `console_output_style` | `"progress"` | `classic`, `progress`, `progress-even-when-capture-no`, `count`, or `times`. |
| `usefixtures` | — | Fixtures applied to every test (like `@pytest.mark.usefixtures` globally). |
| `verbosity_assertions` **(8.0+)** / `verbosity_test_cases` **(8.1+)** / `verbosity_subtests` | `"auto"` | Per-aspect verbosity overrides; `"auto"` uses the global `-v` level. |
| `truncation_limit_chars` / `truncation_limit_lines` | `640` / `8` | **(pytest 8.4+)** Assertion-message truncation limits (`0` disables; auto-disabled on CI). |

```toml
[tool.pytest]
tmp_path_retention_policy = "failed"     # keep tmp dirs only for failed/errored tests
console_output_style = "count"
```

## Import modes & `sys.path`

pytest must import your test modules and `conftest.py` files. **How** it does so is controlled by
`--import-mode` (set on the CLI or, more commonly, in `addopts`). This governs whether duplicate test
filenames are allowed and whether `sys.path` is mutated
(`doc/en/explanation/pythonpath.rst`):

| Mode | `sys.path` change | Duplicate test filenames | Notes |
|---|---|---|---|
| `prepend` (default) | inserts module's root dir at the **front** | not allowed without packages | Classic mode. Local code shadows installed versions. |
| `append` | appends module's root dir at the **end** | not allowed without packages | Lets tests run against an **installed** copy of the package under test. |
| `importlib` | **none** | **allowed** | The most isolated mode (and newest of the three). Test modules can't import each other; put shared test helpers in your application package, not the tests dir. |

**Package vs standalone (`prepend`/`append`):**

- If a test dir is a proper package (`__init__.py` present), pytest walks **up** to the topmost
  `__init__.py` to find the package root, inserts *that* parent on `sys.path`, and imports the module
  by its full dotted name (`pkg.tests.test_x`). Duplicate basenames are fine because names are
  unique.
- If there's **no** `__init__.py`, pytest inserts the test file's own directory and imports it as a
  bare top-level module (`test_x`) — so **every test file must have a unique basename**, or you get
  an import-collision error.

```toml
# src-layout project: tests are NOT a package, code lives under src/
[tool.pytest]
addopts = ["--import-mode=importlib"]
pythonpath = ["src"]          # so `import mypkg` resolves without an editable install
```

**`pythonpath` ini option** **(pytest 7.0+)** — directories (relative to `rootdir`) prepended to
`sys.path` for the whole session. The idiomatic way to make a `src/` layout importable without an
editable install. It does **not** depend on import mode.

**`consider_namespace_packages`** **(pytest 8.1+)** — set `true` when the package under test is a
native namespace package; otherwise pytest won't traverse it correctly. Best paired with an editable
install or with the namespace root added to `pythonpath`.

**`pytest` vs `python -m pytest`** — `python -m pytest` additionally puts the current directory on
`sys.path` (standard `python -m` behavior), which can mask or change import resolution. Prefer plain
`pytest` for reproducibility unless you specifically want the cwd importable.

> **src-layout takeaway:** `src/` layout + `--import-mode=importlib` + `pythonpath = ["src"]` (or an
> editable install) is the most robust modern setup — it forbids accidental imports of uninstalled
> code and sidesteps duplicate-basename collisions. See `doc/en/explanation/goodpractices.rst`.

## `conftest.py` layering

`conftest.py` files are **local, per-directory plugins**: fixtures and hook implementations placed in
a `conftest.py` apply to that directory and everything beneath it, with **no import needed**
(`doc/en/how-to/writing_plugins.rst`).

- **Scope by location.** A hook in `tests/integration/conftest.py` runs only for items under
  `tests/integration/`. For a given test, pytest consults `conftest.py` files in the item's directory
  and **all parent directories**, applying the closest-to-root first.
- **Discovery order.** "Initial" conftests (those above/at the test paths) load early — *before*
  collection — so they may add command-line options via `pytest_addoption`. Non-initial conftests
  load lazily during collection; some hooks therefore can't be implemented in them.
- **No `__init__.py` ambiguity.** If your `conftest.py` files live outside packages, don't `import`
  anything *from* a conftest (two `conftest.py` files can collide on `sys.path`). Keep them
  package-scoped or import-free.
- **`pytest_plugins` only at the root.** Loading plugins via the `pytest_plugins` variable is
  **deprecated in non-root** `conftest.py` files (it would affect the whole tree from a nested
  location). Declare it only in the top-level `conftest.py`.

```python
# tests/integration/conftest.py — applies only to integration tests
import pytest


@pytest.fixture
def http_client():
    ...


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.integration)
```

See `plugins-hooks.md` for the full hook system, registering markers from a conftest, and turning a
conftest into a distributable plugin.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Wrong `rootdir` / `.pytest_cache` in an odd place | No config file found; add an (even empty) `pytest.ini`/`pyproject.toml` at the intended root, or pass `--rootdir`. |
| Config seems ignored | Another higher-precedence file matched first (options are never merged). Check the `configfile:` line in the header. |
| `import file mismatch` / duplicate basename error | `prepend`/`append` mode with non-package tests sharing a filename. Add `__init__.py` to make packages, rename files, or switch to `--import-mode=importlib`. |
| `ModuleNotFoundError` for your own package | Source dir not importable. Add `pythonpath = ["src"]`, or `pip install -e .`. |
| `setup.cfg` settings behaving oddly | `.cfg` uses a different parser; migrate to `pyproject.toml`/`pytest.ini`. |
| Numeric `log_cli_level` rejected in TOML | Quote it: `log_cli_level = "10"` (TOML can't mix types). |
| Custom marker warnings | Register markers in `markers` and set `strict_markers`/`--strict-markers`. |
| `xfail_strict` "unknown" on a doc you copied | On pytest 9+ the canonical name is `strict_xfail` (the old name still works as an alias). |
