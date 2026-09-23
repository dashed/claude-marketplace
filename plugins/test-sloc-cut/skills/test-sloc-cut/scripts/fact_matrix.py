#!/usr/bin/env python3
"""Seed, check and compare a machine-checkable fact matrix for a test suite.

Usage:
    python3 fact_matrix.py seed TEST_FILE [TEST_FILE ...] --out MATRIX.json [--from BASELINE.json]
    python3 fact_matrix.py check MATRIX.json [--coverage analysis.json]
    python3 fact_matrix.py compare BASELINE.json AFTER.json

seed parses the test files and writes one "site" per line that asserts something in a test:
an assert statement, pytest.raises/warns, an assert* method (self.assertEqual,
mock.assert_called_once_with), an assert_* helper, or a call to a module helper that itself
asserts. Each site is anchored by its test, file, line and exact text. The agent then fills
"facts" (what is asserted) and maps every site to its facts, or states why it asserts none.
With --from, sites whose test and text are unchanged keep the baseline's mapping.

check exits 0 when the matrix is complete and consistent, 1 on any violation, and 2 when it
cannot check (a test file changed since seeding, or malformed JSON). With --coverage (the
analysis.json of coverage_map.py) it also requires that some test asserting each fact runs
the fact's production lines.

compare exits 1 when a baseline fact is missing from the after matrix, asserted by a weaker
kind of check, or moved entirely to other tests without a recorded mutant; otherwise 0.

The matrix is bookkeeping for the method in SKILL.md, not proof: a mapped fact is the
agent's claim, checked for consistency with the source and the coverage run.
"""

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
# Stronger kinds pin more of a value; a fact may be subsumed only by a stronger one.
STRENGTH = {"eq": 3, "raises": 3, "called_with": 3, "contains": 2, "len": 2, "truthy": 1}
KINDS = {*STRENGTH, "absent", "other"}
EXPECTS = {"raises", "warns", "deprecated_call"}


class MatrixError(Exception):
    """The matrix or its inputs cannot be checked; the caller exits 2."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def assertion_kinds(node: ast.AST, asserting_helpers: set[str]) -> set[str]:
    """What kind of assertion this node is, if any."""
    if isinstance(node, ast.Assert):
        return {"assert"}
    if isinstance(node, (ast.With, ast.AsyncWith)):
        names = {
            call_name(i.context_expr.func)
            for i in node.items
            if isinstance(i.context_expr, ast.Call)
        }
        return {"expects"} if names & EXPECTS else set()
    if isinstance(node, ast.Call):
        name = call_name(node.func)
        if name in EXPECTS and isinstance(node.func, ast.Attribute):
            return {"expects"}
        if name.startswith("assert"):
            return {"assert-call"}
        if isinstance(node.func, ast.Name) and name in asserting_helpers:
            return {f"helper:{name}"}
    return set()


def test_functions(tree: ast.Module) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """(node-id suffix, function) for module-level tests and methods of Test* classes."""
    found: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            "test"
        ):
            found.append((node.name, node))
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for member in node.body:
                if isinstance(
                    member, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and member.name.startswith("test"):
                    found.append((f"{node.name}::{member.name}", member))
    return found


def seed_file(path: str) -> list[dict[str, Any]]:
    source = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()
    helpers = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("test")
        and any(assertion_kinds(n, set()) for n in ast.walk(node))
    }
    sites = []
    for suffix, function in test_functions(tree):
        test = f"{path}::{suffix}"
        by_line: dict[int, set[str]] = {}
        for node in ast.walk(function):
            kinds = assertion_kinds(node, helpers)
            if kinds and isinstance(node, (ast.stmt, ast.expr)):
                by_line.setdefault(node.lineno, set()).update(kinds)
        for line in sorted(by_line):
            sites.append(
                {
                    "id": f"{test}@{line}",
                    "test": test,
                    "file": path,
                    "line": line,
                    "text": lines[line - 1].strip(),
                    "kind_hint": "/".join(sorted(by_line[line])),
                    "facts": [],
                    "no_fact": None,
                }
            )
    return sites


def seed(files: list[str], baseline: dict[str, Any] | None) -> tuple[dict[str, Any], int]:
    sites = [site for path in files for site in seed_file(path)]
    carried = 0
    if baseline is not None:
        # Unchanged assertions keep their mapping; identical text in one test pairs in order.
        pool: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for old in baseline["sites"]:
            pool.setdefault((old["test"], old["text"]), []).append(old)
        for site in sites:
            matches = pool.get((site["test"], site["text"]))
            if matches:
                old = matches.pop(0)
                site["facts"], site["no_fact"] = list(old["facts"]), old["no_fact"]
                carried += 1
    matrix = {
        "schema_version": SCHEMA_VERSION,
        "files": {path: sha256(Path(path)) for path in files},
        "facts": dict(baseline["facts"]) if baseline else {},
        "sites": sites,
    }
    return matrix, carried


def load(path: str) -> dict[str, Any]:
    try:
        matrix = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise MatrixError(f"cannot read {path}: {error}") from error
    if not isinstance(matrix, dict) or matrix.get("schema_version") != SCHEMA_VERSION:
        raise MatrixError(f"{path} is not a schema {SCHEMA_VERSION} fact matrix")
    if not isinstance(matrix.get("facts"), dict) or not isinstance(matrix.get("sites"), list):
        raise MatrixError(f"{path} needs a facts object and a sites list")
    return matrix


def claimants(matrix: dict[str, Any]) -> dict[str, set[str]]:
    """Fact id -> the tests that assert it."""
    result: dict[str, set[str]] = {fact: set() for fact in matrix["facts"]}
    for site in matrix["sites"]:
        for fact in site["facts"]:
            result.setdefault(fact, set()).add(site["test"])
    return result


def text_at(path: str, line: int) -> str | None:
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    return lines[line - 1].strip() if 1 <= line <= len(lines) else None


def executed(test: str, anchor: dict[str, Any], coverage: dict[str, Any]) -> bool:
    """Did the test (any of its parametrized cases) run the anchor's line?"""
    for name, entry in coverage["per_test"].items():
        if name == test or name.startswith(test + "["):
            if anchor["line"] in entry.get("lines", {}).get(anchor["file"], []):
                return True
    return False


