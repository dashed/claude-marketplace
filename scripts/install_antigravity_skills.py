#!/usr/bin/env python3
"""Install and manage this repository's plugin skills for Antigravity."""

from __future__ import annotations

import argparse
import difflib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence, TextIO

DEFAULT_DEST_DIR = Path("~/.gemini/config/skills")
WORKSPACE_SKILLS_SUBDIR = Path(".agents/skills")

SkillStatus = Literal["enabled", "disabled", "conflict", "external", "invalid"]
Action = Literal["enable", "disable", "uninstall"]


class InstallerError(RuntimeError):
    """Raised when the installer cannot proceed."""


@dataclass(frozen=True)
class SkillState:
    """Current state of one Antigravity skill entry."""

    name: str
    status: SkillStatus
    source_dir: Path | None
    target_path: Path
    expected_link_target: str | None
    detail: str


@dataclass
class OperationResult:
    """Result from applying an enable, disable, or uninstall action."""

    changed: list[str]
    unchanged: list[str]
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def default_repo_root() -> Path:
    """Return the repository root based on this script's location."""
    return Path(__file__).resolve().parent.parent


def discover_skill_dirs(plugins_dir: Path) -> list[Path]:
    """Return skill directories inside plugins/<plugin>/skills/<skill>/ (or flat plugins/<skill>/)."""
    if not plugins_dir.is_dir():
        raise InstallerError(f"plugins directory not found: {plugins_dir}")

    by_name: dict[str, Path] = {}
    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue

        collected: list[Path] = []
        skills_subdir = plugin_dir / "skills"
        if skills_subdir.is_dir():
            for skill_dir in sorted(skills_subdir.iterdir()):
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file():
                    collected.append(skill_dir)

        if (plugin_dir / "SKILL.md").is_file() and not any(
            path.name == plugin_dir.name for path in collected
        ):
            collected.append(plugin_dir)

        for candidate in collected:
            existing = by_name.get(candidate.name)
            if existing is not None:
                raise InstallerError(
                    f"duplicate skill name '{candidate.name}': {existing} and {candidate}"
                )
            by_name[candidate.name] = candidate

    if not by_name:
        raise InstallerError(f"no plugin skills found in {plugins_dir}")

    return sorted(by_name.values(), key=lambda path: path.name)


def resolve_dest_dir(*, dest_dir: Path | None = None, workspace: Path | None = None) -> Path:
    """Resolve the target Antigravity skills directory."""
    if dest_dir is not None and workspace is not None:
        raise InstallerError("choose only one of --dest or --workspace")

    if workspace is not None:
        workspace_path = workspace.expanduser()
        if not workspace_path.is_dir():
            raise InstallerError(f"workspace directory not found: {workspace_path}")
        return workspace_path.resolve() / WORKSPACE_SKILLS_SUBDIR

    raw = (dest_dir or DEFAULT_DEST_DIR).expanduser()
    if raw.is_absolute():
        return raw
    return Path.cwd() / raw


def link_target_for(source_dir: Path) -> str:
    """Return the absolute symlink target string to use for a skill directory."""
    return str(source_dir.resolve())


