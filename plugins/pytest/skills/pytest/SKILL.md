---
name: pytest
description: The pytest testing framework and its Python-specific idioms — the things that set pytest apart from unittest and generic testing. Use when writing, running, debugging, or configuring Python tests with pytest — plain `assert` (rewritten for rich introspection), dependency-injected `@pytest.fixture` (scopes, autouse, yield-teardown, conftest sharing), table-driven `@pytest.mark.parametrize`, `skip`/`skipif`/`xfail` and custom markers, `pytest.raises`/`warns`/`approx`, builtin fixtures (`tmp_path`, `monkeypatch`, `capsys`, `caplog`), the CLI (`-k`/`-m`/`-x`/`--lf`/`--pdb`/node ids), config (`pyproject.toml`/`pytest.ini`/`pytest.toml`, `addopts`, `testpaths`, `--import-mode`), and plugins/hooks (`conftest.py`, `pytest_addoption`, xdist/cov/asyncio/mock). Includes inline `(pytest N.M+)` version annotations + a version-features lookup. The pytest framework — not unittest, not tox/nox runners, not coverage.
---

# pytest

## Overview

`pytest` is the de-facto standard Python test framework. Its whole value proposition is
**removing ceremony**: a test is a plain function whose name starts with `test_`, a check is a
bare `assert`, and everything a test needs is *requested by name* and injected. There are no
`TestCase` subclasses to inherit, no `setUp`/`tearDown` to override, and no `assertEqual`
family to memorize — yet failures still report rich, introspected values.

**The mental-model shift (vs. `unittest`):**

| You'd write in `unittest`… | In pytest you write… |
|---|---|
| `class T(unittest.TestCase):` + methods | a plain module-level `def test_x():` function |
| `self.assertEqual(a, b)`, `assertTrue`, `assertRaises` | `assert a == b`; `with pytest.raises(...)` |
| `setUp` / `tearDown` / `setUpClass` | `@pytest.fixture` requested as a function argument |
| copy-paste a test body for each input | one test + `@pytest.mark.parametrize` |
| `@unittest.skip`, manual skip logic | `@pytest.mark.skip` / `skipif` / `xfail` |
| shared base classes / mixins for setup | fixtures in `conftest.py`, auto-discovered |

The shift is **from inheritance to composition-by-injection**. Setup isn't a lifecycle method on a
base class; it's a *fixture* — a small function pytest runs for you and passes in. Tests declare
dependencies the way a function declares parameters, pytest resolves the graph, and teardown is
just the code after a `yield`. Reaching for fixtures + parametrize + marks instead of class
hierarchies and loops is the entire point.

> **Disambiguation — what this skill is NOT:**
> - **Not `unittest`** — pytest *runs* existing `unittest.TestCase` and `nose`-style tests
>   unchanged, but this skill teaches the pytest-native style. (See `references/configuration.md`
>   for running mixed suites.)
> - **Not a test *runner*/orchestrator** — `tox`/`nox` manage environments and *invoke* pytest;
>   they're a layer above. pytest is what actually collects and runs tests.
> - **Not coverage** — line/branch coverage is the `pytest-cov` plugin (wraps `coverage.py`), not
>   core pytest. Mentioned in `references/plugins-hooks.md`.
> - **Not a mocking library** — use the stdlib `unittest.mock` (often via the `pytest-mock`
>   `mocker` fixture) or builtin `monkeypatch`. See `references/builtin-fixtures.md`.
> - **Not a generic testing tutorial** — assumes you know what a unit test is; covers only what's
>   *pytest-specific*.

## When to Use This Skill

