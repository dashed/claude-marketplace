"""Ensure the eval harness preserves failures and never counts unavailable judgments as passes."""

from __future__ import annotations

import json
from typing import Any

import pytest

from scripts.eval_python_complexity import FIXTURES, behavior_check, semantic_checks


def test_complete_fixtures_match_the_behavior_contract() -> None:
    fixtures = json.loads(FIXTURES.read_text())
    result = behavior_check(fixtures["cases"])
    assert result == {"status": "passed", "inputs_per_case": 119, "failures": []}


def test_behavior_check_detects_a_broken_refactor() -> None:
    result = behavior_check(
        [{"name": "mutant", "complete": True, "source": 'def classify(value): return "accepted"'}]
    )
    assert result["status"] == "failed"
    assert any(row["input"] is None and row["expected"] == "missing" for row in result["failures"])


@pytest.mark.parametrize("status", ["skipped", "incomplete"])
def test_unavailable_semantics_never_pass(status: str) -> None:
    check = {
        "name": "readability",
        "higher": "flat",
        "lower": "nested",
        "signal": "readability",
        "min_delta": 0.25,
    }
    reports = {"flat": {"status": status}, "nested": {"status": "evaluated", "answers": {}}}
    result = semantic_checks([check], reports)
    assert result[0]["status"] == "skipped"
    assert "observed" not in result[0]


@pytest.mark.parametrize("delta, expected", [(0.1, "failed"), (0.25, "passed"), (-0.5, "failed")])
def test_small_and_reversed_effects_fail_the_declared_expectation(
    delta: float, expected: str
) -> None:
    check = {
        "name": "readability",
        "higher": "flat",
        "lower": "nested",
        "signal": "readability",
        "min_delta": 0.25,
    }
    reports = {
        "flat": {"status": "evaluated", "answers": {"readability": {"score": 2 + delta}}},
        "nested": {"status": "evaluated", "answers": {"readability": {"score": 2}}},
    }
    assert semantic_checks([check], reports)[0]["status"] == expected


@pytest.mark.parametrize("observed, expected", [(0.8, "failed"), (0.2, "passed")])
def test_missing_context_probability_check(observed: float, expected: str) -> None:
    check = {"name": "context", "case": "missing", "signal": "context_sufficient", "maximum": 0.3}
    reports = {
        "missing": {
            "status": "evaluated",
            "answers": {"context_sufficient": {"probability": observed}},
        }
    }
    assert semantic_checks([check], reports)[0]["status"] == expected


@pytest.mark.parametrize(
    "choice, expected", [("indirection", "failed"), ("insufficient_context", "passed")]
)
def test_wrong_category_is_retained_as_failure(choice: str, expected: str) -> None:
    check: dict[str, Any] = {
        "name": "context",
        "case": "missing",
        "signal": "dominant_cost",
        "equals": "insufficient_context",
    }
    reports = {"missing": {"status": "evaluated", "answers": {"dominant_cost": {"choice": choice}}}}
    assert semantic_checks([check], reports)[0]["status"] == expected
