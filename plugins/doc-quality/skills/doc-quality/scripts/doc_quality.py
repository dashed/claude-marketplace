#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["markdown-it-py==4.0.0", "github-slugger==0.0.3"]
# ///
"""Analyze engineering Markdown or compare revisions; never edit or autoaccept.

uv run --no-config --no-project doc_quality.py analyze design.md --kind design
Optional Jev uses an explicitly located general Jev helper. No key/helper skips.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from doc_links import check_links
from doc_metrics import analyze_document, compare_documents

RUBRICS = Path(__file__).resolve().parents[1] / "references/rubrics.json"
KINDS = ("design", "analysis", "plan", "adr")
OPTIONS = ("config", "provider", "endpoint", "model", "protocol", "api_key_env", "env_file")
MAX_FILE_BYTES = 1_000_000
MAX_REQUEST_BYTES = 100_000


def link_review(text: str, path: Path, args: argparse.Namespace) -> dict[str, Any]:
    if not args.check_links:
        return {"status": "not_run", "reason": "Enable --check-links for local files and anchors."}
    logical_path = args.document_path or path
    root = args.link_root or logical_path.absolute().parent
    return check_links(text, logical_path, root)


class ReviewError(Exception):
    """Input or optional semantic review could not be completed."""


def encode(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(encode(value)).hexdigest()


def read_text(path: Path) -> str:
    try:
        with path.open("rb") as stream:
            content = stream.read(MAX_FILE_BYTES + 1)
        if len(content) > MAX_FILE_BYTES:
            raise ReviewError("Input exceeds 1,000,000 bytes; select a bounded document excerpt.")
        return content.decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise ReviewError("Could not read the selected UTF-8 input.") from error


def load_context(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"audience": "software engineers", "evidence": [], "missing": []}
    try:
        context = json.loads(read_text(path))
        if not isinstance(context, dict):
            raise ValueError
        encode(context)
    except (ValueError, TypeError) as error:
        raise ReviewError("Context must be a finite JSON object.") from error
    return context


def quality_request(
    kind: str, section: dict[str, Any], context: dict[str, Any], rubric: dict[str, Any]
) -> dict[str, Any]:
    return {
        "state": {"kind": kind, "section": section, "context": context},
        "questions": {**rubric["common"], **rubric["profiles"][kind]},
    }


def comparison_request(
    kind: str, original: str, revised: str, context: dict[str, Any], rubric: dict[str, Any]
) -> dict[str, Any]:
    return {
        "state": {"kind": kind, "original": original, "revised": revised, "context": context},
        "questions": rubric["comparison"],
    }


def validate_evaluation(report: dict[str, Any], request: dict[str, Any]) -> None:
    """Reject stale or incompatible helper evidence before exposing it as evaluated."""
    wire = report.get("request")
    response = report.get("response")
    if not isinstance(wire, dict) or not isinstance(response, dict):
        raise ValueError("Missing provenance")
    questions = wire.get("questions")
    if not isinstance(questions, dict) or any(not isinstance(q, dict) for q in questions.values()):
        raise ValueError("Missing questions")
    normalized = {
        name: {**q, "type": "boolean" if q.get("type") == "noul" else q.get("type")}
        for name, q in questions.items()
    }
    if (
        wire.get("state") != request["state"]
        or normalized != request["questions"]
        or report.get("state_sha256") != digest(wire.get("state"))
        or report.get("questions_sha256") != digest(questions)
        or not isinstance(wire.get("model"), str)
        or not isinstance(response.get("model"), str)
    ):
        raise ValueError("Mismatched provenance")
    raw_answers = response.get("answers")
    answers = report.get("answers")
    if not isinstance(raw_answers, dict) or not isinstance(answers, dict):
        raise ValueError("Missing answers")
    if set(raw_answers) != set(questions) or set(answers) != set(questions):
        raise ValueError("Incomplete answers")

    def number(value: Any, maximum: float = 1) -> bool:
        return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= maximum

    for name, question in request["questions"].items():
        answer, raw = answers[name], raw_answers[name]
        if not isinstance(raw, dict) or raw.get("type") != questions[name]["type"]:
            raise ValueError("Invalid raw answer")
        expected = (
            {"type": "boolean", "probability": raw.get("noul")}
            if raw.get("type") == "noul"
            else raw
        )
        if (
            answer != expected
            or not isinstance(answer, dict)
            or answer.get("type") != question["type"]
        ):
            raise ValueError("Invalid normalized answer")
        kind = question["type"]
        if kind == "boolean":
            if not number(answer.get("probability")):
                raise ValueError("Invalid probability")
            continue
        choices = (
            set(question["criteria"])
            if kind == "choice"
            else {str(i) for i in range(len(question["criteria"]))}
        )
        probabilities = answer.get("probabilities")
        if (
            not isinstance(probabilities, dict)
            or set(probabilities) != choices
            or not all(number(p) for p in probabilities.values())
            or not math.isclose(sum(probabilities.values()), 1, abs_tol=0.025)
            or ("confidence" in answer and not number(answer["confidence"]))
        ):
            raise ValueError("Invalid distribution")
        if kind == "choice" and (
            not isinstance(answer.get("choice"), str) or answer["choice"] not in choices
        ):
            raise ValueError("Invalid choice")
        if kind == "score" and not number(answer.get("score"), len(choices) - 1):
            raise ValueError("Invalid score")


def call_jev(args: argparse.Namespace, request: dict[str, Any]) -> dict[str, Any]:
    if not args.dry_run and (args.jev_helper is None or not args.jev_helper.expanduser().is_file()):
        return {"status": "skipped", "reason": "jev_helper_unavailable"}
    if len(encode(request)) > MAX_REQUEST_BYTES:
        return {
            "status": "incomplete",
            "error": "Request exceeds 100,000 bytes; select a smaller scope. Nothing was truncated.",
        }
    if args.dry_run:
        return {
            "status": "preview",
            "request": request,
            "questions_sha256": digest(request["questions"]),
        }
    if args.jev_helper is None or not args.jev_helper.expanduser().is_file():
        return {"status": "skipped", "reason": "jev_helper_unavailable"}
    with tempfile.TemporaryDirectory(prefix="doc-quality-") as directory:
        path = Path(directory) / "request.json"
        path.write_bytes(encode(request))
        command = [sys.executable, str(args.jev_helper.expanduser()), "--request", str(path)]
        for option in OPTIONS:
            value = getattr(args, option)
            if value is not None:
                command.extend(["--" + option.replace("_", "-"), str(value)])
        try:
            result = subprocess.run(command, capture_output=True, timeout=45, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return {"status": "incomplete", "error": "The selected Jev helper could not complete."}
    try:
        report = json.loads(result.stdout)
        if not isinstance(report, dict):
            raise ValueError
        status = report.get("status")
        if status == "incomplete" and result.returncode == 2:
            return report
        if result.returncode != 0 or status not in ("evaluated", "skipped"):
            raise ValueError
        if status == "evaluated":
            validate_evaluation(report, request)
        return report
    except (ValueError, UnicodeError):
        # Never echo malformed child output or stderr, which may contain credentials.
        return {"status": "incomplete", "error": "The selected helper returned an invalid report."}


def review_requests(
    requests: dict[str, dict[str, Any]], args: argparse.Namespace
) -> dict[str, Any]:
    active = args.dry_run or (
        args.jev_helper is not None and args.jev_helper.expanduser().is_file()
    )
    oversized = [
        name for name, request in requests.items() if len(encode(request)) > MAX_REQUEST_BYTES
    ]
    if active and oversized:
        return {
            "status": "incomplete",
            "reports": {},
            "not_reviewed": list(requests),
            "oversized_requests": oversized,
            "error": "Request batch exceeds the per-request limit; no semantic calls were made.",
        }
    reports: dict[str, Any] = {}
    for name, request in requests.items():
        report = call_jev(args, request)
        reports[name] = report
        if report["status"] in ("skipped", "incomplete"):
            # Stop a missing-key or failed-service sequence; no retries or extra paid calls.
            break
    pending = [name for name in requests if name not in reports]
    states = {report["status"] for report in reports.values()}
    status = (
        "incomplete"
        if "incomplete" in states
        else "skipped"
        if "skipped" in states
        else "preview"
        if "preview" in states
        else "evaluated"
        if reports
        else "not_applicable"
    )
    return {"status": status, "reports": reports, "not_reviewed": pending}


def analyze(
    text: str, kind: str, context: dict[str, Any], rubric: dict[str, Any], args: argparse.Namespace
) -> dict[str, Any]:
    static = analyze_document(text)
    sections = static["sections"]
    selected = sections
    if args.section:
        by_id = {s["id"]: s for s in sections}
        if any(name not in by_id for name in args.section) or len(set(args.section)) != len(
            args.section
        ):
            raise ReviewError("Section IDs must be unique and present in the analysis.")
        selected = [by_id[name] for name in args.section]
    active = args.dry_run or (
        args.jev_helper is not None and args.jev_helper.expanduser().is_file()
    )
    if active and len(selected) > args.max_sections:
        semantic = {
            "status": "incomplete",
            "error": "Selected sections exceed the call budget; select --section IDs or set --max-sections.",
            "not_reviewed": [s["id"] for s in selected],
        }
    elif not active:
        semantic = {"status": "skipped", "reason": "jev_helper_unavailable"}
    else:
        requests = {
            s["id"]: quality_request(
                kind, {"text": s["text"], "heading_path": s["heading_path"]}, context, rubric
            )
            for s in selected
        }
        semantic = review_requests(requests, args)
    return {
        "analysis": static,
        "selected_sections": [s["id"] for s in selected],
        "not_selected": [s["id"] for s in sections if s not in selected],
        "semantic": semantic,
        "link_validation": {
            "status": "not_run",
            "reason": "Use the repository's link/anchor checker.",
        },
    }


def compare(
    original: str,
    revised: str,
    kind: str,
    context: dict[str, Any],
    rubric: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    requests = {}
    if not args.paired_only:
        for name, text in (("before", original), ("after", revised)):
            requests[name] = quality_request(
                kind, {"text": text, "heading_path": []}, context, rubric
            )
    requests["preservation"] = comparison_request(kind, original, revised, context, rubric)
    return {
        "before": analyze_document(original),
        "after": analyze_document(revised),
        "preservation": compare_documents(original, revised),
        "semantic": review_requests(requests, args),
        "acceptance": "requires_evidence_review",
        "link_validation": {
            "status": "not_run",
            "reason": "Use the repository's link/anchor checker.",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("analyze", "compare"):
        command = commands.add_parser(name)
        if name == "analyze":
            command.add_argument("path", type=Path)
            command.add_argument("--section", action="append")
            command.add_argument("--max-sections", type=int, default=6)
        else:
            command.add_argument("original", type=Path)
            command.add_argument("revised", type=Path)
            command.add_argument("--paired-only", action="store_true")
        command.add_argument("--check-links", action="store_true")
        command.add_argument("--link-root", type=Path)
        command.add_argument("--document-path", type=Path)
        command.add_argument("--kind", choices=KINDS, required=True)
        command.add_argument("--context", type=Path)
        command.add_argument("--jev-helper", type=Path)
        command.add_argument("--dry-run", action="store_true")
        for option in OPTIONS:
            command.add_argument("--" + option.replace("_", "-"))
    args = parser.parse_args(argv)
    metadata: dict[str, Any] = {"schema_version": 1, "advisory": True, "kind": args.kind}
    try:
        rubric = json.loads(read_text(RUBRICS))
        metadata.update(rubric_version=rubric["version"], rubric_sha256=digest(rubric))
        context = load_context(args.context)
        if not args.check_links and (args.link_root is not None or args.document_path is not None):
            raise ReviewError("--link-root and --document-path require --check-links.")
        if args.command == "analyze":
            if not 1 <= args.max_sections <= 100:
                raise ReviewError("--max-sections must be between 1 and 100.")
            text = read_text(args.path)
            links = link_review(text, args.path, args)
            report = analyze(text, args.kind, context, rubric, args)
            report["link_validation"] = links
        else:
            original, revised = read_text(args.original), read_text(args.revised)
            before_links = link_review(original, args.revised, args)
            after_links = link_review(revised, args.revised, args)
            report = compare(original, revised, args.kind, context, rubric, args)
            # Historical failures remain visible; only revised failures affect the exit code.
            links = after_links
            report["link_validation"] = {
                "status": after_links["status"],
                "before": before_links,
                "after": after_links,
            }
        status = report["semantic"]["status"]
        report = {**metadata, "status": status, **report}
        print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
        return 2 if status == "incomplete" else 1 if links["status"] == "failed" else 0
    except (ReviewError, OSError, ValueError, KeyError) as error:
        message = (
            str(error) if isinstance(error, ReviewError) else "Could not prepare document review."
        )
        print(json.dumps({**metadata, "status": "incomplete", "error": message}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
