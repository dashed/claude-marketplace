#!/usr/bin/env python3
"""Static call-path census: which callables one entry point enters.

Usage:
    python3 hops.py <package_dir> <module>:<qualname> [options]

Options:
    --own REGEX            count hops whose module path matches REGEX as
                           "branch-owned" (e.g. 'billing/(routing|serve|resolve)\\.py')
    --exclude Q1,Q2,...    do not enter these callables (qualname, or module:qualname);
                           use it to prune arms the scenario cannot take
    --leaf-decorator NAME  enter a callable decorated with @NAME but do not
                           descend into its body (service wrappers, RPC stubs)
    --json                 machine-readable output

Walks the package with `ast` only. A call is resolved when its target is a
bare name defined or imported in the same module, `module.attr` through an
`import module`, `self.method` inside a class body, or `Klass.method` on a
class the package defines. `<anything>.method` is resolved *heuristically*
when exactly one class in the package defines that method name, and flagged.
Everything else is reported as unresolved -- never silently dropped. An
unresolved count of 0 is the only clean run.

The walk is path-INsensitive: it enters every arm that is statically
reachable. That is "what a reader must read to know what can happen", not
"what one input executes" -- see hops_dyn.py for the latter, and report both.

Module names are paths relative to <package_dir> with `/` -> `.`; an import
of `pkg.sub.mod` matches index module `sub.mod` by suffix. Two files with the
same basename in different directories are distinct modules here (unlike
code2flow, which merges them).
"""
import ast
import builtins
import json
import os
import re
import sys

BUILTIN_NAMES = set(dir(builtins))
# Method names that are overwhelmingly builtin-container calls; bucketed as
# builtin rather than unresolved so real unresolved targets stand out.
BUILTIN_METHODS = {
    "get", "items", "keys", "values", "append", "extend", "add", "update", "pop",
    "join", "split", "strip", "format", "startswith", "endswith", "lower", "upper",
    "copy", "setdefault", "discard", "remove", "sort", "index", "count", "encode",
    "decode", "replace", "clear", "insert", "isoformat", "union", "intersection",
    "difference", "popitem", "rstrip", "lstrip", "splitlines", "isdigit", "reverse",
}


class Module:
    def __init__(self, name, path, tree):
        self.name = name
        self.path = path
        self.tree = tree
        self.defs = {}        # qualname -> FunctionDef/AsyncFunctionDef
        self.def_lines = {}   # lineno -> qualname (def line and first decorator line)
        self.classes = {}     # class name -> ClassDef | None (functional NamedTuple)
        self.bases = {}       # class name -> [base names]
        self.imports = {}     # local name -> (module, attr | None)
        self.nested = set()   # qualnames of defs nested inside a def


def _collect(module):
    def visit(node, prefix, in_def):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = f"{prefix}{child.name}"
                module.defs[qual] = child
                module.def_lines[child.lineno] = qual
                if child.decorator_list:
                    module.def_lines[child.decorator_list[0].lineno] = qual
                if in_def:
                    module.nested.add(qual)
                visit(child, f"{qual}.", True)
            elif isinstance(child, ast.ClassDef):
                qual = f"{prefix}{child.name}"
                module.classes[qual] = child
                module.bases[qual] = [b.id for b in child.bases if isinstance(b, ast.Name)]
                visit(child, f"{qual}.", in_def)
            elif isinstance(child, ast.Assign) and isinstance(child.value, ast.Call):
                fn = child.value.func
                fname = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else None
                if fname in ("NamedTuple", "namedtuple", "TypedDict", "make_dataclass") and child.targets:
                    t = child.targets[0]
                    if isinstance(t, ast.Name):
                        module.classes[f"{prefix}{t.id}"] = None
                        module.bases[f"{prefix}{t.id}"] = []
            else:
                visit(child, prefix, in_def)
    visit(module.tree, "", False)
    for node in ast.walk(module.tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                module.imports[a.asname or a.name.split(".")[0]] = (a.name, None)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = module.name.split(".")
                parent = parts[: max(len(parts) - node.level, 0)]
                base = ".".join(p for p in [*parent, base] if p)
            for a in node.names:
                module.imports[a.asname or a.name] = (base, a.name)


def build_index(package_dir):
    package_dir = os.path.abspath(package_dir)
    index = {}
    for root, _dirs, files in os.walk(package_dir):
        for f in sorted(files):
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, package_dir)[:-3].replace(os.sep, ".")
            if rel.endswith(".__init__"):
                rel = rel[: -len(".__init__")]
            with open(path, encoding="utf-8") as fh:
                try:
                    tree = ast.parse(fh.read(), filename=path)
                except SyntaxError as exc:
                    print(f"warning: cannot parse {path}: {exc}", file=sys.stderr)
                    continue
            mod = Module(rel, path, tree)
            _collect(mod)
            index[rel] = mod
    return index


