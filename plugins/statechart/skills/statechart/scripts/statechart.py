#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check a TLA+ spec with TLC and draw its state graph as Mermaid."""

from __future__ import annotations

import io
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
from types import FrameType

import js
from kill import kill_group
from run import message_of

USAGE = """Usage: statechart SPEC.tla [--config FILE] [--view FILE] [--out DIR]

Checks SPEC.tla with TLC and draws its state graph as Mermaid. Above 500 states, the chart
draws only the paths to the rules that break, and with no rule broken there is no chart.mmd.
  --config FILE  TLC config. Default: SPEC.cfg beside the spec.
  --view FILE    A Python module that defines state(vars) and, if you want, step(action, from_,
                 to), group(vars), colors, and title. state() returns a string for a flat chart,
                 a list for parent states, or a dict for regions. Default: each state's values.
                 colors gives each group blue, orange, purple, yellow, teal, tan, or pink.
  --out DIR      Where to write report.md, chart.mmd, tlc.out, and tlc-RULE.out for each
                 property that breaks and each rule that breaks off the chart. The folder must
                 be new or empty. Default: SPEC-chart.
Exit code: TLC's own on the config as written: 0 when every rule holds, 1 when a rule breaks,
and 2 when TLC stops with an error, a signal kills the check, or the command cannot run. 130 or
143 when SIGINT or SIGTERM stops the check. Only exits 0 and 1 write output."""

_OPTIONS = ("config", "view", "out")
_HERE = os.path.dirname(os.path.abspath(__file__))
_NEW_SESSION = sys.platform != "win32"
_NEW_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)


class _UsageError(Exception):
    pass


def _parse_args(argv: list[str]) -> tuple[dict[str, str], list[str]]:
    """Read the arguments as Node's `parseArgs` in strict mode reads them."""
    flags: dict[str, str] = {}
    positionals: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        i += 1
        if arg == "--":
            positionals.extend(argv[i:])
            break
        if not arg.startswith("-") or arg == "-":
            positionals.append(arg)
            continue
        name, eq, value = arg.lstrip("-").partition("=")
        dashes = "--" if arg.startswith("--") else "-"
        if dashes == "-" or name not in _OPTIONS:
            raise _UsageError(
                f"Unknown option '{dashes}{name}'. To specify a positional argument starting "
                f"with a '-', place it at the end of the command after '--', as in "
                f"'-- \"{dashes}{name}\"'"
            )
        if not eq:
            if i >= len(argv):
                raise _UsageError(f"Option '--{name} <value>' argument missing")
            value = argv[i]
            if value.startswith("-"):
                raise _UsageError(
                    f"Option '--{name}' argument is ambiguous.\nDid you forget to specify the "
                    f"option argument for '--{name}'?\nTo specify an option argument starting "
                    f"with a dash use '--{name}=-XYZ'."
                )
            i += 1
        flags[name] = value
    return flags, positionals


_TLA = re.compile(r"\.tla\Z")


