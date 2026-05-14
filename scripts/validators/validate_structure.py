"""Validate file structure and naming conventions."""

import sys
import re
from pathlib import Path
from typing import List, Dict, Any

from rich.console import Console
from rich.table import Table

console = Console()


class StructureValidator:
    """Validate plugin and skill directory structure."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_plugin_structure(self, plugin_dir: Path) -> bool:
        """
        Validate a plugin's directory structure.

        Expected structure:
        plugin-name/
        ├── .claude-plugin/
        │   └── plugin.json (optional with strict=false)
        ├── SKILL.md (if it's a skill directory)
        ├── commands/ (optional)
        ├── agents/ (optional)
        ├── skills/ (optional)
        ├── hooks/ (optional)
        └── scripts/ (optional)
        """
        plugin_name = plugin_dir.name
        is_valid = True

        # Check plugin name format
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", plugin_name):
            self.errors.append(
                f"{plugin_name}: Invalid plugin name. "
                "Must use lowercase letters, numbers, and hyphens only."
            )
            is_valid = False

        # Check for .claude-plugin directory (for plugins with plugin.json)
        claude_plugin_dir = plugin_dir / ".claude-plugin"
        plugin_json = claude_plugin_dir / "plugin.json"

        has_plugin_json = plugin_json.exists()
        has_skill_md = (plugin_dir / "SKILL.md").exists()
        has_skills_dir = any(
            (d / "SKILL.md").exists()
            for d in (plugin_dir / "skills").iterdir()
            if d.is_dir()
        ) if (plugin_dir / "skills").is_dir() else False

        if not has_plugin_json and not has_skill_md and not has_skills_dir:
            self.warnings.append(
                f"{plugin_name}: Neither plugin.json nor SKILL.md found. "
                "This might be okay if strict=false in marketplace."
            )

        # Check that component directories are at plugin root, not in .claude-plugin
        component_dirs = ["commands", "agents", "skills", "hooks", "scripts"]

        for comp_dir in component_dirs:
            wrong_location = claude_plugin_dir / comp_dir
            if wrong_location.exists():
                self.errors.append(
                    f"{plugin_name}: '{comp_dir}/' should be at plugin root, "
                    f"not inside .claude-plugin/"
                )
                is_valid = False

        return is_valid

    def validate_skill_structure(self, skill_dir: Path) -> bool:
        """
        Validate a skill's directory structure.

        Expected:
        skill-name/
        ├── SKILL.md (required)
        ├── reference.md (optional)
        ├── examples.md (optional)
        ├── scripts/ (optional)
        └── templates/ (optional)
        """
        skill_name = skill_dir.name
        is_valid = True

        # Check skill name format
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", skill_name):
            self.errors.append(
                f"{skill_name}: Invalid skill name. "
                "Must use lowercase letters, numbers, and hyphens only."
            )
            is_valid = False

        # Check for SKILL.md (required)
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            self.errors.append(f"{skill_name}: Missing required SKILL.md file")
            is_valid = False

        # Check for common mistakes
        # 1. SKILL.md should not be nested
        nested_skill = skill_dir / "skills" / "SKILL.md"
        if nested_skill.exists():
            self.errors.append(
                f"{skill_name}: SKILL.md should be at root, not in skills/ subdirectory"
            )
            is_valid = False

        # 2. Check for uppercase SKILL names (common mistake)
        for item in skill_dir.iterdir():
            if item.is_file() and item.name.lower() == "skill.md" and item.name != "SKILL.md":
                self.errors.append(
                    f"{skill_name}: Found '{item.name}' but should be 'SKILL.md' (uppercase)"
                )
                is_valid = False

        return is_valid

    def validate_marketplace_structure(self) -> bool:
        """Validate marketplace root structure."""
        is_valid = True

        # Check for .claude-plugin/marketplace.json
        marketplace_json = self.base_dir / ".claude-plugin" / "marketplace.json"
        if not marketplace_json.exists():
            self.errors.append("Missing .claude-plugin/marketplace.json file")
            is_valid = False

        # Check for plugins directory
        plugins_dir = self.base_dir / "plugins"
        if not plugins_dir.exists():
            self.warnings.append(
                "No 'plugins/' directory found. " "This is okay if plugins are sourced externally."
            )

        # Check for recommended files
        recommended_files = ["README.md", "CHANGELOG.md", ".gitignore"]
        for filename in recommended_files:
            if not (self.base_dir / filename).exists():
                self.warnings.append(f"Recommended file missing: {filename}")

        return is_valid

    def validate_all(self) -> Dict[str, Any]:
        """Run all structure validations."""
        results = {
            "marketplace": {"valid": True, "errors": [], "warnings": []},
            "plugins": [],
            "skills": [],
            "summary": {"total_errors": 0, "total_warnings": 0},
        }

        # Validate marketplace structure
        self.errors = []
        self.warnings = []
        is_valid = self.validate_marketplace_structure()
        results["marketplace"] = {
            "valid": is_valid,
            "errors": self.errors.copy(),
            "warnings": self.warnings.copy(),
        }

        # Validate plugins
        plugins_dir = self.base_dir / "plugins"
        if plugins_dir.exists():
            for plugin_dir in sorted(plugins_dir.iterdir()):
                if not plugin_dir.is_dir():
                    continue

                self.errors = []
                self.warnings = []
                is_valid = self.validate_plugin_structure(plugin_dir)

                # Validate skills — check both root SKILL.md and skills/<name>/SKILL.md
                if (plugin_dir / "SKILL.md").exists():
                    skill_valid = self.validate_skill_structure(plugin_dir)
                    is_valid = is_valid and skill_valid

                skills_subdir = plugin_dir / "skills"
                if skills_subdir.is_dir():
                    for skill_dir in sorted(skills_subdir.iterdir()):
                        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                            skill_valid = self.validate_skill_structure(skill_dir)
                            is_valid = is_valid and skill_valid

                results["plugins"].append(
                    {
                        "name": plugin_dir.name,
                        "valid": is_valid,
                        "errors": self.errors.copy(),
                        "warnings": self.warnings.copy(),
                    }
                )

        # Calculate summary
        for result_list in [results["plugins"]]:
            for result in result_list:
                results["summary"]["total_errors"] += len(result["errors"])
                results["summary"]["total_warnings"] += len(result["warnings"])

        results["summary"]["total_errors"] += len(results["marketplace"]["errors"])
        results["summary"]["total_warnings"] += len(results["marketplace"]["warnings"])

        return results


def print_results(results: Dict[str, Any]) -> None:
    """Print validation results."""

    console.print("\n[bold]File Structure Validation[/bold]")

    # Marketplace results
    marketplace = results["marketplace"]
    if marketplace["errors"]:
        console.print("\n[red]✗ Marketplace structure errors:[/red]")
        for error in marketplace["errors"]:
            console.print(f"  • {error}")

    if marketplace["warnings"]:
        console.print("\n[yellow]⚠ Marketplace structure warnings:[/yellow]")
        for warning in marketplace["warnings"]:
            console.print(f"  • {warning}")

    # Plugin results table
    if results["plugins"]:
        table = Table(title="\nPlugin Structure Validation")
        table.add_column("Plugin", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Issues", style="yellow")

        for plugin in results["plugins"]:
            status = "[green]✓ PASS[/green]" if plugin["valid"] else "[red]✗ FAIL[/red]"
            issues = []
            if plugin["errors"]:
                issues.extend([f"[red]✗ {e}[/red]" for e in plugin["errors"]])
            if plugin["warnings"]:
                issues.extend([f"[yellow]⚠ {w}[/yellow]" for w in plugin["warnings"]])

            table.add_row(plugin["name"], status, "\n".join(issues) if issues else "")

        console.print(table)

    # Summary
    summary = results["summary"]
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"Total errors: [red]{summary['total_errors']}[/red]")
    console.print(f"Total warnings: [yellow]{summary['total_warnings']}[/yellow]")

    if summary["total_errors"] == 0:
        console.print("[green]✓ All structure validations passed![/green]")


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate file structure and naming conventions")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("."),
        help="Base directory of the marketplace (default: current directory)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error code if any validation fails (including warnings)",
    )

    args = parser.parse_args()

    validator = StructureValidator(args.base_dir)
    results = validator.validate_all()

    print_results(results)

    # Exit code
    if results["summary"]["total_errors"] > 0:
        return 1

    if args.strict and results["summary"]["total_warnings"] > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