def resolve_module(index, name):
    if name in index:
        return index[name]
    for mod in sorted(index, key=len, reverse=True):
        if name.endswith("." + mod) or mod.endswith("." + name):
            return index[mod]
    return None


def _method_owners(index, attr):
    owners = []
    for mod in index.values():
        for cls in mod.classes:
            if f"{cls}.{attr}" in mod.defs:
                owners.append((mod, f"{cls}.{attr}"))
    return owners


def _class_lookup(index, mod, name):
    """Return (module, class_qualname) for a class name visible in `mod`, else None."""
    if name in mod.classes:
        return mod, name
    if name in mod.imports:
        target, attr = mod.imports[name]
        tmod = resolve_module(index, target) if attr else None
        if tmod and attr in tmod.classes:
            return tmod, attr
    return None


def _method_in_class(index, mod, cls, attr):
    """Find `attr` on class `cls` (walking Name bases within the package)."""
    seen = set()
    stack = [(mod, cls)]
    while stack:
        m, c = stack.pop()
        if (m.name, c) in seen:
            continue
        seen.add((m.name, c))
        if f"{c}.{attr}" in m.defs:
            return m, f"{c}.{attr}"
        for b in m.bases.get(c, []):
            found = _class_lookup(index, m, b)
            if found:
                stack.append(found)
    return None


def resolve_call(index, mod, qual, call):
    """Return a dict describing where one Call lands.

    kind: hop | ctor | heuristic | builtin | external | unresolved
    """
    fn = call.func
    line = call.lineno
    if isinstance(fn, ast.Name):
        name = fn.id
        if name in mod.defs and "." not in name:
            return {"kind": "hop", "target": (mod.name, name), "line": line}
        if f"{qual}.{name}" in mod.defs:
            return {"kind": "hop", "target": (mod.name, f"{qual}.{name}"), "line": line}
        found = _class_lookup(index, mod, name)
        if found:
            tmod, cls = found
            init = _method_in_class(index, tmod, cls, "__init__") or _method_in_class(index, tmod, cls, "__new__")
            return {"kind": "ctor", "type": (tmod.name, cls), "target": (init[0].name, init[1]) if init else None, "line": line}
        if name in mod.imports:
            target, attr = mod.imports[name]
            tmod = resolve_module(index, target)
            if tmod is None:
                return {"kind": "external", "name": f"{target}.{attr}", "line": line}
            if attr in tmod.defs:
                return {"kind": "hop", "target": (tmod.name, attr), "line": line}
            return {"kind": "unresolved", "name": f"{target}.{attr}", "why": "imported name is not a def or class in the index", "line": line}
        if name in BUILTIN_NAMES:
            return {"kind": "builtin", "name": name, "line": line}
        return {"kind": "unresolved", "name": name, "why": "bare name not defined/imported at module level (local variable, decorator-injected, or star import)", "line": line}
    if isinstance(fn, ast.Attribute):
        attr = fn.attr
        v = fn.value
        if isinstance(v, ast.Name):
            if v.id == "self" and "." in qual:
                cls = qual.rsplit(".", 1)[0]
                found = _method_in_class(index, mod, cls, attr)
                if found:
                    return {"kind": "hop", "target": (found[0].name, found[1]), "line": line}
                return {"kind": "unresolved", "name": f"self.{attr}", "why": "method not found on class or Name bases in index", "line": line}
            if v.id in mod.imports and mod.imports[v.id][1] is None:
                tmod = resolve_module(index, mod.imports[v.id][0])
                if tmod is None:
                    return {"kind": "external", "name": f"{v.id}.{attr}", "line": line}
                if attr in tmod.defs:
                    return {"kind": "hop", "target": (tmod.name, attr), "line": line}
                if attr in tmod.classes:
                    init = _method_in_class(index, tmod, attr, "__init__")
                    return {"kind": "ctor", "type": (tmod.name, attr), "target": (init[0].name, init[1]) if init else None, "line": line}
                return {"kind": "unresolved", "name": f"{v.id}.{attr}", "why": "attribute not a def/class of that module", "line": line}
            found = _class_lookup(index, mod, v.id)
            if found:
                m = _method_in_class(index, found[0], found[1], attr)
                if m:
                    return {"kind": "hop", "target": (m[0].name, m[1]), "line": line}
        owners = _method_owners(index, attr)
        if len(owners) == 1:
            return {"kind": "heuristic", "target": (owners[0][0].name, owners[0][1]), "name": f"<expr>.{attr}", "line": line}
        if len(owners) > 1:
            return {"kind": "unresolved", "name": f"<expr>.{attr}", "why": "ambiguous: " + ", ".join(f"{m.name}:{q}" for m, q in owners), "line": line}
        if attr in BUILTIN_METHODS:
            return {"kind": "builtin", "name": f".{attr}", "line": line}
        return {"kind": "unresolved", "name": f"<expr>.{attr}", "why": "no class in the index defines this method", "line": line}
    return {"kind": "unresolved", "name": ast.dump(fn)[:40], "why": "call target is not a Name or Attribute", "line": line}


