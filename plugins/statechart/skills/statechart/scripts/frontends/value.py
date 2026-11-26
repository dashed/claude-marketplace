"""Read a TLA+ value as TLC prints it."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TypeVar

import js
from ir import Function, Interval, Model, SetValue, StatechartError, Value

BRACKET = [0] * 128
for _c in "<{[(":
    BRACKET[ord(_c)] = 1
for _c in ">}])":
    BRACKET[ord(_c)] = -1
_PUNCT = {60: "<<", 62: ">>", 124: "|->", 58: ":>", 64: "@@", 46: ".."}
_SPACE = frozenset(ord(c) for c in js.WS)


def is_space(c: int) -> bool:
    return c == 32 or 9 <= c <= 13 or (c > 127 and c in _SPACE)


def _is_digit(c: int) -> bool:
    return 48 <= c <= 57


def _is_word(c: int) -> bool:
    return _is_digit(c) or 65 <= c <= 90 or 97 <= c <= 122 or c == 95


def _is_line_end(c: int) -> bool:
    return c in (10, 13, 0x2028, 0x2029)


def _code(s: str, i: int) -> int:
    return ord(s[i]) if 0 <= i < len(s) else -1


def token_end(s: str, i: int) -> int:
    c = _code(s, i)
    if c == 34:
        j = i + 1
        while j < len(s):
            d = ord(s[j])
            if d == 34:
                return j + 1
            if d == 92:
                j += 1
                if j >= len(s) or _is_line_end(ord(s[j])):
                    return -1
            j += 1
        return -1
    punct = _PUNCT.get(c)
    if punct:
        return i + len(punct) if s.startswith(punct, i) else -1
    if (0 <= c < 128 and BRACKET[c]) or c == 44:
        return i + 1
    j = i + 1
    if c == 45 or _is_digit(c):
        while _is_digit(_code(s, j)):
            j += 1
        return -1 if c == 45 and j == i + 1 else j
    if not _is_word(c):
        return -1
    while _is_word(_code(s, j)):
        j += 1
    return j


def unreadable(text: str, pos: int) -> StatechartError:
    return StatechartError(f'cannot read TLA+ value at "{text[pos : pos + 20]}"')


T = TypeVar("T")

_INT = re.compile(r"-?[0-9]+")
_NAME = re.compile(r"\w*[A-Za-z]\w*", re.ASCII)
_UNESCAPED = {'"': '"', "\\": "\\", "n": "\n", "t": "\t", "r": "\r", "f": "\f"}

_models: dict[str, Model] = {}


def _model(name: str) -> Model:
    v = _models.get(name)
    if v is None:
        v = _models[name] = Model(name)
    return v


def parse_value(text: str) -> Value:
    tokens: list[str] = []
    starts: list[int] = []
    pos = 0
    while True:
        while pos < len(text) and is_space(ord(text[pos])):
            pos += 1
        if pos == len(text):
            break
        end = token_end(text, pos)
        if end == -1:
            raise unreadable(text, pos)
        tokens.append(text[pos:end])
        starts.append(pos)
        pos = end
    i = 0

    def fail() -> StatechartError:
        return unreadable(text, starts[max(i - 1, 0)] if i < len(starts) else len(text))

    def next_token() -> str:
        nonlocal i
        if i < len(tokens):
            i += 1
            return tokens[i - 1]
        raise fail()

    def eat(t: str) -> None:
        if next_token() != t:
            raise fail()

    def items(close: str, item: Callable[[], T]) -> list[T]:
        nonlocal i
        out: list[T] = []
        if i < len(tokens) and tokens[i] == close:
            i += 1
            return out
        while True:
            out.append(item())
            t = next_token()
            if t == close:
                return out
            if t != ",":
                raise fail()

    def string(t: str) -> str:
        s = ""
        j = start = 1
        while True:
            k = t.find("\\", j)
            if k == -1 or k >= len(t) - 1:
                return s + t[start:-1]
            c = _UNESCAPED.get(t[k + 1])
            if c is None:
                raise fail()
            s += t[start:k] + c
            j = start = k + 2

    def record_field(keys: list[Value], values: list[Value]) -> Callable[[], None]:
        def read() -> None:
            name = next_token()
            if not _NAME.fullmatch(name):
                raise fail()
            eat("|->")
            keys.append(name)
            values.append(value())

        return read

    def value() -> Value:
        nonlocal i
        t = next_token()
        if t == "TRUE":
            return True
        if t == "FALSE":
            return False
        if t == "{":
            return SetValue(items("}", value))
        if t == "<<":
            values = items(">>", value)
            return Function("tuple", list(range(1, len(values) + 1)), values)
        if t == "[":
            keys: list[Value] = []
            values = []
            items("]", record_field(keys, values))
            return Function("record", keys, values)
        if t == "(":
            keys = []
            values = []
            while True:
                keys.append(value())
                eat(":>")
                values.append(value())
                if next_token() != "@@":
                    break
            if tokens[i - 1] != ")":
                raise fail()
            return Function("pairs", keys, values)
        if t.startswith('"'):
            return string(t)
        if _INT.fullmatch(t):
            if i >= len(tokens) or tokens[i] != "..":
                return int(t)
            i += 1
            hi = next_token()
            if not _INT.fullmatch(hi):
                raise fail()
            return Interval(int(t), int(hi))
        if _NAME.fullmatch(t):
            return _model(t)
        raise fail()

    out = value()
    if i < len(tokens):
        i += 1
        raise fail()
    return out
