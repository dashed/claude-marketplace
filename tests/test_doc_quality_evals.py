"""Frozen semantic labels stay independent of polish and unavailable model judgments."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts import eval_doc_quality as evaluator


def fixture_case() -> dict[str, Any]:
    return {
        "name": "sample-01",
        "kind": "design",
        "original": "# Input\n\nThe receiver MUST reject invalid signatures.\n",
        "revised": "# Input\n\nReject invalid signatures.\n",
        "context": {"audience": "engineers", "scope": "acceptance", "evidence": [], "missing": []},
        "expectations": [
            {"signal": "requirements_preserved", "minimum": 0.7},
            {"signal": "preferred", "equals": "revised"},
        ],
    }


def evaluated(answers: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "evaluated",
        "preservation": {"status": "needs_review", "hard_preservation": {"status": "changed"}},
        "semantic": {
            "status": "evaluated",
            "reports": {
                "preservation": {
                    "status": "evaluated",
                    "answers": answers,
                    "request": {"model": "jev-alias", "state": {"kind": "design"}},
                    "response": {"model": "jev-version"},
                    "provider": "test",
                    "protocol": "gateway",
                    "state_sha256": "state-hash",
                    "questions_sha256": "question-hash",
                }
            },
        },
    }


def write_fixtures(path: Path, cases: list[dict[str, Any]]) -> Path:
    path.write_text(json.dumps({"version": "1.0.0", "cases": cases}) + "\n")
    return path


@pytest.mark.parametrize(
    "filename,expected_sha256",
    [
        ("doc-quality.json", "0960ac7daf72f57db99b3ca070ccb80db8e373597d6ab26d421c77d472900ec2"),
        (
            "doc-quality-challenge.json",
            "2de85dffeb61ea431ddc3ee111e656f2cf60ddc502e4ba3fd9ae8e34d9a25e9a",
        ),
    ],
)
def test_frozen_cases_and_labels_have_not_changed(filename: str, expected_sha256: str) -> None:
    raw = evaluator.FIXTURES.with_name(filename).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected_sha256
    fixtures = evaluator.validate_fixtures(json.loads(raw))
    assert len(fixtures["cases"]) == 10
    assert sum(len(case["expectations"]) for case in fixtures["cases"]) == 30
    assert {case["kind"] for case in fixtures["cases"]} == evaluator.KINDS


@pytest.mark.parametrize(
    "expectation,answer,status",
    [
        ({"signal": "preferred", "equals": "revised"}, {"choice": "original"}, "failed"),
        ({"signal": "preferred", "equals": "revised"}, {"choice": "revised"}, "passed"),
        ({"signal": "evidence_supported", "minimum": 0.7}, {"probability": 0.69}, "failed"),
        ({"signal": "evidence_supported", "minimum": 0.7}, {"probability": 0.7}, "passed"),
        ({"signal": "evidence_supported", "maximum": 0.3}, {"probability": 0.31}, "failed"),
        ({"signal": "evidence_supported", "maximum": 0.3}, {"probability": 0.3}, "passed"),
    ],
)
def test_actual_wrong_choices_and_probabilities_remain_failures(
    expectation: dict[str, Any], answer: dict[str, Any], status: str
) -> None:
    case = {"name": "sample", "expectations": [expectation]}
    result = evaluator.check_expectations(case, evaluated({expectation["signal"]: answer}))
    assert result[0]["status"] == status
    assert result[0]["observed"] == next(iter(answer.values()))


@pytest.mark.parametrize(
    "answers",
    [
        {},
        {"preferred": None},
        {"preferred": {"choice": "unknown"}},
        {"requirements_preserved": {"probability": True}},
        {"requirements_preserved": {"probability": "0.9"}},
        {"requirements_preserved": {"probability": float("nan")}},
        {"requirements_preserved": {"probability": 1.1}},
    ],
)
def test_missing_or_invalid_answers_never_pass(answers: dict[str, Any]) -> None:
    assert all(
        row["status"] == "skipped"
        for row in evaluator.check_expectations(fixture_case(), evaluated(answers))
    )


@pytest.mark.parametrize("status", ["preview", "skipped", "incomplete"])
def test_unavailable_results_cannot_pass_with_stale_answers(status: str) -> None:
    report = evaluated({"preferred": {"choice": "revised"}})
    report["status"] = status
    assert all(
        row["status"] == "skipped" for row in evaluator.check_expectations(fixture_case(), report)
    )


def test_failed_run_retains_raw_report_inputs_and_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = write_fixtures(tmp_path / "fixtures.json", [fixture_case()])
    before = source.read_bytes()
    report = evaluated(
        {"requirements_preserved": {"probability": 0.2}, "preferred": {"choice": "original"}}
    )
    monkeypatch.setattr(evaluator, "review_case", lambda *_: report)
    output = tmp_path / "evidence"
    assert evaluator.main(["--fixtures", str(source), "--output-dir", str(output)]) == 1
    summary = json.loads((output / "summary.json").read_text())
    assert summary["status"] == "failed"
    assert summary["semantic_counts"] == {"passed": 0, "failed": 2, "skipped": 0}
    assert json.loads((output / "sample-01/report.json").read_text()) == report
    assert (output / "sample-01/original.md").read_text() == fixture_case()["original"]
    assert (output / "sample-01/revised.md").read_text() == fixture_case()["revised"]
    assert source.read_bytes() == before
    assert summary["fixture_sha256"] == hashlib.sha256(before).hexdigest()
    assert summary["cases"]["sample-01"]["provenance"] == {
        "provider": "test",
        "protocol": "gateway",
        "state_sha256": "state-hash",
        "questions_sha256": "question-hash",
        "requested_model": "jev-alias",
        "response_model": "jev-version",
    }
    for name, digest in summary["cases"]["sample-01"]["sha256"].items():
        assert digest == hashlib.sha256((output / "sample-01" / name).read_bytes()).hexdigest()


def test_static_inventory_warning_does_not_override_semantic_expectations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = write_fixtures(tmp_path / "fixtures.json", [fixture_case()])
    report = evaluated(
        {"requirements_preserved": {"probability": 0.9}, "preferred": {"choice": "revised"}}
    )
    monkeypatch.setattr(evaluator, "review_case", lambda *_: report)
    output = tmp_path / "evidence"
    assert evaluator.main(["--fixtures", str(source), "--output-dir", str(output)]) == 0
    summary = json.loads((output / "summary.json").read_text())
    assert summary["semantic_counts"] == {"passed": 2, "failed": 0, "skipped": 0}
    assert summary["cases"]["sample-01"]["static_preservation"]["status"] == "needs_review"


@pytest.mark.parametrize(
    "report",
    [
        evaluator.unavailable("skipped", "missing_api_key"),
        evaluator.unavailable("incomplete", "service_503"),
        evaluated({}),
    ],
)
def test_unavailable_live_case_stops_calls_and_records_all_remaining_cases(
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
    assert summary["semantic_counts"] == {"passed": 0, "failed": 0, "skipped": 4}
    assert summary["profile"]["halted_by"] == "sample-01"
    assert summary["profile"]["retries"] == 0
    assert (output / "sample-02/original.md").is_file()
    assert json.loads((output / "sample-02/report.json").read_text())["status"] == "skipped"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data.update(cases=[]),
        lambda data: data["cases"].append(copy.deepcopy(data["cases"][0])),
        lambda data: data["cases"][0].update(name="../outside"),
        lambda data: data["cases"][0].update(kind="email"),
        lambda data: data["cases"][0].update(original=None),
        lambda data: data["cases"][0].update(context=[]),
        lambda data: data["cases"][0].update(expectations=[]),
        lambda data: data["cases"][0]["expectations"][0].update(maximum=0.3),
        lambda data: data["cases"][0]["expectations"][0].update(minimum=True),
        lambda data: data["cases"][0]["expectations"][0].update(minimum=float("nan")),
        lambda data: data["cases"][0]["expectations"][0].update(signal="clarity"),
        lambda data: data["cases"][0]["expectations"][1].update(equals="better"),
        lambda data: data["cases"][0]["expectations"].append(
            copy.deepcopy(data["cases"][0]["expectations"][0])
        ),
    ],
)
def test_invalid_fixture_fails_before_calls_or_artifact_writes(
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


def test_existing_output_is_preserved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = write_fixtures(tmp_path / "fixtures.json", [fixture_case()])
    output = tmp_path / "evidence"
    output.mkdir()
    prior = output / "summary.json"
    prior.write_text("previous evidence\n")
    monkeypatch.setattr(evaluator, "review_case", lambda *_: pytest.fail("Do not overwrite"))
    assert evaluator.main(["--fixtures", str(source), "--output-dir", str(output)]) == 2
    assert prior.read_text() == "previous evidence\n"
    assert list(output.iterdir()) == [prior]


def test_offline_preview_runs_without_helper_or_credentials_and_preserves_source(
    tmp_path: Path,
) -> None:
    source = write_fixtures(tmp_path / "fixtures.json", [fixture_case()])
    before = source.read_bytes()
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
                str(tmp_path / "does-not-exist.py"),
            ]
        )
        == 0
    )
    summary = json.loads((output / "summary.json").read_text())
    report = json.loads((output / "sample-01/report.json").read_text())
    assert summary["status"] == "offline_preview"
    assert summary["semantic_counts"] == {"passed": 0, "failed": 0, "skipped": 2}
    assert summary["profile"]["maximum_semantic_calls"] == 0
    assert set(report["semantic"]["reports"]) == {"preservation"}
    assert evaluator.preservation_report(report)["request"]["state"] == {
        key: fixture_case()[key] for key in ("kind", "original", "revised", "context")
    }
    assert source.read_bytes() == before


@pytest.mark.parametrize("behavior", ["timeout", "nonzero", "malformed", "mismatched"])
def test_comparison_process_errors_are_incomplete_and_do_not_echo_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    behavior: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        if behavior == "timeout":
            raise subprocess.TimeoutExpired("comparison", 60)
        if behavior == "nonzero":
            return subprocess.CompletedProcess([], 1, b"private child output", b"private stderr")
        if behavior == "mismatched":
            return subprocess.CompletedProcess([], 0, b'{"status":"evaluated"}', b"")
        return subprocess.CompletedProcess([], 0, b"private child output", b"private stderr")

    monkeypatch.setattr(evaluator.subprocess, "run", fake_run)
    source = write_fixtures(tmp_path / "fixtures.json", [fixture_case()])
    output = tmp_path / "evidence"
    assert evaluator.main(["--fixtures", str(source), "--output-dir", str(output)]) == 2
    captured = capsys.readouterr().out
    saved = (output / "sample-01/report.json").read_text()
    assert "private child output" not in captured + saved
    assert "private stderr" not in captured + saved