def calls_in(node):
    """Call nodes in a def body, in source order. Descends into nested defs,
    lambdas and comprehensions (over-approximation: a nested def's calls are
    charged to the enclosing def even if the nested def is never invoked)."""
    return sorted((n for n in ast.walk(node) if isinstance(n, ast.Call)), key=lambda c: (c.lineno, c.col_offset))


def decorator_names(node):
    """Base names of a def's decorators: `@x`, `@m.x`, `@x(...)` all give `x`."""
    names = []
    for d in node.decorator_list:
        f = d.func if isinstance(d, ast.Call) else d
        if isinstance(f, ast.Name):
            names.append(f.id)
        elif isinstance(f, ast.Attribute):
            names.append(f.attr)
    return names


def trace(index, entry, exclude=(), leaf_decorator=None, own=None):
    """Walk from `entry` (module:qualname). Returns a dict of everything found.

    exclude: qualnames (or module:qualname) never entered.
    leaf_decorator: a def carrying @NAME is entered but not descended into.
    own: regex on module path or name; hops matching are counted as branch-owned.
    """
    mod_name, qual = entry.split(":", 1)
    mod = resolve_module(index, mod_name)
    if mod is None or qual not in mod.defs:
        raise SystemExit(f"entry {entry} not found; modules: {sorted(index)}")
    exclude = set(exclude)
    own_rx = re.compile(own) if own else None
    order = []
    visited = set()
    edges = []
    ctors = []
    heuristics = []
    unresolved = []
    externals = []
    builtins_seen = []
    excluded_hit = []
    leaves = []

    def visit(m, q):
        key = (m.name, q)
        if key in visited:
            return
        if q in exclude or f"{m.name}:{q}" in exclude:
            if key not in excluded_hit:
                excluded_hit.append(key)
            return
        visited.add(key)
        order.append(key)
        node = m.defs[q]
        if leaf_decorator and leaf_decorator in decorator_names(node):
            leaves.append(key)
            return
        for call in calls_in(node):
            r = resolve_call(index, m, q, call)
            r["from"] = key
            if r["kind"] in ("hop", "heuristic"):
                edges.append((key, r["target"]))
                if r["kind"] == "heuristic":
                    heuristics.append(r)
                tm, tq = r["target"]
                visit(index[tm], tq)
            elif r["kind"] == "ctor":
                ctors.append(r)
                if r["target"]:
                    edges.append((key, r["target"]))
                    tm, tq = r["target"]
                    visit(index[tm], tq)
            elif r["kind"] == "unresolved":
                unresolved.append(r)
            elif r["kind"] == "external":
                externals.append(r)
            else:
                builtins_seen.append(r)

    visit(mod, qual)
    by_module = {}
    for m, _q in order:
        by_module[m] = by_module.get(m, 0) + 1
    owned = [k for k in order if own_rx and (own_rx.search(index[k[0]].path) or own_rx.search(k[0]))]
    types = []
    for c in ctors:
        if c["type"] not in types:
            types.append(c["type"])
    return {
        "entry": entry,
        "order": order,
        "count": len(order),
        "own": own,
        "branch_owned": owned,
        "by_module": by_module,
        "edges": edges,
        "types_constructed": types,
        "heuristic": heuristics,
        "unresolved": unresolved,
        "external": externals,
        "builtin": builtins_seen,
        "excluded": excluded_hit,
        "leaves": leaves,
    }


