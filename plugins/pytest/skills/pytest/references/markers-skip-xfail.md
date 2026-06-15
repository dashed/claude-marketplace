# pytest Markers, skip & xfail

**Markers** attach metadata to tests with `@pytest.mark.<name>`. pytest ships a handful of
builtin markers — most importantly `skip`/`skipif` (don't run this test) and `xfail`
(expect this test to fail) — and lets you register **custom** markers to categorize tests
and select them on the command line with `-m`.

Examples are runnable and idiomatic for **pytest 9.x / Python 3.10+**: plain `def` test
functions, bare `assert`, and module-level imports. Inline tags like `(pytest 9.0+)` mark a
minimum version; untagged features are bedrock (stable since pytest 6.x or earlier). For
`@pytest.mark.parametrize` see [parametrize.md](parametrize.md), for `usefixtures` and
fixture mechanics see [fixtures.md](fixtures.md), and for `-k` name selection and the
`-r` reporting flags see [cli-usage.md](cli-usage.md).

## Table of contents

- [Builtin markers](#builtin-markers)
- [Custom markers and registration](#custom-markers-and-registration)
- [Strict mode: erroring on the unexpected](#strict-mode-erroring-on-the-unexpected)
- [Applying marks: function, class, module](#applying-marks-function-class-module)
- [`skip`: unconditionally skip](#skip-unconditionally-skip)
- [`skipif`: skip on a condition](#skipif-skip-on-a-condition)
- [`xfail`: expected failures](#xfail-expected-failures)
- [Skipping and xfailing at runtime](#skipping-and-xfailing-at-runtime)
- [Selecting tests with `-m`](#selecting-tests-with--m)
- [Quick reference](#quick-reference)
- [Gotchas](#gotchas)
- [References](#references)

## Builtin markers

| Marker | Effect | See |
|---|---|---|
| `skip` | Always skip the test | [below](#skip-unconditionally-skip) |
| `skipif` | Skip if a condition is true | [below](#skipif-skip-on-a-condition) |
| `xfail` | Expect the test to fail (report as `xfailed`/`xpassed`) | [below](#xfail-expected-failures) |
| `parametrize` | Run the test once per argument set | [parametrize.md](parametrize.md) |
| `usefixtures` | Require fixtures without naming them as arguments | [fixtures.md](fixtures.md) |
| `filterwarnings` | Apply a warning filter to the test | [configuration.md](configuration.md) |

List every marker known in your project (builtin + custom + plugin) with:

```
pytest --markers
```

> Marks apply to **tests** only — putting a mark on a fixture has no effect.

## Custom markers and registration

Create a custom marker just by using it: `@pytest.mark.slow`. But an **unregistered** mark
emits a warning (to catch typos like `@pytest.mark.slwo`). Register your markers in
configuration — text after the first `:` is an optional description shown by
`pytest --markers`:

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "serial",
]
```

```ini
# pytest.ini
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    serial
```

Or register programmatically (useful for plugins) in a `pytest_configure` hook:

```python
def pytest_configure(config):
    config.addinivalue_line("markers", "env(name): run only on the named environment")
```

```python
@pytest.mark.slow
def test_big_import(): ...


@pytest.mark.env("staging")
def test_against_staging(): ...
```

Custom markers can carry positional/keyword arguments (`@pytest.mark.env("staging")`);
read them back from a hook or fixture via `item.iter_markers(name="env")`, where each
`mark` has `.args` and `.kwargs`.

## Strict mode: erroring on the unexpected

By default unknown markers only **warn**. To make them hard errors (recommended for CI),
enable strict markers — either the bedrock CLI flag or the ini option:

```toml
[tool.pytest.ini_options]
addopts = ["--strict-markers"]   # CLI flag — works on all versions
strict_markers = true            # (pytest 9.0+) equivalent ini option
markers = ["slow", "serial"]
```

The related strictness switches:

| Switch | Effect | Form |
|---|---|---|
| `--strict-markers` | Unknown marker → error | CLI flag (bedrock) |
| `strict_markers = true` | Unknown marker → error | ini option `(pytest 9.0+)` |
| `--strict-config` | Config-parse warning → error | CLI flag (bedrock) |
| `strict_config = true` | Config-parse warning → error | ini option `(pytest 9.0+)` |
| `xfail_strict = true` | Make every `xfail` strict by default (the value defaults to `false`) | ini option (bedrock); also spelled `strict_xfail` `(pytest 9.0+)` |
| `strict_parametrization_ids = true` | Duplicate parametrize ids → error | ini option `(pytest 9.0+)` |
| `strict = true` | Umbrella: enables **all** of the above | ini option `(pytest 9.0+)` |

The `strict` umbrella `(pytest 9.0+)` turns on every individual strictness option at once
(and any added in future versions), so only enable it against a pinned pytest. An explicit
individual option overrides the umbrella. On pytest < 9.0 use the CLI flags
(`--strict-markers`, `--strict-config`) and the older `xfail_strict` ini option. Full
config details live in [configuration.md](configuration.md).

## Applying marks: function, class, module

A mark on a **function** applies to that test. A mark on a **class** applies to every test
method. Assigning to the `pytestmark` module global applies to every test in the file. You
can stack marks.

```python
import pytest


@pytest.mark.slow
def test_one(): ...


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX only")
class TestPosix:
    def test_a(self): ...   # both methods get the skipif
    def test_b(self): ...


# module level — applies to every test in this file
pytestmark = pytest.mark.slow
# or several:
pytestmark = [pytest.mark.slow, pytest.mark.skipif(sys.platform == "win32", reason="POSIX")]
```

If multiple `skipif` marks apply, the test is skipped if **any** condition is true. For
marks inherited through a class hierarchy, pytest follows the full **MRO** `(pytest 7.2+)`,
so a subclass collects marks from all of its base classes.

## `skip`: unconditionally skip

Mark a test that should never run right now, with an optional `reason`:

```python
@pytest.mark.skip(reason="not implemented yet")
def test_feature(): ...
```

## `skipif`: skip on a condition

Skip when a condition (evaluated at collection time) is true. Always pass a `reason`:

```python
import sys


@pytest.mark.skipif(sys.version_info < (3, 12), reason="requires Python 3.12+")
def test_new_syntax(): ...
```

Because `skipif` markers are plain objects, you can **define one once and share it** across
modules:

```python
# compat.py
needs_py312 = pytest.mark.skipif(sys.version_info < (3, 12), reason="requires 3.12+")

# test_x.py
from compat import needs_py312


@needs_py312
def test_something(): ...
```

`skipif` (like any marker) also works on classes and via `pytestmark` to skip a whole
class or module. The condition is normally a **boolean**; legacy **condition strings**
(e.g. `skipif("sys.platform == 'win32'", reason=...)`) are still supported but discouraged
— they exist mainly for backward compatibility and can't be shared between modules easily.

## `xfail`: expected failures

`xfail` marks a test you **expect to fail** (an unfixed bug, an unimplemented feature). The
test still runs, but a failure is reported as `XFAIL` (no traceback noise) and an
unexpected pass as `XPASS`, keeping the suite green.

```python
@pytest.mark.xfail
def test_known_bug(): ...
```

Full signature: `xfail(condition=False, *, reason=None, raises=None, run=True, strict=...)`.

```python
# Conditional xfail — needs a reason
@pytest.mark.xfail(sys.platform == "win32", reason="bug in 3rd-party lib on Windows")
def test_a(): ...


# Only count it as an expected failure if it raises a specific exception;
# any other exception is a real failure.
@pytest.mark.xfail(raises=RuntimeError, reason="not handled yet")
def test_b(): ...


# Don't even execute the test body (e.g. it segfaults) — always reported xfailed.
@pytest.mark.xfail(run=False, reason="crashes the interpreter")
def test_c(): ...


# strict: an unexpected PASS fails the suite (catches silently-fixed bugs).
@pytest.mark.xfail(strict=True, reason="must stay broken until #42 lands")
def test_d(): ...
```

- `raises=` accepts a single exception class or a tuple; subclasses match (like `except`).
  It also accepts a `pytest.RaisesGroup` / `pytest.RaisesExc` `(pytest 8.4+)` to match
  exception groups.
- `run=False` reports the test as xfailed **without running** it.
- `strict=True` turns an `XPASS` into a suite **failure**; `strict=False` lets both
  `xfailed` and `xpassed` pass. When `strict=` is omitted, the per-mark default is read
  from the `xfail_strict` config option, which is itself **`False` by default** (this
  default has never changed). Set `xfail_strict = true` to make every `xfail` strict by
  default. That option is also spelled `strict_xfail` `(pytest 9.0+)` — the same setting,
  newer name; use `xfail_strict` if you target pytest < 9.0.
- To xfail a single parametrized case, use `pytest.param(..., marks=pytest.mark.xfail(...))`
  — see [parametrize.md](parametrize.md).
- Run xfail-marked tests as if unmarked with `pytest --runxfail` (debugging); show
  tracebacks for xfailing tests with `pytest --xfail-tb` `(pytest 8.3+)`.

Show the reasons for skipped/xfailed tests in the summary with `-rs` / `-rxX` (see
[cli-usage.md](cli-usage.md) for the full `-r` reporting flags):

```
pytest -rxXs   # report xfailed (x), xpassed (X), and skipped (s) with reasons
```

## Skipping and xfailing at runtime

When the condition can only be known **while the test runs** (not at import/collection
time), call the imperative functions. They work by raising an internal exception, so no
code runs after them.

```python
import pytest


def test_runtime_skip():
    if not feature_available():
        pytest.skip("backend not reachable")  # skip this test now


def test_runtime_xfail():
    if buggy_path_taken():
        pytest.xfail("hits the known #123 bug")  # mark xfail and stop here
```

Skip an **entire module** during collection with `allow_module_level=True` (a plain
`pytest.skip()` at module scope is an error):

```python
import sys
import pytest

if not sys.platform.startswith("win"):
    pytest.skip("Windows-only tests", allow_module_level=True)
```

Skip when an **optional dependency** is missing, using `importorskip` (returns the imported
module, or skips):

```python
docutils = pytest.importorskip("docutils")
np = pytest.importorskip("numpy", minversion="1.24")  # checks module.__version__
```

`importorskip(modname, minversion=None, reason=None, *, exc_type=None)`:

- On modern pytest, **only `ModuleNotFoundError`** (the module is genuinely absent)
  triggers the skip by default. If the import instead raises a plain `ImportError` — e.g.
  a broken optional sub-dependency — it is **not** caught and propagates as a real error
  (a collection error at module level), unless you opt in below. This arrived in two
  steps: `(pytest 8.2+)` pytest began **warning** when an import raised an `ImportError`
  other than `ModuleNotFoundError` (it still skipped); `(pytest 9.1+)` the default
  `exc_type` became `ModuleNotFoundError`, so that `ImportError` now propagates instead of
  being skipped.
- `exc_type=` `(pytest 8.2+)` controls what counts as "skip": pass `exc_type=ImportError`
  to skip (and silence that warning) when the module imports but raises `ImportError`.

## Selecting tests with `-m`

Run only the tests whose marks match a **boolean marker expression**. `-m` supports
`and`, `or`, `not`, and parentheses over marker names:

```
pytest -m slow                      # tests marked @pytest.mark.slow
pytest -m "not slow"                # everything except slow
pytest -m "slow and not serial"     # combine
pytest -m "(slow or webtest) and not flaky"
```

`-m` also matches on a marker's **keyword arguments** `(pytest 8.3+)` — only keyword
matching is supported, and only `int`, (unescaped) `str`, `bool`, and `None` values:

```python
@pytest.mark.device(serial="123")
def test_quick(): ...
```

```
pytest -m "device(serial='123')"   # select by marker kwarg
```

`-m` matches **marker** names; to select by **test name** substring use `-k` instead (see
[cli-usage.md](cli-usage.md)). Both deselect non-matching tests (reported as "deselected").

## Quick reference

| Construct | Purpose | Since |
|---|---|---|
| `@pytest.mark.skip(reason=...)` | Always skip | bedrock |
| `@pytest.mark.skipif(cond, reason=...)` | Skip if condition true | bedrock |
| `@pytest.mark.xfail(reason=...)` | Expect failure | bedrock |
| `@pytest.mark.xfail(raises=Exc, run=False, strict=True)` | Narrowed / non-running / strict xfail | bedrock |
| `pytest.skip(reason)` / `pytest.xfail(reason)` | Skip/xfail at runtime | bedrock |
| `pytest.skip(reason, allow_module_level=True)` | Skip a whole module | bedrock |
| `pytest.importorskip("mod", minversion=...)` | Skip if dependency missing | bedrock |
| `pytest.importorskip(..., exc_type=ImportError)` | Also skip on `ImportError` | pytest 8.2+ |
| `markers = [...]` (ini/toml) | Register custom markers | bedrock |
| `config.addinivalue_line("markers", ...)` | Register marker in a hook | bedrock |
| `pytestmark = ...` | Apply mark to a whole module | bedrock |
| `--strict-markers` / `--strict-config` | Unknown mark / config warning → error | bedrock (flags) |
| `strict_markers` / `strict_config` / `strict_xfail` (ini) | Same, as ini options | pytest 9.0+ |
| `strict = true` | Umbrella enabling all strictness options | pytest 9.0+ |
| `pytest -m "expr"` | Select by marker expression | bedrock |
| `pytest -m "mark(kw=val)"` | Select by marker keyword argument | pytest 8.3+ |
| `pytest --markers` / `pytest --runxfail` | List markers / ignore xfail | bedrock |

## Gotchas

- **Unregistered marks warn (or error under strict).** Register every custom marker in
  config or a `pytest_configure` hook; enable `--strict-markers` / `strict_markers`
  `(pytest 9.0+)` in CI so a typo fails fast.
- **Marks on fixtures do nothing.** `@pytest.mark.skip` above a `@pytest.fixture` is
  silently ignored — mark the test instead.
- **`xfail` strict catches silent fixes.** A bug that gets fixed makes a non-strict xfail
  `XPASS` quietly; `strict=True` (or `strict_xfail`/`strict` `(pytest 9.0+)`) turns that
  into a failure so you remember to remove the mark.
- **`importorskip` no longer hides `ImportError` by default `(pytest 9.1+)`.** Only a
  missing module (`ModuleNotFoundError`) skips; pass `exc_type=ImportError` to restore the
  broader behavior.
- **`pytest.skip()` at module scope errors** unless you pass `allow_module_level=True`.
- **No code runs after `pytest.skip()`/`pytest.xfail()`** — they raise internally. Don't
  rely on cleanup placed after them; use fixtures/`finally`.
- **`skipif` evaluates at collection time.** A condition that depends on runtime state
  belongs in `pytest.skip()` inside the test, not in the marker.

## References

- pytest — *How to mark test functions with attributes*:
  <https://docs.pytest.org/en/stable/how-to/mark.html>
- pytest — *How to use skip and xfail*:
  <https://docs.pytest.org/en/stable/how-to/skipping.html>
- pytest — *Working with custom markers* (`-m`, keyword expressions):
  <https://docs.pytest.org/en/stable/example/markers.html>
- pytest API — marks reference (`skip`, `skipif`, `xfail`, …):
  <https://docs.pytest.org/en/stable/reference/reference.html#marks-ref>
- Related skill files: [parametrize.md](parametrize.md) (per-case marks),
  [fixtures.md](fixtures.md) (`usefixtures`), [cli-usage.md](cli-usage.md) (`-k`, `-r`),
  [configuration.md](configuration.md) (`markers`, `strict_*`, `filterwarnings`).
