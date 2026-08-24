---
name: oxlint
description: "oxlint — the extremely fast (Rust) JavaScript/TypeScript linter from the oxc project, a drop-in-ish ESLint alternative that needs no config to start. Use when linting JS/TS/JSX/Vue, writing or debugging `.oxlintrc.json` / `oxlint.config.ts`, selecting rules via `plugins` + `categories` (correctness, suspicious, pedantic, perf, style, restriction, nursery), running `--fix` / `--fix-suggestions` / `--fix-dangerously`, suppressing findings with `// oxlint-disable` comments, enabling type-aware rules, wiring oxlint into CI, or migrating a repo from ESLint. Triggers on mentions of oxlint, the oxc linter, `.oxlintrc.json`, `oxlint-disable`, or `npx oxlint`. This is **oxlint**, the linter — NOT **oxfmt** (its sibling formatter, a separate skill here), NOT ESLint or Biome themselves, and NOT **ruff** (the Python linter, also a separate skill here)."
---

# oxlint — JavaScript/TypeScript Linter

## Overview

oxlint is the linter of the **oxc** (Oxidation Compiler) project: one Rust binary, no config
required, finishes a repo in milliseconds. It targets ESLint v8's *config format*, not its plugin
ecosystem.

### Mental model: a rule fires only if its plugin **and** its category are on

```
enabled(rule) = plugin(rule) is ON  AND  category(rule) is ON     then rules{} overrides per-rule
```

Naming a rule in `rules` sets its *severity* — it does **not** enable its plugin. That asymmetry is
the source of the worst bug in this tool (below).

At **1.79.0** there are **870 rules** across **15 plugins** and **7 categories**. Out of the box
exactly **111** run: the `correctness` rules of `eslint` (57, always on) plus the default plugin
set `typescript` (27), `unicorn` (13) and `oxc` (14). Everything else is opt-in. Check any build:

```bash
oxlint --print-config | jq '{plugins, ruleCount: (.rules|length)}'
# {"plugins":["unicorn","typescript","oxc"],"ruleCount":111}   ← `eslint` is implicit, always on
```

### The five things that surprise people

1. **`plugins` REPLACES the default plugin set** — and a rule you explicitly set to `"error"` whose
   plugin is not listed is then **silently discarded: no warning, exit 0**. The #1 footgun (below).
2. **Default severity is `warn`, and warnings exit 0.** A bare `oxlint` in CI passes with
   correctness violations. You must opt into failure.
3. **A nested `.oxlintrc.json` REPLACES the parent config** for files beneath it — no merging.
   (`overrides` *inside* one config *do* merge. Two different mechanisms.)
4. **`--fix` has no dry-run.** No `--diff`, no `--check`, no stdin. Version control is the mitigation.
5. **`--rules` prints nothing under an AI agent** — see the agent note below.

> **Disambiguation:** this is **oxlint**, the linter. **oxfmt** is oxc's sibling *formatter*
> (separate skill here); oxlint does not format. It is an alternative *to* ESLint/Biome, not those
> tools. **ruff** is the Python linter — different language, different skill.

> ### ⚠️ Note for AI agents (verified on 1.79.0)
> oxlint sniffs `CLAUDECODE`, `CLAUDE_CODE`, `AI_AGENT`, `CURSOR_AGENT`, `CODEX_*`, `GEMINI_CLI`
> and friends and silently switches `--format` to `agent` — one compact line per diagnostic instead
> of rich source spans. So your output differs from upstream docs, and **`oxlint --rules` produces
> zero bytes** (the `agent` formatter has no renderer for it): use `--rules --format json`.

## Prerequisites

```bash
npx --yes oxlint@latest --version   # prints "Version: 1.79.0" — note: no tool name
npm i -D oxlint                     # pin per-project (recommended)
```
**Version policy.** oxlint is **1.x, but not SemVer-strict about the CLI.** Minors ship roughly
weekly (77 releases from 1.0.0 to 1.79.0) and *have* carried user-facing breaking changes — "Error
on no matched files", "Report error on unknown builtin rule", "Do not ignore hidden dot directories
by default", and in 1.79.0 "Split react/react-compiler into per-category rules". **Pin it.** This
skill documents **1.79.0**. (Its sibling **oxfmt** is still 0.x.)

