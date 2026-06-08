# jq Builtin Function Library

Reference for jq's builtin functions, grouped by purpose. Every function here was
verified to **exist in jq 1.7.1** (via `jq -n 'builtins'`, ~220 entries) and the
examples were run on the installed `jq-1.7.1`.

> **Version annotations:** Functions marked `(jq 1.7+)` or `(jq 1.8+)` require at
> least that version; everything unmarked is **bedrock** (present in jq 1.6 and
> earlier — don't worry about it). The big modern release is **1.7 (2023)**; **1.8
> (2025)** added the trim family and a few others. A `(jq 1.8+)` function **errors**
> on 1.7.1 (`<name> is not defined`) — those rows are sourced from `NEWS.md` /
> the dev tree, not run here. For the full feature→version table see
> [references/version-features.md](version-features.md).
>
> ⚠️ **These do NOT exist in jq** — do not use them (they error):
> `@base32` / `@base32d` (`base32 is not a valid format`), `toarray`, `dateadd` /
> `datesub`, `GROUP_BY`, `UNIQUE_BY`. The complete format-string list is exactly
> `@text @json @base64 @base64d @uri @urid @csv @tsv @html @sh`. jq date math is
> plain arithmetic on epoch seconds (`now + 86400 | todate`).

## Table of Contents

- [Types & inspection](#types--inspection)
- [Arrays & objects](#arrays--objects)
- [Generators, limits & recursion](#generators-limits--recursion)
- [SQL-style operators](#sql-style-operators)
- [Strings](#strings)
- [Regular expressions](#regular-expressions)
- [Format strings (`@fmt`)](#format-strings-fmt)
- [Math](#math)
- [Dates & time](#dates--time)
- [Paths](#paths)
- [Streaming](#streaming)
- [I/O, debug & control](#io-debug--control)

---

## Types & inspection

| Function | Description |
|----------|-------------|
| `type` | `"null"`/`"boolean"`/`"number"`/`"string"`/`"array"`/`"object"`. |
| `length` | string ⇒ codepoint count; array/object ⇒ element count; number ⇒ absolute value; null ⇒ 0. |
| `utf8bytelength` | Byte length of a string (UTF-8). |
| `has(k)` | True if object has key `k` (or array has index `k`). |
| `in(obj)` | Inverse of `has`: `"k" \| in({...})` — is `.` a key of the argument? |
| `contains(x)` | Deep containment: does `.` contain `x` (recursively, substrings/subsets)? |
| `inside(x)` | Inverse of `contains`: is `.` contained in `x`? |
| `error`, `error(msg)` | Raise an error. A non-string payload is preserved (catchable). |

**Type selectors** (each is `select(type==...)`, passing matching inputs through, dropping the rest): `arrays`, `objects`, `iterables` (arrays+objects), `booleans`, `numbers`, `strings`, `nulls`, `values` (everything except null), `scalars` (non-iterables).

**Numeric predicates / constants:** `isinfinite`, `isnan`, `isnormal`, `isfinite`; `infinite` and `nan` (constants); `finites`, `normals` (selectors).

```sh
echo '{"a":1}'   | jq -c 'type, length, has("a"), ("a"|in({"a":1}))'  # "object" 1 true true
echo '[1,"x",null,[2]]' | jq -c '[.[]|numbers], [.[]|scalars]'   # [1] [1,"x",null]
echo '{"user":{"id":7}}' | jq 'contains({user:{id:7}})'          # true
```

## Arrays & objects

| Function | Description |
|----------|-------------|
| `map(f)` | `[.[] \| f]` — apply `f` to each element. |
| `map_values(f)` | `.[] \|= f` — transform each value, dropping any that produce `empty`. |
| `select(f)` | Keep `.` when `f` is truthy, else `empty`. |
| `add` | Sum/concat/merge all outputs of `.[]` (numbers add, strings/arrays concat, objects merge). |
| `add(f)` `(jq 1.8+)` | `add` over a generator: `add(.[].n)`. |
| `flatten`, `flatten(d)` | Flatten nested arrays fully, or to depth `d`. |
| `sort`, `sort_by(f)` | Sort ascending; `sort_by` by the value(s) of `f`. |
| `group_by(f)` | Group a sorted array into sub-arrays sharing `f`. |
| `unique`, `unique_by(f)` | Dedupe (sorted); `unique_by` keeps first per `f`. |
| `min`, `max`, `min_by(f)`, `max_by(f)` | Extremum of an array. |
| `reverse` | Reverse an array (or string). |
| `transpose` | Transpose a (possibly ragged) array of arrays. |
| `bsearch(t)` | Binary-search a **sorted** array for `t`; returns index, or `-1-insertpos` if absent. |
| `keys`, `keys_unsorted` | Object keys (sorted / insertion order) or array indices. |
| `values` | Selector form: all values of `.[]` except null. |
| `to_entries` | Object ⇒ `[{key,value},...]`. |
| `from_entries` | `[{key,value},...]` ⇒ object (accepts `k`/`name`/`Name`, `v`/`value`). |
| `with_entries(f)` | `to_entries \| map(f) \| from_entries`. |

```sh
echo '[{"d":"x","n":3},{"d":"x","n":1},{"d":"y","n":2}]' \
  | jq -c 'group_by(.d) | map({dept:.[0].d, total:(map(.n)|add)})'
# [{"dept":"x","total":4},{"dept":"y","total":2}]

echo '[{"k":1},{"k":1},{"k":2}]' | jq -c 'unique_by(.k)'     # [{"k":1},{"k":2}]
echo '{"a":1,"b":2}'            | jq -c 'with_entries(.value += 10)'  # {"a":11,"b":12}
echo '[[1,2],[3,4]]'           | jq -c 'transpose'           # [[1,3],[2,4]]
```

## Generators, limits & recursion

| Function | Description |
|----------|-------------|
| `empty` | Produce no output (backtracks). |
| `range(n)`, `range(a;b)`, `range(a;b;c)` | Numeric generator (exclusive upper bound; `c` = step). |
| `first`, `last`, `nth(n)` | First/last/`n`-th element of an **array**. |
| `first(g)`, `last(g)`, `nth(n;g)` | First/last/`n`-th output of a **generator**. |
| `limit(n;g)` | First `n` outputs of generator `g`. |
| `skip(n;g)` `(jq 1.8+)` | Drop the first `n` outputs of `g` (counterpart to `limit`). |
| `until(cond;upd)` | Apply `upd` until `cond` is true. |
| `while(cond;upd)` | Emit `.` and apply `upd` while `cond` holds. |
| `repeat(f)` | Infinite stream applying `f` repeatedly (use with `limit`/`first`). |
| `isempty(g)` | True if generator `g` produces nothing. |
| `all`, `all(f)`, `all(g;f)` | True if all elements / `f` over `.[]` / `f` over `g` are truthy. |
| `any`, `any(f)`, `any(g;f)` | True if any are truthy. |
| `combinations`, `combinations(n)` | Cartesian product of an array of arrays (or of `n` copies). |
| `recurse`, `recurse(f)`, `recurse(f;cond)` | Recursive descent (`recurse` ≡ `recurse(.[]?)`, same as `..`). |
| `walk(f)` | Recursively apply `f` to every value, bottom-up. |

```sh
echo 'null' | jq -c '[limit(3; range(100))]'                 # [0,1,2]
echo 'null' | jq -c 'first(range(5;10))'                     # 5
echo '2'    | jq -c '[while(. < 100; . * 2)]'                # [2,4,8,16,32,64]
echo '{"a":1,"b":[2,3]}' | jq -c 'walk(if type=="number" then .+1 else . end)'
# {"a":2,"b":[3,4]}
```

## SQL-style operators

Relational helpers (all bedrock — present since 1.6). Note there is **no** `GROUP_BY`/`UNIQUE_BY` — use lowercase `group_by`/`unique_by`.

| Function | Description |
|----------|-------------|
| `INDEX(keyf)`, `INDEX(stream;keyf)` | Build a `{key: row}` lookup object keyed by `keyf`. |
| `IN(s)`, `IN(src;s)` | Fast membership: `IN(s)` is true if `.` equals some output of `s`. |
| `JOIN($idx; keyf)` | Pair each row with `$idx[row\|keyf]`. |
| `JOIN($idx; stream; keyf)` / `JOIN($idx; stream; keyf; joiner)` | Relational join against an INDEX; optional `joiner` shapes each pair. |

```sh
echo '[{"id":1,"n":"a"},{"id":2,"n":"b"}]' | jq -c 'INDEX(.id|tostring)'
# {"1":{"id":1,"n":"a"},"2":{"id":2,"n":"b"}}
echo '3' | jq -c 'IN(1,2,3)'                                 # true
echo '[1,5,9]' | jq -c '[.[] | select(IN(1,9))]'             # [1,9]
```

## Strings

| Function | Description |
|----------|-------------|
| `ascii_downcase`, `ascii_upcase` | ASCII-only case folding. |
| `ltrimstr(s)`, `rtrimstr(s)` | Strip prefix/suffix `s` if present (else unchanged). |
| `trimstr(s)` `(jq 1.8+)` | Strip `s` from both ends. |
| `trim`, `ltrim`, `rtrim` `(jq 1.8+)` | Strip leading/trailing whitespace. |
| `startswith(s)`, `endswith(s)` | Prefix/suffix tests. |
| `split(s)` | Split on a literal separator string ⇒ array. |
| `join(s)` | Join an array with separator `s` (nulls ⇒ empty, scalars stringified). |
| `explode`, `implode` | String ↔ array of Unicode codepoints. |
| `ltrimstr`/`rtrimstr` | (see above) |
| `tostring`, `tonumber` | Convert to string (JSON-encode non-strings) / parse a number. |
| `toboolean` `(jq 1.8+)` | `"true"`/`"false"` string ⇒ boolean. |
| `tojson`, `fromjson` | Serialize a value to a JSON string / parse a JSON string. |

String `*` number repeats it (`"ab"*3`); `× 0` (or less) ⇒ `null`.

```sh
echo '"  Hi There  "' | jq -c 'ascii_downcase'               # "  hi there  "
echo '"a-b-c"'         | jq -c 'split("-")'                  # ["a","b","c"]
echo '["a","b","c"]'   | jq -r 'join("/")'                   # a/b/c
echo '"foobar"'        | jq -c 'ltrimstr("foo")'             # "bar"
echo '"abc"'           | jq -c 'explode'                     # [97,98,99]
echo '"3.14"'          | jq -c 'tonumber'                    # 3.14
```

> **1.8 string changes:** in 1.8 `ltrimstr`/`rtrimstr` **error** on non-string input
> (in 1.7 they pass it through), and string `index`/`indices`/`rindex` use codepoint
> (not byte) offsets. Use `utf8bytelength` for byte counts.

## Regular expressions

Oniguruma-backed (since 1.5). The first argument is the regex; the optional second is a **flags** string.

| Function | Description |
|----------|-------------|
| `test(re)`, `test(re;flags)` | Boolean: does `.` match? |
| `match(re)`, `match(re;flags)` | Emit match object(s): `{offset,length,string,captures}`. |
| `capture(re)`, `capture(re;flags)` | Named captures `(?<name>…)` ⇒ object. |
| `scan(re)`, `scan(re;flags)` | Emit each match (or capture-group array). `scan/2` is `(jq 1.7+)`. |
| `split(re;flags)` | Regex split ⇒ array (2-arg form; the 1-arg `split` is a literal split). |
| `splits(re)`, `splits(re;flags)` | Regex split ⇒ **stream** of pieces. |
| `sub(re;str)`, `sub(re;str;flags)` | Replace **first** match; `str` may reference named captures via `\(.name)`. |
| `gsub(re;str)`, `gsub(re;str;flags)` | Replace **all** matches. |

**Flags:** `g` global, `i` case-insensitive, `x` extended (whitespace/comments), `s` single-line (`.` matches newline), `m` multi-line (`^`/`$` per line), `n` ignore empty matches, `p` both `s`+`m`, `l` longest match.

```sh
echo '"2009-02"' | jq -c 'capture("(?<y>[0-9]+)-(?<m>[0-9]+)")'  # {"y":"2009","m":"02"}
echo '"a1b2c3"'  | jq -c '[scan("[0-9]")]'                       # ["1","2","3"]
echo '"Hello"'   | jq -c 'test("hello";"i"), gsub("l";"L")'      # true "HeLLo"
echo '"a,b,c"'   | jq -c '[splits(",")]'                         # ["a","b","c"]
echo '"key=val"' | jq -r 'sub("(?<k>\\w+)=(?<v>\\w+)"; "\(.v):\(.k)")'  # val:key
```

## Format strings (`@fmt`)

A `@fmt` applies a transformation. Used as a filter (`@base64`) or as a prefix on a
string literal, where it applies to each `\(…)` interpolation (`@uri "x=\(.q)"`).

| Format | Effect |
|--------|--------|
| `@text` | `tostring`. |
| `@json` | Serialize as JSON. |
| `@base64` / `@base64d` | Base64 encode / decode. |
| `@uri` | Percent-encode for URLs. |
| `@urid` `(jq 1.8+)` | Percent-**decode** (reverse of `@uri`). |
| `@csv` / `@tsv` | Array ⇒ CSV / TSV row (quotes/escapes per format). |
| `@html` | HTML-escape (`<`, `>`, `&`, `'`, `"`). |
| `@sh` | Shell-quote; arrays ⇒ space-separated quoted words. |

> ⚠️ There is **no `@base32` / `@base32d`** — it errors (`base32 is not a valid format`).

```sh
echo '["a","b,c"]' | jq -r '@csv'            # "a","b,c"
echo '["a","b"]'   | jq -r '@tsv'            # a<TAB>b
echo '"a b"'       | jq -r '@sh'             # 'a b'
echo '{"q":"a b"}' | jq -r '@uri "x=\(.q)"'  # x=a%20b
echo '"hi"'        | jq -r '@base64'         # aGk=
echo '"aGk="'      | jq -r '@base64d'        # hi
```

## Math

Most are thin wrappers over the C math library, so availability of the rarer ones is platform-dependent.

- **Rounding / sign:** `floor`, `ceil`, `round`, `trunc`, `fabs`, `abs` `(jq 1.7+)`, `nearbyint`, `rint`, `copysign(x;y)`.
- **Powers / roots / logs:** `sqrt`, `cbrt`, `pow(x;y)`, `exp`, `exp2`, `exp10`, `log`, `log2`, `log10`, `log1p`, `expm1`, `logb`, `significand`, `frexp`, `ldexp(m;e)`, `scalb(m;e)`, `scalbln(m;e)`, `modf`.
- **Trig / hyperbolic:** `sin cos tan asin acos atan atan2(y;x) sinh cosh tanh asinh acosh atanh hypot(x;y)`.
- **Special (libm, may be absent on some platforms):** `gamma lgamma lgamma_r tgamma erf erfc j0 j1 jn(n;x) y0 y1 yn(n;x) drem(x;y) fmod(x;y) remainder(x;y) fmin(x;y) fmax(x;y) fdim(x;y) fma(a;b;c) nextafter(x;y) nexttoward(x;y)`.
- **Constants / predicates:** `nan`, `infinite`; `isnan`, `isinfinite`, `isnormal`, `isfinite`.

> `abs` `(jq 1.7+)` preserves the number's literal/precision and works on negative
> literals without the libm round-trip that `fabs` does. `pow10` was **removed in
> 1.8** — use `exp10`.

```sh
echo '-3.7' | jq -c 'abs, floor, ceil, round, trunc'        # 3.7 -4 -3 -4 -3
echo 'null' | jq -c 'pow(2;10), (2|sqrt), (1000|log10)'     # 1024 1.414... 3
echo '[3,1,2]' | jq -c '(map(.*.) | add)'                   # 14
```

## Dates & time

Unix epoch **seconds** is the common currency. There is **no `dateadd`/`datesub`** —
do arithmetic on the epoch number.

| Function | Description |
|----------|-------------|
| `now` | Current time as Unix epoch seconds (float). |
| `gmtime` | Epoch ⇒ "broken-down time" array (UTC). |
| `localtime` | Epoch ⇒ broken-down array (local zone). |
| `mktime` | Broken-down UTC array ⇒ epoch. |
| `strftime(fmt)` | Broken-down array (or epoch) ⇒ formatted string (UTC). |
| `strflocaltime(fmt)` | Same, in the local zone. |
| `strptime(fmt)` | Parse a string ⇒ broken-down array. |
| `todate` / `fromdate` | Epoch ⇄ ISO-8601 (`todateiso8601`/`fromdateiso8601`; `date` ≡ `todate`). |

**Broken-down time array** (verified): `[year, month(0-11), mday, hour, min, sec, wday(0=Sun), yday(0-based)]`. Note month is **0-indexed** (Feb = 1) and year is the **full** year.

```sh
echo 'null' | jq -c '1234567890 | gmtime'        # [2009,1,13,23,31,30,5,43]
echo 'null' | jq -c '1234567890 | todate'        # "2009-02-13T23:31:30Z"
echo 'null' | jq    '"2009-02-13T23:31:30Z" | fromdate'   # 1234567890
echo 'null' | jq -r '1234567890 | strftime("%Y-%m-%d %H:%M:%S")'  # 2009-02-13 23:31:30
# date math is plain arithmetic — "tomorrow" in ISO:
echo 'null' | jq -r 'now + 86400 | todate'
```

## Paths

Path expressions locate values; these builtins manipulate them (see also `references/language.md` on assignment).

| Function | Description |
|----------|-------------|
| `path(f)` | The path(s) that filter `f` navigates to. |
| `paths`, `paths(f)` | All paths in the value (optionally only those whose leaf matches `f`, e.g. `paths(scalars)`). |
| `getpath(p)` | Value at path array `p`. |
| `setpath(p; v)` | Return a copy with path `p` set to `v`. |
| `delpaths(ps)` | Delete multiple paths (array of path arrays). |
| `del(pathexpr)` | Delete the location(s) a path expression matches. |
| `pick(pathexprs)` `(jq 1.7+)` | Project: keep only the given paths, others dropped. |

> `leaf_paths` was **removed in 1.7** — use `paths(scalars)`. `recurse_down` was also removed — use `recurse`.

```sh
echo '{"a":{"b":1,"c":2}}' | jq -c 'getpath(["a","b"]), [paths]'
# 1   [["a"],["a","b"],["a","c"]]
echo '{"a":1,"b":2,"c":3}' | jq -c 'pick(.a, .c)'   # {"a":1,"c":3}
echo '{"a":1,"b":2}'        | jq -c 'del(.b)'        # {"a":1}
```

## Streaming

For documents too large to hold in memory; pairs with the CLI `--stream` flag.

| Function | Description |
|----------|-------------|
| `tostream` | Value ⇒ stream of `[path, leaf]` and `[path]` end-markers. |
| `fromstream(g)` | Rebuild a value from such a stream. |
| `truncate_stream(stream)` / `truncate_stream(depth; stream)` | Drop the top `depth` path levels from stream events. |
| `input` | Read and consume the **next** input value. |
| `inputs` | Stream all remaining inputs (great with `-n`). |

```sh
echo '{"a":[1,2]}' | jq -c '[tostream]'
# [[["a",0],1],[["a",1],2],[["a",1]],[["a"]]]
# Sum a stream of NDJSON numbers without slurping the whole file:
printf '1\n2\n3\n' | jq -n 'reduce inputs as $x (0; . + $x)'   # 6
```

## I/O, debug & control

| Function | Description |
|----------|-------------|
| `env`, `$ENV` | Environment as an object (`env` is the builtin, `$ENV` the snapshot). Prefer `$ENV.TOKEN` over shell interpolation. |
| `input_filename` | Name of the file the current input came from (null for stdin). |
| `input_line_number` | Current input line number. |
| `$__loc__` | `{"file","line"}` of this point in the program (debugging). |
| `builtins` | Array of all builtin `name/arity` strings. |
| `debug`, `debug(msgs)` | Echo `["DEBUG:", .]` (or `msgs`, `(jq 1.7+)`) to stderr; pass `.` through unchanged. |
| `stderr` | Write `.` to stderr (raw string, no newline/decoration), pass through. |
| `halt` | Exit immediately with status `0`. |
| `halt_error`, `halt_error(code)` | Print `.` to stderr (strings raw, else JSON) and exit `5` (or `code`). |
| `error`, `error(msg)` | Raise a catchable error. |

```sh
echo 'null' | jq -r '$ENV.HOME'                # value of $HOME, no shell interpolation
echo '{"x":1}' | jq -c '.x | debug | . + 1'    # stderr: ["DEBUG:",1]   stdout: 2
echo 'null' | jq -n 'builtins | length'        # ~220
# control flow via exit code:
echo '{"ok":false}' | jq -e '.ok' >/dev/null; echo $?   # 1
```
