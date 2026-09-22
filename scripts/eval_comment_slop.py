#!/usr/bin/env python3
"""Evaluate frozen comment-review cases without editing or executing their source.

Run with uv run --no-config --locked scripts/eval_comment_slop.py [--offline].
Exit 0: checks passed or semantics skipped; 1: expectation failed; 2: incomplete.
Synthetic thresholds are regression expectations, never automatic deletion gates.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/comment-slop-jev.json"
ADAPTER = ROOT / "plugins/comment-slop/skills/comment-slop/scripts/jev_comments.py"
HELPER = ROOT / "plugins/jev/skills/jev/scripts/jev.py"


def executable_tree(source: str) -> str:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            node.body.pop(0)
    return ast.dump(tree, include_attributes=False)


def proposal_structure(state: dict[str, Any]) -> dict[str, Any]:
    if "proposal" not in state:
        return {"status": "not_applicable"}
    if state["language"].lower() != "python":
        return {"status": "not_run", "reason": "no_parser_for_language"}
    candidate = state["candidate"]
    source = next(s["content"] for s in state["sources"] if s["path"] == candidate["path"])
    lines = source.splitlines(keepends=True)
    first, last = candidate["start_line"] - 1, candidate["end_line"]
    window = "".join(lines[first:last])
    if window.count(candidate["text"]) != 1:
        return {"status": "failed", "reason": "candidate_not_uniquely_anchored"}
    edited = (
        "".join(lines[:first])
        + window.replace(candidate["text"], state["proposal"]["replacement"], 1)
        + "".join(lines[last:])
    )
    try:
        # Compile checks contextual syntax such as a return outside a function; never execute.
        compile(edited, "proposal", "exec")
        unchanged = executable_tree(source) == executable_tree(edited)
    except SyntaxError:
        return {"status": "failed", "reason": "invalid_python_syntax"}
    return {
        "status": "passed" if unchanged else "failed",
        "executable_ast_unchanged": unchanged,
        "limitation": "Leading docstrings are excluded; docs, tooling, and runtime consumers need separate verification.",
    }


def check_expectations(case: dict[str, Any], report: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for expectation in case["expectations"]:
        row = {"case": case["name"], "expectation": expectation}
        if report["status"] != "evaluated":
            results.append({**row, "status": "skipped", "reason": "semantic_result_unavailable"})
            continue
        answer = report.get("answers", {}).get(expectation["signal"])
        if answer is None:
            results.append({**row, "status": "skipped", "reason": "signal_unavailable"})
            continue
        if "equals" in expectation:
            observed = answer["choice"]
            passed = observed == expectation["equals"]
        else:
            observed = answer["probability"]
            passed = (
                observed >= expectation["minimum"]
                if "minimum" in expectation
                else observed <= expectation["maximum"]
            )
        results.append({**row, "status": "passed" if passed else "failed", "observed": observed})
    return results


def review_case(state_file: Path, args: argparse.Namespace) -> dict[str, Any]:
    command = [sys.executable, str(ADAPTER), "--state", str(state_file)]
    if args.offline:
        command.append("--dry-run")
    else:
        command += ["--jev-helper", str(args.jev_helper)]
        for option in ("config", "provider", "env_file"):
            value = getattr(args, option)
            if value is not None:
                command += ["--" + option.replace("_", "-"), str(value)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=110, cwd=ROOT)
    if result.returncode not in (0, 2):
        return {"status": "incomplete", "error": "Comment adapter failed."}
    try:
        report = json.loads(result.stdout)
        if not isinstance(report, dict) or report.get("status") not in (
            "preview",
            "evaluated",
            "skipped",
            "incomplete",
        ):
            raise ValueError
    except ValueError:
        return {"status": "incomplete", "error": "Comment adapter returned invalid JSON."}
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=FIXTURES)
    parser.add_argument("--output-dir", type=Path, help="New or empty evidence directory")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--jev-helper", type=Path, default=HELPER)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--provider", choices=("vercel", "typesafe", "custom"))
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args()
    output = args.output_dir or Path(tempfile.mkdtemp(prefix="jev-comment-eval-"))
    if args.output_dir and output.exists() and any(output.iterdir()):
        parser.error("output directory must be empty; preserve prior evidence")
    output.mkdir(parents=True, exist_ok=True)
    try:
        fixtures = json.loads(args.fixtures.read_text())
        reports, structure, checks = {}, {}, []
        for case in fixtures["cases"]:
            name = case["name"]
            if not re.fullmatch(r"[a-z0-9_]+", name) or name in reports:
                raise ValueError("Invalid or duplicate case name.")
            state_file = output / (name + "-state.json")
            state_file.write_text(json.dumps(case["state"], indent=2) + "\n")
            report = review_case(state_file, args)
            reports[name] = report
            (output / (name + "-review.json")).write_text(json.dumps(report, indent=2) + "\n")
            structure[name] = (
                proposal_structure(case["state"])
                if report["status"] != "incomplete"
                else {"status": "not_run", "reason": "invalid_or_unavailable_review"}
            )
            checks.extend(check_expectations(case, report))
        counts = {
            status: sum(c["status"] == status for c in checks)
            for status in ("passed", "failed", "skipped")
        }
        incomplete = any(r["status"] == "incomplete" for r in reports.values())
        failed = counts["failed"] > 0 or any(s["status"] == "failed" for s in structure.values())
        status = (
            "incomplete"
            if incomplete
            else "failed"
            if failed
            else ("static_only" if counts["skipped"] else "passed")
        )
        summary = {
            "status": status,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "fixture_version": fixtures["version"],
            "fixture_sha256": hashlib.sha256(args.fixtures.read_bytes()).hexdigest(),
            "semantic_counts": counts,
            "semantic_checks": checks,
            "proposal_structure": structure,
            "reports": reports,
            "limitation": "Small synthetic suite with independent labels; neither AST equality nor Jev proves consumer preservation or general decision quality.",
        }
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps({"output_dir": str(output), "status": status, "semantic_counts": counts}))
        return 2 if incomplete else 1 if failed else 0
    except (OSError, ValueError, KeyError, StopIteration, subprocess.TimeoutExpired):
        print(
            json.dumps(
                {
                    "status": "incomplete",
                    "error": "Evaluation could not complete.",
                    "output_dir": str(output),
                }
            )
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
