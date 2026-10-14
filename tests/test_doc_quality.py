"""Verify read-only Markdown analysis, revision comparison, and link checks."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from packaging.specifiers import SpecifierSet

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "plugins/doc-quality/skills/doc-quality/scripts/doc_quality.py"
sys.path.insert(0, str(CLI.parent))
spec = importlib.util.spec_from_file_location("doc_quality", CLI)
assert spec and spec.loader
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
sys.path.pop(0)


def test_cli_reports_static_analysis_and_never_edits_input(tmp_path: Path) -> None:
    document = tmp_path / "doc.md"
    content = "# Plan\nThe owner MUST verify the migration.\n"
    document.write_text(content)
    result = subprocess.run(
        [sys.executable, str(CLI), "analyze", str(document)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    report = json.loads(result.stdout)
    assert report["status"] == "analyzed"
    assert report["analysis"]["metrics"]["word_count"] > 0
    assert report["link_validation"]["status"] == "not_run"
    assert document.read_text() == content


@pytest.mark.parametrize("content", [b"\xff", b"x" * 1_000_001], ids=["invalid_utf8", "oversized"])
def test_invalid_and_oversized_inputs_are_rejected(tmp_path: Path, content: bytes) -> None:
    path = tmp_path / "bad.md"
    path.write_bytes(content)
    with pytest.raises(review.ReviewError):
        review.read_text(path)


def test_comparison_reports_both_versions_without_accepting(tmp_path: Path, capsys: Any) -> None:
    original, revised = tmp_path / "before.md", tmp_path / "after.md"
    original.write_text("# Retry\nClients should retry at most twice.\n")
    revised.write_text("# Retry\nClients retry twice.\n")
    assert review.main(["compare", str(original), str(revised)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "analyzed"
    assert set(report) >= {"before", "after", "preservation"}
    assert report["acceptance"] == "requires_evidence_review"
    assert original.read_text() == "# Retry\nClients should retry at most twice.\n"


def test_local_link_failure_is_visible(tmp_path: Path, capsys: Any) -> None:
    document = tmp_path / "doc.md"
    document.write_text("# Plan\n[missing](missing.md)\n")
    assert review.main(["analyze", str(document), "--check-links"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "analyzed"
    assert report["link_validation"]["status"] == "failed"
    assert report["link_validation"]["counts"]["broken"] == 1


def test_comparison_checks_each_snapshot_at_same_logical_path(tmp_path: Path, capsys: Any) -> None:
    snapshots = tmp_path / "snapshots"
    snapshots.mkdir()
    original, revised = snapshots / "before.md", snapshots / "after.md"
    original.write_text("# Old name\n[section](#old-name)\n[guide](guide.md#intro)\n")
    revised.write_text("# New name\n[section](#old-name)\n[guide](guide.md#intro)\n")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Intro\nA guide.\n")
    # This path need not exist: self-links must use the supplied version's content.
    logical = docs / "design.md"
    assert (
        review.main(
            [
                "compare",
                str(original),
                str(revised),
                "--check-links",
                "--document-path",
                str(logical),
                "--link-root",
                str(docs),
            ]
        )
        == 1
    )
    report = json.loads(capsys.readouterr().out)
    links = report["link_validation"]
    assert links["before"]["status"] == "checked"
    assert links["after"]["counts"]["broken"] == 1
    assert links["after"]["status"] == "failed"
    assert report["acceptance"] == "requires_evidence_review"


def test_repaired_links_do_not_fail_due_to_historical_baseline(tmp_path: Path, capsys: Any) -> None:
    original, revised = tmp_path / "before.md", tmp_path / "after.md"
    original.write_text("# Plan\n[section](#missing)\n")
    revised.write_text("# Plan\n[section](#plan)\n")
    assert (
        review.main(
            [
                "compare",
                str(original),
                str(revised),
                "--check-links",
            ]
        )
        == 0
    )
    links = json.loads(capsys.readouterr().out)["link_validation"]
    assert links["before"]["status"] == "failed"
    assert links["after"]["status"] == "checked"


def test_link_configuration_requires_explicit_check(tmp_path: Path, capsys: Any) -> None:
    document = tmp_path / "doc.md"
    document.write_text("# Design\nText.\n")
    assert (
        review.main(
            [
                "analyze",
                str(document),
                "--link-root",
                str(tmp_path),
            ]
        )
        == 2
    )
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "incomplete"
    assert "require --check-links" in report["error"]


# Released CPython minors; add each new release so the newest admitted bound stays covered.
CPYTHON_MINORS = ("3.10", "3.11", "3.12", "3.13", "3.14")


def admitted_python_bounds() -> tuple[str, str]:
    header = re.search(r'^# requires-python = "([^"]+)"$', CLI.read_text(), re.MULTILINE)
    assert header
    admitted = [minor for minor in CPYTHON_MINORS if SpecifierSet(header[1]).contains(minor)]
    return admitted[0], admitted[-1]


@pytest.mark.parametrize("python", admitted_python_bounds())
def test_documented_uv_command_runs_on_admitted_python_bounds(tmp_path: Path, python: str) -> None:
    # The other tests import the script under the project's Python. Outside the repository,
    # uv may choose any admitted interpreter and installs the pinned dependencies there.
    document = tmp_path / "plan.md"
    document.write_text("# Plan\n\n## Rollout (v2)!\n\nSee [the rollout](#rollout-v2).\n")
    result = subprocess.run(
        [
            "uv",
            "run",
            "--no-config",
            "--no-project",
            "--python",
            python,
            str(CLI),
            "analyze",
            str(document),
            "--check-links",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    links = json.loads(result.stdout)["link_validation"]
    assert links["status"] == "checked"
    assert [link["reason"] for link in links["links"]] == ["anchor_exists"]
