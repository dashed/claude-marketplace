#!/usr/bin/env python3
"""Expose this repository's plugin skills to Codex."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence, TextIO


class InstallerError(RuntimeError):
    """Raised when the installer cannot proceed."""


@dataclass
class InstallSummary:
    """Result of a Codex skills install run."""

    dest_dir: Path
    linked: int = 0
    unchanged: int = 0
    conflicts: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


def default_repo_root() -> Path:
    """Return the repository root based on this script's location."""
    return Path(__file__).resolve().parent.parent


def discover_skill_dirs(plugins_dir: Path) -> list[Path]:
    """Return plugin directories that contain a SKILL.md file."""
    return sorted(
        path for path in plugins_dir.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()
    )


def normalize_dest_dir(dest_dir: Path, repo_root: Path) -> Path:
    """Resolve a destination directory relative to the repo root when needed."""
    dest_dir = dest_dir.expanduser()
    if dest_dir.is_absolute():
        return dest_dir
    return repo_root / dest_dir


def link_target_for(source_dir: Path, dest_dir: Path, repo_root: Path) -> str:
    """Return the symlink target string to use for a skill directory."""
    default_dest = repo_root / ".agents" / "skills"
    if dest_dir.resolve(strict=False) == default_dest.resolve(strict=False):
        return f"../../plugins/{source_dir.name}"
    return str(source_dir.resolve())


def install_codex_skills(
    repo_root: Path,
    dest_dir: Path | None = None,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> InstallSummary:
    """Link plugin skill directories into a Codex skills directory."""
    repo_root = repo_root.expanduser().resolve()
    plugins_dir = repo_root / "plugins"
    if not plugins_dir.is_dir():
        raise InstallerError(f"plugins directory not found: {plugins_dir}")

    dest_dir = normalize_dest_dir(dest_dir or Path(".agents/skills"), repo_root)
    skill_dirs = discover_skill_dirs(plugins_dir)
    if not skill_dirs:
        raise InstallerError(f"no plugin skills found in {plugins_dir}")

    summary = InstallSummary(dest_dir=dest_dir)

    if dry_run:
        summary.messages.append(f"Would create Codex skills directory: {dest_dir}")
    else:
        dest_dir.mkdir(parents=True, exist_ok=True)

    for source_dir in skill_dirs:
        target = dest_dir / source_dir.name
        link_target = link_target_for(source_dir, dest_dir, repo_root)

        if target.is_symlink():
            existing_target = os.readlink(target)
            if existing_target == link_target:
                summary.messages.append(f"Already linked: {target} -> {link_target}")
                summary.unchanged += 1
                continue

            if force:
                prefix = "Would replace" if dry_run else "Replacing"
                summary.messages.append(f"{prefix} symlink: {target} -> {link_target}")
                if not dry_run:
                    target.unlink()
                    target.symlink_to(link_target, target_is_directory=True)
                summary.linked += 1
                continue

            summary.conflicts.append(
                f"{target} is a symlink to {existing_target}, not {link_target}"
            )
            continue

        if target.exists():
            summary.conflicts.append(f"{target} already exists and is not a symlink")
            continue

        prefix = "Would link" if dry_run else "Linking"
        summary.messages.append(f"{prefix}: {target} -> {link_target}")
        if not dry_run:
            target.symlink_to(link_target, target_is_directory=True)
        summary.linked += 1

    return summary


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Expose this repository's plugin skills to Codex by linking plugin "
            "directories containing SKILL.md into a Codex skills directory."
        )
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path(".agents/skills"),
        help="skills directory to populate, relative to the repo root by default",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=default_repo_root(),
        help="repository root to scan for plugins (mostly useful for tests)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the links that would be created without changing files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace existing symlinks that point somewhere else",
    )
    return parser


def print_summary(summary: InstallSummary, stdout: TextIO, stderr: TextIO) -> None:
    """Print a human-readable install summary."""
    for message in summary.messages:
        print(message, file=stdout)

    for conflict in summary.conflicts:
        print(f"conflict: {conflict}", file=stderr)

    print("", file=stdout)
    print(f"Codex skills directory: {summary.dest_dir}", file=stdout)
    print(
        f"Linked: {summary.linked}, already linked: {summary.unchanged}, "
        f"conflicts: {len(summary.conflicts)}",
        file=stdout,
    )

    if summary.conflicts:
        print("Resolve conflicts or rerun with --force to replace symlinks only.", file=stderr)
    else:
        print(
            "Restart Codex or start a new thread from this repo root if the skills do not appear.",
            file=stdout,
        )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        summary = install_codex_skills(
            repo_root=args.repo_root,
            dest_dir=args.dest,
            dry_run=args.dry_run,
            force=args.force,
        )
    except InstallerError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print_summary(summary, sys.stdout, sys.stderr)
    return 1 if summary.conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
