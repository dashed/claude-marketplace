#!/usr/bin/env python3
"""Path-level census: the per-function census, summed over a set of files or
over one static call path.

Usage:
    python3 path_census.py LABEL=file1.py,file2.py[:fn1,fn2,...] [LABEL2=...]
    python3 path_census.py --path <package_dir> <module>:<qualname> [hops.py options] [LABEL=... for comparison]
    python3 path_census.py --rows ...      also print the per-function rows

Per set: modules, defs, nested defs, sum/max cyclomatic (ruff C901 at
threshold 0, --isolated --ignore-noqa), DECISIONS, sum/max cognitive
(complexipy 7.0.1, --no-ignore, JSON), NLOC inside defs, file lines.

    decisions = sum(cyclo over top-level defs) - defs - nested_defs

Cyclomatic is additive over components and equals predicates + 1 per function
(McCabe 1976, p. 314), and ruff charges +1 per nested def, so subtracting both
counts leaves the number of predicates -- which extraction cannot change. If
a split did not lower it, the split removed nothing.

Two traps this script handles for you:
  * `@overload` stubs are rows in BOTH tools; rows are de-duplicated by
    (file, qualname), keeping the highest score, so 25 rows become 23 defs.
  * ruff scores a nested def on its own row AND inside its parent; nested
    rows are excluded from the sums (and counted in nested_defs).
It cannot fix: complexipy never reports methods of a class that is not at
column 0 (cog_missing shows how many defs have no cognitive row).

A `:fn1,fn2` suffix keeps only those function names (last segment or full
qualname) -- for selecting a path that is a subset of a large module.

Requires `ruff` on PATH and `uvx` (override with RUFF_CMD / COMPLEXIPY_CMD).
Refuses to run if `ruff --show-files` does not match every file given.
"""
import ast
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hops  # noqa: E402

RUFF_CMD = shlex.split(os.environ.get("RUFF_CMD", "ruff"))
COMPLEXIPY_CMD = shlex.split(os.environ.get("COMPLEXIPY_CMD", "uvx complexipy@7.0.1"))
RUFF_RE = re.compile(r"^(?P<path>.+?):(?P<line>\d+):\d+: C901 `(?P<name>.+?)` is too complex \((?P<score>\d+) > 0\)$")


def module_for(path):
    mod = hops.Module(path, path, ast.parse(open(path, encoding="utf-8").read(), filename=path))
    hops._collect(mod)
    return mod


def ruff_scores(files):
    """{(abspath, qualname): cyclo} (max over duplicate rows). Exits loudly if ruff saw no file."""
    files = [os.path.abspath(f) for f in files]
    seen = subprocess.run([*RUFF_CMD, "check", "--isolated", "--show-files", *files], capture_output=True, text=True).stdout.split()
    missing = [f for f in files if f not in seen]
    if missing:
        raise SystemExit(f"ruff --show-files did not match: {missing}")
    out = subprocess.run(
        [*RUFF_CMD, "check", "--isolated", "--ignore-noqa", "--select", "C901", "--config", "lint.mccabe.max-complexity=0",
         "--no-cache", "--output-format", "concise", *files], capture_output=True, text=True).stdout
    mods = {f: module_for(f) for f in files}
    scores = {}
    for line in out.splitlines():
        m = RUFF_RE.match(line.strip())
        if not m:
            continue
        p = os.path.abspath(m["path"])
        qual = mods[p].def_lines.get(int(m["line"]), m["name"])
        key = (p, qual)
        scores[key] = max(scores.get(key, 0), int(m["score"]))
    return scores, mods


def complexipy_scores(files):
    """{(abspath, qualname): cog} (max over duplicate rows); `Klass::method` becomes `Klass.method`."""
    files = [os.path.abspath(f) for f in files]
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "scores.json")
        proc = subprocess.run([*COMPLEXIPY_CMD, "--output-format", "json", "--output", out, "--no-ignore", "-q", *files],
                              capture_output=True, text=True, cwd=tmp)
        if not os.path.exists(out):
            raise SystemExit(f"complexipy wrote no JSON (exit {proc.returncode}):\n{proc.stdout}\n{proc.stderr}")
        rows = json.load(open(out))
    scores = {}
    for r in rows:
        key = (os.path.abspath(r["path"]), r["function_name"].replace("::", "."))
        scores[key] = max(scores.get(key, 0), int(r["complexity"]))
    return scores


