#!/usr/bin/env python3
"""Evaluate a curated Python function or call path with a configurable Jev provider.

--state reviews one snapshot with the snapshot rubric. --before and --after
compare two versions in one request with the change rubric, which asks what
the change introduced and removed. Python 3.10+, stdlib only. Prints JSON;
0 means evaluated/previewed/skipped, 2 means incomplete. Missing credentials
skip optional semantic review. A successful evaluation is advisory, never a
quality pass.
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
RUBRIC = Path(__file__).resolve().parent.parent / "references" / "jev-rubric.json"
CHANGE_RUBRIC = RUBRIC.with_name("jev-change-rubric.json")
DEFAULT_ENV = Path.home() / ".config" / "typesafe-ai" / "env"
DEFAULT_CONFIG = Path.home() / ".config" / "typesafe-ai" / "jev-review.json"
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


class ReviewError(Exception):
    """An incomplete review that must not be mistaken for a quality result."""


def encode(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(encode(value)).hexdigest()


def redact(value: Any, key: str) -> Any:
    """Remove literal credentials before JSON escaping changes their representation."""
    if isinstance(value, str):
        return value.replace(key, "[REDACTED]")
    if isinstance(value, list):
        return [redact(item, key) for item in value]
    if isinstance(value, dict):
        return {redact(name, key): redact(item, key) for name, item in value.items()}
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


def check_state(state: Any) -> None:
    if not isinstance(state, dict) or not isinstance(state.get("scope"), str):
        raise ReviewError("State needs a scope string and a nonempty sources array.")
    if not state["scope"].strip():
        raise ReviewError("State scope must not be empty.")
    sources = state.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ReviewError("State needs at least one source with path and content strings.")
    for source in sources:
        if not isinstance(source, dict) or any(
            not isinstance(source.get(key), str) or not source[key].strip()
            for key in ("path", "content")
        ):
            raise ReviewError("Each source needs nonempty path and content strings.")


def finish_request(
    state: dict[str, Any], rubric: dict[str, Any], model: str, protocol: str
) -> dict[str, Any]:
    questions = {
        name: {
            **question,
            "type": "noul"
            if protocol == "typesafe" and question["type"] == "boolean"
            else question["type"],
        }
        for name, question in rubric["questions"].items()
    }
    request = {"model": model, "state": state, "questions": questions}
    try:
        size = len(encode(request))
    except ValueError as error:
        raise ReviewError("State must contain finite JSON values.") from error
    if size > MAX_REQUEST_BYTES:
        raise ReviewError("Request exceeds 100,000 UTF-8 bytes; select a smaller coherent scope.")
    return request


def build_request(
    state: Any, rubric: dict[str, Any], model: str = MODEL, protocol: str = "gateway"
) -> dict[str, Any]:
    check_state(state)
    return finish_request(state, rubric, model, protocol)


def render_sources(sources: list[dict[str, str]]) -> str:
    """One version's code as a single string; several files are separated by path headers."""
    if len(sources) == 1:
        return sources[0]["content"]
    return "\n".join(f"# file: {s['path']}\n{s['content']}" for s in sources)


def build_change_request(
    before: Any, after: Any, rubric: dict[str, Any], model: str = MODEL, protocol: str = "gateway"
) -> dict[str, Any]:
    check_state(before)
    check_state(after)
    contract = ("task", "constraints")
    if any(before.get(key) != after.get(key) for key in contract):
        raise ReviewError("Before and after must state the same task and constraints.")
    # Only the contract and the two versions: supercov found that wrapping the versions in
    # more structure weakened detection. Measurements stay in the report, not the request.
    state: dict[str, Any] = {key: before[key] for key in contract if before.get(key)}
    state["before"] = render_sources(before["sources"])
    state["after"] = render_sources(after["sources"])
    return finish_request(state, rubric, model, protocol)


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
        # Credentials and selected source must stay at the explicitly selected endpoint.
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
    parser.add_argument("--state", type=Path, help="Curated source/context JSON")
    parser.add_argument("--before", type=Path, help="State JSON of the version before a change")
    parser.add_argument("--after", type=Path, help="State JSON of the version after the change")
    parser.add_argument("--env-file", type=Path, help="Literal key assignment; never executed")
    parser.add_argument("--config", type=Path, help="Provider JSON (default: user jev-review.json)")
    parser.add_argument("--provider", choices=PROVIDERS, help="Provider preset (default: vercel)")
    parser.add_argument("--endpoint", help="Full HTTPS evaluation URL")
    parser.add_argument("--model", help="Provider-specific Jev model identifier")
    parser.add_argument("--protocol", choices=("gateway", "typesafe"), help="Evaluation API shape")
    parser.add_argument(
        "--api-key-env", help="Environment variable holding the selected provider key"
    )
    parser.add_argument("--dry-run", action="store_true", help="Print request; no key or network")
    args = parser.parse_args(argv)
    change = args.before is not None or args.after is not None
    if change and (args.state is not None or args.before is None or args.after is None):
        parser.error("use --state alone, or --before and --after together")
    if not change and args.state is None:
        parser.error("--state, or --before and --after, is required")
    try:
        settings = provider_settings(args)
        if change:
            rubric = load_json(CHANGE_RUBRIC)
            before, after = load_json(args.before), load_json(args.after)
            request = build_change_request(
                before, after, rubric, settings["model"], settings["protocol"]
            )
        else:
            rubric = load_json(RUBRIC)
            request = build_request(
                load_json(args.state), rubric, settings["model"], settings["protocol"]
            )
        report: dict[str, Any] = {
            "schema_version": 1,
            "advisory": True,
            "provider": settings["provider"],
            "protocol": settings["protocol"],
            "endpoint": settings["endpoint"],
            "api_key_env": settings["api_key_env"],
            "rubric_version": rubric["version"],
            "rubric_sha256": digest(rubric["questions"]),
            "state_sha256": digest(request["state"]),
            "request": request,
        }
        if change:
            report["mode"] = "change"
            report["scope"] = {"before": before["scope"], "after": after["scope"]}
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
