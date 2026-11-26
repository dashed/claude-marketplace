"""Mark the states that break a rule, and add the states past a bound."""

from __future__ import annotations

from collections.abc import Iterable

from ir import (
    Graph,
    Lasso,
    Mark,
    PathStep,
    Rule,
    Step,
    Trace,
    TraceState,
    Value,
    find_loop,
    find_trace,
    has_rule,
    must,
    past_state,
    state_key,
    values_of,
)

Past = dict[str, list[Rule]]


class Finder:
    """The id of the state with the given values."""

    def __init__(self, graph: Graph, names: list[str]) -> None:
        self._graph = graph
        self._names = names
        self._ids: dict[str, str] | None = None

    def __call__(self, values: list[Value]) -> str | None:
        if self._ids is None:
            self._ids = {}
            for id_, s in self._graph.states.items():
                if not s.excluded:
                    self._ids[state_key(values_of(s.vars, self._names))] = id_
        return self._ids.get(state_key(values))

    def add(self, id_: str, values: list[Value]) -> None:
        if self._ids is not None:
            self._ids[state_key(values)] = id_


def finder(graph: Graph, names: list[str]) -> Finder:
    return Finder(graph, names)


def _add_once(rules: list[Rule], rule: Rule) -> list[Rule]:
    if not any(r is rule for r in rules):
        rules.append(rule)
    return rules


def mark(
    graph: Graph,
    marks: Iterable[Mark],
    names: list[str],
    rules: list[Rule],
    find: Finder | None = None,
) -> Past:
    if find is None:
        find = finder(graph, names)
    by_name = {rule.name: rule for rule in rules}
    past: Past = {}
    for m in marks:
        id_ = find(m.values)
        state = None if id_ is None else graph.states.get(id_)
        for name in m.broken:
            rule = must(by_name, name)
            if state:
                state.breaks.append(rule)
            else:
                k = state_key(m.values)
                past[k] = _add_once(past.get(k, []), rule)
    return past


def dead_ends(graph: Graph, rule: Rule) -> None:
    from_ = {t.from_ for t in graph.steps}
    for id_, s in graph.states.items():
        if not s.past and id_ not in from_:
            s.breaks.append(rule)


def add_past(
    graph: Graph,
    counterexample: list[TraceState],
    names: list[str],
    rule: Rule,
    past: Past,
    excludes: bool,
    find: Finder | None = None,
) -> None:
    if find is None:
        find = finder(graph, names)
    trace = find_trace(counterexample, names, rule, find)
    end = len(trace) - 1
    from_ = trace[end - 1].id if end >= 1 else None
    action = trace[end].action

    def taken(to: str | None) -> bool:
        return any(t.from_ == from_ and t.to == to and t.action == action for t in graph.steps)

    to = trace[end].id
    reached = None if to is None else graph.states.get(to)
    excluded = excludes and reached is not None and end > 0 and not reached.past and not taken(to)
    if excluded:
        to = f"past {to} {action} {from_ if from_ is not None else 'undefined'}"
    if to is None:
        to = f"past {len(graph.states)}"
    last = graph.states.get(to)
    if last is None:
        marked = (
            reached.breaks
            if excluded and reached is not None
            else past.get(state_key(trace[end].values), [])
        )
        last = past_state(trace[end].vars, end == 0, marked, bool(excluded))
        graph.states[to] = last
        if not excluded:
            find.add(to, trace[end].values)
    if not has_rule(last.breaks, rule):
        last.breaks.append(rule)
    if last.ends is None:
        last.ends = []
    last.ends.append(rule)
    if from_ is not None and last.past and not taken(to):
        graph.steps.append(Step(from_, to, action))


def lasso(graph: Graph, trace: Trace, names: list[str], find: Finder | None = None) -> Lasso | None:
    if find is None:
        find = finder(graph, names)
    seq, loop = find_loop(trace, names, find)
    start = seq[0].id if seq else None
    if start is None:
        return None
    out: dict[object, list[Step]] = {}
    for s in seq:
        out[s.id] = []
    for t in graph.steps:
        if t.from_ in out:
            out[t.from_].append(t)
    route: list[PathStep] = []
    for i in range(1, len(seq)):
        step: Step | None = None
        for t in out.get(seq[i - 1].id, []):
            if t.to == seq[i].id and t.action == seq[i].action:
                step = t
                break
        if step is None:
            return None
        route.append(PathStep(step.action, step.to, step))
    return Lasso(start, route, loop, loop == len(seq) - 1)
