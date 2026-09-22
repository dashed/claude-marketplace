"""Profile evaluation keeps missing context, wrong judgments, and skipped calls distinct."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts import eval_doc_profiles as evaluator


def fixture_case() -> dict[str, Any]:
    return {
        "name": "sample-01",
        "kind": "design",
        "text": "# Storage decision\n\nUse PostgreSQL to commit updates and audit events together.\n",
        "context": {"audience": "engineers", "scope": "decision", "evidence": [], "missing": []},
        "expectations": [{"signal": "decision_clarity", "equals": "satisfied"}],
    }


def evaluated(answers: Any) -> dict[str, Any]:
    case = fixture_case()
    section = evaluator.section_input(case)
    return {
        "status": "evaluated",
        "selected_sections": [section["id"]],
        "not_selected": [],
        "semantic": {
            "status": "evaluated",
            "reports": {
                section["id"]: {
                    "status": "evaluated",
                    "answers": answers,
                    "provider": "test",
                    "state_sha256": "state-hash",
                    "questions_sha256": "questions-hash",
                    "request": {
                        "model": "requested-alias",
                        "state": {
                            "kind": case["kind"],
                            "section": {
                                "text": section["text"],
                                "heading_path": section["heading_path"],
                            },
                            "context": case["context"],
                        },
                    },
                    "response": {"model": "model-version"},
                }
            },
        },
    }


def write_fixtures(path: Path, cases: list[dict[str, Any]]) -> Path:
    path.write_text(json.dumps({"version": "1.0.0", "cases": cases}) + "\n")
    return path


def test_frozen_profile_inputs_cover_all_kinds_and_one_section_each() -> None:
    raw = evaluator.FIXTURES.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == (
        "12ff4b7cc682139a0e04fa0c56d1c9902b6db481ab965457bf00c519f2c0e22a"
    )
    fixtures = evaluator.validate_fixtures(json.loads(raw))
    assert len(fixtures["cases"]) == 8
    assert sum(len(case["expectations"]) for case in fixtures["cases"]) == 13
    assert {case["kind"] for case in fixtures["cases"]} == set(evaluator.PROFILES)


@pytest.mark.parametrize("choice", sorted(evaluator.CHOICES))
def test_wrong_profile_choices_fail_even_when_another_valid_category(choice: str) -> None:
    checks = evaluator.check_expectations(
        fixture_case(), evaluated({"decision_clarity": {"choice": choice}})
    )
    assert checks[0]["status"] == ("passed" if choice == "satisfied" else "failed")
    assert checks[0]["observed"] == choice


@pytest.mark.parametrize(
    "answers",
    [
        None,
        {},
        {"decision_clarity": None},
        {"decision_clarity": {"choice": "revised"}},
        {"decision_clarity": {"choice": True}},
        {"decision_clarity": {"probability": 0.99}},
    ],
)
def test_missing_or_invalid_profile_answers_never_pass(answers: Any) -> None:
    assert (
        evaluator.check_expectations(fixture_case(), evaluated(answers))[0]["status"] == "skipped"
    )


@pytest.mark.parametrize("level", ["top", "semantic", "section", "selection", "extra"])
def test_stale_or_partial_results_cannot_pass(level: str) -> None:
    report = evaluated({"decision_clarity": {"choice": "satisfied"}})
    if level == "top":
        report["status"] = "skipped"
    elif level == "semantic":
        report["semantic"]["status"] = "skipped"
    elif level == "section":
        evaluator.section_report(report)["status"] = "skipped"
    elif level == "selection":
        report["not_selected"] = ["section-99"]
    else:
        report["semantic"]["reports"]["section-99"] = {"status": "evaluated"}
    assert evaluator.check_expectations(fixture_case(), report)[0]["status"] == "skipped"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data.update(cases=[]),
        lambda data: data["cases"].append(copy.deepcopy(data["cases"][0])),
        lambda data: data["cases"][0].update(name="../outside"),
        lambda data: data["cases"][0].update(kind="email"),
        lambda data: data["cases"][0].update(text=None),
        lambda data: data["cases"][0].update(text="# A\nBody.\n\n## B\nNext.\n"),
        lambda data: data["cases"][0].update(text="Preamble.\n\n# A\nBody.\n"),
        lambda data: data["cases"][0].update(context=[]),
        lambda data: data["cases"][0]["context"].update(evidence=[1]),
        lambda data: data["cases"][0].update(expectations=[]),
        lambda data: data["cases"][0]["expectations"][0].update(signal="acceptance_recovery"),
        lambda data: data["cases"][0]["expectations"][0].update(equals="revised"),
        lambda data: data["cases"][0]["expectations"][0].update(minimum=0.7),
        lambda data: data["cases"][0]["expectations"].append(
            copy.deepcopy(data["cases"][0]["expectations"][0])
        ),
    ],
)
def test_invalid_fixtures_fail_before_calls_or_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: Any
) -> None:
    data = {"version": "1.0.0", "cases": [fixture_case()]}
    mutation(data)
    source = tmp_path / "fixtures.json"
    source.write_text(json.dumps(data))
    before = source.read_bytes()
    monkeypatch.setattr(evaluator, "review_case", lambda *_: pytest.fail("Must validate first"))
    output = tmp_path / "evidence"
    assert evaluator.main(["--fixtures", str(source), "--output-dir", str(output)]) == 2
    assert not output.exists()
    assert source.read_bytes() == before


def test_reports_hashes_provenance_and_failed_labels_are_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = write_fixtures(tmp_path / "fixtures.json", [fixture_case()])
    before = source.read_bytes()
    report = evaluated({"decision_clarity": {"choice": "gap"}})
    monkeypatch.setattr(evaluator, "review_case", lambda *_: report)
    output = tmp_path / "evidence"
    assert evaluator.main(["--fixtures", str(source), "--output-dir", str(output)]) == 1
    summary = json.loads((output / "summary.json").read_text())
    assert summary["status"] == "failed"
    assert summary["semantic_counts"] == {"passed": 0, "failed": 1, "skipped": 0}
    assert source.read_bytes() == before
    assert (output / "fixtures.json").read_bytes() == before
    assert json.loads((output / "sample-01/report.json").read_text()) == report
    assert summary["cases"]["sample-01"]["provenance"] == {
        "provider": "test",
        "state_sha256": "state-hash",
        "questions_sha256": "questions-hash",
        "requested_model": "requested-alias",
        "response_model": "model-version",
    }
    for name, digest in summary["cases"]["sample-01"]["sha256"].items():
        assert digest == hashlib.sha256((output / "sample-01" / name).read_bytes()).hexdigest()


@pytest.mark.parametrize(
    "report",
    [
        evaluator.unavailable("skipped", "missing_api_key"),
        evaluator.unavailable("incomplete", "service_503"),
        evaluated({}),
    ],
)
def test_unavailable_stops_calls_and_records_remaining_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, report: dict[str, Any]
) -> None:
    first, second = fixture_case(), fixture_case()
    second["name"] = "sample-02"
    source = write_fixtures(tmp_path / "fixtures.json", [first, second])
    calls = []
    monkeypatch.setattr(evaluator, "review_case", lambda *args: calls.append(args) or report)
    output = tmp_path / "evidence"
    assert evaluator.main(["--fixtures", str(source), "--output-dir", str(output)]) == 2
    assert len(calls) == 1
    summary = json.loads((output / "summary.json").read_text())
    assert summary["semantic_counts"] == {"passed": 0, "failed": 0, "skipped": 2}
    assert summary["profile"]["retries"] == 0
    assert summary["profile"]["halted_by"] == "sample-01"
    assert (output / "sample-02/document.md").read_text() == second["text"]


def test_offline_no_credentials_has_one_request_and_no_label_leaks(tmp_path: Path) -> None:
    source = write_fixtures(tmp_path / "fixtures.json", [fixture_case()])
    output = tmp_path / "evidence"
    assert (
        evaluator.main(
            [
                "--fixtures",
                str(source),
                "--output-dir",
                str(output),
                "--offline",
                "--jev-helper",
                str(tmp_path / "absent.py"),
            ]
        )
        == 0
    )
    report = json.loads((output / "sample-01/report.json").read_text())
    summary = json.loads((output / "summary.json").read_text())
    state = evaluator.section_report(report)["request"]["state"]
    assert set(state) == {"kind", "section", "context"}
    assert state == evaluator.section_report(evaluated({}))["request"]["state"]
    assert summary["status"] == "offline_preview"
    assert summary["semantic_counts"] == {"passed": 0, "failed": 0, "skipped": 1}
    assert summary["profile"]["maximum_semantic_calls"] == 0


def test_existing_output_is_never_overwritten(tmp_path: Path) -> None:
    source = write_fixtures(tmp_path / "fixtures.json", [fixture_case()])
    output = tmp_path / "evidence"
    output.mkdir()
    prior = output / "summary.json"
    prior.write_text("prior evidence")
    assert evaluator.main(["--fixtures", str(source), "--output-dir", str(output)]) == 2
    assert prior.read_text() == "prior evidence"
    assert list(output.iterdir()) == [prior]


@pytest.mark.parametrize("behavior", ["timeout", "nonzero", "malformed", "mismatched", "stale"])
def test_process_failure_and_wrong_state_are_incomplete_without_output_leaks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    behavior: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        if behavior == "timeout":
            raise subprocess.TimeoutExpired("profile", 60)
        if behavior == "nonzero":
            return subprocess.CompletedProcess([], 1, b"private output", b"private stderr")
        if behavior == "mismatched":
            return subprocess.CompletedProcess([], 0, b'{"status":"evaluated"}', b"")
        if behavior == "stale":
            report = evaluated({"decision_clarity": {"choice": "satisfied"}})
            evaluator.section_report(report)["request"]["state"]["kind"] = "plan"
            return subprocess.CompletedProcess([], 0, json.dumps(report).encode(), b"")
        return subprocess.CompletedProcess([], 0, b"private output", b"private stderr")

    monkeypatch.setattr(evaluator.subprocess, "run", fake_run)
    source = write_fixtures(tmp_path / "fixtures.json", [fixture_case()])
    output = tmp_path / "evidence"
    assert evaluator.main(["--fixtures", str(source), "--output-dir", str(output)]) == 2
    saved = (output / "sample-01/report.json").read_text()
    captured = capsys.readouterr().out
    assert "private output" not in saved + captured
    assert "private stderr" not in saved + captured
