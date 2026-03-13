"""Tests for scripts.validate — validate_rule()."""

from __future__ import annotations

from scripts.types import CodeExample, Rule
from scripts.validate import validate_rule


def _make_valid_rule() -> Rule:
    """Create a minimal valid rule with required fields."""
    return Rule(
        id="1.1",
        title="Valid Rule",
        section=1,
        impact="HIGH",
        explanation="This explains the rule.",
        examples=[
            CodeExample(label="Incorrect", code="bad()", language="typescript"),
            CodeExample(label="Correct", code="good()", language="typescript"),
        ],
    )


# --- Valid rule ---


def test_valid_rule_no_errors() -> None:
    rule = _make_valid_rule()
    errors = validate_rule(rule, "test.md")
    assert errors == []


# --- Missing title ---


def test_missing_title() -> None:
    rule = _make_valid_rule()
    rule.title = ""
    errors = validate_rule(rule, "test.md")
    messages = [e.message for e in errors]
    assert any("title" in m.lower() for m in messages)


def test_whitespace_only_title() -> None:
    rule = _make_valid_rule()
    rule.title = "   "
    errors = validate_rule(rule, "test.md")
    messages = [e.message for e in errors]
    assert any("title" in m.lower() for m in messages)


# --- Missing explanation ---


def test_missing_explanation() -> None:
    rule = _make_valid_rule()
    rule.explanation = ""
    errors = validate_rule(rule, "test.md")
    messages = [e.message for e in errors]
    assert any("explanation" in m.lower() for m in messages)


def test_whitespace_only_explanation() -> None:
    rule = _make_valid_rule()
    rule.explanation = "  \n  "
    errors = validate_rule(rule, "test.md")
    messages = [e.message for e in errors]
    assert any("explanation" in m.lower() for m in messages)


# --- Missing examples ---


def test_missing_examples_empty_list() -> None:
    rule = _make_valid_rule()
    rule.examples = []
    errors = validate_rule(rule, "test.md")
    messages = [e.message for e in errors]
    assert any("example" in m.lower() for m in messages)


def test_examples_without_code() -> None:
    """Examples exist but have no code — should flag as missing code examples."""
    rule = _make_valid_rule()
    rule.examples = [
        CodeExample(label="Note", code="", language="typescript"),
    ]
    errors = validate_rule(rule, "test.md")
    messages = [e.message for e in errors]
    assert any("code" in m.lower() for m in messages)


def test_examples_only_bad_is_valid() -> None:
    """Having only bad examples (without good) still passes if they are code examples."""
    rule = _make_valid_rule()
    rule.examples = [
        CodeExample(label="Incorrect", code="bad()", language="typescript"),
    ]
    errors = validate_rule(rule, "test.md")
    assert errors == []


def test_examples_only_good_is_valid() -> None:
    """Having only good examples (without bad) still passes."""
    rule = _make_valid_rule()
    rule.examples = [
        CodeExample(label="Usage", code="use()", language="typescript"),
    ]
    errors = validate_rule(rule, "test.md")
    assert errors == []


def test_examples_neither_bad_nor_good() -> None:
    """Code examples that are neither bad nor good should flag an error."""
    rule = _make_valid_rule()
    rule.examples = [
        CodeExample(label="Random", code="something()", language="typescript"),
    ]
    errors = validate_rule(rule, "test.md")
    messages = [e.message for e in errors]
    assert any("bad" in m.lower() or "good" in m.lower() for m in messages)


# --- Invalid impact level ---


def test_invalid_impact_level() -> None:
    rule = _make_valid_rule()
    rule.impact = "SUPER-HIGH"
    errors = validate_rule(rule, "test.md")
    messages = [e.message for e in errors]
    assert any("impact level" in m.lower() for m in messages)


def test_valid_impact_levels() -> None:
    """All valid impact levels should pass."""
    valid_levels = ["CRITICAL", "HIGH", "MEDIUM-HIGH", "MEDIUM", "LOW-MEDIUM", "LOW"]
    for level in valid_levels:
        rule = _make_valid_rule()
        rule.impact = level
        errors = validate_rule(rule, "test.md")
        impact_errors = [e for e in errors if "impact level" in e.message.lower()]
        assert impact_errors == [], f"Impact level {level} should be valid"


# --- Multiple errors ---


def test_multiple_errors_reported() -> None:
    """A rule with multiple issues should report all errors."""
    rule = Rule(
        id="",
        title="",
        section=1,
        impact="INVALID",
        explanation="",
        examples=[],
    )
    errors = validate_rule(rule, "test.md")
    # Should have at least: missing title, missing explanation, missing examples, invalid impact
    assert len(errors) >= 4


# --- Error metadata ---


def test_error_contains_filename() -> None:
    rule = _make_valid_rule()
    rule.title = ""
    errors = validate_rule(rule, "my-rule.md")
    assert errors[0].file == "my-rule.md"


def test_error_contains_rule_id() -> None:
    rule = _make_valid_rule()
    rule.title = ""
    errors = validate_rule(rule, "test.md")
    assert errors[0].rule_id == "1.1"


# --- Label matching keywords ---


def test_bad_keyword_wrong() -> None:
    """The keyword 'wrong' should be recognized as a bad example."""
    rule = _make_valid_rule()
    rule.examples = [
        CodeExample(label="Wrong", code="x()", language="typescript"),
    ]
    errors = validate_rule(rule, "test.md")
    assert errors == []


def test_good_keyword_implementation() -> None:
    """The keyword 'implementation' should be recognized as a good example."""
    rule = _make_valid_rule()
    rule.examples = [
        CodeExample(label="Implementation", code="x()", language="typescript"),
    ]
    errors = validate_rule(rule, "test.md")
    assert errors == []


def test_good_keyword_example() -> None:
    """The keyword 'example' should be recognized as a good example."""
    rule = _make_valid_rule()
    rule.examples = [
        CodeExample(label="Example", code="x()", language="typescript"),
    ]
    errors = validate_rule(rule, "test.md")
    assert errors == []
