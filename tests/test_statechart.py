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


def _tlc_msg(code: int, level: int, text: str) -> str:
    return f"@!@!@STARTMSG {code}:{level} @!@!@\n{text}\n@!@!@ENDMSG {code} @!@!@"


def _tlc_hold_out(distinct: int = 2) -> str:
    return "\n".join(
        [
            _tlc_msg(2262, 0, "TLC2 Version 2.19 of 08 August 2024"),
            _tlc_msg(2185, 0, "Starting..."),
            _tlc_msg(2190, 0, "Finished computing initial states: 1 distinct state generated."),
            _tlc_msg(2193, 0, "Model checking completed. No error has been found."),
            _tlc_msg(
                2199,
                0,
                f"{distinct} states generated, {distinct} distinct states found, 0 states left on queue.",
            ),
            _tlc_msg(2186, 0, "Finished in 10ms"),
        ]
    )


def _tlc_break_out(inv: str, var_name: str, var_val: str) -> str:
    return "\n".join(
        [
            _tlc_msg(2262, 0, "TLC2 Version 2.19 of 08 August 2024"),
            _tlc_msg(2185, 0, "Starting..."),
            _tlc_msg(2190, 0, "Finished computing initial states: 1 distinct state generated."),
            _tlc_msg(2110, 1, f"Invariant {inv} is violated."),
            _tlc_msg(2121, 1, "The behavior up to this point is:"),
            _tlc_msg(2217, 4, f"1: <Initial predicate>\n/\\ {var_name} = {var_val}"),
            _tlc_msg(
                2199, 0, "2 states generated, 2 distinct states found, 0 states left on queue."
            ),
            _tlc_msg(2186, 0, "Finished in 10ms"),
        ]
    )


def _tlc_stop_out(message: str) -> str:
    return "\n".join(
        [
            _tlc_msg(2262, 0, "TLC2 Version 2.19 of 08 August 2024"),
            _tlc_msg(2185, 0, "Starting..."),
            _tlc_msg(1000, 1, message),
            _tlc_msg(2186, 0, "Finished in 10ms"),
        ]
    )


def _sany_xml(
    module: str,
    variables: list[str],
    ops: list[tuple[str, int, int | None]],
) -> str:
    entries: list[str] = []
    refs: list[str] = []
    uid = 100
    for var in variables:
        uid += 1
        entries.append(
            f"<entry><UID>{uid}</UID><OpDeclNode><uniquename>{var}</uniquename>"
            "<kind>3</kind></OpDeclNode></entry>"
        )
        refs.append(f"<OpDeclNodeRef><UID>{uid}</UID></OpDeclNodeRef>")
    for name, arity, param_arity in ops:
        uid += 1
        op_uid = uid
        params_xml = ""
        if arity > 0 and param_arity is not None:
            param_items: list[str] = []
            for p_idx in range(arity):
                uid += 1
                entries.append(
                    f"<entry><UID>{uid}</UID><FormalParamNode><uniquename>p{p_idx}</uniquename>"
                    f"<arity>{param_arity}</arity></FormalParamNode></entry>"
                )
                param_items.append(
                    f"<leibnizparam><FormalParamNodeRef><UID>{uid}</UID></FormalParamNodeRef>"
                    "<leibniz/></leibnizparam>"
                )
            params_xml = f"<params>{''.join(param_items)}</params>"
        entries.append(
            f"<entry><UID>{op_uid}</UID><UserDefinedOpKind><uniquename>{name}</uniquename>"
            f"<arity>{arity}</arity><level>1</level>{params_xml}</UserDefinedOpKind></entry>"
        )
        refs.append(f"<UserDefinedOpKindRef><UID>{op_uid}</UID></UserDefinedOpKindRef>")
    mod_xml = f"<entry><UID>1</UID><ModuleNode><uniquename>{module}</uniquename>{''.join(refs)}</ModuleNode></entry>"
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><modules><RootModule>{module}</RootModule>'
        f"<context>{mod_xml}{''.join(entries)}</context><ModuleNodeRef><UID>1</UID></ModuleNodeRef></modules>"
    )


