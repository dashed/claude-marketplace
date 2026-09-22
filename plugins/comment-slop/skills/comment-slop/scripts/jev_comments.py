#!/usr/bin/env python3
"""Request optional Jev advice about one source-anchored comment or docstring.

Python 3.10+, stdlib only. Use an explicitly selected general Jev helper for
provider configuration, credentials, transport, and typed response validation.
This adapter never changes files or executes the supplied source.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

RUBRIC = Path(__file__).resolve().parents[1] / "references/jev-rubric.json"
MAX_REQUEST_BYTES = 100_000
PROVIDER_OPTIONS = (
    "config",
    "provider",
    "endpoint",
    "model",
    "protocol",
    "api_key_env",
    "env_file",
)


class ReviewError(Exception):
    """The optional review could not be completed."""


def encode(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ReviewError("Could not read valid UTF-8 JSON input.") from error


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def anchored_candidate(state: dict[str, Any], sources: dict[str, str]) -> None:
    candidate = state.get("candidate")
    if not isinstance(candidate, dict):
        raise ReviewError("State needs one candidate object.")
    path, text = candidate.get("path"), candidate.get("text")
    if not isinstance(path, str) or path not in sources:
        raise ReviewError("Candidate path must match exactly one supplied source.")
    if not nonempty_string(text):
        raise ReviewError("Candidate text must be nonempty.")
    start, end = candidate.get("start_line"), candidate.get("end_line")
    lines = sources[path].splitlines(keepends=True)
    if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines):
        raise ReviewError("Candidate lines must be inclusive positive integers within the source.")
    window = "".join(lines[start - 1 : end])
    position = window.find(text)
    if position < 0 or window.find(text, position + 1) >= 0:
        raise ReviewError("Candidate text must occur exactly once within its source line range.")


def validate_state(state: Any) -> None:
    if not isinstance(state, dict):
        raise ReviewError("State must be an object.")
    if not all(nonempty_string(state.get(name)) for name in ("scope", "language")):
        raise ReviewError("State needs nonempty scope and language strings.")
    if not isinstance(state.get("context"), dict):
        raise ReviewError("State needs a context object; record known facts and missing evidence.")
    raw_sources = state.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ReviewError("State needs nonempty sources containing path and content.")
    sources: dict[str, str] = {}
    for source in raw_sources:
        if (
            not isinstance(source, dict)
            or not nonempty_string(source.get("path"))
            or not isinstance(source.get("content"), str)
        ):
            raise ReviewError("Each source needs a nonempty path and string content.")
        if source["path"] in sources:
            raise ReviewError("Source paths must be unique.")
        sources[source["path"]] = source["content"]
    anchored_candidate(state, sources)
    if "proposal" in state and (
        not isinstance(state["proposal"], dict)
        or not isinstance(state["proposal"].get("replacement"), str)
    ):
        raise ReviewError("Proposal needs a replacement string; an empty string means deletion.")


def build_request(state: Any, rubric: Any, *, proposal_review: bool = False) -> dict[str, Any]:
    validate_state(state)
    if (
        not isinstance(rubric, dict)
        or not nonempty_string(rubric.get("version"))
        or not isinstance(rubric.get("questions"), dict)
        or set(rubric["questions"])
        != {
            "context_sufficient",
            "information_loss",
            "disposition",
            "proposal_preserves_information",
        }
    ):
        raise ReviewError("Comment rubric must provide its version and four named questions.")
    if proposal_review and "proposal" not in state:
        raise ReviewError("A proposal review needs an explicit replacement.")
    questions = {
        name: question
        for name, question in rubric["questions"].items()
        if (name == "proposal_preserves_information") == proposal_review
    }
    review_state = state if proposal_review else {k: v for k, v in state.items() if k != "proposal"}
    request = {"state": review_state, "questions": questions}
    try:
        size = len(encode(request))
    except (ValueError, TypeError) as error:
        raise ReviewError("Request must contain finite JSON values.") from error
    if size > MAX_REQUEST_BYTES:
        raise ReviewError("Request exceeds 100,000 UTF-8 bytes; select a smaller coherent scope.")
    return request


def run_helper(
    args: argparse.Namespace, request: dict[str, Any], metadata: dict[str, Any]
) -> tuple[dict[str, Any], int]:
    helper = args.jev_helper
    if helper is None or not helper.expanduser().is_file():
        return {**metadata, "status": "skipped", "reason": "jev_helper_unavailable"}, 0
    with tempfile.TemporaryDirectory(prefix="comment-slop-jev-") as directory:
        request_path = Path(directory) / "request.json"
        request_path.write_bytes(encode(request))
        command = [sys.executable, str(helper.expanduser()), "--request", str(request_path)]
        for name in PROVIDER_OPTIONS:
            value = getattr(args, name)
            if value is not None:
                command.extend(["--" + name.replace("_", "-"), str(value)])
        try:
            process = subprocess.run(command, capture_output=True, timeout=45, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ReviewError("The selected Jev helper could not complete its review.") from error
    # Never echo child stderr or invalid stdout: either may contain source or credentials.
    try:
        report = json.loads(process.stdout)
    except (ValueError, UnicodeError) as error:
        raise ReviewError("The selected Jev helper did not return a JSON report.") from error
    if not isinstance(report, dict):
        raise ReviewError("The selected Jev helper did not return an object report.")
    status = report.get("status")
    if process.returncode == 2 and status == "incomplete":
        return {**report, **metadata}, 2
    if process.returncode != 0 or status not in ("evaluated", "skipped"):
        raise ReviewError("The selected Jev helper returned an unsuccessful review.")
    if status == "evaluated" and (
        not isinstance(report.get("request"), dict)
        or not isinstance(report.get("answers"), dict)
        or set(report["answers"]) != set(request["questions"])
        or not isinstance(report.get("response"), dict)
    ):
        raise ReviewError("The selected Jev helper returned an incomplete evaluated report.")
    return {**report, **metadata}, 0


def helper_review(
    args: argparse.Namespace, request: dict[str, Any], metadata: dict[str, Any]
) -> tuple[dict[str, Any], int]:
    try:
        return run_helper(args, request, metadata)
    except ReviewError as error:
        return {**metadata, "status": "incomplete", "error": str(error)}, 2
    except OSError:
        return {
            **metadata,
            "status": "incomplete",
            "error": "Could not prepare the Jev review.",
        }, 2


def evaluate_reviews(
    args: argparse.Namespace,
    request: dict[str, Any],
    proposal_request: dict[str, Any] | None,
    metadata: dict[str, Any],
) -> tuple[dict[str, Any], int]:
    report, code = helper_review(args, request, metadata)
    report["evaluated_scopes"] = ["candidate"] if report["status"] == "evaluated" else []
    if report["status"] != "evaluated" or proposal_request is None:
        return report, code
    proposal_report, _ = helper_review(args, proposal_request, metadata)
    report["proposal_review"] = proposal_report
    if proposal_report["status"] != "evaluated":
        report["status"] = "incomplete"
        report["reason"] = "proposal_review_incomplete"
        report["error"] = "Candidate evaluated, but the proposal review did not complete."
        report["partial_answers"] = report.pop("answers")
        return report, 2
    # Top-level request/response remain the candidate's originals; the second
    # report retains its own request, raw response, and provenance.
    report["answers"] = {**report["answers"], **proposal_report["answers"]}
    report["evaluated_scopes"].append("proposal")
    return report, 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, type=Path, help="JSON with source and candidate")
    parser.add_argument(
        "--jev-helper", type=Path, help="Explicit path to installed Jev scripts/jev.py"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print request; no helper/key/network"
    )
    for name in PROVIDER_OPTIONS:
        parser.add_argument("--" + name.replace("_", "-"), help="Forward to the general Jev helper")
    args = parser.parse_args(argv)
    metadata: dict[str, Any] = {
        "schema_version": 2,
        "advisory": True,
        "review_mode": "separate_candidate_and_proposal",
    }
    try:
        rubric = load_json(RUBRIC)
        state = load_json(args.state)
        request = build_request(state, rubric)
        proposal_request = (
            build_request(state, rubric, proposal_review=True) if "proposal" in state else None
        )
        metadata.update(
            comment_rubric_version=rubric["version"],
            comment_rubric_sha256=hashlib.sha256(encode(rubric)).hexdigest(),
        )
        if args.dry_run:
            report, code = {**metadata, "status": "preview", "request": request}, 0
            if proposal_request is not None:
                report["proposal_request"] = proposal_request
        else:
            report, code = evaluate_reviews(args, request, proposal_request, metadata)
        print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
        return code
    except ReviewError as error:
        print(json.dumps({**metadata, "status": "incomplete", "error": str(error)}))
        return 2
    except OSError:
        print(
            json.dumps(
                {**metadata, "status": "incomplete", "error": "Could not prepare the Jev review."}
            )
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
