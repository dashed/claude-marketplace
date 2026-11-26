"""Print TLC's -tool messages as plain TLC prints them."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta, timezone

from ir import EC, LEVEL, PART, Message, Part

_PREFIX = {
    LEVEL.ERROR: "Error: ",
    LEVEL.TLCBUG: "TLC Bug: ",
    LEVEL.WARNING: "Warning: ",
    LEVEL.STATE: "State ",
}
_MINUTE = 60_000
_HOUR = 3_600_000
_DAY = 86_400_000
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def runtime(ms: int) -> str:
    t = _EPOCH + timedelta(milliseconds=ms - _DAY if ms > _DAY else ms)
    hh, mm, ss = f"{t.hour:02d}", f"{t.minute:02d}", f"{t.second:02d}"
    if ms > _DAY:
        return f"{t.timetuple().tm_yday}d {hh}h"
    if ms > _HOUR:
        return f"{hh}h {mm}min"
    if ms > _MINUTE:
        return f"{mm}min {ss}s"
    return f"{ss}s"


_BACK = re.compile(r"\A([0-9]+): Back to state: ")
_FINISHED = re.compile(r"\AFinished in ([0-9]+)ms")


def _first_line(m: Message, line: str) -> str:
    if m.code == EC.TLC_BACK_TO_STATE:
        return _BACK.sub(r"Back to state \1: ", line, count=1)
    if m.code == EC.TLC_FINISHED:
        return _FINISHED.sub(
            lambda found: f"Finished in {runtime(int(found.group(1)))}", line, count=1
        )
    return _PREFIX.get(m.level, "") + line


def _render(m: Message) -> str:
    body = "\n".join(part if isinstance(part, str) else _render(part) for part in m.body)
    return (m.before_marker or "") + _first_line(m, body)


def _printed(parts: Iterable[Part]) -> Iterator[str]:
    warned = False
    progress: Message | None = None
    for part in parts:
        if (
            progress is not None
            and progress.body
            and (isinstance(part, str) or part.code != EC.TLC_STATS)
        ):
            yield _render(progress)
        progress = None
        if isinstance(part, str):
            yield part
            continue
        if part.code in (EC.TLC_SANY_START, EC.TLC_SANY_END):
            continue
        if part.code == EC.TLC_PROGRESS_STATS:
            progress = part
        elif part.body:
            yield _render(part)
        if part.level == LEVEL.WARNING and not warned:
            yield "(Use the -nowarning option to disable this warning.)"
            warned = True
    if progress is not None and progress.body:
        yield _render(progress)


def plain_text(parts: Iterable[Part]) -> Iterator[str]:
    chunk: list[str] = []
    size = 0
    for line in _printed(parts):
        chunk.append(f"{line}\n")
        size += len(line) + 1
        if size >= PART:
            yield "".join(chunk)
            chunk = []
            size = 0
    if chunk:
        yield "".join(chunk)
