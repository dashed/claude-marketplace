"""Tests for the statechart skill's command.

The corpus in tests/fixtures/statechart/corpus came with the skill from pstack
(cursor/plugins): each case has a spec, what TLC printed for each run when the corpus was
recorded, and the chart.mmd and report.md that the command must write. `runs.log` lists
the configs that the command gives TLC. The fixture `java` replays the recorded
output, so these tests need no TLC or Java. With TLA2TOOLS set to tla2tools.jar, the last
test runs real TLC on each spec.

The lifecycle tests replay the paths that TLC found in a model of the command
(notes/statechart/): the command killed at each point, Ctrl-C, and a reader of stdout that
goes away. After each, no process of the check may run and no folder of the command may stay.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
COMMAND = ROOT / "plugins/statechart/skills/statechart/scripts/statechart.py"
FIXTURES = ROOT / "tests/fixtures/statechart"
CORPUS = FIXTURES / "corpus"
CASES = sorted(p.name for p in CORPUS.iterdir() if p.is_dir())


def run(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(COMMAND), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, **(env or {})},
        check=False,
    )


def replay(case: Path, log: Path | None = None) -> dict[str, str]:
    env = {"JAVA": str(FIXTURES / "java"), "TLA2TOOLS": "replay", "STATECHART_REPLAY": str(case)}
    if log:
        env["STATECHART_LOG"] = str(log)
    return env


def expected_exit(case: Path) -> int:
    first = case / "verdict-1.exit"
    plain = int(first.read_text()) if first.exists() else 0
    return 0 if plain == 0 else 1 if plain in (11, 12, 13) else 2


def view_args(case: Path) -> list[str]:
    view = case / "view.py"
    return ["--view", str(view)] if view.exists() else []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("name", CASES)
def test_corpus_case_gives_its_chart_report_and_tlc_runs(name: str, tmp_path: Path) -> None:
    case = CORPUS / name
    out = tmp_path / "out"
    log = tmp_path / "runs.log"
    r = run(str(case / f"{name}.tla"), *view_args(case), "--out", str(out), env=replay(case, log))
    assert r.stderr == ""
    assert r.returncode == expected_exit(case)
    assert read(log) == read(case / "runs.log")
    assert read(out / "report.md") == read(case / "report.md")
    chart = case / "chart.mmd"
    if chart.exists():
        assert read(out / "chart.mmd") == read(chart)
    else:
        assert not (out / "chart.mmd").exists()
    assert r.stdout == f"{read(case / 'report.md')}\nWrote {out}\n"


def test_a_spec_in_a_folder_whose_name_is_not_ascii_checks_under_the_posix_locale(
    tmp_path: Path,
) -> None:
    case = tmp_path / "spec-é"
    shutil.copytree(CORPUS / "Login", case)
    out = case / "out"
    env = {**replay(case), "LC_ALL": "POSIX", "LC_CTYPE": "", "LANG": ""}
    r = run(str(case / "Login.tla"), "--view", str(case / "view.py"), "--out", str(out), env=env)
    assert r.stderr == ""
    assert r.returncode == 0
    assert read(out / "chart.mmd") == read(CORPUS / "Login" / "chart.mmd")


def test_the_command_writes_only_to_a_new_or_empty_folder(tmp_path: Path) -> None:
    case = CORPUS / "Counter"
    out = tmp_path / "out"
    out.mkdir()
    (out / "b.txt").write_text("")
    (out / "a.txt").write_text("")
    r = run(str(case / "Counter.tla"), "--out", str(out), env=replay(case))
    assert r.returncode == 2
    assert r.stderr == (
        f"{out} is not empty. It has a.txt. The command writes only to a new or empty folder. "
        "Pass --out with a new folder.\n"
    )
    assert sorted(p.name for p in out.iterdir()) == ["a.txt", "b.txt"]


def test_an_empty_output_folder_gets_the_files(tmp_path: Path) -> None:
    case = CORPUS / "Counter"
    out = tmp_path / "out"
    out.mkdir()
    r = run(str(case / "Counter.tla"), "--out", str(out), env=replay(case))
    assert r.returncode == expected_exit(case)
    assert sorted(p.name for p in out.iterdir()) == ["chart.mmd", "report.md", "tlc.out"]


def test_a_missing_config_is_named(tmp_path: Path) -> None:
    spec = tmp_path / "Lone.tla"
    spec.write_text("---- MODULE Lone ----\n====\n")
    r = run(str(spec))
    assert r.returncode == 2
    assert r.stderr == f"Cannot find the TLC config {tmp_path / 'Lone.cfg'}. Pass --config FILE.\n"


def test_usage_errors_print_the_usage() -> None:
    r = run("--colour", "x", "a.tla")
    assert r.returncode == 2
    assert r.stderr.startswith("Unknown option '--colour'.")
    assert "Usage: statechart SPEC.tla" in r.stderr
    r = run("a.tla", "b.tla")
    assert r.stderr.startswith("Give one SPEC.tla.\n\nUsage:")


def check_with_view(tmp_path: Path, source: str) -> subprocess.CompletedProcess[str]:
    case = CORPUS / "Login"
    view = tmp_path / "view.py"
    view.write_text(source)
    return run(
        str(case / "Login.tla"),
        "--view",
        str(view),
        "--out",
        str(tmp_path / "out"),
        env=replay(case),
    )


def test_a_view_name_that_the_command_does_not_read_is_refused(tmp_path: Path) -> None:
    r = check_with_view(tmp_path, "def states(v):\n    return v['main']\n")
    assert r.returncode == 2
    assert r.stderr == (
        "The view defines states, which the command does not read. Define only state, step, "
        "group, colors and title, and start any other name with _.\n"
    )


def test_private_names_and_imports_in_a_view_are_not_read(tmp_path: Path) -> None:
    source = (
        "from __future__ import annotations\n"
        "import re\n"
        "from typing import Any\n"
        "_SPLIT = re.compile(r'\\.')\n\n"
        "def state(v: dict[str, Any]) -> list[str]:\n"
        "    return _SPLIT.split(v['main'])\n"
    )
    r = check_with_view(tmp_path, source)
    assert r.stderr == ""
    assert read(tmp_path / "out" / "chart.mmd") == read(CORPUS / "Login" / "chart.mmd")


def test_a_view_gets_functions_as_dicts_with_index_keys_first() -> None:
    code = (
        "from frontends.value import parse_value\n"
        "from frontends.view import json\n"
        'print(json(parse_value(\'(2 :> "b" @@ 1 :> "a" @@ "k" :> "c")\')))\n'
        "print(json(parse_value('[b |-> 1, a |-> {3, 1}]')))\n"
    )
    r = subprocess.run(
        [sys.executable, "-c", code],
        cwd=COMMAND.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.stderr == ""
    assert r.stdout == "{'1': 'a', '2': 'b', 'k': 'c'}\n{'b': 1, 'a': [3, 1]}\n"


def processes_naming(path: Path) -> list[str]:
    listing = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True, check=True)
    return [line for line in listing.stdout.splitlines() if str(path) in line]


def settle(path: Path) -> list[str]:
    deadline = time.monotonic() + 10
    while processes_naming(path) and time.monotonic() < deadline:
        time.sleep(0.2)
    return processes_naming(path)


def slow_check(tmp_path: Path) -> tuple[list[str], dict[str, str]]:
    case = CORPUS / "Counter"
    (tmp_path / "tmp").mkdir()
    env = {**replay(case), "STATECHART_DELAY": "3", "TMPDIR": str(tmp_path / "tmp")}
    return [str(case / "Counter.tla"), "--out", str(tmp_path / "out")], env


def test_a_reader_who_stops_reading_does_not_change_the_exit_code(tmp_path: Path) -> None:
    case = CORPUS / "Counter"
    out = tmp_path / "out"
    p = subprocess.Popen(
        [sys.executable, str(COMMAND), str(case / "Counter.tla"), "--out", str(out)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, **replay(case)},
    )
    assert p.stdout is not None and p.stderr is not None
    p.stdout.close()
    assert p.wait() == expected_exit(case)
    assert p.stderr.read() == b""
    assert sorted(f.name for f in out.iterdir()) == ["chart.mmd", "report.md", "tlc.out"]


lifecycle_only_posix = pytest.mark.skipif(sys.platform == "win32", reason="SIGKILL and ps")


@lifecycle_only_posix
@pytest.mark.parametrize("when", ["before-worker", "after-worker"])
def test_a_command_killed_while_it_starts_leaves_no_check_and_no_folders(
    when: str, tmp_path: Path
) -> None:
    args, env = slow_check(tmp_path)
    r = subprocess.run(
        [sys.executable, str(FIXTURES / "die_at.py"), when, str(COMMAND), *args],
        capture_output=True,
        env={**os.environ, **env},
        check=False,
    )
    assert r.returncode == -signal.SIGKILL
    assert settle(tmp_path) == []
    assert sorted(p.name for p in tmp_path.iterdir()) == ["tmp"]
    assert list((tmp_path / "tmp").iterdir()) == []


@lifecycle_only_posix
@pytest.mark.parametrize(
    ("when", "said"),
    [
        ("janitor-fails", os.strerror(11 if sys.platform.startswith("linux") else 35)),
        ("janitor-dies", "The janitor process ended, so the command stopped the check."),
    ],
)
def test_a_command_whose_janitor_is_gone_stops_and_leaves_no_check_and_no_folders(
    when: str, said: str, tmp_path: Path
) -> None:
    args, env = slow_check(tmp_path)
    r = subprocess.run(
        [sys.executable, str(FIXTURES / "die_at.py"), when, str(COMMAND), *args],
        capture_output=True,
        text=True,
        env={**os.environ, **env},
        check=False,
    )
    assert r.returncode == 2
    assert said in r.stderr
    assert settle(tmp_path) == []
    assert sorted(p.name for p in tmp_path.iterdir()) == ["tmp"]
    assert list((tmp_path / "tmp").iterdir()) == []


@lifecycle_only_posix
@pytest.mark.parametrize(
    ("sent", "status"), [(signal.SIGKILL, -signal.SIGKILL), (signal.SIGINT, 130)]
)
def test_a_command_stopped_while_tlc_runs_leaves_no_check_and_no_folders(
    sent: signal.Signals, status: int, tmp_path: Path
) -> None:
    args, env = slow_check(tmp_path)
    p = subprocess.Popen(
        [sys.executable, str(COMMAND), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, **env},
    )
    deadline = time.monotonic() + 10
    while len(processes_naming(tmp_path)) < 3 and time.monotonic() < deadline:
        time.sleep(0.1)
    p.send_signal(sent)
    assert p.wait() == status
    assert settle(tmp_path) == []
    assert sorted(f.name for f in tmp_path.iterdir()) == ["tmp"]
    assert list((tmp_path / "tmp").iterdir()) == []


@pytest.mark.skipif(not os.environ.get("TLA2TOOLS"), reason="set TLA2TOOLS to run TLC")
@pytest.mark.parametrize("name", CASES)
def test_corpus_case_gives_its_chart_and_report_when_tlc_runs(name: str, tmp_path: Path) -> None:
    case = CORPUS / name
    out = tmp_path / "out"
    r = run(str(case / f"{name}.tla"), *view_args(case), "--out", str(out))
    assert r.stderr == ""
    assert r.returncode == expected_exit(case)
    assert read(out / "report.md") == read(case / "report.md")
    if (case / "chart.mmd").exists():
        assert read(out / "chart.mmd") == read(case / "chart.mmd")
