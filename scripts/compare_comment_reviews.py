#!/usr/bin/env python3
"""Compare recorded blind and Jev-assisted reviews against frozen fixture labels.

This deterministic, offline comparison never executes fixture source or calls AI.
Exit 0 means a valid comparison, including ties or harm; 2 means incomplete input.
Probability thresholds become Boolean proposal labels; numerical information-loss
predictions are deliberately excluded from the agent comparison.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

DISPOSITIONS = {"keep", "delete", "reduce", "rewrite", "needs_context"}
TRANSITIONS = {
    ("incorrect", "correct"): "improvements",
    ("correct", "incorrect"): "regressions",
    ("correct", "correct"): "unchanged_correct",
    ("incorrect", "incorrect"): "unchanged_incorrect",
    ("abstained", "correct"): "abstention_to_correct",
    ("abstained", "incorrect"): "abstention_to_incorrect",
    ("correct", "abstained"): "correct_to_abstention",
    ("incorrect", "abstained"): "incorrect_to_abstention",
    ("abstained", "abstained"): "unchanged_abstained",
}


def index_cases(document: Any, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(document, dict) or not isinstance(document.get("cases"), list):
        raise ValueError(f"{label}: expected an object with a cases array.")
    cases = {}
    for case in document["cases"]:
        if not isinstance(case, dict):
            raise ValueError(f"{label}: case must be an object.")
        name = case.get("name")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9_]+", name):
            raise ValueError(f"{label}: invalid case name.")
        if name in cases:
            raise ValueError(f"{label}: duplicate case {name}.")
        cases[name] = case
    if not cases:
        raise ValueError(f"{label}: cases must not be empty.")
    return cases


def frozen_labels(case: dict[str, Any]) -> dict[str, str | bool]:
    name = case["name"]
    if not isinstance(case.get("state"), dict) or not isinstance(case.get("expectations"), list):
        raise ValueError(f"Fixtures: {name} requires state and expectations.")
    labels: dict[str, str | bool] = {}
    for expectation in case["expectations"]:
        if not isinstance(expectation, dict):
            raise ValueError(f"Fixtures: {name} has a malformed expectation.")
        signal = expectation.get("signal")
        if signal == "information_loss":
            continue
        if signal not in ("disposition", "proposal_preserves_information") or signal in labels:
            raise ValueError(f"Fixtures: {name} has an unknown or duplicate decision label.")
        if signal == "disposition":
            value = expectation.get("equals")
            if not isinstance(value, str) or value not in DISPOSITIONS:
                raise ValueError(f"Fixtures: {name} requires a disposition equals label.")
        else:
            bounds = [key for key in ("minimum", "maximum") if key in expectation]
            if len(bounds) != 1:
                raise ValueError(f"Fixtures: {name} requires one proposal probability bound.")
            bound = expectation[bounds[0]]
            if (
                type(bound) not in (int, float)
                or not 0 <= bound <= 1
                or not math.isfinite(bound)
                or (bounds[0] == "minimum" and bound < 0.5)
                or (bounds[0] == "maximum" and bound >= 0.5)
            ):
                raise ValueError(f"Fixtures: {name} has an ambiguous proposal Boolean label.")
            value = bounds[0] == "minimum"
        labels[signal] = value
    required = {"disposition"}
    if "proposal" in case["state"]:
        required.add("proposal_preserves_information")
    if labels.keys() != required:
        raise ValueError(f"Fixtures: {name} lacks labels or labels an absent proposal.")
    return labels


def validate_review(
    document: Any, fixtures: dict[str, dict[str, Any]], label: str
) -> dict[str, dict[str, Any]]:
    cases = index_cases(document, label)
    if not isinstance(document.get("evaluated_at"), str) or not document["evaluated_at"].strip():
        raise ValueError(f"{label}: evaluated_at must be a nonempty string.")
    missing, extra = sorted(fixtures.keys() - cases.keys()), sorted(cases.keys() - fixtures.keys())
    if missing or extra:
        raise ValueError(f"{label}: case coverage differs; missing={missing}, extra={extra}.")
    for name, case in cases.items():
        disposition = case.get("disposition")
        if not isinstance(disposition, str) or disposition not in DISPOSITIONS:
            raise ValueError(f"{label}: {name} has an invalid disposition.")
        if not isinstance(case.get("reason"), str) or not case["reason"].strip():
            raise ValueError(f"{label}: {name} requires a nonempty reason.")
        field = "proposal_preserves_information"
        if "proposal" in fixtures[name]["state"]:
            if field not in case or (case[field] is not None and type(case[field]) is not bool):
                raise ValueError(f"{label}: {name} requires a Boolean or null proposal answer.")
        elif case.get(field) is not None:
            raise ValueError(f"{label}: {name} answers an absent proposal.")
    return cases


def compare_reviews(fixtures: Any, baseline: Any, assisted: Any) -> dict[str, Any]:
    cases = index_cases(fixtures, "Fixtures")
    labels = {name: frozen_labels(case) for name, case in cases.items()}
    before = validate_review(baseline, cases, "Baseline")
    after = validate_review(assisted, cases, "Assisted")
    counts = dict.fromkeys(TRANSITIONS.values(), 0)
    counts.update(
        baseline_correct=0,
        assisted_correct=0,
        baseline_incorrect=0,
        assisted_incorrect=0,
        baseline_abstentions=0,
        assisted_abstentions=0,
    )
    decisions = []
    for name, expected_labels in labels.items():
        for signal, expected in expected_labels.items():
            observations = [before[name][signal], after[name][signal]]
            outcomes = [
                "abstained" if value is None else "correct" if value == expected else "incorrect"
                for value in observations
            ]
            transition = TRANSITIONS[(outcomes[0], outcomes[1])]
            counts[transition] += 1
            for review, outcome in zip(("baseline", "assisted"), outcomes, strict=True):
                counts[f"{review}_{'abstentions' if outcome == 'abstained' else outcome}"] += 1
            decisions.append(
                {
                    "case": name,
                    "signal": signal,
                    "expected": expected,
                    "before": observations[0],
                    "after": observations[1],
                    "baseline_outcome": outcomes[0],
                    "assisted_outcome": outcomes[1],
                    "transition": transition,
                    "baseline_reason": before[name]["reason"],
                    "assisted_reason": after[name]["reason"],
                }
            )
    return {
        "status": "compared",
        "fixture_version": fixtures.get("version"),
        "case_count": len(cases),
        "decision_count": len(decisions),
        "baseline_evaluated_at": baseline["evaluated_at"],
        "assisted_evaluated_at": assisted["evaluated_at"],
        "counts": counts,
        "decisions": decisions,
        "excluded_signals": ["information_loss"],
        "limitation": (
            "Valid comparison does not establish benefit. Labels are frozen fixture judgments; "
            "the comparator cannot verify review independence, blinding, or generalization. "
            "Abstentions are separate from errors and never counted as correct."
        ),
    }


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON field: {key}.")
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--assisted", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, help="New evidence file; existing files are never replaced"
    )
    args = parser.parse_args()
    try:
        documents, hashes = {}, {}
        for label in ("fixtures", "baseline", "assisted"):
            content = getattr(args, label).read_bytes()
            documents[label] = json.loads(content, object_pairs_hook=unique_object)
            hashes[label] = hashlib.sha256(content).hexdigest()
        report = compare_reviews(**documents)
        report["input_sha256"] = hashes
        serialized = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if args.output is not None:
            with args.output.open("x", encoding="utf-8") as output:
                output.write(serialized)
        print(serialized, end="")
        return 0
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"status": "incomplete", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
