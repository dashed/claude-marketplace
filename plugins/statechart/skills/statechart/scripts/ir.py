"""The data that the passes share."""

from __future__ import annotations

import json
from collections.abc import Callable, Hashable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, TypeVar, Union

import js


class Model:
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name


class SetValue:
    __slots__ = ("_json", "_key", "members")

    def __init__(self, members: list[Value]) -> None:
        self.members = members
        self._key: str | None = None
        self._json: Any = None


class Interval:
    __slots__ = ("_json", "_key", "hi", "lo")

    def __init__(self, lo: int, hi: int) -> None:
        self.lo = lo
        self.hi = hi
        self._key: str | None = None
        self._json: Any = None


class Function:
    __slots__ = ("_json", "_key", "keys", "printed_as", "values")

    def __init__(self, printed_as: str, keys: list[Value], values: list[Value]) -> None:
        self.printed_as = printed_as
        self.keys = keys
        self.values = values
        self._key: str | None = None
        self._json: Any = None


Value = Union[bool, int, str, Model, SetValue, Interval, Function]
Vars = dict[str, Value]


@dataclass(eq=False)
class Rule:
    kind: str
    name: str


@dataclass(eq=False)
class State:
    vars: Vars
    start: bool
    breaks: list[Rule]
    ends: list[Rule] | None = None
    past: bool | None = None
    excluded: bool | None = None


@dataclass(eq=False)
class Step:
    from_: str
    to: str
    action: str


@dataclass(eq=False)
class Graph:
    states: dict[str, State]
    steps: list[Step]


@dataclass(eq=False)
class PathStep:
    action: str
    state: str
    step: Step


@dataclass(eq=False)
class Lasso:
    start: str
    path: list[PathStep]
    loop: int | None
    stutters: bool


@dataclass(eq=False)
class Mark:
    values: list[Value]
    broken: list[str]


@dataclass(eq=False)
class TraceState:
    action: str
    vars: Vars


@dataclass(eq=False)
class TraceSeqState:
    action: str
    vars: Vars | None


@dataclass(eq=False)
class Trace:
    seq: list[TraceSeqState]
    loop: int | None


@dataclass(eq=False)
class Bug:
    rule: Rule
    start: str
    path: list[PathStep]
    loop: int | None = None
    stutters: bool | None = None


@dataclass(eq=False)
class ConfigSection:
    key: str
    line: int
    tokens: list[str]


@dataclass(eq=False)
class Config:
    sections: list[ConfigSection] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    properties: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    action_constraints: list[str] = field(default_factory=list)
    check_deadlock: bool | None = None
    init: str | None = None
    next: str | None = None
    spec: str | None = None
    view: str | None = None
    symmetry: str | None = None
    type: str | None = None
    type_constraint: str | None = None


@dataclass(eq=False)
class Spec:
    module: str
    variables: list[str]
    invariants: list[str]
    properties: list[str]
    deadlock: bool
    written: list[ConfigSection]
    folder: str | None = None


@dataclass(eq=False)
class Message:
    code: int
    level: int
    body: list[Part]
    before_marker: str | None = None


Line = str
Part = Union[Line, Message]


class EC:
    TLC_INVARIANT_VIOLATED_INITIAL = 2107
    TLC_PROPERTY_VIOLATED_INITIAL = 2108
    TLC_INVARIANT_VIOLATED_BEHAVIOR = 2110
    TLC_ACTION_PROPERTY_VIOLATED_BEHAVIOR = 2112
    TLC_DEADLOCK_REACHED = 2114
    TLC_TEMPORAL_PROPERTY_VIOLATED = 2116
    TLC_BACK_TO_STATE = 2122
    TLC_FINISHED = 2186
    TLC_INIT_GENERATED1 = 2190
    TLC_INIT_GENERATED2 = 2191
    TLC_STATS = 2199
    TLC_PROGRESS_STATS = 2200
    TLC_STATE_PRINT2 = 2217
    TLC_STATE_PRINT3 = 2218
    TLC_SANY_END = 2219
    TLC_SANY_START = 2220


class LEVEL:
    NONE = 0
    ERROR = 1
    TLCBUG = 2
    WARNING = 3
    STATE = 4


@dataclass(eq=False)
class Verdict:
    rule: Rule
    outcome: str
    messages: Iterable[Part] | None