| Reach for it when you need to… | pytest construct |
|---|---|
| Write a test that reports *why* it failed, with no boilerplate | plain `def test_*()` + bare `assert` |
| Provide setup/teardown and shared resources to tests | `@pytest.fixture` (+ `yield` teardown) |
| Reuse setup across files without import gymnastics | `conftest.py` (auto-discovered fixtures) |
| Run the same test over many inputs | `@pytest.mark.parametrize` |
| Assert an exception or warning is raised | `pytest.raises(...)` / `pytest.warns(...)` |
| Compare floats / nested numbers tolerantly | `pytest.approx(...)` |
| Skip, conditionally skip, or expect-fail a test | `skip` / `skipif` / `xfail` markers |
| Tag tests and run a subset | custom markers + `-m`, or `-k` name expr |
| A unique temp dir, env patching, output/log capture | `tmp_path`, `monkeypatch`, `capsys`, `caplog` |
| Re-run only failures, stop on first error, drop to a debugger | `--lf`, `-x`, `--pdb` |
| Configure discovery, default flags, warning filters | `pyproject.toml` / `pytest.ini` ini options |
| Extend collection/reporting or share options | plugins + hooks (`conftest.py`) |

## Prerequisites

```bash
pip install -U pytest        # or: uv add --dev pytest   /   uv pip install pytest
pytest --version             # e.g. "pytest 9.1.0"
```

Confirm the **installed pytest version** — it governs which features below are available:

```bash
pytest --version                                   # human-readable
python -c "import importlib.metadata as m; print(m.version('pytest'))"
```

**Version note.** pytest follows semantic versioning; new features land on **minor and major**
releases. The latest stable is **9.1.0** (2026-06-13); pytest requires **Python 3.10+**. Features
that have been stable since the **pytest 6.x era or earlier** are treated as **bedrock** and shown
here **unannotated** ("unlisted = long-standing"). Anything newer carries an inline `(pytest N.M+)`
tag — meaning "needs pytest N.M or later" — and **only when sourced** from the changelog. The full
feature → minimum-version map with citations is in
[references/version-features.md](references/version-features.md). Pin a floor in config with
`minversion` (and `required_plugins`) so an too-old pytest fails fast instead of mis-parsing.

## Core Workflows

Each snippet is runnable. Tags like `(pytest 8.2+)` mark the minimum version; untagged = bedrock.

### 1. Write a test

A test is a function named `test_*` in a file named `test_*.py` or `*_test.py`. Use a plain
`assert`; pytest **rewrites** asserts at import time so the failure shows the operands, not just
"AssertionError".

```python
# test_sample.py
def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5          # on failure: "assert 4 == 5  +  where 4 = add(2, 3)"
```

```bash
pytest                 # discover & run everything under the current tree
pytest test_sample.py::test_add   # one test by node id
```

Tests may be grouped in a `class TestThing:` (no base class needed, must be `Test`-prefixed and
have no `__init__`) — useful for sharing fixtures/marks. Each test gets a fresh class instance.

### 2. Fixtures: setup by injection

A fixture is a function decorated with `@pytest.fixture`; request it by adding its name as a test
argument. `yield` splits setup from teardown (teardown runs even if the test fails).

```python
import pytest

@pytest.fixture
def db():
    conn = connect()        # setup
    yield conn              # value handed to the test
    conn.close()            # teardown — always runs

def test_query(db):
    assert db.query("select 1") == [1]
```

- **Scopes** control reuse/lifetime: `@pytest.fixture(scope="function"|"class"|"module"|"package"|"session")` (default `function`).
- **`autouse=True`** applies a fixture to every test in scope without it being requested.
- Put fixtures in **`conftest.py`** to share them across a directory tree with zero imports.
- Fixtures can request other fixtures — pytest resolves the dependency graph.

Full coverage — finalizers, `request`, parametrized & factory fixtures, override precedence,
`usefixtures` — in [references/fixtures.md](references/fixtures.md); the builtin fixtures
(`tmp_path`, `monkeypatch`, `capsys`, `caplog`, `cache`, …) in
[references/builtin-fixtures.md](references/builtin-fixtures.md).

### 3. Parametrize: one test, many inputs

```python
import pytest

@pytest.mark.parametrize("value, expected", [(2, 4), (3, 9), (4, 16)])
def test_square(value, expected):
    assert value ** 2 == expected
```

Each row becomes its own test with a readable id (`test_square[3-9]`). Attach marks/ids to a single
case with `pytest.param(6, 36, marks=pytest.mark.xfail, id="six")`, and **stack** decorators to get
the cartesian product. More — `indirect`, custom `ids=`, `pytest_generate_tests` — in
[references/parametrize.md](references/parametrize.md).

### 4. Assert exceptions, warnings, and approximate equality

