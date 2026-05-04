#!/usr/bin/env python3
"""Interactive manager for Codex skills exposed by this repository."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.install_codex_skills import (
    InstallerError,
    default_repo_root,
    discover_skill_dirs,
    link_target_for,
    normalize_dest_dir,
)

SkillStatus = Literal["enabled", "disabled", "conflict", "external", "invalid"]
Action = Literal["enable", "disable", "uninstall"]


@dataclass(frozen=True)
class SkillState:
    """Current state of one Codex skill entry."""

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


def load_skill_states(repo_root: Path, dest_dir: Path | None = None) -> dict[str, SkillState]:
    """Load repo plugin skills plus existing entries in a Codex skills directory."""
    repo_root = repo_root.expanduser().resolve()
    plugins_dir = repo_root / "plugins"
    if not plugins_dir.is_dir():
        raise InstallerError(f"plugins directory not found: {plugins_dir}")

    dest_dir = normalize_dest_dir(dest_dir or Path(".agents/skills"), repo_root)
    states: dict[str, SkillState] = {}

    for source_dir in discover_skill_dirs(plugins_dir):
        name = source_dir.name
        target_path = dest_dir / name
        expected_link_target = link_target_for(source_dir, dest_dir, repo_root)
        status: SkillStatus = "disabled"
        detail = "not linked"

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

    if dest_dir.exists():
        for target_path in sorted(dest_dir.iterdir()):
            name = target_path.name
            if name in states:
                continue

            if target_path.is_symlink():
                detail = os.readlink(target_path)
                status: SkillStatus = "external"
            elif target_path.is_dir() and (target_path / "SKILL.md").is_file():
                detail = "directory skill outside plugins"
                status = "external"
            else:
                detail = "not a symlink or skill directory"
                status = "invalid"

            states[name] = SkillState(
                name=name,
                status=status,
                source_dir=None,
                target_path=target_path,
                expected_link_target=None,
                detail=detail,
            )

    return dict(sorted(states.items()))


def enable_skill(state: SkillState, *, force: bool = False) -> OperationResult:
    """Enable one repo-backed skill by creating its Codex symlink."""
    if state.source_dir is None or state.expected_link_target is None:
        return OperationResult([], [], [f"{state.name}: cannot enable skills outside plugins"])
    if state.status == "enabled":
        return OperationResult([], [f"{state.name}: already enabled"], [])
    if state.status == "conflict" and not (force and state.target_path.is_symlink()):
        return OperationResult([], [], [f"{state.name}: {state.detail}"])
    if state.target_path.exists() and not state.target_path.is_symlink():
        return OperationResult([], [], [f"{state.name}: {state.detail}"])

    state.target_path.parent.mkdir(parents=True, exist_ok=True)
    if state.target_path.is_symlink():
        state.target_path.unlink()
    state.target_path.symlink_to(state.expected_link_target, target_is_directory=True)
    return OperationResult([f"{state.name}: enabled"], [], [])


def disable_skill(state: SkillState) -> OperationResult:
    """Disable one managed repo skill by removing its expected symlink."""
    if state.status == "disabled":
        return OperationResult([], [f"{state.name}: already disabled"], [])
    if state.status != "enabled":
        return OperationResult([], [], [f"{state.name}: disable refused for {state.status} entry"])
    if not state.target_path.is_symlink():
        return OperationResult([], [], [f"{state.name}: expected a symlink"])

    state.target_path.unlink()
    return OperationResult([f"{state.name}: disabled"], [], [])


def uninstall_skill(state: SkillState) -> OperationResult:
    """Remove one symlinked skill from the Codex skills directory."""
    if state.status == "disabled":
        return OperationResult([], [f"{state.name}: not installed"], [])
    if not state.target_path.is_symlink():
        return OperationResult(
            [],
            [],
            [f"{state.name}: uninstall refused because {state.target_path} is not a symlink"],
        )

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


def apply_action(
    states: dict[str, SkillState],
    action: Action,
    names: Sequence[str],
    *,
    force: bool = False,
) -> OperationResult:
    """Apply an action to named skills."""
    if not names:
        return OperationResult([], [], ["no skills selected"])

    missing = [name for name in names if name not in states]
    if missing:
        return OperationResult([], [], [f"unknown skill: {name}" for name in missing])

    results: list[OperationResult] = []
    for name in names:
        state = states[name]
        if action == "enable":
            results.append(enable_skill(state, force=force))
        elif action == "disable":
            results.append(disable_skill(state))
        else:
            results.append(uninstall_skill(state))
    return merge_results(results)


def all_repo_skill_names(states: dict[str, SkillState]) -> list[str]:
    """Return names backed by this repo's plugins directory."""
    return [name for name, state in states.items() if state.source_dir is not None]


def all_symlink_skill_names(states: dict[str, SkillState]) -> list[str]:
    """Return names currently installed as symlinks."""
    return [name for name, state in states.items() if state.target_path.is_symlink()]


