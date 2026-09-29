#!/usr/bin/env python3
"""List production symbols that only tests refer to: candidate test-only seams.

Usage:
    python3 find_seams.py --src PATH [PATH ...] --tests PATH [PATH ...] [--json]

A .py file under a --tests path, under a directory named tests, testutils or test_utils, or
named test_*.py, *_test.py or conftest.py, is test code. Any other .py file under a --src path
is production. Pass other test-support packages that live in the production tree under
--tests, and every other codebase that imports this one (a sibling repository, a plugin)
under --src, or its uses stay invisible.

A symbol is a module-level function, class or assigned name, or a method, defined in
production. It is a candidate when no production file refers to its name outside the symbol's
own body and some test file does. Matching is by name, so a name that production uses
anywhere, for anything, is never a candidate: the list misses seams with common names rather
than claim more than it can see.

Tags mark candidates that production may still reach without naming them:
    decorated   a decorator other than staticmethod, property and similar: it may register
                the symbol with a framework (a task, a signal receiver, a route)
    override    other production classes define a method with the same name, so a framework
                or a base class may call it
    string      a production string literal, other than a docstring, contains the name: a
                getattr, a registry key or a dotted import path may reach it
    exported    the name is in a production module's __all__: a public contract
    private     the name starts with one underscore (not a reachability tag)

Candidates with no reachability tag come first. Exit 0 when there are no candidates, 1 when
there are, 2 on a usage error.
"""

import argparse
import ast
import json
import os
import re
import sys
from collections import Counter
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path

IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
PLAIN_DECORATORS = {
    "staticmethod",
    "classmethod",
    "property",
    "cached_property",
    "abstractmethod",
    "override",
    "overload",
    "lru_cache",
    "cache",
    "wraps",
    "dataclass",
    "total_ordering",
    "setter",
    "getter",
    "deleter",
}
REACHABILITY = ("decorated", "override", "string", "exported")
TEST_DIRS = {"tests", "testutils", "test_utils"}


@dataclass
class Symbol:
    name: str
    qualname: str
    kind: str
    file: str
    line: int
    end_line: int
    decorators: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    test_refs: int = 0
    test_files: list[str] = field(default_factory=list)


def decorator_name(node: ast.expr) -> str:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def is_test_path(path: Path, root: Path, test_roots: list[Path]) -> bool:
    """Whether a file found under `root` is test code. Directory names count only below the
    root, so a checkout that happens to sit in a directory named tests is still scanned."""
    name = path.name
    if name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py":
        return True
    if TEST_DIRS & set(path.relative_to(root).parts[:-1]):
        return True
    return any(path.is_relative_to(test_root) for test_root in test_roots)


def python_files(roots: list[Path]) -> Iterator[tuple[Path, Path]]:
    """(file, root it was found under) for every .py file, both resolved."""
    for root in roots:
        root = root.resolve()
        if root.is_file():
            yield root, root.parent
        else:
            yield from ((p, root) for p in sorted(root.rglob("*.py")))


def parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError, ValueError) as error:
        print(f"skipped {path}: {error}", file=sys.stderr)
        return None


def export_entries(tree: ast.Module) -> list[ast.Constant]:
    """The string entries of a module-level __all__ list or tuple."""
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            if isinstance(node.value, (ast.List, ast.Tuple)):
                return [
                    e
                    for e in node.value.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                ]
    return []


def definitions(tree: ast.Module, file: str) -> Iterator[Symbol]:
    def function(node: ast.FunctionDef | ast.AsyncFunctionDef, qualname: str, kind: str) -> Symbol:
        decorators = [decorator_name(d) for d in node.decorator_list]
        end = node.end_lineno or node.lineno
        return Symbol(node.name, qualname, kind, file, node.lineno, end, decorators)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield function(node, node.name, "function")
        elif isinstance(node, ast.ClassDef):
            decorators = [decorator_name(d) for d in node.decorator_list]
            end = node.end_lineno or node.lineno
            yield Symbol(node.name, node.name, "class", file, node.lineno, end, decorators)
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    yield function(member, f"{node.name}.{member.name}", "method")
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            end = node.end_lineno or node.lineno
            for target in targets:
                if isinstance(target, ast.Name):
                    yield Symbol(target.id, target.id, "name", file, node.lineno, end)


