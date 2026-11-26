"""Write the chart as a Mermaid stateDiagram-v2."""

from __future__ import annotations

import dataclasses
import re
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass

import js
from ir import Chart, ChartState, Region, append, text_key, tuple_key

_WHITE_SPACE = frozenset(
    [*range(0x09, 0x0E), 0x20, 0x85, 0xA0, 0x1680, *range(0x2000, 0x200B)]
    + [0x2028, 0x2029, 0x202F, 0x205F, 0x3000]
)
"""The code points with the Unicode White_Space property (`\\p{White_Space}`)."""

_SAFE_PUNCT = frozenset(" !'()+,-./=?[]\"_|@{}:\\^%<>")


def _is_letter(c: str) -> bool:
    return unicodedata.category(c).startswith("L")


def _is_letter_or_number(c: str) -> bool:
    return unicodedata.category(c)[0] in "LN"


_REWRITTEN = ["ﬂ°", "¶ß"]
_first_of = {ord(pair[1]): ord(pair[0]) for pair in _REWRITTEN}
_KEPT = 0
_BLANKED = 1
_DROPPED = 2
_CODED = 3
_JOINS = 4


def _kind_of(n: int) -> int:
    c = chr(n)
    if c == " ":
        kind = _KEPT
    elif n in _WHITE_SPACE:
        kind = _BLANKED
    elif n == 0 or 0x80 <= n <= 0x9F:
        kind = _DROPPED
    elif _is_letter_or_number(c) or c in _SAFE_PUNCT:
        kind = _KEPT
    else:
        kind = _CODED
    return kind | _JOINS if n in _first_of else kind


_ASCII = [_kind_of(n) for n in range(128)]
_wide: dict[int, int] = {}


def _kind_at(n: int) -> int:
    if n < 128:
        return _ASCII[n]
    kind = _wide.get(n)
    if kind is None:
        kind = _wide[n] = _kind_of(n)
    return kind


Ref = Callable[[int], str]


def _encode(s: str, ref: Ref) -> str:
    out: list[str] = []
    run = 0
    last = -1
    for i, ch in enumerate(s):
        n = ord(ch)
        if 0xD800 <= n <= 0xDFFF:
            n = 0xFFFD
        kind = _kind_at(n)
        if kind == _DROPPED:
            out.append(s[run:i])
            run = i + 1
        else:
            joined = kind >= _JOINS and _first_of.get(n) == last
            kind &= ~_JOINS
            if joined or kind != _KEPT:
                out.append(s[run:i])
                if joined:
                    out.append(ref(0x2060))
                if kind == _KEPT:
                    run = i
                else:
                    out.append(" " if kind == _BLANKED else ref(n))
                    run = i + 1
            last = n
    out.append(s[run:])
    return "".join(out)


_MARKER = re.compile(r'(?<=marker-end=)"')


def _hazard(s: str, i: int) -> bool:
    """Whether Mermaid would misread the character at `i`, so that it must be written as an entity."""
    c = s[i]
    following = s[i + 1] if i + 1 < len(s) else ""
    if c == ":":
        if following in (":", ""):
            return True
        for d in s[i + 1 :]:
            if d == "#":
                return True
            if d in js.WS:
                return False
        return False
    if c == "\\":
        return following in ("n", "N")
    if c == "%":
        return following == "%"
    if c == "<":
        return following in ("/", "!", "?") or (following != "" and _is_letter(following))
    if c == "_":
        before = s[i - 1] if i > 0 else ""
        return not (following and _is_letter_or_number(following)) or not (
            before and _is_letter_or_number(before)
        )
    return False


def _code(s: str, ref: Ref) -> str:
    encoded = _MARKER.sub(lambda _: f'{ref(0x2060)}"', _encode(s, ref))
    return "".join(
        ref(ord(c)) if c in ":\\%<_" and _hazard(encoded, i) else c for i, c in enumerate(encoded)
    )


_DIRECTION = re.compile(
    r"(direction)" + js.WS_CLASS + r"+(?=LR|RL|TB|BT)", re.IGNORECASE | re.ASCII
)
_DOUBLE_BRACKET = re.compile(r"\[(?=\[)")
_C4 = re.compile(r"C4(?=Container|Component|Dynamic|Deployment)")


def _esc(s: str, quoted: bool = False) -> str:
    plain = _code(s, lambda n: f"#{n};")
    out = plain.replace('"', "#34;") if quoted else plain
    if not js.trim(out):
        return "#32;"
    turned = _DIRECTION.sub(r"\1#32;", out)
    opened = _DOUBLE_BRACKET.sub("#91;", turned) if "[[" in turned else turned
    return _C4.sub("C#52;", opened) if "C4" in opened else opened


def _or(names: Iterable[str]) -> str:
    return " or ".join(sorted(names, key=text_key))


@dataclass(eq=False)
class Edge:
    from_: list[str]
    start: bool
    to: list[str]
    label: str | None


def _within(parent: list[str], path: list[str]) -> bool:
    return len(path) >= len(parent) and all(path[i] == p for i, p in enumerate(parent))


def _way_in(e: Edge) -> str:
    return tuple_key([e.start, e.from_])


