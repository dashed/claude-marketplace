"""Extract test cases from rules for LLM evaluation."""

from __future__ import annotations

import json
import sys

from .config import RULES_DIR, TEST_CASES_FILE
from .parser import parse_rule_file
from .types import Rule, TestCase


def extract_test_cases(rule: Rule) -> list[TestCase]:
    """Extract test cases from a rule."""
    test_cases: list[TestCase] = []

    for example in rule.examples:
        label_lower = example.label.lower()
        is_bad = any(kw in label_lower for kw in ("incorrect", "wrong", "bad"))
        is_good = any(kw in label_lower for kw in ("correct", "good"))

        if is_bad or is_good:
            test_cases.append(
                TestCase(
                    rule_id=rule.id,
                    rule_title=rule.title,
                    type="bad" if is_bad else "good",
                    code=example.code,
                    language=example.language or "typescript",
                    description=(
                        example.description or f"{example.label} example for {rule.title}"
                    ),
                )
            )

    return test_cases


def extract_tests() -> None:
    """Main extraction function."""
    try:
        print("Extracting test cases from rules...")
        print(f"Rules directory: {RULES_DIR}")
        print(f"Output file: {TEST_CASES_FILE}")

        files = sorted(
            f.name
            for f in RULES_DIR.iterdir()
            if f.suffix == ".md" and not f.name.startswith("_") and f.name != "README.md"
        )

        all_test_cases: list[TestCase] = []

        for filename in files:
            file_path = RULES_DIR / filename
            try:
                rf = parse_rule_file(file_path)
                test_cases = extract_test_cases(rf.rule)
                all_test_cases.extend(test_cases)
            except Exception as e:
                print(f"Error processing {filename}: {e}", file=sys.stderr)

        # Write test cases as JSON
        output = [
            {
                "ruleId": tc.rule_id,
                "ruleTitle": tc.rule_title,
                "type": tc.type,
                "code": tc.code,
                "language": tc.language,
                "description": tc.description,
            }
            for tc in all_test_cases
        ]
        TEST_CASES_FILE.write_text(json.dumps(output, indent=2), encoding="utf-8")

        bad_count = sum(1 for tc in all_test_cases if tc.type == "bad")
        good_count = sum(1 for tc in all_test_cases if tc.type == "good")
        print(f"Extracted {len(all_test_cases)} test cases to {TEST_CASES_FILE}")
        print(f"  - Bad examples: {bad_count}")
        print(f"  - Good examples: {good_count}")
    except Exception as e:
        print(f"Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)
