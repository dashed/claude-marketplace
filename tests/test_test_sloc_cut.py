"""Verify test-sloc-cut's coverage map against real per-test pytest-cov runs."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/test-sloc-cut/skills/test-sloc-cut"
SCRIPT = SKILL / "scripts/coverage_map.py"
REFERENCE = SKILL / "references/coverage-and-mutants.md"
FIXTURE = json.loads((ROOT / "tests/fixtures/test-sloc-cut.json").read_text())
spec = importlib.util.spec_from_file_location("coverage_map", SCRIPT)
assert spec and spec.loader
cmap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cmap)

RCFILE = """[run]
branch = True
relative_files = True
data_file = {data_file}
parallel = False
include =
{include}

[json]
show_contexts = True
"""
CALC = ["pkg/calc.py", "pkg/fmt.py"]
COVER_TESTS = [
    "tests/test_calc.py::test_bad_discount",
    "tests/test_calc.py::test_premium",
    "tests/test_calc.py::test_label_neg",
    "tests/test_calc.py::test_bulk",
]


def child_env() -> dict[str, str]:
    # The outer pytest-cov session must not configure or measure the child run.
    return {k: v for k, v in os.environ.items() if not k.startswith(("COV_CORE_", "COVERAGE_"))}


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    for name, content in FIXTURE["files"].items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return root


def measure(project: Path, modules: list[str], *tests: str) -> None:
    """Run the documented serial per-test-context pytest command into project/scratch."""
    scratch = project / "scratch"
    scratch.mkdir(exist_ok=True)
    include = "\n".join(f"    */{m}" for m in modules)
    rcfile = RCFILE.format(data_file=scratch / ".coverage", include=include)
    (scratch / ".coveragerc").write_text(rcfile)
    (scratch / ".coverage").unlink(missing_ok=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-q",
            "--cov",
            "--cov-config=scratch/.coveragerc",
            "--cov-context=test",
            "--cov-report=",
            *tests,
        ],
        cwd=project,
        env=child_env(),
        check=True,
        capture_output=True,
        text=True,
    )


def run_map(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=project,
        env=child_env(),
        capture_output=True,
        text=True,
        check=False,
    )


def report(project: Path, name: str = "analysis.json") -> dict[str, Any]:
    return json.loads((project / "scratch" / name).read_text())


def documented_output(command: str) -> str:
    """Return the lines the reference prints after `$ command`, up to the next prompt or fence.

    Blocks nested in a list item are indented; that indent is removed.
    """
    lines = REFERENCE.read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == f"$ {command}")
    indent = len(lines[start]) - len(lines[start].lstrip())
    end = start + 1
    while not lines[end].strip().startswith(("$ ", "```")):
        end += 1
    return "".join(f"{line[indent:]}\n" for line in lines[start + 1 : end])


def jq_unique(data: dict[str, Any]) -> str:
    """What `jq -r '.per_test | to_entries[] | "\\(.key): \\(.value.unique)"'` prints."""
    return "".join(
        f"{test}: {json.dumps(v['unique'], separators=(',', ':'))}\n"
        for test, v in data["per_test"].items()
    )


def test_reference_output_blocks_match_real_runs(project: Path) -> None:
    measure(project, CALC, "tests/test_calc.py")
    baseline = ["--scratch", "scratch", "--out", "scratch/baseline.json", *CALC]
    result = run_map(project, *baseline)
    assert result.returncode == 0, result.stderr
    assert result.stdout == documented_output(
        "python3 scripts/coverage_map.py " + " ".join(baseline)
    )
    jq = (
        """jq -r '.per_test | to_entries[] | "\\(.key): \\(.value.unique)"' scratch/baseline.json"""
    )
    assert jq_unique(report(project, "baseline.json")) == documented_output(jq)

    measure(project, CALC, *COVER_TESTS)
    cover = ["--scratch", "scratch", "--out", "scratch/cover.json", *CALC]
    result = run_map(project, *cover)
    assert result.stdout == documented_output("python3 scripts/coverage_map.py " + " ".join(cover))
    diff = ["--diff", "scratch/baseline.json", "scratch/cover.json"]
    result = run_map(project, *diff)
    assert result.returncode == 0
    assert result.stdout == documented_output("python3 scripts/coverage_map.py " + " ".join(diff))

    measure(
        project, CALC, "tests/test_calc.py", "--deselect", "tests/test_calc.py::test_bad_discount"
    )
    run_map(project, "--scratch", "scratch", "--out", "scratch/after.json", *CALC)
    diff = ["--diff", "scratch/baseline.json", "scratch/after.json"]
    result = run_map(project, *diff)
    assert result.returncode == 1
    assert result.stdout == documented_output("python3 scripts/coverage_map.py " + " ".join(diff))


@pytest.mark.parametrize(
    ("module", "tests"),
    [("pkg/store.py", "tests/test_store.py"), ("pkg/loops.py", "tests/test_loops.py")],
)
def test_trap_output_blocks_match_real_runs(project: Path, module: str, tests: str) -> None:
    measure(project, [module], tests)
    result = run_map(project, "--scratch", "scratch", module)
    assert result.returncode == 0, result.stderr
    command = f"python3 scripts/coverage_map.py --scratch scratch {module}"
    assert result.stdout == documented_output(command)


def test_fixture_phases_belong_to_their_test(project: Path) -> None:
    measure(project, ["pkg/store.py"], "tests/test_store.py")
    assert run_map(project, "--scratch", "scratch", "pkg/store.py").returncode == 0
    per_test = report(project)["per_test"]
    assert set(per_test) == {
        "tests/test_store.py::test_lookup_memory",
        "tests/test_store.py::test_lookup_remote",
    }
    memory = per_test["tests/test_store.py::test_lookup_memory"]
    assert set(memory["phases"]) == {"setup", "run", "teardown"}
    # Only the fixture reaches the memory branch and close(); the body reaches nothing unique.
    assert memory["unique"]
    assert all(item.endswith(" (fixture)") for item in memory["unique"])
    assert {"pkg/store.py:3 (fixture)", "pkg/store.py:9 (fixture)"} <= set(memory["unique"])
    assert memory["lines"]["pkg/store.py"] == [2, 3, 8, 9, 10, 14]


def test_deleting_a_fixture_owner_is_reported_as_a_loss(project: Path) -> None:
    measure(project, ["pkg/store.py"], "tests/test_store.py")
    run_map(project, "--scratch", "scratch", "--out", "scratch/baseline.json", "pkg/store.py")
    measure(project, ["pkg/store.py"], "tests/test_store.py::test_lookup_remote")
    run_map(project, "--scratch", "scratch", "--out", "scratch/after.json", "pkg/store.py")
    result = run_map(project, "--diff", "scratch/baseline.json", "scratch/after.json")
    assert result.returncode == 1
    assert "  lost: pkg/store.py:3\n" in result.stdout
    assert "  lost: pkg/store.py:9\n" in result.stdout


def test_subline_sites_are_listed_for_coverage_redundant_tests(project: Path) -> None:
    measure(project, ["pkg/loops.py"], "tests/test_loops.py")
    run_map(project, "--scratch", "scratch", "pkg/loops.py")
    per_test = report(project)["per_test"]
    zero = per_test["tests/test_loops.py::test_total_zero"]
    default = per_test["tests/test_loops.py::test_pick_default"]
    # Each is the only test of its outcome, yet coverage sees nothing unique in either.
    assert zero["unique"] == [] and zero["subline"] == ["pkg/loops.py:3 for"]
    assert default["unique"] == [] and default["subline"] == ["pkg/loops.py:9 or"]


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("for x in xs:\n    pass\n", {1: {"for"}}),
        ("y = [\n    v\n    for v in xs\n    if v\n]\n", {1: {"comprehension"}}),
        ("y = a and (b or c)\n", {1: {"and", "or"}}),
        ("y = (\n    a\n    if b\n    else c\n)\n", {1: {"ternary"}}),
        ("f = lambda: 1\n", {1: {"lambda"}}),
        ("match x:\n    case 1 if y:\n        pass\n", {2: {"match guard"}}),
        ("if a:\n    b = 1\n", {}),
    ],
)
def test_subline_sites_map_to_the_statement_first_line(
    source: str, expected: dict[int, set[str]]
) -> None:
    assert dict(cmap.subline_sites(source)) == expected


def fake_report(items: list[str], source: str = "abc") -> dict[str, Any]:
    return {
        "schema_version": cmap.SCHEMA_VERSION,
        "modules": {"pkg/m.py": {"covered_items": items}},
        "provenance": {
            "coverage": "7.0",
            "python": "3.12",
            "modules": {"pkg/m.py": source},
            "ranges": {},
        },
    }


def test_diff_compares_items_not_counts() -> None:
    base = fake_report(["pkg/m.py:1->2", "pkg/m.py:1"])
    swapped = fake_report(["pkg/m.py:1->3", "pkg/m.py:1"])
    code, lines = cmap.diff_reports(base, swapped)
    assert code == 1
    assert "  lost: pkg/m.py:1->2" in lines and "  gained: pkg/m.py:1->3" in lines
    assert cmap.diff_reports(base, copy.deepcopy(base))[0] == 0
    assert (
        cmap.diff_reports(base, fake_report([*base["modules"]["pkg/m.py"]["covered_items"], "x"]))[
            0
        ]
        == 0
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r["provenance"]["modules"].update({"pkg/m.py": "changed"}),
        lambda r: r["provenance"].update({"coverage": "7.1"}),
        lambda r: r["provenance"].update({"ranges": {"pkg/m.py": [1, 5]}}),
        lambda r: r.pop("schema_version"),
    ],
    ids=["source", "coverage", "range", "schema"],
)
def test_diff_refuses_incomparable_reports(change: Any) -> None:
    base = fake_report(["pkg/m.py:1"])
    after = copy.deepcopy(base)
    change(after)
    code, lines = cmap.diff_reports(base, after)
    assert code == 2 and lines


def test_changed_production_source_blocks_the_diff(project: Path) -> None:
    measure(project, ["pkg/store.py"], "tests/test_store.py")
    run_map(project, "--scratch", "scratch", "--out", "scratch/baseline.json", "pkg/store.py")
    with (project / "pkg/store.py").open("a") as source:
        source.write("\n# edited after the baseline\n")
    measure(project, ["pkg/store.py"], "tests/test_store.py")
    run_map(project, "--scratch", "scratch", "--out", "scratch/after.json", "pkg/store.py")
    result = run_map(project, "--diff", "scratch/baseline.json", "scratch/after.json")
    assert result.returncode == 2
    assert "pkg/store.py: source differs" in result.stderr


def test_missing_contexts_and_usage_errors_exit_2(project: Path) -> None:
    scratch = project / "scratch"
    scratch.mkdir()
    rcfile = RCFILE.format(data_file=scratch / ".coverage", include="    */pkg/loops.py")
    (scratch / ".coveragerc").write_text(rcfile)
    subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--cov",
         "--cov-config=scratch/.coveragerc", "--cov-report=", "tests/test_loops.py"],
        cwd=project, env=child_env(), check=True, capture_output=True,
    )  # fmt: skip
    result = run_map(project, "--scratch", "scratch", "pkg/loops.py")
    assert result.returncode == 2 and "no per-test contexts" in result.stderr
    assert run_map(project, "--diff", "a.json").returncode == 2
    assert run_map(project, "--scratch", "scratch").returncode == 2


def test_reference_names_every_trap_the_skill_counts() -> None:
    traps = REFERENCE.read_text().split("## Traps that produce a wrong map", 1)[1].split("\n## ")[0]
    count = len(re.findall(r"^- \*\*", traps, re.MULTILINE))
    words = {6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
    assert f"the {words[count]} traps" in (SKILL / "SKILL.md").read_text()


fm_spec = importlib.util.spec_from_file_location("fact_matrix", SKILL / "scripts/fact_matrix.py")
assert fm_spec and fm_spec.loader
fmat = importlib.util.module_from_spec(fm_spec)
fm_spec.loader.exec_module(fmat)

CALC_FACTS = {
    "F1": {"proposition": "a premium order of 2 costs 40", "kind": "eq"},
    "F2": {"proposition": "a bulk order of 3 with 10% off costs 22", "kind": "eq"},
    "F3": {"proposition": "an unparsable discount prices as None", "kind": "eq"},
    "F4": {"proposition": "a negative number is labelled neg", "kind": "eq"},
}
CALC_MAPPING = {
    "test_premium": ["F1"],
    "test_premium_again": ["F1"],
    "test_bulk": ["F2"],
    "test_bad_discount": ["F3"],
    "test_label_neg": ["F4"],
}


def filled_matrix(project: Path, name: str = "matrix.json") -> dict[str, Any]:
    """Seed the calc tests and map every site as the fact-matrix agent would."""
    assert fmat.main(["seed", "tests/test_calc.py", "--out", name]) == 0
    matrix = json.loads((project / name).read_text())
    matrix["facts"] = copy.deepcopy(CALC_FACTS)
    for site in matrix["sites"]:
        site["facts"] = CALC_MAPPING[site["test"].rsplit("::", 1)[1]]
    return matrix


def save(project: Path, name: str, matrix: dict[str, Any]) -> str:
    (project / name).write_text(json.dumps(matrix))
    return name


def test_seed_finds_every_kind_of_assertion_site(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(project)
    (project / "tests/test_kinds.py").write_text(
        "import pytest\n"
        "from unittest import TestCase, mock\n"
        "\n"
        "\n"
        "def check_positive(x):\n"
        "    assert x > 0\n"
        "\n"
        "\n"
        "def test_plain():\n"
        "    value = 2\n"
        "    assert value == 2\n"
        "    with pytest.raises(ValueError):\n"
        "        int('x')\n"
        "    check_positive(value)\n"
        "\n"
        "\n"
        "class TestMethods(TestCase):\n"
        "    def test_methods(self):\n"
        "        m = mock.Mock()\n"
        "        m(1)\n"
        "        m.assert_called_once_with(1)\n"
        "        self.assertEqual(1, 1)\n"
    )
    assert fmat.main(["seed", "tests/test_kinds.py", "--out", "kinds.json"]) == 0
    sites = json.loads((project / "kinds.json").read_text())["sites"]
    assert [(s["test"].split("::", 1)[1], s["line"], s["kind_hint"]) for s in sites] == [
        ("test_plain", 11, "assert"),
        ("test_plain", 12, "expects"),
        ("test_plain", 14, "helper:check_positive"),
        ("TestMethods::test_methods", 21, "assert-call"),
        ("TestMethods::test_methods", 22, "assert-call"),
    ]
    assert sites[0]["text"] == "assert value == 2" and sites[0]["facts"] == []
    assert fmat.main(["seed", "tests/test_kinds.py", "--out", "kinds.json"]) == 2


def test_check_passes_a_complete_matrix_and_names_single_pinned_facts(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(project)
    name = save(project, "matrix.json", filled_matrix(project, "seed.json"))
    assert fmat.main(["check", name]) == 0
    out = capsys.readouterr().out
    assert "single-pinned (do not touch): F2, F3, F4" in out
    assert "asserted by several tests: F1" in out


@pytest.mark.parametrize(
    ("break_it", "message"),
    [
        (lambda m: m["sites"][0].update(facts=[]), "unmapped"),
        (lambda m: m["sites"][0].update(facts=["F9"]), "unknown facts"),
        (lambda m: m["sites"][0].update(text="assert something else"), "anchor text"),
        (lambda m: m["sites"][0].update(line=1), "not inside test"),
        (lambda m: m["facts"].update(F5={"proposition": "orphan", "kind": "eq"}), "no site"),
        (lambda m: m["facts"]["F1"].update(kind="roughly"), "kind"),
        (lambda m: m["facts"]["F1"].update(kind="absent"), "window"),
        (lambda m: m["facts"]["F1"].update(questions=["which currency?"]), "open questions"),
        (lambda m: m["facts"]["F2"].update(kind="truthy", subsumed_by="F2"), "stronger"),
    ],
    ids=[
        "unmapped",
        "unknown",
        "anchor",
        "span",
        "orphan",
        "kind",
        "window",
        "question",
        "subsume",
    ],
)
def test_check_reports_each_violation(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    break_it: Any,
    message: str,
) -> None:
    monkeypatch.chdir(project)
    matrix = filled_matrix(project, "seed.json")
    break_it(matrix)
    assert fmat.main(["check", save(project, "matrix.json", matrix)]) == 1
    assert message in capsys.readouterr().out


def test_a_no_fact_reason_maps_a_site(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(project)
    matrix = filled_matrix(project, "seed.json")
    matrix["sites"][0].update(facts=[], no_fact="setup sanity check, not a behavior")
    matrix["sites"][1].update(facts=["F1"])
    assert fmat.main(["check", save(project, "matrix.json", matrix)]) == 0


def test_check_refuses_a_matrix_seeded_from_another_version(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(project)
    name = save(project, "matrix.json", filled_matrix(project, "seed.json"))
    with (project / "tests/test_calc.py").open("a") as tests:
        tests.write("\n# edited after seeding\n")
    assert fmat.main(["check", name]) == 2


def test_coverage_join_flags_a_fact_its_tests_never_run(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    measure(project, CALC, "tests/test_calc.py")
    run_map(project, "--scratch", "scratch", *CALC)
    monkeypatch.chdir(project)
    matrix = filled_matrix(project, "seed.json")
    # test_label_neg runs the "neg" return (line 3) but never the "pos" return (line 4).
    matrix["facts"]["F4"]["production"] = [
        {"file": "pkg/fmt.py", "line": 3, "text": 'return "neg"'}
    ]
    ok = save(project, "ok.json", matrix)
    assert fmat.main(["check", ok, "--coverage", "scratch/analysis.json"]) == 0
    matrix["facts"]["F4"]["production"] = [
        {"file": "pkg/fmt.py", "line": 4, "text": 'return "pos"'}
    ]
    wrong = save(project, "wrong.json", matrix)
    assert fmat.main(["check", wrong, "--coverage", "scratch/analysis.json"]) == 1
    assert "F4: no test asserting it runs pkg/fmt.py:4" in capsys.readouterr().out


def test_seed_from_a_baseline_keeps_unchanged_mappings(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(project)
    baseline = save(project, "baseline.json", filled_matrix(project, "seed.json"))
    tests = project / "tests/test_calc.py"
    source = tests.read_text()
    source = source.replace(
        'def test_premium_again():\n    assert price("premium", 2, "0") == 40\n\n\n', ""
    )
    tests.write_text(source.replace('"ten") is None', '"ten") is None  # unparsable'))
    assert fmat.main(["seed", "tests/test_calc.py", "--out", "after.json", "--from", baseline]) == 0
    assert "sites=4 carried=3" in capsys.readouterr().out
    after = json.loads((project / "after.json").read_text())
    unmapped = [s["test"] for s in after["sites"] if not s["facts"]]
    assert unmapped == ["tests/test_calc.py::test_bad_discount"]


def test_compare_accepts_a_cut_that_keeps_every_fact(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(project)
    base = filled_matrix(project, "seed.json")
    after = copy.deepcopy(base)
    after["sites"] = [s for s in after["sites"] if not s["test"].endswith("test_premium_again")]
    assert fmat.compare(base, after) == []


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        (lambda m: m["sites"].pop(2), "lost: F2"),
        (lambda m: m["facts"]["F2"].update(kind="truthy"), "weakened: F2"),
        (
            lambda m: m["sites"][2].update(test="tests/test_calc.py::test_premium"),
            "moved without a mutant: F2",
        ),
    ],
    ids=["lost", "weakened", "moved"],
)
def test_compare_reports_lost_weakened_and_unproven_facts(
    project: Path, monkeypatch: pytest.MonkeyPatch, change: Any, problem: str
) -> None:
    monkeypatch.chdir(project)
    base = filled_matrix(project, "seed.json")
    after = copy.deepcopy(base)
    change(after)
    assert any(p.startswith(problem) for p in fmat.compare(base, after))


def test_a_recorded_mutant_licenses_a_moved_fact(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(project)
    base = filled_matrix(project, "seed.json")
    after = copy.deepcopy(base)
    after["sites"][2]["test"] = "tests/test_calc.py::test_premium"
    after["facts"]["F2"]["mutant"] = "bulk rate 8 -> 9; test_premium fails"
    assert fmat.compare(base, after) == []
