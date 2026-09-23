#!/usr/bin/env python3
"""Evaluate Jev's paired change judgments on a frozen before/after suite, with controls.

uv run --no-config --locked scripts/eval_python_complexity_changes.py [--offline]

For each pair, runs the pair's behavior tests on both versions and the static census. Unless
--offline, it then sends five paired requests through the python-complexity Jev helper: main, a
repeat of main, an AST-identical reformat, before and after swapped, and one without the task
and constraints. Frozen expectations are scored on the main answers. The repeat, reformat and
swap controls are held to the fixture's declared tolerances; the no-context variant is reported
only. Static separability reports, per signal, which census delta already splits the labels.

Exit 0: every expectation and control passed, or semantic review was skipped. Exit 1: an
expectation, a control, or a behavior test failed. Exit 2: tool or API failure.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/python-complexity-jev-changes.json"
SKILL = ROOT / "plugins/python-complexity/skills/python-complexity"
REVIEW = SKILL / "scripts/jev_review.py"
RUBRIC = SKILL / "references/jev-change-rubric.json"
_spec = importlib.util.spec_from_file_location(
    "eval_complexity_base", ROOT / "scripts/eval_python_complexity.py"
)
assert _spec and _spec.loader
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

VARIANTS = ("main", "repeat", "reformat", "swap", "no_context")
STATIC_METRICS = ("defs", "decisions", "cognitive_sum", "max_cognitive", "max_cyclomatic")
CONTROL_TOLERANCES = ("repeat_max_delta", "reformat_max_delta", "swap_max_delta")
NAME = re.compile(r"[a-z][a-z0-9_]{0,60}")


def validate_fixtures(fixtures: dict[str, Any], questions: dict[str, Any]) -> None:
    """Reject a malformed suite before anything runs, so a typo never reads as a result."""
    pairs = fixtures.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("fixtures need a nonempty pairs list")
    names = [pair.get("name") for pair in pairs]
    if len(set(names)) != len(names) or not all(
        isinstance(n, str) and NAME.fullmatch(n) for n in names
    ):
        raise ValueError("pair names must be unique lowercase identifiers")
    for pair in pairs:
        for key in ("task", "entry"):
            if not isinstance(pair.get(key), str) or not pair[key].strip():
                raise ValueError(f"{pair['name']}: {key} must be a nonempty string")
        if not isinstance(pair.get("constraints"), list):
            raise ValueError(f"{pair['name']}: constraints must be a list")
        for side in ("before", "after"):
            version = pair.get(side)
            if not isinstance(version, dict) or not all(
                isinstance(version.get(k), str) and version[k].strip() for k in ("path", "source")
            ):
                raise ValueError(f"{pair['name']}: {side} needs path and source strings")
        if not isinstance(pair.get("complete", True), bool):
            raise ValueError(f"{pair['name']}: complete must be true or false")
        # A pair that omits code on purpose (complete: false) cannot run behavior tests.
        if pair.get("complete", True) and (
            not isinstance(pair.get("tests"), list) or not pair["tests"]
        ):
            raise ValueError(f"{pair['name']}: tests must be a nonempty list")
    controls = fixtures.get("controls", {})
    if set(controls) != set(CONTROL_TOLERANCES) or not all(
        isinstance(v, (int, float)) and 0 <= v <= 1 for v in controls.values()
    ):
        raise ValueError(f"controls must set exactly {CONTROL_TOLERANCES} within 0..1")
    for check in fixtures.get("checks", []):
        bounds = {"minimum", "maximum", "equals"} & set(check)
        if (
            check.get("pair") not in names
            or check.get("signal") not in questions
            or len(bounds) != 1
        ):
            raise ValueError(f"malformed check: {check}")
        question = questions[check["signal"]]
        if ("equals" in check) != (question["type"] == "choice"):
            raise ValueError(f"check bound does not fit the question type: {check}")
        if "equals" in check and check["equals"] not in question["criteria"]:
            raise ValueError(f"unknown choice in check: {check}")


def distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    """Largest probability movement between two normalized answers to the same question."""
    if "probability" in a:
        return abs(a["probability"] - b["probability"])
    return max(abs(a["probabilities"][k] - b["probabilities"][k]) for k in a["probabilities"])


def mirrored(answers: dict[str, Any]) -> dict[str, Any]:
    """What the swapped request should answer, given the main answers, if Jev is consistent."""
    result = {}
    for name, answer in answers.items():
        if name.startswith("introduced_"):
            result["removed_" + name.removeprefix("introduced_")] = answer
        elif name.startswith("removed_"):
            result["introduced_" + name.removeprefix("removed_")] = answer
        else:
            flip = {"before": "after", "after": "before"}
            probabilities = {flip.get(k, k): v for k, v in answer["probabilities"].items()}
            result[name] = {**answer, "probabilities": probabilities}
    return result


def largest_move(a: dict[str, Any], b: dict[str, Any]) -> tuple[float, str]:
    moves = [(round(distance(a[name], b[name]), 6), name) for name in sorted(a)]
    return max(moves)


def score(check: dict[str, Any], answers: dict[str, Any]) -> tuple[bool, Any]:
    answer = answers[check["signal"]]
    if "equals" in check:
        return answer["choice"] == check["equals"], answer["choice"]
    observed = answer["probability"]
    passed = observed >= check["minimum"] if "minimum" in check else observed <= check["maximum"]
    return passed, observed


def static_separability(
    checks: list[dict[str, Any]], deltas: dict[str, dict[str, int]]
) -> dict[str, dict[str, Any]]:
    """Per signal: census deltas that split its labeled pairs with one threshold on this suite."""
    labels: dict[str, list[tuple[str, bool]]] = {}
    for check in checks:
        positive = check["equals"] == "after" if "equals" in check else "minimum" in check
        labels.setdefault(check["signal"], []).append((check["pair"], positive))
    result = {}
    for signal, pairs in sorted(labels.items()):
        pos = [deltas[p] for p, positive in pairs if positive]
        neg = [deltas[p] for p, positive in pairs if not positive]
        separated = []
        if pos and neg:
            for metric in STATIC_METRICS:
                high, low = [d[metric] for d in pos], [d[metric] for d in neg]
                if min(high) > max(low) or max(high) < min(low):
                    separated.append(metric)
        result[signal] = {"positives": len(pos), "negatives": len(neg), "separated_by": separated}
    return result


def reformat(source: str, workdir: Path, name: str) -> str:
    """ruff-format at a narrow width; the result must parse to the identical AST."""
    path = workdir / f"{name}.py"
    path.write_text(source, encoding="utf-8")
    ruff = ["uv", "run", "--no-config", "--locked", "ruff", "format", "--isolated"]
    base.command([*ruff, "--line-length", "40", str(path)], ROOT)
    formatted = path.read_text(encoding="utf-8")
    if ast.dump(ast.parse(formatted)) != ast.dump(ast.parse(source)):
        raise RuntimeError(f"reformatting {name} changed its AST")
    return formatted


def state(pair: dict[str, Any], side: str, source: str, context: bool = True) -> dict[str, Any]:
    result: dict[str, Any] = {
        "scope": f"{pair[side]['path']}:{pair['entry']} and the code it calls",
        "sources": [{"path": pair[side]["path"], "content": source}],
    }
    if context:
        result["task"] = pair["task"]
        if pair["constraints"]:
            result["constraints"] = pair["constraints"]
    return result


def review(
    pair: dict[str, Any],
    variant: str,
    before: dict[str, Any],
    after: dict[str, Any],
    args: Any,
    output: Path,
) -> dict[str, Any]:
    stem = output / f"{pair['name']}-{variant}"
    before_file, after_file = Path(f"{stem}-before.json"), Path(f"{stem}-after.json")
    before_file.write_text(json.dumps(before, indent=2) + "\n")
    after_file.write_text(json.dumps(after, indent=2) + "\n")
    cmd = [sys.executable, str(REVIEW), "--before", str(before_file), "--after", str(after_file)]
    for option in ("config", "provider"):
        value = getattr(args, option)
        if value is not None:
            cmd += ["--" + option, str(value)]
    raw = base.command(cmd, ROOT, (0, 2))
    Path(f"{stem}-review.json").write_text(raw)
    return json.loads(raw)


def controls(reports: dict[str, dict[str, Any]], tolerances: dict[str, float]) -> dict[str, Any]:
    """Compare each variant with main; unavailable variants are reported, never passed."""
    main = reports["main"]
    result: dict[str, Any] = {}
    for variant, expected in (
        ("repeat", main.get("answers")),
        ("reformat", main.get("answers")),
        ("swap", mirrored(main["answers"]) if main["status"] == "evaluated" else None),
        ("no_context", main.get("answers")),
    ):
        report = reports[variant]
        if main["status"] != "evaluated" or report["status"] != "evaluated" or expected is None:
            result[variant] = {"status": "unavailable"}
            continue
        move, signal = largest_move(expected, report["answers"])
        tolerance = tolerances.get(f"{variant}_max_delta")
        status = "reported" if tolerance is None else "passed" if move <= tolerance else "failed"
        result[variant] = {"status": status, "largest_move": move, "signal": signal}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, help="New or empty directory; default: a temp directory"
    )
    parser.add_argument("--offline", action="store_true", help="Behavior and static checks only")
    parser.add_argument("--config", type=Path, help="Jev helper provider config")
    parser.add_argument("--provider", choices=("vercel", "typesafe", "custom"))
    parser.add_argument(
        "--fixtures", type=Path, default=FIXTURES, help="Trusted before/after suite"
    )
    args = parser.parse_args()
    output = (
        args.output_dir.resolve()
        if args.output_dir
        else Path(tempfile.mkdtemp(prefix="jev-changes-"))
    )
    if args.output_dir and output.exists() and any(output.iterdir()):
        parser.error("output directory must be empty so earlier evidence is preserved")
    output.mkdir(parents=True, exist_ok=True)
    try:
        fixtures = json.loads(args.fixtures.read_text())
        rubric = json.loads(RUBRIC.read_text())
        validate_fixtures(fixtures, rubric["questions"])
        pairs = fixtures["pairs"]
        cases = [
            {
                "name": f"{pair['name']}__{side}",
                "complete": pair.get("complete", True),
                "source": pair[side]["source"],
                "entry": pair["entry"],
                "tests": pair.get("tests", []),
            }
            for pair in pairs
            for side in ("before", "after")
        ]
        behavior = base.behavior_check(cases)
        static = base.census(cases, output)
        m = static["cases"]
        deltas = {
            p["name"]: {
                k: m[f"{p['name']}__after"][k] - m[f"{p['name']}__before"][k]
                for k in STATIC_METRICS
            }
            for p in pairs
        }
        reports: dict[str, dict[str, dict[str, Any]]] = {}
        for pair in pairs:
            if args.offline:
                reports[pair["name"]] = {
                    v: {"status": "skipped", "reason": "offline"} for v in VARIANTS
                }
                continue
            before, after = pair["before"]["source"], pair["after"]["source"]
            ref_before = reformat(before, output, f"{pair['name']}__before_reformatted")
            ref_after = reformat(after, output, f"{pair['name']}__after_reformatted")
            variants = {
                "main": (state(pair, "before", before), state(pair, "after", after)),
                "repeat": (state(pair, "before", before), state(pair, "after", after)),
                "reformat": (state(pair, "before", ref_before), state(pair, "after", ref_after)),
                "swap": (state(pair, "after", after), state(pair, "before", before)),
                "no_context": (
                    state(pair, "before", before, context=False),
                    state(pair, "after", after, context=False),
                ),
            }
            reports[pair["name"]] = {
                variant: review(pair, variant, b, a, args, output)
                for variant, (b, a) in variants.items()
            }
        checks = []
        for check in fixtures["checks"]:
            main_report = reports[check["pair"]]["main"]
            if main_report["status"] != "evaluated":
                checks.append(
                    {"expectation": check, "status": "skipped", "reason": main_report["status"]}
                )
                continue
            passed, observed = score(check, main_report["answers"])
            checks.append(
                {
                    "expectation": check,
                    "status": "passed" if passed else "failed",
                    "observed": observed,
                }
            )
        control_results = {
            name: controls(variant_reports, fixtures["controls"])
            for name, variant_reports in reports.items()
        }
        control_failures = [
            {"pair": name, "control": variant, **outcome}
            for name, per_pair in control_results.items()
            for variant, outcome in per_pair.items()
            if outcome["status"] == "failed"
        ]
        counts = {s: sum(c["status"] == s for c in checks) for s in ("passed", "failed", "skipped")}
        incomplete = any(
            r["status"] == "incomplete" for per in reports.values() for r in per.values()
        )
        failed = behavior["status"] == "failed" or counts["failed"] > 0 or bool(control_failures)
        result = {
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "fixture_version": fixtures["version"],
            "fixture_sha256": hashlib.sha256(args.fixtures.read_bytes()).hexdigest(),
            "rubric_version": rubric["version"],
            "rubric_sha256": hashlib.sha256(RUBRIC.read_bytes()).hexdigest(),
            "status": "incomplete"
            if incomplete
            else "failed"
            if failed
            else "static_only"
            if counts["skipped"]
            else "passed",
            "behavior": behavior,
            "static": static,
            "static_deltas": deltas,
            "static_separability": static_separability(fixtures["checks"], deltas),
            "semantic_counts": counts,
            "semantic_checks": checks,
            "controls": control_results,
            "control_failures": control_failures,
            "observations": {
                name: {
                    variant: {
                        k: r[k]
                        for k in (
                            "status",
                            "provider",
                            "endpoint",
                            "state_sha256",
                            "answers",
                            "response",
                            "error",
                        )
                        if k in r
                    }
                    for variant, r in per.items()
                }
                for name, per in reports.items()
            },
            "limitation": "Small synthetic suite; expectations and tolerances are fixture labels, "
            "not production gates or calibration.",
        }
        (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "output_dir": str(output),
                    "status": result["status"],
                    "behavior": behavior["status"],
                    "semantic_counts": counts,
                    "control_failures": len(control_failures),
                    "static_separability": result["static_separability"],
                },
                indent=2,
            )
        )
        return 2 if incomplete else 1 if failed else 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"status": "incomplete", "error": str(error), "output_dir": str(output)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
