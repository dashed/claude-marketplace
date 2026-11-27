"""Write report.md."""

from __future__ import annotations

from dataclasses import dataclass

import js
from ir import (
    CHART_STATES,
    RERUN_STATES,
    AssumptionCheck,
    Bug,
    Chart,
    CheckResult,
    StoryStep,
    has_section,
    list_text,
    must,
    rule_key,
)


@dataclass(eq=False)
class _Told:
    step: str | None
    state: str


def _steps_of(story: list[StoryStep]) -> list[_Told]:
    path: list[_Told] = []
    for s in story:
        parts = [
            (f"{name} " if name else "") + " / ".join(names) for name, names in s.state.items()
        ]
        path.append(_Told(s.step, ", ".join(parts)))
    return path


def _forever(loop: list[_Told], stutters: bool | None) -> str:
    runs = list(dict.fromkeys(f'"{p.state}"' for p in loop))
    if stutters:
        return f"The run stops in {runs[0]} forever."
    if len(runs) == 1:
        return f"The run stays in {runs[0]} forever."
    return f"The run loops through {list_text(runs)} forever."


def _fenced(text: str) -> str:
    return "\n".join(["```", text, "```"])


def _states(n: int) -> str:
    return f"{n:,}"


def _unchecked_tail(ac: AssumptionCheck, target: str) -> str:
    names = list_text(ac.not_checked)
    if ac.cut:
        return (
            f"Without {target}, TLC reached the {_states(RERUN_STATES)}-state bound "
            f"before checking {names}."
        )
    if ac.stop:
        return (
            f"Without {target}, TLC stopped with exit {js.string(ac.stop.status)} "
            f"before checking {names}."
        )
    return f"Without {target}, {names} could not be checked."


