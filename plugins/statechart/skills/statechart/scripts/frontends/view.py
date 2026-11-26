"""Check the reader's view module and give it each state as JSON.

A view defines state, step, group, colors and title. It gets each state as JSON: a set
is a list, and a record, a sequence or a function is a dict with string keys, so
`v["pc"]["1"]` is `pc[1]`.
"""

from __future__ import annotations

import types
from collections.abc import Callable
from typing import Any

import js
from ir import (
    CheckedView,
    Function,
    Interval,
    Model,
    SetValue,
    StatechartError,
    Value,
    Vars,
    list_text,
)

Json = Any


def json(v: Value) -> Json:
    if isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, Model):
        return v.name
    j = v._json
    if j is None:
        if isinstance(v, Interval):
            j = list(range(v.lo, v.hi + 1))
        elif isinstance(v, SetValue):
            j = [json(m) for m in v.members]
        else:
            j = js.object_from_entries(_fields(v))
        v._json = j
    return j


def _fields(v: Function) -> list[tuple[str, Json]]:
    fields: list[tuple[str, Json]] = []
    for k, value in zip(v.keys, v.values):
        name = json(k)
        fields.append(
            (js.stringify(name) if isinstance(name, (list, dict)) else js.string(name), json(value))
        )
    return fields


_projected_vars: dict[int, tuple[Vars, dict[str, Json]]] = {}


def json_vars(vars: Vars) -> dict[str, Json]:
    cached = _projected_vars.get(id(vars))
    if cached is not None and cached[0] is vars:
        return cached[1]
    j = js.object_from_entries((name, json(v)) for name, v in vars.items())
    _projected_vars[id(vars)] = (vars, j)
    return j


THEME_COLORS = ["blue", "orange", "purple", "yellow", "teal", "tan", "pink"]

VIEW_EXPORTS = ["state", "step", "group", "colors", "title"]


def view_exports(module: types.ModuleType) -> dict[str, object]:
    """The names that a view module defines for the command.

    `__all__` lists them when the module has it. Otherwise each name that does not start
    with `_` counts, except modules and what the module imports from elsewhere.
    """
    names = getattr(module, "__all__", None)
    if names is None:
        names = []
        for name, value in vars(module).items():
            if name.startswith("_") or isinstance(value, types.ModuleType):
                continue
            home = getattr(value, "__module__", module.__name__)
            if home != module.__name__:
                continue
            names.append(name)
    return {name: getattr(module, name) for name in names}


def check_view(view: dict[str, object], inspect: Callable[[object], str] = repr) -> CheckedView:
    def literal(v: object) -> str:
        return js.stringify(v) if isinstance(v, str) else inspect(v)

    extra = [name for name in view if name not in VIEW_EXPORTS]
    if extra:
        raise StatechartError(
            f"The view defines {list_text(extra)}, which the command does not read. Define only "
            f"{list_text(VIEW_EXPORTS)}, and start any other name with _."
        )
    wrong: list[str] = []

    def pick(name: str, kind: str, fits: Callable[[object], bool]) -> Any:
        v = view.get(name)
        if v is None or fits(v):
            return v
        wrong.append(f"{name} must be {kind}")
        return None

    state = pick("state", "a function", callable)
    step = pick("step", "a function", callable)
    group = pick("group", "a function", callable)
    exported = pick("colors", "a dict", lambda v: isinstance(v, dict))
    title = pick("title", "a string", lambda v: isinstance(v, str))
    if wrong:
        raise StatechartError(f"The view's {list_text(wrong)}.")
    if group is not None and exported is None:
        raise StatechartError(
            "The view defines group() but no colors. Give each group a color in colors."
        )
    colors: dict[str, str] = {}
    bad: list[str] = []
    for name, color in js.object_order(
        {js.string(k): v for k, v in (exported or {}).items()}
    ).items():
        if isinstance(color, str) and color in THEME_COLORS:
            colors[name] = color
        else:
            bad.append(f"{js.stringify(name)} the color {literal(color)}")
    if bad:
        raise StatechartError(
            f"The view's colors give {list_text(bad)}. Give each group "
            f"{list_text(THEME_COLORS, 'or')}."
        )

    def named(vars: Vars) -> object:
        g = group(json_vars(vars))
        if g is not None and js.string(g) not in colors:
            raise StatechartError(
                f"The view's group() returned {literal(g)}, which colors does not name. Give each "
                "group a color in colors."
            )
        return g

    checked = CheckedView()
    checked.state = (lambda vars: state(json_vars(vars))) if state else None
    checked.step = (
        (lambda action, from_, to: step(action, json_vars(from_), json_vars(to))) if step else None
    )
    checked.group = named if group else None
    checked.colors = colors
    checked.title = title
    return checked