## Everyday commands

| Task | Command |
|------|---------|
| Lint | `oxlint [PATH]...` (default: cwd) |
| **Fail on findings** (CI) | `oxlint -D correctness` or `oxlint --deny-warnings` |
| Resolved config — what will *actually* run | `oxlint --print-config` |
| Rule catalog (machine-readable) | `oxlint --rules --format json` |
| Scaffold a config | `oxlint --init` → `.oxlintrc.json` ⚠️ *overwrites silently* |
| Autofix (safe fixes only) | `oxlint --fix` |
| Which files would be linted | `oxlint --debug files` |
| Turn a category up / down | `-D <cat>` / `-W <cat>` / `-A <cat>` |
| Enable a plugin, CLI-side | `--react-plugin`, `--import-plugin`, … |
| CI annotations / LSP | `oxlint -f github` (also `gitlab`, `sarif`, `junit`) · `oxlint --lsp` |

**Exit codes — there are only two.** `0` and `1`. Unlike ruff, oxlint has **no exit 2**: a broken
config, an unknown rule name, a bad flag, "no files found", and real lint errors all exit `1`, so
you cannot tell "my config is wrong" from "my code is wrong" by exit code — read stderr.

Verified on a file with 4 correctness violations: bare `oxlint` → **exit 0** (the CI trap);
`-D correctness`, `--deny-warnings`, `--max-warnings 0`/`2` → 1; `--max-warnings 10` → 0. A path
matching no files also exits 1 — use `--no-error-on-unmatched-pattern`.
Full matrix: [references/cli-reference.md](references/cli-reference.md#exit-codes).

## Plugins — the big footgun

The default plugin set is exactly **`unicorn | typescript | oxc`** (`impl Default for
LintPlugins`). Core **`eslint` rules are always active** and are not part of that set — they cannot
be switched off through `plugins`, and even `"plugins": []` keeps them. Writing `plugins`
**overwrites** the three; it is never additive.

```jsonc
{ "plugins": ["react"] }                                  // ❌ drops typescript, unicorn, oxc
{ "plugins": ["typescript", "unicorn", "oxc", "react"] }  // ✅ restate the set, then add
```

### The rule you explicitly enabled is silently discarded

Worse than ruff's `select`-replaces-defaults: there you at least see a smaller rule set; here you
**name a rule at `"error"` and get silence**. Verified on `try { doThing() } catch (badName) {…}`:

```bash
$ cat a.json
{"plugins":["react"],"rules":{"unicorn/catch-error-name":"error"}}
$ oxlint -c a.json u2.js   # ← no output whatsoever
$ echo $?
0                          # ← and CI is green

$ cat b.json               # only change: unicorn added back
{"plugins":["react","unicorn"],"rules":{"unicorn/catch-error-name":"error"}}
$ oxlint -c b.json u2.js
u2.js:1:26: error unicorn(catch-error-name): The catch parameter "badName" should be named "error"
$ echo $?   # → 1
```

No warning, no error. **Passing it on the CLI instead (`-D unicorn/catch-error-name`) is equally
silent** — verified. Yet a *misspelled* rule name **is** a hard config error: the validation you
would expect exists for typos and simply does not cover this case.

**The asymmetry is why it survives review.** Put an `eslint` rule and a plugin rule in one config at
the same severity — `{"plugins":["react"],"rules":{"no-invalid-regexp":"error","unicorn/catch-error-name":"error"}}`
— and `eslint(no-invalid-regexp)` fires while the unicorn rule is gone and unmentioned. **Exit is 1
either way**, so the build is red, the config looks like it works, and nobody notices.

**Detection.** Nothing warns you, so check the *plugin set* directly: every plugin your rules
reference must appear in the resolved `plugins`. Anything this prints is a plugin you name rules
for but never enabled — those rules are dead.

```bash
comm -23 \
  <(jq -r '[.rules // {}] + [.overrides // [] | .[] | .rules // {}] | add // {} | keys[]' .oxlintrc.json \
     | sed -E -e 's#^(eslint|oxlint)-plugin-##' -e 's#^@typescript-eslint/#typescript/#' \
              -e 's#^@next/next/#nextjs/#'      -e 's#^react-hooks/#react/#' \
              -e 's#^import-x/#import/#'        -e 's#^deepscan/#oxc/#' \
     | grep / | sed -E 's#/.*##' | sort -u) \
  <(oxlint --print-config | jq -r '.plugins[], "eslint"' | sort -u)
# empty output means you are clean
```

Validated on 16 configs (5 broken, 11 working, covering every alias form): it named the missing
plugin in all 5 and stayed silent on all 11.

⚠️ **Do not check this by comparing rule *names* against `--print-config`** — the obvious version of
this check is quietly wrong in two ways, both verified:

- **Bare-name collisions mask the dead rule.** With `plugins: ["...","vitest"]`, a stale
  `jest/valid-expect` is dead, but `vitest/valid-expect` is present, so a name comparison reports
  "clean". Same for `vue/no-dupe-keys` masked by core `no-dupe-keys`.
- **`--print-config` misreports `overrides`.** A rule inside `overrides` whose plugin is missing
  still prints as `"deny"` there — identical output to the working config, while the rule does
  nothing. Rule-presence checks cannot see this case; the plugin check above can.

The honest fallback if you skip all this: add the plugin back and re-run — new findings mean the
rule was never running. `oxlint --init` sidesteps the trap entirely by writing the base set out
explicitly for you.

**All 15 plugin names.** Default set: `typescript`, `unicorn`, `oxc` (plus always-on `eslint`).
Off by default: `react`, `react-perf`, `import`, `jsdoc`, `jest`, `vitest`, `jsx-a11y`,
`nextjs`, `promise`, `node`, `vue`. Each also has a CLI switch (`--react-plugin`,
`--disable-typescript-plugin`, …).

Aliases are accepted (`@typescript-eslint` → `typescript`, `react-hooks` → **`react`**, `import-x`
→ `import`, `@next/next` → `nextjs`, `deepscan` → `oxc`; `eslint-plugin-*`/`oxlint-plugin-*` prefixes
stripped). Prefer the canonical names so editor schema validation passes.

## Categories

| Category | Rules | Meaning (`correctness` is the only one on by default, at `warn`) |
|---|---|---|
| `correctness` | 272 | Outright wrong or useless |
| `suspicious` | 63 | Most likely wrong or useless |
| `pedantic` | 126 | Strict; occasional false positives |
| `perf` | 15 | Could be written more performantly |
| `style` | 280 | Should be written more idiomatically |
| `restriction` | 103 | Prevent use of language/library features |
| `nursery` | 11 | Under development |

`-D`/`-W`/`-A` **accumulate left to right, and order decides the outcome**:
`oxlint -A all -D no-dupe-keys` → 1 error, but `oxlint -D no-dupe-keys -A all` → 0 findings (the
trailing `-A all` wipes the earlier `-D`). `all` means every category **except `nursery`**, and
does **not** enable plugins.
## Rule lookup — never enumerate, always query

870 rules is far too many to memorize or paste. Query the catalog:

```bash
oxlint --rules --format json > rules.json     # 870 entries
jq -r '.[] | select(.scope=="react" and .category=="correctness") | .value' rules.json
```

Entry fields: `scope` (plugin), `value`, `category`, `type_aware`, `fix`, `default`, `docs_url`.
**Caution:** `scope` uses underscores (`jsx_a11y`, `react_perf`) while *config* wants hyphens; and
`default: true` is an approximation — `--print-config` is the ground truth.
More: [references/rules-and-categories.md](references/rules-and-categories.md).

## Configuration

Discovery order per directory: `.oxlintrc.json`, `.oxlintrc.jsonc`, `oxlint.config.ts`,
`oxlint.config.mts` (JSON/JSONC work everywhere and allow comments; TS/MTS are **experimental,
Node only**). The **12** top-level keys are exactly `$schema`, `categories`, `env`, `extends`,
`globals`, `ignorePatterns`, `jsPlugins`, `options`, `overrides`, `plugins`, `rules`, `settings`.

```jsonc
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["typescript", "unicorn", "oxc", "react"],   // REPLACES the base set
  "categories": { "correctness": "error", "perf": "error" },
  "rules": {
    "no-console": "error",                                 // rules{} beats categories{}
    "curly": ["error", "multi-line"]                       // ESLint-style [severity, options]
  },
  "env": { "builtin": true, "browser": true },            // + "globals": { "x": "readonly" }
  "ignorePatterns": ["**/generated/**", "!keep/**"],       // gitignore-style, rooted at this file
  "overrides": [{ "files": ["tests/**"], "rules": { "no-debugger": "off" } }],   // these MERGE
  "options": { "typeAware": true, "denyWarnings": true }
}
```

**Precedence:** CLI flags > `rules` > `categories`. `options` accepts exactly six keys:
`denyWarnings`, `maxWarnings`, `reportUnusedDisableDirectives`,
`respectEslintDisableDirectives`, `typeAware`, `typeCheck`.

**Nested configs replace; they do not cascade.** A `.oxlintrc.json` in a subdirectory is
auto-discovered and **wholly replaces** the root config for files under it — the child resets to
oxlint's defaults plus its own contents. Verified: a root `correctness: "error"` reverts to `warn`
under a child that sets only one unrelated rule. To inherit, say so with
`{ "extends": ["../base.json"] }` (paths relative to *that* file). `--disable-nested-config` turns
discovery off, as does **passing `-c` explicitly**.

**Ignoring files** is `.gitignore`-driven: it is always honored and `--no-ignore` does **not**
override it (that only disables `.eslintignore`, `--ignore-path`, `--ignore-pattern`). There is
**no special case for `node_modules`** — absent a `.gitignore` listing it, oxlint lints it, and
hidden dot-directories too. Check with `oxlint --debug files`.
Full key map: [references/configuration.md](references/configuration.md).

## Fixing — destructive, with no preview

Three additive flags set an *allowed* bitmask over `{Fix, Suggestion, Dangerous}`:

| Flag | Applies | Notes |
|---|---|---|
| `--fix` | safe **fixes** | Behavior-preserving. The default choice. |
| `--fix-suggestions` | **suggestions** | *May change program behavior* — e.g. deletes `debugger;`. |
| `--fix-dangerously` | everything | May break code. Review every hunk. |

Verified: `--fix` rewrote only the safe fix and left `a === b ? true : false` alone;
`--fix-dangerously` rewrote it to `a === b` (`no-unneeded-ternary`, a dangerous fix). A rule's
catalog `fix` value is its *declared maximum* — individual diagnostics may emit a safer kind.

**There is no dry-run.** No `--diff`, no `--check`, no `--stdin`. Fixes are written in place and
**the exit code stays 0** if only warnings remain, so a fix run looks identical to a clean run. The
mitigation that actually works is version control: run on a committed tree and read `git diff`.
⚠️ **`--init` silently overwrites an existing `.oxlintrc.json`** — no prompt, no backup, exit 0
(verified: a hand-written config was replaced wholesale).

## Suppressing findings

```js
// oxlint-disable-next-line no-dupe-keys     ← also: // eslint-disable-next-line (honored by default)
const a = { x: 1, x: 2 };
const b = { y: 1, y: 2 }; // oxlint-disable-line no-dupe-keys
/* oxlint-disable no-debugger */ ... /* oxlint-enable no-debugger */
```

Omit the rule name to suppress everything on the line; `options.respectEslintDisableDirectives`
(default `true`) governs the `eslint-*` spellings.

**`--report-unused-disable-directives` flags dead directives — it is NOT a safety net.** Verified:
it reports a directive that suppresses *nothing*, and stays silent about one actively hiding a real
`no-dupe-keys` violation; a blanket `// oxlint-disable-next-line` over a genuine bug is invisible
to it. It defaults to **`warn`, so it exits 0** — use
`--report-unused-disable-directives-severity deny` in CI.

## Type-aware rules

**15 of the 111 default rules are type-aware and silently do nothing** unless you enable them —
including `no-floating-promises`, `await-thenable` and `unbound-method`. They still appear in
`--print-config`, which makes the gap easy to miss.

```bash
npm i -D oxlint-tsgolint            # a SEPARATE package; --type-aware fails without it
oxlint --type-aware                 # or "options": { "typeAware": true }
oxlint --type-aware --type-check    # + TS compiler diagnostics (experimental)
```

`--type-check` without `--type-aware` is rejected (exit 1). All 59 are `typescript/*`.

## Coming from ESLint

| Concept | ESLint v8 | oxlint |
|---|---|---|
| Config file | `.eslintrc.json` | `.oxlintrc.json` (same shape, + `categories`) |
| Flat config | `eslint.config.js` | **not supported** — `oxlint.config.ts` is a different thing |
| Enable a plugin | `plugins` + `extends` a preset | `plugins` (**replaces**, no presets) |
| Bulk enable | `extends: ["eslint:recommended"]` | `categories: { "correctness": "error" }` |
| Suppress | `// eslint-disable-next-line` | same, **or** `// oxlint-disable-next-line` |
| Third-party plugins | npm packages | `jsPlugins` (**alpha, not SemVer**) — else keep ESLint |
| Fail CI | non-zero by default | **must** add `-D correctness` / `--deny-warnings` |

Anything outside oxlint's 870 rules (and outside `jsPlugins`) has no equivalent, so most teams run
oxlint first and keep ESLint for the remainder. Upstream ships a migration skill
(`npx skills add https://github.com/oxc-project/oxc --skill migrate-oxlint`). Phased plan:
[references/eslint-migration.md](references/eslint-migration.md).

## Troubleshooting

- **"I enabled a rule and nothing happens."** Its plugin is almost certainly missing from your
  `plugins` array — naming a rule sets severity, it does not enable the plugin, and the mismatch is
  silent. Run the `comm` check above; if the rule is absent from `--print-config`, add its plugin.
  (A merely *misspelled* rule name would give a hard config error instead.)
- **"Rules stopped firing after I edited the config."** Same cause: `plugins` replaced the base
  set. Diff `oxlint --print-config` before and after.
- **"CI is green but the code has problems."** Default severity is `warn` and warnings exit 0. Add
  `-D correctness` or `--deny-warnings`.
- **"My root config is ignored in a subdirectory."** A nested `.oxlintrc.json` replaced it. Add
  `extends`, or pass `--disable-nested-config`.
- **"`oxlint --rules` prints nothing."** Agent/CI environment using the `agent` format — add
  `--format json`.
- **"`no-floating-promises` never fires."** Type-aware: install `oxlint-tsgolint`, pass `--type-aware`.
- **"Exit 1 but no diagnostics."** A config error (unknown rule names are hard errors) or no files
  matched. Read stderr; `--no-error-on-unmatched-pattern` fixes the latter.
- **"It is linting `node_modules`."** Not special-cased — add it to `.gitignore`/`ignorePatterns`.
- **"`eqeqeq`/`no-console` do not fire."** They are `pedantic`/`restriction`, not `correctness`.

## References

- [references/configuration.md](references/configuration.md) — all 12 keys, `options`, `overrides`
  vs nested configs, `extends`, discovery, ignore semantics, `settings`, `jsPlugins`.
- [references/rules-and-categories.md](references/rules-and-categories.md) — plugins × categories,
  catalog queries, fix-safety taxonomy, type-aware rules, per-plugin counts.
- [references/eslint-migration.md](references/eslint-migration.md) — mapping tables, aliases, what
  is unsupported, phased migration and CI recipes.
- [references/cli-reference.md](references/cli-reference.md) — every flag verified against `--help`
  on 1.79.0, output formats, exit codes, agent detection.

**Resources** — `oxlint --help` · [docs](https://oxc.rs/docs/guide/usage/linter) ·
[repo](https://github.com/oxc-project/oxc) · [playground](https://playground.oxc.rs)
