"""Offline behavior and provider-contract checks for the standalone Jev skill."""

from __future__ import annotations

import importlib.util
import io
import json
import urllib.error
from email.message import Message
from pathlib import Path
from typing import Any

import pytest

SKILL = Path(__file__).resolve().parents[1] / "plugins/jev/skills/jev"
spec = importlib.util.spec_from_file_location("generic_jev", SKILL / "scripts/jev.py")
assert spec is not None and spec.loader is not None
jev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jev)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jev, "DEFAULT_CONFIG", tmp_path / "config.json")
    monkeypatch.setattr(jev, "DEFAULT_ENV", tmp_path / "env")
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)


@pytest.fixture
def payload() -> dict[str, Any]:
    return json.loads((SKILL / "examples/review-plan.json").read_text())


@pytest.fixture
def request_file(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "request.json"
    path.write_text(json.dumps(payload))
    return path


def response_for(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": "jev-test",
        "answers": {
            "preservation_supported": {
                "type": "noul"
                if request["questions"]["preservation_supported"]["type"] == "noul"
                else "boolean",
                "noul"
                if request["questions"]["preservation_supported"]["type"] == "noul"
                else "probability": 0.03,
            },
            "next_step": {
                "type": "choice",
                "choice": "verify_failure_paths",
                "probabilities": {
                    "verify_failure_paths": 0.97,
                    "benchmark_success": 0.01,
                    "rename_helper": 0.01,
                    "none": 0.01,
                },
                "confidence": 0.95,
            },
            "evidence_coverage": {
                "type": "score",
                "score": 1.02,
                "probabilities": {"0": 0.01, "1": 0.97, "2": 0.01, "3": 0.01},
                "confidence": 0.95,
            },
        },
        "usage": {"input_tokens": 100, "output_tokens": 20},
    }


def test_preview_validates_example_without_credentials_or_network(
    request_file: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Preview accessed credentials or network")

    monkeypatch.setattr(jev, "load_key", forbidden)
    monkeypatch.setattr(jev, "evaluate", forbidden)
    assert jev.main(["--request", str(request_file), "--dry-run"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "preview"
    assert report["request"]["state"] == json.loads(request_file.read_text())["state"]
    assert report["questions_sha256"] == jev.digest(report["request"]["questions"])


def test_absent_key_skips_without_fabricating_answers(
    request_file: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(jev, "evaluate", lambda *_: pytest.fail("Missing key made a request"))
    assert jev.main(["--request", str(request_file)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "skipped"
    assert report["reason"] == "missing_api_key"
    assert "answers" not in report and "response" not in report


@pytest.mark.parametrize("provider", ["vercel", "typesafe"])
def test_provider_protocol_and_normalized_answers(
    provider: str,
    request_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []
    key_name = jev.PROVIDERS[provider]["api_key_env"]
    monkeypatch.setenv(key_name, "secret-test-key")

    class Provider:
        def open(self, request: Any, timeout: int) -> io.BytesIO:
            assert request.full_url == jev.PROVIDERS[provider]["endpoint"]
            assert request.get_header("Authorization") == "Bearer secret-test-key"
            assert request.get_method() == "POST" and timeout == 30
            body = json.loads(request.data)
            calls.append(body)
            result = response_for(body)
            result["metadata"] = {"echo": "secret-test-key"}
            return io.BytesIO(json.dumps(result).encode())

    monkeypatch.setattr(jev.urllib.request, "build_opener", lambda *_: Provider())
    assert jev.main(["--request", str(request_file), "--provider", provider]) == 0
    output = capsys.readouterr().out
    assert "secret-test-key" not in output
    report = json.loads(output)
    assert len(calls) == 1
    assert calls[0]["model"] == jev.PROVIDERS[provider]["model"]
    kind = "noul" if provider == "typesafe" else "boolean"
    assert calls[0]["questions"]["preservation_supported"]["type"] == kind
    assert report["response"]["answers"]["preservation_supported"]["type"] == kind
    assert report["answers"]["preservation_supported"] == {"type": "boolean", "probability": 0.03}
    assert report["status"] == "evaluated" and report["advisory"] is True
    assert report["response"]["usage"]["input_tokens"] == 100


def test_provider_switch_discards_old_endpoint_model_and_key_file(
    tmp_path: Path, request_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "provider": "vercel",
                "endpoint": "https://custom.example/evaluate",
                "model": "old-model",
                "api_key_env": "OLD_KEY",
                "env_file": str(tmp_path / "old-env"),
            }
        )
    )
    assert (
        jev.main(
            [
                "--request",
                str(request_file),
                "--config",
                str(config),
                "--provider",
                "typesafe",
                "--dry-run",
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["endpoint"] == jev.PROVIDERS["typesafe"]["endpoint"]
    assert report["api_key_env"] == "TYPESAFE_API_KEY"
    assert report["request"]["model"] == "jev-latest"


@pytest.mark.parametrize("key", ['quoted"key', r"slash\key", r'quote"and\slash'])
def test_escaped_credential_echo_redacts_values_and_keys_before_json_encoding(
    key: str,
    request_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("AI_GATEWAY_API_KEY", key)

    class EchoProvider:
        def open(self, request: Any, timeout: int) -> io.BytesIO:
            assert request.get_header("Authorization") == "Bearer " + key
            result = response_for(json.loads(request.data))
            result["metadata"] = {
                "echo": key,
                "nested": [{"prefix-" + key: "before-" + key + "-after"}],
                "unchanged": [0.5, True, None],
            }
            return io.BytesIO(json.dumps(result).encode())

    monkeypatch.setattr(jev.urllib.request, "build_opener", lambda *_: EchoProvider())
    assert jev.main(["--request", str(request_file)]) == 0
    output = capsys.readouterr().out
    report = json.loads(output)
    assert report["status"] == "evaluated"
    assert report["response"]["metadata"] == {
        "echo": "[REDACTED]",
        "nested": [{"prefix-[REDACTED]": "before-[REDACTED]-after"}],
        "unchanged": [0.5, True, None],
    }
    assert json.dumps(key)[1:-1] not in output


def test_custom_provider_requires_explicit_contract(
    request_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = ["--request", str(request_file), "--provider", "custom", "--dry-run"]
    assert jev.main(args) == 2
    capsys.readouterr()
    args += [
        "--endpoint",
        "https://custom.example/evaluate",
        "--model",
        "other-jev",
        "--protocol",
        "typesafe",
        "--api-key-env",
        "CUSTOM_KEY",
    ]
    assert jev.main(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["request"]["questions"]["preservation_supported"]["type"] == "noul"


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://example.org/evaluate",
        "https://u:p@example.org/evaluate",
        "https://example.org/evaluate?key=x",
        "https://example.org/evaluate#x",
        "https://example.org:bad/evaluate",
        "https://different-host.example/evaluate",
    ],
)
def test_unsafe_or_implicit_host_change_rejected_before_key_access(
    endpoint: str,
    request_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(jev, "load_key", lambda *_: pytest.fail("Read key for unsafe endpoint"))
    assert jev.main(["--request", str(request_file), "--endpoint", endpoint]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "incomplete"


@pytest.mark.parametrize(
    "question",
    [
        {"type": "text", "instructions": "Explain"},
        {"type": "boolean", "instructions": " "},
        {"type": "boolean", "instructions": "Does it hold?", "criteria": {"true": "yes"}},
        {"type": "score", "instructions": "Rate", "criteria": ["one level"]},
        {"type": "score", "instructions": "Rate", "criteria": ["x"] * 11},
        {"type": "choice", "instructions": "Choose", "criteria": {"only": None}},
        {"type": "choice", "instructions": "Choose", "criteria": {" ": None, "other": None}},
        {"type": "choice", "instructions": "Choose", "criteria": {"a": 123, "b": None}},
        {"type": "boolean", "instructions": "Does it hold?", "unknown": True},
    ],
)
def test_malformed_questions_rejected(question: dict[str, Any]) -> None:
    with pytest.raises(jev.ReviewError):
        jev.build_request({"state": "Some evidence", "questions": {"question": question}})


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"state": "", "questions": {}},
        {
            "state": "x",
            "questions": {"x": {"type": "boolean", "instructions": "x"}},
            "model": "untrusted",
        },
        {"state": "x", "questions": {"bad id": {"type": "boolean", "instructions": "x"}}},
        {"state": [float("nan")], "questions": {"x": {"type": "boolean", "instructions": "x"}}},
        {"state": "x" * 100_001, "questions": {"x": {"type": "boolean", "instructions": "x"}}},
        {
            "state": "x",
            "questions": {str(i): {"type": "boolean", "instructions": "x"} for i in range(33)},
        },
    ],
)
def test_invalid_request_bounds_fail(payload: Any) -> None:
    with pytest.raises(jev.ReviewError):
        jev.build_request(payload)


def test_structured_instructions_and_aliases_are_preserved() -> None:
    question = {
        "type": "noul",
        "instructions": {
            "question": "Does evidence support the claim?",
            "rule": ["Use supplied evidence only"],
        },
    }
    body = jev.build_request({"state": ["Evidence"], "questions": {"supported": question}})
    assert body["questions"]["supported"]["type"] == "boolean"
    assert body["questions"]["supported"]["instructions"] == question["instructions"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("probability", float("nan")),
        ("probability", True),
        ("probability", 1.1),
        ("probability", 10**400),
        ("type", "noul"),
    ],
)
def test_invalid_response_probability_or_type_rejected(
    payload: dict[str, Any], field: str, value: Any
) -> None:
    request = jev.build_request(payload)
    response = response_for(request)
    response["answers"]["preservation_supported"][field] = value
    with pytest.raises(jev.ReviewError):
        jev.validate_response(response, request["questions"])


@pytest.mark.parametrize(
    "mutation", ["missing", "extra", "bad_choice", "choice_type", "bad_score", "distribution"]
)
def test_response_must_match_requested_questions(payload: dict[str, Any], mutation: str) -> None:
    request = jev.build_request(payload)
    response = response_for(request)
    if mutation == "missing":
        del response["answers"]["next_step"]
    elif mutation == "extra":
        response["answers"]["unasked"] = {"type": "boolean", "probability": 1}
    elif mutation == "bad_choice":
        response["answers"]["next_step"]["choice"] = "not-a-candidate"
    elif mutation == "choice_type":
        response["answers"]["next_step"]["choice"] = []
    elif mutation == "bad_score":
        response["answers"]["evidence_coverage"]["score"] = 4
    else:
        response["answers"]["next_step"]["probabilities"]["none"] = 0.8
    with pytest.raises(jev.ReviewError):
        jev.validate_response(response, request["questions"])


@pytest.mark.parametrize("status", [302, 401, 429, 500])
def test_http_failure_is_incomplete_and_not_retried_or_leaked(
    status: int,
    request_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "secret-test-key")
    calls = []

    class BrokenProvider:
        def open(self, *args: Any, **kwargs: Any) -> None:
            calls.append(True)
            raise urllib.error.HTTPError(
                "https://provider.example",
                status,
                "sensitive body",
                Message(),
                io.BytesIO(b"secret-test-key"),
            )

    monkeypatch.setattr(jev.urllib.request, "build_opener", lambda *_: BrokenProvider())
    assert jev.main(["--request", str(request_file)]) == 2
    output = capsys.readouterr().out
    assert "secret-test-key" not in output and "sensitive body" not in output
    assert json.loads(output)["status"] == "incomplete" and len(calls) == 1


def test_env_is_literal_and_explicit_file_overrides_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "env"
    marker = tmp_path / "must-not-exist"
    path.write_text(f"touch {marker}\nexport AI_GATEWAY_API_KEY='file-key' # comment\n")
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "process-key")
    assert jev.load_key(None) == "process-key"
    assert jev.load_key(path) == "file-key"
    path.write_text(f"AI_GATEWAY_API_KEY='$(touch {marker})'\n")
    with pytest.raises(jev.ReviewError):
        jev.load_key(path)
    assert not marker.exists()


def test_redirect_handler_does_not_forward_credentials() -> None:
    assert (
        jev.NoRedirect().redirect_request(None, None, 302, "", None, "https://other.example")
        is None
    )


def test_invalid_utf8_is_structured_incomplete(
    request_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request_file.write_bytes(b"\xff")
    assert jev.main(["--request", str(request_file)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "incomplete"
