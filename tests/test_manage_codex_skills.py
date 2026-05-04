"""Tests for the interactive Codex skills manager."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.manage_codex_skills import (
    apply_action,
    load_skill_states,
    main,
    names_from_tokens,
)


def create_skill(repo_root: Path, name: str) -> Path:
    """Create a minimal plugin skill fixture."""
    skill_dir = repo_root / "plugins" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Test skill {name}\n---\n\n# {name}\n",
        encoding="utf-8",
    )
    return skill_dir


def test_load_states_tracks_disabled_enabled_and_external(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")
    create_skill(repo_root, "beta")
    dest_dir = repo_root / ".agents" / "skills"
    dest_dir.mkdir(parents=True)
    (dest_dir / "alpha").symlink_to("../../plugins/alpha", target_is_directory=True)
    (dest_dir / "external").symlink_to("/tmp/external-skill", target_is_directory=True)

    states = load_skill_states(repo_root)

    assert states["alpha"].status == "enabled"
    assert states["beta"].status == "disabled"
    assert states["external"].status == "external"


def test_enable_disable_and_uninstall_managed_skill(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")

    states = load_skill_states(repo_root)
    enable_result = apply_action(states, "enable", ["alpha"])
    assert enable_result.ok
    assert os.readlink(repo_root / ".agents" / "skills" / "alpha") == "../../plugins/alpha"

    states = load_skill_states(repo_root)
    disable_result = apply_action(states, "disable", ["alpha"])
    assert disable_result.ok
    assert not (repo_root / ".agents" / "skills" / "alpha").exists()

    states = load_skill_states(repo_root)
    apply_action(states, "enable", ["alpha"])
    states = load_skill_states(repo_root)
    uninstall_result = apply_action(states, "uninstall", ["alpha"])
    assert uninstall_result.ok
    assert not (repo_root / ".agents" / "skills" / "alpha").exists()


def test_disable_refuses_external_symlink(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")
    dest_dir = repo_root / ".agents" / "skills"
    dest_dir.mkdir(parents=True)
    (dest_dir / "external").symlink_to("/tmp/external-skill", target_is_directory=True)

    states = load_skill_states(repo_root)
    result = apply_action(states, "disable", ["external"])

    assert not result.ok
    assert "disable refused" in result.errors[0]
    assert (dest_dir / "external").is_symlink()


def test_uninstall_removes_external_symlink(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")
    dest_dir = repo_root / ".agents" / "skills"
    dest_dir.mkdir(parents=True)
    external = dest_dir / "external"
    external.symlink_to("/tmp/external-skill", target_is_directory=True)

    states = load_skill_states(repo_root)
    result = apply_action(states, "uninstall", ["external"])

    assert result.ok
    assert not external.exists()
    assert not external.is_symlink()


def test_uninstall_refuses_real_directory(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")
    real_dir = repo_root / ".agents" / "skills" / "copied"
    real_dir.mkdir(parents=True)
    (real_dir / "SKILL.md").write_text("---\nname: copied\ndescription: copied\n---\n")

    states = load_skill_states(repo_root)
    result = apply_action(states, "uninstall", ["copied"])

    assert not result.ok
    assert "not a symlink" in result.errors[0]
    assert real_dir.is_dir()


def test_conflicting_symlink_requires_force_to_enable(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")
    target = repo_root / ".agents" / "skills" / "alpha"
    target.parent.mkdir(parents=True)
    target.symlink_to("/tmp/old-alpha", target_is_directory=True)

    states = load_skill_states(repo_root)
    refused = apply_action(states, "enable", ["alpha"])
    assert not refused.ok
    assert os.readlink(target) == "/tmp/old-alpha"

    states = load_skill_states(repo_root)
    forced = apply_action(states, "enable", ["alpha"], force=True)
    assert forced.ok
    assert os.readlink(target) == "../../plugins/alpha"


def test_names_from_tokens_supports_indexes_and_all(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")
    create_skill(repo_root, "beta")
    states = load_skill_states(repo_root)

    assert names_from_tokens(states, ["1"]) == ["alpha"]
    assert names_from_tokens(states, ["all"]) == ["alpha", "beta"]

    with pytest.raises(ValueError, match="invalid selection number"):
        names_from_tokens(states, ["3"])


def test_cli_list_and_enable(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")

    list_exit = main(["--repo-root", str(repo_root), "--list"])
    list_output = capsys.readouterr()
    assert list_exit == 0
    assert "disabled alpha" in list_output.out

    enable_exit = main(["--repo-root", str(repo_root), "--enable", "alpha"])
    enable_output = capsys.readouterr()
    assert enable_exit == 0
    assert "alpha: enabled" in enable_output.out
    assert os.readlink(repo_root / ".agents" / "skills" / "alpha") == "../../plugins/alpha"


def test_cli_rejects_multiple_actions(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo_root = tmp_path / "repo"
    create_skill(repo_root, "alpha")

    exit_code = main(["--repo-root", str(repo_root), "--enable", "alpha", "--disable", "alpha"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "choose only one" in captured.err
