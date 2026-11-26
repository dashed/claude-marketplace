"""Read TLC's -tool messages."""

from __future__ import annotations

import re
from collections.abc import Iterator

import js
from frontends.dot import Lines, lines_of, parse_state
from ir import Message, Part, Vars

_START = re.compile(r"@!@!@STARTMSG ([0-9]+):([0-9]+) @!@!@\Z")
_END = re.compile(r"@!@!@ENDMSG [0-9]+ @!@!@")


def _is_cut_marker(last_line: str) -> bool:
    return last_line.startswith("@!@!@")


def _cut_message(open_: list[Message]) -> Message | None:
    i = len(open_) - 1
    while i > 0 and not open_[i].body:
        open_[i - 1].body.pop()
        i -= 1
    return open_[0] if open_ and open_[0].body else None


def read_messages(tlc_out: Lines) -> Iterator[Part]:
    lines = iter(lines_of(tlc_out))
    open_: list[Message] = []
    try:
        following = next(lines, None)
        while following is not None:
            line = following
            following = next(lines, None)
            if following is None and (not line or _is_cut_marker(line)):
                break
            start = _START.search(line)
            if start:
                message = Message(int(start.group(1)), int(start.group(2)), [])
                if start.start():
                    message.before_marker = line[: start.start()]
                if open_:
                    open_[-1].body.append(message)
                open_.append(message)
            elif _END.fullmatch(line):
                done = open_.pop() if open_ else None
                if done and not open_:
                    yield done
            elif open_:
                open_[-1].body.append(line)
            else:
                yield line
    finally:
        close = getattr(lines, "close", None)
        if close:
            close()
    cut = _cut_message(open_)
    if cut:
        yield cut


def text_of(m: Message) -> str:
    return "\n".join(part for part in m.body if isinstance(part, str))


_ACTION = re.compile(r"[0-9]+: (?:Back to state: )?<([^" + re.escape(js.WS) + r">]+)")


def action_of(m: Message) -> str | None:
    found = _ACTION.match(text_of(m))
    return found.group(1) if found else None


def message_state(m: Message) -> Vars:
    lines = text_of(m).split("\n")
    body: list[str] = []
    i = 1
    while i < len(lines) and js.trim(lines[i]):
        body.append(lines[i])
        i += 1
    return parse_state("\n".join(body))
