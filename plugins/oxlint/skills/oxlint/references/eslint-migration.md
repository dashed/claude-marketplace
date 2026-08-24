# Migrating from ESLint to oxlint

Verified against **oxlint 1.79.0**. Your prior is ESLint; this file is about where that prior holds
and where it breaks.

## Contents

- [What carries over, what does not](#what-carries-over-what-does-not)
- [oxlint does not read your ESLint config](#oxlint-does-not-read-your-eslint-config)
- [Config shape translation](#config-shape-translation)
- [There are no presets — categories replace them](#there-are-no-presets--categories-replace-them)
- [Rule and plugin name translation](#rule-and-plugin-name-translation)
- [Is my rule implemented?](#is-my-rule-implemented)
- [Filling the gaps](#filling-the-gaps)
- [Suppression comments](#suppression-comments)
- [A phased migration](#a-phased-migration)
- [CI](#ci)
- [Behaviour differences that bite](#behaviour-differences-that-bite)

## What carries over, what does not

| Concept | ESLint v8 | oxlint |
|---|---|---|
| Config schema | `.eslintrc.json` | **same shape** in `.oxlintrc.json`, plus `categories` |
| Flat config | `eslint.config.js` | **not supported** — `oxlint.config.ts` is oxlint's own format |
| `env`, `globals`, `settings`, `overrides`, `ignorePatterns`, `extends` | ✔ | ✔ same semantics |
| `rules` severity + options tuple | `["error", {...}]` | ✔ identical, incl. `0`/`1`/`2` |
| `plugins` | additive, pairs with `extends` presets | **replaces the base set**, no presets |
| Shareable configs (`eslint-config-*`) | ✔ | ✘ — `extends` takes file paths only |
| `--ext` | ✔ | ✘ — file types are inferred |
| Third-party plugins | any npm package | `jsPlugins` (alpha) or keep ESLint |
| Processors (`.vue`, `.md` blocks) | ✔ | ✘ — the `vue` plugin is a built-in Rust plugin, not a processor |
| Suppression comments | `eslint-disable*` | `oxlint-disable*` **and** `eslint-disable*` |
| Exit code on findings | non-zero | **0 for warnings** — you must opt into failure |

## oxlint does not read your ESLint config

Verified: with an `.eslintrc.json` setting `no-dupe-keys: "error"` present, oxlint still reported it
at `warning` (its own default). An `eslint.config.js` is likewise ignored. Config discovery only
looks for `.oxlintrc.json`, `.oxlintrc.jsonc`, `oxlint.config.ts`, `oxlint.config.mts`.

Upstream ships a migration skill that does the translation for you:

```bash
npx skills add https://github.com/oxc-project/oxc --skill migrate-oxlint
# then: /migrate-oxlint
```

See also <https://oxc.rs/docs/guide/usage/linter/migrate-from-eslint.html>.

## Config shape translation

```jsonc
// .eslintrc.json                         →  .oxlintrc.json
{
  "extends": [                            //  no presets: use `categories`
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended"
  ],
  "plugins": ["import", "unicorn"],       //  MUST also restate typescript/unicorn/oxc
  "env": { "browser": true },             //  identical
  "globals": { "__DEV__": "readonly" },   //  identical
  "rules": {
    "@typescript-eslint/no-explicit-any": "off",
    "import/no-cycle": "error"
  },
  "overrides": [ ... ],                   //  identical (and these MERGE)
  "ignorePatterns": ["dist"]              //  identical
}
```

becomes

```jsonc
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["typescript", "unicorn", "oxc", "import"],
  "categories": { "correctness": "error" },
  "env": { "builtin": true, "browser": true },
  "globals": { "__DEV__": "readonly" },
  "rules": {
    "typescript/no-explicit-any": "off",
    "import/no-cycle": "error"
  },
  "overrides": [ { "files": ["tests/**"], "rules": { "no-debugger": "off" } } ],
  "ignorePatterns": ["dist"]
}
```

The line that matters most is `plugins`. In ESLint it adds; **in oxlint it replaces**. Writing
`"plugins": ["import"]` here would silently disable `typescript`, `unicorn` and `oxc`, taking 111
rules down to a much smaller set — *and* every `typescript/...` or `unicorn/...` rule you carried
over into `rules` would stop running without a word. Start from `oxlint --init`, which writes the
base set out for you, then append.

## There are no presets — categories replace them

There is no `eslint:recommended`, no `plugin:react/recommended`, no `extends` of a shareable
config. The bulk switch is `categories`:

| ESLint | oxlint |
|---|---|
| `extends: ["eslint:recommended"]` | `"categories": { "correctness": "error" }` |
| a stricter preset | add `"suspicious"`, `"pedantic"`, `"perf"`, … |
| `plugin:react/recommended` | `"plugins": [..., "react"]` + `correctness` |

`categories` cuts across plugins: `correctness: "error"` turns on the correctness rules of *every
enabled* plugin at once. A rule fires only if its plugin **and** its category are on — see
[rules-and-categories.md](rules-and-categories.md).

## Rule and plugin name translation

Canonical form is `plugin/rule`, with `eslint` rules written bare. Aliases are accepted, so most
ESLint rule keys paste across unchanged:

| ESLint key | Works? | Canonical |
|---|---|---|
| `no-dupe-keys` | ✔ | `no-dupe-keys` |
| `@typescript-eslint/no-explicit-any` | ✔ alias | `typescript/no-explicit-any` |
| `ts/no-explicit-any` | ✘ **config error** | — |
| `react-hooks/rules-of-hooks` | ✔ alias | `react/rules-of-hooks` (react-hooks rules live in `react`) |
| `import-x/no-cycle` | ✔ alias | `import/no-cycle` |
| `jsx-a11y/alt-text` | ✔ | `jsx-a11y/alt-text` |
| `@next/next/no-img-element` | ✔ alias | `nextjs/no-img-element` |
| `eslint-plugin-unicorn/...` | ✔ prefix stripped | `unicorn/...` |

Plugin names follow the same alias table (`@typescript-eslint` → `typescript`, `react-hooks` →
`react`, `import-x` → `import`, `deepscan` → `oxc`). Full list:
[rules-and-categories.md](rules-and-categories.md#plugin-name-aliases).

Prefer canonical names in committed configs — the JSON schema's enum only knows those 15, so
aliases make your editor complain even though oxlint accepts them.

## Is my rule implemented?

Do not guess — oxlint implements 870 rules, which is a large subset of the ESLint ecosystem but far
from all of it. Ask the catalog:

```bash
oxlint --rules --format json > rules.json

# exact rule?
jq -r '.[] | select(.value=="no-shadow") | "\(.scope)/\(.value)  \(.category)"' rules.json

# which of my ESLint rules survive the move?
jq -r '.[].value' rules.json | sort -u > have.txt
jq -r '.rules | keys[]' .eslintrc.json | sed 's|.*/||' | sort -u > want.txt
comm -13 have.txt want.txt        # ← rules oxlint does NOT implement
```

This match is deliberately on the **bare** rule name, because "does oxlint implement anything called
this?" is the right question when migrating. Read the result as optimistic, though: a name can exist
under a *different* plugin with different behaviour (`no-dupe-keys` is both `eslint` and `vue`;
`prefer-string-starts-ends-with` is `correctness` under `unicorn` but type-aware `style` under
`typescript`). Confirm anything load-bearing with the `select(.value==...)` query above, which shows
the scope and category.

Remember `--rules` renders **only** with `--format json` or `--format default`; under an AI agent
or CI-agent environment the default `agent` format prints nothing at all.

Coverage is uneven by plugin — `jsx-a11y` is nearly complete (35 of 36 rules are `correctness`),
while `import` ships 33 rules and `node` 11.

## Filling the gaps

Three options, in order of preference:

1. **Run both.** The common production setup: oxlint for everything it covers (milliseconds), ESLint
   for the remainder. Nothing prevents both from running over the same tree.
2. **`oxlint-plugin-eslint`** — an official package (versioned in lockstep, 1.79.0) that exposes
   *ESLint's built-in rules* as an oxlint JS plugin:

   ```bash
   npm i -D oxlint-plugin-eslint
   ```
   ```jsonc
   {
     "jsPlugins": [{ "name": "eslint-js", "specifier": "oxlint-plugin-eslint" }],
     "rules": { "eslint-js/no-restricted-syntax": ["error", { "selector": "..." }] }
   }
   ```
3. **`jsPlugins` with an npm ESLint plugin or a local file.** Verified working, but the schema is
   explicit that **JS plugins are in alpha and not subject to semver**. Alias the plugin when its
   name collides with a built-in Rust plugin:

   ```jsonc
   {
     "plugins": ["import"],
     "jsPlugins": [{ "name": "import-js", "specifier": "eslint-plugin-import" }],
     "rules": { "import/no-cycle": "error", "import-js/no-unresolved": "warn" }
   }
   ```

Note that JS plugins give up much of oxlint's speed advantage for the rules they serve.

## Suppression comments

Your existing `eslint-disable` comments keep working — `options.respectEslintDisableDirectives`
defaults to `true`. Verified: `// eslint-disable-next-line no-dupe-keys` suppressed the finding.

```js
// eslint-disable-next-line no-dupe-keys     ← existing comments: no change needed
// oxlint-disable-next-line no-dupe-keys     ← oxlint's native spelling
const b = { y: 1, y: 2 }; // oxlint-disable-line no-dupe-keys
/* oxlint-disable no-debugger */ … /* oxlint-enable no-debugger */
```

If you keep ESLint alongside oxlint, leave the `eslint-*` spellings in place — they satisfy both.

## A phased migration

```bash
# 1. Scaffold. --init writes the base plugin set explicitly and sets correctness=error.
npx oxlint@latest --init          # ⚠️ overwrites an existing .oxlintrc.json without asking

# 2. Measure. What does the default set find today?
npx oxlint@latest

# 3. Confirm what is actually enabled before you tune anything.
npx oxlint@latest --print-config | jq '{plugins, n: (.rules|length)}'

# 4. Add plugins matching your stack — remembering that `plugins` REPLACES.
#    "plugins": ["typescript", "unicorn", "oxc", "react", "import", "vitest"]

# 5. Port rule overrides from .eslintrc.json into `rules` and `overrides`.
#    Unknown rule names are a hard config error, so this step self-checks.

# 6. Fix the free wins on a COMMITTED tree, then read the diff.
git status --porcelain            # must be empty
npx oxlint@latest --fix
git diff

# 7. Turn off the ESLint rules oxlint now covers, so they stop running twice.

# 8. Make CI fail (see below) and pin the version.
npm i -D oxlint
```

Add one category at a time (`-D suspicious`, then `-D perf`, …) rather than jumping to `-D all`.

## CI

```yaml
# GitHub Actions
- run: npx --yes oxlint@1.79.0 --format github -D correctness
```

```jsonc
// or put the failure policy in the config so local runs match CI
{ "categories": { "correctness": "error" }, "options": { "denyWarnings": true } }
```

**The single most important CI fact:** a bare `oxlint` exits **0** even with correctness
violations, because the built-in severity is `warn` and warnings do not affect the exit code
(upstream's own schema says so). Unlike ESLint, you must opt into failure with `-D correctness`,
`--deny-warnings`, `--max-warnings 0`, or the config equivalents.

Add `--no-error-on-unmatched-pattern` under lint-staged or any hook that may pass an empty file
list, otherwise "no files found" exits 1.

## Behaviour differences that bite

| # | Difference |
|---|---|
| 1 | **`plugins` replaces** the default plugin set (`unicorn`+`typescript`+`oxc`) instead of adding to it — and a rule you then name at `"error"` whose plugin is absent is **silently discarded, exit 0**. ESLint would have errored on an unknown rule. Detect with the `comm` check in [configuration.md](configuration.md#the-silent-discard-bug). |
| 2 | **Warnings exit 0.** ESLint's `--max-warnings` habit is mandatory here. |
| 3 | **A nested `.oxlintrc.json` replaces the parent config**, resetting to defaults + its own contents. ESLint cascaded and merged. `extends` is the opt-in. (`overrides` inside one file still merge.) |
| 4 | **Unknown rule names are a hard config error**, exit 1 — a renamed or recategorised rule breaks the build on upgrade. |
| 5 | **No exit code 2.** Config errors and lint errors are both exit 1; read stderr. |
| 6 | **`no-undef` is a nursery rule** and off by default — surprising if you relied on it. TypeScript already covers most of its ground. |
| 7 | **Type-aware rules need `oxlint-tsgolint`**, a separate package. 16 default rules (incl. `no-floating-promises`) are silent no-ops without it. |
| 8 | **`.gitignore` always applies** and `--no-ignore` cannot turn it off; `node_modules` is not special-cased, and hidden dot-directories *are* linted. |
| 9 | **`--fix` has no dry-run** — no `--diff`, no `--check`, no stdin. Commit first. |
| 10 | **1.x minors carry breaking CLI/behaviour changes.** Pin the version. |
