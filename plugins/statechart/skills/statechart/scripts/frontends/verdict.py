"""Read which rule a TLC run broke and how many states it found."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

import js
from frontends.messages import text_of
from ir import EC, Part


@dataclass(eq=False)
class Break:
    kind: str
    name: str = ""


_NAMED: dict[int, tuple[str, re.Pattern[str]]] = {
    EC.TLC_INVARIANT_VIOLATED_INITIAL: (
        "invariant",
        re.compile(r"\AInvariant (" + js.DOT + r"+) is violated by the initial"),
    ),
    EC.TLC_INVARIANT_VIOLATED_BEHAVIOR: (
        "invariant",
        re.compile(js.BOL + r"Invariant (" + js.DOT + r"+) is violated\." + js.EOL),
    ),
    EC.TLC_PROPERTY_VIOLATED_INITIAL: (
        "property",
        re.compile(r"\AProperty (" + js.DOT + r"+) is violated by the initial"),
    ),
    EC.TLC_ACTION_PROPERTY_VIOLATED_BEHAVIOR: (
        "property",
        re.compile(js.BOL + r"Action property (" + js.DOT + r"+) is violated\." + js.EOL),
    ),
}

_DISTINCT: dict[int, re.Pattern[str]] = {
    EC.TLC_INIT_GENERATED1: re.compile(r"([0-9]+) distinct states? generated"),
    EC.TLC_INIT_GENERATED2: re.compile(r"with ([0-9]+) of them distinct"),
    EC.TLC_STATS: re.compile(r"([0-9]+) distinct states found"),
}

_INITIAL = re.compile(r"([0-9]+) (?:distinct )?states? generated")


@dataclass(eq=False)
class VerdictRead:
    broke: Break | None
    distinct: int
    initial: int


def read_verdict(messages: Iterable[Part]) -> VerdictRead:
    broke: Break | None = None
    distinct = 0
    initial = 0
    for m in messages:
        if isinstance(m, str):
            continue
        pattern = _DISTINCT.get(m.code)
        found = pattern.search(text_of(m)) if pattern else None
        if found:
            distinct = max(distinct, int(found.group(1)))
        if m.code in (EC.TLC_INIT_GENERATED1, EC.TLC_INIT_GENERATED2):
            generated = _INITIAL.search(text_of(m))
            initial = int(generated.group(1)) if generated else 0
        if broke:
            continue
        if m.code == EC.TLC_DEADLOCK_REACHED:
            broke = Break("deadlock")
        elif m.code == EC.TLC_TEMPORAL_PROPERTY_VIOLATED:
            broke = Break("temporal")
        named = _NAMED.get(m.code)
        name = named[1].search(text_of(m)) if named else None
        if named and name and name.group(1):
            broke = Break(named[0], name.group(1))
    return VerdictRead(broke, distinct, initial)
