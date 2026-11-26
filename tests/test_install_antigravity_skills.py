"""Tests for the Antigravity skills installer and manager."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.install_antigravity_skills import (
    InstallerError,
    apply_action,
    default_repo_root,
    discover_skill_dirs,
    filter_states,
    load_skill_states,
    main,
    names_from_tokens,
    run_interactive,
)


def create_nested_skill(repo_root: Path, plugin_name: str, skill_name: str | None = None) -> Path:
    """Create a nested plugin skill fixture under plugins/<plugin>/skills/<skill>/."""
    skill_name = skill_name or plugin_name
    skill_dir = repo_root / "plugins" / plugin_name / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {skill_name}\ndescription: Test skill {skill_name}\n---\n\n# {skill_name}\n",
        encoding="utf-8",
    )
    return skill_dir


def create_flat_skill(repo_root: Path, name: str) -> Path:
    """Create a legacy flat skill fixture under plugins/<name>/."""
    skill_dir = repo_root / "plugins" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Test skill {name}\n---\n\n# {name}\n",
        encoding="utf-8",
    )
    return skill_dir


def test_discover_skill_dirs_handles_nested_and_flat_and_skips_mcp_only(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    nested = create_nested_skill(repo_root, "alpha")
    flat = create_flat_skill(repo_root, "beta")
    mcp_only = repo_root / "plugins" / "sequential-thinking"
    mcp_only.mkdir(parents=True)
    (mcp_only / ".mcp.json").write_text("{}", encoding="utf-8")

    discovered = discover_skill_dirs(repo_root / "plugins")

    assert discovered == [nested, flat]


def test_discover_skill_dirs_rejects_duplicate_names_and_empty_or_missing_plugins(
    tmp_path: Path,
) -> None:
    missing_repo = tmp_path / "missing"
    with pytest.raises(InstallerError, match="plugins directory not found"):
        discover_skill_dirs(missing_repo / "plugins")

    empty_repo = tmp_path / "empty"
    (empty_repo / "plugins").mkdir(parents=True)
    with pytest.raises(InstallerError, match="no plugin skills found"):
        discover_skill_dirs(empty_repo / "plugins")

    dup_repo = tmp_path / "dup"
    create_nested_skill(dup_repo, "plugin-one", "shared")
    create_nested_skill(dup_repo, "plugin-two", "shared")
    with pytest.raises(InstallerError, match="duplicate skill name 'shared'"):
        discover_skill_dirs(dup_repo / "plugins")


def test_discover_skill_dirs_on_real_repository() -> None:
    repo_root = default_repo_root()
    discovered = discover_skill_dirs(repo_root / "plugins")
    names = {path.name for path in discovered}

    assert {"statechart", "tmux", "git"}.issubset(names)
    assert names.isdisjoint({"sequential-thinking", "file-search", "fuzzy-search", "sqlite"})
    assert all((path / "SKILL.md").is_file() for path in discovered)


def test_default_dest_uses_home_gemini_config_skills_and_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo_root = tmp_path / "repo"
    alpha = create_nested_skill(repo_root, "alpha")
    beta = create_nested_skill(repo_root, "beta")
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))

    first_exit = main(["--repo-root", str(repo_root)])
    first_out = capsys.readouterr()
    dest_dir = home_dir / ".gemini" / "config" / "skills"

    assert first_exit == 0
    assert os.readlink(dest_dir / "alpha") == str(alpha.resolve())
    assert os.readlink(dest_dir / "beta") == str(beta.resolve())
    assert (dest_dir / "alpha" / "SKILL.md").is_file()
    assert "/skills reload" in first_out.out

    second_exit = main(["--repo-root", str(repo_root)])
    second_out = capsys.readouterr()
    assert second_exit == 0
    assert "Changed: 0, unchanged: 2, errors: 0" in second_out.out
    assert "/skills reload" not in second_out.out


def test_workspace_dest_and_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo_root = tmp_path / "repo"
    alpha = create_nested_skill(repo_root, "alpha")
    workspace = tmp_path / "project"
    workspace.mkdir()

    exit_code = main(["--repo-root", str(repo_root), "--workspace", str(workspace)])
    capsys.readouterr()
    assert exit_code == 0
    assert os.readlink(workspace / ".agents" / "skills" / "alpha") == str(alpha.resolve())

    missing_ws = tmp_path / "does-not-exist"
    missing_exit = main(["--repo-root", str(repo_root), "--workspace", str(missing_ws)])
    missing_err = capsys.readouterr().err
    assert missing_exit == 1
    assert "workspace directory not found" in missing_err

    file_ws = tmp_path / "file.txt"
    file_ws.write_text("hi", encoding="utf-8")
    file_exit = main(["--repo-root", str(repo_root), "--workspace", str(file_ws)])
    file_err = capsys.readouterr().err
    assert file_exit == 1
    assert "workspace directory not found" in file_err

    both_exit = main(
        [
            "--repo-root",
            str(repo_root),
            "--dest",
            str(tmp_path / "d"),
            "--workspace",
            str(workspace),
        ]
    )
    both_err = capsys.readouterr().err
    assert both_exit == 2
    assert "choose only one of --dest or --workspace" in both_err


def test_custom_dest_expands_home_and_supports_relative_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    alpha = create_nested_skill(repo_root, "alpha")
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.chdir(tmp_path)

    exit_tilde = main(["--repo-root", str(repo_root), "--dest", "~/custom-skills"])
    assert exit_tilde == 0
    assert os.readlink(home_dir / "custom-skills" / "alpha") == str(alpha.resolve())

    exit_rel = main(["--repo-root", str(repo_root), "--dest", "rel-skills"])
    assert exit_rel == 0
    assert os.readlink(tmp_path / "rel-skills" / "alpha") == str(alpha.resolve())


def test_positional_subset_and_deduplication(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo_root = tmp_path / "repo"
    alpha = create_nested_skill(repo_root, "alpha")
    create_nested_skill(repo_root, "beta")
    dest_dir = tmp_path / "skills"

    exit_code = main(["--repo-root", str(repo_root), "--dest", str(dest_dir), "alpha", "alpha"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert os.readlink(dest_dir / "alpha") == str(alpha.resolve())
    assert not (dest_dir / "beta").exists()
    assert "Changed: 1, unchanged: 0, errors: 0" in out


def test_dry_run_does_not_create_directory_or_links(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo_root = tmp_path / "repo"
    create_nested_skill(repo_root, "alpha")
    dest_dir = tmp_path / "nonexistent-skills"

    exit_code = main(["--repo-root", str(repo_root), "--dest", str(dest_dir), "--dry-run"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "alpha: would enable ->" in out
    assert not dest_dir.exists()


def test_conflicts_real_dir_and_force_symlink_replacement(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo_root = tmp_path / "repo"
    alpha = create_nested_skill(repo_root, "alpha")
    beta = create_nested_skill(repo_root, "beta")
    gamma = create_nested_skill(repo_root, "gamma")
    dest_dir = tmp_path / "skills"
    dest_dir.mkdir()

    real_dir = dest_dir / "alpha"
    real_dir.mkdir()
    (real_dir / "SKILL.md").write_text("custom", encoding="utf-8")

    wrong_target = tmp_path / "elsewhere"
    wrong_target.mkdir()
    (dest_dir / "beta").symlink_to(wrong_target, target_is_directory=True)
    (dest_dir / "gamma").symlink_to(tmp_path / "broken-target", target_is_directory=True)

    # Real directory fails even with --force
    alpha_exit = main(["--repo-root", str(repo_root), "--dest", str(dest_dir), "--force", "alpha"])
    alpha_err = capsys.readouterr().err
    assert alpha_exit == 1
    assert "path exists and is not a symlink" in alpha_err
    assert real_dir.is_dir() and not real_dir.is_symlink()

    # Conflicting and broken symlinks fail without --force
    beta_exit = main(["--repo-root", str(repo_root), "--dest", str(dest_dir), "beta", "gamma"])
    beta_err = capsys.readouterr().err
    assert beta_exit == 1
    assert "symlink points to" in beta_err
    assert "rerun with --force" in beta_err

    # Conflicting and broken symlinks are replaced with --force
    force_exit = main(
        ["--repo-root", str(repo_root), "--dest", str(dest_dir), "--force", "beta", "gamma"]
    )
    capsys.readouterr()
    assert force_exit == 0
    assert os.readlink(dest_dir / "beta") == str(beta.resolve())
    assert os.readlink(dest_dir / "gamma") == str(gamma.resolve())
    assert not (dest_dir / "alpha").is_symlink()
    assert os.readlink(dest_dir / "beta") != str(alpha.resolve())


def test_unknown_skill_suggests_close_match(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo_root = tmp_path / "repo"
    create_nested_skill(repo_root, "statechart")
    dest_dir = tmp_path / "skills"

    exit_code = main(["--repo-root", str(repo_root), "--dest", str(dest_dir), "statechar"])
    err = capsys.readouterr().err

    assert exit_code == 1
    assert "unknown skill: statechar (did you mean: statechart)" in err


def test_list_reports_all_statuses_and_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo_root = tmp_path / "repo"
    alpha = create_nested_skill(repo_root, "alpha")
    create_nested_skill(repo_root, "beta")
    create_nested_skill(repo_root, "gamma")
    dest_dir = tmp_path / "skills"
    dest_dir.mkdir()

    (dest_dir / "alpha").symlink_to(alpha.resolve(), target_is_directory=True)
    (dest_dir / "gamma").symlink_to(tmp_path / "other", target_is_directory=True)
    (dest_dir / "ext-link").symlink_to(tmp_path / "ext", target_is_directory=True)
    ext_dir = dest_dir / "ext-dir"
    ext_dir.mkdir()
    (ext_dir / "SKILL.md").write_text("---\nname: ext-dir\ndescription: x\n---\n", encoding="utf-8")
    (dest_dir / "notes.txt").write_text("stray", encoding="utf-8")

    exit_code = main(["--repo-root", str(repo_root), "--dest", str(dest_dir), "--list"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "Summary: enabled: 1, disabled: 1, conflict: 1, external: 2, invalid: 1" in out
    assert "enabled  alpha" in out
    assert "disabled beta" in out
    assert "conflict gamma" in out
    assert "external ext-link" in out
    assert "external ext-dir" in out
    assert "invalid  notes.txt" in out


def test_disable_and_uninstall_behavior(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo_root = tmp_path / "repo"
    alpha = create_nested_skill(repo_root, "alpha")
    create_nested_skill(repo_root, "beta")
    create_nested_skill(repo_root, "gamma")
    dest_dir = tmp_path / "skills"
    dest_dir.mkdir()

    (dest_dir / "alpha").symlink_to(alpha.resolve(), target_is_directory=True)
    (dest_dir / "gamma").symlink_to(tmp_path / "wrong", target_is_directory=True)
    (dest_dir / "ext-link").symlink_to(tmp_path / "ext", target_is_directory=True)
    real_dir = dest_dir / "copied"
    real_dir.mkdir()
    (real_dir / "SKILL.md").write_text("---\nname: copied\ndescription: x\n---\n", encoding="utf-8")

    # Disable dry-run preserves symlink
    dry_disable = main(
        ["--repo-root", str(repo_root), "--dest", str(dest_dir), "--dry-run", "--disable", "alpha"]
    )
    assert dry_disable == 0
    assert (dest_dir / "alpha").is_symlink()
    capsys.readouterr()

    # Disable refuses external and conflict, keeps disabled unchanged
    _, states = load_skill_states(repo_root, dest_dir=dest_dir)
    refused_ext = apply_action(states, "disable", ["ext-link"])
    assert not refused_ext.ok
    assert "disable refused for external" in refused_ext.errors[0]

    refused_conf = apply_action(states, "disable", ["gamma"])
    assert not refused_conf.ok
    assert "disable refused for conflict" in refused_conf.errors[0]

    unchanged_beta = apply_action(states, "disable", ["beta"])
    assert unchanged_beta.ok
    assert unchanged_beta.unchanged == ["beta: already disabled"]

    # Disable all disables alpha without failing on gamma conflict or beta disabled
    all_disable = main(["--repo-root", str(repo_root), "--dest", str(dest_dir), "--disable", "all"])
    all_disable_caps = capsys.readouterr()
    assert all_disable == 1  # gamma is a conflict
    assert not (dest_dir / "alpha").is_symlink()
    assert "alpha: disabled" in all_disable_caps.out
    assert "gamma: disable refused for conflict" in all_disable_caps.err

    # Re-enable alpha, test uninstall dry-run and real uninstall
    main(["--repo-root", str(repo_root), "--dest", str(dest_dir), "alpha"])
    capsys.readouterr()

    dry_uninstall = main(
        [
            "--repo-root",
            str(repo_root),
            "--dest",
            str(dest_dir),
            "--dry-run",
            "--uninstall",
            "all",
        ]
    )
    assert dry_uninstall == 0
    assert (dest_dir / "alpha").is_symlink()
    capsys.readouterr()

    # Uninstall refuses real directory
    real_uninstall = main(
        ["--repo-root", str(repo_root), "--dest", str(dest_dir), "--uninstall", "copied"]
    )
    assert real_uninstall == 1
    assert "not a symlink" in capsys.readouterr().err
    assert real_dir.is_dir()

    # Uninstall all removes all symlinks (alpha, gamma, ext-link)
    all_uninstall = main(
        ["--repo-root", str(repo_root), "--dest", str(dest_dir), "--uninstall", "all"]
    )
    assert all_uninstall == 0
    assert not (dest_dir / "alpha").is_symlink()
    assert not (dest_dir / "gamma").is_symlink()
    assert not (dest_dir / "ext-link").is_symlink()
    capsys.readouterr()

    # Uninstall all when 0 symlinks exist succeeds cleanly
    empty_uninstall = main(
        ["--repo-root", str(repo_root), "--dest", str(dest_dir), "--uninstall", "all"]
    )
    assert empty_uninstall == 0
    assert "no symlinked skills installed" in capsys.readouterr().out


def test_cli_validation_rejects_incompatible_flags(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo_root = tmp_path / "repo"
    create_nested_skill(repo_root, "alpha")
    dest_dir = tmp_path / "skills"

    for argv in [
        [
            "--repo-root",
            str(repo_root),
            "--dest",
            str(dest_dir),
            "--enable",
            "alpha",
            "--disable",
            "alpha",
        ],
        ["--repo-root", str(repo_root), "--dest", str(dest_dir), "--list", "--interactive"],
        ["--repo-root", str(repo_root), "--dest", str(dest_dir), "alpha", "--disable", "alpha"],
        ["--repo-root", str(repo_root), "--dest", str(dest_dir), "--list", "alpha"],
        ["--repo-root", str(repo_root), "--dest", str(dest_dir), "--interactive", "alpha"],
        ["--repo-root", str(repo_root), "--dest", str(dest_dir), "--dry-run", "--interactive"],
        ["--repo-root", str(repo_root), "--dest", str(dest_dir), "--dry-run", "--list"],
    ]:
        exit_code = main(argv)
        err = capsys.readouterr().err
        assert exit_code == 2
        assert err.startswith("error:")


def test_interactive_helpers_and_exit_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    alpha = create_nested_skill(repo_root, "alpha")
    create_nested_skill(repo_root, "beta-tool")
    dest_dir = tmp_path / "skills"
    dest_dir.mkdir()
    (dest_dir / "alpha").symlink_to(alpha.resolve(), target_is_directory=True)

    _, states = load_skill_states(repo_root, dest_dir=dest_dir)
    filtered = filter_states(states, "BETA")
    assert [state.name for state in filtered] == ["beta-tool"]
    assert [state.name for state in filter_states(states, "")] == ["alpha", "beta-tool"]

    assert names_from_tokens(filtered, states, ["1"]) == ["beta-tool"]
    assert names_from_tokens(filtered, states, ["all"]) == ["alpha", "beta-tool"]
    assert names_from_tokens(filtered, states, ["all"], symlink_all=True) == ["alpha"]

    with pytest.raises(ValueError, match="invalid selection number"):
        names_from_tokens(filtered, states, ["2"])

    commands = iter(["f beta", "e 1", "", "q"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(commands))
    assert run_interactive(repo_root, dest_dir=dest_dir) == 0
    assert (dest_dir / "beta-tool").is_symlink()

    def raise_eof(_prompt: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    assert run_interactive(repo_root, dest_dir=dest_dir) == 0