@dataclass(eq=False)
class Property(Verdict):
    bug: Lasso | None = None
    initial_only: bool = False


@dataclass(eq=False)
class Stop:
    status: int | None
    message: str


@dataclass(eq=False)
class States:
    distinct: int = 0
    initial: int = 0
    complete: bool = False
    cut: bool = False


@dataclass(eq=False)
class Drawing:
    status: int | None


@dataclass(eq=False)
class CheckResult:
    spec: Spec
    graph: Graph
    paths: list[Bug] | None
    rules: list[Verdict]
    properties: list[Property]
    exit: int
    stop: Stop | None
    drawing: Drawing | None
    states: States
    messages: Iterable[Part]


RERUN_STATES = 100_000

CHART_STATES = 500


@dataclass(eq=False)
class View:
    state: Callable[..., Any] | None = None
    step: Callable[..., Any] | None = None
    group: Callable[..., Any] | None = None
    colors: dict[str, str] | None = None
    title: str | None = None


class CheckedView(View):
    pass


Shape = dict[str, list[str]]


@dataclass(eq=False)
class Walk:
    ids: list[str]
    states: list[State]
    index: dict[str, int]
    name_of: list[str]
    name_rank: list[int]
    from_: list[int]
    to: list[int]
    action: list[int]
    depth: list[int]
    via: list[int]
    reached: list[int]
    starts: list[int]


Hidden = None


@dataclass(eq=False)
class Answers:
    names: list[str]
    shapes: list[Shape]
    labels: list[str | None]
    group: Callable[[int], Any]


@dataclass(eq=False)
class Labels(Answers):
    drawn_labels: list[str] = field(default_factory=list)
    keys: list[list[str]] = field(default_factory=list)
    kinds: list[list[int]] = field(default_factory=list)
    sizes: list[int] = field(default_factory=list)
    sorted: list[int] = field(default_factory=list)
    path_step_index: dict[Step, int] = field(default_factory=dict)
    path_steps: list[int] = field(default_factory=list)
    together: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)


@dataclass(eq=False)
class StoryStep:
    state: Shape
    step: str | None = None


Story = list[StoryStep]


@dataclass(eq=False)
class ChartBreak:
    rule: Rule
    always: bool


@dataclass(eq=False)
class ChartState:
    path: list[str]
    start: bool
    members: list[int]
    works: bool
    lead: bool
    repeats: bool
    breaks: list[ChartBreak]
    group: Any


@dataclass(eq=False)
class Condition:
    kind: str
    other_keys: list[set[str]] = field(default_factory=list)
    other_tuples: set[str] = field(default_factory=set)


@dataclass(eq=False)
class Arrow:
    from_: str
    to: str
    label: str
    condition: Condition
    when: str | None = None


@dataclass(eq=False)
class ChartStep:
    from_: list[str]
    to: list[str]
    label: str
    when: str | None


@dataclass(eq=False)
class Region:
    name: str
    states: list[ChartState]
    steps: list[ChartStep]
    arrows: list[Arrow]


@dataclass(eq=False)
class Chart:
    title: str | None
    regions: list[Region]
    notes: list[str]
    inside: int
    quiet: int
    colors: dict[str, str]
    paths: list[str]
    loops: list[str]
    lie: str | None = None


class StatechartError(Exception):
    """An error whose message the command prints as it is."""


def is_record(v: object) -> bool:
    return isinstance(v, dict)


def is_strings(v: object) -> bool:
    return isinstance(v, list) and all(isinstance(s, str) for s in v)


PART = 1 << 24

by_text = js.by_text
text_key = js.text_key


def list_text(items: list[str], conjunction: str = "and") -> str:
    if len(items) < 2:
        return "".join(items)
    return f"{', '.join(items[:-1])} {conjunction} {items[-1]}"


_ESCAPES = {'"': '\\"', "\\": "\\\\", "\n": "\\n", "\t": "\\t", "\r": "\\r", "\f": "\\f"}
_QUOTE = str.maketrans(_ESCAPES)


def _quote(s: str) -> str:
    return f'"{s.translate(_QUOTE)}"'


def _joined(items: list[Value], sep: str) -> str:
    return sep.join(show(item) for item in items)


