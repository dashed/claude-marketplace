"""Validate rule files follow the correct structure."""

from __future__ import annotations

import sys
from dataclasses import dataclass

from .config import RULES_DIR
from .parser import parse_rule_file
from .types import VALID_IMPACT_LEVELS, Rule


@dataclass
class ValidationError:
    file: str
    rule_id: str | None = None
    message: str = ""


def validate_rule(rule: Rule, filename: str) -> list[ValidationError]:
    """Validate a rule."""
    errors: list[ValidationError] = []

    # Note: rule.id is auto-generated during build, not required in source files

    if not rule.title or not rule.title.strip():
        errors.append(
            ValidationError(file=filename, rule_id=rule.id, message="Missing or empty title")
        )

    if not rule.explanation or not rule.explanation.strip():
        errors.append(
            ValidationError(file=filename, rule_id=rule.id, message="Missing or empty explanation")
        )

    if not rule.examples:
        errors.append(
            ValidationError(
                file=filename,
                rule_id=rule.id,
                message="Missing examples (need at least one bad and one good example)",
            )
        )
    else:
        # Filter out informational examples (notes, trade-offs, etc.) that don't have code
        code_examples = [e for e in rule.examples if e.code and e.code.strip()]

        has_bad = any(
            any(kw in e.label.lower() for kw in ("incorrect", "wrong", "bad"))
            for e in code_examples
        )
        has_good = any(
            any(
                kw in e.label.lower()
                for kw in ("correct", "good", "usage", "implementation", "example")
            )
            for e in code_examples
        )

        if not code_examples:
            errors.append(
                ValidationError(file=filename, rule_id=rule.id, message="Missing code examples")
            )
        elif not has_bad and not has_good:
            errors.append(
                ValidationError(
                    file=filename,
                    rule_id=rule.id,
                    message="Missing bad/incorrect or good/correct examples",
                )
            )

    if rule.impact not in VALID_IMPACT_LEVELS:
        errors.append(
            ValidationError(
                file=filename,
                rule_id=rule.id,
                message=(
                    f"Invalid impact level: {rule.impact}. "
                    f"Must be one of: {', '.join(VALID_IMPACT_LEVELS)}"
                ),
            )
        )

    return errors


def validate() -> None:
    """Main validation function."""
    try:
        print("Validating rule files...")
        print(f"Rules directory: {RULES_DIR}")

        files = sorted(
            f.name for f in RULES_DIR.iterdir() if f.suffix == ".md" and not f.name.startswith("_")
        )

        all_errors: list[ValidationError] = []

        for filename in files:
            file_path = RULES_DIR / filename
            try:
                rf = parse_rule_file(file_path)
                errors = validate_rule(rf.rule, filename)
                all_errors.extend(errors)
            except Exception as e:
                all_errors.append(ValidationError(file=filename, message=f"Failed to parse: {e}"))

        if all_errors:
            print("\nValidation failed:\n", file=sys.stderr)
            for error in all_errors:
                rule_part = f" ({error.rule_id})" if error.rule_id else ""
                print(f"  {error.file}{rule_part}: {error.message}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"All {len(files)} rule files are valid")
    except Exception as e:
        print(f"Validation failed: {e}", file=sys.stderr)
        sys.exit(1)
