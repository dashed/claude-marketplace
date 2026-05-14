"""Validate YAML frontmatter in SKILL.md files."""

import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any

import yaml
import jsonschema
from rich.console import Console
from rich.table import Table

console = Console()


def extract_frontmatter(content: str) -> Tuple[str, int, int]:
    """
    Extract YAML frontmatter from markdown content.

    Returns:
        Tuple of (frontmatter_content, start_line, end_line)
    """
    lines = content.split("\n")

    # Check for opening ---
    if not lines or lines[0].strip() != "---":
        raise ValueError("Missing opening '---' for frontmatter")

    # Find closing ---
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("Missing closing '---' for frontmatter")

    frontmatter = "\n".join(lines[1:end_idx])
    return frontmatter, 1, end_idx + 1


def validate_skill_frontmatter(skill_path: Path, schema_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate YAML frontmatter in a SKILL.md file.

    Args:
        skill_path: Path to SKILL.md file
        schema_path: Path to JSON schema for validation

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    try:
        # Read skill file
        content = skill_path.read_text()

        # Extract frontmatter
        try:
            frontmatter_str, start_line, end_line = extract_frontmatter(content)
        except ValueError as e:
            errors.append(f"Frontmatter extraction error: {e}")
            return False, errors

        # Parse YAML
        try:
            frontmatter = yaml.safe_load(frontmatter_str)
        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error (lines {start_line}-{end_line}): {e}")
            return False, errors

        # Load schema
        schema = yaml.safe_load(schema_path.read_text())

        # Validate against schema
        try:
            jsonschema.validate(instance=frontmatter, schema=schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
            if e.path:
                errors.append(f"  at path: {'.'.join(str(p) for p in e.path)}")
            return False, errors

        # Additional checks (only if fields are present — both are optional per spec)

        # Check name format (if provided)
        name = frontmatter.get("name")
        if name is not None and not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            errors.append(
                f"Invalid name format: '{name}'. "
                "Must use lowercase letters, numbers, and hyphens only."
            )

        # Check description quality (if provided)
        description = frontmatter.get("description", "")
        if description and len(description) < 20:
            errors.append(
                f"Description too short ({len(description)} chars). "
                "Should be at least 20 characters and include both what the skill does "
                "and when to use it."
            )
        elif not description:
            console.print(
                f"[yellow]Warning:[/yellow] No description in {skill_path.name}. "
                "Recommended for skill discovery."
            )

        # Check for "Use when" clause (best practice)
        if description and "use when" not in description.lower():
            # This is a warning, not an error
            console.print(
                f"[yellow]Warning:[/yellow] Description in {skill_path.name} "
                "should include 'Use when...' clause for better skill discovery."
            )

        if errors:
            return False, errors

        return True, []

    except Exception as e:
        errors.append(f"Unexpected error: {e}")
        return False, errors


def validate_all_skills(plugins_dir: Path, schema_path: Path) -> Dict[str, Any]:
    """
    Validate all SKILL.md files in plugins directory.

    Returns:
        Dictionary with validation results
    """
    results = {"total": 0, "passed": 0, "failed": 0, "details": []}

    # Find all SKILL.md files
    skill_files = list(plugins_dir.glob("*/SKILL.md"))

    if not skill_files:
        console.print(f"[yellow]No SKILL.md files found in {plugins_dir}[/yellow]")
        return results

    results["total"] = len(skill_files)

    for skill_file in sorted(skill_files):
        is_valid, errors = validate_skill_frontmatter(skill_file, schema_path)

        result = {
            "file": str(skill_file.relative_to(plugins_dir.parent)),
            "valid": is_valid,
            "errors": errors,
        }
        results["details"].append(result)

        if is_valid:
            results["passed"] += 1
        else:
            results["failed"] += 1

    return results


def print_results(results: Dict[str, Any]) -> None:
    """Print validation results in a nice table."""

    # Summary
    console.print("\n[bold]YAML Frontmatter Validation Summary[/bold]")
    console.print(f"Total files: {results['total']}")
    console.print(f"[green]Passed: {results['passed']}[/green]")
    console.print(f"[red]Failed: {results['failed']}[/red]")

    # Details table
    if results["details"]:
        table = Table(title="Validation Details")
        table.add_column("File", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Errors", style="red")

        for detail in results["details"]:
            status = "[green]✓ PASS[/green]" if detail["valid"] else "[red]✗ FAIL[/red]"
            errors = "\n".join(detail["errors"]) if detail["errors"] else ""
            table.add_row(detail["file"], status, errors)

        console.print(table)


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate YAML frontmatter in SKILL.md files")
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        default=Path("plugins"),
        help="Directory containing plugin folders (default: plugins)",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("schemas/skill-frontmatter-schema.json"),
        help="Path to JSON schema file",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Exit with error code if any validation fails"
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.plugins_dir.exists():
        console.print(f"[red]Error: Plugins directory not found: {args.plugins_dir}[/red]")
        return 1

    if not args.schema.exists():
        console.print(f"[red]Error: Schema file not found: {args.schema}[/red]")
        return 1

    # Run validation
    results = validate_all_skills(args.plugins_dir, args.schema)

    # Print results
    print_results(results)

    # Exit code
    if args.strict and results["failed"] > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