def show(v: Value) -> str:
    if v is True:
        return "TRUE"
    if v is False:
        return "FALSE"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return _quote(v)
    if isinstance(v, Model):
        return v.name
    if isinstance(v, Interval):
        return f"{v.lo}..{v.hi}"
    if isinstance(v, SetValue):
        return f"{{{_joined(v.members, ', ')}}}"
    if v.printed_as == "tuple":
        return f"<<{_joined(v.values, ', ')}>>"
    record = v.printed_as == "record"
    s = "[" if record else "("
    for i in range(len(v.keys)):
        if record:
            s += f"{', ' if i else ''}{js.string(v.keys[i])} |-> {show(v.values[i])}"
        else:
            s += f"{' @@ ' if i else ''}{show(v.keys[i])} :> {show(v.values[i])}"
    return s + ("]" if record else ")")


K = TypeVar("K")
V = TypeVar("V")


def must(mapping: Mapping[K, V], k: K) -> V:
    if k not in mapping:
        raise StatechartError(f"The chart lost track of {js.stringify_or_undefined(k)}.")
    return mapping[k]


def append(groups: dict[K, list[V]], k: K, item: V) -> None:
    group = groups.get(k)
    if group is not None:
        group.append(item)
    else:
        groups[k] = [item]


def seq_of(bug: Bug, index: Mapping[str, int]) -> list[int]:
    seq = [must(index, bug.start)]
    for p in bug.path:
        seq.append(must(index, p.state))
    return seq


def loop_of(bug: Bug, index: Mapping[str, int]) -> dict[int, None]:
    """The states of the bug's loop, in order (a JavaScript `Set` keeps insertion order)."""
    if bug.loop is None:
        return {}
    return dict.fromkeys(seq_of(bug, index)[bug.loop :])


def default_state(vars: Vars) -> str:
    entries = list(vars.items())
    if len(entries) == 1:
        return show(entries[0][1])
    return " ".join(f"{k}={show(v)}" for k, v in entries)


def state_text(vars: Vars) -> str:
    return " /\\ ".join(f"{k} = {show(v)}" for k, v in vars.items())


def count(n: int) -> list[int]:
    return list(range(n))


def sort_by(items: Iterable[int], keys: list[list[int]]) -> list[int]:
    """A stable sort by `keys[0]`, then `keys[1]`, and so on."""
    return sorted(items, key=lambda i: tuple(k[i] for k in keys))


def tuple_key(parts: list[Any]) -> str:
    return js.stringify(parts)


def unkey(k: str) -> list[str]:
    parts = json.loads(k)
    if not is_strings(parts):
        raise StatechartError(f"The chart cannot read the key {k}.")
    return parts


def holds(condition: Condition, others: list[str]) -> bool:
    if condition.kind == "and":
        return all(others[j] in condition.other_keys[j] for j in range(len(others)))
    if condition.kind == "or":
        return any(others[j] in condition.other_keys[j] for j in range(len(others)))
    return tuple_key(others) in condition.other_tuples


def rule_key(rule: Rule) -> str:
    return tuple_key([rule.kind, rule.name])


def has_rule(rules: list[Rule], rule: Rule) -> bool:
    return any(r.kind == rule.kind and r.name == rule.name for r in rules)


def _ascending(keys: list[str]) -> bool:
    return all(text_key(keys[i - 1]) <= text_key(keys[i]) for i in range(1, len(keys)))


def _span(lo: int, hi: int) -> str:
    return f"{lo}..{hi}" if hi > lo else str(lo)


def _set_key(members: list[Value]) -> str:
    ints: list[int] = []
    others: list[str] = []
    for m in members:
        if isinstance(m, int) and not isinstance(m, bool):
            ints.append(m)
        else:
            others.append(key(m))
    if any(ints[i - 1] >= ints[i] for i in range(1, len(ints))):
        ints.sort()
    if not _ascending(others):
        others.sort(key=text_key)
    s = "{"
    i = 0
    while i < len(ints):
        j = i
        while j + 1 < len(ints) and ints[j + 1] - ints[j] <= 1:
            j += 1
        s += f"{',' if len(s) > 1 else ''}{_span(ints[i], ints[j])}"
        i = j + 1
    for i, other in enumerate(others):
        if not i or other != others[i - 1]:
            s += ("," if len(s) > 1 else "") + other
    return s + "}"


