"""From TLC's results to the files that the command writes."""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from backends.mermaid import mermaid_lines
from backends.plain_text import plain_text
from backends.report import report
from ir import (
    PART,
    Answers,
    Bug,
    Chart,
    CheckedView,
    CheckResult,
    Graph,
    Labels,
    StoryStep,
    View,
    Walk,
    rule_key,
)
from passes.label import as_parents, ask, label_graph, stories_of
from passes.lift import lift
from passes.loop_check import loop_check
from passes.reach import bugs, draw_order, walk
from passes.region_check import regions_lie
from passes.regions import draw_regions


def _in_parts(lines: list[str]) -> Iterator[str]:
    start = 0
    size = 0
    for i, line in enumerate(lines):
        size += len(line) + 1
        if size > PART or i == len(lines) - 1:
            yield ("\n" if start else "") + "\n".join(lines[start : i + 1])
            start = i + 1
            size = 0


def project(
    graph: Graph, walked: Walk, view: View, found: list[Bug]
) -> tuple[Chart, dict[Bug, list[StoryStep]]]:
    order, rank = draw_order(walked)

    def draw(answers: Answers) -> tuple[Labels, Chart]:
        labels = label_graph(graph, walked, answers, rank, found)
        return labels, draw_regions(walked, labels, order, found, view)

    answers = ask(graph, walked, view)
    first_labels, first_chart = draw(answers)
    lie = regions_lie(first_chart.regions, first_labels, walked, order)
    labels, chart = draw(as_parents(walked, answers)) if lie else (first_labels, first_chart)
    loop_check(chart, labels, walked, found)
    lifted = lift(dataclasses.replace(chart, lie=lie) if lie else chart)
    return lifted, stories_of(graph, found, walked, first_labels)


@dataclass(eq=False)
class Compiled:
    report: str
    files: dict[str, Iterable[str | bytes]]
    exit: int


def compile_result(result: CheckResult, view: CheckedView) -> Compiled:
    walked = walk(result.graph)
    found = sorted(
        result.paths if result.paths is not None else bugs(result.graph, walked),
        key=lambda b: len(b.path),
    )
    for p in result.properties:
        if p.bug:
            found.append(
                Bug(p.rule, p.bug.start, p.bug.path, loop=p.bug.loop, stutters=p.bug.stutters)
            )
    chart: Chart | None
    stories: dict[Bug, list[StoryStep]]
    if found or result.paths is None:
        chart, stories = project(result.graph, walked, view, found)
    else:
        chart, stories = None, {}
    text = report(result, found, chart, stories)
    files: dict[str, Iterable[str | bytes]] = {}
    if chart:
        files["chart.mmd"] = _in_parts(mermaid_lines(chart))
    files["report.md"] = [text]
    files["tlc.out"] = plain_text(result.messages)
    drawn = {rule_key(b.rule) for b in found if b.rule.kind != "property"}
    for v in [*result.rules, *result.properties]:
        if v.outcome == "broken" and v.messages and rule_key(v.rule) not in drawn:
            files[f"tlc-{v.rule.name}.out"] = plain_text(v.messages)
    return Compiled(text, files, result.exit)
