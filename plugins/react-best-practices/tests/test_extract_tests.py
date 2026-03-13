"""Tests for scripts.extract_tests — extract_test_cases()."""

from __future__ import annotations

from scripts.extract_tests import extract_test_cases
from scripts.types import CodeExample, Rule


def _make_rule_with_examples(examples: list[CodeExample]) -> Rule:
    return Rule(
        id="1.1",
        title="Test Rule",
        section=1,
        impact="HIGH",
        explanation="Explanation.",
        examples=examples,
    )


# --- Incorrect examples → type="bad" ---


def test_incorrect_label_yields_bad() -> None:
    examples = [
        CodeExample(label="Incorrect", code="bad()", language="typescript"),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    assert len(cases) == 1
    assert cases[0].type == "bad"


def test_wrong_label_yields_bad() -> None:
    examples = [
        CodeExample(label="Wrong", code="bad()", language="typescript"),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    assert len(cases) == 1
    assert cases[0].type == "bad"


def test_bad_label_yields_bad() -> None:
    examples = [
        CodeExample(label="Bad", code="bad()", language="typescript"),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    assert len(cases) == 1
    assert cases[0].type == "bad"


# --- Correct examples → type="good" ---


def test_correct_label_yields_good() -> None:
    examples = [
        CodeExample(label="Correct", code="good()", language="typescript"),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    assert len(cases) == 1
    assert cases[0].type == "good"


def test_good_label_yields_good() -> None:
    examples = [
        CodeExample(label="Good", code="good()", language="typescript"),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    assert len(cases) == 1
    assert cases[0].type == "good"


# --- Non-matching labels → skipped ---


def test_usage_label_skipped() -> None:
    """Usage is not matched by extract_test_cases (only incorrect/wrong/bad and correct/good)."""
    examples = [
        CodeExample(label="Usage", code="use()", language="typescript"),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    assert len(cases) == 0


def test_implementation_label_skipped() -> None:
    """Implementation is not matched by extract_test_cases."""
    examples = [
        CodeExample(label="Implementation", code="impl()", language="typescript"),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    assert len(cases) == 0


def test_example_label_skipped() -> None:
    """Example is not matched by extract_test_cases."""
    examples = [
        CodeExample(label="Example", code="ex()", language="typescript"),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    assert len(cases) == 0


def test_note_label_skipped() -> None:
    examples = [
        CodeExample(label="Note", code="note()", language="typescript"),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    assert len(cases) == 0


# --- Output structure ---


def test_output_fields_match_dataclass() -> None:
    examples = [
        CodeExample(
            label="Incorrect",
            description="sequential calls",
            code="await a(); await b()",
            language="tsx",
        ),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    tc = cases[0]
    assert tc.rule_id == "1.1"
    assert tc.rule_title == "Test Rule"
    assert tc.type == "bad"
    assert tc.code == "await a(); await b()"
    assert tc.language == "tsx"
    assert tc.description == "sequential calls"


def test_description_fallback_when_none() -> None:
    """When example has no description, a default is generated."""
    examples = [
        CodeExample(label="Correct", code="good()", language="typescript"),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    assert "Correct example for Test Rule" in cases[0].description


def test_language_defaults_to_typescript() -> None:
    """When example language is None, defaults to typescript."""
    examples = [
        CodeExample(label="Incorrect", code="bad()", language=None),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    assert cases[0].language == "typescript"


# --- Mixed examples ---


def test_mixed_examples_correct_counts() -> None:
    """A rule with both bad and good examples produces the right number of test cases."""
    examples = [
        CodeExample(label="Incorrect", code="bad()", language="typescript"),
        CodeExample(label="Correct", code="good()", language="typescript"),
        CodeExample(label="Note", code="info()", language="typescript"),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    assert len(cases) == 2
    bad_cases = [c for c in cases if c.type == "bad"]
    good_cases = [c for c in cases if c.type == "good"]
    assert len(bad_cases) == 1
    assert len(good_cases) == 1


def test_multiple_bad_examples() -> None:
    examples = [
        CodeExample(label="Incorrect", description="pattern A", code="a()", language="typescript"),
        CodeExample(label="Wrong", description="pattern B", code="b()", language="typescript"),
        CodeExample(label="Correct", code="good()", language="typescript"),
    ]
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    bad_cases = [c for c in cases if c.type == "bad"]
    assert len(bad_cases) == 2


def test_empty_examples_list() -> None:
    rule = _make_rule_with_examples([])
    cases = extract_test_cases(rule)
    assert cases == []


def test_case_insensitive_label_matching() -> None:
    """Labels like 'INCORRECT' or 'incorrect' should be matched."""
    examples = [
        CodeExample(label="INCORRECT", code="bad()", language="typescript"),
        CodeExample(label="correct", code="good()", language="typescript"),
    ]
    # The label is lowered inside extract_test_cases, so mixed case should work
    rule = _make_rule_with_examples(examples)
    cases = extract_test_cases(rule)
    # Note: extract_test_cases does label_lower = example.label.lower()
    # "INCORRECT" → "incorrect" → contains "incorrect" → bad
    # "correct" → "correct" → contains "correct" → good
    assert len(cases) == 2
    assert cases[0].type == "bad"
    assert cases[1].type == "good"
