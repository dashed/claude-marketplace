#!/usr/bin/env python3
"""List pytest and unittest tests that match low-value patterns ruff does not check.

Usage:
    python3 scan_smells.py PATH [PATH ...] [--select CODE,...] [--assert-helper REGEX] [--json]

PATH is a test file, or a directory searched for test_*.py and *_test.py. A test is a
module-level test* function, or a test* method of a class whose name starts with Test or whose
base class name contains TestCase or ends with Test.

Codes:
    no-assert     the test asserts nothing, so it pins only "does not raise"
    self-compare  both sides of an equality are one call-free expression, written twice or
                  through locals assigned just before it: usually a typo for the expected value
    repeat-call   both sides make the same call: a tautology when the expected value comes from
                  the code under test, deliberate in a determinism or idempotency test
    dup-body      same decorators, arguments and body as an earlier test in the same class or
                  module
    reads-source  the test reads Python source text instead of running it

Neither comparison code fires for a bare name compared with itself (ruff's PLR0124 reports
that) or when a side constructs an object (a test of that type's own __eq__ or __hash__).

A test asserts when it contains an assert statement, a call whose name starts with "assert"
(assertEqual, assert_called_once_with) or "test" (a test that delegates to another test),
pytest.raises/warns/deprecated_call/fail, raise AssertionError, or a call to a function or
fixture in the same file that does one of these. Helpers imported from other files are
invisible: name them with --assert-helper.

Findings are candidates, not verdicts: a no-assert test can be a deliberate smoke test and a
repeat-call can be a determinism check. Exit 0 when nothing matched, 1 when something did,
2 on a usage error.
"""

import argparse
import ast
import copy
import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

CODES = ("no-assert", "self-compare", "repeat-call", "dup-body", "reads-source")
EXPECT_CALLS = {"raises", "warns", "deprecated_call", "fail"}
SKIP_CALLS = {"skip", "skipTest"}
SKIP_DECORATORS = {"skip", "skipif", "skipIf", "skipUnless"}
EQUAL_OPS = (ast.Eq, ast.Is, ast.LtE, ast.GtE)
EQUALITY_METHODS = {"assertEqual", "assertEquals", "assertIs", "assertCountEqual"}
SOURCE_READERS = {"getsource", "getsourcelines"}
FILE_READERS = {"read_text", "read_bytes", "open"}
MESSAGES = {
    "no-assert": 'asserts nothing; pins only "does not raise"',
    "self-compare": "compares an expression with itself, so it holds for any result",
    "repeat-call": "both sides make the same call; a tautology unless determinism is the point",
    "reads-source": "reads source text instead of running the code",
}
Function = ast.FunctionDef | ast.AsyncFunctionDef


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def is_test_class(node: ast.ClassDef) -> bool:
    if node.name.startswith("Test"):
        return True
    return any("TestCase" in call_name(b) or call_name(b).endswith("Test") for b in node.bases)


def collect_tests(tree: ast.Module) -> Iterator[tuple[str, str | None, Function]]:
    """(name, enclosing class, function) for every test in the module."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test"):
                yield node.name, None, node
        elif isinstance(node, ast.ClassDef) and is_test_class(node):
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if member.name.startswith("test"):
                        yield f"{node.name}::{member.name}", node.name, member


def body_without_docstring(function: Function) -> list[ast.stmt]:
    body = function.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        return body[1:]
    return body


def is_skipped(function: Function) -> bool:
    if any(call_name(d) in SKIP_DECORATORS for d in function.decorator_list):
        return True
    body = body_without_docstring(function)
    return bool(body) and all(
        (isinstance(s, ast.Expr) and call_name(s.value) in SKIP_CALLS)
        or (isinstance(s, ast.Raise) and s.exc is not None and call_name(s.exc) == "SkipTest")
        for s in body
    )


def directly_asserts(node: ast.AST, extra: re.Pattern[str] | None) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            return True
        if isinstance(child, ast.Raise) and child.exc is not None:
            if call_name(child.exc) == "AssertionError":
                return True
        if isinstance(child, ast.Call):
            name = call_name(child)
            if name.lower().startswith("assert") or name.startswith("test"):
                return True
            if name in EXPECT_CALLS:
                return True
            if extra and extra.search(name):
                return True
    return False


def asserting_helpers(tree: ast.Module, extra: re.Pattern[str] | None) -> set[str]:
    """Names of the file's non-test functions and fixtures that assert, to a fixpoint."""
    helpers = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("test")
    }
    found = {name for name, node in helpers.items() if directly_asserts(node, extra)}
    changed = True
    while changed:
        changed = False
        for name, node in helpers.items():
            calls = {call_name(n) for n in ast.walk(node) if isinstance(n, ast.Call)}
            if name not in found and calls & found:
                found.add(name)
                changed = True
    return found


