#!/usr/bin/env python3
# /// script
# # github-slugger 0.0.3 has a docstring with lone surrogates, which 3.13+ cannot compile.
# requires-python = ">=3.10,<3.13"
# dependencies = ["markdown-it-py==4.0.0", "github-slugger==0.0.3"]
# ///
"""Analyze engineering Markdown or compare revisions; never edit or autoaccept.

uv run --no-config --no-project doc_quality.py analyze design.md --check-links
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from doc_links import check_links
from doc_metrics import analyze_document, compare_documents

MAX_FILE_BYTES = 1_000_000


class ReviewError(Exception):
    """Input could not be read or the options are inconsistent."""


def read_text(path: Path) -> str:
    try:
        with path.open("rb") as stream:
            content = stream.read(MAX_FILE_BYTES + 1)
        if len(content) > MAX_FILE_BYTES:
            raise ReviewError("Input exceeds 1,000,000 bytes; select a bounded document excerpt.")
        return content.decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise ReviewError("Could not read the selected UTF-8 input.") from error


def link_review(text: str, path: Path, args: argparse.Namespace) -> dict[str, Any]:
    if not args.check_links:
        return {"status": "not_run", "reason": "Enable --check-links for local files and anchors."}
    logical_path = args.document_path or path
    root = args.link_root or logical_path.absolute().parent
    return check_links(text, logical_path, root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("analyze", "compare"):
        command = commands.add_parser(name)
        if name == "analyze":
            command.add_argument("path", type=Path)
        else:
            command.add_argument("original", type=Path)
            command.add_argument("revised", type=Path)
        command.add_argument("--check-links", action="store_true")
        command.add_argument("--link-root", type=Path)
        command.add_argument("--document-path", type=Path)
    args = parser.parse_args(argv)
    metadata: dict[str, Any] = {"schema_version": 2, "advisory": True}
    try:
        if not args.check_links and (args.link_root is not None or args.document_path is not None):
            raise ReviewError("--link-root and --document-path require --check-links.")
        if args.command == "analyze":
            text = read_text(args.path)
            links = link_review(text, args.path, args)
            report: dict[str, Any] = {"analysis": analyze_document(text), "link_validation": links}
        else:
            original, revised = read_text(args.original), read_text(args.revised)
            before_links = link_review(original, args.revised, args)
            # Historical failures remain visible; only revised failures affect the exit code.
            links = link_review(revised, args.revised, args)
            report = {
                "before": analyze_document(original),
                "after": analyze_document(revised),
                "preservation": compare_documents(original, revised),
                "acceptance": "requires_evidence_review",
                "link_validation": {
                    "status": links["status"],
                    "before": before_links,
                    "after": links,
                },
            }
        print(
            json.dumps(
                {**metadata, "status": "analyzed", **report},
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            )
        )
        return 1 if links["status"] == "failed" else 0
    except (ReviewError, OSError, ValueError) as error:
        message = (
            str(error) if isinstance(error, ReviewError) else "Could not prepare document review."
        )
        print(json.dumps({**metadata, "status": "incomplete", "error": message}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
