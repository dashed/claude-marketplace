# pytest Fixtures

Fixtures are pytest's dependency-injection system for **test setup, teardown, and
shared state**. A test (or another fixture) declares a dependency simply by naming a
fixture as a parameter; pytest finds the matching fixture, runs it, and passes the
result in. This replaces `setUp`/`tearDown` methods with small, composable,
explicitly-requested functions.

Examples are runnable and idiomatic for **pytest 9.x / Python 3.10+**: plain `def`
test functions, bare `assert`, module-level imports, and `tmp_path` (not the legacy
`tmpdir`). Inline tags like `(pytest 8.4+)` mark a minimum version; untagged features
are bedrock (stable since pytest 6.x or earlier). For the built-in fixtures pytest
ships (`tmp_path`, `monkeypatch`, `capsys`, `caplog`, …) see
[builtin-fixtures.md](builtin-fixtures.md); for `@pytest.mark.parametrize` on tests
see [parametrize.md](parametrize.md).

## Table of contents

- [Defining and requesting fixtures](#defining-and-requesting-fixtures)
- [The `@pytest.fixture` decorator](#the-pytestfixture-decorator)
- [Scope: how long a fixture lives](#scope-how-long-a-fixture-lives)
- [Teardown / finalization](#teardown--finalization)
- [Autouse fixtures](#autouse-fixtures)
- [The `request` object](#the-request-object)
- [Parametrizing fixtures](#parametrizing-fixtures)
- [Factory as fixture](#factory-as-fixture)
- [Sharing fixtures: `conftest.py` and availability](#sharing-fixtures-conftestpy-and-availability)
- [Overriding fixtures](#overriding-fixtures)
- [`usefixtures`: requiring a fixture without an argument](#usefixtures-requiring-a-fixture-without-an-argument)
- [Fixture instantiation order](#fixture-instantiation-order)
- [Dynamic fixture selection: `getfixturevalue`](#dynamic-fixture-selection-getfixturevalue)
- [Quick reference](#quick-reference)
- [Gotchas](#gotchas)

## Defining and requesting fixtures

Decorate a function with `@pytest.fixture`. Any test whose signature names that
function receives its return value:

```python
import pytest


@pytest.fixture
def fruit_bowl():
    return ["apple", "banana"]


def test_fruit_salad(fruit_bowl):  # "requests" the fruit_bowl fixture
    assert "apple" in fruit_bowl
```

**Fixtures can request other fixtures.** The same rules that apply to tests apply to
fixtures — declare a dependency by naming it as a parameter. pytest resolves the whole
dependency graph:

```python
@pytest.fixture
def first_entry():
    return "a"


@pytest.fixture
def order(first_entry):  # depends on first_entry
    return [first_entry]


def test_string(order):
    order.append("b")
    assert order == ["a", "b"]
```

**Fixtures are reusable and isolated.** Two tests requesting the same
(function-scoped) fixture each get a freshly-executed result, so one test cannot
pollute another.

**Within a single test, a fixture's result is cached.** If a test and several of its
fixtures all request `order`, the `order` fixture runs **once** for that test and they
all share the same object (including side effects):

```python
@pytest.fixture
def order():
    return []


@pytest.fixture
def append_first(order):
    order.append("a")  # mutates the shared list


def test_append(append_first, order):
    # append_first and the test see the SAME list object
    assert order == ["a"]
```

Source: `doc/en/how-to/fixtures.rst` ("Requesting fixtures", "Fixtures are reusable",
"return values are cached").

## The `@pytest.fixture` decorator

```python
@pytest.fixture(
    scope="function",   # function | class | module | package | session (or a callable)
    params=None,        # parametrize the fixture; values exposed as request.param
    autouse=False,      # run for every test in scope without being requested
    ids=None,           # human-readable IDs for params (list or callable)
    name=None,          # register under a different name than the function
)
def my_fixture(): ...
```

Use `name=` when the fixture's natural name collides with the value it returns (a
common clash, since requesting a fixture shadows it in the test's namespace):

```python
@pytest.fixture(name="cart")
def cart_fixture():
    return Cart()


def test_cart(cart):  # request by the registered name
    assert cart.is_empty()
```

Signature confirmed in `src/_pytest/fixtures.py` (`def fixture(...)`).

## Scope: how long a fixture lives

A fixture is created the first time it's requested and destroyed according to its
`scope`. Broadening the scope shares one instance across more tests — useful for
expensive setup (network connections, containers, large files):

| Scope | Created / destroyed | Use for |
|---|---|---|
| `function` (default) | once per test function | cheap, isolated state |
| `class` | once per test class | setup shared by methods of a class |
| `module` | once per `.py` test module | a connection reused across a file |
| `package` | once per package (incl. sub-packages) | per-package shared resource |
| `session` | once per whole test run | the most expensive shared setup |

```python
import smtplib

import pytest


@pytest.fixture(scope="module")
def smtp_connection():
    # created once per module, reused by every test in it
    return smtplib.SMTP("smtp.example.com", 587, timeout=5)
```

A higher-scoped fixture may **not** depend on a narrower-scoped one (a session fixture
cannot use a function fixture meaningfully); the reverse is fine.

> **Caching caveat:** pytest caches only one instance of a fixture per scope *at a
> time*. A parametrized fixture is therefore invoked once per parameter value within
> its scope.

### Dynamic scope

`scope` may be a **callable** that returns a scope string. It's invoked once at fixture
definition with `fixture_name` and `config`, letting a CLI flag decide the scope:

```python
def determine_scope(fixture_name, config):
    if config.getoption("--keep-containers", None):
        return "session"
    return "function"


@pytest.fixture(scope=determine_scope)
def docker_container():
    yield spawn_container()
```

Source: `doc/en/how-to/fixtures.rst` ("Fixture scopes", "Dynamic scope") and
`reference/fixtures.rst`. (Dynamic scope is bedrock — long-standing, untagged.)

## Teardown / finalization

### `yield` fixtures (recommended)

Swap `return` for `yield`. Code **before** the `yield` is setup; code **after** runs as
teardown once the fixture's scope ends. The yielded value is what the test receives:

```python
import pytest


@pytest.fixture
def sending_user(mail_admin):
    user = mail_admin.create_user()
    yield user                      # value handed to the test
    mail_admin.delete_user(user)    # teardown, runs after the test


def test_email(sending_user):
    assert sending_user.inbox == []
```

If a `yield` fixture raises **before** yielding, its own teardown does not run, but any
fixtures that already completed setup are still torn down.

> The legacy `@pytest.yield_fixture` decorator is long deprecated — use
> `@pytest.fixture` with `yield`, as above.

### `addfinalizer`

Alternatively, request the `request` object and register teardown callables with
`request.addfinalizer`. More verbose than `yield`, but lets you register multiple
finalizers conditionally:

```python
@pytest.fixture
def receiving_user(mail_admin, request):
    user = mail_admin.create_user()
    request.addfinalizer(lambda: mail_admin.delete_user(user))
    return user
```

Only register a finalizer *after* the state it cleans up actually exists — pytest runs a
registered finalizer even if the fixture later raises.

### Finalizer order

Teardown runs in **first-in, last-out** order — the reverse of setup. For `yield`
fixtures the right-most/last-requested fixture tears down first. For `addfinalizer`,
the last-registered finalizer runs first (`yield` is implemented on top of
`addfinalizer`).

### Safe teardown structure

Keep each fixture to **one state-changing action**, bundled with its own teardown.
Splitting independent setup steps into separate fixtures ensures that if one fails, the
others still clean up — pytest tears down every fixture that completed setup, regardless
of which order they ran in:

```python
@pytest.fixture
def user(admin_client):
    u = admin_client.create_user()
    yield u
    admin_client.delete_user(u)


@pytest.fixture
def driver():
    d = Chrome()
    yield d
    d.quit()  # runs even if `user` setup failed
```

Source: `doc/en/how-to/fixtures.rst` ("Teardown/Cleanup", "Note on finalizer order",
"Safe fixture structure").

## Autouse fixtures

`autouse=True` makes a fixture run for **every test in its scope** without being
requested. Tests can still name it, but don't have to:

```python
@pytest.fixture(autouse=True)
def reset_singleton():
    Registry.clear()
    yield
    Registry.clear()
```

Autouse fixtures are a good fit for the "act" step shared across many tests, or for
global cleanup. Use sparingly: an autouse fixture affects every test that can *reach*
it (same scope or narrower), even ones that don't want it. A fixture an autouse fixture
requests effectively becomes autouse for those same tests.

## The `request` object

Request the special `request` fixture to introspect the test that triggered the
fixture. `request` is a `FixtureRequest`.

**Attributes** (source: `src/_pytest/fixtures.py`, `class FixtureRequest`):

| Attribute | Meaning |
|---|---|
| `request.param` | current value of a parametrized fixture (only when parametrized) |
| `request.scope` | `"function"`/`"class"`/`"module"`/`"package"`/`"session"` |
| `request.fixturenames` | names of all active fixtures for this request |
| `request.node` | underlying collection node (the test item/scope) |
| `request.config` | the `pytest.Config` object |
| `request.function` | test function object (function scope only) |
| `request.cls` | class of the test (class/function scope; may be `None`) |
| `request.instance` | test instance (function scope; may be `None`) |
| `request.module` | module object the test was collected from |
| `request.path` | `pathlib.Path` of the test file |
| `request.keywords` | markers/keywords for the node |
| `request.session` | the pytest `Session` |

**Methods:** `request.addfinalizer(fn)`, `request.applymarker(marker)`,
`request.getfixturevalue(name)` (see [below](#dynamic-fixture-selection-getfixturevalue)),
`request.raiseerror(msg)`.

### Introspecting the requesting module

```python
@pytest.fixture(scope="module")
def smtp_connection(request):
    server = getattr(request.module, "smtpserver", "smtp.example.com")
    conn = smtplib.SMTP(server, 587, timeout=5)
    yield conn
    conn.close()
```

### Reading markers from a fixture

A fixture can pull data off a marker applied to the test via
`request.node.get_closest_marker`:

```python
@pytest.fixture
def fixt(request):
    marker = request.node.get_closest_marker("fixt_data")
    return marker.args[0] if marker else None


@pytest.mark.fixt_data(42)
def test_fixt(fixt):
    assert fixt == 42
```

Source: `doc/en/how-to/fixtures.rst` ("Fixtures can introspect the requesting test
context", "Using markers to pass data to fixtures").

## Parametrizing fixtures

Pass `params=` to run the fixture — and every test depending on it — once per value.
The fixture reads the current value from `request.param`:

```python
import pytest


@pytest.fixture(params=["sqlite", "postgres"])
def database(request):
    db = connect(request.param)
    yield db
    db.close()


def test_query(database):  # runs twice: [sqlite] and [postgres]
    assert database.ping()
```

pytest builds a test ID per value (e.g. `test_query[sqlite]`), usable with `-k` and
shown by `--collect-only`. Customize IDs with `ids=` — a list of strings, or a callable
returning a string (return `None` to fall back to the auto-generated ID):

```python
@pytest.fixture(params=[0, 1], ids=["spam", "ham"])
def a(request):
    return request.param
```

Attach marks to individual parameter values with `pytest.param`:

```python
@pytest.fixture(params=[0, 1, pytest.param(2, marks=pytest.mark.skip)])
def data_set(request):
    return request.param
```

pytest **groups tests by fixture instance** to minimize active resources: all tests
using parameter value A run (and A is finalized) before value B is set up. This eases
testing code with global state.

> This covers parametrization *of fixtures*. For `@pytest.mark.parametrize` on test
> functions, see [parametrize.md](parametrize.md).

Source: `doc/en/how-to/fixtures.rst` ("Parametrizing fixtures", "Using marks with
parametrized fixtures", "Automatic grouping of tests by fixture instances").

## Factory as fixture

When a test needs the fixture's product *multiple times* or with *varying arguments*,
return a **function** instead of a value. The fixture can also track and clean up
everything the factory created:

```python
@pytest.fixture
def make_customer_record():
    created = []

    def _make(name):
        record = models.Customer(name=name, orders=[])
        created.append(record)
        return record

    yield _make

    for record in created:
        record.destroy()


def test_customers(make_customer_record):
    a = make_customer_record("Lisa")
    b = make_customer_record("Mike")
    assert a.name != b.name
```

Source: `doc/en/how-to/fixtures.rst` ("Factories as fixtures").

## Sharing fixtures: `conftest.py` and availability

Put a fixture in a `conftest.py` file and **every test in that directory and below** can
request it — no import needed; pytest discovers it automatically. Nested directories can
each have their own `conftest.py`, layering fixtures additively.

**Availability follows the test's location.** A test can search *upward* (its module,
then parent `conftest.py` files, then plugins) but never *downward* into a sibling or
child scope. A fixture defined inside a class is visible only to that class's tests; one
defined at module level is visible to the whole module.

```
tests/
    conftest.py          # fixtures here are available to everything under tests/
    test_top.py
    subdir/
        conftest.py      # adds fixtures only for tests under subdir/
        test_sub.py
```

**Order of search:** module → enclosing `conftest.py` files (innermost first) →
installed plugins (searched **last**). The first match wins, which is what makes
[overriding](#overriding-fixtures) work.

**Using fixtures from another package:** projects that ship pytest plugins via entry
points expose their fixtures on install. For a plain module that isn't a registered
plugin, register it from your top-level `conftest.py`:

```python
# conftest.py
pytest_plugins = "mylibrary.fixtures"
```

Avoid *importing* fixtures across modules — that re-registers them as defined in the
importing module and can cause duplicates. Prefer `conftest.py` or `pytest_plugins`.

Source: `doc/en/reference/fixtures.rst` ("Fixture availability", "conftest.py: sharing
fixtures", "Fixtures from third-party plugins") and `how-to/fixtures.rst` ("Using
fixtures from other projects").

## Overriding fixtures

A fixture can be redefined at a more specific level to augment or replace it. The
overriding fixture can **request the same name** to build on the original ("super"):

**Directory (`conftest.py`) level** — `tests/subdir/conftest.py` overrides
`tests/conftest.py`:

```python
# tests/conftest.py
@pytest.fixture
def username():
    return "username"


# tests/subdir/conftest.py
@pytest.fixture
def username(username):  # receives the parent fixture's value
    return "overridden-" + username
```

**Module level** — define a fixture of the same name in the test module.

**Via direct parametrization** — a test parameter overrides a fixture value, even one
the test doesn't name directly:

```python
@pytest.mark.parametrize("username", ["directly-overridden-username"])
def test_username(username):
    assert username == "directly-overridden-username"
```

You can also override a parametrized fixture with a non-parametrized one (and vice
versa) at the module or directory level.

Source: `doc/en/how-to/fixtures.rst` ("Overriding fixtures on various levels").

## `usefixtures`: requiring a fixture without an argument

When a test needs a fixture's *side effect* but not its return value, apply it with the
`usefixtures` marker instead of adding a parameter:

```python
import os

import pytest


@pytest.fixture
def cleandir():
    with tempfile.TemporaryDirectory() as newpath:
        old = os.getcwd()
        os.chdir(newpath)
        yield
        os.chdir(old)


@pytest.mark.usefixtures("cleandir")
class TestInTmpDir:
    def test_cwd_empty(self):
        assert os.listdir(os.getcwd()) == []
```

Specify several at once: `@pytest.mark.usefixtures("a", "b")`. Apply to a whole module
with the module-global `pytestmark = pytest.mark.usefixtures("cleandir")`, or to the
whole project via the `usefixtures` config option.

> **Warning:** `@pytest.mark.usefixtures` has **no effect on a fixture function** — it
> only works on tests/classes/modules. To make one fixture use another, request it as
> an argument. More broadly, applying *any* marker to a fixture function is an **error
> (pytest 9.0+)** — it only emitted a warning in 8.0–8.x.

Source: `doc/en/how-to/fixtures.rst` ("Use fixtures in classes and modules with
usefixtures").

## Fixture instantiation order

pytest orders fixtures by three factors, in this priority:

1. **Scope** — higher-scoped (session) fixtures run before narrower (function) ones.
2. **Dependencies** — a fixture runs after the fixtures it requests.
3. **Autouse** — autouse fixtures run before non-autouse fixtures *of the same scope*.

Names, definition order, and request order do **not** determine execution order beyond
coincidence. If order matters and isn't pinned by a dependency, make it explicit by
having one fixture request the other (even if it ignores the result). Inspect the
planned order with `pytest --setup-plan`.

Source: `doc/en/reference/fixtures.rst` ("Fixture instantiation order", "Autouse
fixtures are executed first within their scope").

## Dynamic fixture selection: `getfixturevalue`

When you can only decide *which* fixture to use at runtime, call
`request.getfixturevalue("name")` to resolve a fixture by name on demand:

```python
@pytest.fixture
def storage_backend(request):
    name = "redis_backend" if request.config.getoption("--redis") else "memory_backend"
    return request.getfixturevalue(name)
```

Declaring fixtures as parameters is preferred where possible (the dependency graph is
then static and visible). Use `getfixturevalue` during setup or the test body; avoid it
during teardown.

> **(pytest 9.1+)** Calling `request.getfixturevalue()` *during teardown* to request a
> fixture that wasn't already active is **deprecated** — request it before the fixture
> yields. (Source: `src/_pytest/fixtures.py`, `getfixturevalue` `versionchanged:: 9.1`.)

## Quick reference

| Task | How |
|---|---|
| Define a fixture | `@pytest.fixture` on a function |
| Request it | name it as a test/fixture parameter |
| Return vs teardown | `return value` / `yield value` then teardown code |
| Register extra teardown | `request.addfinalizer(fn)` |
| Share an instance | `@pytest.fixture(scope="module"/"session"/…)` |
| Scope decided at runtime | `scope=callable(fixture_name, config)` |
| Run for every test in scope | `@pytest.fixture(autouse=True)` |
| Run fixture once per value | `@pytest.fixture(params=[...], ids=[...])` → `request.param` |
| Mark one param value | `pytest.param(v, marks=pytest.mark.skip)` |
| Need it many times in a test | factory-as-fixture (return a function) |
| Share across files | put it in `conftest.py` |
| Use a plain module's fixtures | `pytest_plugins = "pkg.module"` in top `conftest.py` |
| Override for a subtree | redefine same name lower down (request same name for "super") |
| Require without using the value | `@pytest.mark.usefixtures("name")` |
| Avoid the name collision | `@pytest.fixture(name="...")` |
| Resolve a fixture by name at runtime | `request.getfixturevalue("name")` |
| Inspect order / availability | `pytest --setup-plan` / `pytest --fixtures` |

## Gotchas

- **`usefixtures` on a fixture does nothing.** It only applies to tests/classes/modules.
  Make a fixture depend on another by requesting it as an argument.
- **Higher scope can't depend on lower scope.** A `session` fixture requesting a
  `function` fixture is an error/meaningless; widen the dependency instead.
- **Autouse reaches every test in scope.** An autouse fixture in a `conftest.py` runs
  for the whole subtree — scope it deliberately.
- **One cached instance per scope.** A parametrized fixture is re-invoked per parameter
  value; pytest doesn't hold multiple instances of the same fixture simultaneously.
- **Execution order isn't lexical.** Don't rely on definition or request order; pin
  ordering through dependencies (or scope/autouse).
- **Don't import fixtures across modules.** Importing re-registers them as defined in
  the importer (duplicate entries in `--fixtures`, fragile). Use `conftest.py` /
  `pytest_plugins`.
- **`getfixturevalue` in teardown is deprecated (pytest 9.1+)** for not-yet-active
  fixtures — request them before the `yield`.
- **Class-scoped fixture as a bare instance method is deprecated (pytest 9.1+).** A
  fixture defined inside a class that relies on `self` should be a `@staticmethod` (or
  request what it needs as fixtures); the implicit instance-method form is slated for
  removal in pytest 10.
- **Applying a marker to a fixture is an error (pytest 9.0+).** Markers
  (`usefixtures`, `parametrize`, custom marks) belong on tests, not on
  `@pytest.fixture` functions.

## Sources

- `doc/en/how-to/fixtures.rst` — requesting, scopes, dynamic scope, teardown,
  finalizer order, safe structure, autouse, request introspection, parametrizing,
  factories, overriding, `usefixtures`, sharing across projects.
- `doc/en/reference/fixtures.rst` — fixture availability, `conftest.py` sharing,
  third-party plugins, instantiation order, autouse ordering.
- `src/_pytest/fixtures.py` — `fixture()` decorator signature, `FixtureRequest`
  attributes/methods, `getfixturevalue` (incl. `versionchanged:: 9.1`).