def asserts(function: Function, helpers: set[str], extra: re.Pattern[str] | None) -> bool:
    if directly_asserts(function, extra):
        return True
    calls = {call_name(n) for n in ast.walk(function) if isinstance(n, ast.Call)}
    fixtures = {a.arg for a in function.args.args + function.args.kwonlyargs}
    return bool((calls | fixtures) & helpers)


def assignment_counts(function: Function) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in ast.walk(function):
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign, ast.For, ast.AsyncFor)):
            targets = [node.target]
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            targets = [i.optional_vars for i in node.items if i.optional_vars]
        elif isinstance(node, ast.NamedExpr):
            targets = [node.target]
        for target in targets:
            for name in ast.walk(target):
                if isinstance(name, ast.Name):
                    counts[name.id] = counts.get(name.id, 0) + 1
    return counts


def has_call(node: ast.AST) -> bool:
    return any(isinstance(n, (ast.Call, ast.Await)) for n in ast.walk(node))


def names_read(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def inlinable(
    function: Function, at: int, operands: tuple[ast.expr, ast.expr]
) -> dict[str, ast.expr]:
    """Locals the comparison at `at` reads, directly or through each other, that are assigned
    exactly once in a top-level statement before it. None are inlined when a statement between
    the first of those assignments and the comparison calls something without defining one of
    them, as in `before = count(); act(); after = count()`."""
    counts = assignment_counts(function)
    single: dict[str, tuple[int, ast.expr]] = {}
    for index, statement in enumerate(function.body[:at]):
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and counts.get(statement.targets[0].id) == 1
        ):
            single[statement.targets[0].id] = (index, statement.value)
    needed: set[str] = set()
    pending = names_read(operands[0]) | names_read(operands[1])
    while pending:
        name = pending.pop()
        if name in single and name not in needed:
            needed.add(name)
            pending |= names_read(single[name][1])
    if not needed:
        return {}
    for statement in function.body[min(single[n][0] for n in needed) : at]:
        target = statement.targets[0] if isinstance(statement, ast.Assign) else None
        if isinstance(target, ast.Name) and target.id in needed:
            continue
        if has_call(statement) or not isinstance(statement, (ast.Assign, ast.Assert, ast.Pass)):
            return {}
    return {name: single[name][1] for name in needed}


class Inline(ast.NodeTransformer):
    """Replace locals by their assigned values; record whether any value constructs."""

    def __init__(self, values: dict[str, ast.expr]) -> None:
        self.values = values
        self.depth = 0
        self.constructed = False

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id not in self.values or self.depth >= 3:
            return node
        value = self.values[node.id]
        self.constructed |= constructs(value)
        self.depth += 1
        replaced = self.visit(copy.deepcopy(value))
        self.depth -= 1
        return replaced


def constructs(node: ast.expr) -> bool:
    """Whether the expression calls a class: an equality or hash test of that class."""
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            name = call_name(child)
            if name[:1].isupper() or name == "cls":
                return True
    return False


def comparison_code(left: ast.expr, right: ast.expr, values: dict[str, ast.expr]) -> str | None:
    """self-compare or repeat-call when both sides are one expression, else None. A bare
    name compared with itself is left to ruff's PLR0124, and a side that constructs an object
    tests that type's own equality."""
    if isinstance(left, ast.Name) and isinstance(right, ast.Name) and left.id == right.id:
        return None
    if constructs(left) or constructs(right):
        return None
    if ast.dump(left) == ast.dump(right):
        return "repeat-call" if has_call(left) else "self-compare"
    inline = Inline(values)
    left = inline.visit(copy.deepcopy(left))
    right = inline.visit(copy.deepcopy(right))
    if ast.dump(left) != ast.dump(right) or inline.constructed:
        return None
    return "repeat-call" if has_call(left) else "self-compare"


