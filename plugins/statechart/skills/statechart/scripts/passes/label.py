"""Ask the view for the reader's words and group the steps by them."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any, NoReturn, TypeGuard

import js
from ir import (
    Answers,
    Bug,
    Graph,
    Labels,
    Shape,
    StatechartError,
    Step,
    StoryStep,
    Vars,
    View,
    Walk,
    key,
    list_text,
    loop_of,
    must,
    sort_by,
    state_text,
    tuple_key,
)

_ARTIFACT = re.compile(r"\bundefined\b|\bNaN\b|\[object Object\]", re.ASCII)


def _is_label(label: object) -> TypeGuard[str]:
    return isinstance(label, str) and label != "" and not _ARTIFACT.search(label)


def _shape_of(shape: object, vars: Vars) -> Shape:
    def fail() -> NoReturn:
        raise StatechartError(
            f"The view's state() returned {shape!r} for the state "
            f"{state_text(vars)}. Return a string, a list of strings, or a dict of those."
        )

    def path(p: object) -> list[str]:
        labels: list[str] = []
        for label in p if isinstance(p, (list, tuple)) else [p]:
            if not _is_label(label):
                fail()
            labels.append(label)
        if not labels:
            fail()
        return labels

    regions: list[tuple[str, object]]
    if isinstance(shape, dict):
        regions = list(js.object_order({js.string(k): v for k, v in shape.items()}).items())
    else:
        regions = [("", shape)]
    pairs = [(k, path(v)) for k, v in regions]
    if not pairs:
        fail()
    return dict(pairs)


def _step_of(view: View) -> Callable[[str, Vars, Vars], str | None]:
    def step(action: str, from_: Vars, to: Vars) -> str | None:
        label = view.step(action, from_, to) if view.step else action
        if label is None or _is_label(label):
            return label
        raise StatechartError(f"The view's step() returned {label!r} for the step {action}.")

    return step


def _unlabeled(action: str, before: Vars, after: Vars, bug: Bug) -> NoReturn:
    changed = [k for k in after if key(before[k]) != key(after[k])]
    loop = "" if bug.loop is None else " or leaves its loop"
    raise StatechartError(
        f"The view's step() returned None for the step {action} that changes "
        f"{', '.join(changed) or 'nothing'}. It is on the path to the {bug.rule.name} bug{loop}, "
        "so label it."
    )


def ask(graph: Graph, walked: Walk, view: View) -> Answers:
    tla = walked.states
    n = len(walked.name_of)
    m = len(walked.from_)
    state = view.state
    shapes = [
        _shape_of(state(tla[i].vars) if state else walked.name_of[i], tla[i].vars) for i in range(n)
    ]
    names = list(shapes[0] if shapes else {"": []})
    regions_key = tuple_key(names)
    for i in range(n):
        if tuple_key(list(shapes[i])) != regions_key:
            raise StatechartError(
                f"The view's state() returned the regions {', '.join(names)} for one state and "
                f"{', '.join(shapes[i])} for the state {state_text(tla[i].vars)}. Return the same "
                "regions for every state."
            )
    step = _step_of(view)
    labels = [
        step(graph.steps[j].action, tla[walked.from_[j]].vars, tla[walked.to[j]].vars)
        for j in range(m)
    ]
    groups: list[Any] = [None] * n
    asked = [False] * n

    def group(i: int) -> Any:
        if view.group and not asked[i]:
            groups[i] = view.group(tla[i].vars)
            asked[i] = True
        return groups[i]

    return Answers(names, shapes, labels, group)


def as_parents(walked: Walk, answers: Answers) -> Answers:
    tla = walked.states
    parents: list[Shape] = []
    for i, shape in enumerate(answers.shapes):
        path = [f"{n} {p}" for n in answers.names for p in shape[n]]
        parents.append(_shape_of(path, tla[i].vars))
    return Answers([""], parents, answers.labels, answers.group)


def label_graph(
    graph: Graph, walked: Walk, answers: Answers, rank: list[int], found: list[Bug]
) -> Labels:
    index = walked.index
    from_ = walked.from_
    to = walked.to
    action = walked.action
    names = answers.names
    shapes = answers.shapes
    step_labels = answers.labels
    n = len(shapes)
    m = len(step_labels)
    on_path: set[Step] = {p.step for b in found for p in b.path}
    path_step_index: dict[Step, int] = {}
    if on_path:
        for j in range(m):
            if graph.steps[j] in on_path:
                path_step_index[graph.steps[j]] = j
    regions = len(names)
    keys: list[list[str]] = []
    kinds: list[list[int]] = []
    sizes: list[int] = []
    for name in names:
        key_ = [""] * n
        kind = [0] * n
        tops: dict[str, int] = {}
        nested: dict[str, int] = {}
        key_of: list[str] = []
        for i in range(n):
            path = shapes[i][name]
            top = len(path) == 1
            seen = tops if top else nested
            k = path[0] if top else tuple_key(path)
            c = seen.get(k)
            if c is None:
                c = seen[k] = len(key_of)
                key_of.append(tuple_key(path) if top else k)
            key_[i] = key_of[c]
            kind[i] = c
        keys.append(key_)
        kinds.append(kind)
        sizes.append(len(key_of))
    for b in found:
        t: Step | None = None
        for p in b.path:
            if step_labels[must(path_step_index, p.step)] is None:
                t = p.step
                break
        if t is None:
            in_loop = loop_of(b, index)
            if in_loop:
                for j in range(m):
                    if from_[j] in in_loop and to[j] not in in_loop and step_labels[j] is None:
                        t = graph.steps[j]
                        break
        if t is not None:
            _unlabeled(t.action, must(graph.states, t.from_).vars, must(graph.states, t.to).vars, b)
    drawn: list[int] = []
    drawn_labels: list[str] = [""] * m
    for j in range(m):
        label = step_labels[j]
        if label is None:
            continue
        drawn.append(j)
        drawn_labels[j] = label
    from_rank = [rank[from_[j]] for j in range(m)]
    to_rank = [rank[to[j]] for j in range(m)]
    sorted_ = sort_by(drawn, [from_rank, to_rank, action])
    path_steps = [0] * m
    for j in path_step_index.values():
        path_steps[j] = 1
    by_label: dict[str, tuple[list[int], dict[str, None]]] = {}
    if regions > 1:
        for j in sorted_:
            entry = by_label.get(drawn_labels[j])
            if entry is None:
                entry = by_label[drawn_labels[j]] = ([0] * regions, {})
            changed: list[str] = []
            for r in range(regions):
                if kinds[r][from_[j]] != kinds[r][to[j]]:
                    changed.append(names[r])
                    entry[0][r] = 1
            if len(changed) > 1:
                entry[1][list_text(changed)] = None
    together = {text for text, (_, sets) in by_label.items() if sets}
    notes: list[str] = []
    for text, (changed_in, sets) in by_label.items():
        changed = [names[r] for r in range(regions) if changed_in[r]]
        if len(changed) < 2:
            continue
        if text not in together:
            notes.append(f"The step {text} changes only one of {list_text(changed)} at a time.")
            continue
        all_sets = list(sets)
        both = f"{', or '.join(all_sets)}," if len(all_sets) > 1 else all_sets[0]
        notes.append(f"The step {text} changes {both} at the same time.")
    return Labels(
        names=answers.names,
        shapes=answers.shapes,
        labels=answers.labels,
        group=answers.group,
        drawn_labels=drawn_labels,
        keys=keys,
        kinds=kinds,
        sizes=sizes,
        sorted=sorted_,
        path_step_index=path_step_index,
        path_steps=path_steps,
        together=together,
        notes=notes,
    )


def _tell(
    states: Mapping[str, Any],
    found: list[Bug],
    shape_at: Callable[[str], Shape],
    label_at: Callable[[Bug, int, str], str | None],
) -> dict[Bug, list[StoryStep]]:
    def vars_of(id_: str) -> Vars:
        return must(states, id_).vars

    stories: dict[Bug, list[StoryStep]] = {}
    for bug in found:
        story = [StoryStep(shape_at(bug.start))]
        from_ = bug.start
        for k, p in enumerate(bug.path):
            step = label_at(bug, k, from_)
            if step is None:
                _unlabeled(p.action, vars_of(from_), vars_of(p.state), bug)
            story.append(StoryStep(shape_at(p.state), step))
            from_ = p.state
        stories[bug] = story
    return stories


def stories_of(
    graph: Graph, found: list[Bug], walked: Walk, labels: Labels
) -> dict[Bug, list[StoryStep]]:
    return _tell(
        graph.states,
        found,
        lambda id_: labels.shapes[must(walked.index, id_)],
        lambda bug, k, _from: labels.drawn_labels[must(labels.path_step_index, bug.path[k].step)],
    )