def test_overridden_constants_and_assume_run_helpers() -> None:
    code = (
        "from backends.cfg import assume_run\n"
        "from frontends.config import read_config\n"
        "from frontends.spec import overridden_constants\n"
        "cfg = read_config('Sub.cfg', 'CONSTANT A = 1 B = {1, 2} C(1) = 2 D <- E F <- [Mod] G Mod!H <- X')\n"
        "print(sorted(overridden_constants(cfg.sections)))\n"
        "print(assume_run('Sub', {0, 2}))\n"
    )
    r = subprocess.run(
        [sys.executable, "-c", code],
        cwd=COMMAND.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.stderr == ""
    assert r.returncode == 0
    lines = r.stdout.splitlines()
    assert lines[0] == "['A', 'B', 'C', 'D', 'F']"
    generated = "\n".join(lines[1:])
    assert "EXTENDS Sub" in generated
    assert "ChartTrue0 == TRUE" in generated
    assert "ChartTrue2(ChartArg1, ChartArg2) == TRUE" in generated


def test_assume_operators_report_rule_dependencies_offline(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "Sub.tla").write_text("---- MODULE Sub ----\n====\n", encoding="utf-8")
    (case / "Sub.cfg").write_text(
        "INIT Init\nNEXT Next\nINVARIANT NoPaidTrial\nCONSTANT Assume_Overridden <- TRUE\n",
        encoding="utf-8",
    )
    (case / "sany.out").write_text(
        _sany_xml(
            "Sub",
            ["plan"],
            [
                ("Assume_NoUpgradeDuringTrial", 0, None),
                ("Assume_MigrateNoTrial", 0, None),
                ("Assume_Overridden", 0, None),
                ("Assume_Param", 1, 0),
                ("Assume_HigherOrder", 1, 1),
            ],
        ),
        encoding="utf-8",
    )
    (case / "verdict-1.out").write_text(_tlc_hold_out(2), encoding="utf-8")
    (case / "ChartRun.out").write_text(_tlc_hold_out(2), encoding="utf-8")
    (case / "graph.dot").write_text(
        'strict digraph DiskGraph {\nsubgraph cluster_graph {\n1 [label="plan = \\"free\\"",style = filled]\n}\n}\n',
        encoding="utf-8",
    )
    (case / "assume-Assume_NoUpgradeDuringTrial-1.out").write_text(
        _tlc_break_out("NoPaidTrial", "plan", '"paid"'), encoding="utf-8"
    )
    (case / "assume-Assume_NoUpgradeDuringTrial-1.exit").write_text("12", encoding="utf-8")
    (case / "assume-Assume_NoUpgradeDuringTrial-2.out").write_text(
        _tlc_hold_out(2), encoding="utf-8"
    )
    (case / "assume-Assume_MigrateNoTrial-1.out").write_text(_tlc_hold_out(2), encoding="utf-8")
    (case / "assume-Assume_Param-1.out").write_text(_tlc_hold_out(2), encoding="utf-8")
    (case / "assume-all-1.out").write_text(_tlc_hold_out(2), encoding="utf-8")

    out = tmp_path / "out"
    log = tmp_path / "runs.log"
    r = run(str(case / "Sub.tla"), "--out", str(out), env=replay(case, log))

    assert r.stderr == ""
    assert r.returncode == 0
    runs_log = read(log)
    assert "CONSTANT Assume_NoUpgradeDuringTrial <- ChartTrue0" in runs_log
    assert "CONSTANT Assume_MigrateNoTrial <- ChartTrue0" in runs_log
    assert "CONSTANT Assume_Param <- ChartTrue1" in runs_log
    assert "Assume_Overridden <- ChartTrue" not in runs_log
    assert "Assume_HigherOrder <- ChartTrue" not in runs_log
    assert "CONSTRAINT ChartBound" in runs_log
    report_text = read(out / "report.md")
    assert "## Assumptions" in report_text
    assert "- NoPaidTrial holds only under Assume_NoUpgradeDuringTrial." in report_text
    assert "- Every holding rule still holds without Assume_MigrateNoTrial." in report_text
    assert "- Every holding rule still holds without Assume_Param." in report_text
    assert "together" not in report_text


def test_assume_combined_interaction_bound_and_stop_offline(tmp_path: Path) -> None:
    # Case A: two assumptions break NoBad only when relaxed together
    case_a = tmp_path / "case_a"
    case_a.mkdir()
    (case_a / "Mix.tla").write_text("---- MODULE Mix ----\n====\n", encoding="utf-8")
    (case_a / "Mix.cfg").write_text(
        "INIT Init\nNEXT Next\nINVARIANT NoBad\nCHECK_DEADLOCK FALSE\n", encoding="utf-8"
    )
    (case_a / "sany.out").write_text(
        _sany_xml("Mix", ["x"], [("Assume_A", 0, None), ("Assume_B", 0, None)]), encoding="utf-8"
    )
    (case_a / "verdict-1.out").write_text(_tlc_hold_out(1), encoding="utf-8")
    (case_a / "ChartRun.out").write_text(_tlc_hold_out(1), encoding="utf-8")
    (case_a / "graph.dot").write_text(
        'strict digraph DiskGraph {\nsubgraph cluster_graph {\n1 [label="x = 0",style = filled]\n}\n}\n',
        encoding="utf-8",
    )
    (case_a / "assume-Assume_A-1.out").write_text(_tlc_hold_out(2), encoding="utf-8")
    (case_a / "assume-Assume_B-1.out").write_text(_tlc_hold_out(2), encoding="utf-8")
    (case_a / "assume-all-1.out").write_text(_tlc_break_out("NoBad", "x", "1"), encoding="utf-8")
    (case_a / "assume-all-1.exit").write_text("12", encoding="utf-8")

    out_a = tmp_path / "out_a"
    r_a = run(str(case_a / "Mix.tla"), "--out", str(out_a), env=replay(case_a))
    assert r_a.returncode == 0
    assert "- NoBad holds only under Assume_A and Assume_B together." in read(out_a / "report.md")

    # Case B: assumption relaxation hits the 100,000-state bound
    case_b = tmp_path / "case_b"
    case_b.mkdir()
    (case_b / "Big.tla").write_text("---- MODULE Big ----\n====\n", encoding="utf-8")
    (case_b / "Big.cfg").write_text(
        "INIT Init\nNEXT Next\nINVARIANT Safe\nCHECK_DEADLOCK FALSE\n", encoding="utf-8"
    )
    (case_b / "sany.out").write_text(
        _sany_xml("Big", ["x"], [("Assume_Big", 0, None)]), encoding="utf-8"
    )
    (case_b / "verdict-1.out").write_text(_tlc_hold_out(1), encoding="utf-8")
    (case_b / "ChartRun.out").write_text(_tlc_hold_out(1), encoding="utf-8")
    (case_b / "graph.dot").write_text(
        'strict digraph DiskGraph {\nsubgraph cluster_graph {\n1 [label="x = 0",style = filled]\n}\n}\n',
        encoding="utf-8",
    )
    (case_b / "assume-Assume_Big-1.out").write_text(_tlc_hold_out(100_000), encoding="utf-8")

    out_b = tmp_path / "out_b"
    r_b = run(str(case_b / "Big.tla"), "--out", str(out_b), env=replay(case_b))
    assert r_b.returncode == 0
    assert (
        "- Without Assume_Big, TLC reached the 100,000-state bound before checking Safe."
        in read(out_b / "report.md")
    )

    # Case C: assumption relaxation stops with a TLC error
    case_c = tmp_path / "case_c"
    case_c.mkdir()
    (case_c / "Err.tla").write_text("---- MODULE Err ----\n====\n", encoding="utf-8")
    (case_c / "Err.cfg").write_text(
        "INIT Init\nNEXT Next\nINVARIANT Safe\nCHECK_DEADLOCK FALSE\n", encoding="utf-8"
    )
    (case_c / "sany.out").write_text(
        _sany_xml("Err", ["x"], [("Assume_Err", 0, None)]), encoding="utf-8"
    )
    (case_c / "verdict-1.out").write_text(_tlc_hold_out(1), encoding="utf-8")
    (case_c / "ChartRun.out").write_text(_tlc_hold_out(1), encoding="utf-8")
    (case_c / "graph.dot").write_text(
        'strict digraph DiskGraph {\nsubgraph cluster_graph {\n1 [label="x = 0",style = filled]\n}\n}\n',
        encoding="utf-8",
    )
    (case_c / "assume-Assume_Err-1.out").write_text(
        _tlc_stop_out("Attempted to evaluate an undefined operator."), encoding="utf-8"
    )
    (case_c / "assume-Assume_Err-1.exit").write_text("255", encoding="utf-8")

    out_c = tmp_path / "out_c"
    r_c = run(str(case_c / "Err.tla"), "--out", str(out_c), env=replay(case_c))
    assert r_c.returncode == 0
    report_c = read(out_c / "report.md")
    assert "- Without Assume_Err, TLC stopped with exit 255 before checking Safe." in report_c
    assert "Attempted to evaluate an undefined operator." in report_c


@pytest.mark.skipif(not os.environ.get("TLA2TOOLS"), reason="set TLA2TOOLS to run TLC")
def test_assume_sensitivity_with_real_tlc(tmp_path: Path) -> None:
    case = tmp_path / "sub"
    case.mkdir()
    (case / "Sub.tla").write_text(
        "\n".join(
            [
                "---- MODULE Sub ----",
                "VARIABLES plan, trial",
                "Assume_NoUpgradeDuringTrial == ~trial",
                "Assume_MigrateNoTrial == ~trial",
                'Assume_OnlyFree(p) == p = "free"',
                'Init == plan = "free" /\\ trial = FALSE',
                "StartTrial == plan = \"free\" /\\ ~trial /\\ trial' = TRUE /\\ plan' = plan",
                (
                    "Upgrade == Assume_NoUpgradeDuringTrial /\\ Assume_OnlyFree(plan) "
                    "/\\ plan' = \"paid\" /\\ trial' = trial"
                ),
                "Migrate == Assume_MigrateNoTrial /\\ plan' = plan /\\ trial' = trial",
                "Done == UNCHANGED <<plan, trial>>",
                "Next == StartTrial \\/ Upgrade \\/ Migrate \\/ Done",
                'NoPaidTrial == ~(plan = "paid" /\\ trial)',
                "====",
            ]
        ),
        encoding="utf-8",
    )
    (case / "Sub.cfg").write_text("INIT Init\nNEXT Next\nINVARIANT NoPaidTrial\n", encoding="utf-8")
    out = tmp_path / "out"
    r = run(str(case / "Sub.tla"), "--out", str(out))
    assert r.stderr == ""
    assert r.returncode == 0
    assert (out / "chart.mmd").is_file()
    report_text = read(out / "report.md")
    assert "## Rules that hold" in report_text
    assert "## Assumptions" in report_text
    assert "- NoPaidTrial holds only under Assume_NoUpgradeDuringTrial." in report_text
    assert "- Every holding rule still holds without Assume_MigrateNoTrial." in report_text
    assert "- Every holding rule still holds without Assume_OnlyFree." in report_text


@pytest.mark.skipif(not os.environ.get("TLA2TOOLS"), reason="set TLA2TOOLS to run TLC")
def test_assume_combined_interaction_with_real_tlc(tmp_path: Path) -> None:
    case = tmp_path / "pair"
    case.mkdir()
    (case / "Pair.tla").write_text(
        "\n".join(
            [
                "---- MODULE Pair ----",
                "VARIABLES a, b",
                "Assume_A == FALSE",
                "Assume_B == FALSE",
                "Init == a = FALSE /\\ b = FALSE",
                "StepA == Assume_A /\\ a' = TRUE /\\ b' = b",
                "StepB == Assume_B /\\ b' = TRUE /\\ a' = a",
                "Done == UNCHANGED <<a, b>>",
                "Next == StepA \\/ StepB \\/ Done",
                "NoBad == ~(a /\\ b)",
                "====",
            ]
        ),
        encoding="utf-8",
    )
    (case / "Pair.cfg").write_text("INIT Init\nNEXT Next\nINVARIANT NoBad\n", encoding="utf-8")
    out = tmp_path / "out"
    r = run(str(case / "Pair.tla"), "--out", str(out))
    assert r.stderr == ""
    assert r.returncode == 0
    report_text = read(out / "report.md")
    assert "- Every holding rule still holds without Assume_A." in report_text
    assert "- Every holding rule still holds without Assume_B." in report_text
    assert "- NoBad holds only under Assume_A and Assume_B together." in report_text


def test_report_is_read_before_dest_is_published(tmp_path: Path) -> None:
    case = CORPUS / "Counter"
    out = tmp_path / "out"
    code = (
        "import os, sys\n"
        "import statechart\n"
        "orig_rename = statechart._rename\n"
        "def rename_and_drop_report(src, dst):\n"
        "    orig_rename(src, dst)\n"
        "    os.unlink(os.path.join(dst, 'report.md'))\n"
        "statechart._rename = rename_and_drop_report\n"
        "sys.exit(statechart.main(sys.argv[1:]))\n"
    )
    r = subprocess.run(
        [sys.executable, "-c", code, str(case / "Counter.tla"), "--out", str(out)],
        cwd=COMMAND.parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, **replay(case)},
        check=False,
    )
    assert r.stderr == ""
    assert r.returncode == expected_exit(case)
    assert r.stdout == f"{read(case / 'report.md')}\nWrote {out}\n"
    assert not (out / "report.md").exists()