def load_skill_states(
    repo_root: Path,
    dest_dir: Path | None = None,
    *,
    workspace: Path | None = None,
) -> tuple[Path, dict[str, SkillState]]:
    """Load repo plugin skills plus existing entries in an Antigravity skills directory."""
    repo_root = repo_root.expanduser().resolve()
    plugins_dir = repo_root / "plugins"
    skill_dirs = discover_skill_dirs(plugins_dir)
    resolved_dest = resolve_dest_dir(dest_dir=dest_dir, workspace=workspace)

    if resolved_dest.exists() and not resolved_dest.is_dir():
        raise InstallerError(f"skills destination is not a directory: {resolved_dest}")

    states: dict[str, SkillState] = {}
    for source_dir in skill_dirs:
        name = source_dir.name
        target_path = resolved_dest / name
        expected_link_target = link_target_for(source_dir)
        status: SkillStatus = "disabled"
        detail = "not linked"

        # Check is_symlink() before exists() so broken symlinks classify as conflicts.
        if target_path.is_symlink():
            existing_target = os.readlink(target_path)
            if existing_target == expected_link_target:
                status = "enabled"
                detail = existing_target
            else:
                status = "conflict"
                detail = f"symlink points to {existing_target}"
        elif target_path.exists():
            status = "conflict"
            detail = "path exists and is not a symlink"

        states[name] = SkillState(
            name=name,
            status=status,
            source_dir=source_dir,
            target_path=target_path,
            expected_link_target=expected_link_target,
            detail=detail,
        )

    if resolved_dest.is_dir():
        for target_path in sorted(resolved_dest.iterdir()):
            name = target_path.name
            if name in states:
                continue

            if target_path.is_symlink():
                status = "external"
                detail = os.readlink(target_path)
            elif target_path.is_dir() and (target_path / "SKILL.md").is_file():
                status = "external"
                detail = "directory skill outside marketplace"
            else:
                status = "invalid"
                detail = "not a symlink or skill directory"

            states[name] = SkillState(
                name=name,
                status=status,
                source_dir=None,
                target_path=target_path,
                expected_link_target=None,
                detail=detail,
            )

    return resolved_dest, dict(sorted(states.items()))


def enable_skill(
    state: SkillState, *, force: bool = False, dry_run: bool = False
) -> OperationResult:
    """Enable one marketplace skill by creating its Antigravity symlink."""
    if state.source_dir is None or state.expected_link_target is None:
        return OperationResult([], [], [f"{state.name}: cannot enable skills outside marketplace"])
    if state.status == "enabled":
        return OperationResult([], [f"{state.name}: already enabled"], [])
    if state.status == "conflict" and not (force and state.target_path.is_symlink()):
        return OperationResult([], [], [f"{state.name}: {state.detail}"])
    if state.target_path.exists() and not state.target_path.is_symlink():
        return OperationResult([], [], [f"{state.name}: {state.detail}"])

    is_replace = state.target_path.is_symlink()
    if dry_run:
        verb = "would replace" if is_replace else "would enable"
        return OperationResult([f"{state.name}: {verb} -> {state.expected_link_target}"], [], [])

    state.target_path.parent.mkdir(parents=True, exist_ok=True)
    if is_replace:
        state.target_path.unlink()
    state.target_path.symlink_to(state.expected_link_target, target_is_directory=True)
    verb = "replaced" if is_replace else "enabled"
    return OperationResult([f"{state.name}: {verb} -> {state.expected_link_target}"], [], [])


def disable_skill(state: SkillState, *, dry_run: bool = False) -> OperationResult:
    """Disable one managed marketplace skill by removing its expected symlink."""
    if state.status == "disabled":
        return OperationResult([], [f"{state.name}: already disabled"], [])
    if state.status != "enabled" or not state.target_path.is_symlink():
        return OperationResult([], [], [f"{state.name}: disable refused for {state.status} entry"])

    if dry_run:
        return OperationResult([f"{state.name}: would disable"], [], [])

    state.target_path.unlink()
    return OperationResult([f"{state.name}: disabled"], [], [])


def uninstall_skill(state: SkillState, *, dry_run: bool = False) -> OperationResult:
    """Remove one symlinked skill from the Antigravity skills directory."""
    if state.status == "disabled":
        return OperationResult([], [f"{state.name}: not installed"], [])
    if not state.target_path.is_symlink():
        return OperationResult(
            [],
            [],
            [f"{state.name}: uninstall refused because {state.target_path} is not a symlink"],
        )

    if dry_run:
        return OperationResult([f"{state.name}: would uninstall"], [], [])

    state.target_path.unlink()
    return OperationResult([f"{state.name}: uninstalled"], [], [])