def check(matrix: dict[str, Any], coverage: dict[str, Any] | None) -> tuple[list[str], list[str]]:
    """Return (violations, summary lines). Raises MatrixError when it cannot check."""
    changed = [
        path
        for path, digest in matrix.get("files", {}).items()
        if not Path(path).exists() or sha256(Path(path)) != digest
    ]
    if changed:
        raise MatrixError(f"test files changed since seeding: {changed}; re-seed with --from")
    spans: dict[str, tuple[str, int, int]] = {}
    for path in matrix["files"]:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
        for suffix, function in test_functions(tree):
            end = function.end_lineno or function.lineno
            spans[f"{path}::{suffix}"] = (path, function.lineno, end)
    facts = matrix["facts"]
    violations = []
    for site in matrix["sites"]:
        where = site.get("id", "?")
        span = spans.get(site.get("test", ""))
        if (
            span is None
            or span[0] != site.get("file")
            or not span[1] <= site.get("line", 0) <= span[2]
        ):
            violations.append(f"{where}: not inside test {site.get('test')}")
        elif text_at(site["file"], site["line"]) != site.get("text"):
            violations.append(f"{where}: anchor text is not at line {site['line']}")
        unknown = [f for f in site.get("facts", []) if f not in facts]
        if unknown:
            violations.append(f"{where}: unknown facts {unknown}")
        if not site.get("facts") and not (
            isinstance(site.get("no_fact"), str) and site["no_fact"].strip()
        ):
            violations.append(f"{where}: unmapped (name its facts or give a no_fact reason)")
    owners = claimants(matrix)
    for fid, fact in facts.items():
        if not isinstance(fact.get("proposition"), str) or not fact["proposition"].strip():
            violations.append(f"{fid}: proposition is empty")
        kind = fact.get("kind")
        if kind not in KINDS:
            violations.append(f"{fid}: kind {kind!r} is not one of {sorted(KINDS)}")
        if kind == "absent" and not (
            isinstance(fact.get("window"), str) and fact["window"].strip()
        ):
            violations.append(f"{fid}: an absent fact needs the window it is observed over")
        stronger = fact.get("subsumed_by")
        if stronger is not None and (
            stronger not in facts
            or STRENGTH.get(facts[stronger].get("kind"), 0) <= STRENGTH.get(kind, 0)
        ):
            violations.append(f"{fid}: subsumed_by {stronger!r} must name a stronger kind of check")
        for anchor in fact.get("production", []):
            if text_at(anchor["file"], anchor["line"]) != anchor.get("text"):
                violations.append(
                    f"{fid}: production anchor {anchor['file']}:{anchor['line']} drifted"
                )
            elif (
                coverage is not None
                and owners.get(fid)
                and not any(executed(t, anchor, coverage) for t in owners[fid])
            ):
                violations.append(
                    f"{fid}: no test asserting it runs {anchor['file']}:{anchor['line']} "
                    "(a mocked or different path)"
                )
        if fact.get("questions"):
            violations.append(f"{fid}: open questions {fact['questions']}")
        if not owners.get(fid):
            violations.append(f"{fid}: no site asserts it")
    single = sorted(f for f, tests in owners.items() if len(tests) == 1)
    duplicated = sorted(f for f, tests in owners.items() if len(tests) > 1)
    mapped = sum(1 for s in matrix["sites"] if s.get("facts"))
    summary = [
        f"sites={len(matrix['sites'])} mapped={mapped} "
        f"no_fact={len(matrix['sites']) - mapped} facts={len(facts)}",
        f"single-pinned (do not touch): {', '.join(single) or '-'}",
        f"asserted by several tests: {', '.join(duplicated) or '-'}",
    ]
    return violations, summary


