# pytest Feature → Minimum Version

A consolidated lookup of **which pytest version introduced each feature, fixture, marker, CLI
flag, or config option** this skill documents — so you know what works on an older (or newer)
pytest. Use it to answer "is my pytest new enough for X?" and "what do I need to upgrade to?"

This file is also the **source of truth for the inline `(pytest N.M+)` tags** used throughout the
skill's reference files. Every row is sourced from the pytest repo's changelog
(`doc/en/changelog.rst`, mirrored at <https://docs.pytest.org/en/stable/changelog.html>) with the
issue/PR number that introduced it.

## How to read this

- pytest versions look like `MAJOR.MINOR.PATCH` (e.g. `8.4.0`). **Features land on minor or major
  releases** (`7.4.0`, `8.0.0`, `9.0.0`); **patch releases** (`8.3.5`, `9.0.3`) are bug/security
  fixes only and never add features. So the `+` in a tag always points at a `MAJOR.MINOR`: `(pytest
  8.4+)` means "the pytest 8.4.0 release and later." You will never see a tag like `(pytest 8.3.5+)`.
- **Bedrock = stable since the 6.x era (or earlier).** Anything present and stable at or before
  pytest **6.2** (the last 6.x, 2020–2021) is treated as long-standing and carries **no version
  tag** in the skill ("unlisted = long-standing"). The interesting, taggable surface starts at
  **pytest 7.0** (2022-02-03). This mirrors the fact that 7.0 is the oldest release a modern
  project realistically targets, and everything older — fixtures, parametrize, marks, assert
  rewriting, the core built-in fixtures — is universal.
- **Verify, don't guess.** Every versioned row below is sourced from the official changelog with
  its `#issue`/`#pr` number. A feature without a clean "added in version N" source is treated as
  bedrock and **omitted** rather than guessed.
- **Latest stable is pytest `9.1.0`** (2026-06-13). The in-repo dev tip is `9.2.0.dev0` — **do not
  pin to it**; nothing here is tagged `9.2`. The minimum **Python** for pytest 9.x is **3.10**
  (3.9 was dropped in 9.0, `#13719`); pytest 8.x required ≥3.8, 7.x required ≥3.7.

### What's bedrock (intentionally untagged)

These are present since the 6.x era or earlier and appear in the skill **without** a tag:

- **Fixtures:** `@pytest.fixture`, all scopes (`function`/`class`/`module`/`package`/`session`),
  `params=`, `autouse=`, `ids=`, yield fixtures + finalizers (`request.addfinalizer`),
  `request`/`request.param`, `request.getfixturevalue()`, fixture overriding, fixture
  parametrization. (`yield_fixture` exists but was deprecated back in 6.2.)
- **Built-in fixtures:** `tmp_path` & `tmp_path_factory` (added 3.9), `tmpdir` & `tmpdir_factory`
  (older still — **not formally deprecated**, only *discouraged* in favor of `tmp_path` per a 7.1.3
  doc note), `monkeypatch`, `capsys`/`capfd`/`capsysbinary`/`capfdbinary`, `caplog`, `recwarn`,
  `pytestconfig`, `cache`, `doctest_namespace`, `pytester` (added 3.9, replaced `testdir`),
  `request`.
- **Parametrize & marks:** `@pytest.mark.parametrize` (incl. `indirect=`, `ids=`, `pytest.param`,
  `marks=`), `@pytest.mark.skip`/`skipif`/`xfail`/`usefixtures`/`filterwarnings`, custom markers +
  the `markers` ini option, `pytestmark`. `xfail_strict` ini (**default `False`**, never changed)
  and per-mark `@pytest.mark.xfail(strict=True)`.
- **Assertions & helpers:** `assert` rewriting, `pytest.raises` (incl. `match=`), `pytest.warns`
  (incl. `match=`), `pytest.approx`, `pytest.fail`/`skip`/`xfail`/`exit`/`importorskip`,
  `ExceptionInfo`.
- **CLI:** `-k`, `-m`, `-x`, `-s`, `--collect-only` **and its `--co` alias** (alias added 5.3),
  `-p`, `--pdb`, `-r` report chars, `--tb=`, `--lf`/`--ff`/`--nf`, `--maxfail`, `-v`/`-vv`,
  `--durations`, `--fixtures`, `-c`/`--config-file`.
- **Config & plugins:** `pytest.ini`, `pyproject.toml [tool.pytest.ini_options]` (since 6.0),
  `setup.cfg`, `tox.ini`, `addopts`, `minversion`, `testpaths`, `python_files`/`python_classes`/
  `python_functions`, `filterwarnings`, **`required_plugins`** (added 6.0, `#7305`),
  `--strict-markers` & `--strict-config` (6.x), `norecursedirs`, `conftest.py`, plugin loading
  (`-p`, `PYTEST_PLUGINS`, setuptools entry points), the long-standing `pytest_*` hooks,
  `pytest.hookimpl`/`pytest.hookspec`, and **old-style `@pytest.hookimpl(hookwrapper=True)`** (still
  supported, not formally deprecated).
- **Import:** `--import-mode=importlib` exists since **6.0** (`#7245`) — it is *opt-in*. The
  **default import mode is still `prepend`** through 9.1; importlib has never become the default.

## Versioned features (ascending by pytest release)

Grouped within each release by **Area**. Every row cites the changelog issue/PR.

| Min version | Feature | Area | Source |
|---|---|---|---|
| pytest 7.0+ | `pytest.Stash` — type-safe per-`Config`/`Node` storage for plugins | Plugins | `#8920` |
| pytest 7.0+ | `pythonpath` ini option (adds paths to `sys.path` for the session) | Config | `#9114` |
| pytest 7.0+ | `pytest.version_tuple` — numeric `(9, 1, 0)` for version checks | API | `#8761` |
| pytest 7.0+ | Public type exports: `pytest.Config`, `pytest.Mark`, `pytest.MarkDecorator`, `pytest.Metafunc`, `pytest.CallInfo`, `pytest.ExceptionInfo`, `pytest.Parser`, `pytest.TestReport`, `pytest.CollectReport`, … (for annotations) | API | `#7469` |
| pytest 7.0+ | `pathlib.Path` hook params — `collection_path`/`file_path`/`module_path`/`start_path` added to `pytest_ignore_collect`/`pytest_collect_file`/`pytest_pycollect_makemodule`/`pytest_report_header`/`pytest_report_collectionfinish` | Hooks | `#8144` |
| pytest 7.0+ | `Node.path` exposed as a `pathlib.Path` | Hooks | `#8251` |
| pytest 7.0+ | `cache.mkdir()` (pathlib) + `parser.addini(type="paths")` | Config | `#7259` |
| pytest 7.0+ | `RunResult.assert_outcomes(warnings=...)` (pytester) | Plugins | `#8953` |
| pytest 7.0+ | `RunResult.assert_outcomes(deselected=...)` (pytester) | Plugins | `#9113` |
| pytest 7.0+ | **Deprecated:** `pytest.warns(None)` | Deprecation | `#8645` |
| pytest 7.0+ | **Deprecated:** `skip()/fail()/exit()` `msg=` → use `reason=` | Deprecation | `#8948` |
| pytest 7.1+ | `ids` accepts more types: `bytes`, `complex`, `re.Pattern`, `Enum`, anything with `__name__` | Parametrize | `#9678` |
| pytest 7.2+ | Marker inheritance now follows the full **MRO** in test classes | Markers | `#7792` |
| pytest 7.2+ | `@pytest.mark.parametrize` accepts any `Sequence[str]` for argnames (not just list/tuple) | Parametrize | `#10218` |
| pytest 7.2+ | `testpaths` supports shell-style wildcards | Config | `#9897` |
| pytest 7.2+ | `.pytest.ini` hidden config file accepted | Config | `#9987` |
| pytest 7.2+ | `--no-showlocals` (override `--showlocals` from addopts) | CLI | `#10381` |
| pytest 7.2+ | `pytest.raises` empty-tuple now errors with a helpful message | Assertions | `#8646` |
| pytest 7.2+ | Multiline display for `pytest.warns` match comparison | Assertions | `#8508` |
| pytest 7.2+ | **Deprecated:** running `nose`-style tests (`setup`/`teardown`, `@with_setup`) | Deprecation | `#9886` |
| pytest 7.2+ | **Deprecated:** configuring hookspecs/impls via marks/attributes (use `pytest.hookimpl`/`hookspec`) | Deprecation | `#4562` |
| pytest 7.2+ | **Deprecated:** returning non-`None` from a test function (warning) | Deprecation | `#7337` |
| pytest 7.3+ | `@classmethod` test methods are now discovered as tests | Collection | `#10525` |
| pytest 7.3+ | `tmp_path_retention_count` + `tmp_path_retention_policy` config | Config | `#8141` |
| pytest 7.3+ | `--log-disable` CLI option (disable individual loggers) | CLI | `#7431` |
| pytest 7.3+ | `console_output_style = progress-even-when-capture-no` | Config | `#10755` |
| pytest 7.3+ | Multiple teardown errors re-raised as an `ExceptionGroup` | Fixtures | `#10226` |
| pytest 7.4+ | `ExceptionInfo.from_exception()` (simpler than `from_exc_info()`) | Assertions | `#10901` |
| pytest 7.4+ | `caplog.set_level()`/`at_level()` temporarily re-enable a level disabled via `logging.disable()` | Built-in fixtures | `#8711` |
| pytest 8.0+ | **New-style hook wrappers** `@pytest.hookimpl(wrapper=True)` usable (needs `pytest>=8` / pluggy ≥1.2) | Hooks | `#11122` |
| pytest 8.0+ | Collection-tree node types `pytest.Directory` (base) + `pytest.Dir`; `pytest.Package` is no longer a `Module`/`File`; alphabetical collection | Collection | `#7777`, `#11137` |
| pytest 8.0+ | `pytest pkg/__init__.py` collects only that module (not the whole package) | Collection | `#8976` |
| pytest 8.0+ | `pytest_collect_directory` hook (customize directory collection) | Hooks | `#7777` |
| pytest 8.0+ | `ExceptionInfo.group_contains()` assertion helper for `ExceptionGroup` | Assertions | `#10441` |
| pytest 8.0+ | `pytest.raises(match=...)` also matches PEP-678 `__notes__` | Assertions | `#11227` |
| pytest 8.0+ | `verbosity_assertions` config + `config.get_verbosity()` (fine-grained verbosity) | Config | `#11387` |
| pytest 8.0+ | Colored/syntax-highlighted `-vv` diffs; improved container diffs | Assertions | `#11520`, `#1531` |
| pytest 8.0+ | `pytest.FixtureDef` exported for typing | API | `#7469` |
| pytest 8.0+ | **Breaking:** `pytest.warns` re-emits unmatched warnings on block exit | Assertions | `#9288` |
| pytest 8.0+ | **Deprecated:** applying a mark to a fixture (warning; **error in 9.0**) | Deprecation | `#3664` |
| pytest 8.1+ | `consider_namespace_packages` config (default `False`) | Config | `#11475` |
| pytest 8.1+ | `verbosity_test_cases` config (fine-grained test-case verbosity) | Config | `#11653` |
| pytest 8.1+ | `--log-file-mode` (`"w"`/`"a"`) for the logging plugin | CLI | `#11978` |
| pytest 8.1+ | `--import-mode=importlib` now uses the standard import mechanism (canonical module names) | Config | `#11475` |
| pytest 8.2+ | Read CLI args from a file: `pytest @args.txt` (one arg per line) | CLI | `#11871` |
| pytest 8.2+ | `PYTEST_VERSION` environment variable (set during the session) | API | `#9502` |
| pytest 8.2+ | `importorskip(exc_type=...)` parameter added; importorskip warns when a module raises `ImportError` (not `ModuleNotFoundError`) | Assertions | `#11523`; `outcomes.py` `versionadded:: 8.2` |
| pytest 8.2+ | **Deprecated:** `py.path.local` params for legacy hooks (warning; removed 9.0) | Deprecation | `#12069` |
| pytest 8.3+ | `--xfail-tb` (show tracebacks for XFAIL results) | CLI | `#12231` |
| pytest 8.3+ | **Keyword matching in `-m` marker expressions** (select by marker kwargs: int/str/bool/None) | Markers | `#12281` |
| pytest 8.3+ | `--no-fold-skipped` (list skipped tests individually) | CLI | `#12567` |
| pytest 8.4+ | **`pytest.RaisesGroup`** + **`pytest.RaisesExc`** — `raises`-equivalent for `ExceptionGroup`; `RaisesExc` is the new engine behind `raises` | Assertions | `#11538` |
| pytest 8.4+ | **`capteesys`** fixture — capture AND pass output through to the `--capture=` handler | Built-in fixtures | `#12081` |
| pytest 8.4+ | `@pytest.mark.xfail(raises=...)` accepts `RaisesGroup`/`RaisesExc` | Markers | `#12504` |
| pytest 8.4+ | `pytest.raises(check=fn)` — extra predicate the exception must satisfy | Assertions | `#13192` |
| pytest 8.4+ | `pytest.raises(match="")` now **warns** (empty pattern matches anything; use `match="^$"`) | Assertions | `#13192` |
| pytest 8.4+ | `pytest.HIDDEN_PARAM` usable in `pytest.param(id=...)` / `ids=` (hide a param set from the test name) | Parametrize | `#13228` |
| pytest 8.4+ | `collect_imported_tests` config (only collect tests defined in the file) | Config | `#12749` |
| pytest 8.4+ | `truncation_limit_lines` + `truncation_limit_chars` config | Config | `#12765` |
| pytest 8.4+ | `console_output_style = times` (per-test execution time) | Config | `#13125` |
| pytest 8.4+ | `--force-short-summary` (condensed summary regardless of verbosity) | CLI | `#12713` |
| pytest 8.4+ | `--disable-plugin-autoload` flag (CLI/addopts alt to `PYTEST_DISABLE_PLUGIN_AUTOLOAD`) | CLI | `#13253` |
| pytest 8.4+ | `pygments` is now a **required** dependency (output always highlighted unless `--code-highlight=no`) | CLI | `#7683` |
| pytest 8.4+ | **Breaking:** async test with no suitable plugin now **fails** (was warn+skip) | Collection | `#11372` |
| pytest 8.4+ | **Breaking:** returning non-`None` from a test now **fails** | Collection | `#12346` |
| pytest 8.4+ | **Breaking:** a `yield` in a test function is now an explicit error | Collection | `#12960` |
| pytest 9.0+ | **`subtests`** fixture + `pytest.Subtests` + `unittest` `subTest` support — *experimental*; merged into core from the `pytest-subtests` plugin | Built-in fixtures | `#1367` |
| pytest 9.0+ | **Native TOML config** — `[tool.pytest]` table + `pytest.toml`/`.pytest.toml` (vs. the bedrock `[tool.pytest.ini_options]` INI-compat mode) | Config | `#13743` |
| pytest 9.0+ | **Strict mode** — `strict` config option enables `strict_config`/`strict_markers`/`strict_parametrization_ids`/`strict_xfail` together; `--strict` flag re-enabled | Config | `#13823` |
| pytest 9.0+ | `strict_parametrization_ids` config (error on duplicate param-set IDs) | Parametrize | `#13737` |
| pytest 9.0+ | `strict_xfail`/`strict_config`/`strict_markers` — INI **aliases** of the bedrock `xfail_strict` ini / `--strict-config` / `--strict-markers` flags | Config | `#13823` |
| pytest 9.0+ | `faulthandler_exit_on_timeout` config (interrupt process on faulthandler timeout) | Config | `#13678` |
| pytest 9.0+ | `Parser.addini(aliases=...)` — plugins can register config-option aliases | Plugins | `#13829` |
| pytest 9.0+ | `consider_namespace_packages` now also affects `--pyargs` test discovery (PEP 420) | Config | `#478` |
| pytest 9.0+ | Terminal-tab progress (OSC 9;4) — **disabled by default since 9.0.2** except Windows; enable with `-p terminalprogress` | CLI | `#13072` |
| pytest 9.0+ | **Breaking:** overlapping path args dedup (`pytest a/ a/b` ≡ `pytest a`); `--keep-duplicates` restores old behavior | CLI | `#12083` |
| pytest 9.0+ | **Breaking:** Python 3.9 dropped → min Python **3.10** | Compat | `#13719` |
| pytest 9.0+ | **Breaking:** applying a mark to a fixture is now an **error** (was a warning since 8.0) | Markers | `#3664` |
| pytest 9.1+ | `pytest.register_fixture()` — imperative fixture registration (advanced/plugin) | Fixtures | `#12376` |
| pytest 9.1+ | `pytest.ScopeName` made public (usable in signatures) | API | `#14137` |
| pytest 9.1+ | `--max-warnings` CLI + `max_warnings` config (fail run over a warning threshold) | CLI | `#14371` |
| pytest 9.1+ | `--report-chars` long option (alias for the `-r` report-chars selector) | CLI | `#14023` |
| pytest 9.1+ | `assertion_text_diff_style` config (`Left:`/`Right:` blocks vs. `ndiff`) | Config | `#6757` |
| pytest 9.1+ | `pytest.approx` supports `datetime`/`timedelta` comparisons | Assertions | `#8395` |
| pytest 9.1+ | `pytest.warns` shows "Regex pattern did not match" when warnings fired but `match` failed | Assertions | `#11225` |
| pytest 9.1+ | `importorskip` **default `exc_type` narrowed to `ModuleNotFoundError`** — a broader `ImportError` (e.g. a broken optional dependency) now propagates instead of being silently skipped; opt back in with `exc_type=ImportError` | Assertions | `outcomes.py` `versionchanged:: 9.1` |
| pytest 9.1+ | Official Python 3.15 support | Compat | `#14524` |
| pytest 9.1+ | **Deprecated:** `--pastebin` (moved to the `pytest-pastebin` plugin) | Deprecation | `#14434` |
| pytest 9.1+ | **Deprecated:** `pytest.console_main` | Deprecation | `#1764` |
| pytest 9.1+ | **Deprecated:** `getfixturevalue()` during teardown for a not-yet-requested fixture (error in 10) | Deprecation | `#12882` |
| pytest 9.1+ | **Deprecated:** non-`Collection` iterables (generators/iterators) as parametrize `argvalues` (error in 10) | Deprecation | `#13409` |
| pytest 9.1+ | **Deprecated:** private `config.inicfg` (use `config.getini()`) | Deprecation | `#13946` |

## Commonly mis-pinned items (read before tagging)

These trip people up. The skill pins them as follows:

- **`pytest.RaisesGroup` / `pytest.RaisesExc` → 8.4** (`#11538`), *not* 9.x. `RaisesExc` is the
  engine `pytest.raises` now uses internally; `RaisesGroup` is the `ExceptionGroup` analog. The
  `xfail(raises=...)` acceptance of them is also 8.4 (`#12504`).
- **`capteesys` → 8.4** (`#12081`). It's the newest capture fixture; the rest (`capsys`/`capfd`/…)
  are bedrock.
- **`tmp_path` is bedrock (3.9)**, *not* a 7.x feature. `tmpdir` is **not deprecated** — only
  *discouraged* in favor of `tmp_path` (a 7.1.3 doc note, `#9937`). Neither carries a version tag.
  What *is* tagged is the retention config: `tmp_path_retention_count`/`_policy` → **7.3** (`#8141`).
- **`--import-mode=importlib` → 6.0 (bedrock)**, opt-in. The **default mode is still `prepend`**
  through 9.1 — importlib has *not* become the default. The 8.1 change (`#11475`) only made
  importlib *better* (standard import mechanism), and `consider_namespace_packages` → **8.1**.
- **`subtests` → 9.0 (core, experimental)** (`#1367`). It used to be the external `pytest-subtests`
  plugin and was merged into core in 9.0 — so for current pytest it *is* tagged `(pytest 9.0+)`,
  not treated as a third-party-only plugin. (`pytest-subtests` the plugin still has its own
  separate versioning if installed on older pytest.)
- **New-style hook wrappers `wrapper=True` → 8.0** (`#11122`). The old
  `@pytest.hookimpl(hookwrapper=True)` form is bedrock and **still supported** — it was not removed.
- **`--co` → bedrock (5.3 alias of `--collect-only`)** (`#6116`). Do not tag it.
- **`xfail` strict default is `False` and has never changed.** `xfail_strict` (ini) and
  `@pytest.mark.xfail(strict=True)` (per-mark) are bedrock. What's new is the **9.0** `strict_xfail`
  alias and the umbrella `strict` mode (`#13823`) — tag those, not "strict xfail" itself.
- **`pytest.raises(match=...)` / `pytest.warns(match=...)` are bedrock.** The `check=fn` parameter
  and the empty-`match` warning are the **8.4** additions (`#13192`).
- **Native TOML `[tool.pytest]` → 9.0** (`#13743`). The older `[tool.pytest.ini_options]` table in
  `pyproject.toml` is **bedrock (6.0)** — don't conflate them.
- **`required_plugins` → 6.0 (bedrock)** (`#7305`); **`--strict-markers`/`--strict-config` → 6.x
  (bedrock)**. The `strict_*` *ini aliases* are the 9.0 additions.
- **`importorskip` is a two-version split.** The **`exc_type=` parameter → 8.2** (`#11523`,
  `versionadded:: 8.2`). The **default behavior change → 9.1** (`versionchanged:: 9.1` in
  `src/_pytest/outcomes.py`): the default `exc_type` narrowed to `ModuleNotFoundError`, so a broader
  `ImportError` (e.g. a half-broken optional dependency) now *propagates* by default instead of being
  silently skipped. The 9.1 default-narrowing has **no dedicated changelog entry** — it's sourced
  from the function docstring, which overrides the changelog here. Don't collapse both to one version.

## Checking your version

```bash
pytest --version            # e.g. "pytest 9.1.0"
pytest --version --version  # also lists plugins and their versions (since 9.0, single --version is fast and plugin-free)
```

```python
import pytest

pytest.__version__          # "9.1.0"  (string)
pytest.version_tuple        # (9, 1, 0)  — numeric compare; added in pytest 7.0 (#8761)

# Robust runtime check independent of the pytest import:
from importlib.metadata import version
version("pytest")           # "9.1.0"
```

Gate behavior on the numeric tuple when you need to support multiple pytest versions:

```python
if pytest.version_tuple >= (8, 4):
    ...  # safe to use pytest.RaisesGroup
```

**Enforce a minimum in config** so the suite fails fast on too-old pytest, rather than erroring
mid-run (both are bedrock):

```ini
# pytest.ini  (or [tool.pytest.ini_options] in pyproject.toml)
[pytest]
minversion = 8.4
required_plugins = pytest-xdist>=3.0 pytest-cov
```

- `minversion` — pytest refuses to run if its own version is lower.
- `required_plugins` — pytest refuses to run unless the listed plugins (with optional version
  specifiers) are installed. Added in pytest 6.0 (`#7305`); supports version specifiers.

## Sources

All sourced from the **pytest repository** (`pytest-dev/pytest`), `doc/en/` docs and git tags:

- **`doc/en/changelog.rst`** (primary) — every row above cites its `#issue`/`#pr`; the per-version
  section headers (`pytest 9.1.0 (2026-06-13)`, `pytest 9.0.0 (2025-11-05)`, … down to
  `pytest 7.0.0 (2022-02-03)`) anchor the release dates. Mirror:
  <https://docs.pytest.org/en/stable/changelog.html>.
- **`doc/en/deprecations.rst`** — current deprecation/removal status (e.g. `tmpdir` is absent → not
  formally deprecated; the `--pastebin`, `console_main`, `config.inicfg` removal-in-10 entries).
  Mirror: <https://docs.pytest.org/en/stable/deprecations.html>.
- **`doc/en/backwards-compatibility.rst`** — the deprecation→error→removal scheme
  (`PytestRemovedInXWarning` becomes an error by default in `X.0`, feature removed in `X.1`).
- **git tags** (`git tag --sort=-creatordate`) — latest stable `9.1.0`; dev tip `9.2.0.dev0`; the
  yanked `8.1.0` (its features effectively shipped in `8.1.1`).