def summarise(label, keys, cyc, cog, mods, nfiles, file_lines):
    top = [k for k in keys if k[1] not in mods[k[0]].nested]
    nested = [k for k in keys if k[1] in mods[k[0]].nested]
    cyc_vals = [cyc[k] for k in top if k in cyc]
    cog_vals = [cog[k] for k in top if k in cog]
    nloc = sum(mods[p].defs[q].end_lineno - mods[p].defs[q].lineno + 1 for p, q in top if q in mods[p].defs)
    return {
        "label": label, "modules": nfiles, "defs": len(top), "nested_defs": len(nested),
        "cyclo_sum": sum(cyc_vals), "cyclo_max": max(cyc_vals, default=0),
        "decisions": sum(cyc_vals) - len(cyc_vals) - len(nested),
        "cog_sum": sum(cog_vals), "cog_max": max(cog_vals, default=0),
        "cog_missing": len(top) - len(cog_vals), "nloc_defs": nloc, "file_lines": file_lines,
        "_rows": sorted(((p, q, cyc.get(k, "-"), cog.get(k, "-")) for k in top for p, q in [k]),
                        key=lambda r: (-(r[3] if isinstance(r[3], int) else -1), r[0], r[1])),
    }


COLS = ["label", "modules", "defs", "nested_defs", "cyclo_sum", "cyclo_max", "decisions", "cog_sum", "cog_max", "cog_missing", "nloc_defs", "file_lines"]


def print_table(rows, show_rows=False):
    widths = [max(len(c), *(len(str(r[c])) for r in rows)) for c in COLS]
    print("  ".join(c.ljust(w) for c, w in zip(COLS, widths)))
    for r in rows:
        print("  ".join(str(r[c]).ljust(w) for c, w in zip(COLS, widths)))
    if any(r["cog_missing"] for r in rows):
        print("cog_missing = defs ruff reported that complexipy did not (methods of non-top-level classes, `# complexipy: ignore`)")
    if show_rows:
        for r in rows:
            print(f"\n## {r['label']}  (function  cyclo  cog; sorted by cognitive)")
            for p, q, c, g in r["_rows"]:
                print(f"  {os.path.basename(p)}::{q}  {c}  {g}")


def select_keys(cyc, cog, fns):
    keys = sorted(set(cyc) | set(cog))
    if not fns:
        return keys
    return [k for k in keys if k[1] in fns or k[1].rsplit(".", 1)[-1] in fns]


def main(argv):
    show_rows = "--rows" in argv
    args = [a for a in argv[1:] if a != "--rows"]
    if not args:
        print(__doc__)
        return 2
    rows = []
    if args[0] == "--path":
        opts, rest = hops.parse_options(args[1:])
        pkg, entry = rest[0], rest[1]
        args = rest[2:]
        index = hops.build_index(pkg)
        result = hops.trace(index, entry, **opts)
        files = sorted({index[m].path for m, _ in result["order"]})
        cyc, mods = ruff_scores(files)
        cog = complexipy_scores(files)
        keys = [(os.path.abspath(index[m].path), q) for m, q in result["order"]]
        file_lines = sum(1 for f in files for _ in open(f))
        rows.append(summarise(f"path {entry}", keys, cyc, cog, mods, len(files), file_lines))
    for spec in args:
        label, _, rest = spec.partition("=")
        flist, _, fns = rest.partition(":")
        files = flist.split(",")
        fnset = set(fns.split(",")) if fns else None
        cyc, mods = ruff_scores(files)
        cog = complexipy_scores(files)
        keys = select_keys(cyc, cog, fnset)
        file_lines = sum(1 for f in files for _ in open(f))
        rows.append(summarise(label, keys, cyc, cog, mods, len(files), file_lines))
    print_table(rows, show_rows)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
