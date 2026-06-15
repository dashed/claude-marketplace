# pytest Assertions

pytest's assertion model is **just the plain Python `assert` statement**. There is no
`assertEqual`/`assertTrue` family to memorize — you write `assert <expr>`, and pytest
rewrites your test modules at import time so that when an assert fails it can show you
the *values* that went into the expression, not merely "AssertionError". On top of that
one statement, pytest adds a small set of helpers for the things a bare `assert` can't
express cleanly: `pytest.raises` (expected exceptions), `pytest.warns` /
`pytest.deprecated_call` (expected warnings), `pytest.approx` (float tolerance), and the
imperative outcomes `pytest.fail` / `pytest.skip` / `pytest.xfail`.

Examples are runnable and idiomatic for **pytest 9.x / Python 3.10+**: plain `def` test
functions, bare `assert`, and module-level imports. Inline tags like `(pytest 8.4+)`
mark a minimum version; untagged features are bedrock (stable since pytest 6.x or
earlier). For the **marker** forms `@pytest.mark.skip` / `skipif` / `xfail` (as opposed
to the imperative `pytest.skip()` / `pytest.xfail()` covered here) see
[markers-skip-xfail.md](markers-skip-xfail.md); for the `recwarn` and `capsys` fixtures
see [builtin-fixtures.md](builtin-fixtures.md); for `filterwarnings`, truncation limits,
and `assertion_text_diff_style` config see [configuration.md](configuration.md); for the
`pytest_assertrepr_compare` hook see [plugins-hooks.md](plugins-hooks.md).

## Table of contents

