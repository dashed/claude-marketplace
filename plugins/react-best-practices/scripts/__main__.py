"""CLI entry point: python -m scripts build|validate|extract-tests."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="scripts",
        description="Build tools for React Best Practices skill",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # build subcommand
    build_parser = subparsers.add_parser("build", help="Build AGENTS.md from rules")
    build_parser.add_argument(
        "--skill",
        type=str,
        default=None,
        help="Skill name to build (default: react-best-practices)",
    )
    build_parser.add_argument(
        "--all",
        action="store_true",
        dest="build_all",
        help="Build all skills",
    )
    build_parser.add_argument(
        "--upgrade-version",
        action="store_true",
        help="Increment the version in metadata.json",
    )

    # validate subcommand
    subparsers.add_parser("validate", help="Validate rule files")

    # extract-tests subcommand
    subparsers.add_parser("extract-tests", help="Extract test cases from rules")

    args = parser.parse_args()

    if args.command == "build":
        from .build import build

        build(
            skill_name=args.skill,
            build_all=args.build_all,
            upgrade_version=args.upgrade_version,
        )
    elif args.command == "validate":
        from .validate import validate

        validate()
    elif args.command == "extract-tests":
        from .extract_tests import extract_tests

        extract_tests()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
