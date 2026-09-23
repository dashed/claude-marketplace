#!/usr/bin/env python3
"""Per-test unique coverage, a verified minimum covering set, and an identity diff.

Usage:
    python3 coverage_map.py --scratch DIR [--range MOD=LO-HI ...] [--out FILE] MODULE [MODULE ...]
    python3 coverage_map.py --diff BASELINE.json AFTER.json

Reads the coverage data file that a serial, per-test-context pytest run
wrote into DIR (see references/coverage-and-mutants.md for the .coveragerc
and the pytest command) and, for the production MODULEs (repo-relative
paths, as they appear in the data file), writes DIR/analysis.json with:

  modules     per module: statements, covered, missing lines, branch arcs,
              branch arcs taken, and every covered line and arc by name
  per_test    per test, with pytest's setup, call and teardown phases merged
              under the node id: item count per phase, the lines it reaches,
              the lines/arcs no other test reaches ("unique"), and the reached
              lines whose outcomes coverage cannot see ("subline")
  cover       a greedy minimum covering set over what only tests can supply
              (import-time coverage, context "", is excluded), and its size
  provenance  module hashes and the coverage version; --diff requires both
              reports to match

A unique arc tagged (exc) is one coverage's static model does not list, such
as a jump into an except handler. A unique item tagged (fixture) is reached
only in the test's setup or teardown phase. A module- or session-scoped
fixture runs in the first test that requests it, so deleting that test moves
the item to the next requester instead of losing it.

A test with an empty "unique" list is coverage-redundant. That is NOT
assertion-redundant: two tests can walk the same lines and assert different
values. Nor does coverage see outcomes inside a line: zero-iteration loops,
and/or operands, ternary arms, comprehension filters, lambdas and match
guards, which are listed per test under "subline". Delete only on the
intersection with the fact matrix.

Leave-one-out is not a licence either: if exactly two tests reach a line,
neither is unique, yet dropping both loses the line. That is what the
covering set is for -- verify it by running only those tests with the same
.coveragerc and comparing the two reports with --diff.

--diff BASELINE AFTER compares covered lines and arcs by name, not by count.
Exit 0: nothing the baseline covered was lost. Exit 1: items were lost, each
one listed. Exit 2: the reports cannot be compared (different module
sources, ranges or coverage version, or a report from an older version).

--range MOD=LO-HI scopes a large module to the functions under test
(e.g. --range pkg/big.py=558-689). Requires `coverage` importable in the
same environment that ran the tests (`uvx --with coverage python3 ...`).
"""

import argparse
import ast
import collections
import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any

try:
    import coverage
    from coverage.sqldata import CoverageData
except ImportError:
    print(
        "coverage is not importable; run with the test environment's interpreter "
        "or `uvx --with coverage python3 coverage_map.py ...`",
        file=sys.stderr,
    )
    sys.exit(2)

SCHEMA_VERSION = 2
PHASES = ("setup", "run", "teardown")
SUBLINE_KINDS: dict[type, str] = {
    ast.For: "for",
    ast.AsyncFor: "for",
    ast.ListComp: "comprehension",
    ast.SetComp: "comprehension",
    ast.DictComp: "comprehension",
    ast.GeneratorExp: "comprehension",
    ast.IfExp: "ternary",
    ast.Lambda: "lambda",
}

Item = tuple[Any, ...]


class ReportError(Exception):
    """The data file cannot answer the question; the caller exits 2."""


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(__doc__ or "").split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--scratch", help="directory holding .coverage and .coveragerc")
    p.add_argument(
        "--range", action="append", default=[], metavar="MOD=LO-HI", help="restrict MOD to LO..HI"
    )
    p.add_argument(
        "--out", default=None, help="output JSON path (default: <scratch>/analysis.json)"
    )
    p.add_argument(
        "--diff",
        nargs=2,
        metavar=("BASELINE", "AFTER"),
        help="compare two reports by covered line and arc identity",
    )
    p.add_argument("modules", nargs="*", help="repo-relative module paths as recorded in the data")
    a = p.parse_args(argv)
    if a.diff:
        if a.scratch or a.modules or a.range or a.out:
            p.error("--diff takes only the two report paths")
        return a
    if not a.scratch or not a.modules:
        p.error("--scratch and at least one MODULE are required")
    a.ranges = {}
    for spec in a.range:
        mod, _, lo_hi = spec.partition("=")
        lo, _, hi = lo_hi.partition("-")
        a.ranges[mod] = (int(lo), int(hi))
    a.out = a.out or f"{a.scratch}/analysis.json"
    return a


def split_context(context: str) -> tuple[str, str]:
    """Return (test node id, phase) for a pytest-cov context such as 'nodeid|setup'."""
    test, sep, phase = context.rpartition("|")
    if sep and phase in PHASES:
        return test, phase
    return context, "run"


