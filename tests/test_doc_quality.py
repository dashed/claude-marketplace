"""Verify source isolation, budgets, provider reuse, and optional Markdown review."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "plugins/doc-quality/skills/doc-quality/scripts/doc_quality.py"
sys.path.insert(0, str(CLI.parent))
spec = importlib.util.spec_from_file_location("doc_quality", CLI)
assert spec and spec.loader
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
sys.path.pop(0)
RUBRIC = json.loads(review.RUBRICS.read_text())


def args(**overrides: Any) -> argparse.Namespace:
    return argparse.Namespace(
        **{
            **dict.fromkeys(review.OPTIONS),
            "dry_run": True,
            "jev_helper": None,
            "section": None,
            "max_sections": 6,
            "paired_only": False,
            **overrides,
        }
    )


def test_before_after_questions_match_and_do_not_leak_the_other_version() -> None:
    before = "# Decision\nKeep uncertain ORIGINAL_VALUE.\n"
    after = "# Decision\nKeep uncertain REVISED_VALUE.\n"
    context = {"audience": "maintainers", "missing": ["timing not verified"]}
    result = review.compare(before, after, "design", context, RUBRIC, args())
    reports = result["semantic"]["reports"]
    original_request, revised_request = reports["before"]["request"], reports["after"]["request"]
    assert original_request["questions"] == revised_request["questions"]
    assert original_request["state"]["context"] == revised_request["state"]["context"] == context
    assert "REVISED_VALUE" not in json.dumps(original_request)
    assert "ORIGINAL_VALUE" not in json.dumps(revised_request)
    assert reports["preservation"]["request"]["state"]["original"] == before
    assert reports["preservation"]["request"]["state"]["revised"] == after
    assert result["acceptance"] == "requires_evidence_review"


@pytest.mark.parametrize("kind", review.KINDS)
def test_kind_specific_questions_are_selected_without_loading_other_profiles(kind: str) -> None:
    request = review.quality_request(kind, {"text": "A section"}, {}, RUBRIC)
    assert request["questions"] == {**RUBRIC["common"], **RUBRIC["profiles"][kind]}
    assert request["state"]["kind"] == kind


def test_paired_only_does_not_make_absolute_quality_calls() -> None:
    result = review.compare("before", "after", "analysis", {}, RUBRIC, args(paired_only=True))
    assert set(result["semantic"]["reports"]) == {"preservation"}


def test_budget_failure_preserves_static_analysis_and_makes_no_calls(monkeypatch: Any) -> None:
    def forbidden(*unused: Any) -> None:
        pytest.fail("Budget rejection must not call Jev")

    monkeypatch.setattr(review, "call_jev", forbidden)
    result = review.analyze("# One\nText\n# Two\nText\n", "adr", {}, RUBRIC, args(max_sections=1))
    assert len(result["analysis"]["sections"]) == 2
    assert result["semantic"]["status"] == "incomplete"
    assert result["semantic"]["not_reviewed"] == ["section-1", "section-3"]


def test_explicit_section_selection_retains_unselected_inventory() -> None:
    result = review.analyze(
        "# One\nText\n# Two\nText\n", "adr", {}, RUBRIC, args(section=["section-3"], max_sections=1)
    )
    assert result["selected_sections"] == ["section-3"]
    assert result["not_selected"] == ["section-1"]
    assert len(result["analysis"]["sections"]) == 2
    assert list(result["semantic"]["reports"]) == ["section-3"]


@pytest.mark.parametrize("sections", [["missing"], ["section-1", "section-1"]])
def test_unknown_and_duplicate_section_ids_fail(sections: list[str]) -> None:
    with pytest.raises(review.ReviewError):
        review.analyze("# One\nText\n", "adr", {}, RUBRIC, args(section=sections))


@pytest.mark.parametrize("status", ["skipped", "incomplete"])
def test_unavailable_first_call_stops_sequence_without_resampling(
    monkeypatch: Any, status: str
) -> None:
    calls = []

    def unavailable(unused: Any, request: Any) -> dict[str, str]:
        calls.append(request)
        return {"status": status}

    monkeypatch.setattr(review, "call_jev", unavailable)
    result = review.compare("a", "b", "plan", {}, RUBRIC, args(dry_run=False))
    assert len(calls) == 1
    assert result["semantic"]["status"] == status
    assert result["semantic"]["not_reviewed"] == ["after", "preservation"]
    assert result["acceptance"] == "requires_evidence_review"


def test_partial_service_failure_keeps_successful_evidence(monkeypatch: Any) -> None:
    results = iter([{"status": "evaluated", "answers": {"clarity": 2}}, {"status": "incomplete"}])
    monkeypatch.setattr(review, "call_jev", lambda *unused: next(results))
    result = review.compare("a", "b", "design", {}, RUBRIC, args(dry_run=False))
    assert result["semantic"]["reports"]["before"]["answers"] == {"clarity": 2}
    assert result["semantic"]["not_reviewed"] == ["preservation"]
    assert result["semantic"]["status"] == "incomplete"


def test_oversized_request_is_not_truncated_or_called() -> None:
    result = review.call_jev(args(), {"state": "x" * 100_001, "questions": {}})
    assert result["status"] == "incomplete"
    assert "truncated" in result["error"]
    assert "request" not in result


def test_missing_helper_is_an_explicit_skip() -> None:
    assert review.call_jev(args(dry_run=False), {"state": "x", "questions": {}}) == {
        "status": "skipped",
        "reason": "jev_helper_unavailable",
    }


def test_provider_options_are_forwarded_to_general_helper(tmp_path: Path) -> None:
    helper = tmp_path / "fake.py"
    helper.write_text(
        "import json,sys\nprint(json.dumps({'status':'skipped','received':sys.argv[1:]}))\n"
    )
    configured = args(
        dry_run=False,
        jev_helper=helper,
        provider="custom",
        endpoint="https://example.invalid/v1/evaluate",
        model="another-model",
        protocol="gateway",
        api_key_env="DOC_TEST_KEY",
        config="config.json",
        env_file="keys.env",
    )
    result = review.call_jev(configured, {"state": "x", "questions": {}})
    received = result["received"]
    for name in review.OPTIONS:
        assert received[received.index("--" + name.replace("_", "-")) + 1] == getattr(
            configured, name
        )


@pytest.mark.parametrize(
    "payload,code",
    [
        ("not json SECRET", 0),
        ("[]", 0),
        ('{"status":"evaluated","answers":{}}', 0),
        ('{"status":"skipped"}', 1),
    ],
)
def test_bad_helper_reports_are_incomplete_without_echoing_output(
    tmp_path: Path, payload: str, code: int
) -> None:
    helper = tmp_path / "bad.py"
    helper.write_text(f"print({payload!r})\nraise SystemExit({code})\n")
    result = review.call_jev(
        args(dry_run=False, jev_helper=helper), {"state": "x", "questions": {}}
    )
    assert result["status"] == "incomplete"
    assert "SECRET" not in json.dumps(result)


def test_actual_helper_without_key_skips_and_never_edits_input(tmp_path: Path) -> None:
    document = tmp_path / "doc.md"
    content = "# Plan\nThe owner MUST verify the migration.\n"
    document.write_text(content)
    config = tmp_path / "config.json"
    config.write_text("{}")
    env = dict(os.environ)
    env.pop("DOC_QUALITY_TEST_ABSENT_KEY", None)
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "analyze",
            str(document),
            "--kind",
            "plan",
            "--jev-helper",
            str(ROOT / "plugins/jev/skills/jev/scripts/jev.py"),
            "--config",
            str(config),
            "--env-file",
            str(tmp_path / "missing.env"),
            "--api-key-env",
            "DOC_QUALITY_TEST_ABSENT_KEY",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    report = json.loads(result.stdout)
    assert report["status"] == "skipped"
    assert report["analysis"]["metrics"]["word_count"] > 0
    assert document.read_text() == content


@pytest.mark.parametrize("content", [b"\xff", b"x" * 1_000_001], ids=["invalid_utf8", "oversized"])
def test_invalid_and_oversized_inputs_are_rejected(tmp_path: Path, content: bytes) -> None:
    path = tmp_path / "bad.md"
    path.write_bytes(content)
    with pytest.raises(review.ReviewError):
        review.read_text(path)


def test_large_scope_without_helper_still_returns_optional_skip() -> None:
    document = "# One\n" + "word " * 25_000
    result = review.compare(document, document, "design", {}, RUBRIC, args(dry_run=False))
    assert result["semantic"]["status"] == "skipped"
    many = "\n".join(f"# Section {n}\nText" for n in range(10))
    result = review.analyze(
        many, "plan", {}, RUBRIC, args(dry_run=False, jev_helper=Path("/missing/helper.py"))
    )
    assert result["semantic"]["status"] == "skipped"
    assert len(result["analysis"]["sections"]) == 10


def evaluated_boolean_report(protocol: str = "gateway") -> tuple[dict[str, Any], dict[str, Any]]:
    request = {
        "state": {"text": "The caller MUST retry."},
        "questions": {"preserved": {"type": "boolean", "instructions": "Was it preserved?"}},
    }
    questions = {
        "preserved": {
            **request["questions"]["preserved"],
            "type": "noul" if protocol == "typesafe" else "boolean",
        }
    }
    raw = (
        {"type": "noul", "noul": 0.8}
        if protocol == "typesafe"
        else {"type": "boolean", "probability": 0.8}
    )
    report = {
        "status": "evaluated",
        "request": {"model": "jev-test", "state": request["state"], "questions": questions},
        "response": {"model": "jev-test-1", "answers": {"preserved": raw}},
        "answers": {"preserved": {"type": "boolean", "probability": 0.8}},
        "state_sha256": review.digest(request["state"]),
        "questions_sha256": review.digest(questions),
    }
    return report, request


@pytest.mark.parametrize("protocol", ["gateway", "typesafe"])
def test_valid_provider_normalization_and_provenance_are_accepted(protocol: str) -> None:
    report, request = evaluated_boolean_report(protocol)
    review.validate_evaluation(report, request)


@pytest.mark.parametrize(
    "defect",
    [
        "null_answer",
        "bad_probability",
        "stale_state",
        "stale_questions",
        "bad_hash",
        "response_disagrees",
    ],
)
def test_invalid_or_stale_evaluation_cannot_masquerade_as_current(defect: str) -> None:
    report, request = evaluated_boolean_report()
    if defect == "null_answer":
        report["answers"]["preserved"] = None
    elif defect == "bad_probability":
        report["answers"]["preserved"]["probability"] = 2
        report["response"]["answers"]["preserved"]["probability"] = 2
    elif defect == "stale_state":
        report["request"]["state"] = {"text": "Some other document."}
    elif defect == "stale_questions":
        report["request"]["questions"]["preserved"]["instructions"] = "Is it short?"
    elif defect == "bad_hash":
        report["state_sha256"] = "incorrect"
    else:
        report["response"]["answers"]["preserved"]["probability"] = 0.1
    with pytest.raises(ValueError):
        review.validate_evaluation(report, request)


@pytest.mark.parametrize("kind", ["choice", "score"])
def test_invalid_typed_distributions_are_rejected(kind: str) -> None:
    report, request = evaluated_boolean_report()
    criteria = {"a": "first", "b": "second"} if kind == "choice" else ["first", "second"]
    question = {"type": kind, "instructions": "Choose.", "criteria": criteria}
    request["questions"] = {"preserved": question}
    report["request"]["questions"] = request["questions"]
    report["questions_sha256"] = review.digest(request["questions"])
    answer = {"type": kind, "probabilities": {"a": 0.9, "b": 0.9}, "choice": "a", "score": 1}
    report["answers"] = {"preserved": answer}
    report["response"]["answers"] = report["answers"]
    with pytest.raises(ValueError):
        review.validate_evaluation(report, request)


def test_comparison_preflights_pair_budget_before_quality_calls(monkeypatch: Any) -> None:
    def forbidden(*unused: Any) -> None:
        pytest.fail("An oversized preservation request must prevent preceding quality calls")

    monkeypatch.setattr(review, "call_jev", forbidden)
    result = review.compare("A " * 28_000, "B " * 28_000, "design", {}, RUBRIC, args())
    assert result["semantic"]["status"] == "incomplete"
    assert result["semantic"]["reports"] == {}
    assert result["semantic"]["oversized_requests"] == ["preservation"]
    assert result["before"]["metrics"]["word_count"] == 28_000
