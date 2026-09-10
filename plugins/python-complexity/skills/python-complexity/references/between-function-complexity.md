# Between-function complexity

How to measure the complexity that a per-function census cannot see: the cost that moves *between*
functions when logic is spread across many small ones. The per-function census locates a function
that is hard to read; this file locates a *path* that is hard to read although every function on
it scores low. It is the same two tool runs, summed, plus three counts no census gives.

The judgment layer — which layers protect an invariant and which are glue — is
[layering-review.md](layering-review.md). This file is the measurement layer.

**Provenance.** Every number below was measured on ruff 0.12.7 (`C901`, `PLR*`) and complexipy
7.0.1, macOS, on **Python 3.10.15 and 3.14.7** — both were run; the only difference found is in
`hops_dyn.py`'s synthetic-frame count (comprehensions are inlined from 3.12, PEP 709). ruff 0.14.10
gave byte-identical `C901` output on the real case; 0.16.6 was used for the PLR preview-status table.
code2flow 2.5.1. The scripts are in `scripts/` beside this file; the `triple/` and `golf/` fixtures
and `test_equiv.py` that the pasted commands run against are not shipped — the pasted outputs are
the verification, substitute your own package. The real case is a read path in a large Django
monorepo; its numbers are quoted, its identifiers are not. Where a claim is inference
rather than measurement it is labelled **(inferred)**.

## Table of contents

