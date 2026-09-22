"""Verify that comment evals retain failures and separate syntax from semantic loss."""

from __future__ import annotations

import json
from typing import Any

import pytest

from scripts.eval_comment_slop import FIXTURES, check_expectations, proposal_structure


def test_frozen_proposals_parse_without_changing_executable_structure() -> None:
    fixtures = json.loads(FIXTURES.read_text())
    proposals = [c for c in fixtures["cases"] if "proposal" in c["state"]]
    assert len(proposals) == 5
    assert all(proposal_structure(c["state"])["status"] == "passed" for c in proposals)
    # These proposals deliberately lose facts despite preserving executable structure.
    assert len([c for c in proposals if "loses" in c["name"]]) == 2


def test_held_out_proposals_preserve_executable_structure() -> None:
    fixtures = json.loads(FIXTURES.with_name("comment-slop-jev-holdout.json").read_text())
    proposals = [c for c in fixtures["cases"] if "proposal" in c["state"]]
    assert len(proposals) == 12
    assert all(proposal_structure(c["state"])["status"] == "passed" for c in proposals)


@pytest.mark.parametrize("replacement", ["    return 42", "    this is not valid Python !"])
def test_structure_check_rejects_logic_and_syntax_changes(replacement: str) -> None:
    state = {
        "language": "python",
        "sources": [{"path": "x.py", "content": "def f():\n    # Return one.\n    return 1\n"}],
        "candidate": {"path": "x.py", "start_line": 2, "end_line": 2, "text": "    # Return one."},
        "proposal": {"replacement": replacement},
    }
    assert proposal_structure(state)["status"] == "failed"


@pytest.mark.parametrize("status", ["skipped", "incomplete", "preview"])
def test_unavailable_judgment_is_never_a_pass(status: str) -> None:
    case = {"name": "rationale", "expectations": [{"signal": "disposition", "equals": "keep"}]}
    assert check_expectations(case, {"status": status})[0]["status"] == "skipped"


@pytest.mark.parametrize(
    "signal,value,expected",
    [
        ("disposition", "delete", "failed"),
        ("disposition", "keep", "passed"),
        ("proposal_preserves_information", 0.6, "failed"),
        ("proposal_preserves_information", 0.8, "passed"),
    ],
)
def test_wrong_and_weak_judgments_remain_failures(signal: str, value: Any, expected: str) -> None:
    check = {
        "signal": signal,
        **({"equals": "keep"} if signal == "disposition" else {"minimum": 0.7}),
    }
    answer = {"choice" if signal == "disposition" else "probability": value}
    case = {"name": "rationale", "expectations": [check]}
    report = {"status": "evaluated", "answers": {signal: answer}}
    assert check_expectations(case, report)[0]["status"] == expected


def test_absent_signal_is_not_assumed_safe() -> None:
    case = {"name": "rationale", "expectations": [{"signal": "information_loss", "maximum": 0.3}]}
    result = check_expectations(case, {"status": "evaluated", "answers": {}})
    assert result[0]["status"] == "skipped"
