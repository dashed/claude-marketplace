"""Say how a regions chart misstates the model, if it does."""

from __future__ import annotations

from dataclasses import dataclass

from ir import Arrow, Labels, Region, Walk, append, holds, tuple_key, unkey


@dataclass(eq=False)
class _Move:
    from_: list[str]
    text: str
    to: list[str]


@dataclass(eq=False)
class _Enabled:
    i: int
    a: Arrow


def regions_lie(
    regions: list[Region], labels: Labels, walked: Walk, order: list[int]
) -> str | None:
    names = labels.names
    keys = labels.keys
    drawn_labels = labels.drawn_labels
    together = labels.together
    from_ = walked.from_
    to = walked.to
    if len(names) < 2:
        return None

    def combo(i: int) -> list[str]:
        return [keys[r][i] for r in range(len(names))]

    def words(c: list[str]) -> str:
        return ", ".join(f"{names[i]} {' / '.join(unkey(c[i]))}" for i in range(len(names)))

    def add_move(moves: dict[str, _Move], m: _Move) -> None:
        moves[tuple_key([m.from_, m.text, m.to])] = m

    product: list[list[str]] = [[]]
    for r in regions:
        product = [[*c, tuple_key(s.path)] for c in product for s in r.states if s.start]
    real_starts = {tuple_key(combo(i)) for i in walked.starts}
    for c in product:
        if tuple_key(c) not in real_starts:
            return f"The regions chart starts at {words(c)}, where the model never starts."
    for i, r in enumerate(regions):
        for a in r.arrows:
            if a.condition.kind == "tuples":
                return (
                    f"In {names[i]}, {a.label} from {' / '.join(unkey(a.from_))} depends on the "
                    'other regions in a way that one "and" or "or" condition cannot say.'
                )
    real: dict[str, _Move] = {}
    for j in labels.sorted:
        before = combo(from_[j])
        after = combo(to[j])
        if tuple_key(before) != tuple_key(after):
            add_move(real, _Move(before, drawn_labels[j], after))
    combos: dict[str, list[str]] = {}
    for i in order:
        c = combo(i)
        combos[tuple_key(c)] = c
    drawn: dict[str, _Move] = {}
    for c in combos.values():
        enabled: dict[str, list[_Enabled]] = {}
        for i, r in enumerate(regions):
            rest = [c[k] for k in range(len(c)) if k != i]
            for a in r.arrows:
                if a.from_ == c[i] and holds(a.condition, rest):
                    append(enabled, a.label, _Enabled(i, a))
        for text, options in enabled.items():
            groups: list[list[_Enabled]] = []
            if text in together:
                by_region: dict[int, list[_Enabled]] = {}
                for m in options:
                    append(by_region, m.i, m)
                groups = [[]]
                for opts in by_region.values():
                    groups = [[*g, m] for g in groups for m in opts]
            else:
                groups = [[m] for m in options]
            for group in groups:
                target = list(c)
                for e in group:
                    target[e.i] = e.a.to
                add_move(drawn, _Move(c, text, target))
    for k, extra in drawn.items():
        if k not in real:
            return (
                f"The regions chart lets {words(extra.from_)} go to {words(extra.to)} by "
                f"{extra.text}, which the model never does."
            )
    for k, missing in real.items():
        if k not in drawn:
            return (
                f"The model goes from {words(missing.from_)} to {words(missing.to)} by "
                f"{missing.text}, which the regions chart cannot show."
            )
    return None