- [Definitions](#definitions)
- [The layering triple](#the-layering-triple)
- [Two sums from the census you already ran](#two-sums-from-the-census-you-already-ran)
- [Callables entered](#callables-entered)
- [Argument threading and selector sites](#argument-threading-and-selector-sites)
- [Intermediate representations](#intermediate-representations)
- [Predicting what a refactor breaks](#predicting-what-a-refactor-breaks)
- [Tools that see the non-branching blind spots](#tools-that-see-the-non-branching-blind-spots)
- [Silent failures of every tool in this file](#silent-failures-of-every-tool-in-this-file)
- [Reading the numbers: ratio to a baseline, never a threshold](#reading-the-numbers-ratio-to-a-baseline-never-a-threshold)
- [What these cannot see](#what-these-cannot-see)
- [Unverified](#unverified)

## Definitions

Used verbatim in SKILL.md; defined once here.

**Hop / callables entered.** A hop is a `def` whose body a reader must read to follow one public
call. *Static* callables entered is every def reachable from the entry by resolvable calls — every
arm, including the ones a given input never takes: what a reader must read to know what *can*
happen. *Dynamic* callables entered is every def whose frame was actually created during one call:
what one input executes. They answer different questions; report both.

**Branch-owned.** The hops that live in the modules under review (`--own REGEX`), as opposed to
pre-existing plumbing any caller would pay for (service wrappers, serializers, ORM).

**Glue hops.** Branch-owned hops between the public entry and the first callable that computes
the answer. Measured by subtraction: run `hops.py` from the entry, run it again from the computing
callable, and subtract the second branch-owned count from the first.

**Argument threading.** For one parameter name, the number of signatures on the path that declare
it. Three or more is a pass-through variable — a value carried down a chain of methods that only
the last one uses. It is the glue, whatever the individual bodies score.

**Selector.** A parameter whose value is compared in more than one function to re-discover which
public call was made. Its *sites* are counted by role: signatures declaring it, producers giving
it a literal, forwards passing it on unchanged, compares reading it, and every other read (metric
tags, log fields, f-strings).

**Intermediate representation.** A package-defined type (class, dataclass, NamedTuple, TypedDict)
constructed on the path, or a callable on the path that returns an ad-hoc tuple. The shapes a
reader must hold between the entry and the value served.

**Decisions.** `Σ cyclomatic over top-level defs − defs − nested defs`: the number of predicates
on the path. Invariant under extraction, because each new def costs exactly the +1 the split adds.

**Path census.** The per-function census summed over a file set or a static path: Σ cognitive,
decisions, defs, modules, NLOC — read against a baseline.

**Baseline.** The path the code replaced, or a sibling that solves the same problem in the same
codebase. There are no thresholds between functions; there are only ratios.

## The layering triple

The analogue of `gate_flat` / `gate_nested` / `gate_ternary` in
[interpreting-scores.md](interpreting-scores.md): one behaviour, three shapes.

- **`mono`** — one 64-line function: a per-category table with overrides, an org-wide scalar, a
  lift rule that substitutes 90 for eligible categories, a missing-category default, three read
  shapes selected inside by a `method` string.
- **`layered`** — the same behaviour split into 26 functions across three modules in the style of
  the real case: `method: Literal[...]` threaded through ten signatures and compared in six
  functions; a NamedTuple whose two booleans exist only to choose a metric tag; two fallback
  helpers that are value-identical for every input the resolver can produce; a full-table rebuild
  to answer one category. Split one round further than first written, until every function scored
  cognitive ≤ 3 — the move a layer-golfer makes.
- **`seamed`** — the same behaviour split by meaning into 9 functions: one resolve-and-lift pass
  into a `Resolved` dataclass with the three reads as methods, three typed entry points, no
  selector, one fallback object.

`test_equiv.py`: 2 seeds × 20,000 random contracts × 15 reads = **600,000 comparisons, 0
mismatches** (inputs include 0, 89/90/91, 395/396 and `None` tiers).

### The per-function census is inverted

```
ruff check --isolated --ignore-noqa --select C901 --config "lint.mccabe.max-complexity=0" --no-cache --output-format concise triple/
uvx complexipy@7.0.1 --output-format json --output scores.json --no-ignore -q triple/
```

| Shape | Defs | max cyclo / cog | Functions with cog > 4 |
|---|---:|---:|---:|
| `mono` | 1 | **20 / 47** | 1 |
| `layered` | 26 | **3 / 3** | 0 |
| `seamed` | 9 | 4 / 7 | 1 |

Reading the pair the way SKILL.md prescribes — sort by cognitive, tie-break by the gap, read the
top — ranks `mono` as the target (correct) and then **ranks `layered` as the best of the three**.
Every one of its 26 functions passes every threshold in the skill. Per-function metrics do not
merely fail to distinguish the pass-through split from the by-meaning split; they prefer the wrong
one.

### Metric × shape

Entry points `mono:retention`, `layered_routing:get_standard`, `seamed:standard`; every row
measured with the command in its section below.

| Metric | `mono` | `layered` | `seamed` | Separates layered from seamed? |
|---|---:|---:|---:|---|
| max cyclo / max cog (per function) | 20 / 47 | 3 / 3 | 4 / 7 | **No — inverted** |
| decisions (Σcyclo − defs) | 19 | 20 | 9 | Yes, 2.2× |
| Σcog | 47 | 38 | 20 | Yes, 1.9× |
| defs / modules | 1 / 1 | 26 / 3 | 9 / 1 | Yes |
| callables entered, static | 1 | **24** | 5 | Yes, 4.8× |
| callables entered, dynamic (one input) | 1 | 19 (21 invocations) | 5 (6 invocations) | Yes, 3.8× |
| max argument threading | 1 | **10** (`method`); `resolved` 8, `category` 7, `contract` 7 | 2 | Yes, 5× |
| parameters threaded through ≥ 3 signatures | 0 | 6 | 0 | Yes |
| selector sites / compares / functions comparing | 6 / 5 / 1 | **29 / 8 / 6** | 0 / 0 / 0 | Yes |
| types constructed on path | 0 | 3 | 2 | Weak |
| NLOC inside defs / file lines | 54 / 64 | 128 / 226 | 58 / 100 | Yes, 2.2× |

The real case has the same silhouette: 24 branch-owned hops, a selector with 8 compares in 4
functions across 8 signatures, 5 intermediate types.

**The thesis.** Golfing the path metrics — inlining until hops fall — pushes code toward `mono`,
which the per-function census catches at 20 / 47. Golfing the per-function census — splitting
until every max is green — pushes code toward `layered`, which the path census catches at 24 hops
and a name threaded through ten signatures. Each census catches the other's golf. It is the
argument the skill already makes for running cyclomatic and cognitive together, one level up.

## Two sums from the census you already ran

Both come from the outputs of the two commands above. No new tool.

**Σ cognitive.** Campbell's white paper (v1.7, p. 6) says the metric "does not increment for
methods" by design, and (p. 10) that "because Cognitive Complexity does not increment for the
method structure, aggregate numbers become useful." Σcog is the aggregate the metric's author
endorses. It is *not* conserved under extraction — nesting penalties vanish when a body moves out
— so it drifts down under layer-golf: 47 → 38 → 20. But 47 → 38 is not 47 → 3; the sum falls 19 %
where the max falls 94 %.

**Decisions.** McCabe 1976 (p. 314) proves that "the complexity of a collection C of control
graphs with k connected components is equal to the summation of their complexities," and that for
a structured program *v = π + 1* (predicates plus one). So Σv over a path is Σπ + defs, and
**Σv − defs is the predicate count**, which extraction cannot change. (Definition 1 in the paper is
`e − n + p`; `e − n + 2p` is the program form after the virtual exit→entry edge — say which one if
you quote it.) Measured: 19 → 20 → 9. Splitting one function into 26 removed no decision and added
one (the re-dispatch on `method`); splitting by meaning removed ten.

Why raw Σcyclo must not be summed: Campbell (p. 4) — "because each method has a minimum Cyclomatic
Complexity score of one, it is impossible to know whether any given class with a high aggregate
Cyclomatic Complexity is a large, easily maintained domain class, or a small class with a complex
control flow … of little use above the method level." Subtracting the def count removes exactly
that +1. Two further traps: ruff scores a nested def on its own row *and* inside its parent, so
nested rows double-count — sum top-level rows only and subtract the nested count too (ruff charges
+1 per nested def; `register` in interpreting-scores.md scores 6 with zero conditionals); and
`@overload` stubs are rows in **both** tools (ruff 1 each, complexipy 0), so `defs` inflates by the
stub count — on the real case 25 rows for 23 defs. Decisions is stub-invariant (59 − 25 = 57 − 23 =
34) because each stub adds 1 to Σ and 1 to defs; Σcog is unaffected because stubs score 0.

The one-liners, over the census outputs for `layered`:

```bash
grep C901 ruff.txt | awk -F'[()]' '{split($2,a," "); s+=a[1]; n++} END {print "defs="n, "sum_cyclo="s, "decisions="s-n}'
# defs=26 sum_cyclo=46 decisions=20
jq '{defs: length, sum_cog: (map(.complexity) | add), max_cog: (map(.complexity) | max)}' scores.json
# {"defs": 26, "sum_cog": 38, "max_cog": 3}
```

(`seamed`: `defs=9 sum_cyclo=18 decisions=9` / `sum_cog 20`; `mono`: `defs=1 sum_cyclo=20
decisions=19` / `sum_cog 47`.) complexipy 7.0.1 prints **no per-file or per-run total in any
output format** — `--plain` is one row per function, the default report ends with "All functions
are within the allowed complexity." and no sum, and the JSON rows carry only `complexity`,
`file_name`, `function_name`, `path`, `refactor_plans` — so Σcog is always computed, never read.
The awk line counts every ruff row, so it is only right when there are no nested defs and no
overload stubs. `scripts/path_census.py` handles both: it maps each row
to a qualname, drops nested rows from the sums, keeps the maximum over duplicate rows, and refuses
to run if `ruff --show-files` did not match every file.

```
$ python3 scripts/path_census.py mono=triple/mono.py layered=triple/layered_routing.py,triple/layered_serve.py,triple/layered_read.py seamed=triple/seamed.py
label    modules  defs  nested_defs  cyclo_sum  cyclo_max  decisions  cog_sum  cog_max  cog_missing  nloc_defs  file_lines
mono     1        1     0            20         20         19         47       47       0            54         64
layered  3        26    0            46         3          20         38       3        0            128        226
seamed   1        9     0            18         4          9          20       7        0            58         100
```

`LABEL=files:fn1,fn2` keeps only the named functions — for a path that is a subset of a large
module. `--path <pkg> <entry>` restricts the set to what `hops.py` reaches (for `layered`: 24 defs,
Σcyclo 44, decisions 20, Σcog 38 — the two unreached entry points drop out). `--rows` prints the
per-function rows sorted by cognitive. `cog_missing` counts defs ruff reported that complexipy did
not — methods of a class not at column 0, or a `# complexipy: ignore`.

## Callables entered

### Static: `scripts/hops.py`

```
$ python3 scripts/hops.py triple layered_routing:get_standard
entry: layered_routing:get_standard
callables entered: 24
by module: layered_routing 2, layered_serve 12, layered_read 10
path (pre-order):
    1 layered_routing:get_standard
    2 layered_routing:route
    3 layered_serve:stack_default
    4 layered_serve:serve
    5 layered_read:resolve
    …
   24 layered_serve:track
types constructed on path: layered_read:CategoryRetention, layered_read:Resolved, layered_serve:ServedCategory
heuristic resolutions: 0
unresolved call sites: 0
external (outside index): 0
builtins skipped: .append x1, .get x3, .items x4, .values x1, any x1, bool x1, frozenset x3, min x1, tuple x1
```

`seamed:standard` enters 5 (one `heuristic` resolution: `<expr>.standard` resolved to
`Resolved.standard` because exactly one class in the package defines that method name — printed,
so you can check it); `mono:retention` enters 1.

Resolution rules, so the number can be checked: a bare name defined or imported in the module;
`module.attr` through `import module`; `self.method` walking `Name` bases; `Klass.method`; a nested
def called from its parent; `<expr>.method` when exactly one class defines that name (`heuristic`);
ambiguous names listed with candidates; `_OPS[k](x)`, `getattr(o, n)(x)`, `fn(x)` on a parameter →
`unresolved` with the reason. A constructor counts as a type constructed, and as a hop only if the
class defines `__init__` or `__new__` — dataclass and NamedTuple constructors are generated in
`<string>` and are invisible to the dynamic tracer too, so the two agree. Calls inside a nested def,
lambda or comprehension are charged to the enclosing def (an over-approximation, stated).

**An unresolved count of 0 is the only clean run.** Anything else is a hole in the number, and the
script prints every hole with its reason rather than hiding it.

On object-heavy code the holes are large and the count is a **floor**. Measured on the `coverage`
package (7.16.0 source, 5,445 lines): from `Coverage.start`, 144 callables entered with **63
heuristic and 169 unresolved** sites — `self.debug.should` ×32, `.write` ×27, `.read` ×11 land
in "ambiguous" because the script does no attribute-type inference. Report such a run as
"≥ 144, 169 unresolved", scope the entry to the path under review, use `--leaf-decorator` for
service boundaries, and prefer the dynamic count when the package can be imported (`start()`
plus `stop()` traced 67 callables, 17 branch-owned). A static count quoted without its buckets
is the between-function version of a clean run that measured nothing.

### Dynamic: `scripts/hops_dyn.py`

```
$ python3 scripts/hops_dyn.py triple --setup "import layered_routing as L" \
    --call "L.get_standard({'defaults': {'error': (30, 10)}, 'overrides': {}, 'org_days': None, 'grandfathered': True}, 'error', frozenset({'error'}))"
call: L.get_standard({…}, 'error', frozenset({'error'}))
result: 90
callables entered: 19  (invocations: 21)
by module: layered_routing 2, layered_serve 7, layered_read 10
path (first entry order):
    1 layered_routing:get_standard  x1
    …
    6 layered_read:standard_days  x2
    …
   13 layered_read:lifted_names  x2
    …
   19 layered_serve:track  x1
comprehension/lambda code objects entered: 6 over 2 sites
```

(On 3.10 the last line reads `8 over 4 sites` — pre-3.12 comprehensions have their own frames.
Every other line is identical.) `seamed:standard` for the same input enters 5 with 6 invocations
(`_resolve_category ×2`).

**Static 24 > dynamic 19**, because the static walk enters `stack_default`, `resolved_fallback`,
`all_retentions`, `scalar_days` and `missing_category_days` — the arms this input does not take.
Static is what a reader must read to know what can happen; dynamic is what one input executes.
Report both; they answer different questions. The dynamic **invocation counts** expose the
rebuild-everything-to-read-one pattern directly: `standard_days ×2` and `lifted_names ×2` for a
single-category read of a one-category table, and on a three-category table the fixture report
measured `resolve_category ×3`, `standard_days ×5`, `serve_category ×3`.

### Pruning: what the reader must read for one scenario

A static count includes every arm. To count what a *scenario* reads (a migrated organisation, a
cache miss), prune by hand:

- `--exclude Q1,Q2` — do not enter these callables (arms the scenario cannot take: the error
  fallback, the empty-result fallback, the whole-mapping read).
- `--leaf-decorator NAME` — enter a callable carrying `@NAME` but do not descend into it (RPC
  wrappers, `@service_method`, anything whose body is pre-existing plumbing).
- `--own REGEX` — count hops whose module path matches as branch-owned.

On the real case, unpruned static gave **24** branch-owned callables (three independently written
resolvers agreed on 24; `code2flow` started below the router also gave 24). With three arms
excluded and the two service wrappers as leaves it gave **19** hops plus 2 generated constructors on
the path — the hand count's 21, which had counted the constructors. State which definition you
used; the two are one flag apart.

### Glue hops, by subtraction

Run from the entry with `--own`, then from the first callable that computes (the resolver, the
service call — the first def whose body produces the answer rather than routing towards it) with
the same `--own`; subtract:

```bash
python3 scripts/hops.py pkg routing:get_standard --own 'routing|serve|resolve' | grep branch-owned
python3 scripts/hops.py pkg resolve:resolve     --own 'routing|serve|resolve' | grep branch-owned
```

Real case, by the script: 19 − 10 = **9** glue hops between the public
entry and the resolver. Counting the two generated constructors as the hand count did (and as the
before/after table in [layering-review.md](layering-review.md) does): 21 − 11 = **10** — the number
the layering argument rests on, and the one that fell to 4 in the proposed shape. Say which
definition you used.

## Argument threading and selector sites

`scripts/arg_threading.py` prints two things: the threading table for the scope, and — per
`--name` — every site of one value by role.

```
$ python3 scripts/arg_threading.py triple --entry layered_routing:get_standard --name method
scope: static path from layered_routing:get_standard (24 callables)
argument threading (parameter -> signatures in scope declaring it; >= 2 shown):
  method                       10
  resolved                     8
  category                     7
  contract                     7
  lift_categories              6
  org_days                     3
  default                      2
  override                     2

selector `method`: 29 sites
  signatures   10
  producers    1
      layered_routing:get_standard:13 "standard" -> layered_routing:route
  forwards     9
  compares     8
      layered_serve:stack_default:29 method == 'all'
      layered_serve:stack_default:31 method == 'standard'
      …
  other reads  1
      layered_serve:track:25
  functions that compare on it: 6  ['layered_serve:category_days', 'layered_serve:missing_category_days', 'layered_serve:resolved_fallback', 'layered_serve:scalar_days', 'layered_serve:stack_default', 'layered_serve:to_read_shape']
```

`seamed:standard`: no parameter carried through more than 2 signatures; `method` has 0 sites. On
the real case, package scope (no `--entry`) gave **37 sites**: 10 signatures (8 plus the 2
`@overload` stubs, flagged `(overload stub)`), 3 producers, 13 forwards, 8 compares, 3 other reads,
in **4 comparing functions** — every role the hand count named, one site short of its 38 total,
the difference being the alias definition. From the public read with `--entry` it is 33 (8 / 1 /
13 / 8 / 3): the stubs are shadowed and only the one producer on that path is in scope.

**Why `rg` cannot do this.** On the real case, for one name: `rg -ow` gives 44 occurrences (it
double-counts `"method": method` and matches prose), `rg -cw` gives 37 lines, an `ast` role count
gives 37 sites in five roles. Only the roles say what the value is *for* — a value that is forwarded
eight times and compared eight times in four functions exists to re-discover the caller.

**Scope.** With `--entry`, the scope is the static path, which sees one def per qualname (overload
stubs are shadowed by the implementation) and only the producers on that path. For the full
producer count run without `--entry` on a directory that has no tests — test files count as
producers otherwise.

**The golf, measured.** Rename the selector at each layer boundary (`method` → `kind` in the serve
layer → `shape` in the leaf readers). The single-name count collapses; the threading table does not:

```
$ python3 scripts/arg_threading.py golf --entry layered_routing:get_standard --name method --name kind --name shape
argument threading (parameter -> signatures in scope declaring it; >= 2 shown):
  resolved                     8
  category                     7
  contract                     7
  kind                         6
  lift_categories              6
  org_days                     3
  shape                        3
  …
selector `method`: 4 sites   (signatures 1, producers 1, forwards 2, compares 0; 0 functions)
selector `kind`: 18 sites    (signatures 6, forwards 6, compares 5; 3 functions)
selector `shape`: 7 sites    (signatures 3, forwards 1, compares 3; 3 functions)
```

29 / 8 / 6 became 4 / 0 / 0 for `method` — and `kind 6, shape 3` in the threading table is where a
reader looks next. Hops are unchanged at 24. Counter: run `--name` on every parameter the table
shows at ≥ 3.

## Intermediate representations

The quick version is the `types constructed on path:` line of `hops.py` (three for `layered`, two
for `seamed`, none for `mono`). The fuller recipe lists, per function, constructor calls of
CapWords names, dict comprehensions, and the return annotation:

```python
import ast, re, sys
for spec in sys.argv[1:]:
    path, _, fns = spec.partition(":"); want = set(fns.split(",")) if fns else None
    tree = ast.parse(open(path).read())
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)): continue
        if want and node.name not in want: continue
        ctors = [f"{s.func.id}@{s.lineno}" for s in ast.walk(node)
                 if isinstance(s, ast.Call) and isinstance(s.func, ast.Name)
                 and re.match(r"^_?[A-Z][A-Za-z0-9_]*$", s.func.id)]
        dicts = [f"{type(s).__name__}@{s.lineno}" for s in ast.walk(node) if isinstance(s, (ast.DictComp, ast.Dict))]
        ret = ast.unparse(node.returns) if node.returns else "-"
        print(f"{path.split('/')[-1]}::{node.name:<32} returns {ret:<50} ctors={ctors} dicts={dicts}")
```

Usage: `python3 reprs.py file.py[:fn1,fn2] …`. Three things measured on the real case:

- The regex must be `^_?[A-Z]`. A `^[A-Z]` regex silently misses a private NamedTuple with a
  leading underscore — one of the five representations on the real path.
- A `dict[Category, tuple[int, int | None]]` has **no constructor**; it appeared only as the
  return annotation of the function that builds it by comprehension. Read the `returns` column.
- The pass recovered all five representations the hand count named, after dropping the
  request/service constructors a human dismisses at a glance — and surfaced one the hand count
  missed: **two different classes with the same name** (a proto type and a wire type) constructed
  on the same path. A reader holding "the settings type" in their head is holding two things.

What it cannot see: dict- and tuple-shaped intermediates with no type (the recipe above does not
count ad-hoc tuple returns — add a check for an `ast.Return` whose value is an `ast.Tuple`, or a
`tuple[...]` return annotation, if you want the `(value, bool)` channels counted; the fixture's
`layered` has eight of them), and representation *changes* between types — the real case's hand
count of sixteen changes had no definition a script could reproduce.

## Predicting what a refactor breaks

Whether a test asserts behaviour or plumbing is a judgment that depends on the refactor you have in
mind — see [layering-review.md](layering-review.md). What *is* mechanical: given the set of names a
refactor deletes, how many tests reference any of them. Written as a regex, scanned over each test
body **and the same-file helpers it calls**:

```python
import ast, re, sys
rx = re.compile(sys.argv[1]); total = 0
for f in sys.argv[2:]:
    tree = ast.parse(open(f).read()); hit = []
    fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.FunctionDef) and node.name.startswith("test_")): continue
        texts = [ast.unparse(node)]
        for c in ast.walk(node):                      # one level of same-file helpers
            if isinstance(c, ast.Call):
                nm = c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", None)
                if nm in fns and nm != node.name: texts.append(ast.unparse(fns[nm]))
            if isinstance(c, ast.With):               # context-manager helpers
                for item in c.items:
                    nm = getattr(getattr(item.context_expr, "func", None), "attr", None) or getattr(getattr(item.context_expr, "func", None), "id", None)
                    if nm in fns: texts.append(ast.unparse(fns[nm]))
        if any(rx.search(t) for t in texts): hit.append(node.name)
    total += len(hit); print(f"{f.split('/')[-1]:<45} {len(hit):>3}  {hit if len(hit) <= 8 else str(len(hit)) + ' tests'}")
print("TOTAL", total)
```

Usage: `python3 breakage.py '<deletion-set regex>' test_a.py test_b.py …`. On the real case, with
the deletion set of each of two candidate refactors written as a regex (a metric-tag string, two
frozenset fields, a NamedTuple name; and one field rename), it reproduced the hand count of
**tests broken as written: 20 and 21**, per file, exactly. Two things the exact match depended on:

- Scanning bodies plus helpers, not asserts. A test that *builds* the old shape in a fixture
  breaks as surely as one that asserts on it; an asserts-only scan missed the hand-built object in
  the routing suite.
- Naming only what the refactor removes. Putting an *input* constructor that survives the refactor
  into the set over-counted one suite (18 instead of 11). `ast.unparse` emits single quotes, so a
  pattern must not assume `"`.

"Broken as written" means "references a deleted name", not an observed failure — the number is a
cost estimate, not a test run.

## Tools that see the non-branching blind spots

interpreting-scores.md lists what neither C901 nor complexipy sees: length, parameter count,
`with` and `try/finally` nesting, closure depth. Three of these are visible to ruff rules in the
same run. The extended census, all seven `PLR` rules inverted to `0` (verified: every default
fires on `>`, `=0` lists everything, `-1` is rejected with `expected usize`, exit 2):

```bash
ruff check --isolated --ignore-noqa --no-cache --preview --output-format json \
  --select C901,PLR0911,PLR0912,PLR0913,PLR0915,PLR0916,PLR0917,PLR1702 \
  --config "lint.mccabe.max-complexity=0" \
  --config "lint.pylint.max-args=0"            --config "lint.pylint.max-positional-args=0" \
  --config "lint.pylint.max-statements=0"      --config "lint.pylint.max-returns=0" \
  --config "lint.pylint.max-branches=0"        --config "lint.pylint.max-bool-expr=0" \
  --config "lint.pylint.max-nested-blocks=0"   path/ \
  | jq -r '.[] | "\(.location.row):\(.location.column) \(.code) \(.message)"'
```

| Rule | Sees | Default | 0.12.7 | 0.16.6 | Measured quirk |
|---|---|---:|---|---|---|
| `PLR0913` | arguments | 5 | stable | stable | keyword-only args count here but not in `PLR0917` |
| `PLR0917` | positional arguments | 5 | preview | stable | message is `(12/5)` on 0.12.7, `(12 > 5)` on 0.16.6 |
| `PLR0915` | statements | 50 | stable | stable | **counts `return` and `for` as 0** — `def f(x): return g(x)` is invisible at every threshold; ruff cannot enumerate glue hops |
| `PLR0911` | return statements | 6 | stable | stable | — |
| `PLR0912` | branches | 12 | stable | stable | — |
| `PLR0916` | boolean operators | 5 | preview | preview | **inspects `if` statements only** — the same 8-operator expression in a `while`, an assignment or a ternary is invisible even at 0 |
| `PLR1702` | nested blocks | 5 | preview | preview | rows are **nesting sites, not functions** — the row's line is the block, not the `def`; zero-nesting functions never appear |

No PLR message carries a function name (only `C901` does); joining a PLR census to a function list
needs a line→def map, and for `PLR1702` the line is a block.

**`PLR1702` is the headline win.** A 5-deep `with` pyramid and a 5-deep `try/finally` pyramid score
complexipy **0**; `PLR1702` scores both **5**:

```
$ ruff check --isolated --ignore-noqa --no-cache --preview --output-format json --select C901,PLR0915,PLR1702 … nesting.py | jq -r '…'
1:5 C901 `with_pyramid` is too complex (1 > 0)
1:5 PLR0915 Too many statements (5 > 0)
2:5 PLR1702 Too many nested blocks (5 > 0)      # def is on line 1
9:5 C901 `try_pyramid` is too complex (1 > 0)
9:5 PLR0915 Too many statements (20 > 0)
10:5 PLR1702 Too many nested blocks (5 > 0)
27:5 C901 `loop_pyramid` is too complex (6 > 0)
28:5 PLR1702 Too many nested blocks (5 > 0)
```

(complexipy 7.0.1 on the same file: `with_pyramid 0`, `try_pyramid 0`, `loop_pyramid 15`,
`six_if 21`.) It does **not** see the 5-deep closure pyramid; nothing tested does except
`uvx radon@6.0.1 cc -j --show-closures`, whose `col_offset` field is the depth (0/4/8/12/16/20 with
correct dotted qualnames) — with the trap that a recursive `jq` walk of that JSON yields **21**
objects for **6** functions, because closures are listed both nested and at the top.

For NLOC, parameter count and token count in one table, `uvx lizard@1.24.0 --csv path/` (columns
`nloc,ccn,token,param,length,location,file,name,signature,start,end`, no header row **(inferred)**
from column order); it sees nested-class methods that complexipy and radon miss. Its warnings are in
the table below.

## Silent failures of every tool in this file

Every tool here has a way to report success while measuring the wrong thing. This table is the
price of the numbers above.

| Tool | What it does silently | How to detect |
|---|---|---|
| `scripts/hops.py` | enters **every** reachable arm (24 where one input runs 19); cannot follow `getattr`, dict-of-lambdas dispatch, callbacks, star imports — prints each as `unresolved` with a reason, and `<expr>.method` guesses as `heuristic` | read `unresolved call sites:` — **0 is the only clean run**; prune with `--exclude` / `--leaf-decorator` and say so |
| `scripts/hops_dyn.py` | sees only what the input reaches and says nothing about the rest — the same entry point measured 1 callable on a cache hit and 4 on a miss; dataclass/NamedTuple constructors never appear (no frame). Until 1.2.0 it put the package dir first on `sys.path`, so a package containing `html.py`, `types.py` or `parser.py` shadowed the stdlib and the import crashed — flat fixture dirs never showed it; a package is now imported through its parent | pair with the static count; choose inputs that take each arm |
| `scripts/path_census.py` | none found — refuses to run if `ruff --show-files` misses a file; but `cog_missing > 0` means complexipy skipped defs (nested-class methods, `# complexipy: ignore`) | read `cog_missing` |
| `scripts/arg_threading.py` | with `--entry`, overload stubs are shadowed and only on-path producers count; without `--entry`, test files count as producers | run both scopes; point package scope at a directory without tests |
| `python -m trace --trackcalls` | `--ignore-dir` and `--ignore-module` have **no effect** under `--trackcalls` — `globaltrace_trackcallers` never consults `self.ignore` (3.14.7 source); output floods with `typing`, `annotationlib`, importlib frames, `<module>`, `<genexpr>`; propagates the traced program's exit status | do not use it as a number; `hops_dyn.py` is 80 lines and clean |
| `code2flow --target-function` | from a public entry whose callee has `@overload` stubs, drops the ambiguous edge ("linked them to multiple function definitions") and reported **6 nodes at exit 0** for a 35-callable path; names modules by bare filename, so two files with the same basename in different directories merged into one `basename::` namespace; dict-of-lambdas dispatch produces no edge; an unqualified target matching two defs is picked silently | start below the overloads; never trust per-module counts on a tree with duplicate basenames; pass `module::function` |
| ruff preview rules (`PLR0916`, `PLR1702`, `PLR0917` on 0.12.7) selected without `--preview` | `warning: Selection … has no effect because preview is not enabled` on **stderr**; `All checks passed!` on stdout; **exit 0** | never pipe stderr away; check the warning |
| ruff 0.16.x `--preview` + `--output-format concise` | prints rule **names** not codes (`too-many-arguments:` instead of `PLR0913`), so `grep PLR0913` finds nothing | use `--output-format json`; `.code` is stable across versions |
| `PLR0915` | a pure forwarder (`return g(x)`) counts 0 statements and is unreachable at any threshold | count hops with `hops.py`, not statements |
| ruff `C901` mistyped path | `warning: Failed to lint …` + `All checks passed!`, exit 0 (already in the skill) | `ruff check --isolated --show-files path/` first |
| `lizard` | prints **`CCN 2` for a file that does not parse**; a mistyped path prints an empty summary at exit 0; `#lizard forgives` deletes a function from the listing with no override flag; `-ENS` nesting depth is a **running total that never resets** (three identical 5-deep functions read 5, 10, 15 — and it carries across files); `-Eduplicate` reports `0.00%` for an 11-line byte-identical clone | parse with `ast` first; never use `-ENS` or `-Eduplicate` |
| `radon cc` | shares complexipy's nested-class blind spot — identical bodies: ruff 6 / lizard 6 / complexipy absent / radon absent; mistyped path prints nothing at exit 0; syntax error prints `ERROR` on stdout at exit 0 | use ruff or lizard as the cross-check, not radon |
| `radon mi`, `radon hal` | MI scores a cyclo 6 / cog 15 nested function **100.00, grade A** (everything in the corpus is grade A); Halstead gives a 5-branch, 6-return function volume 0, bugs 0 | do not use either |
| `pylint --enable=duplicate-code` | finds nothing on a single file (compares modules), exit 0; exit code is a bitfield (**8** for a refactor message); one `# pylint: disable=duplicate-code` in *either* file silences the pair, and pylint has no `--ignore-noqa` | always ≥ 2 files; grep for the disable comment first |
| `grimp`, `pydeps`, `cohesion` | an empty or non-package directory yields a 0-module graph / no output at exit 0 | check the module count |
| `tach` | needs a `tach.toml` written into the repo under audit; no `--config` | use `grimp` for measurement; `import-linter --config` for enforcement |
| `complexipy` | `@overload` stubs are rows scoring 0; methods of a class not at column 0 are never reported (already in the skill) | de-duplicate by name; read `cog_missing` |

## Reading the numbers: ratio to a baseline, never a threshold

There are no sourced thresholds between functions, and none is proposed here. The number means
something only against a baseline: the path the code replaced, or a sibling in the same codebase
that solves the same problem. The real case's totals table, as the analysis wrote it:

| Path | Defs | Σcog | max cog | Decisions | Modules |
|---|---:|---:|---:|---:|---:|
| The new read path | 23 | **61** | 8 | **34** | 3 |
| The path it replaced | 7 | **24** | 11 | **9** | 2 |
| The resolver alone, before the change | 6 | 21 | 6 | 10 | 1 |

Read down the max column and nothing is wrong: 8 is under every threshold, 11 is the old code. Read
across the sums and the new path is 2.5× the old one in cognitive cost and 3.8× in decisions — of
which the 8 re-dispatches on the selector are the ones the layering itself manufactured; the rest
are error containment and fallbacks the old path did not have, which is a judgment
([layering-review.md](layering-review.md)), not a number. One public call entered 35 callables
against 11. The absolute 61 says nothing; 61 against 24 for the same job is the finding.

## What these cannot see

- **Whether a seam has meaning.** `seamed` and a split-by-line-count would both score 5 hops. Hops
  say how many pieces, never whether the pieces are named after concepts.
- **Value-identical fallbacks with different code.** Two helpers that return the same value for
  every reachable input are two hops and two representations here; only a differential test finds
  that they are one thing. `test_equiv.py` in the fixture is the template.
- **Dict- and tuple-shaped intermediate representations**, and changes of representation between
  two typed values.
- **Why a module boundary exists.** An import-boundary lint can manufacture a layer; `by module`
  counts modules and cannot tell a load-bearing boundary from a manufactured one.
- **Test plumbing ratio** — which tests pin structure rather than behaviour is relative to the
  refactor being considered; the breakage count above is its mechanical shadow, not the judgment.
- **State threaded outside signatures**: module globals, thread-locals, `self` attributes set in
  one method and read in another. Invisible to the threading table.
- **Anything the input does not reach** (dynamic) and **anything called through a value** (static).

## Unverified

- The real-case counts were produced statically on extracted sources; no real read was executed
  under a tracer (the dynamic count for it is the hand count, not a measurement).
- Scripts were exercised on the fixture triple, the golf variant, a dispatch-construct fixture, and
  one real nested package tree. Not on a third codebase.
- `hops.py`'s heuristic `<expr>.method` resolution was measured to be wrong when two classes share
  a method name only in the sense that it reports the ambiguity; a fixture where it silently picks
  the wrong one of two *visible* classes was not built.
- The `lizard --csv` column names are inferred from column order; lizard prints no header.
- `sys.monitoring` (3.12+) as a lower-overhead replacement for `sys.setprofile` was not tested.
- code2flow's `mod::Class.method` target form worked for the real entry, but the `@overload`
  truncation means the 6-node result did not exercise method resolution depth.
