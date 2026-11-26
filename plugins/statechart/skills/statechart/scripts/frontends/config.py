"""Read a TLC config the way TLC does, or say why TLC would refuse it."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from ir import CHECK_DEADLOCK, Config, ConfigSection, StatechartError


@dataclass(frozen=True)
class _Section:
    key: str
    plural: str | None = None
    field: str | None = None
    undefined_noun: str | None = None


_LIST_FIELDS = ("invariants", "properties", "constraints", "action_constraints")

_SECTIONS: dict[str, _Section] = {}
for _section in (
    _Section("CONSTANT", plural="CONSTANTS"),
    _Section(CHECK_DEADLOCK, field="check_deadlock"),
    _Section("INIT", field="init", undefined_noun="initial predicate"),
    _Section("NEXT", field="next", undefined_noun="next state action"),
    _Section("SPECIFICATION", field="spec", undefined_noun="name"),
    _Section("VIEW", field="view", undefined_noun="view function"),
    _Section("SYMMETRY", field="symmetry", undefined_noun="symmetry function"),
    _Section("TYPE", field="type"),
    _Section("TYPE_CONSTRAINT", field="type_constraint"),
    _Section("INVARIANT", plural="INVARIANTS", field="invariants", undefined_noun="invariant"),
    _Section("PROPERTY", plural="PROPERTIES", field="properties", undefined_noun="property"),
    _Section("CONSTRAINT", plural="CONSTRAINTS", field="constraints", undefined_noun="constraint"),
    _Section(
        "ACTION_CONSTRAINT",
        plural="ACTION_CONSTRAINTS",
        field="action_constraints",
        undefined_noun="action constraint",
    ),
):
    _SECTIONS[_section.key] = _section
    if _section.plural:
        _SECTIONS[_section.plural] = _section

NAME = re.compile(r"\w*[A-Za-z]\w*", re.ASCII)
_WORD = re.compile(r"\w+", re.ASCII)
_CONFIG_HOLDS = (
    "A config can hold only names, numbers, strings, comments, and the symbols "
    "{ } ( ) [ ] , = ! <-."
)
_VALUE = re.compile(r'[0-9]+|"[^\n\r  ]*"')


def _shown(c: str) -> str:
    code = ord(c[0]) if c else 0
    hex_ = f"U+{code:04X}"
    if code < 0x20 or code == 0x7F:
        return hex_
    return f'"{c}"' if code < 0x7F else f'"{c}" ({hex_})'


@dataclass(frozen=True)
class _Token:
    image: str
    line: int


def _tokenize(text: str, fail: Callable[[int, str], StatechartError]) -> tuple[list[_Token], int]:
    if text.startswith("﻿"):
        raise fail(1, "The file starts with a byte order mark. Save it as UTF-8 without one.")
    tokens: list[_Token] = []
    line = 1
    last = 1
    i = 0
    n = len(text)

    def skip(to: int) -> None:
        nonlocal i, line, last
        while i < to:
            last = line
            if text[i] == "\n" or (text[i] == "\r" and (i + 1 >= n or text[i + 1] != "\n")):
                line += 1
            i += 1

    def push(image: str) -> None:
        tokens.append(_Token(image, line))
        skip(i + len(image))

    while i < n:
        c = text[i]
        two = text[i : i + 2]
        start = line
        if c in (" ", "\t", "\n", "\r"):
            skip(i + 1)
        elif two == "\\*":
            end = re.search(r"[\n\r]", text[i:])
            skip(n if end is None else i + end.start())
        elif two == "(*":
            marks = re.compile(r"\(\*|\*\)")
            depth = 0
            while True:
                m = marks.search(text, i)
                if not m:
                    raise fail(start, "A comment starts here and does not end.")
                depth += 1 if m.group(0) == "(*" else -1
                skip(m.start() + 2)
                if not depth:
                    break
        elif c == '"':
            j = i + 1
            while j >= n or text[j] != '"':
                ch = text[j] if j < n else None
                if ch is None:
                    raise fail(start, "A string starts here and does not end.")
                if ch in ("\n", "\r"):
                    raise fail(
                        start,
                        "A string starts here and does not end on its line. Write \\n for a "
                        "line break in a string.",
                    )
                if ch == "\0":
                    raise fail(start, "A string has the character U+0000.")
                if ch == "\\" and j + 1 < n and text[j + 1] not in '"\\ntrf':
                    raise fail(
                        start,
                        f"A string has a backslash before {_shown(text[j + 1])}. A string can use "
                        'only the escapes \\" \\\\ \\n \\t \\r \\f.',
                    )
                j += 2 if ch == "\\" else 1
            push(text[i : j + 1])
        elif re.match(r"\w", c, re.ASCII):
            found = _WORD.match(text, i)
            word = found.group(0) if found else c
            if re.match(r"[WS]F_", word):
                raise fail(
                    start,
                    f"TLC reads {word[:3]} at the start of a word as a TLA+ keyword, so it cannot "
                    f"read {word} as a name.",
                )
            if not re.search(r"[A-Za-z]", word) and word != "_":
                if re.search(r"[^0-9]", word):
                    parts = " ".join(re.findall(r"[0-9]+|_", word))
                    raise fail(
                        start, f"TLC splits {word} into {parts}, because a name needs a letter."
                    )
                if int(word) > 2147483647:
                    raise fail(start, f"TLC cannot read a number above 2147483647, such as {word}.")
            push(word)
        elif two == "<-":
            push(two)
        elif two in ("[]", "]_", "==", "=<", "!!"):
            raise fail(start, f"TLC reads {two} as one TLA+ symbol, and a config cannot hold it.")
        elif c in "{}()[],=!":
            push(c)
        else:
            where = " outside a string" if c > "\x7f" else ""
            raise fail(start, f"It cannot read the character {_shown(c)}{where}. {_CONFIG_HOLDS}")
    return tokens, last


def read_config(file: str, text: str) -> Config:
    def refuse(line: int, words: str) -> StatechartError:
        return StatechartError(f"TLC refuses the config {file} at line {line}. {words}")

    def cannot(line: int, words: str) -> StatechartError:
        return StatechartError(f"The command cannot read the config {file} at line {line}. {words}")

    tokens, end = _tokenize(text, cannot)
    eof = _Token("", end)
    at = 0

    def next_token() -> _Token:
        nonlocal at
        t = tokens[at] if at < len(tokens) else eof
        at += 1
        return t

    deferred: list[StatechartError] = []

    def defer(error: StatechartError) -> None:
        if not deferred:
            deferred.append(error)

    def defined(t: _Token, undefined_noun: str | None) -> None:
        if not NAME.fullmatch(t.image):
            defer(
                refuse(
                    t.line,
                    f"The {undefined_noun} {t.image} specified in the configuration file is not "
                    "defined in the specification.",
                )
            )

    def name(t: _Token, what: str) -> None:
        if t.image in _SECTIONS:
            defer(cannot(t.line, f"TLC would read the keyword {t.image} as {what}."))
        elif not NAME.fullmatch(t.image):
            defer(cannot(t.line, f"TLC would read {t.image} as {what}, and it is not a name."))

    def value(t: _Token) -> None:
        if t is eof:
            raise refuse(t.line, "It was expecting a value, but did not find it.")
        if t.image == "{":
            t = next_token()
            if t.image == "}":
                return
            value(t)
            t = next_token()
            while t.image == ",":
                value(next_token())
                t = next_token()
            if t.image != "}":
                raise refuse(t.line, "It was expecting }, but did not find it.")
        elif t.image in _SECTIONS:
            defer(cannot(t.line, f"TLC would read the keyword {t.image} as a value."))
        elif not NAME.fullmatch(t.image) and not _VALUE.fullmatch(t.image):
            defer(
                cannot(
                    t.line,
                    f"TLC would read {t.image} as a value. A value is a name, a number, a "
                    "string, or a set in braces.",
                )
            )

    def constant(t: _Token, loc: int) -> None:
        name(t, "a constant name")
        t = next_token()
        while t.image == "!":
            t = next_token()
            name(t, "a constant name")
            t = next_token()
        if t.image == "<-":
            t = next_token()
            if t.image == "[":
                t = next_token()
                if t is eof:
                    raise refuse(t.line, "Expected an identifier after <-[.")
                name(t, "a module name")
                t = next_token()
                if t.image != "]":
                    raise refuse(t.line, "It was expecting ], but did not find it.")
                t = next_token()
                if t is eof:
                    raise refuse(t.line, "Expected an identifier after <-[mod].")
            elif t is eof:
                raise refuse(t.line, "Expected an identifier after <-.")
            name(t, "the name after <-")
            return
        if t.image == "(":
            value(next_token())
            t = next_token()
            while t.image == ",":
                value(next_token())
                t = next_token()
            if t.image != ")":
                raise refuse(
                    loc,
                    "TLC gives no reason here. An operator's arguments are one or more values "
                    "in ( ), with commas between them.",
                )
            t = next_token()
        if t.image != "=":
            raise refuse(t.line, "It was expecting = or <-, but did not find it.")
        t = next_token()
        if t.image == "[":
            t = next_token()
            if t is eof:
                raise refuse(t.line, "Expected an identifier after =[.")
            name(t, "a module name")
            t = next_token()
            if t.image != "]":
                raise refuse(t.line, "It was expecting ], but did not find it.")
            t = next_token()
        value(t)

    config = Config()
    t = next_token()
    while t is not eof:
        keyword = t
        section = _SECTIONS.get(keyword.image)
        if not section:
            raise refuse(t.line, "It was expecting a keyword, but did not find it.")
        key = section.key
        field_ = section.field
        undefined_noun = section.undefined_noun
        begin = at
        if field_ is None:
            t = next_token()
            while t is not eof and t.image not in _SECTIONS:
                constant(t, keyword.line)
                t = next_token()
        elif field_ in _LIST_FIELDS:
            t = next_token()
            while t is not eof and t.image not in _SECTIONS:
                getattr(config, field_).append(t.image)
                defined(t, undefined_noun)
                t = next_token()
        else:
            t = next_token()
            if t is eof:
                raise refuse(
                    keyword.line,
                    f"The keyword {keyword.image} was not followed by an identifier.",
                )
            if field_ == "check_deadlock" and t.image not in ("TRUE", "FALSE"):
                raise refuse(t.line, "It was expecting TRUE or FALSE, but did not find it.")
            if getattr(config, field_) is not None:
                raise refuse(keyword.line, f"The keyword {keyword.image} appeared twice.")
            if field_ == "check_deadlock":
                config.check_deadlock = t.image == "TRUE"
            else:
                setattr(config, field_, t.image)
                if t.image in _SECTIONS:
                    defer(
                        cannot(
                            t.line,
                            f"TLC would read the keyword {t.image} as the name after {key}.",
                        )
                    )
                elif undefined_noun:
                    defined(t, undefined_noun)
            t = next_token()
        stop = len(tokens) if t is eof else at - 1
        images = [tokens[k].image for k in range(begin, stop)]
        config.sections.append(ConfigSection(key, keyword.line, images))
    if deferred:
        raise deferred[0]
    return config
