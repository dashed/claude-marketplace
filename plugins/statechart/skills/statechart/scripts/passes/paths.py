"""A graph of only the bug paths, for a model above the chart budget."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from ir import (
    Bug,
    Graph,
    Lasso,
    PathStep,
    Rule,
    State,
    StatechartError,
    Step,
    Trace,
    TraceSeqState,
    TraceState,
    Vars,
    has_rule,
    must,
    state_key,
)


@dataclass(eq=False)
class PathGraph:
    graph: Graph
    bug: Callable[[Rule, list[TraceState]], Bug]
    lasso: Callable[[Trace], Lasso | None]


def path_graph(names: list[str]) -> PathGraph:
    graph = Graph({}, [])
    ids: dict[str, str] = {}
    taken: dict[str, Step] = {}

    def id_of(vars: Vars | None, start: bool) -> str:
        if vars is None:
            raise StatechartError("TLC's trace has a state with no values.")
        k = state_key([vars[name] for name in names])
        id_ = ids.get(k)
        if id_ is None:
            id_ = ids[k] = str(len(ids))
            graph.states[id_] = State(vars, start, [])
        elif start:
            must(graph.states, id_).start = True
        return id_

    def route(seq: Sequence[TraceState | TraceSeqState]) -> tuple[str, list[PathStep]]:
        start = id_of(seq[0].vars, True)
        path: list[PathStep] = []
        from_ = start
        for i in range(1, len(seq)):
            action = seq[i].action
            to = id_of(seq[i].vars, False)
            k = f"{from_} {to} {action}"
            step = taken.get(k)
            if step is None:
                step = taken[k] = Step(from_, to, action)
                graph.steps.append(step)
            path.append(PathStep(action, to, step))
            from_ = to
        return start, path

    def bug(rule: Rule, trace: list[TraceState]) -> Bug:
        if not trace:
            raise StatechartError(f"TLC's trace for {rule.name} has no states.")
        start, path = route(trace)
        found = Bug(rule, start, path)
        end = must(graph.states, path[-1].state if path else start)
        if not has_rule(end.breaks, rule):
            end.breaks.append(rule)
        return found

    def lasso(trace: Trace) -> Lasso | None:
        if not trace.seq:
            return None
        start, path = route(trace.seq)
        return Lasso(start, path, trace.loop, trace.loop == len(trace.seq) - 1)

    return PathGraph(graph, bug, lasso)