def drawn_edges(r: Region) -> list[Edge]:
    out: list[Edge] = [Edge([], True, s.path, None) for s in r.states if s.start]
    for s in r.steps:
        out.append(Edge(s.from_, False, s.to, s.label + (f" [{s.when}]" if s.when else "")))
    parents: dict[str, list[str]] = {}
    for s in r.states:
        for i in range(1, len(s.path)):
            prefix = s.path[:i]
            parents[tuple_key(prefix)] = prefix
    for parent in sorted(parents.values(), key=len):
        into = [
            e
            for e in out
            if len(e.to) > len(parent) and _within(parent, e.to) and not _within(parent, e.from_)
        ]
        if not into or any(_way_in(e) != _way_in(into[0]) for e in into):
            continue
        one = len(into) == 1
        at = next(k for k, e in enumerate(out) if e is into[0])
        out = [e for e in out if not any(e is x for x in into)]
        out[at:at] = [
            dataclasses.replace(into[0], to=parent, label=into[0].label if one else None),
            *(Edge(parent, True, e.to, None if one else e.label) for e in into),
        ]
    return out


_MARK_STYLES = {
    "breaks": "fill:#ffecee,stroke:#e72e3b,stroke-width:2.5px,color:#cd2834",
    "mayBreak": "fill:#fff3e6,stroke:#e8730c,stroke-width:2.5px,color:#b85a06",
}


def mermaid_lines(chart: Chart) -> list[str]:
    counter = 0
    marks: list[str] = []
    used: set[str] = set()
    rules: dict[str, dict[str, None]] = {"breaks": {}, "mayBreak": {}}

    def region(r: Region) -> list[str]:
        out: list[str] = []
        top_ids: dict[str, str] = {}
        nested_ids: dict[str, str] = {}

        def id_(path: list[str]) -> str:
            nonlocal counter
            top = len(path) == 1
            named = top_ids if top else nested_ids
            k = path[0] if top else tuple_key(path)
            s = named.get(k)
            if s is None:
                s = named[k] = f"s{counter}"
                counter += 1
            return s

        known: dict[int, tuple[list[str], str]] = {}

        def id_of(path: list[str]) -> str:
            found = known.get(id(path))
            if found is not None and found[0] is path:
                return found[1]
            s = id_(path)
            known[id(path)] = (path, s)
            return s

        drawn = drawn_edges(r)

        def line(e: Edge, indent: str) -> str:
            label = "" if e.label is None else f": {_esc(e.label)}"
            return f"{indent}{'[*]' if e.start else id_of(e.from_)} --> {id_of(e.to)}{label}"

        def tree(prefix: list[str], indent: str, below: list[ChartState]) -> None:
            heads: dict[str, list[ChartState]] = {}
            for s in below:
                append(heads, s.path[len(prefix)], s)
            for head, under in heads.items():
                path = [*prefix, head]
                leaf: ChartState | None = None
                inner: list[ChartState] = []
                for s in under:
                    if len(s.path) > len(path):
                        inner.append(s)
                    else:
                        leaf = s
                if inner:
                    out.append(f'{indent}state "{_esc(head, True)}" as {id_(path)} {{')
                    tree(path, indent + "  ", inner)
                    k = tuple_key(path)
                    for e in drawn:
                        if e.start and tuple_key(e.from_) == k:
                            out.append(line(e, f"{indent}  "))
                    out.append(f"{indent}}}")
                elif leaf is not None:
                    sid = id_of(leaf.path)
                    out.append(f"{indent}{sid}: {_esc(head)}")
                    mark = "mayBreak" if leaf.breaks and not leaf.works else None
                    if mark and any(b.always for b in leaf.breaks):
                        mark = "breaks"
                    if mark:
                        for b in leaf.breaks:
                            rules[mark][b.rule.name] = None
                    trail = ["bugPath" if leaf.lead else None, "repeats" if leaf.repeats else None]
                    color = None if leaf.group is None else chart.colors.get(js.string(leaf.group))
                    for cls in [color, mark, *trail]:
                        if cls:
                            used.add(cls)
                            marks.append(f"  class {sid} {cls}")

        tree([], "  ", r.states)
        for e in drawn:
            if not e.start or not e.from_:
                out.append(line(e, "  "))
        return out

    body: list[str]
    if len(chart.regions) > 1:
        body = ['  state "At the same time" as all {']
        for i, r in enumerate(chart.regions):
            if i:
                body.append("    --")
            body.append(f'    state "{_esc(r.name, True)}" as r{i} {{')
            body.extend(f"    {text}" for text in region(r))
            body.append("    }")
        body.append("  }")
    else:
        body = region(chart.regions[0])
    legend: list[tuple[str, str]] = []
    for entry in [
        *chart.colors.items(),
        (f"Breaks {_or(rules['breaks'])}", "breaks"),
        (f"Breaks {_or(rules['mayBreak'])} in some cases", "mayBreak"),
        (f"Path to the {_or(chart.paths)} bug", "bugPath"),
        (f"Repeats forever, so {_or(chart.loops)} breaks", "repeats"),
    ]:
        if entry[1] in used:
            legend.append(entry)
    lines: list[str] = []
    title = _code(chart.title, lambda n: f"ﬂ°°{n}¶ß").replace("<", "ﬂ°°60¶ß") if chart.title else ""
    if title:
        lines.extend(["---", f"title: {js.stringify(title)}", "---"])
    lines.append("stateDiagram-v2")
    if len(chart.regions) > 1:
        lines.append("  direction LR")
    if legend:
        lines.append('  state "Legend" as legend {')
        for i, (text, _) in enumerate(legend):
            lines.append(f"    lg{i}: {_esc(text)}")
        lines.append("  }")
        for i, (_, cls) in enumerate(legend):
            lines.append(f"  class lg{i} {cls}")
    lines.extend(body)
    for cls, style in _MARK_STYLES.items():
        if cls in used:
            lines.append(f"  classDef {cls} {style}")
    lines.extend(marks)
    return lines


def mermaid(chart: Chart) -> str:
    return "\n".join(mermaid_lines(chart))
