"""Read TLC's state graph dump."""

from __future__ import annotations

import re
from collections.abc import Iterable

import js
from frontends.value import parse_value
from ir import Graph, State, StatechartError, Step, Value, Vars


def _unescape_dot(s: str) -> str:
    i = s.find("\\")
    if i == -1:
        return s
    out = ""
    start = 0
    while i != -1 and i + 1 < len(s):
        c = s[i + 1]
        if c in ("\n", "\r", " ", " "):
            i = s.find("\\", i + 1)
            continue
        out += s[start:i] + ("\n" if c == "n" else c)
        i += 2
        start = i
        i = s.find("\\", i)
    return out + s[start:]


_PAIR = re.compile(r"(\w+)" + js.WS_CLASS + r"*=" + js.WS_CLASS + r"*(.*)\Z", re.ASCII | re.DOTALL)


def parse_state(label: str, parsed: dict[str, tuple[str, Value]] | None = None) -> Vars:
    if parsed is None:
        parsed = {}
    pairs: list[tuple[str, Value]] = []
    for part in (label[3:] if label.startswith("/\\ ") else label).split("\n/\\ "):
        pair = parsed.get(part)
        if pair is None:
            m = _PAIR.match(part)
            if not m:
                raise StatechartError(f'cannot read the TLC state line "{part}"')
            pair = parsed[part] = (m.group(1), parse_value(m.group(2)))
        pairs.append(pair)
    return dict(pairs)


Lines = str | Iterable[str]

_LINE_BREAK = re.compile(r"\r?\n")


def split_lines(text: str) -> list[str]:
    return _LINE_BREAK.split(text[:-1] if text.endswith("\r") else text)


def lines_of(lines: Lines) -> Iterable[str]:
    return split_lines(lines) if isinstance(lines, str) else lines


_EDGE = re.compile(r'(-?[0-9]+) -> (-?[0-9]+) \[label="([^"]*)"')
_NODE = re.compile(r'(-?[0-9]+) \[label="((?:[^"\\]|\\' + js.DOT + r')*)"(,style = filled)?')


def parse_dot(lines: Lines) -> Graph:
    states: dict[str, State] = {}
    steps: dict[str, Step] = {}
    parsed: dict[str, tuple[str, Value]] = {}
    for line in lines_of(lines):
        edge = _EDGE.match(line)
        if edge:
            steps[" ".join(edge.groups())] = Step(edge.group(1), edge.group(2), edge.group(3))
            continue
        node = _NODE.match(line)
        if node:
            states[node.group(1)] = State(
                parse_state(_unescape_dot(node.group(2)), parsed), bool(node.group(3)), []
            )
    for loose in steps.values():
        if loose.from_ not in states or loose.to not in states:
            raise StatechartError(
                f"The TLC graph dump has a step {loose.action} to or from a state that it does not list."
            )
    return Graph(states, list(steps.values()))
