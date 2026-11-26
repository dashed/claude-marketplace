"""Breadth-first order of the state graph and the shortest path to each bug."""

from __future__ import annotations

from ir import (
    Bug,
    Graph,
    PathStep,
    Rule,
    State,
    Walk,
    count,
    default_state,
    must,
    rule_key,
    sort_by,
    text_key,
)


def walk(graph: Graph) -> Walk:
    ids: list[str] = []
    states: list[State] = []
    name_of: list[str] = []
    starts: list[int] = []
    unique: dict[str, None] = {}
    for id_, s in graph.states.items():
        name = default_state(s.vars)
        if s.start:
            starts.append(len(ids))
        ids.append(id_)
        states.append(s)
        name_of.append(name)
        unique[name] = None
    names = sorted(unique, key=text_key)
    rank_of = {name: i for i, name in enumerate(names)}
    n = len(ids)
    index: dict[str, int] = {}
    name_rank = [0] * n
    for i in range(n):
        index[ids[i]] = i
        name_rank[i] = must(rank_of, name_of[i])
    m = len(graph.steps)
    from_ = [0] * m
    to = [0] * m
    action = [0] * m
    actions: dict[str, int] = {}
    for j in range(m):
        t = graph.steps[j]
        from_[j] = must(index, t.from_)
        to[j] = must(index, t.to)
        a = actions.get(t.action)
        if a is None:
            a = actions[t.action] = len(actions)
        action[j] = a
    action_rank = [0] * len(actions)
    for i, a in enumerate(sorted(actions, key=text_key)):
        action_rank[must(actions, a)] = i
    to_name = [0] * m
    for j in range(m):
        action[j] = action_rank[action[j]]
        to_name[j] = name_rank[to[j]]
    first = [0] * (n + 1)
    for j in range(m):
        first[from_[j] + 1] += 1
    for i in range(n):
        first[i + 1] += first[i]
    fill = first[:n]
    following = [0] * m
    for j in sort_by(count(m), [action, to_name]):
        following[fill[from_[j]]] = j
        fill[from_[j]] += 1
    starts.sort(key=lambda s: name_rank[s])
    depth = [-1] * n
    via = [-1] * n
    reached = [0] * n
    size = 0
    for s in starts:
        depth[s] = 0
        reached[size] = s
        size += 1
    q = 0
    while q < size:
        s = reached[q]
        for e in range(first[s], first[s + 1]):
            t = to[following[e]]
            if depth[t] >= 0:
                continue
            depth[t] = depth[s] + 1
            via[t] = following[e]
            reached[size] = t
            size += 1
        q += 1
    return Walk(
        ids=ids,
        states=states,
        index=index,
        name_of=name_of,
        name_rank=name_rank,
        from_=from_,
        to=to,
        action=action,
        depth=depth,
        via=via,
        reached=reached[:size],
        starts=starts,
    )


def draw_order(walked: Walk) -> tuple[list[int], list[int]]:
    depth = walked.depth
    n = len(depth)
    deepest = max((d for d in depth), default=0)
    deepest = max(deepest, 0)
    level = [deepest + 1 if depth[i] < 0 else depth[i] for i in range(n)]
    order = sort_by(count(n), [level, walked.name_rank])
    rank = [0] * n
    for p in range(n):
        rank[order[p]] = p
    return order, rank


def bugs(graph: Graph, walked: Walk | None = None) -> list[Bug]:
    if walked is None:
        walked = walk(graph)
    ids = walked.ids
    from_ = walked.from_
    via = walked.via
    ends: dict[str, str] = {}
    for id_, s in graph.states.items():
        for rule in s.ends or []:
            ends[rule_key(rule)] = id_
    first: dict[str, tuple[Rule, int]] = {}
    for i in walked.reached:
        s = must(graph.states, ids[i])
        for rule in (s.ends or []) if s.past else s.breaks:
            k = rule_key(rule)
            if k not in first and ends.get(k, ids[i]) == ids[i]:
                first[k] = (rule, i)
    found: list[Bug] = []
    for rule, i in first.values():
        path: list[PathStep] = []
        start = i
        while via[start] >= 0:
            j = via[start]
            step = graph.steps[j]
            path.insert(0, PathStep(step.action, step.to, step))
            start = from_[j]
        found.append(Bug(rule, ids[start], path))
    return found
