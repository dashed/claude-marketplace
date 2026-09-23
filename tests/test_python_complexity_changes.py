"""Offline tests for paired before/after Jev review and its evaluation controls."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.eval_python_complexity import behavior_check
from scripts.eval_python_complexity_changes import (
    FIXTURES,
    ROOT,
    RUBRIC,
    controls,
    mirrored,
    score,
    static_separability,
    validate_fixtures,
)

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "plugins/python-complexity/skills/python-complexity/scripts/jev_review.py"
)
spec = importlib.util.spec_from_file_location("jev_review_changes", SCRIPT)
assert spec is not None and spec.loader is not None
jev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jev)
QUESTIONS = json.loads(RUBRIC.read_text())["questions"]


@pytest.fixture(autouse=True)
def isolated_user_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jev, "DEFAULT_CONFIG", tmp_path / "no-user-config.json")


def version(content: str, **contract: Any) -> dict[str, Any]:
    return {
        "scope": "price.py:price",
        "sources": [{"path": "price.py", "content": content}],
        "measurements": {"defs": 1},
        **contract,
    }


CONTRACT = {"task": "Price an order.", "constraints": ["Keep the signature."]}


def test_rubric_directions_mirror_each_other() -> None:
    # The swap control relies on every introduced_X having a removed_X about the same property.
    introduced = {n.removeprefix("introduced_") for n in QUESTIONS if n.startswith("introduced_")}
    removed = {n.removeprefix("removed_") for n in QUESTIONS if n.startswith("removed_")}
    assert introduced == removed and len(introduced) == 4
    for name, question in QUESTIONS.items():
        if question["type"] == "boolean":
            assert set(question["criteria"]) == {"true", "false"}, name
    assert set(QUESTIONS["preferred"]["criteria"]) == {
        "before",
        "after",
        "equivalent",
        "insufficient_context",
    }


def test_change_request_sends_only_the_contract_and_both_versions() -> None:
    rubric = json.loads(RUBRIC.read_text())
    request = jev.build_change_request(
        version("def price(q):\n    return q * 10\n", **CONTRACT),
        version("UNIT = 10\n\ndef price(q):\n    return q * UNIT\n", **CONTRACT),
        rubric,
    )
    assert request["state"] == {
        **CONTRACT,
        "before": "def price(q):\n    return q * 10\n",
        "after": "UNIT = 10\n\ndef price(q):\n    return q * UNIT\n",
    }
    assert set(request["questions"]) == set(QUESTIONS)
    typesafe = jev.build_change_request(
        version("a = 1\n"), version("a = 2\n"), rubric, "jev-latest", "typesafe"
    )
    assert typesafe["state"] == {"before": "a = 1\n", "after": "a = 2\n"}
    assert {q["type"] for q in typesafe["questions"].values()} == {"noul", "choice"}


def test_several_files_are_joined_with_path_headers() -> None:
    sources = [{"path": "a.py", "content": "x = 1\n"}, {"path": "b.py", "content": "y = 2\n"}]
    assert jev.render_sources(sources) == "# file: a.py\nx = 1\n\n# file: b.py\ny = 2\n"


def test_different_contracts_are_refused(tmp_path: Path) -> None:
    before, after = tmp_path / "before.json", tmp_path / "after.json"
    before.write_text(json.dumps(version("a = 1\n", task="One task.")))
    after.write_text(json.dumps(version("a = 2\n", task="Another task.")))
    assert jev.main(["--before", str(before), "--after", str(after), "--dry-run"]) == 2


@pytest.mark.parametrize(
    "argv",
    [["--before", "b.json"], ["--state", "s.json", "--before", "b.json", "--after", "a.json"]],
)
def test_modes_cannot_be_mixed_or_half_given(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        jev.main(argv)
    assert exit_info.value.code == 2


def test_live_change_review_records_scope_and_normalizes_answers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    before, after = tmp_path / "before.json", tmp_path / "after.json"
    before.write_text(json.dumps(version("a = 1\n", **CONTRACT)))
    after.write_text(json.dumps(version("a = 2\n", **CONTRACT)))
    monkeypatch.setenv("TYPESAFE_API_KEY", "secret-test-key")

    class FakeProvider:
        def open(self, request: Any, timeout: int) -> io.BytesIO:
            questions = json.loads(request.data)["questions"]
            answers = {
                name: {"type": "noul", "noul": 0.2}
                if q["type"] == "noul"
                else {
                    "type": "choice",
                    "choice": "after",
                    "probabilities": {k: float(k == "after") for k in q["criteria"]},
                }
                for name, q in questions.items()
            }
            return io.BytesIO(json.dumps({"model": "jev", "answers": answers}).encode())

    monkeypatch.setattr(jev.urllib.request, "build_opener", lambda *_: FakeProvider())
    argv = ["--before", str(before), "--after", str(after), "--provider", "typesafe"]
    assert jev.main(argv) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "change" and report["status"] == "evaluated"
    assert report["scope"] == {"before": "price.py:price", "after": "price.py:price"}
    assert report["answers"]["introduced_pass_through"] == {"type": "boolean", "probability": 0.2}
    assert report["answers"]["preferred"]["choice"] == "after"
    assert "measurements" not in report["request"]["state"]


def answers(p: float = 0.1, preferred_after: float = 0.8) -> dict[str, Any]:
    result: dict[str, Any] = {
        name: {"type": "boolean", "probability": p}
        for name, q in QUESTIONS.items()
        if q["type"] == "boolean"
    }
    result["introduced_domain_rule"] = {"type": "boolean", "probability": 0.9}
    rest = (1 - preferred_after) / 3
    result["preferred"] = {
        "type": "choice",
        "choice": "after",
        "probabilities": {
            "before": rest,
            "after": preferred_after,
            "equivalent": rest,
            "insufficient_context": rest,
        },
    }
    return result


def evaluated(values: dict[str, Any]) -> dict[str, Any]:
    return {"status": "evaluated", "answers": values}


TOLERANCES = {"repeat_max_delta": 0.05, "reformat_max_delta": 0.15, "swap_max_delta": 0.25}


def test_a_consistent_swap_mirrors_directions_and_preferences() -> None:
    main = answers()
    swapped = mirrored(main)
    assert swapped["removed_domain_rule"]["probability"] == 0.9
    assert swapped["introduced_domain_rule"]["probability"] == 0.1
    assert swapped["preferred"]["probabilities"]["before"] == 0.8
    reports = {v: evaluated(main) for v in ("main", "repeat", "reformat", "no_context")}
    reports["swap"] = evaluated(swapped)
    result = controls(reports, TOLERANCES)
    assert {v: r["status"] for v, r in result.items()} == {
        "repeat": "passed",
        "reformat": "passed",
        "swap": "passed",
        "no_context": "reported",
    }


def test_controls_fail_beyond_tolerance_and_never_pass_when_unavailable() -> None:
    main = answers()
    drifted = copy.deepcopy(main)
    drifted["removed_pass_through"]["probability"] = 0.3
    unmirrored = mirrored(main)
    unmirrored["preferred"]["probabilities"]["before"] = 0.4
    reports = {
        "main": evaluated(main),
        "repeat": evaluated(drifted),
        "reformat": evaluated(main),
        "swap": evaluated(unmirrored),
        "no_context": {"status": "incomplete"},
    }
    result = controls(reports, TOLERANCES)
    assert result["repeat"] == {
        "status": "failed",
        "largest_move": 0.2,
        "signal": "removed_pass_through",
    }
    assert result["swap"]["status"] == "failed" and result["swap"]["signal"] == "preferred"
    assert result["no_context"] == {"status": "unavailable"}
    reports["main"] = {"status": "skipped"}
    assert all(r["status"] == "unavailable" for r in controls(reports, TOLERANCES).values())


def test_scores_use_the_frozen_bound() -> None:
    values = answers()
    assert score({"signal": "introduced_domain_rule", "minimum": 0.7}, values) == (True, 0.9)
    assert score({"signal": "removed_pass_through", "maximum": 0.05}, values) == (False, 0.1)
    assert score({"signal": "preferred", "equals": "before"}, values) == (False, "after")


def test_static_separability_names_only_metrics_that_split_every_label() -> None:
    deltas = {
        "a": {
            "defs": 1,
            "decisions": 0,
            "cognitive_sum": -4,
            "max_cognitive": -2,
            "max_cyclomatic": 0,
        },
        "b": {
            "defs": 1,
            "decisions": 0,
            "cognitive_sum": 3,
            "max_cognitive": 1,
            "max_cyclomatic": 0,
        },
        "c": {
            "defs": 0,
            "decisions": 0,
            "cognitive_sum": -2,
            "max_cognitive": 0,
            "max_cyclomatic": 0,
        },
    }
    checks = [
        {"pair": "a", "signal": "preferred", "equals": "after"},
        {"pair": "c", "signal": "preferred", "equals": "after"},
        {"pair": "b", "signal": "preferred", "equals": "before"},
        {"pair": "a", "signal": "introduced_pass_through", "maximum": 0.3},
    ]
    result = static_separability(checks, deltas)
    assert result["preferred"]["separated_by"] == ["cognitive_sum", "max_cognitive"]
    assert result["introduced_pass_through"] == {"positives": 0, "negatives": 1, "separated_by": []}


def minimal_fixture() -> dict[str, Any]:
    return {
        "version": 1,
        "controls": dict(TOLERANCES),
        "pairs": [
            {
                "name": "rename_only",
                "task": "Return the price.",
                "constraints": [],
                "entry": "price",
                "before": {"path": "p.py", "source": "def price(q):\n    return q\n"},
                "after": {"path": "p.py", "source": "def price(quantity):\n    return quantity\n"},
                "tests": [{"args": [2], "expected": 2}],
            }
        ],
        "checks": [{"pair": "rename_only", "signal": "preferred", "equals": "equivalent"}],
    }


@pytest.mark.parametrize(
    "break_it",
    [
        lambda f: f["checks"].append({"pair": "rename_only", "signal": "nope", "maximum": 0.3}),
        lambda f: f["checks"].append(
            {"pair": "rename_only", "signal": "preferred", "maximum": 0.3}
        ),
        lambda f: f["checks"].append(
            {"pair": "rename_only", "signal": "removed_pass_through", "equals": "after"}
        ),
        lambda f: f["checks"].append(
            {"pair": "rename_only", "signal": "preferred", "equals": "tie"}
        ),
        lambda f: f["checks"].append({"pair": "missing", "signal": "preferred", "equals": "after"}),
        lambda f: f["pairs"].append(copy.deepcopy(f["pairs"][0])),
        lambda f: f["controls"].pop("swap_max_delta"),
        lambda f: f["pairs"][0].pop("tests"),
    ],
    ids=[
        "signal",
        "bound",
        "choice-on-boolean",
        "choice",
        "pair",
        "duplicate",
        "controls",
        "tests",
    ],
)
def test_malformed_suites_are_rejected_before_running(break_it: Any) -> None:
    fixture = minimal_fixture()
    validate_fixtures(fixture, QUESTIONS)
    break_it(fixture)
    with pytest.raises(ValueError):
        validate_fixtures(fixture, QUESTIONS)


def test_frozen_change_suite_is_valid_unchanged_and_behavior_preserving() -> None:
    fixtures = json.loads(FIXTURES.read_text())
    validate_fixtures(fixtures, QUESTIONS)
    freeze = json.loads(
        (ROOT / "notes/python-complexity/jev-changes-freeze-2026-09-22.json").read_text()
    )
    # A frozen suite is not edited after results are read; a revision needs a new suite.
    assert hashlib.sha256(FIXTURES.read_bytes()).hexdigest() == freeze["fixture"]["sha256"]
    assert hashlib.sha256(RUBRIC.read_bytes()).hexdigest() == freeze["rubric"]["sha256"]
    cases = [
        {
            "name": f"{pair['name']}__{side}",
            "complete": pair.get("complete", True),
            "source": pair[side]["source"],
            "entry": pair["entry"],
            "tests": pair.get("tests", []),
        }
        for pair in fixtures["pairs"]
        for side in ("before", "after")
    ]
    result = behavior_check(cases)
    assert result["status"] == "passed", result["failures"]
    assert (len(fixtures["pairs"]), len(fixtures["checks"]), result["total_checks"]) == (
        15,
        129,
        168,
    )
