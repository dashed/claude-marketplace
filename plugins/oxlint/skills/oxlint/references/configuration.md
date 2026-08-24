# oxlint Configuration Reference

Every key verified against `npm/oxlint/configuration_schema.json` shipped with **oxlint 1.79.0**
(the schema's own `version` field matches the binary), plus behaviour tested on that binary.

## Contents

- [Config file discovery](#config-file-discovery)
- [The 12 top-level keys](#the-12-top-level-keys)
- [`plugins` — replaces, never adds](#plugins--replaces-never-adds)
  - [The silent-discard bug](#the-silent-discard-bug)
- [`categories` and `rules`](#categories-and-rules)
- [`options`](#options)
- [`env` and `globals`](#env-and-globals)
- [`ignorePatterns` and file discovery](#ignorepatterns-and-file-discovery)
- [`overrides` — merges](#overrides--merges)
- [Nested configs — replace](#nested-configs--replace)
- [`extends`](#extends)
- [`settings`](#settings)
- [`jsPlugins`](#jsplugins)
- [Config errors](#config-errors)

## Config file discovery

Per directory, oxlint looks for, in order:

1. `.oxlintrc.json`
2. `.oxlintrc.jsonc`
3. `oxlint.config.ts`
4. `oxlint.config.mts`

JSON and JSONC work in every runtime and **accept comments** (the oxc repo's own `oxlintrc.json`
uses `//` comments freely). TS/MTS configs are **experimental and require running under Node**;
they export `defineConfig({...})` from the `oxlint` package. In Vite+ mode (`VP_VERSION` set) only
`vite.config.ts` is consulted.

`-c/--config <path>` names the root config explicitly. **Passing `-c` also disables nested-config
discovery** — same effect as `--disable-nested-config`. Verified.

Scaffold a correct starting point:

```bash
oxlint --init
```

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["typescript", "unicorn", "oxc"],
  "categories": { "correctness": "error" },
  "rules": {},
  "env": { "builtin": true }
}
```

Two things worth noticing: it writes the **base plugin set out explicitly** (so your later additions
are genuinely additive), and it sets `correctness` to `error` rather than the built-in `warn`.

> ⚠️ **`--init` silently overwrites an existing `.oxlintrc.json`.** No prompt, no backup, exit 0,
> and the message is the same "Configuration file created" as on first run. Verified: a
> hand-written config with custom `plugins` and `rules` was replaced wholesale. Never run it in a
> repo that already has a config unless you intend to discard it.

## The 12 top-level keys

Exactly these validate — anything else is a config error:

| Key | Type | Default |
|---|---|---|
| `$schema` | string | — (editor tooling only) |
| `categories` | object | `{}` (built-in: `correctness` at `warn`) |
| `env` | object | `{ "builtin": true }` |
| `extends` | string[] (JSON) / config objects (TS) | none |
| `globals` | object | `{}` |
| `ignorePatterns` | string[] | `[]` |
| `jsPlugins` | array | none |
| `options` | object | none |
| `overrides` | array | none |
| `plugins` | string[] | `["typescript","unicorn","oxc"]` + implicit `eslint` |
| `rules` | object | `{}` |
| `settings` | object | per-plugin defaults |

## `plugins` — replaces, never adds

The default set is exactly `UNICORN | TYPESCRIPT | OXC` (`impl Default for LintPlugins` in
`crates/oxc_linter/src/config/plugins.rs`). `eslint` is not a member — its rules are always active
and cannot be disabled through `plugins`. The schema states the replacement outright: *"Setting the
`plugins` field will overwrite the base set of plugins. The `plugins` array should reflect all of
the plugins you want to use."*

Verified on 1.79.0 against a file with one violation from each default plugin:

| Config | Findings | Resolved rule count |
|---|---|---|
| *(no `plugins` key)* | eslint, typescript, unicorn, oxc | 111 |
| `{"plugins":["react"]}` | eslint only | 88 |
| `{"plugins":[]}` | eslint only | — |
| `{"plugins":["eslint"]}` | eslint only | — |
| `{"plugins":["typescript","unicorn","oxc"]}` | all four | 111 |

`eslint` is not really a plugin — it is the always-on base and cannot be switched off through
`plugins`. Everything else must be restated.

```jsonc
{ "plugins": ["typescript", "unicorn", "oxc", "react", "import"] }
```

### The silent-discard bug

Dropping a plugin does not just disable its category-driven rules — it **silently discards a rule
you named explicitly in `rules`, at any severity**, with no warning and exit 0:

```bash
$ cat a.json
{"plugins":["react"],"rules":{"unicorn/catch-error-name":"error"}}
$ oxlint -c a.json u2.js     # file: try { doThing() } catch (badName) { ... }
                             # ← no output whatsoever
$ echo $?
0

$ cat b.json                 # only change: unicorn added back
{"plugins":["react","unicorn"],"rules":{"unicorn/catch-error-name":"error"}}
$ oxlint -c b.json u2.js
u2.js:1:26: error unicorn(catch-error-name): The catch parameter "badName" should be named "error"
$ echo $?   # → 1
```

Passing the rule on the CLI instead (`-D unicorn/catch-error-name`) is **equally silent** —
verified. Note the inconsistency: a *misspelled* rule name is a hard config error
(`Rule 'x' not found in plugin 'eslint'`), so oxlint does validate rule names — it just does not
warn when a valid rule's plugin is absent.

**Why it survives code review.** `eslint` rules are unaffected, so a config that mixes both keeps
working *partially*:

```bash
$ cat mix.json
{"plugins":["react"],"rules":{"no-invalid-regexp":"error","unicorn/catch-error-name":"error"}}
$ oxlint -c mix.json mix.js
mix.js:1:25: error eslint(no-invalid-regexp): Invalid regular expression …
$ echo $?   # → 1
```

The build is red either way, so the missing unicorn rule never draws attention.

**Detection.** No flag warns. Check the **plugin set**, not the rule list: every plugin your rules
reference must be present in the resolved `plugins`.

```bash
comm -23 \
  <(jq -r '[.rules // {}] + [.overrides // [] | .[] | .rules // {}] | add // {} | keys[]' .oxlintrc.json \
     | sed -E -e 's#^(eslint|oxlint)-plugin-##' -e 's#^@typescript-eslint/#typescript/#' \
              -e 's#^@next/next/#nextjs/#'      -e 's#^react-hooks/#react/#' \
              -e 's#^import-x/#import/#'        -e 's#^deepscan/#oxc/#' \
     | grep / | sed -E 's#/.*##' | sort -u) \
  <(oxlint --print-config | jq -r '.plugins[], "eslint"' | sort -u)
```

The `sed` chain normalizes the accepted aliases to their canonical plugin name; `grep /` drops bare
`eslint` rules, which are always on. Validated on 16 configs (5 broken, 11 working, exercising every
alias form, `rules` set to `"off"`, a config with no `rules` key, and a rule buried in `overrides`):
it named the missing plugin in all 5 broken cases and stayed silent on all 11 working ones.

### Why not compare rule names against `--print-config`

The intuitive check — list the rules you named, list the rules that survived, diff them — is
**unreliable in two verified ways**, so prefer the plugin check above.

**1. Bare-name collisions hide the dead rule.** Stripping the plugin prefix (needed, because
`--print-config` normalizes `@typescript-eslint/x` → `typescript/x` and spells `jsx-a11y` as
`jsx_a11y`) makes a surviving twin mask a dead rule. 870 rules contain many duplicated bare names —
`jest`/`vitest` alone share about 30:

```bash
$ cat .oxlintrc.json
{"plugins":["typescript","unicorn","oxc","vitest"],"rules":{"jest/valid-expect":"error"}}
# jest/valid-expect is dead, but vitest/valid-expect is present, so a bare-name diff prints
# nothing at all. Same trap: vue/no-dupe-keys masked by the always-on core no-dupe-keys.
```

**2. `--print-config` actively misreports `overrides`.** A rule inside `overrides` whose plugin is
missing is still printed as `"deny"` — byte-identical to the working config — while the rule does
nothing:

```bash
$ cat .oxlintrc.json
{"plugins":["react"],"overrides":[{"files":["**/*.js"],"rules":{"unicorn/catch-error-name":"error"}}]}
$ oxlint --print-config | jq -c '.overrides[0].rules'
{"unicorn/catch-error-name":"deny"}     # ← identical with or without unicorn in plugins
$ oxlint .                              # ← no output, exit 0: the rule is dead
```

So no rule-presence check can detect the `overrides` case at all. The plugin-membership check can,
because `plugins` is resolved correctly even when the `overrides` rule map is not.

If you skip the check entirely, the honest fallback is to add the plugin back and re-run: new
findings mean the rule was never running.

Alias handling and the full plugin table live in
[rules-and-categories.md](rules-and-categories.md#the-15-plugins).

## `categories` and `rules`

```jsonc
{
  "categories": { "correctness": "error", "perf": "error" },
  "rules": {
    "no-console": "error",
    "curly": ["error", "multi-line"],
    "prefer-const": ["error", { "destructuring": "all" }],
    "typescript/ban-ts-comment": ["error", { "ts-expect-error": "allow-with-description" }],
    "vitest/prefer-snapshot-hint": "off"
  }
}
```

`rules` beats `categories` for the named rule — the schema says so and it is verified: root
`{"categories":{"correctness":"error"},"rules":{"no-dupe-keys":"warn"}}` yields 3 errors + 1 warning.

Rule keys accept the bare name (`no-dupe-keys` → the `eslint` plugin), the canonical qualified name
(`typescript/no-explicit-any`), or an ESLint-style alias (`@typescript-eslint/no-explicit-any`).
`ts/...` is **not** an accepted alias and fails config parsing.

Severity values: `"allow"`/`"off"`/`0`, `"warn"`/`1`, `"error"`/`"deny"`/`2`.

## `options`

Exactly six keys — the schema sets `additionalProperties: false`:

| Key | Type | CLI equivalent | Notes |
|---|---|---|---|
| `denyWarnings` | boolean | `--deny-warnings` | Warnings produce a non-zero exit |
| `maxWarnings` | integer ≥ 0 | `--max-warnings` | Exceeding the threshold exits non-zero |
| `reportUnusedDisableDirectives` | severity | `--report-unused-disable-directives-severity` | **Root config only**; CLI wins |
| `respectEslintDisableDirectives` | boolean (default `true`) | — | Honor `eslint-disable*` comments. **Root config only** |
| `typeAware` | boolean | `--type-aware` | Requires the `oxlint-tsgolint` package |
| `typeCheck` | boolean | `--type-check` | Experimental; requires `typeAware` too |

```jsonc
{ "options": { "typeAware": true, "typeCheck": true, "denyWarnings": true } }
```

## `env` and `globals`

Straight from ESLint v8 and behaviourally identical. `env` defaults to `{ "builtin": true }`
(latest ECMAScript globals, equivalent to `es2026`).

```jsonc
{
  "env": { "builtin": true, "browser": true, "node": true, "vitest": true },
  "globals": { "myGlobal": "readonly", "__DEV__": "writable", "oldApi": "off" }
}
```

43 environments are recognised: `amd`, `applescript`, `astro`, `atomtest`, `audioworklet`,
`browser`, `builtin`, `commonjs`, `embertest`, `es2015`–`es2026`, `es6`, `greasemonkey`, `jasmine`,
`jest`, `jquery`, `meteor`, `mocha`, `mongo`, `nashorn`, `node`, `phantomjs`, `prototypejs`,
`protractor`, `qunit`, `serviceworker`, `shared-node-browser`, `shelljs`, `svelte`, `vitest`,
`vue`, `webextensions`, `worker`.

These only matter for rules that consult the global scope. `no-undef` is the main one — and it is
a **nursery** rule, so it is off until you enable it. Verified: with `no-undef` on and no `env`,
`window` and `process` both report; adding `"browser": true, "node": true` clears them, and
`globals` clears a project-specific name.

## `ignorePatterns` and file discovery

```jsonc
{
  "ignorePatterns": [
    "**/generated/**",
    "tasks/coverage/**",
    "!apps/oxlint/test/fixtures/**",   // leading ! re-includes
    "*.d.ts"
  ]
}
```

Gitignore-style matching, **rooted at the directory containing the config file**. Files outside
that directory cannot be matched, and a pattern containing `..` is rejected as a config error.

**Ignore precedence, verified:**

| Source | Honored by default | Disabled by `--no-ignore`? |
|---|---|---|
| `.gitignore` | ✅ (even outside a git repo) | ❌ **no** — always applied |
| `.eslintignore` | ✅ | ✅ |
| `--ignore-path <file>` | when passed | ✅ |
| `--ignore-pattern <glob>` | when passed | ✅ |
| `ignorePatterns` in config | ✅ | ❌ |

Two consequences people trip on:

- **`node_modules` is not special-cased.** In a directory whose `.gitignore` does not list it,
  `oxlint --debug files .` includes `node_modules/x.js`. Real projects are saved only by their
  `.gitignore`.
- **Hidden dot-directories are linted** by default (a deliberate 1.x change:
  *"oxlint: [BREAKING] Do not ignore hidden dot directories by default"*).

`oxlint --debug files` prints the resolved file list and exits — the fastest way to settle any
"why isn't this file linted" question. If nothing matches, oxlint exits **1** with
`No files found to lint`; `--no-error-on-unmatched-pattern` makes that exit 0 (useful under
lint-staged).

## `overrides` — merges

`overrides` entries are **patched onto** the surrounding config for matching files. Accepted keys:
`files`, `excludeFiles`, `rules`, `plugins`, `env`, `globals`, `jsPlugins`.

```jsonc
{
  "categories": { "correctness": "error" },
  "overrides": [
    { "files": ["tests/**"], "rules": { "no-debugger": "off" } },
    { "files": ["src/**"], "plugins": ["react"], "rules": { "no-dupe-keys": "warn" } }
  ]
}
```

Verified: under the first override, `tests/**` files still report `no-dupe-keys` at **error** —
the base `categories` survives. That is the opposite of nested-config behaviour below.

## Nested configs — replace

A `.oxlintrc.json` in a subdirectory is auto-discovered by walking up from each linted file, and it
**wholly replaces** the root config for files beneath it. The child does not inherit; it starts
from oxlint's built-in defaults plus its own contents.

Two verifications, both with a child config that only sets `{"rules":{"no-debugger":"off"}}`:

| Root config | Without child | With child |
|---|---|---|
| `{"categories":{"correctness":"error"},"rules":{"no-dupe-keys":"error"}}` | `no-dupe-keys` at **error** | `no-dupe-keys` at **warn** |
| `{"plugins":["react"],"categories":{"correctness":"error"}}` | typescript rule silent (plugin dropped) | typescript rule **reappears at warn** |

In the second case the child discarded the root's `plugins` restriction *and* its severity, landing
back on plain defaults. This is easy to misread as "my root config is being ignored".

Turn discovery off with `--disable-nested-config`, or by passing `-c` explicitly.

## `extends`

The opt-in way to inherit:

```jsonc
// pkg/.oxlintrc.json
{ "extends": ["../base.json"], "rules": { "no-debugger": "off" } }
```

- In JSON configs, `extends` is `string[]` of **paths resolved relative to the file that contains
  the `extends`** — verified: from `pkg/.oxlintrc.json`, `"./base.json"` looks for `pkg/base.json`.
- Configs merge **first to last, with the last overriding earlier ones**.
- In `oxlint.config.ts`, `extends` takes imported config *objects*, not paths.

Verified: the example above restored the root's `no-dupe-keys: "error"` while keeping the child's
`no-debugger: "off"`.

## `settings`

Plugin-specific configuration. Six built-in sections: `jest`, `jsdoc`, `jsx-a11y`, `next`, `react`,
`vitest` (plus arbitrary keys consumed by `jsPlugins`).

```jsonc
{
  "settings": {
    "react": { "version": "18.2.0", "formComponents": [], "linkComponents": [] },
    "jsx-a11y": { "polymorphicPropName": null, "components": {}, "attributes": {} },
    "next": { "rootDir": [] },
    "jsdoc": { "ignorePrivate": false, "tagNamePreference": {} },
    "vitest": { "typecheck": false },
    "jest": { "version": null }
  }
}
```

## `jsPlugins`

An ESLint-shaped JavaScript/TypeScript plugin system. The schema is explicit:
**"JS plugins are in alpha and not subject to semver."** Treat it accordingly.

```jsonc
{
  "jsPlugins": ["./custom-plugin.js"],
  "rules": { "demo/no-foo": "error" }
}
```

```js
// custom-plugin.js
export default {
  meta: { name: "demo" },
  rules: {
    "no-foo": {
      create(context) {
        return { Identifier(node) {
          if (node.name === "foo") context.report({ node, message: "no foo allowed" });
        } };
      },
    },
  },
};
```

Verified working on 1.79.0 — the rule fires and reports as `demo(no-foo)`. Rules are addressed as
`<meta.name>/<rule>`.

TypeScript plugin files work on Deno, Bun, and Node ≥22.18.0 / ^20.19.0 (native type stripping);
older Node needs plain JavaScript. An npm-published ESLint plugin can be aliased to avoid colliding
with a built-in Rust plugin of the same name:

```jsonc
{
  "plugins": ["import"],
  "jsPlugins": [{ "name": "import-js", "specifier": "eslint-plugin-import" }],
  "rules": { "import/no-cycle": "error", "import-js/no-unresolved": "warn" }
}
```

## Config errors

All config problems exit **1** — the same code as lint findings (oxlint has no exit 2). Read
stderr. Verified messages:

| Situation | Message |
|---|---|
| Unknown rule name | `Rule 'totally-not-a-rule' not found in plugin 'eslint'` |
| Wrong value type | `Failed to parse config with error Error("invalid type: string ...")` |
| `-c` path missing | `Failed to parse config <path> ... NotFound` |
| Unknown CLI flag | `Error: '--bogus-flag' is not expected in this context` |
| `--type-check` alone | `The '--type-check' option requires type-aware linting.` |

Unknown rule names being a *hard error* is a deliberate 1.x behaviour change
(*"linter: [BREAKING] Report error on unknown builtin rule"*), so a config that worked on an older
oxlint can fail outright after an upgrade — usually because a rule was renamed or recategorised.
