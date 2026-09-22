#!/usr/bin/env python3
"""Evaluate frozen Markdown revision cases without changing their inputs.

Run with uv run --no-config --locked scripts/eval_doc_quality.py [--offline].
Exit 0: semantic expectations passed, or all skipped in an offline preview;
1: expectation failure; 2: incomplete. No retries or automatic acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/doc-quality.json"
CLI = ROOT / "plugins/doc-quality/skills/doc-quality/scripts/doc_quality.py"
HELPER = ROOT / "plugins/jev/skills/jev/scripts/jev.py"
KINDS = {"design", "analysis", "plan", "adr"}
PROBABILITY_SIGNALS = {
    "requirements_preserved",
    "behavior_preserved",
    "uncertainty_preserved",
    "evidence_supported",
}
PREFERENCES = {"original", "revised", "equivalent", "needs_context"}
MAX_CASES = 100
MAX_FIXTURE_BYTES = 2_000_000
LIMITATION = (
    "Small synthetic regression suite with frozen independent labels. Meaning and evidence "
    "preservation take priority over polish. Probabilities are advisory model judgments, not "
    "calibrated guarantees. Static inventory changes require review and do not establish semantic "
    "failure or safety. Offline previews and missing judgments never count as semantic passes."
)


def encode(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def probability(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and 0 <= value <= 1
    )


def validate_fixtures(value: Any) -> dict[str, Any]:
    """Reject ambiguous labels and unsafe case paths before creating artifacts or calling Jev."""
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
            "original",
            "revised",
            "context",
            "expectations",
        }:
            raise ValueError("Invalid fixture case.")
        name = case["name"]
        if (
            not isinstance(name, str)
            or re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", name) is None
            or name in names
            or not isinstance(case["kind"], str)
            or case["kind"] not in KINDS
            or any(
                not isinstance(case[key], str) or not case[key].strip()
                for key in ("original", "revised")
            )
        ):
            raise ValueError("Invalid case name, kind, or document.")
        names.add(name)
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
        if not isinstance(expectations, list) or not 1 <= len(expectations) <= 5:
            raise ValueError("Invalid expectation list.")
        signals: set[str] = set()
        for expectation in expectations:
            if not isinstance(expectation, dict):
                raise ValueError("Invalid expectation.")
            signal = expectation.get("signal")
            if not isinstance(signal, str) or signal in signals:
                raise ValueError("Invalid or duplicate expectation signal.")
            signals.add(signal)
            if signal == "preferred":
                if (
                    set(expectation) != {"signal", "equals"}
                    or not isinstance(expectation["equals"], str)
                    or expectation["equals"] not in PREFERENCES
                ):
                    raise ValueError("Invalid preference label.")
            elif signal in PROBABILITY_SIGNALS:
                bounds = set(expectation) - {"signal"}
                if bounds not in ({"minimum"}, {"maximum"}) or not probability(
                    expectation[next(iter(bounds))]
                ):
                    raise ValueError("Invalid probability label.")
            else:
                raise ValueError("Unknown expectation signal.")
    return value


def preservation_report(report: dict[str, Any]) -> dict[str, Any]:
    semantic = report.get("semantic")
    reports = semantic.get("reports") if isinstance(semantic, dict) else None
    preservation = reports.get("preservation") if isinstance(reports, dict) else None
    return preservation if isinstance(preservation, dict) else {}


def report_provenance(report: dict[str, Any]) -> dict[str, Any]:
    """Extract the general helper's flat provenance without discarding raw reports."""
    result = {
        key: report[key]
        for key in (
            "provider",
            "protocol",
            "endpoint",
            "state_sha256",
            "questions_sha256",
            "evaluated_at",
        )
        if key in report
    }
    for field, label in (("request", "requested_model"), ("response", "response_model")):
        value = report.get(field)
        if isinstance(value, dict) and isinstance(value.get("model"), str):
            result[label] = value["model"]
    return result


