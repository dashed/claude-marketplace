# pytest Plugins & Hooks

Using third-party plugins, controlling which plugins load, writing your own (local `conftest.py`
plugins and installable `pytest11` plugins), the hook system (`hookimpl`/`hookspec`, `firstresult`,
hook wrappers, ordering), the most useful hooks, and testing plugins with the `pytester` fixture.

Version tags like `(pytest 8.0+)` mark the minimum version a feature requires; **untagged = bedrock**
(stable since pytest 6.x or earlier). Sources cited inline as `doc/en/...` / `src/_pytest/...`.

> **Scope:** this file covers the *plugin & hook* machinery. For ini options and `addopts` see
> `configuration.md`; for fixture authoring see `fixtures.md`; for CLI runtime flags see
> `cli-usage.md`.

## Contents

- [The plugin model](#the-plugin-model)
- [Using third-party plugins](#using-third-party-plugins)
- [Listing & controlling plugins](#listing--controlling-plugins)
- [Plugin discovery order at startup](#plugin-discovery-order-at-startup)
- [Writing local plugins (`conftest.py`)](#writing-local-plugins-conftestpy)
- [Making an installable plugin (`pytest11`)](#making-an-installable-plugin-pytest11)
- [The hook system](#the-hook-system)
- [Key hooks reference](#key-hooks-reference)
- [Testing plugins with `pytester`](#testing-plugins-with-pytester)
- [Troubleshooting](#troubleshooting)

## The plugin model

pytest is itself a plugin system: collection, running, and reporting are all implemented by calling
**hooks** on registered plugins. Each hook call is a `1:N` call — pytest invokes *every* registered
implementation of a given hook spec. All hook names use the `pytest_` prefix
(`doc/en/how-to/writing_plugins.rst`). There are three kinds of plugin:

1. **Builtin** — modules in pytest's internal `_pytest` package.
2. **Installed (external)** — third-party distributions discovered via the `pytest11` packaging
   entry point.
3. **`conftest.py`** — local, per-directory modules auto-discovered in your test tree.

## Using third-party plugins

Install with pip; pytest **auto-discovers and activates** installed plugins — no registration step:

```bash
pip install pytest-xdist pytest-cov
pytest -n auto --cov=mypkg          # both plugins now active
```

Notable plugins (`doc/en/how-to/plugins.rst`; the full searchable list is the docs' "plugin list"):

| Plugin | What it adds | Typical use |
|---|---|---|
| `pytest-xdist` | Parallel / distributed runs | `pytest -n auto` (one worker per CPU) or `-n logical`; `--dist loadscope`/`loadgroup`/`worksteal` |
| `pytest-cov` | Coverage (works with xdist) | `pytest --cov=mypkg --cov-report=term-missing` |
| `pytest-asyncio` | `async def` test support | `asyncio_mode = "auto"` ini, or `@pytest.mark.asyncio` |
| `pytest-mock` | `mocker` fixture wrapping `unittest.mock` | `mocker.patch("mod.func")` |
| `pytest-randomly` | Randomize test order each run (seeded) | reorders automatically; `--randomly-seed=…`, disable with `-p no:randomly` |
| `pytest-django` | Django integration | `DJANGO_SETTINGS_MODULE` / `django_settings` ini, `db` fixture, `@pytest.mark.django_db`, `--reuse-db` |
| `pytest-timeout` | Per-test timeouts | `--timeout=30`, `timeout` ini, `@pytest.mark.timeout(5)` |
| `pytest-instafail` | Show failures as they happen | `pytest --instafail` |
| `pytest-bdd` | Behaviour-driven (Gherkin) tests | scenarios bound to step fixtures |

Pin required plugins so a misconfigured environment fails loudly (see `configuration.md`):

```toml
[tool.pytest]
required_plugins = ["pytest-xdist>=3.0", "pytest-cov"]
```

## Listing & controlling plugins

```bash
pytest --trace-config        # header lists every active plugin + loaded conftest.py files
pytest -p xdist              # force-load a plugin (by entry-point name) for this run
pytest -p no:randomly        # block a plugin (even a builtin) for this run
```

- **`-p NAME`** loads a plugin early (before normal arg parsing); **`-p no:NAME`** blocks it. Find a
  plugin's name with `--trace-config`.
- Disable a plugin project-wide via `addopts`:
  ```toml
  [tool.pytest]
  addopts = ["-p", "no:cacheprovider"]   # e.g. turn off the cache plugin
  ```
- **`PYTEST_ADDOPTS="-p no:randomly"`** disables a plugin in one environment (e.g. CI) without
  editing files.
- **`--disable-plugin-autoload`** **(pytest 8.4+)** / **`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`** (env var is bedrock) turns off
  *all* entry-point autoloading; you then opt in explicitly with `-p NAME` or the `PYTEST_PLUGINS`
  env var. Useful for reproducible, minimal environments.
  ```bash
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p xdist        # load ONLY xdist
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_PLUGINS=mymod.plugin,xdist pytest
  ```
  Don't specify the same plugin via two mechanisms (e.g. `-p` *and* `PYTEST_PLUGINS`) — double
  registration errors (`doc/en/how-to/plugins.rst`).

## Plugin discovery order at startup

Knowing the order explains *why a hook isn't available yet* (e.g. why a `conftest.py` can't influence
another plugin's `pytest_addoption`). pytest loads plugins like this
(`doc/en/how-to/writing_plugins.rst`):

1. Scan the command line for `-p no:NAME` and **block** those plugins.
2. Load all **builtin** plugins.
3. Scan for `-p NAME` and load those.
4. Load **entry-point** (installed) plugins — unless `PYTEST_DISABLE_PLUGIN_AUTOLOAD` is set.
5. Load plugins named in the `PYTEST_PLUGINS` env var.
6. Load **initial `conftest.py`** files: determine the test paths (CLI args, else `testpaths` from
   rootdir, else cwd); for each, load `conftest.py` (and parents' conftests first), then recursively
   load any `pytest_plugins` they declare.

> Because conftests load **last**, hook implementations in a `conftest.py` are **not** available to
> other plugins during *their* `pytest_addoption()` — only earlier-loaded plugins (builtin, `-p`,
> entry-point, `PYTEST_PLUGINS`) are. An *initial* conftest can still implement its own
> `pytest_addoption()` (`doc/en/how-to/writing_hook_functions.rst`).

## Writing local plugins (`conftest.py`)

A `conftest.py` is a plugin scoped to its directory subtree — drop hook functions and fixtures in and
they're picked up automatically (no import, no registration). See `configuration.md` for layering
rules. Two examples:

**Register custom markers** (so they appear in `--markers` and don't warn under `strict_markers`):

```python
# conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow to run")
    config.addinivalue_line("markers", "serial: must not run in parallel")
```

**Add a command-line option and a fixture that reads it:**

```python
# conftest.py
import pytest


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="dev", help="target environment")


@pytest.fixture
def env(request):
    return request.config.getoption("--env")
```

**Load shared support code as a plugin** with the `pytest_plugins` variable (only in the **root**
conftest — non-root use is deprecated):

```python
# conftest.py (project root)
pytest_plugins = ["myapp.testsupport.fixtures", "myapp.testsupport.hooks"]
```

This is the lightweight way to share fixtures/hooks across a codebase without packaging a separate
distribution. Modules loaded this way are also marked for assertion rewriting.

## Making an installable plugin (`pytest11`)

To ship a plugin on PyPI, expose it through the **`pytest11`** entry point in `pyproject.toml`
(`doc/en/how-to/writing_plugins.rst`):

```toml
# pyproject.toml of your plugin distribution
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pytest-myplugin"
classifiers = ["Framework :: Pytest"]      # so users can find it on PyPI

[project.entry-points.pytest11]
myplugin = "pytest_myplugin.plugin"          # name = importable module
```

Once installed, pytest auto-loads `pytest_myplugin.plugin` as a plugin. Confirm with
`pytest --trace-config`.

**Assertion rewriting in packaged plugins.** pytest's rich `assert` introspection comes from
rewriting the AST of test modules and *plugin modules*. Only the module named in the `pytest11`
entry point (and `conftest.py` files) is rewritten automatically. If your plugin keeps assertion
helpers in *other* modules, register them **before import** — easiest from the package `__init__.py`:

```python
# pytest_myplugin/__init__.py
import pytest

pytest.register_assert_rewrite("pytest_myplugin.helpers")
```

**Collaborating with another plugin** — fetch it by name from the plugin manager, and guard against
it being absent:

```python
def pytest_configure(config):
    if config.pluginmanager.hasplugin("xdist"):
        config.pluginmanager.register(MyXdistSupport())

# elsewhere
other = config.pluginmanager.get_plugin("name_of_plugin")
```

## The hook system

A **hookspec** declares a hook (signature + docs); a **hookimpl** is your implementation. You write
hookimpls; only plugins *declaring new hooks* write hookspecs (`doc/en/how-to/writing_hook_functions.rst`).

**Argument pruning (future-compatibility).** Declare only the parameters you need — pytest passes
hook arguments by keyword and matches them to your signature. This is why old plugins keep working
when pytest adds new hook parameters:

```python
# the spec is pytest_collection_modifyitems(session, config, items); take only what you use
def pytest_collection_modifyitems(config, items):
    ...
```

> Hooks other than `pytest_runtest_*` must **not** raise — doing so breaks the run.

**`@pytest.hookimpl` options:**

| Option | Effect |
|---|---|
| `tryfirst=True` | Run as early as possible among implementations. |
| `trylast=True` | Run as late as possible. |
| `wrapper=True` **(pytest 8.0+)** | New-style hook wrapper (generator; see below). |
| `hookwrapper=True` | Older-style wrapper (still supported); yields a `Result` object. |
| `optionalhook=True` | Don't error if no matching spec exists (hook from an optional plugin). |
| `specname="pytest_…"` | Implement a hook under a different function name (function still must start with `pytest_`). |

**`firstresult` hooks.** Most hooks collect a **list** of all non-`None` returns. Hooks declared with
`@hookspec(firstresult=True)` stop at the **first** non-`None` result. Examples in pytest:
`pytest_runtest_makereport`, `pytest_pyfunc_call`, `pytest_cmdline_main`, `pytest_collection`,
`pytest_ignore_collect`, `pytest_runtest_protocol` (`src/_pytest/hookspec.py`).

**Hook wrappers** wrap the execution of all the non-wrapper implementations. A wrapper is a generator
that `yield`s exactly once; the value of the `yield` is the result from the wrapped implementations
(or it raises if they did). New-style (`wrapper=True`, **pytest 8.0+** — requires `pytest>=8`):

```python
import pytest


@pytest.hookimpl(wrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    do_before()
    try:
        result = yield          # runs the actual implementations; re-raises on error
    finally:
        do_after()
    return result               # MUST return a result (or raise)
```

The simplest pass-through wrapper is `return (yield)`. To merely observe, wrap the `yield` in
`try/finally`. To adapt the outcome, return a new value. (Old `hookwrapper=True` instead yields a
`Result` object you call `.get_result()`/`.force_result()` on.)

**Ordering** — wrappers run outermost; among non-wrappers `tryfirst` runs before `trylast`:

```python
@pytest.hookimpl(wrapper=True)          # 1: before yield (outermost)
def pytest_collection_modifyitems(items): return (yield)   # 4: after yield

@pytest.hookimpl(tryfirst=True)         # 2
def pytest_collection_modifyitems(items): ...

@pytest.hookimpl(trylast=True)          # 3
def pytest_collection_modifyitems(items): ...
```

**Declaring new hooks** — register a module of hookspecs from `pytest_addhooks`:

```python
# hooks.py
def pytest_my_event(config):
    """Called when ... ; implementations may return X."""

# plugin.py
def pytest_addhooks(pluginmanager):
    from . import hooks
    pluginmanager.add_hookspecs(hooks)

# call it later: results = config.hook.pytest_my_event(config=config)
```

`pytest_addhooks` is `historic=True` (so late-registered plugins still see past calls), as are
`pytest_addoption`, `pytest_configure`, and `pytest_plugin_registered`
(`src/_pytest/hookspec.py`).

**Sharing data across hooks** — use the type-safe `Stash` instead of monkey-patching attributes onto
items:

```python
import pytest

been_there = pytest.StashKey[bool]()


def pytest_runtest_setup(item):
    item.stash[been_there] = True
```

## Key hooks reference

Selected hooks, by phase (full list + signatures: `src/_pytest/hookspec.py`). `fr` = `firstresult`.

| Hook | When | Notes |
|---|---|---|
| `pytest_addoption(parser, pluginmanager)` | Startup, once | Add CLI options / ini values. `historic`. Only in initial conftests / early plugins. |
| `pytest_configure(config)` | After options parsed | Register markers, set up plugin state. `historic`. |
| `pytest_unconfigure(config)` | At shutdown | Tear down what `pytest_configure` set up. |
| `pytest_sessionstart(session)` / `pytest_sessionfinish(session, exitstatus)` | Around the whole session | Global setup/teardown, summary. |
| `pytest_collection_modifyitems(session, config, items)` | After collection | Filter/re-order `items` **in place**. If you drop items, call `config.hook.pytest_deselected(items=…)`. |
| `pytest_generate_tests(metafunc)` | Per test function, at collection | Programmatic parametrization (`metafunc.parametrize(...)`). **Also discovered inside test modules/classes**, unlike most hooks. |
| `pytest_runtest_setup(item)` / `pytest_runtest_call(item)` / `pytest_runtest_teardown(item, nextitem)` | The three run phases | Per-item setup/run/teardown; conftest-local (only the item's dir + parents). |
| `pytest_runtest_makereport(item, call)` | After each phase | `fr`. Build the `TestReport`. Common pattern: a `wrapper` here to attach phase reports for fixtures. |
| `pytest_runtest_protocol(item, nextitem)` | Per item | `fr`. Override the whole setup/call/teardown protocol. |
| `pytest_report_header(config, start_path)` | Startup | Add lines to the run header. |
| `pytest_terminal_summary(terminalreporter, exitstatus, config)` | End | Add custom summary output. |
| `pytest_assertrepr_compare(config, op, left, right)` | On failing `assert` | Custom explanation for comparisons of your types. |
| `pytest_collect_file(file_path, parent)` | Per file during collection | Collect non-Python test files (custom collectors). |

The hooks themselves are long-standing, but their **`pathlib.Path` parameters** — `file_path`,
`collection_path`, `module_path`, `start_path` (shown above) — were added in **pytest 7.0+**,
replacing the older `py.path.local`-based `path`/`fspath` params (the legacy params were removed in
pytest 9.0). Use the `Path` names in new code.

Plugins and conftests can also define **fixtures** directly (just `@pytest.fixture` functions) — the
most common way a plugin exposes capabilities (e.g. `mocker`, `db`). See `fixtures.md`.

## Testing plugins with `pytester`

pytest ships the **`pytester`** fixture for testing plugin/hook code by running pytest in an isolated
temp project. It's disabled by default — enable it in your test suite's `conftest.py`
(`doc/en/how-to/writing_plugins.rst`):

```python
# conftest.py
pytest_plugins = ["pytester"]          # or invoke pytest with: -p pytester
```

```python
def test_my_plugin(pytester):
    # write a temp conftest + test file into the isolated project
    pytester.makeconftest(
        """
        import pytest

        @pytest.fixture
        def hello():
            return "Hello World!"
        """
    )
    pytester.makepyfile(
        """
        def test_greeting(hello):
            assert hello == "Hello World!"
        """
    )

    result = pytester.runpytest()            # run pytest in the temp dir
    result.assert_outcomes(passed=1)         # assert on outcomes
    result.stdout.fnmatch_lines(["*1 passed*"])
```

Useful `pytester` API: `makepyfile` / `makeconftest` / `maketxtfile`, `runpytest()` (in-process) and
`runpytest_subprocess()`, `copy_example()` (needs `pytester_example_dir` set in config),
`parseconfig()`. `runpytest()` returns a `RunResult` with `assert_outcomes(...)`, `.stdout`,
`.stderr`, and `.ret`.

> **Legacy:** `testdir` is the older `py.path`-based equivalent of `pytester` and still exists, but
> new code should use `pytester` (`pathlib`-based).

```toml
# enable pytester.copy_example to pull fixtures from a known dir
[tool.pytest]
pytester_example_dir = "."
```

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Installed plugin "does nothing" | Confirm it's loaded: `pytest --trace-config`. Autoload may be disabled (`PYTEST_DISABLE_PLUGIN_AUTOLOAD`). |
| Hook never fires | Wrong name (must start with `pytest_` and match a spec exactly), or implemented in a non-initial conftest for an early hook. |
| `pytest_addoption` can't see another plugin's hook | conftests load **after** other plugins; move the hookspec into an entry-point/`-p` plugin. |
| Wrapper "did not return a result" error | A `wrapper=True` generator must `return` a value (e.g. `return (yield)`) or raise. |
| Double-registration error | Same plugin specified via two mechanisms (`-p` and `PYTEST_PLUGINS`, etc.). Pick one. |
| Assertions in a plugin helper not rewritten | `register_assert_rewrite("pkg.helper")` in the package `__init__.py` before import. |
| `pytester` fixture not found | Enable it: `pytest_plugins = ["pytester"]` or `-p pytester`. |
| `wrapper=True` raises `TypeError` on old pytest | New-style wrappers need `pytest>=8`; use `hookwrapper=True` for older support. |
