"""Check the spec and write the files into the stage folder."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import os
import re
import sys
import threading

from frontends.view import check_view, view_exports
from ir import StatechartError
from kill import kill_group
from pipeline import compile_result
from run import check, message_of

_SURROGATE = re.compile("[\ud800-\udfff]")


def _utf8(text: str) -> bytes:
    """UTF-8 bytes, with U+FFFD for a lone surrogate, as Node's `Buffer.from()` writes it."""
    try:
        return text.encode("utf-8")
    except UnicodeEncodeError:
        return _SURROGATE.sub("�", text).encode("utf-8")


def _watch_command() -> None:
    """Kill this process group when the command's pipe closes, which means the command died.

    The janitor does this too, but it learns the worker's pid only after the worker starts,
    so a command that dies in between would leave the check running. The thread reads the
    file descriptor, not `sys.stdin`, whose lock it would hold when the interpreter exits.
    """
    try:
        while os.read(0, 4096):
            pass
    except OSError:
        pass
    kill_group(os.getpid())


def load_view(file: str) -> dict[str, object]:
    path = os.path.abspath(file)
    name = "statechart_view"
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    if spec is None:
        raise StatechartError(f"Cannot load the view {file} as a Python module.")
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    sys.modules[name] = module
    loader.exec_module(module)
    return view_exports(module)


def main(argv: list[str]) -> int:
    stage, spec_file, config_file, *rest = argv
    threading.Thread(target=_watch_command, daemon=True).start()
    try:
        view = check_view(load_view(rest[0]) if rest else {})
        compiled = compile_result(check(spec_file, config_file), view)
        draft = os.path.join(stage, "draft")
        os.mkdir(draft)
        for name, parts in compiled.files.items():
            with open(os.path.join(draft, name), "xb") as f:
                for part in parts:
                    f.write(_utf8(part) if isinstance(part, str) else part)
                f.write(b"\n")
        os.rename(draft, os.path.join(stage, "done"))
        return compiled.exit
    except Exception as error:
        print(message_of(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.exit(main(sys.argv[1:]))