def self_compares(function: Function) -> Iterator[tuple[str, ast.stmt]]:
    for index, statement in enumerate(function.body):
        pair: tuple[ast.expr, ast.expr] | None = None
        if isinstance(statement, ast.Assert) and isinstance(statement.test, ast.Compare):
            test = statement.test
            if len(test.ops) == 1 and isinstance(test.ops[0], EQUAL_OPS):
                pair = (test.left, test.comparators[0])
        elif isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            call = statement.value
            if call_name(call) in EQUALITY_METHODS and len(call.args) >= 2:
                pair = (call.args[0], call.args[1])
        if pair and (code := comparison_code(*pair, inlinable(function, index, pair))):
            yield code, statement


def names_source_file(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            if child.value.endswith(".py"):
                return True
        # module.__file__ is production source; a bare __file__ is usually sample bytes.
        if isinstance(child, ast.Attribute) and child.attr == "__file__":
            return True
    return False


def reads_source(function: Function) -> Iterator[ast.Call]:
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node)
        if name in SOURCE_READERS:
            yield node
        elif name == "open" and isinstance(node.func, ast.Name):
            if node.args and names_source_file(node.args[0]):
                yield node
        elif name in FILE_READERS and isinstance(node.func, ast.Attribute):
            if names_source_file(node.func.value):
                yield node


def fingerprint(function: Function) -> str:
    parts = [ast.dump(d) for d in function.decorator_list]
    parts.append(ast.dump(function.args))
    parts.extend(ast.dump(s) for s in body_without_docstring(function))
    return "\n".join(parts)


def scan(path: Path, extra: re.Pattern[str] | None) -> tuple[int, list[dict[str, Any]]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    helpers = asserting_helpers(tree, extra)
    findings: list[dict[str, Any]] = []
    first_with_body: dict[tuple[str | None, str], str] = {}
    tests = 0

    def add(code: str, test: str, node: ast.AST, message: str = "") -> None:
        line = getattr(node, "lineno", 0)
        findings.append(
            {
                "file": str(path),
                "line": line,
                "code": code,
                "test": test,
                "message": message or MESSAGES[code],
            }
        )

    for test, owner, function in collect_tests(tree):
        tests += 1
        if is_skipped(function):
            continue
        if not asserts(function, helpers, extra):
            add("no-assert", test, function)
        for code, statement in self_compares(function):
            add(code, test, statement)
        for call in reads_source(function):
            add("reads-source", test, call)
        key = (owner, fingerprint(function))
        if key in first_with_body:
            earlier = first_with_body[key]
            add("dup-body", test, function, f"same decorators, arguments and body as {earlier}")
        else:
            first_with_body[key] = test
    return tests, findings


def collect_files(paths: list[str]) -> Iterator[Path]:
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            for found in sorted(path.rglob("*.py")):
                if found.name.startswith("test_") or found.name.endswith("_test.py"):
                    yield found
        else:
            yield path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("paths", nargs="+", metavar="PATH")
    parser.add_argument("--select", help="comma-separated codes to report (default: all)")
    parser.add_argument(
        "--assert-helper",
        action="append",
        default=[],
        metavar="REGEX",
        help="count calls whose name matches REGEX as assertions (repeatable)",
    )
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    args = parser.parse_args(argv)
    selected = set(args.select.split(",")) if args.select else set(CODES)
    if unknown := selected - set(CODES):
        parser.error(f"unknown code(s): {', '.join(sorted(unknown))}")
    for raw in args.paths:
        if not Path(raw).exists():
            parser.error(f"no such path: {raw}")
    helper = "|".join(f"(?:{p})" for p in args.assert_helper)
    extra = re.compile(helper) if helper else None

    tests = 0
    findings: list[dict[str, Any]] = []
    for path in collect_files(args.paths):
        try:
            count, found = scan(path, extra)
        except (SyntaxError, UnicodeDecodeError) as error:
            print(f"skipped {path}: {error}", file=sys.stderr)
            continue
        tests += count
        findings.extend(f for f in found if f["code"] in selected)

    if args.json:
        print(json.dumps({"tests": tests, "findings": findings}, indent=2))
    else:
        for f in findings:
            print(f"{f['file']}:{f['line']}: {f['code']} {f['test']} — {f['message']}")
        counts = [(c, sum(f["code"] == c for f in findings)) for c in CODES]
        summary = ", ".join(f"{n} {code}" for code, n in counts if n) or "no findings"
        print(f"{tests} tests scanned; {summary}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
