"""Draw one region for each key of the view's state()."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

import js
from ir import (
    Arrow,
    Bug,
    Chart,
    ChartBreak,
    ChartState,
    ChartStep,
    Condition,
    Labels,
    Region,
    Rule,
    StatechartError,
    View,
    Walk,
    append,
    has_rule,
    holds,
    loop_of,
    must,
    rule_key,
    seq_of,
    text_key,
    tuple_key,
    unkey,
)

_ANY_REST = Condition("and", [])


@dataclass(eq=False)
class _RegionMove:
    f: int
    t: int
    text: str
    group: list[int] = field(default_factory=list)
    other: _RegionMove | None = None


def draw_regions(
    walked: Walk, labels: Labels, order: list[int], found: list[Bug], view: View
) -> Chart:
    tla = walked.states
    index = walked.index
    from_ = walked.from_
    to = walked.to
    names = labels.names
    shapes = labels.shapes
    drawn_labels = labels.drawn_labels
    keys = labels.keys
    kinds = labels.kinds
    sizes = labels.sizes
    sorted_ = labels.sorted
    path_steps = labels.path_steps
    n = len(shapes)
    m = len(drawn_labels)
    regions_count = len(names)
    lead = [0] * n
    looped = [0] * n
    for b in found:
        seq = seq_of(b, index)
        for i in seq if b.loop is None else seq[: b.loop]:
            lead[i] = 1
        for i in loop_of(b, index):
            looped[i] = 1

    def loop(j: int) -> bool:
        return regions_count == 1 and path_steps[j] == 1

    def stays(j: int) -> bool:
        return all(kinds[r][from_[j]] == kinds[r][to[j]] for r in range(regions_count))

    inside = sum(1 for j in sorted_ if stays(j) and not loop(j))

    def combo_of(i: int) -> int | str:
        if regions_count == 1:
            return kinds[0][i]
        return ",".join(str(kinds[r][i]) for r in range(regions_count))

    dirty: dict[int | str, int] = {}
    for i in order:
        if tla[i].breaks:
            c = combo_of(i)
            if c not in dirty:
                dirty[c] = i
    clean = [0 if dirty and combo_of(i) in dirty else 1 for i in range(n)]
    regions: list[Region] = []
    objects: list[list[ChartState | None]] = []
    for r, name in enumerate(names):
        key = keys[r]
        kind = kinds[r]
        states: dict[str, ChartState] = {}
        object_of: list[ChartState | None] = [None] * sizes[r]
        key_of: list[str] = [""] * sizes[r]
        position = [0] * sizes[r]
        for i in order:
            s = tla[i]
            o = object_of[kind[i]]
            if o is None:
                o = ChartState(
                    path=shapes[i][name],
                    start=False,
                    members=[],
                    works=False,
                    lead=False,
                    repeats=False,
                    breaks=[],
                    group=None,
                )
                object_of[kind[i]] = o
                key_of[kind[i]] = key[i]
                position[kind[i]] = len(states)
                states[key[i]] = o
            o.start = o.start or s.start
            o.works = o.works or clean[i] == 1
            o.lead = o.lead or lead[i] == 1
            o.repeats = o.repeats or looped[i] == 1
            o.members.append(i)
        parents: set[str] = set()
        for s in states.values():
            for i in range(1, len(s.path)):
                parents.add(tuple_key(s.path[:i]))
        for s in states.values():
            if parents and tuple_key(s.path) in parents:
                where = f" in {name}" if name else ""
                raise StatechartError(
                    f"The view's state() returned {' / '.join(s.path)} both as a state and as a "
                    f"parent state{where}. Give that state a child name of its own."
                )
            rules: dict[str, Rule] = {}
            for i in s.members:
                for rule in tla[i].breaks:
                    rules[rule_key(rule)] = rule
            s.breaks = []
            for rule in sorted(rules.values(), key=lambda a: (text_key(a.name), text_key(a.kind))):
                always = all(has_rule(tla[i].breaks, rule) for i in s.members)
                s.breaks.append(ChartBreak(rule, always))
            groups: dict[object, Any] = {}
            for i in s.members:
                g = labels.group(i)
                groups.setdefault(js.same_value(g), g)
            s.group = next(iter(groups.values())) if len(groups) == 1 else None
        others = [o for o in range(regions_count) if o != r]

        def tuple_(i: int, others: list[int] = others) -> list[str]:
            return [keys[o][i] for o in others]

        two = len(others) == 1

        def words(vs: Iterable[str], two: bool = two) -> str:
            texts = sorted((" / ".join(unkey(v)) for v in vs), key=text_key)
            return (" or " if two else ", ").join(texts)

        def is_(o: int, vs: set[str], two: bool = two) -> str:
            if two:
                return f"when {words(vs)}"
            return f"{names[o]} is {'one of ' if len(vs) > 1 else ''}{words(vs)}"

        def is_not(o: int, vs: list[str], two: bool = two) -> str:
            if two:
                return f"unless {words(vs)}"
            return f"{names[o]} is {'none of' if len(vs) > 1 else 'not'} {words(vs)}"

        moves: list[_RegionMove] = []
        pairs: dict[int, _RegionMove] = {}
        size = sizes[r]
        for j in sorted_:
            f = kind[from_[j]]
            t = kind[to[j]]
            if f == t and not loop(j):
                continue
            text = drawn_labels[j]
            pair = position[f] * size + position[t]
            move = pairs.get(pair)
            while move is not None and move.text != text:
                move = move.other
            if move is None:
                move = _RegionMove(f, t, text, [], pairs.get(pair))
                pairs[pair] = move
                moves.append(move)
            if regions_count > 1:
                move.group.append(j)
        tuples_at: dict[int, list[int]] = {}
        seen_at: dict[int, list[list[str]]] = {}
        if regions_count > 1:
            for i in order:
                append(tuples_at, kind[i], i)
        arrows: list[Arrow] = []
        for move in moves:
            from_key = key_of[move.f]
            to_key = key_of[move.t]
            if regions_count == 1:
                arrows.append(Arrow(from_key, to_key, move.text, _ANY_REST, None))
                continue
            ok = {tuple_key(tuple_(from_[j])) for j in move.group}

            def takes(t: list[str], ok: set[str] = ok) -> bool:
                return tuple_key(t) in ok

            seen = seen_at.get(move.f)
            if seen is None:
                seen = []
                seen_keys: set[str] = set()
                for i in must(tuples_at, move.f):
                    t = tuple_(i)
                    k = tuple_key(t)
                    if k in seen_keys:
                        continue
                    seen_keys.add(k)
                    seen.append(t)
                seen_at[move.f] = seen
            all_: list[dict[str, None]] = []
            and_: list[set[str]] = []
            or_: list[set[str]] = []
            for j in range(len(others)):
                values: dict[str, None] = {}
                taken: set[str] = set()
                untaken: set[str] = set()
                for t in seen:
                    values[t[j]] = None
                    if takes(t):
                        taken.add(t[j])
                    else:
                        untaken.add(t[j])
                only = {v for v in values if v not in untaken}
                all_.append(values)
                and_.append(taken)
                or_.append(only)

            def fits(condition: Condition, seen: list[list[str]] = seen) -> bool:
                return all(holds(condition, t) == takes(t) for t in seen)

            and_holds = Condition("and", and_)
            or_holds = Condition("or", or_)
            text = move.text
            if fits(and_holds):
                parts: list[str] = []
                for j in range(len(others)):
                    no = [v for v in all_[j] if v not in and_[j]]
                    if no:
                        parts.append(
                            is_(others[j], and_[j])
                            if len(and_[j]) <= len(no)
                            else is_not(others[j], no)
                        )
                when = (parts[0] if two else f"when {' and '.join(parts)}") if parts else None
                arrows.append(Arrow(from_key, to_key, text, and_holds, when))
            elif fits(or_holds):
                parts = [is_(others[j], or_[j]) for j in range(len(others)) if or_[j]]
                arrows.append(Arrow(from_key, to_key, text, or_holds, f"when {' or '.join(parts)}"))
            else:
                arrows.append(Arrow(from_key, to_key, text, Condition("tuples", other_tuples=ok)))
        steps: list[ChartStep] = []
        for k, a in enumerate(arrows):
            source = object_of[moves[k].f]
            target = object_of[moves[k].t]
            assert source is not None and target is not None
            steps.append(
                ChartStep(
                    source.path, target.path, a.label, None if a.label.endswith("]") else a.when
                )
            )
        regions.append(Region(name, list(states.values()), steps, arrows))
        objects.append(object_of)
    hidden: list[list[ChartState]] = []
    for i in dirty.values():
        ps = [s for r in range(regions_count) if (s := objects[r][kinds[r][i]]) is not None]
        if all(s.works for s in ps):
            hidden.append(ps)
    for ps in hidden:
        for s in ps:
            s.works = False
    paths: list[str] = []
    loops: list[str] = []
    for b in found:
        if b.loop != 0:
            paths.append(b.rule.name)
        if b.loop is not None:
            loops.append(b.rule.name)
    return Chart(
        title=view.title,
        regions=regions,
        notes=labels.notes,
        inside=inside,
        quiet=m - len(sorted_),
        colors=view.colors or {},
        paths=paths,
        loops=loops,
    )
