"""Verify test-audit's smell scanner, seam finder, and the pattern examples in its reference."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/test-audit/skills/test-audit"
SMELLS = SKILL / "scripts/scan_smells.py"
SEAMS = SKILL / "scripts/find_seams.py"
PATTERNS = SKILL / "references/patterns.md"

spec = importlib.util.spec_from_file_location("scan_smells", SMELLS)
assert spec and spec.loader
smells = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smells)


def child_env(**extra: str) -> dict[str, str]:
    # The outer pytest-cov session must not configure or measure a child run.
    env = {k: v for k, v in os.environ.items() if not k.startswith(("COV_CORE_", "COVERAGE_"))}
    env.update(extra)
    return env


def write(root: Path, files: dict[str, str]) -> Path:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content))
    return root


def run(script: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        env=child_env(),
        capture_output=True,
        text=True,
        check=False,
    )


def findings(path: Path, *args: str) -> set[tuple[str, str]]:
    """(code, test) for every finding the scanner reports on a file."""
    result = run(SMELLS, path.parent, path.name, "--json", *args)
    assert result.returncode in (0, 1), result.stderr
    return {(f["code"], f["test"]) for f in json.loads(result.stdout)["findings"]}


def seams(root: Path, *args: str) -> dict[str, list[str]]:
    """qualname -> tags for every candidate the seam finder reports."""
    result = run(SEAMS, root, *args, "--json")
    assert result.returncode in (0, 1), result.stderr
    return {c["qualname"]: c["tags"] for c in json.loads(result.stdout)["candidates"]}


# scan_smells.py ---------------------------------------------------------------------------

NO_ASSERT = """
import pytest
from unittest import TestCase


def check(value):
    assert value


def check_twice(value):
    check(value)


@pytest.fixture
def verified():
    assert True
    return 1


def test_nothing():
    int("1")


def test_assert():
    assert int("1") == 1


def test_helper():
    check_twice(1)


def test_fixture(verified):
    int("1")


def test_raise_assertion_error():
    if int("1") != 1:
        raise AssertionError("bad")


def test_raises():
    with pytest.raises(ValueError):
        int("x")


def test_external_helper(client):
    client.get_success_response("slug")


def test_constructs_a_test_client(app, TestClient):
    TestClient(app).get("/")


@pytest.mark.skip(reason="later")
def test_skipped_by_marker():
    int("1")


def test_skipped_in_body():
    pytest.skip("later")


class WidgetTest(TestCase):
    def test_unittest_assert(self):
        self.assertEqual(int("1"), 1)

    def test_delegates(self):
        self.test_unittest_assert()

    def test_nothing_either(self):
        int("1")


class Helper:
    def test_not_collected(self):
        int("1")
"""


def test_no_assert_sees_local_helpers_fixtures_and_delegation(tmp_path: Path) -> None:
    path = write(tmp_path, {"test_mod.py": NO_ASSERT}) / "test_mod.py"
    flagged = {test for code, test in findings(path) if code == "no-assert"}
    assert flagged == {
        "test_nothing",
        "test_external_helper",
        "test_constructs_a_test_client",
        "WidgetTest::test_nothing_either",
    }


def test_assert_helper_names_helpers_from_other_files(tmp_path: Path) -> None:
    path = write(tmp_path, {"test_mod.py": NO_ASSERT}) / "test_mod.py"
    flagged = {t for c, t in findings(path, "--assert-helper", "^get_success") if c == "no-assert"}
    assert "test_external_helper" not in flagged


COMPARISONS = """
from unittest import TestCase


class Invoice:
    total = 5


def test_attribute_itself(invoice):
    assert invoice.total == invoice.total


def test_bare_name_is_left_to_ruff(x):
    assert x == x


def test_constructor_equality():
    assert Invoice() == Invoice()


def test_through_a_local(invoice):
    total = invoice.total
    assert invoice.total == total


def test_expected_from_code_under_test(slug):
    expected = slug("A B")
    assert slug("A B") == expected


def test_idempotent(ensure):
    first = ensure()
    second = ensure()
    assert first.id == second.id


def test_state_changes_between(count, act):
    before = count()
    act()
    after = count()
    assert before == after


def test_call_in_an_assignment_between(count, act):
    initial = count()
    response = act()
    final = count()
    assert final == initial


def test_different_sides(slug):
    assert slug("a") == slug("b")


class InvoiceTest(TestCase):
    def test_unittest_itself(self):
        self.assertEqual(self.invoice.total, self.invoice.total)
"""


def test_self_compare_and_repeat_call(tmp_path: Path) -> None:
    path = write(tmp_path, {"test_cmp.py": COMPARISONS}) / "test_cmp.py"
    assert findings(path) == {
        ("self-compare", "test_attribute_itself"),
        ("self-compare", "test_through_a_local"),
        ("self-compare", "InvoiceTest::test_unittest_itself"),
        ("repeat-call", "test_expected_from_code_under_test"),
        ("repeat-call", "test_idempotent"),
    }


DUPLICATES = """
import pytest


