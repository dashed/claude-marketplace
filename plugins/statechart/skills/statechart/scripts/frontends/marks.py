"""Read the states that the chart run marks, and counterexamples."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

import js
from frontends.messages import action_of, message_state
from frontends.value import BRACKET, is_space, parse_value, token_end, unreadable
from ir import (
    EC,
    Mark,
    Part,
    SetValue,
    StatechartError,
    TraceState,
    Value,
    memo,
)


@dataclass(eq=False)
class _MarkTexts:
    values: list[str]
    rules: str


def _mark_texts(chunk: str, top: list[int], inner: list[int]) -> _MarkTexts | None:
    if len(top) != 2:
        return None
    a, b = top
    open_ = chunk.find("<<", a)
    close = chunk.rfind(">>", 0, b + 2)
    end = len(js.trim_end(chunk)) - 2
    if open_ < 0 or js.trim(chunk[a + 1 : open_]) or js.trim(chunk[close + 2 : b]):
        return None
    if not chunk.startswith(">>", max(end, 0)):
        return None
    cuts = [open_ + 1]
    for k in inner:
        if open_ < k < close:
            cuts.append(k)
    cuts.append(close)
    texts = [chunk[cuts[k - 1] + 1 : cuts[k]] for k in range(1, len(cuts))]
    return _MarkTexts(texts, chunk[b + 1 : end])


def _rule_names(v: Value) -> list[str] | None:
    if not isinstance(v, SetValue):
        return None
    names: list[str] = []
    for m in v.members:
        if not isinstance(m, str):
            return None
        names.append(m)
    return names


def read_marks(messages: Iterable[Part], tag: str) -> Iterator[Mark]:
    read = memo(parse_value)
    start = f'"{tag}",'
    chunk = ""
    depth = 0
    top: list[int] = []
    inner: list[int] = []
    for line in messages:
        if not isinstance(line, str):
            continue
        if not chunk:
            if not line.startswith("<<") or not js.trim_start(line[2:]).startswith(start):
                continue
            depth = 0
            top = []
            inner = []
        base = len(chunk)
        chunk += line + "\n"
        i = 0
        last = 0
        while i < len(line):
            c = ord(line[i])
            if is_space(c):
                i += 1
                continue
            j = token_end(line, i)
            if j == -1:
                raise unreadable(line + "\n", last)
            if c == 44 and depth == 1:
                top.append(base + i)
            elif c == 44 and depth == 2:
                inner.append(base + i)
            depth += BRACKET[c] if c < 128 else 0
            i = last = j
        if depth > 0:
            continue
        texts = _mark_texts(chunk, top, inner)
        values: list[Value] = []
        if texts:
            for v in texts.values:
                values.append(read(v))
        broken = _rule_names(read(texts.rules)) if texts else None
        if broken is None:
            raise StatechartError(
                f"TLC printed a mark that the command cannot read:\n{chunk[:2000]}"
            )
        chunk = ""
        yield Mark(values, broken)
    if chunk:
        raise StatechartError(
            "TLC's output ends inside a marked state, so the command cannot tell which rules "
            f"it breaks:\n{chunk[:2000]}"
        )


def read_counterexample(messages: Iterable[Part]) -> list[TraceState]:
    trace: list[TraceState] = []
    for m in messages:
        if isinstance(m, str):
            continue
        action = action_of(m) if m.code == EC.TLC_STATE_PRINT2 else None
        if action is not None:
            trace.append(TraceState(action, message_state(m)))
        elif m.code in (EC.TLC_INVARIANT_VIOLATED_INITIAL, EC.TLC_PROPERTY_VIOLATED_INITIAL):
            trace.append(TraceState("", message_state(m)))
    return trace
