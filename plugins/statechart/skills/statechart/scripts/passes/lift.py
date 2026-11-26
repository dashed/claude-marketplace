"""Move a step that every child of a parent takes up to the parent."""

from __future__ import annotations

import dataclasses

from ir import Chart, ChartState, ChartStep, Region, append, must, tuple_key, unkey


def lift_to_parents(states: list[ChartState], steps: list[ChartStep]) -> list[ChartStep]:
    depths: dict[str, int] = {}
    leaves: dict[str, int] = {}
    for s in states:
        for i in range(1, len(s.path)):
            prefix = tuple_key(s.path[:i])
            depths[prefix] = i
            leaves[prefix] = leaves.get(prefix, 0) + 1
    if not depths:
        return steps
    leaving: dict[str, list[ChartStep]] = {}
    for s in steps:
        same = 0
        while same < len(s.from_) and same < len(s.to) and s.from_[same] == s.to[same]:
            same += 1
        for i in range(1, len(s.from_)):
            if i <= same and i < len(s.to):
                continue
            prefix = tuple_key(s.from_[:i])
            if prefix in depths:
                append(leaving, prefix, s)
    removed: set[ChartStep] = set()
    lifted: list[ChartStep] = []
    for prefix, _depth in sorted(depths.items(), key=lambda entry: entry[1]):
        groups: dict[str, list[ChartStep]] = {}
        for s in leaving.get(prefix, []):
            if s not in removed:
                append(groups, tuple_key([s.label, s.when, s.to]), s)
        under = must(leaves, prefix)
        for group in groups.values():
            if under < 2 or len(group) < under:
                continue
            removed.update(group)
            lifted.append(dataclasses.replace(group[0], from_=unkey(prefix)))
    kept = [s for s in steps if s not in removed]
    kept.extend(lifted)
    return kept


def lift(chart: Chart) -> Chart:
    regions: list[Region] = []
    for r in chart.regions:
        known: dict[int, int] = {}
        for s in r.states:
            known[id(s.path)] = len(known)
        numbers: dict[str, int] | None = None
        held: list[list[str]] = []

        def path_index(path: list[str], r: Region = r) -> int:
            nonlocal numbers
            i = known.get(id(path))
            if i is not None:
                return i
            if numbers is None:
                numbers = {}
                for s in r.states:
                    numbers[tuple_key(s.path)] = len(numbers)
            k = tuple_key(path)
            i = numbers.get(k)
            if i is None:
                i = numbers[k] = len(numbers)
            known[id(path)] = i
            held.append(path)
            return i

        merged: dict[int | str, ChartStep] = {}
        for s in lift_to_parents(r.states, r.steps):
            f = path_index(s.from_)
            t = path_index(s.to)
            k: int | str = (
                f * 2**26 + t
                if s.when is None and f < 2**26 and t < 2**26
                else f"{f},{t}:{'undefined' if s.when is None else s.when}"
            )
            prior = merged.get(k)
            if prior is not None:
                prior.label += f" or {s.label}"
            else:
                merged[k] = dataclasses.replace(s)
        regions.append(dataclasses.replace(r, steps=list(merged.values())))
    return dataclasses.replace(chart, regions=regions)