def _function_key(v: Function) -> str:
    keys = v.keys
    key_texts = [key(k) for k in keys]
    ints = sum(1 for k in keys if isinstance(k, int) and not isinstance(k, bool))

    def rank(i: int) -> float:
        k = keys[i]
        return k if isinstance(k, int) and not isinstance(k, bool) else float("inf")

    order = sorted(range(len(keys)), key=lambda i: (rank(i), text_key(key_texts[i]), i))
    tuple_ = ints == len(keys)
    for i, k in enumerate(order):
        if not tuple_:
            break
        tuple_ = keys[k] == i + 1 and not isinstance(keys[k], bool)
    s = "<<" if tuple_ else "("
    kept = 0
    for i, k in enumerate(order):
        if i and key_texts[k] == key_texts[order[i - 1]]:
            continue
        text = key(v.values[k])
        if tuple_:
            s += f"{',' if kept else ''}{text}"
        else:
            s += f"{'@@' if kept else ''}{key_texts[k]}:>{text}"
        kept += 1
    return s + (">>" if tuple_ else ")")


def key(v: Value) -> str:
    if v is True:
        return "TRUE"
    if v is False:
        return "FALSE"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return js.stringify(v)
    if isinstance(v, Model):
        return v.name
    k = v._key
    if k is None:
        if isinstance(v, Interval):
            k = f"{{{'' if v.lo > v.hi else _span(v.lo, v.hi)}}}"
        elif isinstance(v, SetValue):
            k = _set_key(v.members)
        else:
            k = _function_key(v)
        v._key = k
    return k


def state_key(values: list[Value]) -> str:
    return ",".join(key(v) for v in values)


H = TypeVar("H", bound=Hashable)


def memo(make: Callable[[H], V], limit: int = 1 << 16) -> Callable[[H], V]:
    cache: dict[H, V] = {}

    def get(k: H) -> V:
        if k in cache:
            return cache[k]
        if len(cache) >= limit:
            cache.clear()
        v = cache[k] = make(k)
        return v

    return get


def values_of(vars: Vars, names: list[str]) -> list[Value]:
    return [vars[n] for n in names]


Find = Callable[[list[Value]], Any]


@dataclass(eq=False)
class FoundState:
    action: str
    vars: Vars
    values: list[Value]
    id: Any


def find_trace(
    counterexample: list[TraceState], names: list[str], rule: Rule, find: Find
) -> list[FoundState]:
    trace: list[FoundState] = []
    for t in counterexample:
        values = values_of(t.vars, names)
        trace.append(FoundState(t.action, t.vars, values, find(values)))
    end = len(trace) - 1
    if end < 0:
        raise StatechartError(f"TLC's trace for {rule.name} has no states.")
    for i in range(end):
        if trace[i].id is None:
            raise StatechartError(
                f"TLC's trace for {rule.name} has a state before its last that the dump does not list."
            )
    return trace


@dataclass(eq=False)
class FoundStep:
    action: str
    id: Any


def find_loop(trace: Trace, names: list[str], find: Find) -> tuple[list[FoundStep], int | None]:
    found = [
        FoundStep(s.action, None if s.vars is None else find(values_of(s.vars, names)))
        for s in trace.seq
    ]
    return found, trace.loop


def past_state(vars: Vars, start: bool, marked: Iterable[Rule], excluded: bool) -> State:
    breaks: list[Rule] = []
    for r in marked:
        if not has_rule(breaks, r):
            breaks.append(r)
    return State(vars, start, breaks, ends=[], past=True, excluded=excluded)


CHECK_DEADLOCK = "CHECK_DEADLOCK"


def _deadlock_rule(spec: Spec) -> Rule:
    named = "NoDeadlock" in spec.invariants or "NoDeadlock" in spec.properties
    return Rule("deadlock", CHECK_DEADLOCK if named else "NoDeadlock")


def has_section(spec: Spec, *keys: str) -> bool:
    return any(s.key in keys for s in spec.written)


def state_rules(spec: Spec) -> list[Rule]:
    rules = [Rule("invariant", name) for name in spec.invariants]
    if spec.deadlock:
        rules.append(_deadlock_rule(spec))
    return rules
