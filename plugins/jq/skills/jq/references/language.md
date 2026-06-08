# jq Filter Language Reference

The jq programming language: every construct that makes up a filter, with runnable examples. jq is a pure functional language — a program is a **filter** mapping one JSON input to a stream of zero, one, or many JSON outputs. There are no statements and no mutation; "assignment" operators return a modified *copy*.

All examples were verified on **jq 1.7.1**. Constructs are **bedrock** (jq 1.6 and earlier) and shown unannotated; only features that arrived in 1.7 or later carry a `(jq 1.X+)` tag. Run any example yourself with `echo '<input>' | jq '<filter>'` (or `jq -n '<filter>'` where the input is `null`).

## Table of Contents

- [Identity, Paths & Recursive Descent](#identity-paths--recursive-descent)
- [Composition: Pipe and Comma](#composition-pipe-and-comma)
- [Constructing Arrays and Objects](#constructing-arrays-and-objects)
- [Operators](#operators)
- [The Alternative Operator `//`](#the-alternative-operator-)
- [Conditionals](#conditionals)
- [Error Handling: `try`/`catch` and `?`](#error-handling-trycatch-and-)
- [`reduce` and `foreach`](#reduce-and-foreach)
- [Variables & Destructuring](#variables--destructuring)
- [Function Definitions, Recursion & Closures](#function-definitions-recursion--closures)
- [`label`/`break`](#labelbreak)
- [String Interpolation & `@format` Strings](#string-interpolation--format-strings)
- [Assignment & Path-Expression Semantics](#assignment--path-expression-semantics)
- [Path Builtins](#path-builtins)
- [Modules](#modules)
- [Comments](#comments)

## Identity, Paths & Recursive Descent

| Filter | Meaning | Example (`echo INPUT \| jq 'FILTER'`) |
|--------|---------|----------------------------------------|
| `.` | Identity — input unchanged (pretty-printed) | `{"a":1}` → `{"a":1}` |
| `.foo` | Object index | `{"foo":1}` → `1` |
| `.foo.bar` | Nested index | `{"foo":{"bar":2}}` → `2` |
| `."foo bar"` | Index a non-identifier key | `{"foo bar":1}` → `1` |
| `.["foo"]` | Generic (bracket) index | `{"foo":1}` → `1` |
| `.[expr]` | Index by a computed key/index | `{"k":1}` with `.["k"]` → `1` |
| `.[]` | Iterate values of an array/object (a generator) | `[1,2,3]` → `1` `2` `3` |
| `.[i]` | Array index, negative counts from end | `[10,20,30]` with `.[-1]` → `30` |
| `.[i:j]` | Slice of an array or string | `[1,2,3,4]` with `.[1:3]` → `[2,3]` |
| `..` | Recursive descent — every value at every depth | `{"a":{"b":1}}` → `{"a":{"b":1}}` `{"b":1}` `1` |

Slices accept open ends and negatives: `.[2:]`, `.[:3]`, `.[-2:]`. Strings slice by codepoint: `"hello" | .[1:3]` → `"el"`.

`..` is exactly `recurse`: `[..] == [recurse]` is `true`. It is the workhorse for "find this anywhere", e.g. `.. | .id? // empty`.

**Dot-before-bracket** `.a.["k"]` and `.a.[]` are accepted *(jq 1.7+)*; before 1.7 you wrote `.a["k"]` / `.a[]` (both still work).

### Optional `?`

A trailing `?` suppresses errors from the filter it follows, turning an error into *no output* (empty). It is shorthand for `try`: `EXPR?` ≡ `try EXPR`.

```sh
echo '5'        | jq '.foo?'   # (no output — indexing a number would error)
echo '{"a":1}'  | jq '.b?'     # null  (missing key is null, not an error)
echo '[1,"x",2]'| jq '[.[] | (. * 2)?]'   # [2,4]  — the string is dropped
```

Use `.foo?` / `.[]?` to walk heterogeneous data without aborting on the wrong type. Note the distinction: indexing a *missing* object key yields `null` (no error needed); indexing the *wrong type* (e.g. a string as an object) is an error that `?` swallows.

## Composition: Pipe and Comma

- **Pipe `|`** — `f | g` runs `g` once on *each* output of `f`. This is the backbone of every jq program.
- **Comma `,`** — `f, g` concatenates output streams: emit all of `f`'s values, then all of `g`'s.
- **Parentheses** group sub-expressions: `(f)`.

```sh
echo '{"x":1,"y":2}' | jq '.x, .y'          # 1  then  2
echo '{"x":1,"y":2}' | jq -c '[.x, .y]'     # [1,2]
echo '{"a":{"b":3}}' | jq '.a | .b'         # 3
echo '[1,2,3]'       | jq -c '(.[0], .[2]) | . + 100'   # 101 then 103
```

Because a filter can emit many values, downstream stages run once per value (a generator / backtracking model) — this is why `.[] | f` applies `f` to every element.

## Constructing Arrays and Objects

**Array** `[ f ]` collects *all* outputs of `f` into a single array:

```sh
echo '[{"n":"a"},{"n":"b"}]' | jq -c '[.[] | .n]'   # ["a","b"]
jq -nc '[range(3)]'                                  # [0,1,2]
```

**Object** `{ ... }`:

```sh
echo '{"x":1,"y":2}'        | jq -c '{a: .x, b: .y}'    # {"a":1,"b":2}
echo '{"name":"a","age":3}' | jq -c '{name, age}'       # {"name":"a","age":3}  (shorthand)
echo '{"k":"id","v":7}'     | jq -c '{(.k): .v}'        # {"id":7}              (computed key)
```

- `{name, age}` is shorthand for `{name: .name, age: .age}`.
- `{(EXPR): v}` uses a **computed key** — `EXPR` must produce a string.
- `{$var: 1}` uses a bound variable directly as a key *(jq 1.7+)*; before 1.7 you wrote `{($var): 1}` (still valid). Verify: `jq -n --arg k name '{$k: 1}'` → `{"name":1}`.
- An object **value that is a generator** produces multiple objects (cartesian product):

```sh
jq -nc '{x: (1,2)}'    # {"x":1}  then  {"x":2}
```

## Operators

**Arithmetic** `+ - * / %` — `+` is overloaded by type:

| Expression | Result | Note |
|------------|--------|------|
| `2 + 3` | `5` | numbers add |
| `"a" + "b"` | `"ab"` | strings concat |
| `[1,2] + [3]` | `[1,2,3]` | arrays concat |
| `{"a":1} + {"b":2}` | `{"a":1,"b":2}` | objects merge (right side wins, shallow) |
| `[1,2,3] - [2]` | `[1,3]` | array `-` removes elements |
| `{"a":{"x":1}} * {"a":{"y":2}}` | `{"a":{"x":1,"y":2}}` | object `*` = **deep recursive merge** |
| `"ab" * 3` | `"ababab"` | string × number = repeat |

Division and `%` (modulo) by zero raise an error.

**Comparison** `== != < <= > >=` use a **total order across all types**: `null < false < true < numbers < strings < arrays < objects`. So `1 < "a"` is `true` and sorting mixed-type arrays is well-defined.

**Boolean** `and`, `or`, `not`. Only `false` and `null` are falsy — *everything else is truthy*, including `0`, `""`, and `[]`. `not` is a **filter**, not a prefix operator, so you pipe into it:

```sh
jq -nc 'true and false'      # false
jq -nc '(1 < 2) and (2 < 3)' # true
echo 'true' | jq 'not'       # false
echo '0'    | jq 'not'       # false  (0 is truthy)
```

## The Alternative Operator `//`

`a // b` yields **all outputs of `a` that are neither `null` nor `false`**; if `a` produces none such (or only `null`/`false`, or *errors*), it yields `b`. This is the standard default idiom — and note it also swallows errors in `a`, so it is *not* a boolean OR (that's `or`).

```sh
echo '{"a":null}'      | jq '.a // "default"'   # "default"
echo '{"a":0}'         | jq '.a // "default"'   # 0   (0 is not null/false)
echo '{}'              | jq -c '.missing // []' # []
echo '{"name":"bob"}'  | jq -r '.nick // .name' # bob
```

There is a *separate, unrelated* `?//` operator used only inside destructuring patterns — see [Variables & Destructuring](#variables--destructuring).

## Conditionals

```
if COND then THEN elif COND2 then THEN2 else ELSE end
```

```sh
echo '2' | jq 'if . == 1 then "one" elif . == 2 then "two" else "many" end'   # "two"
```

The `else` branch is **optional** *(jq 1.7+)* — an omitted `else` defaults to `.` (identity), passing the input through unchanged when no condition matches:

```sh
echo '5' | jq 'if . > 10 then "big" end'   # 5    (no else → identity)
```

The condition is itself a filter; if it emits multiple values, the `if` runs once per value.

## Error Handling: `try`/`catch` and `?`

- `try EXPR catch HANDLER` — if `EXPR` raises, `HANDLER` runs with the **error value** as its input (usually a string).
- `try EXPR` alone — swallow the error, producing no output.
- `EXPR?` — postfix shorthand for `try EXPR`.
- `error` / `error(msg)` — raise an error. `error` given a non-string keeps that value as the error payload.

```sh
jq -nc 'try error("boom") catch .'        # "boom"
jq -nc 'try (1/0) catch "div by zero"'    # "div by zero"
echo '[1,"x",2]' | jq -c '[.[] | (.*2)?]' # [2,4]   — error on "x" dropped
jq -nc 'error({code:42}) ' 2>&1 | head -1 # error payload can be any value
```

*(jq 1.7+ tightened `try`/`catch` so it only catches errors raised by its own body, not by downstream filters.)*

## `reduce` and `foreach`

**`reduce`** folds a generator into a single accumulated value. `.` inside the body is the accumulator:

```
reduce GENERATOR as $x (INIT; UPDATE)
```

```sh
echo '[1,2,3,4]' | jq 'reduce .[] as $x (0; . + $x)'        # 10  (sum)
echo '[1,2,3,4]' | jq 'reduce .[] as $x (1; . * $x)'        # 24  (product)
```

**`foreach`** is like `reduce` but **emits** a value at each step via the optional EXTRACT clause — giving running/scan behaviour:

```
foreach GENERATOR as $x (INIT; UPDATE; EXTRACT)
```

```sh
echo '[1,2,3]' | jq -c '[foreach .[] as $x (0; . + $x; .)]'  # [1,3,6]  (running totals)
```

Both support **pattern destructuring** in the binding (see below):

```sh
echo '[{"a":1,"b":2},{"a":3,"b":4}]' | jq 'reduce .[] as {$a,$b} (0; . + $a + $b)'  # 10
```

## Variables & Destructuring

`EXPR as $x | BODY` binds each output of `EXPR` to `$x` within `BODY` (iterating cartesian-style over `EXPR`'s outputs). Scope is lexical to the `| BODY`.

```sh
echo '{"a":1,"b":2}' | jq '. as $o | $o.a + $o.b'   # 3
```

**Destructuring patterns** bind several variables at once:

```sh
jq -nc '[1,2,3] as [$a,$b,$c] | $a + $c'                       # 4
jq -nc '{"a":1,"b":2} as {a:$x, b:$y} | [$x,$y]'               # [1,2]
jq -nc '{"a":1,"b":2} as {$a,$b} | [$a,$b]'                    # [1,2]  (shorthand: $a binds .a)
```

Patterns nest (`. as {a: [$first]} | $first`) and may appear anywhere a binding is allowed (`reduce`, `foreach`, function args).

**`?//` — destructuring alternative** *(jq 1.6+)*: try each pattern in turn until one matches without error. Useful when the input might be an array *or* an object. Every variable named across all patterns is bound; those a matching pattern didn't fill become `null`.

```sh
jq -nc '[1,2] as [$a] ?// $a | $a'            # 1   (array pattern matches)
jq -nc '{"a":9} as [$a] ?// {$a} | $a'        # 9   (falls through to object pattern)
```

## Function Definitions, Recursion & Closures

```
def name: BODY;            # 0-argument
def name(f): BODY;         # filter argument (call-by-name / closure)
def name($v): BODY;        # value argument ($v is evaluated and bound)
```

Arguments are **filters by default** (passed as closures, evaluated against the caller's `.`); prefix with `$` to receive an evaluated value instead. Multiple arities of the same name may coexist.

```sh
echo '5'   | jq 'def inc: . + 1; inc'                  # 6
echo '3'   | jq 'def twice(f): f + f; twice(. * 10)'   # 60   (f is a filter)
jq -nc 'def mul($v): $v * 2; mul(10)'                  # 20   (value arg)
```

**Recursion** — a def may call itself; inner defs form closures over enclosing scope:

```sh
echo '5' | jq 'def fac: if . <= 1 then 1 else . * (. - 1 | fac) end; fac'   # 120
```

`recurse(f)`, `recurse(f; cond)`, and bare `recurse` (≡ `recurse(.[]?)`) walk trees:

```sh
echo '[1,[2,[3]]]' | jq -c '[recurse(.[]?) | numbers]'   # [1,2,3]
```

Trailing local funcs are in scope for the rest of the program: `def f: ...; def g: ...; MAIN`.

## `label`/`break`

`label $out | ... break $out` is a non-local exit from a generator — it stops the enclosing labelled stream. This is how builtins like `first`, `limit`, and `until` short-circuit *(label/break since jq 1.5)*.

```sh
jq -nc '[label $out | range(10) | if . == 3 then break $out else . end]'   # [0,1,2]
jq -nc '[limit(3; range(100))]'                                            # [0,1,2]
```

## String Interpolation & `@format` Strings

`"\(EXPR)"` splices a jq expression into a string literal. A non-string value is rendered as JSON; a string is inserted as-is.

```sh
echo '{"n":"ann","a":3}' | jq -r '"\(.n) is \(.a)"'   # ann is 3
echo '{"x":[1,2]}'       | jq -r '"got \(.x)"'        # got [1,2]
```

A `@format` prefix on a string literal applies that format to **each interpolation** (handy for escaping):

```sh
echo '{"q":"a b&c"}' | jq -r '@uri  "search?q=\(.q)"'   # search?q=a%20b%26c
echo '{"v":"hi"}'    | jq -r '@json "value=\(.v)"'      # value="hi"
```

The full list of formats (`@base64`, `@csv`, `@tsv`, `@html`, `@sh`, `@json`, `@text`, `@uri`, …) is in the builtins reference.

## Assignment & Path-Expression Semantics

jq has no mutation; "assignment" operators take a **path expression** on the left and return a *modified copy* of the input. A path expression is anything that resolves to a *location*: `.a.b`, `.[]`, `.a[1:3]`, `.a, .b`, even `select`-filtered iterations.

| Operator | Meaning |
|----------|---------|
| `LHS = RHS` | Set value. **RHS is evaluated against the original root `.`**, not the value at the path. |
| `LHS \|= RHS` | **Update**: RHS is a filter applied to the *current value at the path* (`.` = old value there). |
| `LHS += RHS` (`-= *= /= %=`) | Arithmetic update; RHS operand evaluated against the root. `.a += 1` ≈ `.a \|= . + 1`. |
| `LHS //= RHS` | Set only where the current value is `null`/`false`. |

```sh
echo '{"a":1}'        | jq -c '.a = 5'           # {"a":5}
echo '{"a":1,"b":9}'  | jq -c '.a = .b'          # {"a":9,"b":9}   (RHS .b read from root)
echo '{"a":1}'        | jq -c '.a |= . + 1'      # {"a":2}         (. = old value at .a)
echo '{"a":1}'        | jq -c '.a += 10'         # {"a":11}
echo '{"a":null}'     | jq -c '.a //= "def"'     # {"a":"def"}
echo '{"items":["x","y"]}' | jq -c '.items[] |= ascii_upcase'   # {"items":["X","Y"]}
```

**A path expression can match many locations**, and the assignment updates all of them:

```sh
echo '[{"v":1},{"v":2},{"v":3}]' | jq -c '(.[] | select(.v >= 2) | .v) |= . * 10'
#   → [{"v":1},{"v":20},{"v":30}]
echo '{"a":1,"b":2}'             | jq -c '(.a, .b) = 0'   # {"a":0,"b":0}
```

**Deletion via `|= empty`** *(jq 1.7+)*: assigning `empty` to matched paths deletes them. For array elements this was fixed to work correctly in 1.7:

```sh
echo '{"l":[1,2,3,4]}' | jq -c '(.l[] | select(. >= 3)) |= empty'   # {"l":[1,2]}
```

## Path Builtins

These operate on *paths* (arrays of keys/indices) rather than values — the machinery behind assignment.

| Builtin | Purpose | Example |
|---------|---------|---------|
| `path(f)` | The path(s) that filter `f` navigates to | `{"a":{"b":1}} \| path(.a.b)` → `["a","b"]` |
| `paths` | All paths in the value | `{"a":1,"b":[2]}` → `["a"]` `["b"]` `["b",0]` |
| `paths(f)` | Paths whose leaf satisfies `f` | `[paths(scalars)]` for leaf paths |
| `getpath(p)` | Value at path array `p` | `{"a":{"b":5}} \| getpath(["a","b"])` → `5` |
| `setpath(p; v)` | Copy with path `p` set to `v` | `null \| setpath(["a","b"]; 7)` → `{"a":{"b":7}}` |
| `del(pathexpr)` | Copy with the path(s) removed | `{"a":1,"b":2} \| del(.a)` → `{"b":2}` |
| `delpaths(paths)` | Delete multiple path arrays at once | `delpaths([["a"],["c"]])` |
| `pick(pathexprs)` | Projection — keep only the given paths *(jq 1.7+)* | `{"a":1,"b":2} \| pick(.a)` → `{"a":1}` |

```sh
echo '{"a":1,"b":[2,3]}' | jq -c '[paths]'           # [["a"],["b"],["b",0],["b",1]]
echo '{"a":1,"b":[2,3]}' | jq -c '[paths(scalars)]'  # [["a"],["b",0],["b",1]]  (leaf paths)
echo '{"a":1,"b":2,"c":3}' | jq -c 'delpaths([["a"],["c"]])'   # {"b":2}
```

> **Removed in 1.7:** `leaf_paths` (use `paths(scalars)`) and `recurse_down` (use `recurse`/`..`). Both error on jq 1.7.1 — do not use them in new filters.

## Modules

A jq module is a `.jq` file of `def`s. Pull one into your program at the top:

```
import "path/module" as name;   # functions namespaced as name::func
include "path/module";          # functions merged into the current namespace
import "datafile" as $name;     # import a JSON / .jq-data file as a variable
```

```sh
# /tmp/mymod.jq contains:  def greet: "hi " + .;
echo '"bob"' | jq -L /tmp 'include "mymod"; greet'        # "hi bob"
echo '"bob"' | jq -L /tmp 'import "mymod" as m; m::greet' # "hi bob"
```

- The module **search path** is set by `-L dir` (repeatable; `-L dir` or `-Ldir`) plus the `$ORIGIN`-based default, which includes `~/.jq` (a file *or* a directory). A `~/.jq` file is auto-loaded as your personal library — a good home for helper defs.
- `import "m" as m {search: "..."};` accepts an optional metadata object.
- `modulemeta` introspects a module's metadata (and, since 1.7, its function names).

See the CLI reference for full `-L` / search-path mechanics.

## Comments

`#` begins a comment that runs to the end of the line:

```sh
jq -nc '1 + 1   # this is ignored'   # 2
```

*(jq 1.7+ allows carriage returns inside comments; jq 1.8+ adds CRLF line breaks in filters and a Tcl-style multi-line shebang trick via a trailing `\`.)* Plain `#` line comments are bedrock.