def compare(base: dict[str, Any], after: dict[str, Any]) -> list[str]:
    before_owners, after_owners = claimants(base), claimants(after)
    problems = []
    for fid, fact in base["facts"].items():
        now = after["facts"].get(fid)
        if now is None or not after_owners.get(fid):
            problems.append(f"lost: {fid} ({fact.get('proposition')})")
            continue
        if STRENGTH.get(now.get("kind"), 0) < STRENGTH.get(fact.get("kind"), 0):
            problems.append(f"weakened: {fid} from {fact.get('kind')} to {now.get('kind')}")
        moved = before_owners.get(fid) and not before_owners[fid] & after_owners[fid]
        if moved and not (isinstance(now.get("mutant"), str) and now["mutant"].strip()):
            problems.append(
                f"moved without a mutant: {fid} now asserted only by {sorted(after_owners[fid])}"
            )
    return problems


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p_seed = sub.add_parser("seed", help="write a matrix skeleton from test files")
    p_seed.add_argument("files", nargs="+")
    p_seed.add_argument("--out", required=True)
    p_seed.add_argument("--from", dest="baseline", help="carry mappings from this matrix")
    p_check = sub.add_parser("check", help="validate a filled matrix")
    p_check.add_argument("matrix")
    p_check.add_argument("--coverage", help="coverage_map.py analysis.json (schema 2)")
    p_compare = sub.add_parser("compare", help="baseline facts must survive in the after matrix")
    p_compare.add_argument("baseline")
    p_compare.add_argument("after")
    a = parser.parse_args(argv)
    try:
        if a.command == "seed":
            if Path(a.out).exists():
                raise MatrixError(f"{a.out} exists; choose a new name so earlier work is kept")
            baseline = load(a.baseline) if a.baseline else None
            matrix, carried = seed(a.files, baseline)
            Path(a.out).write_text(json.dumps(matrix, indent=1) + "\n", encoding="utf-8")
            print(f"sites={len(matrix['sites'])} carried={carried} wrote {a.out}")
            return 0
        if a.command == "check":
            coverage = None
            if a.coverage:
                coverage = json.loads(Path(a.coverage).read_text(encoding="utf-8"))
                if coverage.get("schema_version") != 2:
                    raise MatrixError(
                        "--coverage needs a schema 2 analysis.json from coverage_map.py"
                    )
            violations, summary = check(load(a.matrix), coverage)
            print("\n".join([*summary, *(f"  violation: {v}" for v in violations)]))
            print(
                f"{len(violations)} violations"
                if violations
                else "matrix is complete and consistent"
            )
            return 1 if violations else 0
        problems = compare(load(a.baseline), load(a.after))
        print("\n".join(problems or ["every baseline fact survives"]))
        return 1 if problems else 0
    except (MatrixError, OSError, ValueError, KeyError) as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
