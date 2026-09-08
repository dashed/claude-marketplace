#!/usr/bin/env python3
"""Argument threading along a call path, and every site of a selector value.

Usage:
    python3 arg_threading.py <package_dir> [--entry <module>:<qualname>] [hops.py options] [--name NAME ...]

Threading table (always): for each parameter name, how many signatures in
scope declare it. A name carried through three or more signatures is a
pass-through variable -- the glue, whatever the individual bodies score.

Selector sites (per --name): every place the name is
  signatures  declared as a parameter (overload stubs flagged)
  producers   given a string literal (keyword `NAME=`, the matching positional
              slot of a def in the index, or `NAME = "..."`)
  forwards    passed on unchanged to another call (positional or keyword)
  compares    read by a Compare, `match`, or `if NAME` / `while NAME` / ternary
  other       every other Load (f-strings, dict values such as metric tags,
              subscripts, returns)
and the number of distinct functions that compare on it -- a value compared in
several functions to re-discover which public call was made.

Scope is the static path from --entry (hops.py; --exclude / --leaf-decorator
apply) or, without --entry, every def in the package. Without --entry, test
files in the package count as producers -- point it at a directory without
tests or give an entry.

Golf and its counter: renaming the selector at each layer boundary moves the
sites to new names; the threading table lists them. Run --name on every
parameter the table shows at >= 3.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hops  # noqa: E402


def own_params(fn):
    a = fn.args
    names = [p.arg for p in [*a.posonlyargs, *a.args, *a.kwonlyargs]]
    if a.vararg:
        names.append(a.vararg.arg)
    if a.kwarg:
        names.append(a.kwarg.arg)
    return [n for n in names if n not in ("self", "cls")]


def param_index(fn, name):
    names = [p.arg for p in [*fn.args.posonlyargs, *fn.args.args]]
    return names.index(name) if name in names else None


def selector_sites(index, scope, name):
    sig, prod, fwd, cmp_, other = [], [], [], [], []
    cmp_funcs = set()
    covered = set()

    def site(mod, q, node):
        return f"{mod.name}:{q}:{node.lineno}"

    for mod, q in scope:
        fn = mod.defs[q]
        if name in own_params(fn):
            sig.append(site(mod, q, fn))
        # The index keeps one def per qualname (the implementation); the
        # @overload stubs that shadow it are still signatures the reader meets.
        for node in ast.walk(mod.tree):
            if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not fn
                    and node.name == q.rsplit(".", 1)[-1] and "overload" in hops.decorator_names(node)
                    and name in own_params(node)):
                sig.append(site(mod, q, node) + " (overload stub)")
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == name and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        prod.append(site(mod, q, node) + f' {name}="{kw.value.value}"')
                    if isinstance(kw.value, ast.Name) and kw.value.id == name:
                        fwd.append(site(mod, q, node))
                        covered.add(id(kw.value))
                r = hops.resolve_call(index, mod, q, node)
                target = r.get("target") if r["kind"] in ("hop", "heuristic") else None
                if target:
                    tfn = index[target[0]].defs[target[1]]
                    i = param_index(tfn, name)
                    if i is not None and i < len(node.args) and isinstance(node.args[i], ast.Constant) and isinstance(node.args[i].value, str):
                        prod.append(site(mod, q, node) + f' "{node.args[i].value}" -> {target[0]}:{target[1]}')
                for arg in node.args:
                    if isinstance(arg, ast.Name) and arg.id == name:
                        fwd.append(site(mod, q, node))
                        covered.add(id(arg))
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == name and isinstance(node.value, ast.Constant):
                        prod.append(site(mod, q, node) + f' {name} = "{node.value.value}"')
            elif isinstance(node, ast.Compare):
                operands = [node.left, *node.comparators]
                if any(isinstance(o, ast.Name) and o.id == name for o in operands):
                    cmp_.append(site(mod, q, node) + " " + ast.unparse(node)[:60])
                    cmp_funcs.add(f"{mod.name}:{q}")
                    covered.update(id(o) for o in operands if isinstance(o, ast.Name) and o.id == name)
            elif isinstance(node, ast.Match) and isinstance(node.subject, ast.Name) and node.subject.id == name:
                cmp_.append(site(mod, q, node) + " match")
                cmp_funcs.add(f"{mod.name}:{q}")
                covered.add(id(node.subject))
            elif isinstance(node, (ast.If, ast.While, ast.IfExp)) and isinstance(node.test, ast.Name) and node.test.id == name:
                cmp_.append(site(mod, q, node) + " truthiness")
                cmp_funcs.add(f"{mod.name}:{q}")
                covered.add(id(node.test))
        for node in ast.walk(fn):
            if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Load) and id(node) not in covered:
                other.append(site(mod, q, node))
    return sig, prod, fwd, cmp_, other, cmp_funcs


def main(argv):
    opts, rest = hops.parse_options(argv[1:])
    if not rest:
        print(__doc__)
        return 2
    index = hops.build_index(rest[0])
    names = [rest[i + 1] for i, a in enumerate(rest) if a == "--name" and i + 1 < len(rest)]
    if "--entry" in rest:
        entry = rest[rest.index("--entry") + 1]
        path = hops.trace(index, entry, **opts)["order"]
        scope = [(index[m], q) for m, q in path]
        print(f"scope: static path from {entry} ({len(scope)} callables)")
    else:
        scope = [(mod, q) for mod in index.values() for q in mod.defs]
        print(f"scope: every def in {rest[0]} ({len(scope)} callables)")
    threading = {}
    for mod, q in scope:
        for p in own_params(mod.defs[q]):
            threading[p] = threading.get(p, 0) + 1
    print("argument threading (parameter -> signatures in scope declaring it; >= 2 shown):")
    for p, k in sorted(threading.items(), key=lambda kv: (-kv[1], kv[0])):
        if k >= 2:
            print(f"  {p:28s} {k}")
    for name in names:
        sig, prod, fwd, cmp_, other, cmp_funcs = selector_sites(index, scope, name)
        total = len(sig) + len(prod) + len(fwd) + len(cmp_) + len(other)
        print(f"\nselector `{name}`: {total} sites")
        for label, rows in (("signatures", sig), ("producers", prod), ("forwards", fwd), ("compares", cmp_), ("other reads", other)):
            print(f"  {label:12s} {len(rows)}")
            for r in rows:
                print(f"      {r}")
        print(f"  functions that compare on it: {len(cmp_funcs)}  {sorted(cmp_funcs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
