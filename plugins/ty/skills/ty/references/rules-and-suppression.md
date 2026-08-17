# ty rules & suppression

Counts and rule names verified against **ty 0.0.72** via `ty explain rule --output-format json`.
This file deliberately does **not** enumerate all 126 rules — it teaches the severity model, the
naming scheme, and the lookup commands, so you can answer rule questions on *your* build.

## Contents

- [The severity model](#the-severity-model)
- [Looking a rule up](#looking-a-rule-up)
- [Rule categories (naming scheme)](#rule-categories-naming-scheme)
- [The opt-in rules](#the-opt-in-rules)
- [Setting levels](#setting-levels)
- [Suppression comments](#suppression-comments)
- [Unused-suppression hygiene](#unused-suppression-hygiene)
- [`--add-ignore`: baselining an existing codebase](#--add-ignore-baselining-an-existing-codebase)
- [Suppression-related rules](#suppression-related-rules)

## The severity model

Every rule has one of three **levels** — this is a severity, not an on/off switch:

| Level | Diagnostic prefix | Exit code impact |
|---|---|---|
| `error` | `error[rule-name]` | Exit 1 |
| `warn` | `warning[rule-name]` | Exit 1 **by default** (`terminal.error-on-warning = true`); exit 0 with `--exit-zero-on-warning` |
| `ignore` | — | Rule is off |

There is a fourth severity you'll see in output — `info[rule-name]`, e.g. `revealed-type` from
`reveal_type()`. `info` diagnostics never affect the exit code and are not rule-configurable in the
same way.

Distribution on 0.0.72 (126 rules total):

| Default level | Count | Meaning |
|---|---|---|
| `error` | 93 | Almost certainly a bug |
| `warn` | 23 | Suspicious, or about ty's own directives |
| `ignore` | 10 | Opt-in: opinionated or false-positive-prone |

That distribution *is* ty's strictness story: nearly everything is on by default, which is why ty has
no `--strict` flag. Adopting ty is mostly about turning things **down**, not up.

## Looking a rule up

Do not memorize the catalog. Every diagnostic prints its rule name in brackets — feed that to:

```bash
ty explain rule invalid-argument-type       # what it does / why it's bad / example
ty explain rule                             # every rule, long form
ty explain rule --output-format json        # machine-readable catalog
```

Misspellings are helpful rather than fatal:

```
$ ty explain rule possibly-unbound-attribute
ty failed
  Cause: Unknown rule `possibly-unbound-attribute`. Did you mean `possibly-missing-attribute`?
```

Useful JSON queries — each record has `name`, `summary`, `documentation`, `default_level`, `status`:

```bash
ty explain rule --output-format json | jq -r '.[] | select(.default_level=="ignore") | .name'
ty explain rule --output-format json | jq -r '.[] | "\(.default_level)\t\(.name)"' | sort
ty explain rule --output-format json | jq -r '.[] | select(.name|test("typed-dict")) | .name'
ty explain rule --output-format json | jq -r '.[] | "\(.name) \(.status.type) \(.status.since // "")"'
```

`status` reports stability (`{"type":"stable","since":"0.0.64"}`); on 0.0.72 all 126 rules report
`stable`, so `status` is currently a weak filter — use `default_level` to find the opt-ins.

Prose docs: `docs/reference/rules.md` in the ty repo, or <https://docs.astral.sh/ty/reference/rules/>.

## Rule categories (naming scheme)

Rule names are systematic, so you can usually guess the family before looking it up:

| Prefix | ~n | What it covers |
|---|---|---|
| `invalid-*` | 48 | By far the largest family: a declaration, annotation, or construct is malformed — `invalid-argument-type`, `invalid-assignment`, `invalid-return-type`, `invalid-type-form`, `invalid-method-override`, the `invalid-typed-dict-*` and `invalid-type-variable-*` sub-families. |
| `unresolved-*` | 4 | A name can't be found: `unresolved-import`, `unresolved-reference`, `unresolved-attribute`, `unresolved-global`. |
| `possibly-*` | 5 | Conditionally-bound / conditionally-present things — attribute, import, submodule, implicit call, reference. Mostly opt-in; the source of most "why is this an error?" surprises. |
| `missing-*` | 4 | Something required is absent: `missing-argument`, `missing-typed-dict-key`, `missing-type-argument`, `missing-override-decorator`. |
| `unsupported-*` | 4 | The operation isn't valid for the type: `unsupported-operator`, `unsupported-base`, `unsupported-bool-conversion`, `unsupported-dynamic-base`. |
| `unused-*` | 3 | Dead code/directives: `unused-ignore-comment`, `unused-type-ignore-comment`, `unused-awaitable`. |
| `unsound-*` | 2 | Opt-in soundness holes ty tolerates by default: `unsound-return-statement`, `unsound-yield`. |
| class-shape families | ~15 | `abstract-*`, `final-*`, `override-of-final-*`, `subclass-of-*`, `conflicting-*`, `duplicate-*`, `cyclic-*`, `inconsistent-mro`, `instance-layout-conflict`. |
| directive hygiene | 5 | `invalid-ignore-comment`, `ignore-comment-unknown-rule`, `blanket-ignore-comment`, plus the `unused-*-ignore-comment` pair. (Overlaps the `invalid-*` and `unused-*` rows above.) |
| one-offs | — | `deprecated`, `redundant-cast`, `not-iterable`, `not-subscriptable`, `index-out-of-bounds`, `division-by-zero`, `no-matching-overload`, `too-many-positional-arguments`, `undefined-reveal`, … |

## The opt-in rules

The 10 rules at `ignore` by default — these are your strictness dial:

| Rule | What it catches |
|---|---|
| `possibly-missing-attribute` | Attribute may not exist on the object (conditionally defined) |
| `possibly-missing-import` | Import may not be present |
| `possibly-unresolved-reference` | Name may be unbound on some path |
| `missing-type-argument` | Bare generic used without type parameters (mypy `type-arg`) |
| `missing-override-decorator` | Override without `@override` (mypy `explicit-override`) |
| `unsound-return-statement` | Returns a type that isn't a subtype of the annotated return |
| `unsound-yield` | Yields a type that isn't a subtype of the annotated yield type |
| `unsupported-dynamic-base` | Dynamic base class whose MRO ty can't compute |
| `blanket-ignore-comment` | Bare `# ty: ignore` with no rule code |
| `division-by-zero` | Literal division by zero |

The `possibly-*` three and `division-by-zero` are the false-positive-prone group — ty's own docs
flag them as "enable at your own risk". `missing-type-argument`, `possibly-unresolved-reference`,
and `unsound-return-statement` are the recommended first three to turn on.

## Setting levels

CLI — repeatable, later wins, `all` targets everything:

```bash
ty check --warn unused-ignore-comment --ignore redundant-cast --error possibly-missing-import
ty check --error all                    # allowed; not recommended
```

Config — equivalent, and what you actually commit:

```toml
[tool.ty.rules]                          # or [rules] in ty.toml
all = "error"
redundant-cast = "ignore"
possibly-missing-import = "warn"
```

Per-path, via `[[overrides]]`:

```toml
[[tool.ty.overrides]]
include = ["tests/**"]
rules = { possibly-missing-attribute = "ignore" }
```

An unknown rule name in config produces `warning[unknown-rule]` and checking continues — it is not
a hard failure. After any upstream rule rename, a stale entry silently stops applying, so don't
suppress `unknown-rule`.

## Suppression comments

ty's native form carries the rule code in brackets, at the **end of the line**:

```python
a = 10 + "test"                       # ty: ignore[unsupported-operator]
```

**Multiple rules on one line** — comma-separated inside one bracket:

```python
sum_three(  "one", 5)                 # ty: ignore[missing-argument, invalid-argument-type]
```

**Multi-line violations** — put the comment on the **first or last** line of the span:

```python
sum_three(                            # ty: ignore[missing-argument]
    3,
    2
)

sum_three(
    3,
    2
)                                     # ty: ignore[missing-argument]
```

**File-level** — a `# ty: ignore[<rule>]` on its own line, **before any Python code**:

```python
# ty: ignore[invalid-argument-type]

sum_three(3, 2, "1")
```

**PEP 484 interop** — ty also honors the standard form:

- `# type: ignore` — suppresses **everything** on that line.
- `# type: ignore[ty:<rule>]` — behaves exactly like `# ty: ignore[<rule>]`. Codes without a `ty:`
  prefix are ignored by ty, so one comment can serve several checkers:

```python
value = f("one", 5, 2)   # type: ignore[arg-type, ty:invalid-argument-type]
```

Set `analysis.respect-type-ignore-comments = false` to make ty stop honoring bare `# type: ignore`
— useful when migrating off mypy and you want ty-specific suppressions only.

**Stacking with other tools' comments** — put both on the same line, in either order:

```python
result = calculate()  # ty: ignore[invalid-argument-type]  # fmt: skip
result = calculate()  # fmt: off  # ty: ignore[invalid-argument-type]
```

**Whole function** — the standard `@no_type_check` decorator silences everything inside a function.
Applying it to a **class is not supported**.

```python
from typing import no_type_check

@no_type_check
def main():
    sum_three(1, 2)      # no error
```

Always name the rule. A bare `# ty: ignore` swallows every future diagnostic on that line —
`blanket-ignore-comment` (opt-in) exists specifically to ban it, and Ruff's `PGH003` covers the
`# type: ignore` equivalent.

## Unused-suppression hygiene

`unused-ignore-comment` (**warn** by default) reports suppressions that no longer suppress anything.
The rule has a deliberate quirk worth knowing:

> `unused-ignore-comment` violations can only be suppressed with
> `# ty: ignore[unused-ignore-comment]` — **not** with a bare `# ty: ignore` and **not** with
> `# type: ignore`.

Companion rules: `unused-type-ignore-comment` (warn), `invalid-ignore-comment` (warn, malformed
syntax), `ignore-comment-unknown-rule` (warn, the code names a rule ty doesn't have — the tell for a
renamed rule).

Since these are warn-level and warnings exit 1 by default, stale suppressions will fail CI. That is
usually what you want; if not, `--exit-zero-on-warning`.

## `--add-ignore`: baselining an existing codebase

```bash
ty check --add-ignore
```

Rewrites your source, appending `# ty: ignore[<rule>]` to every line that currently has a
diagnostic, reports `Added N ignore comments`, and exits **0**. Verified on 0.0.72:

```python
# before
g("s")
# after
g("s")  # ty: ignore[invalid-argument-type]
```

This is the intended adoption path on a large repo: land a green baseline in one mechanical commit,
turn on CI, then delete suppressions incrementally — `unused-ignore-comment` tells you when a fix
has made one redundant. Run it on a clean working tree and review the diff; it edits files in place
and will happily suppress a real bug.

Related but different: `--fix` applies actual code fixes where a rule offers one (output shows
`(N fixed, M remaining)`). Most type errors have no automatic fix, so `--fix` is usually a no-op.

## Suppression-related rules

| Rule | Default | Purpose |
|---|---|---|
| `unused-ignore-comment` | warn | `ty: ignore` / `type: ignore` that suppresses nothing |
| `unused-type-ignore-comment` | warn | Specifically an unused `type: ignore` |
| `invalid-ignore-comment` | warn | Malformed suppression syntax |
| `ignore-comment-unknown-rule` | warn | Suppression names a rule that doesn't exist |
| `blanket-ignore-comment` | ignore (opt-in) | Bare `ty: ignore` with no rule code |

One more diagnostic to know about: **`unknown-rule`** fires (as a warning) when a *config* entry names a rule that doesn't exist. It is a diagnostic id, **not a configurable rule** — it is absent from `ty explain rule`, and `rules.unknown-rule = "ignore"` does not silence it; it merely triggers another `unknown-rule` warning. Same for `revealed-type`, the `info` diagnostic emitted by `reveal_type()`.