def render_table(states: dict[str, SkillState], dest_dir: Path) -> None:
    """Render the current skill state table."""
    print(f"Codex Skills: {dest_dir}")
    print(f"{'#':>3}  {'Status':<9}  {'Skill':<28}  Detail")
    print("-" * 80)

    for index, state in enumerate(states.values(), start=1):
        print(f"{index:>3}  {state.status:<9}  {state.name:<28}  {state.detail}")

    print("\nCommands: e <skill|#|all>, d <skill|#|all>, u <skill|#|all>, r refresh, q quit")


def names_from_tokens(
    states: dict[str, SkillState], tokens: Sequence[str], *, symlink_all: bool = False
) -> list[str]:
    """Resolve command tokens to skill names."""
    if len(tokens) == 1 and tokens[0] == "all":
        return all_symlink_skill_names(states) if symlink_all else all_repo_skill_names(states)

    names_by_index = list(states)
    names: list[str] = []
    for token in tokens:
        if token.isdigit():
            index = int(token)
            if index < 1 or index > len(names_by_index):
                raise ValueError(f"invalid selection number: {token}")
            names.append(names_by_index[index - 1])
        else:
            names.append(token)
    return names


def print_operation_result(result: OperationResult) -> None:
    """Print operation output."""
    for message in result.changed:
        print(message)
    for message in result.unchanged:
        print(message)
    for message in result.errors:
        print(f"error: {message}", file=sys.stderr)


def run_interactive(repo_root: Path, dest_dir: Path, *, force: bool = False) -> int:
    """Run the interactive skills manager."""
    repo_root = repo_root.expanduser().resolve()
    dest_dir = normalize_dest_dir(dest_dir, repo_root)

    while True:
        states = load_skill_states(repo_root, dest_dir)
        print("\033[H\033[J", end="")
        render_table(states, dest_dir)
        raw_command = input("codex-skills> ").strip()
        if not raw_command:
            continue
        if raw_command in {"q", "quit", "exit"}:
            return 0
        if raw_command in {"r", "refresh"}:
            continue

        parts = raw_command.split()
        command = parts[0]
        tokens = parts[1:]
        action_by_command: dict[str, Action] = {
            "e": "enable",
            "enable": "enable",
            "d": "disable",
            "disable": "disable",
            "u": "uninstall",
            "uninstall": "uninstall",
        }
        action = action_by_command.get(command)
        if action is None:
            print("error: unknown command", file=sys.stderr)
            input("press enter to continue")
            continue

        try:
            names = names_from_tokens(states, tokens, symlink_all=action == "uninstall")
        except ValueError as error:
            print(f"error: {error}", file=sys.stderr)
            input("press enter to continue")
            continue

        result = apply_action(states, action, names, force=force)
        print_operation_result(result)
        input("press enter to continue")


def print_plain_list(states: dict[str, SkillState], dest_dir: Path) -> None:
    """Print a plain text list suitable for non-interactive output."""
    print(f"Codex skills directory: {dest_dir}")
    for state in states.values():
        print(f"{state.status:8} {state.name} - {state.detail}")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Interactively enable, disable, and uninstall Codex skills."
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path(".agents/skills"),
        help="Codex skills directory to manage, relative to the repo root by default",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=default_repo_root(),
        help="repository root to scan for plugin skills",
    )
    parser.add_argument("--list", action="store_true", help="list skill states and exit")
    parser.add_argument("--enable", nargs="+", metavar="SKILL", help="enable skill names and exit")
    parser.add_argument(
        "--disable", nargs="+", metavar="SKILL", help="disable skill names and exit"
    )
    parser.add_argument(
        "--uninstall", nargs="+", metavar="SKILL", help="uninstall skill names and exit"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="when enabling, replace conflicting symlinks that point elsewhere",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    dest_dir = normalize_dest_dir(args.dest, repo_root)

    selected_actions = [
        name
        for name, values in [
            ("enable", args.enable),
            ("disable", args.disable),
            ("uninstall", args.uninstall),
        ]
        if values
    ]
    if len(selected_actions) > 1:
        print("error: choose only one of --enable, --disable, or --uninstall", file=sys.stderr)
        return 2

    try:
        states = load_skill_states(repo_root, dest_dir)
    except InstallerError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.list:
        print_plain_list(states, dest_dir)
        return 0

    action: Action | None = None
    action_names: Sequence[str] | None = None
    if args.enable:
        action = "enable"
        action_names = args.enable
    elif args.disable:
        action = "disable"
        action_names = args.disable
    elif args.uninstall:
        action = "uninstall"
        action_names = args.uninstall

    if action_names:
        assert action is not None
        result = apply_action(states, action, action_names, force=args.force)
        print_operation_result(result)
        return 0 if result.ok else 1

    return run_interactive(repo_root, dest_dir, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
