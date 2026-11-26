"""Clean up after the check when the command dies before it can.

The command starts the janitor before it makes its folders, so that the janitor can
remove them whenever the command dies. The command keeps this process's stdin open and
writes `pid N` when it starts the check, and `exited` when the check ends. When stdin
closes, the command is gone: the janitor kills the check's process group and removes
the folders that it names.
"""

from __future__ import annotations

import shutil
import sys

from kill import kill_group


def main(dirs: list[str]) -> None:
    pid: int | None = None
    exited = False
    try:
        for raw in sys.stdin.buffer:
            line = raw.decode("utf-8", "replace").strip()
            if line.startswith("pid "):
                pid = int(line[4:])
            elif line == "exited":
                exited = True
    except (OSError, ValueError):
        pass
    group_outlives_worker = sys.platform != "win32"
    if pid is not None and (not exited or group_outlives_worker):
        kill_group(pid)
    for d in dirs:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
