#!/usr/bin/env python3
"""Run a small, labeled Jev complexity evaluation; retain failures and raw reports.

uv run --no-config --locked scripts/eval_python_complexity.py [--offline]
Live runs use the Jev helper's user configuration, or --config / --provider.
Exit 0: checks passed or semantic review skipped; 1: expectation failed;
2: tool/API failure. Fixture expectations are not production quality gates.
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
FIXTURES = ROOT / "tests/fixtures/python-complexity-jev.json"
REVIEW = ROOT / "plugins/python-complexity/skills/python-complexity/scripts/jev_review.py"


def command(args: list[str], cwd: Path, accepted: tuple[int, ...] = (0,)) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=120)
    if result.returncode not in accepted:
        raise RuntimeError(f"Tool failed with exit {result.returncode}: {args[0]}")
    return result.stdout


def behavior_check(cases: list[dict[str, Any]]) -> dict[str, Any]:
    # Expected labels come from the task contract, independently of the fixture implementations.
    inputs: list[tuple[Any, str]] = [(None, "missing"), (True, "odd"), (False, "accepted")]
    inputs += [(value, "not_integer") for value in ("", "7", 1.5, {}, [])]
    inputs += [(value, "negative") for value in range(-5, 0)]
    inputs += [(value, "accepted") for value in range(0, 101, 2)]
    inputs += [(value, "odd") for value in range(1, 101, 2)]
    inputs += [(value, "too_large") for value in range(101, 106)]
    failures = []
    checks_per_case = {}
    for case in cases:
        if not case["complete"]:
            continue
        namespace: dict[str, Any] = {}
        # Only the small, checked-in fixtures are executed, never user review state.
        exec(compile(case["source"], case["name"], "exec"), namespace)
        tests = case.get(
            "tests", [{"args": [value], "expected": expected} for value, expected in inputs]
        )
        checks_per_case[case["name"]] = len(tests)
        for test in tests:
            expected = test.get("expected")
            try:
                actual = namespace[case.get("entry", "classify")](*test["args"])
                matched = "raises" not in test and actual == expected
            except Exception as error:
                actual = {"raises": type(error).__name__}
                matched = test.get("raises") == type(error).__name__
            if not matched:
                failures.append(
                    {
                        "case": case["name"],
                        "input": test["args"],
                        "expected": test.get("raises", expected),
                        "actual": actual,
                    }
                )
    return {
        "status": "failed" if failures else "passed",
        "checks_per_case": checks_per_case,
        "total_checks": sum(checks_per_case.values()),
        "failures": failures,
    }


def census(cases: list[dict[str, Any]], output: Path) -> dict[str, Any]:
    files = []
    for case in cases:
        file = output / (case["name"] + ".py")
        file.write_text(case["source"], encoding="utf-8")
        files.append(str(file))
    ruff = ["uv", "run", "--no-config", "--locked", "ruff"]
    diagnostics = json.loads(
        command(
            [
                *ruff,
                "check",
                "--isolated",
                "--ignore-noqa",
                "--select",
                "C901",
                "--config",
                "lint.mccabe.max-complexity=0",
                "--no-cache",
                "--output-format",
                "json",
                *files,
            ],
            ROOT,
            (0, 1),
        )
    )
    cognitive_path = output / "cognitive.json"
    command(
        [
            "uvx",
            "complexipy@7.0.1",
            "--output-format",
            "json",
            "--output",
            str(cognitive_path),
            "--no-ignore",
            "-q",
            *files,
        ],
        output,
        (0, 1),
    )
    cognitive = json.loads(cognitive_path.read_text())
    measurements = {}
    for case in cases:
        name = case["name"]
        rows = [row for row in diagnostics if Path(row["filename"]).stem == name]
        scores = []
        for row in rows:
            match = re.search(r"\((\d+) > 0\)", row["message"])
            if row["code"] != "C901" or match is None:
                raise RuntimeError("Unexpected Ruff diagnostic in eval fixture")
            scores.append(int(match.group(1)))
        cog = [row["complexity"] for row in cognitive if Path(row["path"]).stem == name]
        defs = sum(
            isinstance(node, ast.FunctionDef) for node in ast.walk(ast.parse(case["source"]))
        )
        if len(scores) != defs or len(cog) != defs:
            raise RuntimeError("Static tools did not report every fixture function")
        measurements[name] = {
            "defs": defs,
            "max_cyclomatic": max(scores),
            "decisions": sum(scores) - defs,
            "cognitive_sum": sum(cog),
            "max_cognitive": max(cog),
        }
    return {
        "ruff_version": command([*ruff, "--version"], ROOT).strip(),
        "complexipy_version": "7.0.1",
        "cases": measurements,
    }


def semantic_checks(checks: list[dict[str, Any]], reports: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for check in checks:
        names = [check["higher"], check["lower"]] if "higher" in check else [check["case"]]
        if any(reports[name]["status"] != "evaluated" for name in names):
            results.append(
                {"expectation": check, "status": "skipped", "reason": "semantic_result_unavailable"}
            )
            continue
        signal = check["signal"]
        if any(signal not in reports[name]["answers"] for name in names):
            results.append(
                {"expectation": check, "status": "skipped", "reason": "signal_unavailable"}
            )
            continue
        if "higher" in check:
            high = reports[check["higher"]]["answers"][signal]["score"]
            low = reports[check["lower"]]["answers"][signal]["score"]
            observed = {"higher": high, "lower": low, "delta": round(high - low, 6)}
            passed = high - low >= check["min_delta"]
        elif "equals" in check:
            observed = reports[check["case"]]["answers"][signal]["choice"]
            passed = observed == check["equals"]
        else:
            observed = reports[check["case"]]["answers"][signal][check.get("field", "probability")]
            passed = (
                observed >= check["minimum"] if "minimum" in check else observed <= check["maximum"]
            )
        results.append(
            {"expectation": check, "status": "passed" if passed else "failed", "observed": observed}
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, help="New/empty directory; default: a temp directory"
    )
    parser.add_argument(
        "--offline", action="store_true", help="Run behavior and static checks only"
    )
    parser.add_argument("--config", type=Path, help="Jev helper provider config")
    parser.add_argument("--provider", choices=("vercel", "typesafe", "custom"))
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=FIXTURES,
        help="Trusted fixture JSON; executes its source for behavior checks",
    )
    args = parser.parse_args()
    output = (
        args.output_dir.resolve()
        if args.output_dir
        else Path(tempfile.mkdtemp(prefix="jev-complexity-eval-"))
    )
    if args.output_dir and output.exists() and any(output.iterdir()):
        parser.error("output directory must be empty so earlier evidence is preserved")
    output.mkdir(parents=True, exist_ok=True)
    fixtures = json.loads(args.fixtures.read_text())
    try:
        behavior = behavior_check(fixtures["cases"])
        static = census(fixtures["cases"], output)
        m = static["cases"]
        static_checks = (
            {
                "flattening_reduces_cognitive": m["flat"]["cognitive_sum"]
                < m["nested"]["cognitive_sum"],
                "ternary_lowers_cyclomatic_without_lowering_cognitive": m["ternary"][
                    "max_cyclomatic"
                ]
                < m["flat"]["max_cyclomatic"]
                and m["ternary"]["cognitive_sum"] > m["flat"]["cognitive_sum"],
                "forwarders_add_defs_without_removing_decisions": m["layered"]["defs"]
                > m["flat"]["defs"]
                and m["layered"]["decisions"] == m["flat"]["decisions"],
            }
            if {"flat", "nested", "layered", "ternary"} <= m.keys()
            else {}
        )
        reports = {}
        for case in fixtures["cases"]:
            name = case["name"]
            state = {
                "scope": case.get("scope", "classifier.py:classify and its call path"),
                "task": case.get("task", fixtures.get("task")),
                "constraints": case.get("constraints", fixtures.get("constraints", [])),
                "sources": [{"path": case.get("path", "classifier.py"), "content": case["source"]}],
                "measurements": {
                    "ruff_version": static["ruff_version"],
                    "complexipy_version": "7.0.1",
                    **m[name],
                },
                "missing_context": case.get("missing_context", [])
                if case["complete"]
                else ["The _dispatch implementation is omitted."],
            }
            state_file = output / (name + "-state.json")
            state_file.write_text(json.dumps(state, indent=2) + "\n")
            if args.offline:
                reports[name] = {"status": "skipped", "reason": "offline"}
                continue
            cmd = [sys.executable, str(REVIEW), "--state", str(state_file)]
            for option in ("config", "provider"):
                value = getattr(args, option)
                if value is not None:
                    cmd += ["--" + option, str(value)]
            raw = command(cmd, ROOT, (0, 2))
            (output / (name + "-review.json")).write_text(raw)
            reports[name] = json.loads(raw)
        checks = semantic_checks(fixtures["checks"], reports)
        counts = {
            status: sum(check["status"] == status for check in checks)
            for status in ("passed", "failed", "skipped")
        }
        incomplete = any(report["status"] == "incomplete" for report in reports.values())
        failed = (
            behavior["status"] == "failed"
            or not all(static_checks.values())
            or counts["failed"] > 0
        )
        result = {
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "fixture_version": fixtures["version"],
            "fixture_sha256": hashlib.sha256(args.fixtures.read_bytes()).hexdigest(),
            "status": "incomplete"
            if incomplete
            else "failed"
            if failed
            else "passed"
            if not counts["skipped"]
            else "static_only",
            "behavior": behavior,
            "static": static,
            "static_checks": static_checks,
            "semantic_counts": counts,
            "semantic_checks": checks,
            "review_statuses": {name: report["status"] for name, report in reports.items()},
            "observations": {
                name: {
                    field: report[field]
                    for field in (
                        "provider",
                        "protocol",
                        "endpoint",
                        "rubric_sha256",
                        "rubric_version",
                        "state_sha256",
                        "evaluated_at",
                        "response",
                        "error",
                        "reason",
                    )
                    if field in report
                }
                for name, report in reports.items()
            },
            "limitation": "Small synthetic regression suite; thresholds are fixture expectations, not production gates or calibration.",
        }
        (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"output_dir": str(output), **result}, indent=2))
        return 2 if incomplete else 1 if failed else 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"status": "incomplete", "error": str(error), "output_dir": str(output)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