def merge_results(results: Sequence[OperationResult]) -> OperationResult:
    """Merge multiple operation results."""
    merged = OperationResult([], [], [])
    for result in results:
        merged.changed.extend(result.changed)
        merged.unchanged.extend(result.unchanged)
        merged.errors.extend(result.errors)
    return merged


def all_repo_skill_names(states: dict[str, SkillState]) -> list[str]:
    """Return skill names backed by this repository's plugins directory."""
    return [name for name, state in states.items() if state.source_dir is not None]


def all_symlink_skill_names(states: dict[str, SkillState]) -> list[str]:
    """Return skill names currently installed as symlinks."""
    return [name for name, state in states.items() if state.target_path.is_symlink()]


def dedupe_preserve_order(names: Sequence[str]) -> list[str]:
    """Return unique names preserving their first-seen order."""
    return list(dict.fromkeys(names))


def expand_requested_names(
    states: dict[str, SkillState], requested: Sequence[str], *, action: Action
) -> list[str]:
    """Expand 'all' tokens and deduplicate requested skill names."""
    expanded: list[str] = []
    for token in requested:
        if token == "all":
            expanded.extend(
                all_symlink_skill_names(states)
                if action == "uninstall"
                else all_repo_skill_names(states)
            )
        else:
            expanded.append(token)
    return dedupe_preserve_order(expanded)


def apply_action(
    states: dict[str, SkillState],
    action: Action,
    names: Sequence[str],
    *,
    force: bool = False,
    dry_run: bool = False,
) -> OperationResult:
    """Apply an action to named skills (supports 'all')."""
    if not names:
        return OperationResult([], [], ["no skills selected"])

    expanded = expand_requested_names(states, names, action=action)
    if action == "uninstall" and not expanded:
        return OperationResult([], ["no symlinked skills installed"], [])
    if not expanded:
        return OperationResult([], [], ["no skills selected"])

    missing = [name for name in expanded if name not in states]
    if missing:
        known = list(states)
        errors: list[str] = []
        for name in missing:
            matches = difflib.get_close_matches(name, known, n=3)
            if matches:
                errors.append(f"unknown skill: {name} (did you mean: {', '.join(matches)})")
            else:
                errors.append(f"unknown skill: {name}")
        return OperationResult([], [], errors)

    results: list[OperationResult] = []
    for name in expanded:
        state = states[name]
        if action == "enable":
            results.append(enable_skill(state, force=force, dry_run=dry_run))
        elif action == "disable":
            results.append(disable_skill(state, dry_run=dry_run))
        else:
            results.append(uninstall_skill(state, dry_run=dry_run))
    return merge_results(results)


def filter_states(states: dict[str, SkillState], query: str) -> list[SkillState]:
    """Return skill states filtered case-insensitively by substring on name."""
    needle = query.strip().lower()
    if not needle:
        return list(states.values())
    return [state for state in states.values() if needle in state.name.lower()]


def names_from_tokens(
    visible_states: Sequence[SkillState],
    all_states: dict[str, SkillState],
    tokens: Sequence[str],
    *,
    symlink_all: bool = False,
) -> list[str]:
    """Resolve interactive command tokens to skill names."""
    if len(tokens) == 1 and tokens[0] == "all":
        return (
            all_symlink_skill_names(all_states) if symlink_all else all_repo_skill_names(all_states)
        )

    names: list[str] = []
    for token in tokens:
        if token.isdigit():
            index = int(token)
            if index < 1 or index > len(visible_states):
                raise ValueError(f"invalid selection number: {token}")
            names.append(visible_states[index - 1].name)
        else:
            names.append(token)
    return names


def status_counts(states: dict[str, SkillState]) -> dict[SkillStatus, int]:
    """Count skill entries per status."""
    counts: dict[SkillStatus, int] = {
        "enabled": 0,
        "disabled": 0,
        "conflict": 0,
        "external": 0,
        "invalid": 0,
    }
    for state in states.values():
        counts[state.status] += 1
    return counts


