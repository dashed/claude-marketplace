#!/usr/bin/env python3
"""Evaluate frozen, single-section engineering-document profile judgments.

Run with uv run --no-config --locked python scripts/eval_doc_profiles.py [--offline].
Exit 0: all labels matched, or offline previews; 1: mismatched labels; 2: unavailable.
Inputs and raw reports are retained; unavailable judgments never count as passes.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.eval_doc_quality import (
    CLI,
    HELPER,
    MAX_CASES,
    MAX_FIXTURE_BYTES,
    ROOT,
    encode,
    report_provenance,
    sha256,
    write_new,
)

FIXTURES = ROOT / "tests/fixtures/doc-quality-profiles.json"
PROFILES = {
    "design": {"decision_clarity", "rationale", "tradeoffs"},
    "analysis": {"claim_evidence", "assumptions", "conclusion_support"},
    "plan": {"actionability", "dependencies", "acceptance_recovery"},
    "adr": {"decision_clarity", "rationale", "consequences"},
}
CHOICES = {"satisfied", "gap", "not_applicable", "needs_context"}
LIMITATION = (
    "Small independently labeled profile suite, not calibrated production accuracy. Each case "
    "uses one complete bounded section and supplied context; missing judgments never pass. "
    "Labels concern the named document purpose, not a universal completeness checklist. "
    "Passing these checks does not establish factual correctness or authorize a rewrite."
)
_SPEC = importlib.util.spec_from_file_location("doc_metrics", CLI.with_name("doc_metrics.py"))
assert _SPEC and _SPEC.loader
_METRICS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_METRICS)


def section_input(case: dict[str, Any]) -> dict[str, Any]:
    sections = _METRICS.analyze_document(case["text"])["sections"]
    if len(sections) != 1 or sections[0]["text"] != case["text"]:
        raise ValueError("Profile cases must contain exactly one complete Markdown section.")
    return sections[0]


def validate_fixtures(value: Any) -> dict[str, Any]:
    """Validate every input and label before creating artifacts or invoking the CLI."""
    if (
        not isinstance(value, dict)
        or set(value) != {"version", "cases"}
        or not isinstance(value["version"], str)
        or not value["version"].strip()
        or not isinstance(value["cases"], list)
        or not 1 <= len(value["cases"]) <= MAX_CASES
    ):
        raise ValueError("Invalid fixture envelope.")
    names: set[str] = set()
    for case in value["cases"]:
        if not isinstance(case, dict) or set(case) != {
            "name",
            "kind",
            "text",
            "context",
            "expectations",
        }:
            raise ValueError("Invalid profile case.")
        name = case["name"]
        if (
            not isinstance(name, str)
            or re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", name) is None
            or name in names
            or not isinstance(case["kind"], str)
            or case["kind"] not in PROFILES
            or not isinstance(case["text"], str)
            or not case["text"].strip()
        ):
            raise ValueError("Invalid case name, kind, or document.")
        names.add(name)
        section_input(case)
        context = case["context"]
        if (
            not isinstance(context, dict)
            or set(context) != {"audience", "scope", "evidence", "missing"}
            or any(not isinstance(context[key], str) for key in ("audience", "scope"))
            or any(
                not isinstance(context[key], list)
                or not all(isinstance(item, str) for item in context[key])
                for key in ("evidence", "missing")
            )
        ):
            raise ValueError("Invalid fixture context.")
        expectations = case["expectations"]
        if not isinstance(expectations, list) or not 1 <= len(expectations) <= 3:
            raise ValueError("Invalid expectation list.")
        signals: set[str] = set()
        for expected in expectations:
            if (
                not isinstance(expected, dict)
                or set(expected) != {"signal", "equals"}
                or not isinstance(expected["signal"], str)
                or expected["signal"] not in PROFILES[case["kind"]]
                or expected["signal"] in signals
                or not isinstance(expected["equals"], str)
                or expected["equals"] not in CHOICES
            ):
                raise ValueError("Invalid or duplicate profile expectation.")
            signals.add(expected["signal"])
    return value


def section_report(report: dict[str, Any]) -> dict[str, Any]:
    semantic = report.get("semantic")
    reports = semantic.get("reports") if isinstance(semantic, dict) else None
    if not isinstance(reports, dict) or len(reports) != 1:
        return {}
    selected = report.get("selected_sections")
    if selected != list(reports) or report.get("not_selected") != []:
        return {}
    result = next(iter(reports.values()))
    return cast(dict[str, Any], result) if isinstance(result, dict) else {}


def check_expectations(case: dict[str, Any], report: dict[str, Any]) -> list[dict[str, Any]]:
    section = section_report(report)
    semantic = report.get("semantic")
    evaluated = (
        report.get("status") == "evaluated"
        and isinstance(semantic, dict)
        and semantic.get("status") == "evaluated"
        and section.get("status") == "evaluated"
    )
    answers = section.get("answers")
    checks = []
    for expected in case["expectations"]:
        row = {"case": case["name"], "expectation": expected}
        answer = answers.get(expected["signal"]) if isinstance(answers, dict) else None
        if not evaluated:
            checks.append({**row, "status": "skipped", "reason": "semantic_result_unavailable"})
        elif not isinstance(answer, dict):
            checks.append({**row, "status": "skipped", "reason": "signal_unavailable"})
        elif not isinstance(answer.get("choice"), str) or answer["choice"] not in CHOICES:
            checks.append({**row, "status": "skipped", "reason": "invalid_signal"})
        else:
            checks.append(
                {
                    **row,
                    "status": "passed" if answer["choice"] == expected["equals"] else "failed",
                    "observed": answer["choice"],
                }
            )
    return checks


def unavailable(status: str, reason: str) -> dict[str, Any]:
    return {"status": status, "semantic": {"status": status, "reason": reason}}


def review_case(directory: Path, case: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    section = section_input(case)
    command = [
        sys.executable,
        str(CLI),
        "analyze",
        str(directory / "document.md"),
        "--kind",
        case["kind"],
        "--context",
        str(directory / "context.json"),
        "--max-sections",
        "1",
    ]
    if args.offline:
        command.append("--dry-run")
    else:
        command += ["--jev-helper", str(args.jev_helper.expanduser().resolve())]
        for option in ("config", "provider", "env_file"):
            selected = getattr(args, option)
            if selected is not None:
                if isinstance(selected, Path):
                    selected = selected.expanduser().resolve()
                command += ["--" + option.replace("_", "-"), str(selected)]
    try:
        process = subprocess.run(command, capture_output=True, timeout=60, check=False, cwd=ROOT)
        if process.returncode not in (0, 2):
            raise ValueError
        report = json.loads(process.stdout)
        if not isinstance(report, dict) or report.get("status") not in {
            "evaluated",
            "preview",
            "skipped",
            "incomplete",
        }:
            raise ValueError
        encode(report)
        semantic = report.get("semantic")
        if not isinstance(semantic, dict) or semantic.get("status") != report["status"]:
            raise ValueError
        if report["status"] != "incomplete" and process.returncode != 0:
            raise ValueError
        if report["status"] in {"evaluated", "preview"}:
            result = section_report(report)
            request = result.get("request")
            expected_state = {
                "kind": case["kind"],
                "section": {"text": section["text"], "heading_path": section["heading_path"]},
                "context": case["context"],
            }
            if (
                result.get("status") != report["status"]
                or report["selected_sections"] != [section["id"]]
                or not isinstance(request, dict)
                or request.get("state") != expected_state
            ):
                raise ValueError
        return report
    except (OSError, subprocess.TimeoutExpired, ValueError, UnicodeError):
        return unavailable("incomplete", "profile_process_failed_or_returned_invalid_report")


def run_evaluation(
    fixtures: dict[str, Any], raw: bytes, output: Path, args: argparse.Namespace
) -> dict[str, Any]:
    write_new(output / "fixtures.json", raw)
    checks: list[dict[str, Any]] = []
    cases: dict[str, Any] = {}
    halted_by: str | None = None
    calls = 0
    for case in fixtures["cases"]:
        name = case["name"]
        directory = output / name
        directory.mkdir()
        inputs = {key: case[key] for key in ("kind", "text", "context")}
        hashes = {
            "document.md": write_new(directory / "document.md", case["text"].encode()),
            "context.json": write_new(directory / "context.json", encode(case["context"])),
            "input.json": write_new(directory / "input.json", encode(inputs)),
        }
        if halted_by is None:
            report = review_case(directory, case, args)
            calls += 1
        else:
            report = unavailable("skipped", "prior_case_unavailable:" + halted_by)
        hashes["report.json"] = write_new(directory / "report.json", encode(report))
        case_checks = check_expectations(case, report)
        checks.extend(case_checks)
        section = section_report(report)
        cases[name] = {
            "kind": case["kind"],
            "status": report["status"],
            "directory": name,
            "sha256": hashes,
            "rubric_version": report.get("rubric_version"),
            "rubric_sha256": report.get("rubric_sha256"),
            "request_sha256": sha256(encode(section["request"])) if "request" in section else None,
            "provenance": report_provenance(section),
        }
        valid_preview = args.offline and report["status"] == "preview"
        if not valid_preview and (
            report["status"] != "evaluated" or any(c["status"] == "skipped" for c in case_checks)
        ):
            halted_by = halted_by or name
    counts = {
        status: sum(c["status"] == status for c in checks)
        for status in ("passed", "failed", "skipped")
    }
    all_preview = args.offline and all(c["status"] == "preview" for c in cases.values())
    incomplete = any(c["status"] == "incomplete" for c in cases.values()) or (
        counts["skipped"] > 0 and not all_preview
    )
    status = (
        "incomplete"
        if incomplete
        else "failed"
        if counts["failed"]
        else "offline_preview"
        if all_preview
        else "passed"
    )
    return {
        "status": status,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "fixture_version": fixtures["version"],
        "fixture_sha256": sha256(raw),
        "case_count": len(cases),
        "expectation_count": len(checks),
        "semantic_counts": counts,
        "semantic_checks": checks,
        "cases": cases,
        "profile": {
            "mode": "offline_preview" if args.offline else "live",
            "evaluation": "single_section_document_profile",
            "kinds": dict(Counter(case["kind"] for case in fixtures["cases"])),
            "analysis_processes": calls,
            "maximum_semantic_calls": 0 if args.offline else calls,
            "sequential": True,
            "retries": 0,
            "halted_by": halted_by,
        },
        "limitation": LIMITATION,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=FIXTURES)
    parser.add_argument("--output-dir", type=Path, help="New or empty evidence directory")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--jev-helper", type=Path, default=HELPER)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--provider", choices=("vercel", "typesafe", "custom"))
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args(argv)
    output: Path | None = None
    try:
        with args.fixtures.expanduser().open("rb") as stream:
            raw = stream.read(MAX_FIXTURE_BYTES + 1)
        if len(raw) > MAX_FIXTURE_BYTES:
            raise ValueError("Fixture exceeds the byte budget.")
        fixtures = validate_fixtures(json.loads(raw))
        output = (
            args.output_dir.expanduser().absolute()
            if args.output_dir
            else Path(tempfile.mkdtemp(prefix="doc-profile-eval-"))
        )
        if output.is_symlink() or (
            output.exists() and (not output.is_dir() or any(output.iterdir()))
        ):
            raise ValueError("Output directory must be new or empty; preserve prior evidence.")
        output.mkdir(parents=True, exist_ok=True)
        summary = run_evaluation(fixtures, raw, output, args)
        write_new(output / "summary.json", encode(summary))
        print(
            json.dumps(
                {
                    "output_dir": str(output),
                    "status": summary["status"],
                    "semantic_counts": summary["semantic_counts"],
                }
            )
        )
        return 2 if summary["status"] == "incomplete" else 1 if summary["status"] == "failed" else 0
    except (OSError, ValueError, TypeError, OverflowError):
        print(
            json.dumps(
                {
                    "status": "incomplete",
                    "output_dir": str(output) if output else None,
                    "error": "Invalid fixtures, output directory, or profile evaluation.",
                }
            )
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