def subline_sites(source: str) -> dict[int, set[str]]:
    """Map each statement's first line to the outcomes inside it that coverage cannot see."""
    sites: dict[int, set[str]] = collections.defaultdict(set)
    stack: list[tuple[ast.AST, int]] = [(ast.parse(source), 0)]
    while stack:
        node, line = stack.pop()
        if isinstance(node, ast.stmt):
            line = node.lineno
        elif isinstance(node, ast.match_case):
            line = node.pattern.lineno
            if node.guard is not None:
                sites[line].add("match guard")
        if isinstance(node, ast.BoolOp):
            sites[line].add("and" if isinstance(node.op, ast.And) else "or")
        elif type(node) in SUBLINE_KINDS:
            sites[line].add(SUBLINE_KINDS[type(node)])
        stack.extend((child, line) for child in ast.iter_child_nodes(node))
    return sites


def analyze(scratch: str, modules: list[str], ranges: dict[str, tuple[int, int]]) -> dict[str, Any]:
    def in_scope(mod: str, line: int) -> bool:
        lo_hi = ranges.get(mod)
        return True if lo_hi is None else lo_hi[0] <= abs(line) <= lo_hi[1]

    cov = coverage.Coverage(data_file=f"{scratch}/.coverage", config_file=f"{scratch}/.coveragerc")
    cov.load()
    data = CoverageData(basename=f"{scratch}/.coverage")
    data.read()
    measured = set(data.measured_files())
    missing_mods = [m for m in modules if m not in measured]
    if missing_mods:
        raise ReportError(
            f"not in the data file: {missing_mods}\nmeasured files: {sorted(measured)}"
        )
    contexts = sorted(data.measured_contexts())
    phase_of = {c: split_context(c) for c in contexts if c}  # "" is the import-time context
    if not phase_of:
        raise ReportError(
            "no per-test contexts in the data file; run pytest with --cov-context=test "
            "(and no dynamic_context in the rcfile)"
        )

    analyses = {m: cov._analyze(m) for m in modules}
    statements = {m: {n for n in analyses[m].statements if in_scope(m, n)} for m in modules}
    static_arcs = {m: set(analyses[m].arc_possibilities_set) for m in modules}
    sources = {m: Path(analyses[m].filename).read_bytes() for m in modules}
    sites = {
        m: {
            n: kinds
            for n, kinds in subline_sites(sources[m].decode()).items()
            if n in statements[m]
        }
        for m in modules
    }

    def endpoint_ok(mod: str, value: int) -> bool:
        # negative values are function or module exits; positive ones must be real statements
        return in_scope(mod, value) and (value < 0 or value in statements[mod])

    def items_for(context: str) -> set[Item]:
        data.set_query_context(context)
        items: set[Item] = set()
        for mod in modules:
            items |= {("L", mod, n) for n in (data.lines(mod) or []) if n in statements[mod]}
            items |= {
                ("A", mod, x, y)
                for (x, y) in (data.arcs(mod) or [])
                if endpoint_ok(mod, x) and endpoint_ok(mod, y)
            }
        return items

    def label(item: Item) -> str:
        if item[0] == "L":
            return f"{item[1]}:{item[2]}"
        tag = "" if (item[2], item[3]) in static_arcs[item[1]] else " (exc)"
        return f"{item[1]}:{item[2]}->{item[3]}{tag}"

    sets = {c: items_for(c) for c in contexts}
    imported = sets.get("", set())
    phases: dict[str, dict[str, set[Item]]] = collections.defaultdict(dict)
    for context, (test, phase) in phase_of.items():
        phases[test][phase] = phases[test].get(phase, set()) | sets[context]
    tests = sorted(phases)
    reached = {t: set().union(*phases[t].values()) for t in tests}
    count = collections.Counter(i for s in (imported, *reached.values()) for i in s)
    everything = imported.union(*reached.values())

    report: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "modules": {}, "per_test": {}}
    for mod in modules:
        stats = {k: v for k, v in analyses[mod].branch_stats().items() if in_scope(mod, k)}
        missing = sorted(n for n in analyses[mod].missing if in_scope(mod, n))
        report["modules"][mod] = {
            "n_statements": len(statements[mod]),
            "n_covered": len(statements[mod]) - len(missing),
            "missing_lines": missing,
            "n_branch_arcs": sum(t for t, _ in stats.values()),
            "n_branch_arcs_taken": sum(x for _, x in stats.values()),
            "covered_items": [label(i) for i in sorted(everything) if i[1] == mod],
        }
    for t in tests:
        run_phase = phases[t].get("run", set())
        lines = {m: sorted(i[2] for i in reached[t] if i[0] == "L" and i[1] == m) for m in modules}
        report["per_test"][t] = {
            "n_items": len(reached[t]),
            "phases": {p: len(phases[t][p]) for p in PHASES if p in phases[t]},
            "lines": {m: ns for m, ns in lines.items() if ns},
            "unique": [
                label(i) + ("" if i in run_phase else " (fixture)")
                for i in sorted(reached[t])
                if count[i] == 1
            ],
            "subline": [
                f"{m}:{n} {'/'.join(sorted(sites[m][n]))}"
                for m in modules
                for n in lines[m]
                if n in sites[m]
            ],
        }

    # Greedy minimum covering set over what only tests can supply.
    target = set().union(*reached.values()) - imported
    remaining, chosen = set(target), []
    while remaining:
        best = max(
            tests, key=lambda t: (len((reached[t] - imported) & remaining), -len(reached[t]))
        )
        if not (reached[best] - imported) & remaining:
            break
        chosen.append(best)
        remaining -= reached[best]
    report["cover"] = {"tests": chosen, "target_size": len(target), "union_items": len(everything)}
    report["provenance"] = {
        "coverage": coverage.__version__,
        "python": platform.python_version(),
        "modules": {m: hashlib.sha256(sources[m]).hexdigest() for m in modules},
        "ranges": {m: list(lo_hi) for m, lo_hi in sorted(ranges.items())},
    }
    return report