def format_status_summary(states: dict[str, SkillState]) -> str:
    """Format a compact one-line status count summary."""
    counts = status_counts(states)
    return (
        f"enabled: {counts['enabled']}, disabled: {counts['disabled']}, "
        f"conflict: {counts['conflict']}, external: {counts['external']}, "
        f"invalid: {counts['invalid']}"
    )


def render_table(
    visible_states: Sequence[SkillState],
    all_states: dict[str, SkillState],
    dest_dir: Path,
    *,
    query: str = "",
    stdout: TextIO | None = None,
) -> None:
    """Render the current skill state table."""
    out = stdout or sys.stdout
    print(f"Antigravity Skills: {dest_dir}", file=out)
    print(f"Summary: {format_status_summary(all_states)}", file=out)
    if query:
        print(f"Filter: {query} ({len(visible_states)}/{len(all_states)})", file=out)
    print(f"{'#':>3}  {'Status':<9}  {'Skill':<28}  Detail", file=out)
    print("-" * 80, file=out)

    for index, state in enumerate(visible_states, start=1):
        print(f"{index:>3}  {state.status:<9}  {state.name:<28}  {state.detail}", file=out)

    print(
        "\nCommands: e <skill|#|all>, d <skill|#|all>, u <skill|#|all>, "
        "f [query], r refresh, q quit",
        file=out,
    )


def print_operation_result(
    result: OperationResult, stdout: TextIO | None = None, stderr: TextIO | None = None
) -> None:
    """Print operation messages and errors."""
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    for message in result.changed:
        print(message, file=out)
    for message in result.unchanged:
        print(message, file=out)
    for message in result.errors:
        print(f"error: {message}", file=err)