def _run(flags: dict[str, str], spec_file: str, stopped: list[signal.Signals]) -> int:
    config_file = flags.get("config") or _TLA.sub(".cfg", spec_file, count=1)
    if not os.path.exists(config_file):
        raise _CommandError(f"Cannot find the TLC config {config_file}. Pass --config FILE.")
    out = flags.get("out") or _TLA.sub("-chart", spec_file, count=1)
    entries: list[str] = []
    try:
        entries = os.listdir(out)
        dest = os.path.realpath(out)
    except FileNotFoundError:
        if os.path.lexists(out):
            raise _CommandError(
                f"{out} cannot be the output folder. It is a broken link. Pass --out with a new "
                "folder."
            ) from None
        dest = os.path.abspath(out)
    except OSError as error:
        raise _CommandError(
            f"{out} cannot be the output folder. {error.strerror or error}. Pass --out with a "
            "new folder."
        ) from error
    if entries:
        first = sorted(entries, key=js.text_key)[0]
        raise _CommandError(
            f"{out} is not empty. It has {first}. The command writes only to a new or empty "
            "folder. Pass --out with a new folder."
        )

    base = os.path.dirname(dest)
    while not os.path.exists(base):
        base = os.path.dirname(base)
    token = secrets.token_hex(8)
    stage = os.path.join(base, f".{os.path.basename(dest)}.statechart-{token}")
    tmp = os.path.join(tempfile.gettempdir(), f"statechart-{token}")
    done = os.path.join(stage, "done")
    janitor: subprocess.Popen[bytes] | None = None
    worker: subprocess.Popen[bytes] | None = None
    try:
        janitor = cleaner = subprocess.Popen(
            [sys.executable, os.path.join(_HERE, "janitor.py"), stage, tmp],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=_NEW_SESSION,
            creationflags=_NEW_GROUP,
        )
        os.mkdir(stage, 0o700)
        os.mkdir(tmp, 0o700)
        worker = check = subprocess.Popen(
            [
                sys.executable,
                os.path.join(_HERE, "worker.py"),
                stage,
                spec_file,
                config_file,
                *([flags["view"]] if flags.get("view") else []),
            ],
            stdin=subprocess.PIPE,
            env={**os.environ, "TMPDIR": tmp, "TEMP": tmp, "TMP": tmp},
            start_new_session=_NEW_SESSION,
            creationflags=_NEW_GROUP,
        )
        if not _tell(cleaner, f"pid {check.pid}"):
            raise _CommandError("The janitor process ended, so the command stopped the check.")
        while not stopped:
            try:
                check.wait(timeout=0.1)
                break
            except subprocess.TimeoutExpired:
                continue
        if check.returncode is not None:
            _tell(cleaner, "exited")
        running = check.returncode is None
        group_outlives_worker = sys.platform != "win32"
        if running or group_outlives_worker:
            kill_group(check.pid)
        verdict = check.wait()
        _tell(cleaner, "exited")
        if stopped:
            name = stopped[0]
            _say(f"{name.name} stopped the check, so the command wrote nothing.")
            return 128 + int(name)
        if verdict < 0:
            _say(f"{signal.Signals(-verdict).name} killed the check, so the command wrote nothing.")
            return 2
        if verdict in (0, 1) and os.path.exists(done):
            with open(os.path.join(done, "report.md"), "rb") as f:
                report = f.read()
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try:
                _rename(done, dest)
            except OSError as error:
                if not os.path.isdir(dest) or not os.listdir(dest):
                    raise
                first = sorted(os.listdir(dest), key=js.text_key)[0]
                raise _CommandError(
                    f"{os.path.join(out, first)} appeared while the check ran, so the command "
                    "wrote nothing. Pass --out with a new folder."
                ) from error
            _print(report + f"\nWrote {out}\n".encode())
            return verdict
        return 2
    finally:
        if worker is not None and worker.returncode is None:
            kill_group(worker.pid)
            worker.wait()
        shutil.rmtree(stage, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)
        if janitor is not None:
            janitor.kill()
            janitor.wait()


def _tell(janitor: subprocess.Popen[bytes], line: str) -> bool:
    """Send the janitor one line. False when the janitor is gone."""
    try:
        if janitor.stdin is None or janitor.stdin.closed:
            return False
        janitor.stdin.write(f"{line}\n".encode())
        janitor.stdin.flush()
        return True
    except OSError:
        return False


def _print(data: bytes) -> None:
    """Write to stdout. When nobody reads stdout any more, the output folder still counts."""
    try:
        sys.stdout.buffer.write(data)
        sys.stdout.flush()
    except OSError:
        try:
            devnull = os.open(os.devnull, os.O_WRONLY)
            try:
                os.dup2(devnull, sys.stdout.fileno())
            finally:
                os.close(devnull)
        except OSError:
            pass


def _say(text: str) -> None:
    try:
        print(text, file=sys.stderr)
    except OSError:
        pass


def _rename(source: str, dest: str) -> None:
    try:
        os.rename(source, dest)
    except OSError:
        if sys.platform != "win32" or not os.path.isdir(dest) or os.listdir(dest):
            raise
        os.rmdir(dest)
        os.rename(source, dest)


class _CommandError(Exception):
    pass


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    stopped: list[signal.Signals] = []

    def on_signal(signum: int, _frame: FrameType | None) -> None:
        if not stopped:
            stopped.append(signal.Signals(signum))

    for name in ("SIGINT", "SIGTERM"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), on_signal)
    try:
        flags, positionals = _parse_args(argv)
        if len(positionals) != 1:
            raise _UsageError("Give one SPEC.tla.")
    except _UsageError as error:
        _say(f"{error}\n\n{USAGE}")
        return 2
    try:
        return _run(flags, positionals[0], stopped)
    except Exception as error:
        _say(str(error) if isinstance(error, _CommandError) else message_of(error))
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
