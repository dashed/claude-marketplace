"""Run statechart.py and SIGKILL it at a chosen point, as the lifecycle model's paths do.

Usage: die_at.py MODE STATECHART.PY ARGS...

before-worker and after-worker SIGKILL the command just before or after it starts the
worker. janitor-fails makes starting the janitor fail. janitor-dies kills the janitor as
soon as it starts, before the command can tell it the worker's pid.
"""

import errno
import os
import runpy
import signal
import subprocess
import sys

when, script, *args = sys.argv[1:]
real = subprocess.Popen


class Dying(real):
    def __init__(self, *a, **k) -> None:
        command = str(a[0] if a else k.get("args"))
        starts_worker = "worker.py" in command
        starts_janitor = "janitor.py" in command
        if when == "before-worker" and starts_worker:
            os.kill(os.getpid(), signal.SIGKILL)
        if when == "janitor-fails" and starts_janitor:
            raise OSError(errno.EAGAIN, os.strerror(errno.EAGAIN))
        super().__init__(*a, **k)
        if when == "after-worker" and starts_worker:
            os.kill(os.getpid(), signal.SIGKILL)
        if when == "janitor-dies" and starts_janitor:
            self.kill()
            self.wait()


setattr(subprocess, "Popen", Dying)
sys.path.insert(0, os.path.dirname(script))
sys.argv = [script, *args]
runpy.run_path(script, run_name="__main__")