def report(
    result: CheckResult,
    found: list[Bug],
    chart: Chart | None,
    stories: dict[Bug, list[StoryStep]],
) -> str:
    spec = result.spec
    graph = result.graph
    paths = result.paths
    states = result.states
    drawing = result.drawing
    size = 0
    arrows = 0
    for r in chart.regions if chart else []:
        size += len(r.states)
        arrows += len(r.steps)
    past = 0
    past_steps = 0
    excluded = 0
    for s in graph.states.values():
        if s.excluded:
            excluded += 1
        elif s.past:
            past += 1
    for t in graph.steps:
        if must(graph.states, t.to).past:
            past_steps += 1

    def includes(n: int) -> str:
        return f", and the chart includes {'it' if n == 1 else 'them'}" if chart else ""

    if paths is not None:
        reached = (
            f"{_states(states.distinct)} states, more than"
            if states.complete and not states.cut and states.distinct > CHART_STATES
            else "more states than"
        )
        drawn = (
            f"the chart draws only the bug paths: {size} states and {arrows} arrows"
            if chart
            else "the command wrote no chart.mmd"
        )
        summary = f"TLC reached {reached} the chart budget of {CHART_STATES}, so {drawn}."
    else:
        summary = (
            f"TLC reached {len(graph.states) - past - excluded} states and "
            f"{len(graph.steps) - past_steps} steps. The chart draws {size} states and "
            f"{arrows} arrows."
        )
    out = [f"# {spec.module}", "", summary]
    if drawing:
        out.append(
            f"TLC stopped the drawing run with exit {js.string(drawing.status)}, so the chart draws only "
            "the states that it reached before it stopped."
        )
    if paths is None and not drawing and len(graph.states) == past + excluded:
        out.append(
            "Every initial state is outside the constraints, so TLC explores none of them."
            if states.initial
            else "TLC found no state that satisfies Init, so no state can break a rule."
        )
    if past:
        ends = (
            "1 state outside the constraints ends"
            if past == 1
            else f"{past} states outside the constraints each end"
        )
        out.append(
            f"{ends} a rule's path{includes(past)}. TLC checks the rules in a state outside the "
            "constraints, but it does not explore past it."
        )
    if excluded:
        ends = (
            "1 step that the constraints exclude ends"
            if excluded == 1
            else f"{excluded} steps that the constraints exclude each end"
        )
        out.append(
            f"{ends} a rule's path{includes(excluded)}. TLC checks the rules after such a step, "
            "but it does not take the step."
        )
    if chart and chart.inside:
        out.append(f"The chart does not draw {chart.inside} steps that stay in one chart state.")
    if chart and chart.quiet:
        out.append(f"The view hides {chart.quiet} steps, so the chart does not draw them.")
    for v in result.rules:
        if (
            paths is None
            and v.rule.kind == "deadlock"
            and v.outcome == "broken"
            and (drawing or has_section(spec, "CONSTRAINT", "ACTION_CONSTRAINT"))
        ):
            out.append(
                "The chart marks only the deadlock that TLC reports, because the drawing run "
                "stopped before it reached every state."
                if drawing
                else "The chart marks only the deadlock that TLC reports. Under a CONSTRAINT or an "
                "ACTION_CONSTRAINT, a state with no step in the chart can still have steps that "
                "the constraints leave out, and TLC does not count it as a deadlock."
            )
    if chart and chart.lie:
        out.append(f"{chart.lie} So the chart draws parent states in place of regions.")
    out.extend(chart.notes if chart else [])
    merged = [k for k in ("VIEW", "SYMMETRY") if has_section(spec, k)]
    if chart and merged:
        out.append(
            f"With {list_text(merged)}, TLC keeps one representative for each group of states "
            "that it counts as the same. An arrow can lead to the representative rather than to "
            "the state that the step reaches."
        )
    for bug in found:
        steps = f"{len(bug.path)} step{'' if len(bug.path) == 1 else 's'}"
        out.extend(["", f"## {bug.rule.name} breaks"])
        out.append(
            f"TLC's counterexample is in tlc-{bug.rule.name}.out. It has {steps}:"
            if bug.rule.kind == "property"
            else f"The shortest path has {steps}:"
        )
        path = _steps_of(must(stories, bug))
        for i, p in enumerate(path):
            out.append(f"{i}. {f'{p.step}: ' if p.step else ''}{p.state}")
        if bug.loop is not None:
            out.append(_forever(path[bug.loop :], bug.stutters))
    drawn_rules = {rule_key(b.rule) for b in found}
    holds: list[str] = []
    unchecked: list[str] = []
    for v in [*result.rules, *result.properties]:
        if v.outcome == "holds":
            holds.append(v.rule.name)
        elif v.outcome == "not checked":
            unchecked.append(v.rule.name)
        elif v.messages and rule_key(v.rule) not in drawn_rules:
            out.extend(
                [
                    "",
                    f"## {v.rule.name} breaks",
                    f"TLC found a counterexample. It is in tlc-{v.rule.name}.out.",
                ]
            )
    if holds:
        out.extend(["", "## Rules that hold", ", ".join(holds)])
    if unchecked:
        out.extend(["", "## Rules not checked", ", ".join(unchecked)])
    these = "this rule" if len(unchecked) == 1 else "these rules"
    if unchecked and states.cut:
        out.append(
            f"After the first break, each TLC run stops at {_states(RERUN_STATES)} distinct "
            f"states. A run reached that bound before it checked {these} in every state."
        )
    stop = result.stop
    if stop:
        if unchecked:
            out.append(f"TLC stopped with exit {js.string(stop.status)} before it checked {these}:")
        else:
            out.extend(["", "## TLC stopped", f"TLC stopped with exit {js.string(stop.status)}:"])
        out.append(_fenced(stop.message))
    for p in result.properties:
        if p.outcome == "holds" and p.initial_only:
            out.append(
                f"TLC checked {p.rule.name} only in the initial states, because it has no [], "
                "<>, or ~>. List it as an INVARIANT to check every state."
            )
    if result.assumptions:
        out.extend(["", "## Assumptions"])
        for ac in result.assumptions:
            target = ac.names[0] if len(ac.names) == 1 else f"{list_text(ac.names)} together"
            if ac.broken:
                verb = "holds" if len(ac.broken) == 1 else "hold"
                line = f"- {list_text(ac.broken)} {verb} only under {target}."
                if ac.not_checked:
                    line += f" {_unchecked_tail(ac, target)}"
                out.append(line)
            elif ac.not_checked:
                out.append(f"- {_unchecked_tail(ac, target)}")
            else:
                out.append(f"- Every holding rule still holds without {target}.")
            if ac.stop:
                out.append(_fenced(ac.stop.message))
    return "\n".join(out)
