# pytest Parametrization

Parametrization runs **one test function many times with different arguments**, so each
input/expected pair becomes its own reported test case (its own pass/fail, its own id)
instead of a loop hidden inside a single test. pytest expands parameters at **collection
time**, before any test runs, so `pytest --collect-only` already shows every generated
case.

Examples are runnable and idiomatic for **pytest 9.x / Python 3.10+**: plain `def` test
functions, bare `assert`, and module-level imports. Inline tags like `(pytest 9.0+)` mark a
minimum version; untagged features are bedrock (stable since pytest 6.x or earlier). This
file covers parametrizing **tests and fixtures**; for general fixture mechanics (scope,
teardown, `request`) see [fixtures.md](fixtures.md), for `skip`/`xfail`/custom markers see
[markers-skip-xfail.md](markers-skip-xfail.md), and for selecting tests on the command line
see [cli-usage.md](cli-usage.md).

> When you want many checks inside **one** test (rather than many separate tests),
> pytest's experimental **subtests** `(pytest 9.0+)` are an alternative to parametrization
> — a failure in one subtest doesn't stop the others.

## Table of contents

- [`@pytest.mark.parametrize` basics](#pytestmarkparametrize-basics)
- [Stacking decorators: the cartesian product](#stacking-decorators-the-cartesian-product)
- [Parametrizing a whole class or module](#parametrizing-a-whole-class-or-module)
- [`pytest.param`: per-case marks and ids](#pytestparam-per-case-marks-and-ids)
- [Custom test ids](#custom-test-ids)
- [Indirect parametrization: send values through a fixture](#indirect-parametrization-send-values-through-a-fixture)
- [Parametrizing fixtures with `params=`](#parametrizing-fixtures-with-params)
- [`pytest_generate_tests`: dynamic / programmatic parametrization](#pytest_generate_tests-dynamic--programmatic-parametrization)
- [Quick reference](#quick-reference)
- [Gotchas](#gotchas)
- [References](#references)

## `@pytest.mark.parametrize` basics

Decorate the test with `@pytest.mark.parametrize(argnames, argvalues)`. The argument
names are a single comma-separated string (or a list/tuple of strings); the values are a
list, one entry per generated test.

```python
import pytest


@pytest.mark.parametrize("test_input,expected", [("3+5", 8), ("2+4", 6), ("6*9", 42)])
def test_eval(test_input, expected):
    assert eval(test_input) == expected
```

This runs `test_eval` three times. The values appear in each test id and in the
traceback, so a failure is reported as a distinct case:

```
test_eval[3+5-8] PASSED
test_eval[2+4-6] PASSED
test_eval[6*9-42] FAILED
```

**Single argument** → `argvalues` is a flat list of values:

```python
@pytest.mark.parametrize("n", [0, 1, 2, 100])
def test_is_int(n):
    assert isinstance(n, int)
```

**Multiple arguments** → each entry is a tuple matching the names, in order:

```python
@pytest.mark.parametrize("a,b,expected", [(1, 2, 3), (10, 20, 30)])
def test_add(a, b, expected):
    assert a + b == expected
```

> Parameter values are passed **as-is** — no copy. If a test mutates a list/dict passed
> as a parameter, the mutation is visible to later cases. Use immutable values or rebuild
> mutable state inside the test.

## Stacking decorators: the cartesian product

Stack multiple `parametrize` decorators to run **every combination** of their values:

```python
@pytest.mark.parametrize("x", [0, 1])
@pytest.mark.parametrize("y", [2, 3])
def test_foo(x, y):
    pass
```

This produces four cases — `x=0/y=2`, `x=1/y=2`, `x=0/y=3`, `x=1/y=3`: the **topmost**
decorator's values vary fastest and the one **closest to the function** varies slowest
(decorators apply bottom-up, so the closest is the first parametrization and each one
above multiplies it). Each stacked decorator must use **different** argument names.

## Parametrizing a whole class or module

Applying `parametrize` to a **class** invokes every test method with each argument set:

```python
@pytest.mark.parametrize("n,expected", [(1, 2), (3, 4)])
class TestClass:
    def test_simple_case(self, n, expected):
        assert n + 1 == expected

    def test_weird_simple_case(self, n, expected):
        assert (n * 1) + 1 == expected
```

To parametrize **every test in a module**, assign the mark to the `pytestmark` global:

```python
import pytest

pytestmark = pytest.mark.parametrize("n,expected", [(1, 2), (3, 4)])
```

(See [markers-skip-xfail.md](markers-skip-xfail.md) for more on applying marks at
function / class / module scope.)

## `pytest.param`: per-case marks and ids

Wrap an individual case in `pytest.param(*values, marks=..., id=...)` to attach a marker
or a custom id to just that case. The most common use is xfailing or skipping one
combination:

```python
import sys
import pytest


@pytest.mark.parametrize(
    "n,expected",
    [
        (1, 2),
        pytest.param(1, 0, marks=pytest.mark.xfail),
        pytest.param(1, 3, marks=pytest.mark.xfail(reason="known bug #123")),
        pytest.param(2, 3, id="two"),
        pytest.param(
            10, 11, marks=pytest.mark.skipif(sys.version_info < (3, 12), reason="py3.12+")
        ),
    ],
)
def test_increment(n, expected):
    assert n + 1 == expected
```

`marks=` takes a single marker or a list of markers. `id=` sets the bracketed test id for
that case. (`pytest.param` cannot carry `usefixtures` — apply that on the test/class.)

## Custom test ids

By default pytest builds an id from the values (`test_eval[3+5-8]`). Override with `ids=`.

**A list of strings**, one per case:

```python
@pytest.mark.parametrize(
    "a,b,expected", [(1, 2, 3), (4, 5, 9)], ids=["small", "bigger"]
)
def test_add(a, b, expected):
    assert a + b == expected
```

**A callable** called once per value; return a string to label that value, or `None` to
fall back to the auto-generated id for it:

```python
from datetime import datetime, timedelta


def idfn(val):
    if isinstance(val, datetime):
        return val.strftime("%Y%m%d")
    return None  # timedelta values keep the default repr


@pytest.mark.parametrize(
    "a,b,expected",
    [(datetime(2001, 12, 12), datetime(2001, 12, 11), timedelta(1))],
    ids=idfn,
)
def test_timedistance(a, b, expected):
    assert a - b == expected
```

**Per-case via `pytest.param(id=...)`** keeps the label next to the data (often the
clearest option):

```python
@pytest.mark.parametrize(
    "a,b",
    [
        pytest.param(datetime(2001, 12, 12), datetime(2001, 12, 11), id="forward"),
        pytest.param(datetime(2001, 12, 11), datetime(2001, 12, 12), id="backward"),
    ],
)
def test_order(a, b):
    assert a != b
```

**Hide a parameter set from the id** with the `pytest.HIDDEN_PARAM` sentinel
`(pytest 8.4+)` — useful for a single "default" case whose values would only clutter the
name. It may be used at most once per parametrize call (ids must stay unique):

```python
@pytest.mark.parametrize("value", [pytest.param("default", id=pytest.HIDDEN_PARAM), "x"])
def test_value(value): ...
# ids: test_value  and  test_value[x]
```

Notes:

- For the auto-generated id, pytest derives a label from each value. Beyond the obvious
  `str`/`int`/`float`/`bool`, it knows how to label `bytes`, `complex`, `re.Pattern`,
  `enum.Enum`, and any object with a `__name__` (classes, functions) `(pytest 7.1+)`;
  other objects fall back to a positional id like `value0`.
- pytest **escapes non-ASCII** characters in generated ids by default. To see Unicode
  as-is, set `disable_test_id_escaping_and_forfeit_all_rights_to_community_support = true`
  in config (use at your own risk).
- Duplicate ids are normally made unique automatically by appending `0`, `1`, … Set
  `strict_parametrization_ids = true` `(pytest 9.0+)` to make pytest **error** on
  non-unique ids instead (catches unintended duplicates); fix by giving explicit `ids=`.

## Indirect parametrization: send values through a fixture

By default a parametrized value is passed straight to the test argument. With
`indirect=True` the value is instead sent to the **fixture** of the same name as
`request.param`, so the fixture can turn it into something richer (or do expensive setup
at test-run time rather than collection time):

```python
import pytest


@pytest.fixture
def fixt(request):
    return request.param * 3


@pytest.mark.parametrize("fixt", ["a", "b"], indirect=True)
def test_indirect(fixt):
    assert len(fixt) == 3  # "aaa", "bbb"
```

Pass a **list of names** to make only some arguments indirect; the rest go directly to
the test:

```python
@pytest.fixture
def x(request):
    return request.param * 3


@pytest.mark.parametrize("x, y", [("a", "b")], indirect=["x"])
def test_mixed(x, y):
    assert x == "aaa"  # routed through the x fixture
    assert y == "b"    # passed directly
```

This is the bridge between `parametrize` and fixtures: the parametrized values feed a
fixture's `request.param`. For how fixtures themselves work, see
[fixtures.md](fixtures.md).

## Parametrizing fixtures with `params=`

A fixture can be parametrized directly by passing `params=` to `@pytest.fixture`. The
fixture (and **every test that uses it**) then runs once per value, which the fixture
reads from `request.param`:

```python
import pytest


@pytest.fixture(params=["sqlite", "postgres"])
def db(request):
    return connect(request.param)  # request.param is "sqlite", then "postgres"


def test_query(db):  # runs twice, once per backend
    assert db.ping()
```

This differs from `parametrize(..., indirect=True)`: here the **fixture owns** the
parameter list, so any test that depends on the fixture is multiplied — ideal for
exercising the same suite against several configurations.

`ids=` works the same as for `parametrize` (a list or a callable), and individual values
can carry marks via `pytest.param`:

```python
@pytest.fixture(params=[0, 1, pytest.param(2, marks=pytest.mark.skip)], ids=["a", "b", "c"])
def value(request):
    return request.param
```

For fixture scope, teardown, and the `request` object, see [fixtures.md](fixtures.md).

## `pytest_generate_tests`: dynamic / programmatic parametrization

When the parameter list isn't known statically — it comes from a CLI option, a config
file, a database, or class attributes — implement the
[`pytest_generate_tests`](plugins-hooks.md) hook. pytest calls it while collecting each
test function and passes a `metafunc` object; call `metafunc.parametrize(...)` (same
signature as the marker: `argnames, argvalues, indirect=False, ids=None, scope=None`).

Drive parametrization from a custom command-line option:

```python
# conftest.py
def pytest_addoption(parser):
    parser.addoption("--stringinput", action="append", default=[])


def pytest_generate_tests(metafunc):
    if "stringinput" in metafunc.fixturenames:
        metafunc.parametrize("stringinput", metafunc.config.getoption("stringinput"))
```

```python
# test_strings.py
def test_valid_string(stringinput):
    assert stringinput.isalpha()
```

```
pytest --stringinput=hello --stringinput=world   # runs test_valid_string twice
```

Useful `metafunc` attributes: `metafunc.fixturenames` (names this test will receive),
`metafunc.config` (the pytest config, e.g. `getoption`), `metafunc.cls` (the class, if
any), and `metafunc.function`/`metafunc.module`. The hook may live in `conftest.py`, a
plugin, **or** directly in a test module/class (unlike most hooks).

Build argument names and values dynamically (a "scenarios" pattern), using `scope=` to
group by parameter instance:

```python
def pytest_generate_tests(metafunc):
    if not hasattr(metafunc.cls, "scenarios"):
        return
    idlist, argvalues = [], []
    for scenario_id, params in metafunc.cls.scenarios:
        idlist.append(scenario_id)
        argvalues.append(list(params.values()))
    argnames = list(metafunc.cls.scenarios[0][1])
    metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")


class TestSample:
    scenarios = [("basic", {"attr": "x"}), ("advanced", {"attr": "y"})]

    def test_demo(self, attr):
        assert isinstance(attr, str)
```

If `argvalues` is **empty**, the test's outcome follows the
[`empty_parameter_set_mark`](configuration.md) config option (default `skip`; also
`xfail` or `fail_at_collect`). Calling `metafunc.parametrize` more than once is allowed
only with **different** argument names.

> `(pytest 9.1+)` Passing a non-`Collection` iterable (a bare generator or iterator) as
> `argvalues` is **deprecated** — pytest needs to iterate it more than once. Wrap it:
> `metafunc.parametrize("n", list(gen()))`.

## Quick reference

| Construct | Purpose | Since |
|---|---|---|
| `@pytest.mark.parametrize("a", [1, 2])` | Single argument, flat value list | bedrock |
| `@pytest.mark.parametrize("a,b", [(1, 2)])` | Multiple arguments, tuples | bedrock |
| Stacked `@parametrize` decorators | Cartesian product of all combinations | bedrock |
| `@pytest.mark.parametrize(..., ids=[...])` | Custom ids (list) | bedrock |
| `@pytest.mark.parametrize(..., ids=fn)` | Custom ids (callable; `None` → auto) | bedrock |
| `pytest.param(*vals, id="...")` | Per-case id | bedrock |
| `pytest.param(*vals, marks=pytest.mark.xfail)` | Per-case marker (skip/xfail/…) | bedrock |
| `pytest.param(..., id=pytest.HIDDEN_PARAM)` | Hide one case from the test id | pytest 8.4+ |
| `@pytest.mark.parametrize(..., indirect=True)` | Route values through same-named fixture | bedrock |
| `@pytest.mark.parametrize(..., indirect=["x"])` | Route only listed args through fixtures | bedrock |
| `@pytest.fixture(params=[...])` + `request.param` | Parametrize a fixture (multiplies dependents) | bedrock |
| `@pytest.mark.parametrize(..., scope="class")` | Override grouping scope of the params | bedrock |
| `pytest_generate_tests(metafunc)` + `metafunc.parametrize(...)` | Dynamic / programmatic cases | bedrock |
| `strict_parametrization_ids = true` | Error (not auto-dedupe) on duplicate ids | pytest 9.0+ |
| `empty_parameter_set_mark` | Outcome when the value list is empty | bedrock |

## Gotchas

- **One name → flat list; many names → tuples.** With a single argument name, pass a
  flat list of values; pytest wraps each one, so even tuple values work as expected:
  `parametrize("x", [(1, 2), (3, 4)])` gives `x == (1, 2)` then `x == (3, 4)`. With
  multiple names, each entry must be a sequence matching the names:
  `parametrize("x,y", [(1, 2)])` → `x=1, y=2`. (A trailing comma — `"x,"` — switches a
  single name to explicit tuple-style, where you must supply 1-tuples like `[(1,), (2,)]`;
  rarely needed.)
- **`request` is reserved.** You cannot name a parametrized argument `request`; pytest
  errors at collection.
- **`indirect=True` needs a fixture.** The argument must have a matching fixture that
  reads `request.param`, otherwise collection fails. Without `indirect`, no fixture is
  involved.
- **Mutable parameter values are shared** across cases (no copy) — see the note above.
- **Duplicate auto-ids are silently de-duped** (`a0`, `a1`, …) unless
  `strict_parametrization_ids` `(pytest 9.0+)` is set. If two cases collapse to the same
  id unexpectedly, give explicit `ids=`.
- **Empty value list ≠ a passing test.** It is skipped by default
  (`empty_parameter_set_mark`); a typo that yields no values can quietly skip coverage.

## References

- pytest — *How to parametrize fixtures and test functions*:
  <https://docs.pytest.org/en/stable/how-to/parametrize.html>
- pytest — *Parametrizing tests* (more examples, indirect, scenarios):
  <https://docs.pytest.org/en/stable/example/parametrize.html>
- pytest API — `Metafunc.parametrize`, `pytest.param`:
  <https://docs.pytest.org/en/stable/reference/reference.html#pytest-metafunc>
- Related skill files: [fixtures.md](fixtures.md) (fixture mechanics),
  [markers-skip-xfail.md](markers-skip-xfail.md) (per-case marks, `skip`/`xfail`),
  [cli-usage.md](cli-usage.md) (`-k`/`-m` selection), [configuration.md](configuration.md)
  (`empty_parameter_set_mark`, `strict_parametrization_ids`).
