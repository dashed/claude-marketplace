# pytest Command-Line Usage

How to **invoke pytest, select which tests run, and control its output** from the command
line. The mental model: `pytest` discovers and runs tests, and almost every aspect —
*which* tests, *when to stop*, *how much to print*, *which plugins load* — is a flag you
can stack on the invocation. The same flags can live in `addopts` in your config file so
they apply to every run (see [configuration.md](configuration.md)).

Examples are runnable and idiomatic for **pytest 9.x / Python 3.10+**. Inline tags like
`(pytest 9.1+)` mark a minimum version; untagged flags are bedrock (stable since pytest
6.x or earlier). Marker selection with `-m` and the `@pytest.mark.*` decorators are
summarized here but covered in full in [markers-skip-xfail.md](markers-skip-xfail.md);
warning *filters* (`-W`, `filterwarnings`) are cross-referenced to
[assertions.md](assertions.md) and [configuration.md](configuration.md); the imperative
`pytest.skip()` / `pytest.fail()` functions live in [assertions.md](assertions.md).

## Table of contents

- [Invoking pytest](#invoking-pytest)
- [Selecting which tests run](#selecting-which-tests-run)
- [Stopping early](#stopping-early)
- [Rerunning from the cache](#rerunning-from-the-cache)
- [Output and reporting](#output-and-reporting)
- [Traceback and locals](#traceback-and-locals)
- [Slowest tests: `--durations`](#slowest-tests---durations)
- [Collection control](#collection-control)
- [Debugging: `--pdb` and `--trace`](#debugging---pdb-and---trace)
- [Activating and disabling plugins: `-p`](#activating-and-disabling-plugins--p)
- [Warnings on the command line](#warnings-on-the-command-line)
- [JUnit XML](#junit-xml)
- [Exit codes](#exit-codes)
- [Quick reference](#quick-reference)
- [Sources](#sources)

## Invoking pytest

Run `pytest` and it collects every `test_*.py` / `*_test.py` under the current directory
(per the standard discovery rules) and runs the `test_*` functions/methods inside:

```bash
pytest                    # everything under the current dir
pytest tests/             # a directory
pytest tests/test_mod.py  # a single module
```

Two other entry points:

```bash
python -m pytest [...]    # same as `pytest`, but ALSO adds the current dir to sys.path
pytest --pyargs pkg.testing   # locate tests by importable package name, not path
```

You can call pytest from Python too — `pytest.main(["-x", "tests/"])` returns the
[exit code](#exit-codes) (it does **not** raise `SystemExit`).

**Read arguments from a file** *(pytest 8.2+)* with the `@` prefix — one argument per
line, handy for large or generated selections:

```bash
pytest @tests_to_run.txt   # file generated e.g. by: pytest --collect-only -q
```

Quick introspection: `pytest --version`, `pytest --fixtures`, `pytest --markers`,
`pytest -h`.

Source: `doc/en/how-to/usage.rst` ("Specifying which tests to run", "Other ways of
calling pytest", "Read arguments from file").

## Selecting which tests run

**Node IDs** address a specific test. The format is the module path, then `::`-separated
class and function names, then the parametrization in `[...]`:

```bash
pytest tests/test_mod.py::test_func
pytest tests/test_mod.py::TestClass
pytest tests/test_mod.py::TestClass::test_method
pytest "tests/test_mod.py::test_func[x1,y2]"   # one parametrized variant
```

**`-k` — keyword expression.** Run tests whose *name* matches a Python-like boolean
expression (substring match, case-insensitive):

```bash
pytest -k "MyClass and not method"
pytest -k "parse or serialize"
```

**`-m` — marker expression.** Run tests by applied marker; supports `and`/`or`/`not` and
argument matching:

```bash
pytest -m slow
pytest -m "not slow"
pytest -m "db and not slow"
pytest -m "slow(phase=1)"     # marker with a keyword argument
```

See [markers-skip-xfail.md](markers-skip-xfail.md) for defining and registering markers.

Source: `doc/en/how-to/usage.rst` ("Specifying which tests to run");
`doc/en/reference/reference.rst` (`-k`, `-m`).

## Stopping early

```bash
pytest -x            # alias --exitfirst: stop on the FIRST failure/error
pytest --maxfail=2   # stop after N failures/errors
```

Source: `doc/en/how-to/failures.rst` ("Stopping after the first (or N) failures").

## Rerunning from the cache

pytest records the last run's results (in `.pytest_cache`), enabling fast iteration:

| Flag | Effect |
|---|---|
| `--lf`, `--last-failed` | run **only** tests that failed last time (all tests if none failed) |
| `--ff`, `--failed-first` | run everything, but **last failures first** |
| `--nf`, `--new-first` | run new/recently-modified test files first |
| `--sw`, `--stepwise` | stop at the first failure; **resume there** next run |
| `--sw-skip`, `--stepwise-skip` | like `--sw` but skip the *first* failing test, stop on the next |
| `--lfnf=all\|none`, `--last-failed-no-failures` | what `--lf` does when nothing failed (default `all`) |
| `--cache-clear` | wipe the cache **before** the run (recommended in CI) |
| `--cache-show[=GLOB]` | print cache contents and exit (no collection/run) |

```bash
pytest --lf            # iterate on just the failures
pytest --sw            # fix failures one at a time, resuming each run
pytest --cache-clear   # clean slate
```

Source: `doc/en/how-to/cache.rst` ("Rerunning only failures or failures first",
"Stepwise", "Clearing Cache content").

## Output and reporting

**Verbosity:**

```bash
pytest -q     # quiet: less output
pytest -v     # one line per test; fuller assert diffs
pytest -vv    # even more detail; disables assertion-diff truncation
```

**`-r` — short test summary.** Appends a "short test summary info" section listing
outcomes by category. It defaults to `fE` (failures + errors); pass characters to choose:

| Char | Includes | | Char | Includes |
|---|---|---|---|---|
| `f` | failed | | `p` | passed |
| `E` | error | | `P` | passed **with output** |
| `s` | skipped | | `a` | all except passed (`p`/`P`) |
| `x` | xfailed | | `A` | all |
| `X` | xpassed | | `N` | none (reset the list) |
|  |  | | `w` | warnings (on by default) |

```bash
pytest -ra     # everything except passes — a great default
pytest -rfE    # just failures and errors (the implicit default)
pytest -rsx    # skipped and xfailed
```

**Capture control** — pytest captures stdout/stderr and shows it only for failing tests.
To see output live, disable capture:

```bash
pytest -s                 # alias --capture=no: don't capture at all
pytest --capture=fd       # default: capture at the file-descriptor level
pytest --capture=sys      # capture Python-level sys.stdout/stderr only
pytest --capture=tee-sys  # capture AND echo to the terminal
```

`--show-capture=no|stdout|stderr|log|all` controls what captured output is shown on
failures (default `all`). Trim the header/summary with `--no-header` / `--no-summary`.

Source: `doc/en/how-to/output.rst` ("Verbosity", "Producing a detailed summary
report"); `doc/en/reference/reference.rst` (`-r`, `--capture`, `--show-capture`).

## Traceback and locals

**`--tb=STYLE`** sets how failure tracebacks are rendered:

| Style | Output |
|---|---|
| `auto` | (default) long for the first/last frame, short for the rest |
| `long` | exhaustive, every frame in full |
| `short` | condensed frames |
| `line` | a single line per failure |
| `native` | Python's standard `traceback` formatting |
| `no` | no traceback at all |

```bash
pytest --tb=short
pytest --tb=no       # just the pass/fail counts
```

**`-l` / `--showlocals`** adds local-variable values to each traceback frame
(`--no-showlocals` negates it if enabled via `addopts`). **`--full-trace`** prints
untruncated traces — and ensures a trace is printed if you interrupt a hanging run with
Ctrl-C.

Source: `doc/en/how-to/output.rst` / `doc/en/how-to/failures.rst` ("Modifying Python
traceback printing"); `doc/en/reference/reference.rst` (`--tb`, `--showlocals`,
`--full-trace`).

## Slowest tests: `--durations`

Find what's slow:

```bash
pytest --durations=10               # show the 10 slowest setups/tests
pytest --durations=10 --durations-min=1.0   # only those ≥ 1.0s
pytest --durations=0                # show ALL durations, slowest first
```

`--durations-min` defaults to `0.005s` (and durations under that are hidden unless `-vv`).

Source: `doc/en/how-to/usage.rst` ("Profiling test execution duration");
`doc/en/reference/reference.rst` (`--durations`, `--durations-min`).

## Collection control

Inspect or prune what gets collected — *without* running anything:

```bash
pytest --collect-only      # alias --co: list what WOULD run
pytest --co -q             # compact; output is valid for `@argfile`
```

| Flag | Effect |
|---|---|
| `--ignore=PATH` | skip a path during collection (repeatable) |
| `--ignore-glob=PATTERN` | skip paths matching a glob (repeatable) |
| `--deselect=NODEID` | drop a specific test/prefix (repeatable) |
| `--continue-on-collection-errors` | run collectible tests even if some modules fail to import |

```bash
pytest --ignore=tests/legacy --ignore-glob="*_wip.py"
pytest --deselect "tests/test_mod.py::test_flaky"
```

Source: `doc/en/reference/reference.rst` ("Collection": `--collect-only`, `--ignore`,
`--ignore-glob`, `--deselect`).

## Debugging: `--pdb` and `--trace`

```bash
pytest --pdb          # drop into the debugger on each failure / KeyboardInterrupt
pytest -x --pdb       # ...but only the first failure, then stop
pytest --trace        # break at the START of every test
pytest --pdbcls=IPython.terminal.debugger:TerminalPdb   # use a custom debugger class
```

On a failure, the exception is also stored on `sys.last_value` / `sys.last_traceback`
for postmortem inspection. A plain `breakpoint()` in your code works too: pytest
disables output capture for that test while you're at the prompt.

Source: `doc/en/how-to/failures.rst` ("Using pdb with pytest");
`doc/en/reference/reference.rst` (`--pdb`, `--trace`, `--pdbcls`).

## Activating and disabling plugins: `-p`

`-p NAME` early-loads a plugin (a dotted module name or an entry-point name). The
`no:` prefix **disables** a plugin — including pytest's own built-ins:

```bash
pytest -p pytest_cov                 # early-load a plugin
pytest -p no:cacheprovider           # disable the cache (no .pytest_cache)
pytest -p no:warnings                # disable the warnings plugin entirely
pytest -p no:randomly                # disable a third-party plugin for one run
```

`--disable-plugin-autoload` *(pytest 8.4+)* loads *only* plugins you name with `-p` (or
`PYTEST_PLUGINS`), ignoring entry-point auto-discovery — useful for reproducible runs.

Source: `doc/en/how-to/usage.rst` ("Managing loading of plugins");
`doc/en/reference/reference.rst` (`-p`, `--disable-plugin-autoload`).

## Warnings on the command line

```bash
pytest -W error                  # turn ALL warnings into errors
pytest -W error::DeprecationWarning   # only this category becomes an error
pytest -W ignore::UserWarning    # silence a category
pytest --disable-warnings        # hide the warnings SUMMARY (warnings still happen)
pytest --max-warnings=10         # (pytest 9.1+) fail the run if warnings exceed N
```

`-W` mirrors Python's own `-W` filter syntax and is repeatable; persistent filters
belong in the `filterwarnings` config option ([configuration.md](configuration.md)), and
asserting on warnings in a test uses `pytest.warns` ([assertions.md](assertions.md)).
`--max-warnings` *(pytest 9.1+)* exits with code `6` if all tests pass but the warning
count exceeds the threshold (filtered warnings don't count); if any test fails the exit
code stays `1`.

Source: `doc/en/how-to/capture-warnings.rst` ("Controlling warnings", "Setting a maximum
number of warnings", `versionadded:: 9.1`); `doc/en/reference/reference.rst` (`-W`,
`--max-warnings`, `--disable-warnings`).

## JUnit XML

Emit a JUnit-style XML report for CI servers (Jenkins, GitLab, etc.):

```bash
pytest --junit-xml=report.xml     # alias: --junitxml=report.xml
```

The suite name and time semantics are configurable via `junit_suite_name` /
`junit_duration_report` in the config file ([configuration.md](configuration.md)).

Source: `doc/en/how-to/output.rst` ("Creating JUnitXML format files");
`doc/en/reference/reference.rst` (`--junit-xml`).

## Exit codes

`pytest` returns one of these process exit codes, exposed as the `pytest.ExitCode` enum
(`from pytest import ExitCode`):

| Code | `ExitCode` | Meaning |
|---|---|---|
| `0` | `OK` | all collected tests passed |
| `1` | `TESTS_FAILED` | tests ran but some failed |
| `2` | `INTERRUPTED` | the run was interrupted (e.g. Ctrl-C) |
| `3` | `INTERNAL_ERROR` | an internal pytest error occurred |
| `4` | `USAGE_ERROR` | command-line usage error |
| `5` | `NO_TESTS_COLLECTED` | no tests were collected |
| `6` | `MAX_WARNINGS_ERROR` | *(pytest 9.1+)* warnings exceeded `--max-warnings` (only when all tests otherwise pass) |

> **Watch for code `5`** in CI: a bad path or an over-eager `-k`/`-m`/`--ignore` that
> matches nothing exits non-zero even though "nothing failed". Code `1` always wins over
> code `6` — a failing test reports `1` regardless of the warning count.

Source: `doc/en/reference/exit-codes.rst`; `doc/en/how-to/capture-warnings.rst`
(code `6`, `versionadded:: 9.1`).

## Quick reference

| Goal | Command |
|---|---|
| Run one test | `pytest path::Class::test[param]` |
| By name substring | `pytest -k "expr and not other"` |
| By marker | `pytest -m "slow and not db"` |
| Stop on first failure | `pytest -x` / `pytest --maxfail=N` |
| Rerun only failures | `pytest --lf` |
| Failures first | `pytest --ff` |
| Fix one at a time | `pytest --sw` |
| Clear the cache | `pytest --cache-clear` |
| Verbose / quiet | `pytest -v` / `pytest -vv` / `pytest -q` |
| Summary of all outcomes | `pytest -ra` |
| Show prints live | `pytest -s` |
| Short tracebacks | `pytest --tb=short` (or `line`, `no`, `native`) |
| Show locals in traceback | `pytest -l` |
| Slowest tests | `pytest --durations=10` |
| List without running | `pytest --collect-only` (`--co`) |
| Ignore paths | `pytest --ignore=PATH --ignore-glob=PAT` |
| Deselect a test | `pytest --deselect NODEID` |
| Debug on failure | `pytest --pdb` (`-x --pdb` for just the first) |
| Break at test start | `pytest --trace` |
| Disable a plugin | `pytest -p no:cacheprovider` |
| Warnings → errors | `pytest -W error` |
| Cap warnings | `pytest --max-warnings=N` *(9.1+)* |
| JUnit report | `pytest --junit-xml=report.xml` |

## Sources

- `doc/en/how-to/usage.rst` — invocation, `python -m pytest`, `--pyargs`, `@argfile`
  (`8.2`), `pytest.main`, `-k`/`-m`, `--durations`, `-p` plugin loading.
- `doc/en/how-to/failures.rst` — `-x`/`--maxfail`, `--pdb`/`--trace`/`--pdbcls`.
- `doc/en/how-to/cache.rst` — `--lf`/`--ff`/`--nf`/`--sw`, `--lfnf`, `--cache-clear`,
  `--cache-show`.
- `doc/en/how-to/output.rst` — verbosity, `-r` report chars, `--capture`/`-s`, `--tb`,
  `--showlocals`, truncation, `--junit-xml`.
- `doc/en/how-to/capture-warnings.rst` — `-W`, `--disable-warnings`, `--max-warnings`
  (`9.1`).
- `doc/en/reference/exit-codes.rst` — the `ExitCode` enum (0–6).
- `doc/en/reference/reference.rst` — the complete command-line flags reference.
