"""Offline evidence anchoring and delegation checks for optional comment judgments."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/comment-slop/skills/comment-slop"
spec = importlib.util.spec_from_file_location("comment_jev", SKILL / "scripts/jev_comments.py")
assert spec is not None and spec.loader is not None
comments = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comments)


@pytest.fixture
def state() -> dict[str, Any]:
    return {
        "scope": "Retry count comment",
        "language": "python",
        "sources": [
            {
                "path": "retry.py",
                "content": "def retry():\n    # Increment the retry count\n    retries += 1\n",
            }
        ],
        "candidate": {
            "path": "retry.py",
            "start_line": 2,
            "end_line": 2,
            "text": "# Increment the retry count",
        },
        "context": {"published_docs": False, "missing": []},
    }


@pytest.fixture
def state_path(tmp_path: Path, state: dict[str, Any]) -> Path:
    path = tmp_path / "state.json"
    path.write_text(json.dumps(state))
    return path


def test_preview_preserves_exact_evidence_without_helper_execution(
    state_path: Path,
    state: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Preview must not invoke a helper")

    monkeypatch.setattr(comments.subprocess, "run", forbidden)
    assert comments.main(["--state", str(state_path), "--dry-run"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "preview" and report["advisory"] is True
    assert report["request"]["state"] == state
    assert set(report["request"]["questions"]) == {
        "context_sufficient",
        "information_loss",
        "disposition",
    }
    assert report["comment_rubric_version"]
    assert len(report["comment_rubric_sha256"]) == 64


@pytest.mark.parametrize("replacement", ["", "# Retrying permits transient server failures"])
def test_proposal_question_requires_explicit_replacement_and_preserves_original(
    state: dict[str, Any], replacement: str
) -> None:
    original = copy.deepcopy(state)
    state["proposal"] = {"replacement": replacement}
    request = comments.build_request(
        state, comments.load_json(comments.RUBRIC), proposal_review=True
    )
    assert set(request["questions"]) == {"proposal_preserves_information"}
    assert request["state"]["proposal"]["replacement"] == replacement
    assert request["state"]["candidate"] == original["candidate"]
    assert request["state"]["sources"] == original["sources"]


def test_candidate_request_is_invariant_under_added_or_changed_proposal(
    state: dict[str, Any],
) -> None:
    rubric = comments.load_json(comments.RUBRIC)
    baseline = comments.encode(comments.build_request(state, rubric))
    for replacement in ("", "# Preserve all facts", "# An unsupported replacement claim"):
        state["proposal"] = {"replacement": replacement}
        request = comments.build_request(state, rubric)
        assert comments.encode(request) == baseline
        assert "proposal" not in request["state"]
        assert "proposal_preserves_information" not in request["questions"]
        assert state["proposal"]["replacement"] == replacement


def test_proposal_review_requires_proposal(state: dict[str, Any]) -> None:
    with pytest.raises(comments.ReviewError, match="explicit replacement"):
        comments.build_request(state, comments.load_json(comments.RUBRIC), proposal_review=True)


def test_proposal_preview_exposes_both_isolated_requests_without_helper_execution(
    state_path: Path,
    state: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state["proposal"] = {"replacement": ""}
    state_path.write_text(json.dumps(state))
    monkeypatch.setattr(
        comments.subprocess, "run", lambda *a, **k: pytest.fail("Preview invoked a helper")
    )
    assert comments.main(["--state", str(state_path), "--dry-run"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert "proposal" not in report["request"]["state"]
    assert "proposal_preserves_information" not in report["request"]["questions"]
    assert report["proposal_request"]["state"] == state
    assert set(report["proposal_request"]["questions"]) == {"proposal_preserves_information"}
    assert report["review_mode"] == "separate_candidate_and_proposal"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("start_line", 0),
        ("start_line", -1),
        ("start_line", True),
        ("start_line", 2.0),
        ("start_line", "2"),
        ("start_line", 3),
        ("end_line", 10),
        ("end_line", False),
        ("text", ""),
        ("text", "   "),
        ("text", "# Similar but not the source comment"),
        ("text", None),
        ("path", "another.py"),
        ("path", None),
    ],
)
def test_bad_candidate_anchor_is_rejected(state: dict[str, Any], field: str, value: Any) -> None:
    state["candidate"][field] = value
    with pytest.raises(comments.ReviewError):
        comments.validate_state(state)


def test_repeated_text_in_selected_range_requires_narrower_anchor(state: dict[str, Any]) -> None:
    state["sources"][0]["content"] = "# same\n# same\n"
    state["candidate"].update(start_line=1, end_line=2, text="# same")
    with pytest.raises(comments.ReviewError, match="exactly once"):
        comments.validate_state(state)
    state["candidate"]["end_line"] = 1
    comments.validate_state(state)


def test_overlapping_matches_are_ambiguous(state: dict[str, Any]) -> None:
    state["sources"][0]["content"] = "###\n"
    state["candidate"].update(start_line=1, end_line=1, text="##")
    with pytest.raises(comments.ReviewError, match="exactly once"):
        comments.validate_state(state)


def test_multiline_docstring_matches_only_complete_line_window(state: dict[str, Any]) -> None:
    state["sources"][0]["content"] = (
        'def retry():\n    """Retry requests.\n\n    Returns count.\n    """\n'
    )
    state["candidate"].update(
        start_line=2, end_line=5, text='"""Retry requests.\n\n    Returns count.\n    """'
    )
    comments.validate_state(state)
    state["candidate"]["end_line"] = 4
    with pytest.raises(comments.ReviewError, match="exactly once"):
        comments.validate_state(state)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("scope", " "),
        ("language", 12),
        ("context", None),
        ("sources", []),
        ("sources", [{"path": "retry.py", "content": None}]),
        ("sources", [{"path": "", "content": "test"}]),
        ("candidate", None),
        ("proposal", {"replacement": None}),
        ("proposal", ""),
        ("proposal", {}),
    ],
)
def test_invalid_state_shape_is_rejected(state: dict[str, Any], field: str, value: Any) -> None:
    state[field] = value
    with pytest.raises(comments.ReviewError):
        comments.validate_state(state)


def test_duplicate_source_paths_cannot_silently_select_one(state: dict[str, Any]) -> None:
    state["sources"].append(dict(state["sources"][0]))
    with pytest.raises(comments.ReviewError, match="unique"):
        comments.validate_state(state)


def test_no_source_execution_or_file_walk(state: dict[str, Any], tmp_path: Path) -> None:
    sentinel = tmp_path / "must-not-exist"
    state["sources"][0]["content"] += f"open({str(sentinel)!r}, 'w').write('executed')\n"
    state["sources"][0]["path"] = "../../not-a-real-source.py"
    state["candidate"]["path"] = "../../not-a-real-source.py"
    comments.build_request(state, comments.load_json(comments.RUBRIC))
    assert not sentinel.exists()


@pytest.mark.parametrize("oversize", [False, True])
def test_nonfinite_and_oversized_context_cannot_reach_helper(
    state: dict[str, Any], oversize: bool
) -> None:
    state["context"]["extra"] = "x" * comments.MAX_REQUEST_BYTES if oversize else float("nan")
    with pytest.raises(comments.ReviewError):
        comments.build_request(state, comments.load_json(comments.RUBRIC))


@pytest.mark.parametrize("explicit", [False, True])
def test_missing_helper_skips_optional_review(
    state_path: Path,
    tmp_path: Path,
    explicit: bool,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        comments.subprocess, "run", lambda *a, **k: pytest.fail("Missing helper was executed")
    )
    args = ["--state", str(state_path)]
    if explicit:
        args.extend(["--jev-helper", str(tmp_path / "not-installed.py")])
    assert comments.main(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "skipped" and report["reason"] == "jev_helper_unavailable"
    assert "answers" not in report


def test_subprocess_uses_parent_interpreter_and_forwards_provider_options(
    state_path: Path,
    state: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    helper = tmp_path / "helper with spaces.py"
    helper.touch()
    args = ["--state", str(state_path), "--jev-helper", str(helper)]
    for name in comments.PROVIDER_OPTIONS:
        args.extend(["--" + name.replace("_", "-"), f"test {name}"])
    request_file: Path | None = None

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        nonlocal request_file
        assert command[:3] == [sys.executable, str(helper), "--request"]
        request_file = Path(command[3])
        request = json.loads(request_file.read_text())
        assert request["state"] == state
        assert kwargs == {"capture_output": True, "timeout": 45, "check": False}
        assert command[4:] == args[4:]
        report = {
            "status": "evaluated",
            "request": {"model": "jev-test", **request},
            "answers": {name: {"test": True} for name in request["questions"]},
            "response": {"usage": {"input_tokens": 10}, "metadata": "unmodified"},
            "state_sha256": "helper-state-hash",
        }
        return subprocess.CompletedProcess(
            command, 0, json.dumps(report).encode(), b"secret-stderr"
        )

    monkeypatch.setattr(comments.subprocess, "run", run)
    assert comments.main(args) == 0
    output = capsys.readouterr().out
    assert "secret-stderr" not in output
    report = json.loads(output)
    assert report["request"]["state"] == state
    assert report["state_sha256"] == "helper-state-hash"
    assert report["response"]["metadata"] == "unmodified"
    assert report["response"]["usage"]["input_tokens"] == 10
    assert request_file is not None and not request_file.exists()


def test_actual_generic_helper_missing_key_is_skipped(
    state_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = tmp_path / "config.json"
    config.write_text("{}")
    assert (
        comments.main(
            [
                "--state",
                str(state_path),
                "--jev-helper",
                str(ROOT / "plugins/jev/skills/jev/scripts/jev.py"),
                "--config",
                str(config),
                "--env-file",
                str(tmp_path / "missing-env"),
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "skipped" and report["reason"] == "missing_api_key"
    assert report["provider"] == "vercel" and report["comment_rubric_version"]
    assert "answers" not in report


@pytest.mark.parametrize(
    ("code", "stdout"),
    [
        (1, '{"status":"evaluated"}'),
        (0, '{"status":"preview"}'),
        (0, '{"status":"evaluated"}'),
        (0, '{"status":"made_up_status"}'),
        (0, "[]"),
        (0, "invalid secret output"),
        (4, '{"status":"skipped"}'),
    ],
)
def test_unexpected_helper_results_are_incomplete_without_output_leaks(
    state_path: Path,
    tmp_path: Path,
    code: int,
    stdout: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    helper = tmp_path / "fake.py"
    helper.write_text("pass")
    monkeypatch.setattr(
        comments.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess([], code, stdout.encode(), b"secret stderr"),
    )
    assert comments.main(["--state", str(state_path), "--jev-helper", str(helper)]) == 2
    output = capsys.readouterr().out
    assert "secret" not in output
    assert json.loads(output)["status"] == "incomplete"


def test_delegated_incomplete_report_preserves_error_and_metadata(
    state_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    helper = tmp_path / "fake.py"
    helper.touch()
    report = {"status": "incomplete", "error": "Jev returned HTTP 503."}
    monkeypatch.setattr(
        comments.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess([], 2, json.dumps(report).encode(), b""),
    )
    assert comments.main(["--state", str(state_path), "--jev-helper", str(helper)]) == 2
    actual = json.loads(capsys.readouterr().out)
    assert actual["error"] == report["error"] and actual["comment_rubric_version"]
    assert "answers" not in actual


@pytest.mark.parametrize("timeout", [False, True])
def test_helper_launch_failures_are_incomplete(
    state_path: Path,
    tmp_path: Path,
    timeout: bool,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    helper = tmp_path / "fake.py"
    helper.touch()

    def fail(*args: Any, **kwargs: Any) -> None:
        if timeout:
            raise subprocess.TimeoutExpired("secret command", 45, stderr=b"secret stderr")
        raise OSError("secret error details")

    monkeypatch.setattr(comments.subprocess, "run", fail)
    assert comments.main(["--state", str(state_path), "--jev-helper", str(helper)]) == 2
    output = capsys.readouterr().out
    assert "secret" not in output
    assert json.loads(output)["status"] == "incomplete"


def test_malformed_json_does_not_echo_private_input(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"secret-text": broken')
    assert comments.main(["--state", str(path), "--dry-run"]) == 2
    output = capsys.readouterr().out
    assert "secret-text" not in output and json.loads(output)["status"] == "incomplete"


def evaluated_report(request: dict[str, Any]) -> dict[str, Any]:
    answers = {
        name: {"type": "boolean", "probability": 0.7}
        if name != "disposition"
        else {"type": "choice", "choice": "delete", "probabilities": {"delete": 1.0}}
        for name in request["questions"]
    }
    return {
        "status": "evaluated",
        "request": {"model": "jev-test", **request},
        "answers": answers,
        "response": {"answers": answers, "usage": {"input_tokens": 10}},
        "state_sha256": "proposal-hash" if "proposal" in request["state"] else "candidate-hash",
    }


def test_live_proposal_review_is_second_call_and_preserves_both_reports(
    state_path: Path,
    state: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state["proposal"] = {"replacement": ""}
    state_path.write_text(json.dumps(state))
    helper = tmp_path / "fake.py"
    helper.touch()
    requests: list[dict[str, Any]] = []

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        request = json.loads(Path(command[3]).read_text())
        requests.append(request)
        return subprocess.CompletedProcess(
            command, 0, json.dumps(evaluated_report(request)).encode()
        )

    monkeypatch.setattr(comments.subprocess, "run", run)
    assert comments.main(["--state", str(state_path), "--jev-helper", str(helper)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert len(requests) == 2
    assert "proposal" not in requests[0]["state"]
    assert set(requests[0]["questions"]) == {
        "context_sufficient",
        "information_loss",
        "disposition",
    }
    assert requests[1]["state"] == state
    assert set(requests[1]["questions"]) == {"proposal_preserves_information"}
    assert report["evaluated_scopes"] == ["candidate", "proposal"]
    assert report["state_sha256"] == "candidate-hash"
    assert report["proposal_review"]["state_sha256"] == "proposal-hash"
    assert report["request"]["state"] == requests[0]["state"]
    assert report["response"] == evaluated_report(requests[0])["response"]
    assert report["proposal_review"] == {
        **evaluated_report(requests[1]),
        "schema_version": 2,
        "advisory": True,
        "review_mode": "separate_candidate_and_proposal",
        "comment_rubric_version": report["comment_rubric_version"],
        "comment_rubric_sha256": report["comment_rubric_sha256"],
    }
    assert set(report["answers"]) == set(requests[0]["questions"]) | set(requests[1]["questions"])


@pytest.mark.parametrize("first_status", ["skipped", "incomplete"])
def test_no_proposal_call_after_candidate_missing_key_or_failure(
    state_path: Path,
    state: dict[str, Any],
    tmp_path: Path,
    first_status: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state["proposal"] = {"replacement": ""}
    state_path.write_text(json.dumps(state))
    helper = tmp_path / "fake.py"
    helper.touch()
    calls = 0
    code = 0 if first_status == "skipped" else 2

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        nonlocal calls
        calls += 1
        assert calls == 1
        request = json.loads(Path(command[3]).read_text())
        assert "proposal" not in request["state"]
        response = {"status": first_status, "reason": "missing_api_key"}
        return subprocess.CompletedProcess(command, code, json.dumps(response).encode())

    monkeypatch.setattr(comments.subprocess, "run", run)
    assert comments.main(["--state", str(state_path), "--jev-helper", str(helper)]) == code
    report = json.loads(capsys.readouterr().out)
    assert calls == 1 and report["status"] == first_status
    assert report["evaluated_scopes"] == []
    assert "proposal_review" not in report and "answers" not in report


@pytest.mark.parametrize("second_failure", ["skipped", "incomplete", "invalid_json", "timeout"])
def test_failed_second_call_keeps_candidate_evidence_without_claiming_complete_answers(
    state_path: Path,
    state: dict[str, Any],
    tmp_path: Path,
    second_failure: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state["proposal"] = {"replacement": ""}
    state_path.write_text(json.dumps(state))
    helper = tmp_path / "fake.py"
    helper.touch()
    requests: list[dict[str, Any]] = []

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        request = json.loads(Path(command[3]).read_text())
        requests.append(request)
        if len(requests) == 1:
            return subprocess.CompletedProcess(
                command, 0, json.dumps(evaluated_report(request)).encode()
            )
        assert len(requests) == 2
        if second_failure == "timeout":
            raise subprocess.TimeoutExpired("secret-command", 45, stderr=b"secret-stderr")
        if second_failure == "invalid_json":
            return subprocess.CompletedProcess(command, 0, b"secret invalid JSON", b"secret-stderr")
        response = {"status": second_failure, "reason": "provider_unavailable"}
        return subprocess.CompletedProcess(
            command, 0 if second_failure == "skipped" else 2, json.dumps(response).encode()
        )

    monkeypatch.setattr(comments.subprocess, "run", run)
    assert comments.main(["--state", str(state_path), "--jev-helper", str(helper)]) == 2
    output = capsys.readouterr().out
    assert "secret" not in output
    report = json.loads(output)
    assert len(requests) == 2 and report["status"] == "incomplete"
    assert report["reason"] == "proposal_review_incomplete"
    assert report["evaluated_scopes"] == ["candidate"]
    assert "answers" not in report
    assert report["partial_answers"] == evaluated_report(requests[0])["answers"]
    assert report["request"] == evaluated_report(requests[0])["request"]
    assert report["response"] == evaluated_report(requests[0])["response"]
    assert report["proposal_review"]["status"] in ("skipped", "incomplete")