```python
import pytest

def test_raises():
    with pytest.raises(ValueError, match=r"must be positive"):
        int_sqrt(-1)

def test_warns():
    with pytest.warns(DeprecationWarning):
        old_api()

def test_float():
    assert 0.1 + 0.2 == pytest.approx(0.3)        # tolerant; works on lists/dicts too
```

`pytest.raises(...)` returns an `ExceptionInfo` (`exc.value`, `exc.type`). Details — `match=`,
exception **groups**, `RaisesGroup`, `deprecated_call`, `approx` tolerances — in
[references/assertions.md](references/assertions.md).

### 5. Skip, skipif, xfail, and custom markers

```python
import sys
import pytest

@pytest.mark.skip(reason="not implemented yet")
def test_todo(): ...

@pytest.mark.skipif(sys.platform == "win32", reason="POSIX only")
def test_posix(): ...

@pytest.mark.xfail(strict=True, reason="known bug #123")
def test_known_bug(): ...

@pytest.mark.slow                      # custom marker — register it (see below)
def test_big_import(): ...
```

Register custom markers so `--strict-markers` can catch typos:

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = ["slow: marks tests as slow"]
```

Select by marker with `-m "slow and not flaky"`. Full semantics (`run=`, `raises=`, runtime
`pytest.skip`/`importorskip`) in [references/markers-skip-xfail.md](references/markers-skip-xfail.md).

### 6. Run and select tests

```bash
pytest -q                         # quieter output
pytest -k "login and not slow"    # select by name substring expression
pytest -m slow                    # select by marker expression
pytest -x                         # stop at first failure
pytest --maxfail=2                # stop after N failures
pytest --lf                       # re-run only last-failed   (--last-failed)
pytest --ff                       # run last-failed first, then the rest
pytest -s                         # don't capture stdout (show prints)
pytest -ra                        # summary of all non-passing outcomes at the end
pytest --pdb                      # drop into the debugger on failure
pytest --durations=10             # report the 10 slowest tests
```

Node ids select precisely: `pytest tests/test_api.py::TestAuth::test_login[user2]`. Full flag tour
(traceback styles, `--co`, `--stepwise`, plugin toggles, exit codes) in
[references/cli-usage.md](references/cli-usage.md).

### 7. Configure the project

pytest reads its config from the first matching file at the **rootdir**. Prefer `pyproject.toml`:

```toml
# pyproject.toml
[tool.pytest.ini_options]            # INI-style table (pyproject.toml support is bedrock)
minversion = "7.0"
addopts = "-ra -q --strict-markers"  # flags applied to every run
testpaths = ["tests"]                # where to look when no path is given
markers = ["slow: long-running tests"]
filterwarnings = ["error"]           # turn warnings into errors
```

pytest **9.0+** also supports a dedicated `pytest.toml`/`.pytest.toml` and a native-typed
`[tool.pytest]` table in `pyproject.toml`. Other sources: `pytest.ini`, `tox.ini` (`[pytest]`),
`setup.cfg` (`[tool:pytest]`). Discovery/rootdir rules, `--import-mode` (`prepend`/`append`/
`importlib`), `pythonpath`, and the full ini-option list are in
[references/configuration.md](references/configuration.md).

## Quick Reference

Untagged = bedrock (stable since pytest 6.x or earlier). Tags mark the minimum version.

| Task | Construct |
|---|---|
| Define a test | `def test_*():` in `test_*.py` / `*_test.py` |
| Check a condition | bare `assert expr` (rewritten for rich output) |
| Setup/teardown by injection | `@pytest.fixture` + `yield` |
| Share fixtures across files | `conftest.py` |
| Fixture lifetime | `@pytest.fixture(scope="module"\|"session"\|…)` |
| Apply a fixture implicitly | `@pytest.fixture(autouse=True)` |
| Require a fixture without an arg | `@pytest.mark.usefixtures("name")` |
| Table-driven tests | `@pytest.mark.parametrize("a,b", [...])` |
| Mark one parametrized case | `pytest.param(..., marks=..., id=...)` |
| Expect an exception | `with pytest.raises(Exc, match=r"..."):` |
| Expect a warning | `with pytest.warns(Warning):` |
| Approximate float/seq compare | `pytest.approx(expected)` |
| Skip / conditionally skip | `@pytest.mark.skip` / `skipif(cond, reason=)` |
| Expected failure | `@pytest.mark.xfail(strict=True, raises=...)` |
| Skip if import missing | `pytest.importorskip("numpy")` |
| Unique temp dir | `tmp_path` fixture (`pathlib.Path`) |
| Patch env/attr safely | `monkeypatch` fixture |
| Capture stdout/stderr | `capsys` / `capfd` fixture |
| Capture log records | `caplog` fixture |
| Select by name / marker | `pytest -k EXPR` / `pytest -m EXPR` |
| Re-run failures / stop early | `pytest --lf` / `pytest -x` |
| Read args from a file | `pytest @args.txt` (pytest 8.2+) |
| Default flags / discovery | `addopts`, `testpaths` (config file) |
| Dedicated config file | `pytest.toml` / `[tool.pytest]` (pytest 9.0+) |
| Parallelize | `pytest -n auto` (pytest-xdist plugin) |
| Coverage | `pytest --cov=pkg` (pytest-cov plugin) |

## Troubleshooting

- **"fixture 'x' not found"** — the name is misspelled, the fixture lives outside the test's
  `conftest.py` scope, or you forgot `@pytest.fixture`. Run `pytest --fixtures` to list what's
  available where.
- **A test passes alone but fails in the suite** — shared state. Prefer function-scoped fixtures;
  if you widened a scope (`module`/`session`), the fixture's object is being reused/mutated.
- **`assert` shows no detail / "AssertionError" only** — asserts in a *non-test* helper module
  aren't rewritten; call `pytest.register_assert_rewrite("mypkg.helpers")` (see
  [references/assertions.md](references/assertions.md)), or keep assertions in test modules.
- **Custom marker warning ("Unknown pytest.mark.*")** — register it in `markers` and add
  `--strict-markers` to fail on typos.
- **`ModuleNotFoundError` on import / wrong module shadows another** — an `--import-mode`/layout
  issue. For a `src/` layout, set `pythonpath`/`importmode=importlib`; see
  [references/configuration.md](references/configuration.md).
- **xfail that *passes* doesn't fail the suite** — use `xfail(strict=True)` (or `xfail_strict` ini)
  so an unexpected pass (XPASS) becomes a failure.
- **Warnings I want to ignore turn into errors (or vice-versa)** — tune `filterwarnings` /
  `-W` / `@pytest.mark.filterwarnings`; see [references/cli-usage.md](references/cli-usage.md).

## Advanced Usage

Comprehensive, source-cited references (each self-contained):

- [references/fixtures.md](references/fixtures.md) — scopes, autouse, finalization, `request`,
  parametrized & factory fixtures, conftest sharing, override precedence, `usefixtures`.
- [references/builtin-fixtures.md](references/builtin-fixtures.md) — `tmp_path`/`tmp_path_factory`,
  `monkeypatch`, `capsys`/`capfd`/`capteesys`, `caplog`, `recwarn`, `cache`, `pytestconfig`, …
- [references/parametrize.md](references/parametrize.md) — `parametrize` (ids, stacking, indirect),
  parametrized fixtures, `pytest_generate_tests`.
- [references/markers-skip-xfail.md](references/markers-skip-xfail.md) — builtin & custom markers,
  `skip`/`skipif`/`xfail`, `-m` expressions, strict markers/config.
- [references/assertions.md](references/assertions.md) — assert rewriting, `raises`, exception
  groups/`RaisesGroup`, `warns`/`deprecated_call`, `approx`.
- [references/cli-usage.md](references/cli-usage.md) — selection, stopping, cache reruns, output &
  traceback flags, durations, debugging, plugin toggles, exit codes.
- [references/configuration.md](references/configuration.md) — config files & precedence, rootdir,
  ini options, `--import-mode`, `pythonpath`, conftest layering.
- [references/plugins-hooks.md](references/plugins-hooks.md) — using & writing plugins, the hook
  system, key hooks, `pytester`.
- [references/version-features.md](references/version-features.md) — feature → minimum pytest
  version, the bedrock list, and version-check guidance.
