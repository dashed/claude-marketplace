#!/usr/bin/env python3
"""Ask bounded typed questions of Jev using a configurable provider.

Python 3.10+, stdlib only. Prints JSON; 0 means evaluated/previewed/skipped,
2 means incomplete. Missing credentials skip the optional judgment.
A successful evaluation is advisory, never a correctness or authorization proof.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shlex
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENDPOINT = "https://ai-gateway.vercel.sh/v1/evaluate"
MODEL = "typesafe-ai/jev"
DEFAULT_ENV = Path.home() / ".config" / "typesafe-ai" / "env"
DEFAULT_CONFIG = Path.home() / ".config" / "typesafe-ai" / "jev.json"
PROVIDERS = {
    "vercel": {
        "endpoint": ENDPOINT,
        "model": MODEL,
        "protocol": "gateway",
        "api_key_env": "AI_GATEWAY_API_KEY",
    },
    "typesafe": {
        "endpoint": "https://api.typesafe.ai/v1/systemone",
        "model": "jev-latest",
        "protocol": "typesafe",
        "api_key_env": "TYPESAFE_API_KEY",
    },
    "custom": {},
}
MAX_REQUEST_BYTES = 100_000  # Local bound, not a claim about the model's token limit.
MAX_QUESTIONS = 32  # Keep each call bounded; split unrelated decisions.


class ReviewError(Exception):
    """An incomplete review that must not be mistaken for a quality result."""


def encode(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(encode(value)).hexdigest()


def redact(value: Any, secret: str) -> Any:
    """Redact JSON strings before serialization can escape part of the credential."""
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]")
    if isinstance(value, list):
        return [redact(item, secret) for item in value]
    if isinstance(value, dict):
        return {redact(name, secret): redact(item, secret) for name, item in value.items()}
    return value


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        # Do not echo file content or exception excerpts containing source/secrets.
        raise ReviewError("Could not read valid UTF-8 JSON input.") from error


def provider_settings(args: argparse.Namespace) -> dict[str, str]:
    config_path = args.config or DEFAULT_CONFIG
    config = load_json(config_path) if args.config or config_path.exists() else {}
    fields = {"provider", "endpoint", "model", "protocol", "api_key_env", "env_file"}
    if not isinstance(config, dict) or set(config) - fields:
        raise ReviewError("Provider config contains unknown fields; store keys in the env file.")
    if any(not isinstance(value, str) or not value.strip() for value in config.values()):
        raise ReviewError("Provider config values must be nonempty strings.")
    provider = args.provider or config.get("provider", "vercel")
    if provider not in PROVIDERS:
        raise ReviewError("Provider must be vercel, typesafe, or custom.")
    # Switching a preset via CLI discards the other provider's config overrides.
    if args.provider and args.provider != config.get("provider", "vercel"):
        config = {}
    settings = {**PROVIDERS[provider], **config, "provider": provider}
    for name in fields - {"provider"}:
        value = getattr(args, name)
        if value is not None:
            settings[name] = str(value)
    if any(not settings.get(name, "").strip() for name in fields - {"env_file"}):
        raise ReviewError("Custom providers require endpoint, model, protocol, and api_key_env.")
    if settings["protocol"] not in ("gateway", "typesafe"):
        raise ReviewError("Protocol must be gateway or typesafe.")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", settings["api_key_env"]):
        raise ReviewError("api_key_env must name an environment variable.")
    try:
        url = urllib.parse.urlsplit(settings["endpoint"])
        url.port  # Validate a configured port before loading credentials.
    except ValueError as error:
        raise ReviewError("Endpoint is not a valid URL.") from error
    if (
        url.scheme != "https"
        or not url.hostname
        or url.username is not None
        or url.password is not None
        or url.query
        or url.fragment
    ):
        raise ReviewError("Endpoint must be an HTTPS URL without credentials, query, or fragment.")
    preset_url = PROVIDERS[provider].get("endpoint")
    if (
        preset_url
        and url.netloc != urllib.parse.urlsplit(preset_url).netloc
        and not (args.api_key_env or config.get("api_key_env"))
    ):
        raise ReviewError("Changing the provider host requires an explicit api_key_env.")
    return settings


def description(value: Any) -> bool:
    return isinstance(value, (str, dict, list)) and bool(
        value.strip() if isinstance(value, str) else value
    )


def validate_question(question: Any) -> None:
    if not isinstance(question, dict) or set(question) - {"type", "instructions", "criteria"}:
        raise ReviewError("Questions support only type, instructions, and criteria.")
    if not description(question.get("instructions")):
        raise ReviewError("Each question needs nonempty string, object, or array instructions.")
    kind = question.get("type")
    criteria = question.get("criteria")
    if kind in ("boolean", "noul"):
        if criteria is not None and (
            not isinstance(criteria, dict)
            or set(criteria) != {"true", "false"}
            or not all(description(value) for value in criteria.values())
        ):
            raise ReviewError("Boolean criteria must describe both true and false.")
    elif kind == "score":
        if (
            not isinstance(criteria, list)
            or not 2 <= len(criteria) <= 10
            or not all(description(level) for level in criteria)
        ):
            raise ReviewError("Score criteria need 2-10 nonempty ordered level descriptions.")
    elif kind == "choice":
        if (
            not isinstance(criteria, dict)
            or not 2 <= len(criteria) <= 255
            or any(not isinstance(key, str) or not key.strip() for key in criteria)
            or not all(value is None or description(value) for value in criteria.values())
        ):
            raise ReviewError("Choice criteria need 2-255 named options with descriptions or null.")
    else:
        raise ReviewError("Question type must be boolean, noul, score, or choice.")


def build_request(payload: Any, model: str = MODEL, protocol: str = "gateway") -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"state", "questions"}:
        raise ReviewError("Request JSON must contain exactly state and questions.")
    if not description(payload["state"]):
        raise ReviewError("State must be a nonempty string, object, or array.")
    questions = payload["questions"]
    if not isinstance(questions, dict) or not 1 <= len(questions) <= MAX_QUESTIONS:
        raise ReviewError("Request needs 1-32 questions.")
    for name, question in questions.items():
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", name):
            raise ReviewError(
                "Question IDs need 1-80 ASCII letters, digits, underscores, or hyphens."
            )
        validate_question(question)
    questions = {
        name: {
            **question,
            "type": ("noul" if protocol == "typesafe" else "boolean")
            if question["type"] in ("boolean", "noul")
            else question["type"],
        }
        for name, question in questions.items()
    }
    request = {"model": model, "state": payload["state"], "questions": questions}
    try:
        size = len(encode(request))
    except ValueError as error:
        raise ReviewError("Request must contain finite JSON values.") from error
    if size > MAX_REQUEST_BYTES:
        raise ReviewError("Request exceeds 100,000 UTF-8 bytes; select a smaller coherent scope.")
    return request


def load_key(env_file: Path | None, key_name: str = "AI_GATEWAY_API_KEY") -> str | None:
    # An explicit file wins; otherwise prefer the process environment, then our convention.
    key = os.environ.get(key_name, "") if env_file is None else ""
    if not key:
        path = (env_file or DEFAULT_ENV).expanduser()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as error:
            raise ReviewError("Could not read the provider key file.") from error
        for line in lines:
            if not re.match(rf"^\s*(?:export\s+)?{re.escape(key_name)}\s*=", line):
                continue
            try:
                parts = shlex.split(line, comments=True)
            except ValueError as error:
                raise ReviewError(f"Malformed {key_name} assignment.") from error
            if parts and parts[0] == "export":
                parts = parts[1:]
            if len(parts) != 1 or not parts[0].startswith(key_name + "="):
                raise ReviewError(f"Use {key_name}='value' with optional export.")
            key = parts[0].partition("=")[2]
    if not key:
        return None
    if any(char.isspace() for char in key) or "$" in key or "`" in key:
        raise ReviewError(f"{key_name} must be a nonempty literal key.")
    return key


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        # Credentials and selected state must stay at the explicitly selected endpoint.
        return None


def evaluate(request: dict[str, Any], key: str, endpoint: str = ENDPOINT) -> dict[str, Any]:
    http_request = urllib.request.Request(
        endpoint,
        data=encode(request),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.build_opener(NoRedirect()).open(http_request, timeout=30) as response:
            result = json.load(response)
            encode(result)  # Reject non-finite values anywhere, including provider metadata.
    except urllib.error.HTTPError as error:
        raise ReviewError(
            f"Provider returned HTTP {error.code}; evaluation incomplete. No automatic retry."
        ) from error
    except (OSError, ValueError) as error:
        raise ReviewError(
            "Provider network error or invalid JSON; evaluation incomplete."
        ) from error
    validate_response(result, request["questions"])
    return result


def finite_number(value: Any, maximum: float) -> bool:
    # Bounds first avoid overflowing float conversion for an arbitrary JSON integer.
    return type(value) in (int, float) and 0 <= value <= maximum and math.isfinite(value)


def validate_response(result: Any, questions: dict[str, Any]) -> None:
    if not isinstance(result, dict) or not isinstance(result.get("model"), str):
        raise ReviewError("Provider response is missing its model.")
    answers = result.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(questions):
        raise ReviewError("Provider response has missing or unexpected answers.")
    for name, question in questions.items():
        answer = answers[name]
        kind = question["type"]
        if not isinstance(answer, dict) or answer.get("type") != kind:
            raise ReviewError(f"Invalid answer type for {name}.")
        if kind in ("boolean", "noul"):
            field = "noul" if kind == "noul" else "probability"
            if not finite_number(answer.get(field), 1):
                raise ReviewError(f"Invalid probability for {name}.")
            continue
        criteria = question["criteria"]
        keys = set(criteria) if kind == "choice" else {str(i) for i in range(len(criteria))}
        probabilities = answer.get("probabilities")
        if (
            not isinstance(probabilities, dict)
            or set(probabilities) != keys
            or not all(finite_number(value, 1) for value in probabilities.values())
            or not math.isclose(sum(probabilities.values()), 1, abs_tol=0.025)
        ):
            raise ReviewError(f"Invalid probability distribution for {name}.")
        if kind == "score" and not finite_number(answer.get("score"), len(criteria) - 1):
            raise ReviewError(f"Invalid score for {name}.")
        if kind == "choice" and (
            not isinstance(answer.get("choice"), str) or answer["choice"] not in keys
        ):
            raise ReviewError(f"Invalid choice for {name}.")
        if "confidence" in answer and not finite_number(answer["confidence"], 1):
            raise ReviewError(f"Invalid confidence for {name}.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path, help="JSON with state and questions")
    parser.add_argument("--env-file", type=Path, help="Literal key assignment; never executed")
    parser.add_argument("--config", type=Path, help="Provider JSON (default: user jev.json)")
    parser.add_argument("--provider", choices=PROVIDERS, help="Provider preset (default: vercel)")
    parser.add_argument("--endpoint", help="Full HTTPS evaluation URL")
    parser.add_argument("--model", help="Provider-specific Jev model identifier")
    parser.add_argument("--protocol", choices=("gateway", "typesafe"), help="Evaluation API shape")
    parser.add_argument(
        "--api-key-env", help="Environment variable holding the selected provider key"
    )
    parser.add_argument("--dry-run", action="store_true", help="Print request; no key or network")
    args = parser.parse_args(argv)
    try:
        settings = provider_settings(args)
        request = build_request(load_json(args.request), settings["model"], settings["protocol"])
        report: dict[str, Any] = {
            "schema_version": 1,
            "advisory": True,
            "provider": settings["provider"],
            "protocol": settings["protocol"],
            "endpoint": settings["endpoint"],
            "api_key_env": settings["api_key_env"],
            "questions_sha256": digest(request["questions"]),
            "state_sha256": digest(request["state"]),
            "request": request,
        }
        key = None
        if args.dry_run:
            report["status"] = "preview"
        else:
            env_file = Path(settings["env_file"]) if "env_file" in settings else None
            key = load_key(env_file, settings["api_key_env"])
            if key is None:
                report["status"] = "skipped"
                report["reason"] = "missing_api_key"
            else:
                started = time.monotonic()
                response = evaluate(request, key, settings["endpoint"])
                report["response"] = response
                report["answers"] = {
                    name: {"type": "boolean", "probability": answer["noul"]}
                    if answer["type"] == "noul"
                    else answer
                    for name, answer in response["answers"].items()
                }
                report["elapsed_seconds"] = round(time.monotonic() - started, 3)
                report["evaluated_at"] = datetime.now(timezone.utc).isoformat()
                report["status"] = "evaluated"
        if key is not None:
            report = redact(report, key)
        print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except ReviewError as error:
        print(json.dumps({"status": "incomplete", "advisory": True, "error": str(error)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