def summary(report: dict[str, Any], out: str) -> list[str]:
    lines = [
        f"{mod}: lines {m['n_covered']}/{m['n_statements']} "
        f"arcs {m['n_branch_arcs_taken']}/{m['n_branch_arcs']} missing={m['missing_lines']}"
        for mod, m in report["modules"].items()
    ]
    per_test = report["per_test"]
    redundant = [t for t, v in per_test.items() if not v["unique"]]
    lines.append(
        f"tests={len(per_test)} coverage-redundant={len(redundant)} cover={len(report['cover']['tests'])}"
    )
    for t in redundant:
        sub = per_test[t]["subline"]
        note = ""
        if sub:
            more = f" +{len(sub) - 3} more" if len(sub) > 3 else ""
            note = f"  (not seen by coverage: {', '.join(sub[:3])}{more})"
        lines.append(f"  coverage-redundant: {t}{note}")
    for t, v in per_test.items():
        via_fixture = [u for u in v["unique"] if u.endswith(" (fixture)")]
        if via_fixture:
            lines.append(f"  unique through a fixture: {t} ({len(via_fixture)} items)")
    lines.append(f"covering set: {report['cover']['tests']}")
    lines.append(f"wrote {out}")
    return lines


def diff_reports(base: dict[str, Any], after: dict[str, Any]) -> tuple[int, list[str]]:
    """Compare covered items by name: (0, ...) nothing lost, (1, ...) losses, (2, ...) incomparable."""
    for name, r in (("baseline", base), ("after", after)):
        if r.get("schema_version") != SCHEMA_VERSION:
            return 2, [
                f"{name} report has schema {r.get('schema_version')}, not {SCHEMA_VERSION}; "
                "re-run coverage_map.py for it"
            ]
    bp, ap = base["provenance"], after["provenance"]
    problems = [
        f"{mod}: source differs between the reports or is missing from one"
        for mod in sorted(set(bp["modules"]) | set(ap["modules"]))
        if bp["modules"].get(mod) != ap["modules"].get(mod)
    ]
    if bp["ranges"] != ap["ranges"]:
        problems.append(f"--range differs: {bp['ranges']} vs {ap['ranges']}")
    if bp["coverage"] != ap["coverage"]:
        problems.append(f"coverage version differs: {bp['coverage']} vs {ap['coverage']}")
    if problems:
        return 2, [
            *problems,
            "line numbers are comparable only for identical production sources and tooling",
        ]

    lines, lost_total = [], 0
    for mod, before in base["modules"].items():
        now = after["modules"][mod]["covered_items"]
        now_set, before_set = set(now), set(before["covered_items"])
        lost = [i for i in before["covered_items"] if i not in now_set]
        gained = [i for i in now if i not in before_set]
        lost_total += len(lost)
        lines.append(
            f"{mod}: {len(before_set)} -> {len(now_set)} covered items, "
            f"lost {len(lost)}, gained {len(gained)}"
        )
        lines += [f"  lost: {i}" for i in lost] + [f"  gained: {i}" for i in gained]
    if lost_total:
        lines.append(
            f"LOST {lost_total} covered items; find the deleted tests that owned them "
            "in the baseline's per_test table"
        )
        return 1, lines
    lines.append("nothing the baseline covered was lost")
    return 0, lines


def main(argv: list[str]) -> int:
    a = parse_args(argv)
    if a.diff:
        try:
            base, after = (json.loads(Path(p).read_text()) for p in a.diff)
        except (OSError, ValueError) as error:
            print(f"cannot read a report: {error}", file=sys.stderr)
            return 2
        code, lines = diff_reports(base, after)
        print("\n".join(lines), file=sys.stderr if code == 2 else sys.stdout)
        return code
    try:
        report = analyze(a.scratch, a.modules, a.ranges)
    except ReportError as error:
        print(error, file=sys.stderr)
        return 2
    Path(a.out).write_text(json.dumps(report, indent=1, sort_keys=True))
    print("\n".join(summary(report, a.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
