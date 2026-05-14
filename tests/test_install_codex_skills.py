"""Tests for the Codex skills installer."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.install_codex_skills import install_codex_skills, main


def create_skill(repo_root: Path, name: str) -> Path:
    """Create a minimal plugin skill fixture."""
    skill_dir = repo_root / "plugins" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Test skill {name}\n---\n\n# {name}\n",
        encoding="utf-8",
    )
    return skill_dir


def test_installs_repo_local_relative_symlinks(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")
    create_skill(repo_root, "beta")
    (repo_root / "plugins" / "not-a-skill").mkdir()

    summary = install_codex_skills(repo_root)

    dest_dir = repo_root / ".agents" / "skills"
    assert summary.linked == 2
    assert summary.unchanged == 0
    assert summary.conflicts == []
    assert os.readlink(dest_dir / "alpha") == str((repo_root / "plugins" / "alpha").resolve())
    assert os.readlink(dest_dir / "beta") == str((repo_root / "plugins" / "beta").resolve())
    assert (dest_dir / "alpha" / "SKILL.md").is_file()
    assert not (dest_dir / "not-a-skill").exists()


def test_install_is_idempotent(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")

    install_codex_skills(repo_root)
    summary = install_codex_skills(repo_root)

    assert summary.linked == 0
    assert summary.unchanged == 1
    assert summary.conflicts == []


def test_dry_run_does_not_create_links_or_directories(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")

    summary = install_codex_skills(repo_root, dry_run=True)

    assert summary.linked == 1
    assert summary.unchanged == 0
    assert summary.conflicts == []
    assert not (repo_root / ".agents").exists()


def test_custom_dest_uses_absolute_symlinks(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    skill_dir = create_skill(repo_root, "alpha")
    dest_dir = tmp_path / "codex-skills"

    summary = install_codex_skills(repo_root, dest_dir=dest_dir)

    assert summary.linked == 1
    assert summary.conflicts == []
    assert os.readlink(dest_dir / "alpha") == str(skill_dir.resolve())


def test_custom_dest_expands_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    skill_dir = create_skill(repo_root, "alpha")
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))

    summary = install_codex_skills(repo_root, dest_dir=Path("~/codex-skills"))

    assert summary.dest_dir == home_dir / "codex-skills"
    assert os.readlink(summary.dest_dir / "alpha") == str(skill_dir.resolve())


def test_existing_directory_is_conflict(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")
    existing_dir = repo_root / ".agents" / "skills" / "alpha"
    existing_dir.mkdir(parents=True)

    summary = install_codex_skills(repo_root)

    assert summary.linked == 0
    assert summary.unchanged == 0
    assert len(summary.conflicts) == 1
    assert "already exists and is not a symlink" in summary.conflicts[0]
    assert existing_dir.is_dir()


def test_force_replaces_symlink_only(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")
    target = repo_root / ".agents" / "skills" / "alpha"
    target.parent.mkdir(parents=True)
    target.symlink_to("/tmp/old-alpha", target_is_directory=True)

    summary = install_codex_skills(repo_root, force=True)

    assert summary.linked == 1
    assert summary.conflicts == []
    assert os.readlink(target) == str((repo_root / "plugins" / "alpha").resolve())


def test_cli_supports_dry_run_without_mutating_repo(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")

    exit_code = main(["--repo-root", str(repo_root), "--dry-run"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Would link:" in captured.out
    assert "conflict:" not in captured.err
    assert not (repo_root / ".agents").exists()