def test_first():
    assert int("1") == 1


def test_copy():
    '''A docstring does not make a body different.'''
    assert int("1") == 1


@pytest.mark.slow
def test_marked_copy():
    assert int("1") == 1


class TestOne:
    def test_first(self):
        assert int("1") == 1


class TestTwo:
    def test_first(self):
        assert int("1") == 1

    def test_again(self):
        assert int("1") == 1
"""


def test_dup_body_compares_within_one_class_or_module(tmp_path: Path) -> None:
    path = write(tmp_path, {"test_dup.py": DUPLICATES}) / "test_dup.py"
    found = {(code, test) for code, test in findings(path) if code == "dup-body"}
    assert found == {("dup-body", "test_copy"), ("dup-body", "TestTwo::test_again")}


READS = """
import inspect
from pathlib import Path

import app


def test_getsource():
    assert "timeout" in inspect.getsource(app.fetch)


def test_open_literal():
    assert "timeout" in open("app/client.py").read()


def test_module_file():
    assert "timeout" in Path(app.__file__).read_text()


def test_own_file_as_sample_bytes():
    with open(__file__, "rb") as handle:
        assert app.upload(handle)


def test_path_as_data():
    assert app.program_name(Path("example.py")) == "example.py"
"""


def test_reads_source(tmp_path: Path) -> None:
    path = write(tmp_path, {"test_src.py": READS}) / "test_src.py"
    assert {t for c, t in findings(path) if c == "reads-source"} == {
        "test_getsource",
        "test_open_literal",
        "test_module_file",
    }


def test_directory_scan_select_and_exit_codes(tmp_path: Path) -> None:
    write(
        tmp_path,
        {
            "tests/test_a.py": "def test_a():\n    int('1')\n",
            "tests/b_test.py": "def test_b():\n    assert 1 == int('1')\n",
            "tests/helpers.py": "def test_not_a_test_file():\n    int('1')\n",
            "tests/test_broken.py": "def test_(:\n",
        },
    )
    result = run(SMELLS, tmp_path, "tests")
    assert result.returncode == 1
    assert "tests/test_a.py:1: no-assert test_a" in result.stdout
    assert result.stdout.splitlines()[-1] == "2 tests scanned; 1 no-assert"
    assert "skipped tests/test_broken.py" in result.stderr

    assert run(SMELLS, tmp_path, "tests", "--select", "dup-body").returncode == 0
    for bad in (["tests", "--select", "nope"], ["missing"]):
        assert run(SMELLS, tmp_path, *bad).returncode == 2


# find_seams.py ----------------------------------------------------------------------------

PROJECT = {
    "src/pkg/__init__.py": """
        __all__ = ["public_only_tests"]
        from pkg.core import used
    """,
    "src/pkg/core.py": '''
        """Mentions only_in_docstring in prose."""
        import functools

        from pkg.registry import task


        def used():
            return _helper()


        def _helper():
            return 1


        def _reset_for_tests():
            _reset_for_tests.calls = 0


        def recursive(n):
            return recursive(n - 1) if n else 0


        def public_only_tests():
            return 2


        def only_in_docstring():
            return 3


        def by_getattr():
            return 4


        def lookup():
            return getattr(__import__("pkg.core"), "by_getattr")


        @task
        def scheduled():
            return 5


        @functools.lru_cache
        def cached_only_tests():
            return 6


        class Handler:
            def to_representation(self):
                return 7

            def custom_only_tests(self):
                return 8


        class OtherHandler:
            def to_representation(self):
                return 9


        FLAG_FOR_TESTS = True
    ''',
    "src/pkg/registry.py": """
        def task(fn):
            return fn
    """,
    "src/pkg/testutils/fixtures.py": """
        from pkg.core import _reset_for_tests


        def fresh():
            _reset_for_tests()
    """,
    "tests/test_core.py": """
        from pkg import core


        def test_everything():
            core.used()
            core._helper()
            core.recursive(2)
            core.public_only_tests()
            core.only_in_docstring()
            core.by_getattr()
            core.scheduled()
            core.cached_only_tests()
            core.Handler().to_representation()
            core.Handler().custom_only_tests()
            assert core.FLAG_FOR_TESTS
    """,
}


def test_seams_lists_test_only_symbols_with_reachability_tags(tmp_path: Path) -> None:
    root = write(tmp_path / "tests" / "checkout", PROJECT)
    assert seams(root, "--src", "src", "--tests", "tests") == {
        "_reset_for_tests": ["private"],
        "recursive": [],
        "public_only_tests": ["exported"],
        "only_in_docstring": [],
        "by_getattr": ["string"],
        "scheduled": ["decorated"],
        "cached_only_tests": [],
        "Handler": [],
        "Handler.to_representation": ["override"],
        "OtherHandler.to_representation": ["override"],
        "Handler.custom_only_tests": [],
        "FLAG_FOR_TESTS": [],
    }


def test_seams_ranks_untagged_first_and_counts_consumers(tmp_path: Path) -> None:
    root = write(tmp_path, PROJECT)
    result = run(SEAMS, root, "--src", "src", "--tests", "tests", "--json")
    ranked = [c["qualname"] for c in json.loads(result.stdout)["candidates"]]
    assert ranked[0] == "_reset_for_tests"
    assert ranked.index("recursive") < ranked.index("by_getattr")

    write(root, {"consumer/use.py": "from pkg.core import recursive\n"})
    assert "recursive" not in seams(root, "--src", "src", "consumer", "--tests", "tests")


def test_seams_text_output_and_exit_codes(tmp_path: Path) -> None:
    root = write(tmp_path, PROJECT)
    result = run(SEAMS, root, "--src", "src", "--tests", "tests")
    assert result.returncode == 1
    assert "src/pkg/core.py:16: function _reset_for_tests [private]" in result.stdout
    assert result.stdout.splitlines()[-1].endswith("12 referenced only by tests")

    clean = write(tmp_path / "clean", {"src/m.py": "def f():\n    return f\n", "tests/t.py": ""})
    assert run(SEAMS, clean, "--src", "src", "--tests", "tests").returncode == 0
    assert run(SEAMS, clean, "--src", "missing", "--tests", "tests").returncode == 2


# references/patterns.md -------------------------------------------------------------------


def pattern_module(tmp_path: Path) -> Path:
    blocks = re.findall(r"^```python\n(.*?)^```", PATTERNS.read_text(), re.M | re.S)
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    path = tmp_path / "test_patterns.py"
    path.write_text("\n\n".join(blocks))
    return path


def outcomes(path: Path, broken: str) -> dict[str, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-rA", "-q", path.name],
        cwd=path.parent,
        env=child_env(BROKEN=broken),
        capture_output=True,
        text=True,
        check=False,
    )
    lines = re.findall(r"^(PASSED|FAILED) \S+::(\w+)", result.stdout, re.M)
    return {test: outcome for outcome, test in lines}


def test_pattern_examples_hold_both_ways(tmp_path: Path) -> None:
    path = pattern_module(tmp_path)
    working = outcomes(path, "0")
    assert working and set(working.values()) == {"PASSED"}
    broken = outcomes(path, "1")
    assert broken.keys() == working.keys()
    for test, outcome in broken.items():
        assert outcome == ("FAILED" if test.endswith("_fixed") else "PASSED"), test


def test_pattern_detectors_find_their_weak_tests(tmp_path: Path) -> None:
    path = pattern_module(tmp_path)
    assert findings(path) == {
        ("no-assert", "test_add_weak"),
        ("self-compare", "test_invoice_total_weak"),
        ("repeat-call", "test_slug_weak"),
        ("repeat-call", "test_cache_key_weak"),
        ("dup-body", "test_decode_explicit_encoding_weak"),
    }


@pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff is not installed")
def test_pattern_ruff_rules_find_their_weak_tests(tmp_path: Path) -> None:
    path = pattern_module(tmp_path)
    result = subprocess.run(
        ["ruff", "check", "--isolated", "--output-format", "json", "--select"]
        + ["PT011,PT012,PT017,B015,F631,PLR0124", path.name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    lines = path.read_text().splitlines()

    def test_at(line: int) -> str:
        return next(
            re.sub(r"def (\w+).*", r"\1", s.strip())
            for s in reversed(lines[:line])
            if s.startswith("def ")
        )

    reported: set[tuple[str, str]] = {
        (d["code"], test_at(d["location"]["row"])) for d in json.loads(result.stdout)
    }
    assert reported == {
        ("B015", "test_add_weak"),
        ("PT011", "test_overdraw_weak"),
        ("PT011", "test_port_range_weak"),
        ("PT012", "test_port_range_weak"),
    }


def smell_codes_documented(text: str) -> set[str]:
    return set(re.findall(r"`(no-assert|self-compare|repeat-call|dup-body|reads-source)`", text))


def test_skill_documents_every_scanner_code() -> None:
    documented = smell_codes_documented((SKILL / "SKILL.md").read_text())
    assert documented == set(smells.CODES)


def test_json_output_counts_tests_and_records_fields(tmp_path: Path) -> None:
    path = write(tmp_path, {"test_mod.py": NO_ASSERT}) / "test_mod.py"
    result = run(SMELLS, tmp_path, path.name, "--json")
    data: dict[str, Any] = json.loads(result.stdout)
    assert data["tests"] == 13
    assert set(data["findings"][0]) == {"file", "line", "code", "test", "message"}
