# oxlint Rules, Plugins & Categories

Verified against **oxlint 1.79.0** and `npm/oxlint/configuration_schema.json` from the same version.

## Contents

- [The composition model](#the-composition-model)
- [The 15 plugins](#the-15-plugins)
- [The 7 categories](#the-7-categories)
- [Severity values](#severity-values)
- [Resolution order](#resolution-order)
- [CLI accumulation is order-dependent](#cli-accumulation-is-order-dependent)
- [Querying the catalog](#querying-the-catalog)
- [Fix-safety taxonomy](#fix-safety-taxonomy)
- [Type-aware rules](#type-aware-rules)
- [Suppression comments](#suppression-comments)
- [Recipes](#recipes)

## The composition model

```
enabled(rule)  =  plugin(rule) is ON  AND  category(rule) is ON
final severity =  rules{}  >  categories{}  >  built-in default
CLI flags override the config file in both directions.
```

There is **no "recommended" preset**. Where ESLint has `extends: ["eslint:recommended"]`, oxlint has
`categories: { "correctness": "error" }`. Categories are the bulk switch.

**Out of the box, 111 rules run** — the `correctness` rules of the four default-on plugins. Confirm
on your build:

```bash
oxlint --print-config | jq '{plugins, n: (.rules|length)}'
# {"plugins":["unicorn","typescript","oxc"],"n":111}
```

`--print-config` is the ground truth for "what will actually run". Note it spells `eslint` rules
bare (`no-dupe-keys`) and every other plugin qualified (`typescript/no-this-alias`).

## The 15 plugins

`plugins` **replaces** the base set — it is never additive. The default is exactly
`UNICORN | TYPESCRIPT | OXC` (`impl Default for LintPlugins`); `eslint` is not a member of that set
but is always on and cannot be removed (even `"plugins": []` keeps it).

⚠️ Dropping a plugin **silently discards rules you named explicitly in `rules`** — no warning,
exit 0, and the CLI `-D` form is just as silent. See
[configuration.md](configuration.md#the-silent-discard-bug) for the verified repro and the only
detection that works.

| Plugin | Rules | of which `correctness` | On by default |
|---|---:|---:|---|
| `eslint` | 187 | 57 | ✅ (implicit — never listed, never removable) |
| `unicorn` | 138 | 13 | ✅ |
| `typescript` | 110 | 27 | ✅ |
| `oxc` | 27 | 14 | ✅ |
| `react` | 85 | 31 | off |
| `vitest` | 73 | 17 | off |
| `jest` | 60 | 12 | off |
| `vue` | 46 | 31 | off |
| `jsx-a11y` | 36 | 35 | off |
| `import` | 33 | 2 | off |
| `jsdoc` | 23 | 9 | off |
| `nextjs` | 21 | 21 | off |
| `promise` | 16 | 3 | off |
| `node` | 11 | 0 | off |
| `react-perf` | 4 | 0 | off |

**870 rules total.** Note `react-perf` and `node` have zero `correctness` rules — enabling those
plugins alone changes nothing until you also enable a category or name rules explicitly.

**Naming gotcha:** the `--rules --format json` catalog reports `scope` with underscores
(`jsx_a11y`, `react_perf`); *config* requires hyphens (`jsx-a11y`, `react-perf`). `--print-config`
uses hyphens.

**CLI equivalents.** Default-on plugins have `--disable-*-plugin` switches
(`--disable-unicorn-plugin`, `--disable-oxc-plugin`, `--disable-typescript-plugin`); the rest have
`--*-plugin` enablers (`--react-plugin`, `--import-plugin`, `--jsdoc-plugin`, `--jest-plugin`,
`--vitest-plugin`, `--jsx-a11y-plugin`, `--nextjs-plugin`, `--react-perf-plugin`,
`--promise-plugin`, `--node-plugin`, `--vue-plugin`).

### Plugin-name aliases

Accepted at runtime and normalized (source: `crates/oxc_linter/src/config/plugins.rs`):

| You write | Resolves to |
|---|---|
| `typescript-eslint`, `typescript_eslint`, `@typescript-eslint` | `typescript` |
| `react-hooks`, `react_hooks` | **`react`** (react-hooks rules live in the react plugin) |
| `import-x` | `import` |
| `jsx_a11y`, `jsx-a11y-x`, `jsx_a11y-x` | `jsx-a11y` |
| `react_perf` | `react-perf` |
| `deepscan` | `oxc` (legacy; those rules moved into `oxc`) |
| `@next`, `@next/next` | `nextjs` |
| `eslint-plugin-<x>`, `oxlint-plugin-<x>`, `@scope/eslint-plugin-<x>` | prefix stripped |

Aliases work, but the JSON schema's `plugins` enum lists only the 15 canonical names — use those so
editor schema validation stays quiet.

## The 7 categories

| Category | Rules | Description (from `--help`) | Default |
|---|---:|---|---|
| `correctness` | 272 | Code that is outright wrong or useless | **on, `warn`** |
| `style` | 280 | Should be written in a more idiomatic way | off |
| `pedantic` | 126 | Rather strict or occasional false positives | off |
| `restriction` | 103 | Prevent the use of language/library features | off |
| `suspicious` | 63 | Most likely wrong or useless | off |
| `perf` | 15 | Could be written in a more performant way | off |
| `nursery` | 11 | New lints still under development | off |

Counts cross-checked two ways: `oxlint --rules --format default` prints them as section headers,
and `jq 'group_by(.category)'` over `--rules --format json` agrees exactly (sum = 870).

`all` = every category **except `nursery`**, and it does **not** enable plugins.

The 11 nursery rules at 1.79.0: `eslint/no-restricted-exports`, `eslint/no-undef`,
`eslint/no-unreachable-loop`, `eslint/no-useless-assignment`, `import/export`, `import/named`,
`promise/no-return-in-finally`, `react/require-render-return`,
`typescript/no-unnecessary-condition`, `typescript/prefer-optional-chain`,
`unicorn/no-useless-iterator-to-array`. (`no-undef` being nursery surprises people migrating from
ESLint — it is off unless you ask for it.)

## Severity values

`rules` and `categories` both accept, per the schema:

| String | Number | Meaning |
|---|---|---|
| `"allow"` / `"off"` | `0` | Rule off |
| `"warn"` | `1` | On — **does not affect the exit code** |
| `"error"` / `"deny"` | `2` | On — exits non-zero |

Rule options use the ESLint tuple form: `"curly": ["error", "multi-line"]`.

That "`warn` doesn't affect exit code" line is upstream's own wording in the schema, and it is the
reason a default `oxlint` run is green on a repo full of correctness violations.

## Resolution order

1. Built-in defaults (`correctness` at `warn`, four plugins on).
2. `categories` in the config.
3. `rules` in the config — beats `categories` for the named rule.
4. `overrides[].rules` for matching files — merged onto the above.
5. CLI `-A`/`-W`/`-D`, applied left to right.

None of this enables a *plugin*: steps 3–5 set severity only. Naming `unicorn/catch-error-name` in
`rules` when `unicorn` is not in `plugins` is a silent no-op.

Verified: root `{"categories":{"correctness":"error"},"rules":{"no-dupe-keys":"warn"}}` produced
3 errors + 1 warning.

## CLI accumulation is order-dependent

`-A`/`-W`/`-D` accumulate **left to right**, and a later flag can undo an earlier one:

```bash
oxlint -A all -D no-dupe-keys      # 1 error   — allow all, then re-deny one rule
oxlint -D no-dupe-keys -A all      # 0 findings — the trailing -A all wipes it
oxlint -D correctness -A no-debugger
```

Always put the broad flag first and the narrowing flags after.

## Querying the catalog

**Never enumerate 870 rules.** Two renderers exist, and only two:

```bash
oxlint --rules --format json      # 870 JSON objects — the machine-readable catalog
oxlint --rules --format default   # ~907-line markdown table grouped by category
```

`stylish`, `unix`, `github` and **`agent`** render nothing for `--rules`. Because oxlint
auto-selects `agent` under an AI agent or CI-agent environment, a bare `oxlint --rules` there emits
**zero bytes** — always pass `--format json`.

Catalog fields: `scope`, `value`, `category`, `type_aware`, `fix`, `default`, `docs_url`.

```bash
oxlint --rules --format json > rules.json

# every rule of one plugin
jq -r '.[] | select(.scope=="react") | "\(.value)\t\(.category)"' rules.json

# what does this rule cost me?
jq '.[] | select(.value=="no-floating-promises")' rules.json

# all autofixable correctness rules
jq -r '.[] | select(.category=="correctness" and (.fix|startswith("fixable"))) | .value' rules.json

# rules that need type information
jq -r '.[] | select(.type_aware) | "\(.scope)/\(.value)"' rules.json

# per-category totals
jq -r 'group_by(.category)[] | "\(.[0].category)\t\(length)"' rules.json
```

`docs_url` gives the canonical page, e.g.
`https://oxc.rs/docs/guide/usage/linter/rules/eslint/no-dupe-keys.html`.

**`default: true` is an approximation.** 114 rules carry it, but only 111 actually run by default —
`vue/no-dupe-keys` (plugin off), `eslint/no-implied-eval` (`suspicious`) and
`typescript/prefer-string-starts-ends-with` (`style`) are flagged `default` yet sit outside the
default plugin × category intersection. Trust `--print-config`.

## Fix-safety taxonomy

Internally a fix carries a bitmask over `{Fix, Suggestion, Dangerous}`
(`crates/oxc_linter/src/fixer/fix.rs`), and each CLI flag sets which bits are *allowed*
(`apps/oxlint/src/command/lint.rs`):

| Flag | Allowed bits | Effect |
|---|---|---|
| `--fix` | `Fix` | Safe fixes only. Behavior-preserving. |
| `--fix-suggestions` | `Suggestion` | Recommendations — "shouldn't cause parse or runtime errors, but may change the meaning of the code". |
| `--fix-dangerously` | `Dangerous \| Fix \| Suggestion` | Everything, including aggressive removals and under-development fixes. |

The flags are additive; `--fix-dangerously` alone subsumes the other two.

Catalog `fix` values seen at 1.79.0 (with counts): `none` 460, `fixable_fix` 153, `pending` 90,
`fixable_suggestion` 73, `conditional_fix` 43, `fixable_dangerous_fix` 17,
`conditional_suggestion` 10, `fixable_safe_fix_or_suggestion` 7,
`conditional_safe_fix_or_suggestion` 6, `conditional_dangerous_fix` 5,
`fixable_dangerous_suggestion` 3, `fixable_dangerous_fix_or_suggestion` 2,
`conditional_dangerous_fix_or_suggestion` 1.

- `fixable_*` — the rule always emits that kind.
- `conditional_*` — depends on the rule's own options.
- `pending` — a fix is planned but not implemented.

**The catalog value is a declared maximum, not a per-diagnostic guarantee.** Verified:
`unicorn/no-useless-spread` is `fixable_dangerous_fix`, yet `--fix` rewrote `[...[1,2,3]]` →
`[1,2,3]` because *that* diagnostic emitted a safe fix. In the same run `--fix` left
`a === b ? true : false` (`eslint/no-unneeded-ternary`, dangerous) untouched; only
`--fix-dangerously` rewrote it to `a === b`.

**There is no dry-run** — no `--diff`, no `--check`, no `--stdin`. Fixes land in place and the exit
code does not change to signal that files were rewritten. Run on a committed tree and review
`git diff`.

## Type-aware rules

59 rules require type information; **all of them are `typescript/*`**. They need a separate npm
package:

```bash
npm i -D oxlint-tsgolint
oxlint --type-aware                  # or "options": { "typeAware": true }
oxlint --type-aware --type-check     # + TypeScript compiler diagnostics (experimental)
```

Without it: `Failed to find tsgolint executable. You may need to add the 'oxlint-tsgolint'
package to your project?` and exit 1. `--type-check` without `--type-aware` is rejected with a
message pointing at the right combination.

**15 of the 111 default rules are type-aware**, so they appear in `--print-config` and silently do
nothing until you enable type-awareness — they are exactly the `typescript/*` rules that are both
`correctness` and type-aware: `await-thenable`, `no-array-delete`, `no-base-to-string`,
`no-duplicate-type-constituents`, `no-floating-promises`, `no-for-in-array`, `no-implied-eval`,
`no-meaningless-void-operator`, `no-misused-spread`, `no-redundant-type-constituents`,
`no-unsafe-unary-minus`, `no-useless-default-assignment`, `require-array-sort-compare`,
`restrict-template-expressions`, `unbound-method`.

> `prefer-string-starts-ends-with` looks like a 16th but is not: the copy in the default set is
> **`unicorn/prefer-string-starts-ends-with`** (`correctness`, *not* type-aware).
> `typescript/prefer-string-starts-ends-with` is type-aware but sits in `style`, so it is off by
> default. Reproduce the list without falling into that trap by keeping the plugin prefix:
>
> ```bash
> comm -12 <(oxlint --print-config | jq -r '.rules|keys[]' | sort -u) \
>          <(oxlint --rules --format json | jq -r '.[]|select(.type_aware)|"\(.scope)/\(.value)"' | sort -u)
> ```

Import resolution uses the nearest `tsconfig.json` automatically; `--tsconfig=<path>` overrides it
only for non-standard names/locations.

## Suppression comments

```js
// oxlint-disable-next-line no-dupe-keys
const a = { x: 1, x: 2 };
const b = { y: 1, y: 2 }; // oxlint-disable-line no-dupe-keys
// eslint-disable-next-line no-dupe-keys        ← honored by default
/* oxlint-disable no-debugger */
debugger;
/* oxlint-enable no-debugger */
debugger;                  // ← fires again: the enable closed the range
```

All four forms verified working. Omitting the rule name suppresses everything on the line.
`options.respectEslintDisableDirectives` (default `true`) toggles the `eslint-*` spellings; it is
only honored in the **root** config.

### The unused-directive ratchet, and what it does not do

```bash
oxlint --report-unused-disable-directives                      # severity: warn → exit 0
oxlint --report-unused-disable-directives-severity deny        # → exit 1  (use this in CI)
```

The two flags are mutually exclusive. Config equivalent:
`"options": { "reportUnusedDisableDirectives": "deny" }` (root config only; CLI wins).

**It is not a safety net for suppressed bugs.** Verified on 1.79.0 with a file containing two
directives — one dead, one hiding a real `no-dupe-keys` violation:

```
u.js:1:1: warning: Unused oxlint-disable directive (no problems were reported).
```

Only the dead directive is reported. The load-bearing one stays invisible, forever, and the run is
green. A blanket `// oxlint-disable-next-line` with no rule name over a genuine bug is likewise not
reported. Treat the flag as hygiene for stale comments, not as verification — audit suppressions by
reading them.

## Recipes

```bash
# What actually runs here?
oxlint --print-config | jq '{plugins, n: (.rules|length)}'

# Did my config edit change the enabled set?
oxlint --print-config | jq -S . > before.json   # …edit…   diff with after.json

# Adopt one category at a time, measuring as you go
oxlint -D correctness                 # start here — it is already on, just make it fail
oxlint -D correctness -D suspicious
oxlint -D correctness -D suspicious -D perf

# Try a plugin before committing to it
oxlint --react-plugin -D correctness src/

# Turn a single noisy rule down without touching the category
oxlint -D correctness -W no-debugger
```
