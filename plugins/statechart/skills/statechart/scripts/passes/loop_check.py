"""Refuse a chart that draws a way out of a bug's loop that the loop cannot take."""

from __future__ import annotations

from ir import (
    Arrow,
    Bug,
    Chart,
    Labels,
    StatechartError,
    Walk,
    append,
    holds,
    loop_of,
    must,
    tuple_key,
    unkey,
)


def loop_check(chart: Chart, labels: Labels, walked: Walk, found: list[Bug]) -> None:
    names = labels.names
    keys = labels.keys
    drawn_labels = labels.drawn_labels
    index = walked.index
    from_ = walked.from_
    to = walked.to
    regions = len(names)

    def combo(i: int) -> str:
        return tuple_key([keys[r][i] for r in range(regions)])

    steps_from: dict[int, list[int]] = {}
    arrows_from: list[dict[str, list[Arrow]]] = []
    if chart.loops:
        for j in labels.sorted:
            append(steps_from, from_[j], j)
        for region in chart.regions:
            out: dict[str, list[Arrow]] = {}
            for a in region.arrows:
                append(out, a.from_, a)
            arrows_from.append(out)
    for b in found:
        if b.loop is None:
            continue
        in_loop: set[str] = set()
        twins_of: dict[str, list[int]] = {}
        for i in loop_of(b, index):
            in_loop.add(combo(i))
            append(twins_of, combo(i), i)
        for i in loop_of(b, index):
            twins = must(twins_of, combo(i))
            for r, name in enumerate(names):

                def takes(a: Arrow, r: int = r, twins: list[int] = twins) -> bool:
                    for s in twins:
                        for j in steps_from.get(s, []):
                            if drawn_labels[j] == a.label and keys[r][to[j]] == a.to:
                                return True
                    return False

                rest = [keys[o][i] for o in range(regions) if o != r]
                for a in arrows_from[r].get(keys[r][i], []):
                    if not holds(a.condition, rest):
                        continue
                    following = [a.to if o == r else keys[o][i] for o in range(regions)]
                    if tuple_key(following) not in in_loop and not takes(a):
                        where = f"{name} " if name else ""
                        raise StatechartError(
                            f"The chart draws the step {a.label} out of {where}"
                            f"{' / '.join(unkey(a.from_))}, but the {b.rule.name} loop cannot "
                            "take it there. Show in a label what stops it."
                        )
