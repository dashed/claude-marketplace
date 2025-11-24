"""Run all validation checks for the Claude marketplace."""

import sys
import subprocess
import glob
from pathlib import Path
from typing import Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def run_validator(
    script: str, description: str, args: list[str] | None = None, is_shell_command: bool = False
) -> Dict[str, Any]:
    """
    Run a validation script and capture results.

    Args:
        script: Path to validation script or shell command
        description: Human-readable description
        args: Additional arguments to pass to script
        is_shell_command: If True, run as shell command instead of Python script

    Returns:
        Dictionary with results
    """
    if is_shell_command:
        cmd = [script]
        if args:
            # Expand glob patterns in args
            expanded_args = []
            for arg in args:
                if "*" in arg or "?" in arg:
                    # Expand glob pattern
                    matches = glob.glob(arg)
                    if matches:
                        expanded_args.extend(matches)
                    else:
                        # No matches, keep original arg
                        expanded_args.append(arg)
                else:
                    expanded_args.append(arg)
            cmd.extend(expanded_args)
    else:
        cmd = [sys.executable, script]
        if args:
            cmd.extend(args)

    result = subprocess.run(cmd, capture_output=True, text=True)

    return {
        "description": description,
        "script": script,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "passed": result.returncode == 0,
    }


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run all validation checks")
    parser.add_argument(
        "--strict", action="store_true", help="Exit with error code if any validation fails"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show full output from all validators"
    )

    args = parser.parse_args()

    validators_dir = Path(__file__).parent
    strict_flag = ["--strict"] if args.strict else []

    # Define validators to run
    validators = [
        {
            "script": str(validators_dir / "validate_structure.py"),
            "description": "File Structure Validation",
            "args": strict_flag,
        },
        {
            "script": str(validators_dir / "validate_json.py"),
            "description": "JSON Manifest Validation",
            "args": ["--all"] + strict_flag,
        },
        {
            "script": str(validators_dir / "validate_yaml.py"),
            "description": "YAML Frontmatter Validation",
            "args": strict_flag,
        },
    ]

    # Note: yamllint validation disabled because SKILL.md files are Markdown
    # with YAML frontmatter, not pure YAML. We use validate_yaml.py instead
    # which properly extracts and validates the frontmatter section.

    console.print(
        Panel.fit(
            "[bold cyan]Claude Marketplace - Static Validation Suite[/bold cyan]\n"
            f"Running {len(validators)} validation checks...",
            border_style="cyan",
        )
    )

    results = []

    # Run validators with progress indicator
    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:

        for validator in validators:
            task = progress.add_task(f"[cyan]{validator['description']}...", total=None)

            result = run_validator(
                validator["script"],
                validator["description"],
                validator.get("args"),
                validator.get("is_shell_command", False),
            )
            results.append(result)

            progress.update(task, completed=True)

            # Show result immediately
            status = "[green]✓ PASS[/green]" if result["passed"] else "[red]✗ FAIL[/red]"
            console.print(f"{status} {validator['description']}")

    # Print detailed results
    console.print("\n" + "=" * 70 + "\n")

    total_passed = 0
    total_failed = 0

    for result in results:
        if result["passed"]:
            total_passed += 1
        else:
            total_failed += 1

        if args.verbose or not result["passed"]:
            console.print(f"\n[bold]{result['description']}[/bold]")
            console.print(result["stdout"])
            if result["stderr"]:
                console.print(f"[red]Stderr:[/red]\n{result['stderr']}")

    # Summary
    console.print("\n" + "=" * 70)
    console.print(
        Panel.fit(
            f"[bold]Validation Summary[/bold]\n\n"
            f"Total checks: {len(results)}\n"
            f"[green]Passed: {total_passed}[/green]\n"
            f"[red]Failed: {total_failed}[/red]",
            border_style="green" if total_failed == 0 else "red",
        )
    )

    if total_failed == 0:
        console.print("[green bold]✓ All validations passed![/green bold]")
        return 0
    else:
        console.print("[red bold]✗ Some validations failed.[/red bold]")
        console.print("Run with --verbose to see full output.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
