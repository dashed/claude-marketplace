"""Offline contract and failure tests for the configurable Jev helper."""

from __future__ import annotations

import importlib.util
import io
import json
import urllib.error
from email.message import Message
from pathlib import Path
from typing import Any

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "plugins/python-complexity/skills/python-complexity/scripts/jev_review.py"
)
spec = importlib.util.spec_from_file_location("jev_review", SCRIPT)
assert spec is not None and spec.loader is not None
jev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jev)


@pytest.fixture(autouse=True)
def isolated_user_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jev, "DEFAULT_CONFIG", tmp_path / "no-user-config.json")


@pytest.fixture
def state_file(tmp_path: Path) -> Path:
    path = tmp_path / "state.json"
    path.write_text(
        json.dumps(
            {
                "scope": "demo.py:identity",
                "sources": [{"path": "demo.py", "content": "def identity(x): return x"}],
                "measurements": {"status": "not_run"},
            }
        )
    )
    return path


def gateway_response(questions: dict[str, Any]) -> dict[str, Any]:
    answers = {}
    for name, question in questions.items():
        kind = question["type"]
        if kind in ("boolean", "noul"):
            answers[name] = {"type": kind, "noul" if kind == "noul" else "probability": 0.9}
        else:
            keys = (
                list(question["criteria"])
                if kind == "choice"
                else [str(i) for i in range(len(question["criteria"]))]
            )
            answers[name] = {
                "type": kind,
                "probabilities": {key: float(i == 0) for i, key in enumerate(keys)},
                **({"choice": keys[0]} if kind == "choice" else {"score": 0}),
            }
    return {
        "model": "typesafe-ai/jev",
        "answers": answers,
        "usage": {"inputTokens": 123, "outputTokens": 42},
        "providerMetadata": {"gateway": {"cost": "0.01", "generationId": "example"}},
    }