def fmt(result):
    out = [f"entry: {result['entry']}", f"callables entered: {result['count']}"]
    if result["own"]:
        out.append(f"branch-owned (module matches {result['own']!r}): {len(result['branch_owned'])}")
    out.append("by module: " + ", ".join(f"{m} {n}" for m, n in result["by_module"].items()))
    out.append("path (pre-order):")
    owned = set(result["branch_owned"])
    leaves = set(result["leaves"])
    for i, (m, q) in enumerate(result["order"], 1):
        mark = (" *" if (m, q) in owned else "") + (" [leaf]" if (m, q) in leaves else "")
        out.append(f"  {i:3d} {m}:{q}{mark}")
    if result["excluded"]:
        out.append("excluded (reached, not entered): " + ", ".join(f"{m}:{q}" for m, q in result["excluded"]))
    out.append("types constructed on path: " + (", ".join(f"{m}:{c}" for m, c in result["types_constructed"]) or "none"))
    out.append(f"heuristic resolutions: {len(result['heuristic'])}" + "".join(
        f"\n  {r['from'][0]}:{r['from'][1]}:{r['line']} {r['name']} -> {r['target'][0]}:{r['target'][1]} (unique method name)" for r in result["heuristic"]))
    out.append(f"unresolved call sites: {len(result['unresolved'])}" + "".join(
        f"\n  {r['from'][0]}:{r['from'][1]}:{r['line']} {r['name']} -- {r['why']}" for r in result["unresolved"]))
    out.append(f"external (outside index): {len(result['external'])}" + "".join(
        f"\n  {r['from'][0]}:{r['from'][1]}:{r['line']} {r['name']}" for r in result["external"]))
    bi = {}
    for r in result["builtin"]:
        bi[r["name"]] = bi.get(r["name"], 0) + 1
    out.append("builtins skipped: " + (", ".join(f"{k} x{v}" for k, v in sorted(bi.items())) or "none"))
    return "\n".join(out)


def parse_options(argv):
    """Shared option parsing for the scripts that wrap trace()."""
    opts = {"exclude": (), "leaf_decorator": None, "own": None}
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--exclude":
            opts["exclude"] = tuple(x for x in argv[i + 1].split(",") if x)
            i += 2
        elif a == "--leaf-decorator":
            opts["leaf_decorator"] = argv[i + 1]
            i += 2
        elif a == "--own":
            opts["own"] = argv[i + 1]
            i += 2
        else:
            rest.append(a)
            i += 1
    return opts, rest


def main(argv):
    opts, rest = parse_options(argv[1:])
    if len(rest) < 2:
        print(__doc__)
        return 2
    index = build_index(rest[0])
    result = trace(index, rest[1], **opts)
    if "--json" in rest:
        print(json.dumps({k: v for k, v in result.items() if k != "edges"}, default=list, indent=1))
    else:
        print(fmt(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
