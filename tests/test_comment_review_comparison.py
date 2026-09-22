"""Keep absent evidence, abstentions, and harmful assistance visible in comparisons."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.compare_comment_reviews import compare_reviews

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/compare_comment_reviews.py"


def fixture_case(name: str, disposition: str, preserves: bool | None = None) -> dict[str, Any]:
    expectations: list[dict[str, Any]] = [{"signal": "disposition", "equals": disposition}]
    state: dict[str, Any] = {"sources": []}
    if preserves is not None:
        state["proposal"] = {"replacement": ""}
        expectations.append(
            {
                "signal": "proposal_preserves_information",
                "minimum" if preserves else "maximum": 0.7 if preserves else 0.3,
            }
        )
    return {"name": name, "state": state, "expectations": expectations}


def review(*decisions: tuple[str, str, bool | None]) -> dict[str, Any]:
    return {
        "evaluated_at": "2026-09-22T00:00:00Z",
        "cases": [
            {
                "name": name,
                "disposition": disposition,
                "proposal_preserves_information": preserves,
                "reason": "Recorded independent judgment.",
            }
            for name, disposition, preserves in decisions
        ],
    }


def run_comparison(
    tmp_path: Path, fixtures: Any, baseline: Any, assisted: Any, *extra: str
) -> subprocess.CompletedProcess[str]:
    paths = []
    for name, document in (("fixtures", fixtures), ("baseline", baseline), ("assisted", assisted)):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(document))
        paths.extend((f"--{name}", str(path)))
    return subprocess.run(
        [sys.executable, str(SCRIPT), *paths, *extra], text=True, capture_output=True, check=False
    )


@pytest.mark.parametrize("side", ["baseline", "assisted"])
@pytest.mark.parametrize("defect", ["missing", "extra", "duplicate"])
def test_bad_coverage_is_incomplete_not_a_zero_score(
    tmp_path: Path, side: str, defect: str
) -> None:
    fixtures = {"version": 1, "cases": [fixture_case("a", "keep"), fixture_case("b", "delete")]}
    reviews = {
        side: review(("a", "keep", None), ("b", "delete", None))
        for side in ("baseline", "assisted")
    }
    cases = reviews[side]["cases"]
    if defect == "missing":
        cases.pop()
    elif defect == "extra":
        cases.append({**cases[0], "name": "extra"})
    else:
        cases.append(copy.deepcopy(cases[0]))
    result = run_comparison(tmp_path, fixtures, **reviews)
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["status"] == "incomplete"
    assert "counts" not in report
    assert side.title() in report["error"]


def test_harm_and_reversing_review_order_are_visible() -> None:
    fixtures = {"cases": [fixture_case("a", "keep", False)]}
    right = review(("a", "keep", False))
    wrong = review(("a", "delete", True))
    harmed = compare_reviews(fixtures, right, wrong)
    helped = compare_reviews(fixtures, wrong, right)
    assert harmed["counts"]["baseline_correct"] == 2
    assert harmed["counts"]["assisted_correct"] == 0
    assert harmed["counts"]["regressions"] == helped["counts"]["improvements"] == 2
    assert harmed["counts"]["improvements"] == helped["counts"]["regressions"] == 0


def test_mixed_changes_count_only_corrected_errors_as_improvements() -> None:
    fixtures = {
        "cases": [fixture_case(name, "keep") for name in ("fixed", "harmed", "right", "wrong")]
    }
    baseline = review(
        ("fixed", "delete", None),
        ("harmed", "keep", None),
        ("right", "keep", None),
        ("wrong", "delete", None),
    )
    assisted = review(
        ("fixed", "keep", None),
        ("harmed", "delete", None),
        ("right", "keep", None),
        ("wrong", "rewrite", None),
    )
    report = compare_reviews(fixtures, baseline, assisted)
    assert report["counts"]["baseline_correct"] == report["counts"]["assisted_correct"] == 2
    for key in ("improvements", "regressions", "unchanged_correct", "unchanged_incorrect"):
        assert report["counts"][key] == 1
    decision = report["decisions"][-1]
    assert (decision["before"], decision["after"], decision["expected"]) == (
        "delete",
        "rewrite",
        "keep",
    )
    assert decision["transition"] == "unchanged_incorrect"


def test_abstentions_are_separate_from_correct_and_incorrect() -> None:
    fixtures = {
        "cases": [fixture_case(name, "reduce", True) for name in ("resolved", "lost", "unknown")]
    }
    baseline = review(
        ("resolved", "reduce", None), ("lost", "reduce", True), ("unknown", "reduce", None)
    )
    assisted = review(
        ("resolved", "reduce", True), ("lost", "reduce", None), ("unknown", "reduce", None)
    )
    report = compare_reviews(fixtures, baseline, assisted)
    assert report["decision_count"] == 6
    for side in ("baseline", "assisted"):
        assert report["counts"][f"{side}_correct"] == 4
        assert report["counts"][f"{side}_abstentions"] == 2
        assert report["counts"][f"{side}_incorrect"] == 0
    for key in ("abstention_to_correct", "correct_to_abstention", "unchanged_abstained"):
        assert report["counts"][key] == 1
    assert report["counts"]["improvements"] == report["counts"]["regressions"] == 0


@pytest.mark.parametrize("value", [0, 1, 0.8, "true"])
def test_proposal_answer_requires_a_boolean_not_a_probability(value: Any) -> None:
    fixtures = {"cases": [fixture_case("a", "reduce", True)]}
    baseline = review(("a", "reduce", True))
    assisted = copy.deepcopy(baseline)
    assisted["cases"][0]["proposal_preserves_information"] = value
    with pytest.raises(ValueError, match="Boolean or null"):
        compare_reviews(fixtures, baseline, assisted)


def test_missing_proposal_answer_is_incomplete() -> None:
    fixtures = {"cases": [fixture_case("a", "reduce", True)]}
    baseline = review(("a", "reduce", True))
    assisted = copy.deepcopy(baseline)
    del assisted["cases"][0]["proposal_preserves_information"]
    with pytest.raises(ValueError, match="Boolean or null"):
        compare_reviews(fixtures, baseline, assisted)


@pytest.mark.parametrize("bound,value", [("minimum", 0.49), ("maximum", 0.5), ("minimum", True)])
def test_ambiguous_fixture_proposal_label_is_rejected(bound: str, value: Any) -> None:
    case = fixture_case("a", "reduce", True)
    case["expectations"][-1] = {"signal": "proposal_preserves_information", bound: value}
    reviews = review(("a", "reduce", True))
    with pytest.raises(ValueError, match="ambiguous"):
        compare_reviews({"cases": [case]}, reviews, reviews)


def test_cli_is_deterministic_preserves_inputs_and_never_executes_source(tmp_path: Path) -> None:
    marker = tmp_path / "source_was_executed"
    case = fixture_case("a", "keep")
    case["state"]["sources"] = [
        {"path": "sample.py", "content": f"open({str(marker)!r}, 'w').write('executed')"}
    ]
    case["expectations"].append({"signal": "information_loss", "minimum": 0.7})
    fixtures = {"version": 1, "cases": [case]}
    baseline, assisted = review(("a", "keep", None)), review(("a", "delete", None))
    baseline["cases"][0]["information_loss"] = 0.1
    assisted["cases"][0]["information_loss"] = 0.9
    original = copy.deepcopy((fixtures, baseline, assisted))
    output = tmp_path / "comparison.json"
    result = run_comparison(tmp_path, fixtures, baseline, assisted, "--output", str(output))
    assert result.returncode == 0  # Harm is a valid comparison, never a passing quality gate.
    report = json.loads(result.stdout)
    assert report["counts"]["regressions"] == 1
    assert report["decision_count"] == 1
    assert output.read_text() == result.stdout
    for label, document in zip(("fixtures", "baseline", "assisted"), original, strict=True):
        raw = (tmp_path / f"{label}.json").read_bytes()
        assert json.loads(raw) == document
        assert report["input_sha256"][label] == hashlib.sha256(raw).hexdigest()
    assert (fixtures, baseline, assisted) == original
    again = run_comparison(tmp_path, fixtures, baseline, assisted)
    assert again.stdout == result.stdout
    assert not marker.exists()


def test_output_cannot_overwrite_evidence(tmp_path: Path) -> None:
    fixtures = {"cases": [fixture_case("a", "keep")]}
    reviews = review(("a", "keep", None))
    output = tmp_path / "existing.json"
    output.write_text("prior evidence\n")
    result = run_comparison(tmp_path, fixtures, reviews, reviews, "--output", str(output))
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "incomplete"
    assert output.read_text() == "prior evidence\n"


def test_duplicate_fixture_cases_are_rejected() -> None:
    case = fixture_case("a", "keep")
    reviews = review(("a", "keep", None))
    with pytest.raises(ValueError, match="duplicate case"):
        compare_reviews({"cases": [case, case]}, reviews, reviews)
