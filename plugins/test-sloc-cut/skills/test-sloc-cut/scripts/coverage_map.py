#!/usr/bin/env python3
"""Per-test unique coverage and a verified minimum covering set.

Usage:
    python3 coverage_map.py --scratch DIR [--range MOD=LO-HI ...] [--out FILE] MODULE [MODULE ...]

Reads the coverage data file that a serial, per-test-context pytest run
wrote into DIR (see references/coverage-and-mutants.md for the .coveragerc
and the pytest command) and, for the production MODULEs (repo-relative
paths, as they appear in the data file), writes DIR/analysis.json with:

  modules   per module: statements, covered, missing lines, branch arcs,
            branch arcs taken
  per_test  per test context: item count and the lines/arcs no other test
            reaches ("unique"); an arc into an except handler is tagged
            (exc) because coverage's static arc model does not list it
  cover     a greedy minimum covering set over what only tests can supply
            (import-time coverage, context "", is excluded), and its size

A test with an empty "unique" list is coverage-redundant. That is NOT
assertion-redundant: two tests can walk the same lines and assert
different values. Delete only on the intersection with the fact matrix.

Leave-one-out is not a licence either: if exactly two tests reach a line,
neither is unique, yet dropping both loses the line. That is what the
covering set is for -- verify it by running only those tests with the
same .coveragerc and comparing the item union to this baseline.

--range MOD=LO-HI scopes a large module to the functions under test
(e.g. --range pkg/big.py=558-689). Requires `coverage` importable in the
same environment that ran the tests (`uvx --with coverage python3 ...`).
"""
import argparse
import collections
import json
import sys

try:
    import coverage
    from coverage.sqldata import CoverageData
except ImportError:
    print("coverage is not importable; run with the test environment's interpreter or `uvx --with coverage python3 coverage_map.py ...`", file=sys.stderr)
    sys.exit(2)


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scratch", required=True, help="directory holding .coverage and .coveragerc")
    p.add_argument("--range", action="append", default=[], metavar="MOD=LO-HI", help="restrict MOD to lines LO..HI")
    p.add_argument("--out", default=None, help="output JSON path (default: <scratch>/analysis.json)")
    p.add_argument("modules", nargs="+", help="repo-relative module paths as recorded in the data file")
    a = p.parse_args(argv)
    a.ranges = {}
    for spec in a.range:
        mod, _, lo_hi = spec.partition("=")
        lo, _, hi = lo_hi.partition("-")
        a.ranges[mod] = (int(lo), int(hi))
    a.out = a.out or f"{a.scratch}/analysis.json"
    return a


def main(argv):
    a = parse_args(argv)
    modules = a.modules

    def in_scope(mod, line):
        lo_hi = a.ranges.get(mod)
        return True if lo_hi is None else lo_hi[0] <= abs(line) <= lo_hi[1]

    cov = coverage.Coverage(data_file=f"{a.scratch}/.coverage", config_file=f"{a.scratch}/.coveragerc")
    cov.load()
    data = CoverageData(basename=f"{a.scratch}/.coverage")
    data.read()
    measured = set(data.measured_files())
    missing_mods = [m for m in modules if m not in measured]
    if missing_mods:
        print(f"not in the data file: {missing_mods}\nmeasured files: {sorted(measured)}", file=sys.stderr)
        return 2
    contexts = sorted(data.measured_contexts())
    tests = [c for c in contexts if c]           # "" is the import-time context
    if not tests:
        print("no per-test contexts in the data file; run pytest with --cov-context=test (and no dynamic_context in the rcfile)", file=sys.stderr)
        return 2

    analyses = {m: cov._analyze(m) for m in modules}
    statements = {m: {l for l in analyses[m].statements if in_scope(m, l)} for m in modules}
    static_arcs = {m: set(analyses[m].arc_possibilities_set) for m in modules}

    def endpoint_ok(mod, value):
        # negative values are function or module exits; positive ones must be real statements
        return in_scope(mod, value) and (value < 0 or value in statements[mod])

    def items_for(context):
        data.set_query_context(context)
        items = set()
        for mod in modules:
            items |= {("L", mod, l) for l in (data.lines(mod) or []) if l in statements[mod]}
            items |= {("A", mod, x, y) for (x, y) in (data.arcs(mod) or [])
                      if endpoint_ok(mod, x) and endpoint_ok(mod, y)}
        return items

    sets = {c: items_for(c) for c in contexts}
    data.set_query_context(None)

    count = collections.Counter(i for c in contexts for i in sets[c])
    report = {"modules": {}, "per_test": {}}
    for mod in modules:
        stats = {k: v for k, v in analyses[mod].branch_stats().items() if in_scope(mod, k)}
        missing = sorted(m for m in analyses[mod].missing if in_scope(mod, m))
        report["modules"][mod] = {
            "n_statements": len(statements[mod]),
            "n_covered": len(statements[mod]) - len(missing),
            "missing_lines": missing,
            "n_branch_arcs": sum(t for t, _ in stats.values()),
            "n_branch_arcs_taken": sum(x for _, x in stats.values()),
        }
    for c in tests:
        unique = sorted(i for i in sets[c] if count[i] == 1)
        report["per_test"][c] = {
            "n_items": len(sets[c]),
            "unique": [f"{i[1]}:{i[2]}" if i[0] == "L"
                       else f"{i[1]}:{i[2]}->{i[3]}" + ("" if (i[2], i[3]) in static_arcs[i[1]] else " (exc)")
                       for i in unique],
        }

    # Greedy minimum covering set over what only tests can supply.
    imported = sets[""] if "" in sets else set()
    target = set().union(*(sets[c] for c in tests)) - imported
    remaining, chosen = set(target), []
    while remaining:
        best = max(tests, key=lambda c: (len((sets[c] - imported) & remaining), -len(sets[c])))
        if not (sets[best] - imported) & remaining:
            break
        chosen.append(best)
        remaining -= sets[best]
    report["cover"] = {"tests": chosen, "target_size": len(target), "union_items": len(target | imported)}

    json.dump(report, open(a.out, "w"), indent=1, sort_keys=True)
    for mod, m in report["modules"].items():
        print(f"{mod}: lines {m['n_covered']}/{m['n_statements']} "
              f"arcs {m['n_branch_arcs_taken']}/{m['n_branch_arcs']} missing={m['missing_lines']}")
    redundant = [c for c in tests if not report["per_test"][c]["unique"]]
    print(f"tests={len(tests)} coverage-redundant={len(redundant)} cover={len(chosen)}")
    for c in redundant:
        print(f"  coverage-redundant: {c}")
    print(f"covering set: {chosen}")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
