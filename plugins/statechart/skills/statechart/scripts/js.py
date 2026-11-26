"""JavaScript string, whitespace, JSON and key-order rules that the output follows.

The command began as a TypeScript program, and its chart.mmd and report.md follow
JavaScript's rules: strings sort by UTF-16 code units, `\\s` and `trim()` use
JavaScript's whitespace set, JSON has no spaces, and an object lists its array-index
keys first. The corpus tests pin that output, so these helpers keep it.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable
from typing import Any

WS = "\t\n\v\f\r                  　﻿"
"""The characters in JavaScript's `\\s` and `String.prototype.trim()`."""

WS_CLASS = "[" + re.escape(WS) + "]"
NOT_WS_CLASS = "[^" + re.escape(WS) + "]"
DOT = "[^\n\r  ]"
"""JavaScript's `.` without the `s` flag."""
BOL = "(?:\\A|(?<=[\n\r  ]))"
"""JavaScript's `^` with the `m` flag."""
EOL = "(?=[\n\r  ]|\\Z)"
"""JavaScript's `$` with the `m` flag."""


def text_key(s: str) -> bytes:
    """Sort key that orders strings by UTF-16 code units, as `a < b` does in JavaScript."""
    return s.encode("utf-16-be", "surrogatepass")


def by_text(a: str, b: str) -> int:
    ka = text_key(a)
    kb = text_key(b)
    return -1 if ka < kb else 1 if ka > kb else 0


def trim(s: str) -> str:
    return s.strip(WS)


def trim_end(s: str) -> str:
    return s.rstrip(WS)


def trim_start(s: str) -> str:
    return s.lstrip(WS)


def is_number(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def number_text(n: float) -> str:
    """`String(n)` for a number."""
    if isinstance(n, int):
        return str(n)
    if math.isnan(n):
        return "NaN"
    if math.isinf(n):
        return "Infinity" if n > 0 else "-Infinity"
    if n == int(n) and abs(n) < 1e21:
        return str(int(n))
    text = repr(n)
    if "e" in text:
        mantissa, exponent = text.split("e")
        sign = "-" if exponent.startswith("-") else "+"
        text = f"{mantissa.removesuffix('.0')}e{sign}{exponent.lstrip('+-').lstrip('0') or '0'}"
    return text


def string(v: object) -> str:
    """`String(v)` for the values that JSON can hold, as Python gives them."""
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, str):
        return v
    if isinstance(v, (int, float)):
        return number_text(v)
    if isinstance(v, (list, tuple)):
        return ",".join("" if x is None else string(x) for x in v)
    if isinstance(v, dict):
        return "[object Object]"
    return str(v)


def stringify(v: Any) -> str:
    """`JSON.stringify(v)` for strings, numbers, booleans, None, lists and dicts."""
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def stringify_or_undefined(v: Any) -> str:
    """`JSON.stringify(v) ?? "undefined"` where `v` may hold values that JSON cannot."""
    try:
        return stringify(v)
    except (TypeError, ValueError):
        return repr(v)


_INDEX = re.compile(r"0|[1-9][0-9]*", re.ASCII)


def _is_index(k: str) -> bool:
    return bool(_INDEX.fullmatch(k)) and int(k) < 2**32 - 1


def object_from_entries(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    """`Object.fromEntries(pairs)`: array-index keys first in numeric order, then the rest."""
    out: dict[str, Any] = {}
    for k, v in pairs:
        out[k] = v
    return object_order(out)


def object_order(d: dict[str, Any]) -> dict[str, Any]:
    """The key order that `Object.keys()` gives for an object with the keys of `d`."""
    keys = list(d)
    indexes = [k for k in keys if _is_index(k)]
    if not indexes:
        return d
    indexes.sort(key=int)
    ordered = {k: d[k] for k in indexes}
    for k in keys:
        if k not in ordered:
            ordered[k] = d[k]
    return ordered


def same_value(v: object) -> object:
    """A key that two values share when a JavaScript `Set` holds them as one."""
    if v is None or isinstance(v, (str, int, float)):
        return (type(v).__name__, v)
    return ("object", id(v))