def test_dry_run_needs_no_key_or_network(
    state_file: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Dry run accessed credentials or network")

    monkeypatch.setattr(jev, "load_key", forbidden)
    monkeypatch.setattr(jev, "evaluate", forbidden)
    assert jev.main(["--state", str(state_file), "--dry-run"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "preview"
    assert result["request"]["state"] == json.loads(state_file.read_text())
    assert "response" not in result


def test_literal_key_file_does_not_execute_shell(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    marker = tmp_path / "should-not-exist"
    credentials = tmp_path / "env"
    credentials.write_text(
        f"touch {marker}\nOTHER=$(touch {marker})\nexport AI_GATEWAY_API_KEY='file-key' # comment\n"
    )
    assert jev.load_key(credentials) == "file-key"
    assert not marker.exists()
    credentials.write_text(f"AI_GATEWAY_API_KEY='$(touch {marker})'\n")
    with pytest.raises(jev.ReviewError):
        jev.load_key(credentials)
    assert not marker.exists()


def test_credential_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    credentials = tmp_path / "env"
    credentials.write_text("AI_GATEWAY_API_KEY='file-key'\n")
    monkeypatch.setattr(jev, "DEFAULT_ENV", credentials)
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "process-key")
    assert jev.load_key(None) == "process-key"
    assert jev.load_key(credentials) == "file-key"
    monkeypatch.delenv("AI_GATEWAY_API_KEY")
    assert jev.load_key(None) == "file-key"


@pytest.mark.parametrize(
    "state",
    [
        {},
        {"scope": "x", "sources": []},
        {"scope": " ", "sources": [{"path": "x", "content": "x"}]},
        {"scope": "x", "sources": [{"path": "x"}]},
        {"scope": "x", "sources": [{"path": "x", "content": ""}]},
        {"scope": "x", "sources": [{"path": "x", "content": "x" * 100_001}]},
        {"scope": "x", "sources": [{"path": "x", "content": "x"}], "score": float("nan")},
    ],
)
def test_bad_state_fails_before_network(
    state: Any,
    state_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_file.write_text(json.dumps(state))
    monkeypatch.setattr(jev, "evaluate", lambda *_: pytest.fail("Network called for invalid state"))
    assert jev.main(["--state", str(state_file)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "incomplete"


@pytest.mark.parametrize("key", ["secret-test-key", 'secret"quoted-key', "secret\\slash-key"])
def test_live_contract_records_request_and_redacts_key(
    key: str,
    state_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []
    monkeypatch.setenv("AI_GATEWAY_API_KEY", key)

    class FakeGateway:
        def open(self, request: Any, timeout: int) -> io.BytesIO:
            assert request.full_url == "https://ai-gateway.vercel.sh/v1/evaluate"
            assert request.get_method() == "POST"
            assert request.get_header("Authorization") == "Bearer " + key
            assert timeout == 30
            payload = json.loads(request.data)
            calls.append(payload)
            response = gateway_response(payload["questions"])
            response["providerMetadata"]["echo"] = key
            response["providerMetadata"]["nested"] = [{key: "echo " + key}]
            return io.BytesIO(json.dumps(response).encode())

    monkeypatch.setattr(jev.urllib.request, "build_opener", lambda *_: FakeGateway())
    assert jev.main(["--state", str(state_file)]) == 0
    output = capsys.readouterr().out
    assert key not in output
    report = json.loads(output)
    assert report["response"]["providerMetadata"]["echo"] == "[REDACTED]"
    assert report["response"]["providerMetadata"]["nested"] == [{"[REDACTED]": "echo [REDACTED]"}]
    assert len(calls) == 1
    assert report["request"] == calls[0]
    assert report["status"] == "evaluated" and report["advisory"] is True
    assert report["response"]["usage"]["inputTokens"] == 123
    assert report["response"]["providerMetadata"]["gateway"]["cost"] == "0.01"
    assert report["state_sha256"] == jev.digest(calls[0]["state"])
    assert report["rubric_sha256"] == jev.digest(calls[0]["questions"])


@pytest.mark.parametrize("code", [401, 429, 500, 302])
def test_http_errors_are_incomplete_without_retry_or_body_leak(
    code: int,
    state_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "secret-test-key")
    calls = []

    class BrokenGateway:
        def open(self, *args: Any, **kwargs: Any) -> None:
            calls.append(1)
            raise urllib.error.HTTPError(
                jev.ENDPOINT, code, "secret-test-key", Message(), io.BytesIO(b"private-source")
            )

    monkeypatch.setattr(jev.urllib.request, "build_opener", lambda *_: BrokenGateway())
    assert jev.main(["--state", str(state_file)]) == 2
    output = capsys.readouterr().out
    assert "secret-test-key" not in output and "private-source" not in output
    assert len(calls) == 1
    report = json.loads(output)
    assert report["status"] == "incomplete" and "response" not in report
    assert str(code) in report["error"]


def test_redirects_are_refused() -> None:
    assert (
        jev.NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://elsewhere") is None
    )


@pytest.mark.parametrize(
    "broken",
    [
        {},
        {"type": "boolean", "probability": True},
        {"type": "boolean", "probability": float("nan")},
        {"type": "boolean", "probability": 1.01},
        {"type": "boolean", "probability": 10**400},
        {"type": "score", "score": 0, "probabilities": {"0": 1}},
    ],
)
def test_rejects_malformed_boolean(broken: Any) -> None:
    questions = {"condition": {"type": "boolean"}}
    with pytest.raises(jev.ReviewError):
        jev.validate_response({"model": jev.MODEL, "answers": {"condition": broken}}, questions)


def test_unhashable_choice_is_rejected_as_review_error() -> None:
    question = {"action": {"type": "choice", "criteria": {"yes": "Yes", "no": "No"}}}
    response = gateway_response(question)
    response["answers"]["action"]["choice"] = []
    with pytest.raises(jev.ReviewError, match="Invalid choice"):
        jev.validate_response(response, question)


@pytest.mark.parametrize("failure", ["timeout", "bad_json", "nonfinite_metadata"])
def test_transport_and_metadata_failures_are_incomplete(
    failure: str,
    state_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "secret-test-key")

    class InvalidGateway:
        def open(self, request: Any, **kwargs: Any) -> io.BytesIO:
            if failure == "timeout":
                raise TimeoutError("secret-test-key")
            if failure == "bad_json":
                return io.BytesIO(b"not JSON: secret-test-key")
            response = gateway_response(json.loads(request.data)["questions"])
            response["providerMetadata"]["invalid"] = float("nan")
            return io.BytesIO(json.dumps(response).encode())

    monkeypatch.setattr(jev.urllib.request, "build_opener", lambda *_: InvalidGateway())
    assert jev.main(["--state", str(state_file)]) == 2
    output = capsys.readouterr().out
    assert "secret-test-key" not in output
    assert json.loads(output)["status"] == "incomplete"


@pytest.mark.parametrize("defect", ["missing", "score", "distribution", "choice"])
def test_rejects_incomplete_or_invalid_typed_answers(defect: str) -> None:
    questions = {
        "readability": {"type": "score", "criteria": ["opaque", "clear"]},
        "cost": {"type": "choice", "criteria": {"nesting": "nested", "none": "clear"}},
    }
    response = gateway_response(questions)
    if defect == "missing":
        del response["answers"]["cost"]
    elif defect == "score":
        response["answers"]["readability"]["score"] = 2
    elif defect == "distribution":
        response["answers"]["readability"]["probabilities"] = {"0": 0.2, "1": 0.2}
    else:
        response["answers"]["cost"]["choice"] = "invented"
    with pytest.raises(jev.ReviewError):
        jev.validate_response(response, questions)


@pytest.mark.parametrize(
    "contents",
    [None, "", "OTHER=value\n", "AI_GATEWAY_API_KEY=''\n", "export AI_GATEWAY_API_KEY=\n"],
)
def test_missing_credentials_skips_without_network(
    contents: str | None,
    state_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    credentials = tmp_path / "env"
    if contents is not None:
        credentials.write_text(contents)
    monkeypatch.setattr(jev, "DEFAULT_ENV", credentials)
    monkeypatch.setattr(jev, "evaluate", lambda *_: pytest.fail("Network called without a key"))
    assert jev.main(["--state", str(state_file)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "skipped" and report["reason"] == "missing_api_key"
    assert "response" not in report and "evaluated_at" not in report


@pytest.mark.parametrize("key", ["$(secret-command)", "invalid key"])
def test_configured_malformed_key_remains_an_error(
    key: str,
    state_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("AI_GATEWAY_API_KEY", key)
    monkeypatch.setattr(
        jev, "evaluate", lambda *_: pytest.fail("Network called with malformed key")
    )
    assert jev.main(["--state", str(state_file)]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "incomplete" and "response" not in report


def test_typesafe_preset_converts_request_and_normalizes_answers(
    state_file: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("TYPESAFE_API_KEY", "native-key")
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "wrong-provider-key")

    class NativeAPI:
        def open(self, request: Any, timeout: int) -> io.BytesIO:
            assert request.full_url == "https://api.typesafe.ai/v1/systemone"
            assert request.get_header("Authorization") == "Bearer native-key"
            body = json.loads(request.data)
            assert body["model"] == "jev-latest"
            assert body["questions"]["split_helpful"]["type"] == "noul"
            response = gateway_response(body["questions"])
            response["model"] = "jev-1.13.0"
            response["usage"] = {"input_tokens": 123, "output_tokens": 42}
            return io.BytesIO(json.dumps(response).encode())

    monkeypatch.setattr(jev.urllib.request, "build_opener", lambda *_: NativeAPI())
    assert jev.main(["--state", str(state_file), "--provider", "typesafe"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["provider"] == "typesafe" and result["protocol"] == "typesafe"
    assert result["response"]["answers"]["split_helpful"] == {"type": "noul", "noul": 0.9}
    assert result["answers"]["split_helpful"] == {"type": "boolean", "probability": 0.9}
    assert result["response"]["usage"]["input_tokens"] == 123
    assert result["rubric_sha256"] == jev.digest(jev.load_json(jev.RUBRIC)["questions"])


def test_missing_selected_provider_key_does_not_fall_back_to_vercel(
    state_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "wrong-provider-key")
    credentials = tmp_path / "env"
    credentials.write_text("AI_GATEWAY_API_KEY='file-vercel-key'\n")
    monkeypatch.setattr(jev, "DEFAULT_ENV", credentials)
    monkeypatch.setattr(jev, "evaluate", lambda *_: pytest.fail("Used the wrong provider key"))
    assert jev.main(["--state", str(state_file), "--provider", "typesafe"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "skipped" and result["api_key_env"] == "TYPESAFE_API_KEY"


def test_config_and_cli_overrides(
    state_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = tmp_path / "provider.json"
    config.write_text(
        json.dumps(
            {
                "provider": "custom",
                "endpoint": "https://example.org/evaluate",
                "protocol": "gateway",
                "api_key_env": "CUSTOM_JEV_KEY",
                "model": "jev-custom",
            }
        )
    )
    assert (
        jev.main(
            [
                "--state",
                str(state_file),
                "--config",
                str(config),
                "--model",
                "jev-pinned",
                "--dry-run",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["endpoint"] == "https://example.org/evaluate"
    assert result["request"]["model"] == "jev-pinned"
    assert result["api_key_env"] == "CUSTOM_JEV_KEY"

    # A different preset must not inherit the custom host, model, or key variable.
    assert (
        jev.main(
            [
                "--state",
                str(state_file),
                "--config",
                str(config),
                "--provider",
                "typesafe",
                "--dry-run",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["endpoint"] == "https://api.typesafe.ai/v1/systemone"
    assert result["request"]["model"] == "jev-latest"
    assert result["api_key_env"] == "TYPESAFE_API_KEY"


def test_custom_provider_loads_only_its_named_key(
    state_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    credentials = tmp_path / "env"
    credentials.write_text("AI_GATEWAY_API_KEY='wrong-key'\nCUSTOM_JEV_KEY='custom-key'\n")

    def evaluate(request: dict[str, Any], key: str, endpoint: str) -> dict[str, Any]:
        assert key == "custom-key" and endpoint == "https://example.org/eval"
        return gateway_response(request["questions"])

    monkeypatch.setattr(jev, "evaluate", evaluate)
    assert (
        jev.main(
            [
                "--state",
                str(state_file),
                "--provider",
                "custom",
                "--protocol",
                "gateway",
                "--endpoint",
                "https://example.org/eval",
                "--model",
                "jev-custom",
                "--api-key-env",
                "CUSTOM_JEV_KEY",
                "--env-file",
                str(credentials),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "evaluated"


@pytest.mark.parametrize(
    "config",
    [
        {"provider": "custom"},
        {"provider": "unknown"},
        {"api_key": "secret-should-not-be-in-config"},
        {"model": ""},
        {"protocol": "unknown"},
        {"api_key_env": "NOT=A_NAME"},
        {"endpoint": "https://other-host.example/eval"},
        {"endpoint": "http://ai-gateway.vercel.sh/v1/evaluate"},
        {"endpoint": "https://user:secret@ai-gateway.vercel.sh/eval"},
        {"endpoint": "https://ai-gateway.vercel.sh/eval?key=secret"},
        {"endpoint": "https://ai-gateway.vercel.sh:invalid/eval"},
    ],
)
def test_bad_provider_config_fails_before_credentials(
    config: Any,
    state_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    monkeypatch.setattr(jev, "load_key", lambda *_: pytest.fail("Read credentials for bad config"))
    assert jev.main(["--state", str(state_file), "--config", str(path)]) == 2
    output = capsys.readouterr().out
    assert "secret" not in output
    assert json.loads(output)["status"] == "incomplete"