def run_interactive(
    repo_root: Path,
    *,
    dest_dir: Path | None = None,
    workspace: Path | None = None,
    force: bool = False,
) -> int:
    """Run the interactive Antigravity skills manager."""
    query = ""
    action_by_command: dict[str, Action] = {
        "e": "enable",
        "enable": "enable",
        "d": "disable",
        "disable": "disable",
        "u": "uninstall",
        "uninstall": "uninstall",
    }

    while True:
        resolved_dest, states = load_skill_states(repo_root, dest_dir=dest_dir, workspace=workspace)
        visible_states = filter_states(states, query)
        print("\033[H\033[J", end="")
        render_table(visible_states, states, resolved_dest, query=query)

        try:
            raw_command = input("antigravity-skills> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not raw_command:
            continue
        if raw_command in {"q", "quit", "exit"}:
            return 0
        if raw_command in {"r", "refresh"}:
            continue

        parts = raw_command.split()
        command = parts[0]
        if command in {"f", "filter"}:
            remainder = raw_command.split(maxsplit=1)
            query = remainder[1].strip() if len(remainder) > 1 else ""
            continue

        action = action_by_command.get(command)
        if action is None:
            print("error: unknown command", file=sys.stderr)
            try:
                input("press enter to continue")
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            continue

        tokens = parts[1:]
        try:
            names = names_from_tokens(
                visible_states, states, tokens, symlink_all=action == "uninstall"
            )
        except ValueError as error:
            print(f"error: {error}", file=sys.stderr)
            try:
                input("press enter to continue")
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            continue

        result = apply_action(states, action, names, force=force)
        print_operation_result(result)
        try:
            input("press enter to continue")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0


def print_plain_list(
    states: dict[str, SkillState], dest_dir: Path, stdout: TextIO | None = None
) -> None:
    """Print a plain text list suitable for non-interactive output."""
    out = stdout or sys.stdout
    print(f"Antigravity skills directory: {dest_dir}", file=out)
    print(f"Summary: {format_status_summary(states)}", file=out)
    for state in states.values():
        print(f"{state.status:8} {state.name} - {state.detail}", file=out)


def print_cli_summary(
    result: OperationResult,
    dest_dir: Path,
    *,
    dry_run: bool,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> None:
    """Print a CLI summary and reload/conflict hints after applying an action."""
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    print_operation_result(result, stdout=out, stderr=err)
    print("", file=out)
    print(f"Antigravity skills directory: {dest_dir}", file=out)
    print(
        f"Changed: {len(result.changed)}, unchanged: {len(result.unchanged)}, "
        f"errors: {len(result.errors)}",
        file=out,
    )

    if result.ok and not dry_run and result.changed:
        print(
            "Antigravity reads skills before each turn. In Antigravity CLI, run /skills reload "
            "(or start a new conversation) to refresh slash commands.",
            file=out,
        )

    if any(
        "symlink points to" in err_msg or "not a symlink" in err_msg for err_msg in result.errors
    ):
        print("Resolve conflicts or rerun with --force to replace symlinks only.", file=err)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Install and manage this repository's plugin skills for Antigravity "
            "(App, CLI, and IDE) via symlinks."
        )
    )
    parser.add_argument(
        "skills",
        nargs="*",
        metavar="SKILL",
        help="skill names to install (or 'all'); omit to install all marketplace skills",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=None,
        help="Antigravity skills directory (default: ~/.gemini/config/skills)",
    )
    parser.add_argument(
        "-w",
        "--workspace",
        type=Path,
        default=None,
        help="project workspace root (installs into <workspace>/.agents/skills)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=default_repo_root(),
        help="repository root containing plugins/ (mostly useful for tests)",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="list skill states and exit",
    )
    parser.add_argument(
        "--enable",
        nargs="+",
        metavar="SKILL",
        help="enable named skills (or 'all') and exit",
    )
    parser.add_argument(
        "--disable",
        nargs="+",
        metavar="SKILL",
        help="disable managed marketplace skills (or 'all') and exit",
    )
    parser.add_argument(
        "--uninstall",
        nargs="+",
        metavar="SKILL",
        help="uninstall symlinked skills (or 'all') and exit",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="open the interactive Antigravity skills manager",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="preview changes without modifying files",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="replace conflicting symlinks that point elsewhere",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.dest is not None and args.workspace is not None:
        print("error: choose only one of --dest or --workspace", file=sys.stderr)
        return 2

    explicit_modes = [
        flag
        for flag, active in [
            ("--list", bool(args.list)),
            ("--enable", bool(args.enable)),
            ("--disable", bool(args.disable)),
            ("--uninstall", bool(args.uninstall)),
            ("--interactive", bool(args.interactive)),
        ]
        if active
    ]
    if len(explicit_modes) > 1:
        print(
            "error: choose only one of --list, --enable, --disable, --uninstall, or --interactive",
            file=sys.stderr,
        )
        return 2

    if args.skills and explicit_modes:
        print(
            "error: positional skill names cannot be combined with "
            "--list, --enable, --disable, --uninstall, or --interactive",
            file=sys.stderr,
        )
        return 2

    if args.dry_run and (args.interactive or args.list):
        print("error: --dry-run cannot be used with --interactive or --list", file=sys.stderr)
        return 2

    try:
        resolved_dest, states = load_skill_states(
            args.repo_root, dest_dir=args.dest, workspace=args.workspace
        )
    except InstallerError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.list:
        print_plain_list(states, resolved_dest)
        return 0

    if args.interactive:
        try:
            return run_interactive(
                args.repo_root, dest_dir=args.dest, workspace=args.workspace, force=args.force
            )
        except InstallerError as error:
            print(f"error: {error}", file=sys.stderr)
            return 1

    action: Action
    requested_names: Sequence[str]
    if args.enable:
        action = "enable"
        requested_names = args.enable
    elif args.disable:
        action = "disable"
        requested_names = args.disable
    elif args.uninstall:
        action = "uninstall"
        requested_names = args.uninstall
    elif args.skills:
        action = "enable"
        requested_names = args.skills
    else:
        action = "enable"
        requested_names = ["all"]

    result = apply_action(states, action, requested_names, force=args.force, dry_run=args.dry_run)
    print_cli_summary(result, resolved_dest, dry_run=args.dry_run)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