- [The `assert` statement and introspection](#the-assert-statement-and-introspection)
- [Rich comparison output](#rich-comparison-output)
- [Assertion rewriting](#assertion-rewriting)
- [`pytest.raises`: expecting exceptions](#pytestraises-expecting-exceptions)
- [Expecting exception *groups*](#expecting-exception-groups)
- [`pytest.warns` and `pytest.deprecated_call`](#pytestwarns-and-pytestdeprecated_call)
- [`pytest.approx`: floating-point tolerance](#pytestapprox-floating-point-tolerance)
- [Imperative outcomes: `fail` / `skip` / `xfail`](#imperative-outcomes-fail--skip--xfail)
- [Quick reference](#quick-reference)
- [Gotchas](#gotchas)
- [Sources](#sources)

## The `assert` statement and introspection

Use the standard Python `assert`. When it fails, pytest reports the intermediate values:

```python
# content of test_assert.py
def f():
    return 3


def test_function():
    assert f() == 4
```

```pytest
>       assert f() == 4
E       assert 3 == 4
E        +  where 3 = f()
```

pytest shows the values of the most common subexpressions — calls, attributes,
comparisons, and binary/unary operators — so you keep idiomatic Python without losing
introspection. Add a custom message with the standard second operand; it prints
*alongside* (not instead of) the introspection:

```python
assert a % 2 == 0, "value was odd, should be even"
```

Source: `doc/en/how-to/assert.rst` ("Asserting with the assert statement").

## Rich comparison output

For common container/string comparisons pytest produces a context-sensitive diff
instead of a flat repr:

- **long strings** — a character-level context diff
- **long sequences** — the first index that differs
- **dicts / sets** — which entries differ, which are extra on each side

```pytest
>       assert set1 == set2
E       AssertionError: assert {'0', '1', '3', '8'} == {'0', '3', '5', '8'}
E         Extra items in the left set:
E         '1'
E         Extra items in the right set:
E         '5'
E         Use -v to get more diff
```

In string diffs, `-` lines come from the **left** operand of `assert left == right` and
`+` lines from the **right**. Verbosity changes how much is shown: by default long
values are truncated; `-v` shows fuller diffs and `-vv` disables truncation entirely
(see [cli-usage.md](cli-usage.md) for the flags, and `assertion_text_diff_style` in
[configuration.md](configuration.md) to switch between inline `ndiff` and `block` style).

You can teach pytest how to compare your own types by implementing the
`pytest_assertrepr_compare` hook in a `conftest.py` — see
[plugins-hooks.md](plugins-hooks.md).

Source: `doc/en/how-to/assert.rst` ("Making use of context-sensitive comparisons",
"Defining your own explanation for failed assertions"); `how-to/output.rst`
("Verbosity").

## Assertion rewriting

pytest gives `assert` its introspection by **rewriting assert statements at import
time**. Crucially, it only rewrites modules it collects as **test modules**. Asserts in
*supporting* modules — shared helpers, assertion libraries imported by your tests — are
**not** rewritten, so a failing helper assert shows only `AssertionError` with no values.

To opt a non-test module into rewriting, register it **before it is imported** with
`pytest.register_assert_rewrite(*module_names)`. The natural place is the root
`conftest.py`, or a plugin package's `__init__.py`:

```python
# conftest.py (or your plugin package's __init__.py)
import pytest

pytest.register_assert_rewrite("mylib.testing.helpers")
```

This is the standard fix for a pytest **plugin shipped as a package**: only the module
registered via the `pytest11` entry point is rewritten automatically, so a separate
`helpers.py` with asserts must be registered explicitly (and before anything imports it).

**Disabling rewriting** (rarely needed):

| Goal | How |
|---|---|
| Disable for one module | put the string `PYTEST_DONT_REWRITE` in its docstring |
| Disable for the whole run | run with `--assert=plain` (see [cli-usage.md](cli-usage.md)) |
| Stop caching rewritten `.pyc` | `import sys; sys.dont_write_bytecode = True` at the top of `conftest.py` |

Rewritten modules are cached to `.pyc` on disk; caching is silently skipped on a
read-only filesystem or inside a zipfile (you still get introspection, just no cache).

Source: `doc/en/how-to/assert.rst` ("Assertion introspection details", "Disabling assert
rewriting"); `src/_pytest/assertion/__init__.py` (`register_assert_rewrite`);
`how-to/writing_plugins.rst` ("Assertion rewriting").

## `pytest.raises`: expecting exceptions

Use `pytest.raises` as a context manager to assert that a block raises a given exception
type **or any subclass** (matching `except` semantics):

```python
import pytest


def test_zero_division():
    with pytest.raises(ZeroDivisionError):
        1 / 0
```

**Inspect the exception** via the `ExceptionInfo` object bound with `as`. Its main
attributes are `.type`, `.value` (the exception instance), and `.traceback`:

```python
def test_recursion_depth():
    with pytest.raises(RuntimeError) as excinfo:
        ...
    assert "maximum recursion" in str(excinfo.value)
```

**`match=`** asserts a regex against the string form of the exception (via `re.search`,
so it matches a *substring* unless you anchor it). It also matches against
[PEP 678](https://peps.python.org/pep-0678/) `__notes__` *(pytest 8.0+)*:

```python
def test_match():
    with pytest.raises(ValueError, match=r"must be \d+ or None"):
        raise ValueError("value must be 42 or None")
```

To match a literal string containing regex metacharacters (`(`, `.`, …), escape it first
with `re.escape(...)`.

**Multiple acceptable types** — pass a tuple:

```python
with pytest.raises((ValueError, TypeError)):
    ...
```

**`check=`** *(pytest 8.4+)* takes a callable run with the exception after the type and
`match` pass; it must return `True` for the match to succeed:

```python
import errno

with pytest.raises(OSError, check=lambda e: e.errno == errno.EACCES):
    raise OSError(errno.EACCES, "no permission")
```

**Match/check-only form** *(pytest 8.4+)* — the exception type is now optional, so you
can verify *only* the message or a predicate:

```python
with pytest.raises(match="must be positive"):
    raise ValueError("must be positive")
```

**Legacy callable form** — predating the `with` statement, you may pass a function plus
its arguments; rarely used today, the context-manager form is preferred:

```python
pytest.raises(ValueError, int, "not a number")  # calls int("not a number")
```

> **Exact type, not subclass.** `pytest.raises(RuntimeError)` also catches a
> `NotImplementedError` (a subclass). To require an exact type, assert on it:
> `assert excinfo.type is RuntimeError`.

> **Final line in scope.** The expected exception must be the **last** statement that
> runs inside the `with` block — code after the raising line will not execute. Inspect
> `excinfo` *after* the `with` block, not inside it.

Source: `doc/en/how-to/assert.rst` ("Assertions about expected exceptions");
`src/_pytest/raises.py` (`raises`, `check`/match-only overloads, `versionadded:: 8.4`).

## Expecting exception *groups*

For an `ExceptionGroup` / `BaseExceptionGroup` (PEP 654), prefer **`pytest.RaisesGroup`**
*(pytest 8.4+)*, which checks the group's *structure* — it requires exactly the expected
exceptions and no others:

```python
def test_group():
    with pytest.RaisesGroup(ValueError):
        raise ExceptionGroup("msg", [ValueError("boom")])

    with pytest.RaisesGroup(ValueError, TypeError):
        raise ExceptionGroup("msg", [ValueError("a"), TypeError("b")])
```

`RaisesGroup` accepts `match=` (against the group message) and `check=` (a callable given
the whole group). It is **strict about nesting** by default; relax with `flatten_subgroups=True`
(collapse nested groups) and/or `allow_unwrapped=True` (accept a bare, ungrouped
exception). Specify a nested group by passing another `RaisesGroup`, and constrain a
contained exception with **`pytest.RaisesExc`** *(pytest 8.4+)*:

```python
with pytest.RaisesGroup(pytest.RaisesExc(ValueError, match="foo")):
    raise ExceptionGroup("", [ValueError("foo")])

with pytest.RaisesGroup(pytest.RaisesGroup(ValueError)):  # nested structure
    raise ExceptionGroup("", [ExceptionGroup("", [ValueError()])])
```

Both expose a standalone **`.matches(exc)`** method (with a `.fail_reason` when it
fails) for checking an exception you already hold, e.g. a `__cause__` or `__context__`:

```python
r = pytest.RaisesExc(ValueError)
assert r.matches(some_exc), r.fail_reason
```

`RaisesGroup` also works as the `raises=` argument of `@pytest.mark.xfail` (see
[markers-skip-xfail.md](markers-skip-xfail.md)).

**Legacy approach** *(pytest 8.0+)* — `pytest.raises(ExceptionGroup)` plus
`excinfo.group_contains(ExcType, match=..., depth=...)` searches the (possibly nested)
group for a matching exception:

```python
with pytest.raises(ExceptionGroup) as excinfo:
    raise ExceptionGroup("msg", [RuntimeError("123")])
assert excinfo.group_contains(RuntimeError, match=r"123")
assert not excinfo.group_contains(TypeError)
```

> **`group_contains` cannot prove a group is "clean".** It only checks *presence*, so a
> group carrying an *extra* unexpected exception still passes. When you need to assert
> the group contains exactly what you expect and nothing more, use `RaisesGroup`.

Source: `doc/en/how-to/assert.rst` ("Assertions about expected exception groups",
"ExceptionInfo.group_contains()"); `src/_pytest/raises.py` (`RaisesExc`, `RaisesGroup`,
`versionadded:: 8.4`).

## `pytest.warns` and `pytest.deprecated_call`

`pytest.warns` is to warnings what `pytest.raises` is to exceptions: the block must emit
at least one warning of the given class. It also supports `match=` (regex against the
warning message):

```python
import warnings

import pytest


def test_warning():
    with pytest.warns(UserWarning, match="must be 0 or None"):
        warnings.warn("value must be 0 or None", UserWarning)
```

Pass a **tuple** to accept any of several categories: `pytest.warns((RuntimeWarning,
UserWarning))`. **Record** emitted warnings by binding the context manager and querying
the resulting list of `warnings.WarningMessage` objects; with **no argument** it defaults
to the generic `Warning` and simply records everything:

```python
with pytest.warns() as record:                 # no arg → record any warning
    warnings.warn("first", UserWarning)
    warnings.warn("second", RuntimeWarning)

assert len(record) == 2
assert str(record[0].message) == "first"
```

`pytest.deprecated_call()` is a focused alias that expects a `DeprecationWarning`,
`PendingDeprecationWarning`, **or** `FutureWarning`:

```python
def test_deprecated():
    with pytest.deprecated_call():
        my_old_api()
```

Notes:

- Since pytest 8.0, warnings that don't match are **re-emitted** when the context
  closes, so they still surface in the run's warnings summary.
- For recording across an entire test function, use the `recwarn` fixture instead — see
  [builtin-fixtures.md](builtin-fixtures.md).
- To turn warnings into errors or filter them, use `-W` / the `filterwarnings` config —
  see [cli-usage.md](cli-usage.md) and [configuration.md](configuration.md).

Source: `doc/en/how-to/capture-warnings.rst` ("Asserting warnings", "Recording
warnings", "Ensuring code triggers a deprecation warning"); `src/_pytest/recwarn.py`
(`warns`, `deprecated_call`).

## `pytest.approx`: floating-point tolerance

Comparing floats directly is unreliable (`0.1 + 0.2 != 0.3`). Wrap the expected value in
`pytest.approx` to compare within a tolerance:

```python
def test_floats():
    assert (0.1 + 0.2) == pytest.approx(0.3)
```

`approx` works on **scalars, ordered sequences, dicts (by value), NumPy arrays, and
`Decimal`**:

```python
assert [0.1 + 0.2, 0.2 + 0.4] == pytest.approx([0.3, 0.6])
assert {"a": 0.1 + 0.2} == pytest.approx({"a": 0.3})
```

**Tolerances** — by default a value is "equal" within a **relative** tolerance of `1e-6`
*or* an **absolute** tolerance of `1e-12` (the absolute floor handles comparisons against
`0.0`). Override either:

```python
assert 1.0001 == pytest.approx(1, rel=1e-3)   # relative
assert 1.0001 == pytest.approx(1, abs=1e-3)   # absolute
```

- If you pass **`abs` only**, the relative tolerance is ignored entirely.
- If you pass **both**, the values match when **either** tolerance is satisfied.
- `nan_ok=True` makes `NaN` compare equal to `NaN` (off by default).
- `datetime` / `timedelta` values can be compared with an `abs=timedelta(...)` tolerance
  *(pytest 9.1+)* (an explicit `timedelta` tolerance is required; `rel` is unsupported for
  `datetime`).

> **Pitfalls:** `approx` supports only **ordered** sequences — a `set` raises
> `TypeError`. Ordering comparisons (`>`, `>=`, `<`, `<=`) against an `approx` also raise
> `TypeError` — it only defines `==`/`!=`. And `approx` treats booleans as distinct from
> numbers, so `1 == approx(True)` is `False`.

Source: `doc/en/how-to/assert.rst` ("Assertions about approximate equality");
`src/_pytest/python_api.py` (`approx`, tolerance defaults); `doc/en/changelog.rst` #8395
(datetime/timedelta support, pytest 9.1.0).

## Imperative outcomes: `fail` / `skip` / `xfail`

These functions end the current test immediately by raising; call them from inside a
test (or fixture). They are the **imperative** counterparts to the `@pytest.mark.*`
decorators — reach for a marker when the condition is known at collection time, and for
these functions when you only discover the situation at runtime (see
[markers-skip-xfail.md](markers-skip-xfail.md)).

```python
import pytest

# Force a failure with a message:
pytest.fail("invariant violated")
pytest.fail("custom report", pytrace=False)   # suppress the Python traceback

# Skip the rest of this test at runtime:
pytest.skip("backend not reachable")

# Skip the WHOLE module during collection (e.g. optional dependency missing):
pytest.skip("needs feature X", allow_module_level=True)

# Mark the running test as an expected failure and stop here:
pytest.xfail("known bug #123")
```

Behavioral notes:

- `pytest.fail(reason, pytrace=False)` prints `reason` as the entire failure (no
  traceback) — handy for assembling your own message.
- `pytest.skip(reason)` aborts only the current test; `allow_module_level=True` lets you
  call it at module top level to skip the entire file.
- `pytest.xfail(reason)` records an expected failure and runs no further code in the test.
- Related helpers: `pytest.importorskip("mod", minversion="1.2")` imports a module or
  skips if it's absent (its default skips on `ModuleNotFoundError` as of pytest 9.1; pass
  `exc_type=ImportError` to also skip on import errors — the `exc_type` param is pytest
  8.2+), and `pytest.exit("stop now", returncode=...)` ends the whole session.

> Don't `return True`/`False` from a test to signal pass/fail — pytest ignores test
> return values and emits a `PytestReturnNotNoneWarning` *(pytest 7.2+)*. Use `assert`.

Source: `doc/en/how-to/assert.rst` ("Returning non-None value in test functions");
`src/_pytest/outcomes.py` (`fail`, `skip`, `xfail`, `exit`, `importorskip`, incl.
`exc_type` `versionadded:: 8.2` and the 9.1 default change).

## Quick reference

| Goal | How |
|---|---|
| Assert a condition | `assert expr` (+ optional `, "message"`) |
| Rewrite asserts in a helper module | `pytest.register_assert_rewrite("pkg.helpers")` before import |
| Turn off rewriting | `--assert=plain`, or `PYTEST_DONT_REWRITE` in a module docstring |
| Expect an exception | `with pytest.raises(ValueError):` |
| Match its message | `pytest.raises(ValueError, match=r"regex")` |
| Inspect it | `with pytest.raises(E) as exc: ...` → `exc.type`/`exc.value`/`exc.traceback` |
| Accept several types | `pytest.raises((A, B))` |
| Custom predicate | `pytest.raises(E, check=lambda e: ...)` *(8.4+)* |
| Match only (no type) | `pytest.raises(match="...")` *(8.4+)* |
| Expect an exception group | `pytest.RaisesGroup(ValueError, ...)` *(8.4+)* |
| Constrain a grouped exc | `pytest.RaisesExc(ValueError, match="...")` *(8.4+)* |
| Find an exc in a group | `pytest.raises(ExceptionGroup)` → `exc.group_contains(E, match=, depth=)` |
| Expect a warning | `with pytest.warns(UserWarning, match="..."):` |
| Record warnings | `with pytest.warns() as record:` → list of `WarningMessage` |
| Expect a deprecation | `with pytest.deprecated_call():` |
| Float tolerance | `value == pytest.approx(expected, rel=, abs=)` |
| Fail now | `pytest.fail("msg", pytrace=False)` |
| Skip now / whole module | `pytest.skip("msg")` / `pytest.skip("msg", allow_module_level=True)` |
| xfail now | `pytest.xfail("msg")` |
| Skip if import missing | `pytest.importorskip("numpy", minversion="1.20")` |

## Gotchas

- **Helper-module asserts aren't introspected.** Only collected test modules are
  rewritten; register others with `register_assert_rewrite` *before* import.
- **`raises` matches subclasses.** Avoid `pytest.raises(Exception)` — it hides bugs.
  Assert `excinfo.type is Exact` when you need an exact type.
- **`match` is a `re.search`, not a full match.** It matches a substring; anchor with
  `^`/`$` if you mean the whole message, and `re.escape` literal text. An empty
  `match=""` matches *anything* and now warns *(pytest 8.4+)* — use `match="^$"` to assert
  a genuinely empty message.
- **Code after the raising line in a `with pytest.raises` block never runs.** Put
  assertions on `excinfo` *after* the block.
- **`group_contains` can't prove absence of *other* exceptions** — use `RaisesGroup` for
  exact group structure.
- **`approx` only does `==`/`!=` and only ordered containers.** Ordering operators and
  `set`s raise `TypeError`; booleans aren't equal to `0`/`1`.
- **`abs`-only `approx` ignores the relative tolerance** — pass both if you want either
  to qualify.
- **Don't `return` a bool from a test.** pytest ignores it and warns; assert instead.

## Sources

- `doc/en/how-to/assert.rst` — `assert` introspection, custom messages, rich
  comparisons, `pytest_assertrepr_compare`, `pytest.raises` (match, ExceptionInfo,
  subclass behavior, tuple, legacy form), exception groups (`RaisesGroup`/`RaisesExc`,
  `group_contains`), `approx`, return-not-None.
- `doc/en/how-to/capture-warnings.rst` — `pytest.warns`, recording, `deprecated_call`,
  re-emission of unmatched warnings.
- `src/_pytest/python_api.py` — `approx` tolerances, supported types; datetime/timedelta
  support is pytest 9.1.0 (`doc/en/changelog.rst` #8395).
- `src/_pytest/raises.py` — `raises` signature, `check`/match-only forms, `RaisesExc`,
  `RaisesGroup` (`versionadded:: 8.4`).
- `src/_pytest/recwarn.py` — `warns`, `deprecated_call`, `WarningsRecorder`.
- `src/_pytest/outcomes.py` — `fail`, `skip`, `xfail`, `exit`, `importorskip`.
- `src/_pytest/assertion/__init__.py` — `register_assert_rewrite`;
  `how-to/writing_plugins.rst` for the plugin-packaging rationale.
