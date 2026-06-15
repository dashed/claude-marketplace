# pytest Built-in Fixtures

pytest ships a set of fixtures you can request by name in any test — no imports, no
setup. They cover temporary files, patching/mocking, output and log capture, warnings,
test metadata, and cross-run caching. This file is the reference for each one.

Examples target **pytest 9.x / Python 3.10+** and are idiomatic: plain `def` tests,
bare `assert`, `tmp_path` over the legacy `tmpdir`, module-level imports,
`encoding="utf-8"` on text I/O. Inline tags like `(pytest 8.4+)` mark a minimum
version; untagged features are bedrock (stable since pytest 6.x or earlier). For
*defining your own* fixtures (scopes, `yield`, autouse, parametrization), see
[fixtures.md](fixtures.md). For `pytest.raises` / `pytest.warns` / `pytest.approx`, see
[assertions.md](assertions.md).

List every fixture available to a test (add `-v` to include underscore-prefixed ones):

```bash
pytest --fixtures            # all available fixtures with docstrings
pytest --fixtures test_x.py  # only those visible to that test file
```

## Table of contents

- [`tmp_path` and `tmp_path_factory`](#tmp_path-and-tmp_path_factory)
- [`monkeypatch`](#monkeypatch)
- [Capturing output: `capsys`, `capfd`, and friends](#capturing-output-capsys-capfd-and-friends)
- [`caplog`](#caplog)
- [`recwarn`](#recwarn)
- [`request`](#request)
- [`cache` / `config.cache`](#cache--configcache)
- [`pytestconfig`](#pytestconfig)
- [`record_property`, `record_xml_attribute`, `record_testsuite_property`](#record_property-record_xml_attribute-record_testsuite_property)
- [`doctest_namespace`](#doctest_namespace)
- [Quick reference](#quick-reference)

## `tmp_path` and `tmp_path_factory`

### `tmp_path`

A unique, empty temporary directory **per test function**, as a
`pathlib.Path`. The standard way to test code that touches the filesystem:

```python
CONTENT = "content"


def test_create_file(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(CONTENT, encoding="utf-8")
    assert p.read_text(encoding="utf-8") == CONTENT
    assert len(list(tmp_path.iterdir())) == 1
```

### `tmp_path_factory`

A **session-scoped** factory for creating temporary directories from fixtures or tests
— ideal for a costly artifact built once and shared:

```python
import pytest


@pytest.fixture(scope="session")
def image_file(tmp_path_factory):
    img = compute_expensive_image()
    fn = tmp_path_factory.mktemp("data") / "img.png"
    img.save(fn)
    return fn
```

API (source: `src/_pytest/tmpdir.py`):

- `tmp_path_factory.mktemp(basename, numbered=True)` → `Path`. With `numbered=True`
  pytest appends a counter to keep names unique.
- `tmp_path_factory.getbasetemp()` → `Path`, the per-run base temp directory.

### Location and retention

Temp dirs are created under `{temproot}/pytest-of-{user}/pytest-{num}/{testname}/`.
pytest keeps the **last 3** runs by default (the `{num}` counter), so you can inspect
the previous run's files. Tune with config:

- `tmp_path_retention_count` — how many runs to keep. **(pytest 7.3+)**
- `tmp_path_retention_policy` — `all` / `failed` / `none`. **(pytest 7.3+)**

Override the base directory with `--basetemp=DIR` (⚠️ that directory is **cleared
before each run** — use a dedicated path, and note retention is disabled in this mode).

### Legacy: `tmpdir` and `tmpdir_factory`

`tmpdir` / `tmpdir_factory` are the older equivalents that return `py.path.local`
objects instead of `pathlib.Path`. **Prefer `tmp_path` / `tmp_path_factory`** in new
code. They aren't removed, but to forbid them while modernizing a codebase, disable the
legacy plugin:

```bash
pytest -p no:legacypath   # makes tests using tmpdir/tmpdir_factory error
```

Source: `doc/en/how-to/tmp_path.rst`, `doc/en/builtin.rst`, `doc/en/reference/fixtures.rst`.

## `monkeypatch`

Safely set/delete attributes, dict items, and environment variables, or modify
`sys.path` / the working directory — **all undone automatically** when the requesting
test or fixture finishes. Function-scoped.

Methods (source: `src/_pytest/monkeypatch.py`):

| Method | Effect |
|---|---|
| `setattr(obj, name, value, raising=True)` | set an attribute (also `setattr("pkg.mod.attr", value)`) |
| `delattr(obj, name, raising=True)` | delete an attribute |
| `setitem(mapping, key, value)` | set a dict item |
| `delitem(mapping, key, raising=True)` | delete a dict item |
| `setenv(name, value, prepend=None)` | set an env var (with `prepend=os.pathsep`, prepend to existing) |
| `delenv(name, raising=True)` | delete an env var |
| `syspath_prepend(path)` | prepend to `sys.path` (invalidates import caches) |
| `chdir(path)` | change the working directory |
| `context()` | context manager that undoes patches on block exit |
| `undo()` | manually undo all patches so far (rarely needed) |

`raising` controls whether deleting/replacing a missing target raises
(`AttributeError`/`KeyError`) or is silently skipped.

### Patching functions and attributes

```python
from pathlib import Path


def getssh():
    return Path.home() / ".ssh"


def test_getssh(monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: Path("/abc"))
    assert getssh() == Path("/abc/.ssh")
```

**Patch where the name is looked up, not where it's defined.** If your module does
`from os import getcwd`, patch `mymodule.getcwd`, not `os.getcwd`:

```python
def test_get_json(monkeypatch):
    class MockResponse:
        @staticmethod
        def json():
            return {"mock_key": "mock_response"}

    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse())
    assert app.get_json("https://fake")["mock_key"] == "mock_response"
```

### Environment variables and dicts

```python
def test_env(monkeypatch):
    monkeypatch.setenv("USER", "TestingUser")
    monkeypatch.delenv("TOKEN", raising=False)  # tolerate it being absent
    assert get_user().lower() == "testinguser"


def test_config(monkeypatch):
    monkeypatch.setitem(app.DEFAULT_CONFIG, "user", "test_user")
    monkeypatch.delitem(app.DEFAULT_CONFIG, "database", raising=False)
```

### Scoped patching with `context()`

To bound a patch to a block (rather than the whole test) — important when patching
stdlib objects pytest itself relies on — use `monkeypatch.context()`:

```python
import functools


def test_partial(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(functools, "partial", 3)
        assert functools.partial == 3
    # undone here, before the test ends
```

> Avoid patching builtins (`open`, `compile`) and libraries pytest uses internally — it
> can break pytest. Prefer making dependencies injectable; when unavoidable, scope the
> patch with `context()`.

Source: `doc/en/how-to/monkeypatch.rst`, `src/_pytest/monkeypatch.py`.

## Capturing output: `capsys`, `capfd`, and friends

These fixtures capture what code under test writes to stdout/stderr and expose it via
`readouterr()`, which returns a namedtuple `(out, err)`. Each `readouterr()` call
**snapshots and resets** the buffer, so you can assert incrementally.

| Fixture | Captures | Returns |
|---|---|---|
| `capsys` | `sys.stdout` / `sys.stderr` | `str` |
| `capsysbinary` | `sys.stdout` / `sys.stderr` | `bytes` |
| `capfd` | OS file descriptors 1 / 2 (incl. subprocesses, C libs) | `str` |
| `capfdbinary` | OS file descriptors 1 / 2 | `bytes` |
| `capteesys` **(pytest 8.4+)** | `sys` level, **and** passes output through per `--capture=` | `str` |

```python
import sys


def test_output(capsys):
    print("hello")
    sys.stderr.write("world\n")
    captured = capsys.readouterr()
    assert captured.out == "hello\n"
    assert captured.err == "world\n"
```

Use `capfd` when output comes from a **subprocess** or C extension writing to FD 1/2
directly (which `capsys` can't see):

```python
import os


def test_system_echo(capfd):
    os.system('echo "hello"')
    assert capfd.readouterr().out == "hello\n"
```

`capteesys` **(pytest 8.4+)** captures *and* lets the output through (live-printed /
reported) according to `--capture=`, combining inspection with pass-through. (The
underlying `--capture=tee-sys` capture *mode* is older and bedrock — distinct from the
`capteesys` fixture, which is the 8.4 addition.)

**Temporarily disabling capture** inside a test — each capture fixture offers a
`disabled()` context manager:

```python
def test_progress(capsys):
    with capsys.disabled():
        print("goes straight to the real terminal")
```

> When a capture fixture is requested, it takes precedence over global `-s` /
> `--capture=no` — output in that test is still captured and available via
> `readouterr()`.

Source: `doc/en/how-to/capture-stdout-stderr.rst`, `doc/en/builtin.rst`, changelog
`#12081` (capteesys, pytest 8.4.0) and `#4597` (`--capture=tee-sys`, pytest 5.4).

## `caplog`

Capture and assert on log records emitted during a test. By default pytest captures
`WARNING`+ and shows it on failures; `caplog` lets you lower the level and inspect
records.

```python
import logging


def test_logs(caplog):
    caplog.set_level(logging.INFO)             # restored at test end
    do_work()
    assert "started" in caplog.text
    assert caplog.records[0].levelname == "INFO"
    assert caplog.record_tuples == [("myapp", logging.INFO, "started")]
```

**Setting the level:**

- `caplog.set_level(level, logger=None)` — set for the rest of the test (root logger by
  default, or a named `logger`); auto-restored at teardown.
- `with caplog.at_level(level, logger=None):` — change only inside the block.

Both also re-enable a level previously turned off globally via `logging.disable()`
**(pytest 7.4+)**.

**Inspecting captured logs:**

| Attribute / method | Gives |
|---|---|
| `caplog.records` | list of `logging.LogRecord` (current stage only) |
| `caplog.record_tuples` | list of `(logger_name, levelno, message)` |
| `caplog.messages` | list of format-interpolated message strings |
| `caplog.text` | the full formatted log output |
| `caplog.clear()` | reset captured records and text |
| `caplog.get_records(when)` | records from `"setup"` / `"call"` / `"teardown"` |

`caplog.records` holds only the **current phase's** records; use
`caplog.get_records("setup")` etc. to reach across phases (e.g. assert from a teardown
that no warnings were logged during setup/call):

```python
@pytest.fixture
def window(caplog):
    win = create_window()
    yield win
    warnings = [r for r in caplog.get_records("call") if r.levelno == logging.WARNING]
    if warnings:
        pytest.fail(f"warnings during test: {[r.message for r in warnings]}")
```

> **Warning:** `caplog` attaches a handler to the **root logger**. If the test
> reconfigures the root logger (e.g. `logging.config.dictConfig`) and *replaces* rather
> than *adds* handlers, capture stops. Ensure any reconfiguration only adds handlers.

The full API is `pytest.LogCaptureFixture`. Source: `doc/en/how-to/logging.rst`,
`doc/en/builtin.rst`.

## `recwarn`

Record **all** warnings emitted during a test. `recwarn` is a `WarningsRecorder`
(a list-like recorder); each entry is a `warnings.WarningMessage` with `.message`,
`.category`, `.filename`, `.lineno`:

```python
import warnings


def test_warns(recwarn):
    warnings.warn("deprecated", DeprecationWarning)
    assert len(recwarn) == 1
    w = recwarn.pop(DeprecationWarning)
    assert issubclass(w.category, DeprecationWarning)
    assert str(w.message) == "deprecated"
```

API (source: `src/_pytest/recwarn.py`): `len(recwarn)`, `recwarn[i]`, iteration,
`recwarn.list`, `recwarn.pop(cls=Warning)` (the first recorded warning matching `cls`),
`recwarn.clear()`.

> `recwarn` records *every* warning for the whole test. To assert a specific block
> **raises** a particular warning, prefer `pytest.warns(...)` /
> `pytest.deprecated_call(...)` — those live in [assertions.md](assertions.md).

## `request`

The `request` fixture exposes the requesting test context to a fixture — `request.param`
for parametrized fixtures, plus `.config`, `.node`, `.module`, `.cls`, `.fixturenames`,
`request.addfinalizer(...)`, `request.getfixturevalue(...)`, and more. It's primarily
used *inside fixtures you write*, so it's documented in full in
[fixtures.md → The `request` object](fixtures.md#the-request-object).

## `cache` / `config.cache`

A small JSON-backed store that **persists values across pytest runs** (the same store
that powers `--last-failed` / `--failed-first`). Reach it directly via the `cache`
fixture, or as `request.config.cache` / `pytestconfig.cache`.

```python
def test_uses_cache(cache):
    value = cache.get("myplugin/last-value", None)   # default on miss
    cache.set("myplugin/last-value", 42)             # JSON-serializable
```

API (source: `src/_pytest/cacheprovider.py`):

- `cache.get(key, default)` — `key` is a `/`-separated string; prefix it with your
  plugin/app name to avoid clashes. Returns `default` on miss or unreadable value.
- `cache.set(key, value)` — `value` must be JSON-serializable.
- `cache.mkdir(name)` → `Path` — a managed directory for non-JSON artifacts (e.g. DB
  dumps). **(pytest 7.0+)**

Inspect the cache from the CLI with `pytest --cache-show` and clear it with
`pytest --cache-clear`.

## `pytestconfig`

A session-scoped shortcut to the `pytest.Config` object (`request.config`). Read CLI
options, ini/toml settings, paths, and the cache:

```python
def test_config(pytestconfig):
    if pytestconfig.getoption("verbose") > 0:
        ...
    rootdir = pytestconfig.rootpath               # pathlib.Path
    marker_cfg = pytestconfig.getini("markers")   # ini/toml value
```

Common members: `getoption(name)`, `getini(name)`, `rootpath`, `cache`,
`get_verbosity()`, `pluginmanager`. Source: `doc/en/builtin.rst`,
`src/_pytest/fixtures.py`.

## `record_property`, `record_xml_attribute`, `record_testsuite_property`

Attach metadata to test reports, primarily for JUnit XML output.

- `record_property(name, value)` — add a `<property>` to the **calling test**'s report
  (value is XML-encoded). Available to reporters like JUnit XML.

  ```python
  def test_function(record_property):
      record_property("example_key", 1)
  ```

- `record_xml_attribute(name, value)` — add an XML **attribute** to the test's
  `<testcase>` tag (JUnit XML only; requires a compatible `junit_family`). Niche.

- `record_testsuite_property(name, value)` — **session-scoped**; add a `<property>`
  under the root `<testsuite>` for suite-wide metadata (`xunit2`-compatible):

  ```python
  def test_suite_info(record_testsuite_property):
      record_testsuite_property("ARCH", "PPC")
      record_testsuite_property("STORAGE_TYPE", "CEPH")
  ```

  > ⚠️ Does **not** currently work under `pytest-xdist` (upstream issue #7767).

Source: `doc/en/builtin.rst` (`_pytest/junitxml.py`).

## `doctest_namespace`

A **session-scoped** `dict` injected into the namespace of all doctests — handy for
making a module available under a short alias without repeating an import in every
docstring. Pair it with an autouse fixture:

```python
import numpy

import pytest


@pytest.fixture(autouse=True)
def add_np(doctest_namespace):
    doctest_namespace["np"] = numpy
```

Now doctests can use `np` directly. Source: `doc/en/builtin.rst` (`_pytest/doctest.py`).

## Quick reference

| Fixture | Purpose | Returns / key API |
|---|---|---|
| `tmp_path` | per-test temp dir | `pathlib.Path` |
| `tmp_path_factory` | session temp-dir factory | `.mktemp(name)`, `.getbasetemp()` |
| `tmpdir` / `tmpdir_factory` | legacy temp dirs | `py.path.local` — prefer `tmp_path` |
| `monkeypatch` | safe patch, auto-undone | `setattr/delattr/setitem/delitem/setenv/delenv/syspath_prepend/chdir/context` |
| `capsys` / `capsysbinary` | capture `sys` stdout/stderr | `readouterr()` → str / bytes |
| `capfd` / `capfdbinary` | capture FD 1/2 (subprocesses) | `readouterr()` → str / bytes |
| `capteesys` | capture **and** pass through | `readouterr()` → str · **pytest 8.4+** |
| `caplog` | capture log records | `set_level`, `at_level`, `records`, `record_tuples`, `messages`, `text`, `clear`, `get_records(when)` |
| `recwarn` | record all warnings | list-like; `.pop(cls)`, `.clear()` |
| `request` | requesting test context | `.param`, `.config`, …(see fixtures.md) |
| `cache` | cross-run JSON store | `.get(k, default)`, `.set(k, v)`, `.mkdir(name)` (7.0+) |
| `pytestconfig` | the `Config` object | `.getoption`, `.getini`, `.rootpath`, `.cache` |
| `record_property` | per-test report property | `record_property(name, value)` |
| `record_testsuite_property` | suite-wide property (session) | `record_testsuite_property(name, value)` |
| `doctest_namespace` | inject names into doctests | `dict` (session-scoped) |

Disable capture fixture precedence / capture globally: `pytest -s` (but a requested
capture fixture still captures). Temporarily disable inside a test:
`with capsys.disabled():`.

## Sources

- `doc/en/how-to/tmp_path.rst` — `tmp_path`, `tmp_path_factory`, retention, `--basetemp`,
  legacy `tmpdir`.
- `doc/en/how-to/monkeypatch.rst` + `src/_pytest/monkeypatch.py` — all `monkeypatch`
  methods, `context()`, `undo()`, `raising`, patch-where-used guidance.
- `doc/en/how-to/capture-stdout-stderr.rst` + `doc/en/builtin.rst` — `capsys`/`capfd`
  family, `readouterr()`, `disabled()`, `capteesys`.
- `doc/en/how-to/logging.rst` — `caplog` API, level control, `get_records`, root-logger
  warning.
- `doc/en/builtin.rst` + `doc/en/reference/fixtures.rst` — `recwarn`, `request`, `cache`,
  `pytestconfig`, `record_*`, `doctest_namespace`.
- `doc/en/changelog.rst` — `capteesys` pytest 8.4.0 (#12081); `--capture=tee-sys`
  pytest 5.4 (#4597); `cache.mkdir` 7.0 (`versionadded`); `tmp_path_retention_*`
  pytest 7.3 (#8141).