def check_expectations(case: dict[str, Any], report: dict[str, Any]) -> list[dict[str, Any]]:
    preservation = preservation_report(report)
    semantic = report.get("semantic", {})
    evaluated = (
        report.get("status") == "evaluated"
        and isinstance(semantic, dict)
        and semantic.get("status") == "evaluated"
        and preservation.get("status") == "evaluated"
    )
    answers = preservation.get("answers")
    results = []
    for expectation in case["expectations"]:
        row = {"case": case["name"], "expectation": expectation}
        answer = answers.get(expectation["signal"]) if isinstance(answers, dict) else None
        if not evaluated:
            results.append({**row, "status": "skipped", "reason": "semantic_result_unavailable"})
            continue
        if not isinstance(answer, dict):
            results.append({**row, "status": "skipped", "reason": "signal_unavailable"})
            continue
        if "equals" in expectation:
            observed = answer.get("choice")
            valid = isinstance(observed, str) and observed in PREFERENCES
            passed = observed == expectation["equals"]
        else:
            observed = answer.get("probability")
            valid = probability(observed)
            passed = valid and (
                observed >= expectation["minimum"]
                if "minimum" in expectation
                else observed <= expectation["maximum"]
            )
        if not valid:
            results.append({**row, "status": "skipped", "reason": "invalid_signal"})
        else:
            results.append(
                {**row, "status": "passed" if passed else "failed", "observed": observed}
            )
    return results


def unavailable(status: str, reason: str) -> dict[str, Any]:
    return {
        "status": status,
        "semantic": {
            "status": status,
            "reports": {"preservation": {"status": status, "reason": reason}},
        },
    }


def review_case(directory: Path, case: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    command = [
        sys.executable,
        str(CLI),
        "compare",
        str(directory / "original.md"),
        str(directory / "revised.md"),
        "--kind",
        case["kind"],
        "--context",
        str(directory / "context.json"),
        "--paired-only",
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
        result = subprocess.run(command, capture_output=True, timeout=60, check=False, cwd=ROOT)
        if result.returncode not in (0, 2):
            raise ValueError
        report = json.loads(result.stdout)
        if not isinstance(report, dict) or report.get("status") not in {
            "evaluated",
            "preview",
            "skipped",
            "incomplete",
        }:
            raise ValueError
        encode(report)
        if report["status"] != "incomplete":
            if (
                result.returncode != 0
                or not isinstance(report.get("semantic"), dict)
                or report["semantic"].get("status") != report["status"]
                or preservation_report(report).get("status") != report["status"]
            ):
                raise ValueError
        return report
    except (OSError, subprocess.TimeoutExpired, ValueError, UnicodeError):
        # Do not echo arbitrary child stderr/stdout, which may contain credentials.
        return unavailable("incomplete", "comparison_process_failed_or_returned_invalid_report")


def write_new(path: Path, content: bytes) -> str:
    with path.open("xb") as stream:
        stream.write(content)
    return sha256(content)


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
        inputs = {key: case[key] for key in ("kind", "original", "revised", "context")}
        hashes = {
            "original.md": write_new(directory / "original.md", case["original"].encode()),
            "revised.md": write_new(directory / "revised.md", case["revised"].encode()),
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
        preservation = preservation_report(report)
        cases[name] = {
            "kind": case["kind"],
            "status": report["status"],
            "directory": name,
            "sha256": hashes,
            "rubric_version": report.get("rubric_version"),
            "rubric_sha256": report.get("rubric_sha256"),
            "request_sha256": sha256(encode(preservation["request"]))
            if "request" in preservation
            else None,
            "provenance": report_provenance(preservation),
            "static_preservation": report.get("preservation", {"status": "not_run"}),
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
        else ("offline_preview" if all_preview else "passed")
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
            "comparison": "paired_preservation_only",
            "kinds": dict(Counter(case["kind"] for case in fixtures["cases"])),
            "comparison_processes": calls,
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
            else Path(tempfile.mkdtemp(prefix="doc-quality-eval-"))
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
                    "error": "Invalid fixtures, unavailable output directory, or incomplete evaluation.",
                }
            )
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