def references(tree: ast.AST) -> Iterator[tuple[str, int]]:
    """(name, line) for every use of a name: loads, attributes and imports."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Store):
            yield node.id, node.lineno
        elif isinstance(node, ast.Attribute):
            yield node.attr, node.lineno
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                yield alias.name, node.lineno
        elif isinstance(node, ast.Import):
            for alias in node.names:
                for part in alias.name.split("."):
                    yield part, node.lineno


def prose_and_exports(tree: ast.Module) -> set[int]:
    """Ids of the docstring and __all__ constants: neither is a dynamic use of a name."""
    found = {id(e) for e in export_entries(tree)}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                found.add(id(body[0].value))
    return found


def string_mentions(tree: ast.Module) -> Iterator[str]:
    skip = prose_and_exports(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            yield from IDENTIFIER.findall(node.value)


def skipped(symbol: Symbol) -> bool:
    name = symbol.name
    return (name.startswith("__") and name.endswith("__")) or name.startswith("test")


def find(src: list[Path], tests: list[Path], base: Path) -> tuple[list[Symbol], int]:
    test_roots = [p.resolve() for p in tests]
    production = {
        str(p): tree
        for p, root in python_files(src)
        if not is_test_path(p, root, test_roots) and (tree := parse(p))
    }
    test_trees = {
        str(p): tree
        for p, root in python_files(tests + src)
        if is_test_path(p, root, test_roots) and (tree := parse(p))
    }

    symbols: list[Symbol] = []
    exported: set[str] = set()
    for file, tree in production.items():
        exported.update(str(e.value) for e in export_entries(tree))
        symbols.extend(s for s in definitions(tree, file) if not skipped(s))
    names = {s.name for s in symbols}
    method_owners = Counter(s.name for s in symbols if s.kind == "method")

    production_refs: dict[str, list[tuple[str, int]]] = {}
    mentioned: set[str] = set()
    for file, tree in production.items():
        for name, line in references(tree):
            if name in names:
                production_refs.setdefault(name, []).append((file, line))
        mentioned.update(n for n in string_mentions(tree) if n in names)

    test_refs: dict[str, Counter[str]] = {}
    for file, tree in test_trees.items():
        for name, _ in references(tree):
            if name in names:
                test_refs.setdefault(name, Counter())[file] += 1

    candidates: dict[tuple[str, str], Symbol] = {}
    for symbol in symbols:
        outside = [
            (file, line)
            for file, line in production_refs.get(symbol.name, [])
            if not (file == symbol.file and symbol.line <= line <= symbol.end_line)
        ]
        if outside or symbol.name not in test_refs or (symbol.file, symbol.qualname) in candidates:
            continue
        by_file = test_refs[symbol.name]
        symbol.test_refs = sum(by_file.values())
        symbol.test_files = sorted(os.path.relpath(f, base) for f in by_file)
        if any(d not in PLAIN_DECORATORS for d in symbol.decorators):
            symbol.tags.append("decorated")
        if symbol.kind == "method" and method_owners[symbol.name] > 1:
            symbol.tags.append("override")
        if symbol.name in mentioned:
            symbol.tags.append("string")
        if symbol.name in exported:
            symbol.tags.append("exported")
        if symbol.name.startswith("_"):
            symbol.tags.append("private")
        key = (symbol.file, symbol.qualname)
        symbol.file = os.path.relpath(symbol.file, base)
        candidates[key] = symbol

    def rank(s: Symbol) -> tuple[int, bool, str, int]:
        reachable = sum(tag in REACHABILITY for tag in s.tags)
        return reachable, "private" not in s.tags, s.file, s.line

    return sorted(candidates.values(), key=rank), len(symbols)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--src", nargs="+", required=True, type=Path, metavar="PATH")
    parser.add_argument("--tests", nargs="+", required=True, type=Path, metavar="PATH")
    parser.add_argument("--json", action="store_true", help="print candidates as JSON")
    args = parser.parse_args(argv)
    for path in args.src + args.tests:
        if not path.exists():
            parser.error(f"no such path: {path}")
    base = Path.cwd().resolve()
    candidates, total = find(args.src, args.tests, base)
    if args.json:
        payload = {"symbols": total, "candidates": [asdict(c) for c in candidates]}
        print(json.dumps(payload, indent=2))
    else:
        for c in candidates:
            tags = f" [{', '.join(c.tags)}]" if c.tags else ""
            shown = ", ".join(c.test_files[:3]) + (" ..." if len(c.test_files) > 3 else "")
            print(f"{c.file}:{c.line}: {c.kind} {c.qualname}{tags} — {c.test_refs} refs in {shown}")
        print(f"{total} production symbols; {len(candidates)} referenced only by tests")
    return 1 if candidates else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
