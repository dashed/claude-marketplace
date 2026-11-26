"""Read the rules from the config and the variables from SANY's XML."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import js
from frontends.config import NAME
from ir import Config, ConfigSection, Spec, StatechartError


@dataclass(eq=False)
class Checks:
    invariants: list[str]
    properties: list[str]
    deadlock: bool
    written: list[ConfigSection]


def read_checks(config_file: str, config: Config) -> Checks:
    def refuse(words: str) -> StatechartError:
        return StatechartError(f"TLC refuses the config {config_file}. {words}")

    if config.spec and (config.init or config.next):
        raise refuse(
            "The configuration file cannot specify both INIT/NEXT and SPECIFICATION fields."
        )
    if not config.spec and not config.init:
        raise refuse("The configuration file did not specify the initial state predicate.")
    written = [
        s for s in config.sections if s.key not in ("INVARIANT", "PROPERTY", "CHECK_DEADLOCK")
    ]
    return Checks(
        invariants=config.invariants,
        properties=config.properties,
        deadlock=config.check_deadlock is not False,
        written=written,
    )


@dataclass(eq=False)
class XmlNode:
    tag: str
    text: str = ""
    children: list[XmlNode] = field(default_factory=list)


_ENTITIES = {"amp": "&", "apos": "'", "gt": ">", "lt": "<", "quot": '"'}
_ENTITY = re.compile(r"&(#x?)?(\w+);", re.ASCII)
_HEX = re.compile(r"[0-9a-fA-F]*")
_DEC = re.compile(r"[0-9]*")


def _code_point(number: str, name: str) -> str:
    digits = (_HEX if number == "#x" else _DEC).match(name)
    text = digits.group(0) if digits else ""
    return chr(int(text, 16 if number == "#x" else 10)) if text else "�"


def _decode(text: str) -> str:
    return _ENTITY.sub(
        lambda m: (
            _code_point(m.group(1), m.group(2))
            if m.group(1)
            else _ENTITIES.get(m.group(2), "undefined")
        ),
        text,
    )


_TAG = re.compile(
    r"<(/?)([^" + re.escape(js.WS) + r"/>?!]+)[^>]*?(/?)>|<[?!][^>]*>|([^<]+)",
)


def _parse_xml(xml: str) -> XmlNode:
    document = XmlNode("")
    open_ = [document]
    for m in _TAG.finditer(xml):
        close, tag, empty, text = m.groups()
        parent = open_[-1]
        if text is not None:
            parent.text += _decode(text)
        elif close:
            open_.pop()
        elif tag:
            node = XmlNode(tag)
            parent.children.append(node)
            if not empty:
                open_.append(node)
    return document


def _child(node: XmlNode | None, tag: str) -> XmlNode | None:
    if node is None:
        return None
    for c in node.children:
        if c.tag == tag:
            return c
    return None


def _text_of(node: XmlNode | None, tag: str) -> str:
    c = _child(node, tag)
    return c.text if c else ""


@dataclass(eq=False)
class Sany:
    variables: list[str]
    definitions: dict[str, XmlNode]


_VARIABLE_KIND = "3"


def read_sany(xml: str) -> Sany:
    modules = _child(_parse_xml(xml), "modules")
    symbols: dict[str, XmlNode] = {}
    context = _child(modules, "context")
    for entry in context.children if context else []:
        if len(entry.children) > 1:
            symbols[_text_of(entry, "UID")] = entry.children[1]
    root = _text_of(modules, "RootModule")
    module: XmlNode | None = None
    for node in symbols.values():
        if node.tag == "ModuleNode" and _text_of(node, "uniquename") == root:
            module = node
    definitions: dict[str, XmlNode] = {}
    variables: list[tuple[int, str]] = []
    for ref in module.children if module else []:
        if ref.tag not in ("OpDeclNodeRef", "UserDefinedOpKindRef"):
            continue
        uid = _text_of(ref, "UID")
        node = symbols.get(uid)
        if node is None:
            continue
        name = _text_of(node, "uniquename")
        definitions[name] = node
        if node.tag == "OpDeclNode" and _text_of(node, "kind") == _VARIABLE_KIND:
            variables.append((int(uid), name))
    variables.sort(key=lambda v: v[0])
    return Sany([name for _, name in variables], definitions)


def read_spec(module: str, sany: Sany, checks: Checks) -> Spec:
    return Spec(
        module=module,
        variables=sany.variables,
        invariants=checks.invariants,
        properties=checks.properties,
        deadlock=checks.deadlock,
        written=checks.written,
    )


_STATE_LEVEL = 1


def initial_only_properties(sany: Sany, spec: Spec) -> set[str]:
    replaced: dict[str, str] = {}
    for s in spec.written:
        if s.key == "CONSTANT":
            for i in range(1, len(s.tokens) - 1):
                if s.tokens[i] == "<-" and NAME.fullmatch(s.tokens[i + 1]):
                    replaced[s.tokens[i - 1]] = s.tokens[i + 1]
    names: set[str] = set()
    for name in spec.properties:
        definition = sany.definitions.get(replaced.get(name, name))
        if definition and _number(_text_of(definition, "level")) <= _STATE_LEVEL:
            names.add(name)
    return names


def _number(text: str) -> float:
    """`Number(text)`: an empty string is 0, and text that is not a number is NaN."""
    stripped = js.trim(text)
    if not stripped:
        return 0
    try:
        return float(stripped)
    except ValueError:
        return float("nan")
