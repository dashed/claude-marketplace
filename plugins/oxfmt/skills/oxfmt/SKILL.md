---
name: oxfmt
description: "oxfmt — the fast Rust code formatter from oxc (the Oxidation Compiler), a Prettier-compatible alternative that formats JS/TS/JSX plus JSON, CSS/SCSS/Less, YAML, TOML, GraphQL, Markdown, HTML and Vue. Use when formatting or checking code with oxfmt, configuring `.oxfmtrc.json` / `.oxfmtrc.jsonc`, migrating a project off Prettier or Biome (`--migrate`), enabling its built-in `sortImports` / `sortPackageJson` / `sortTailwindcss` / `jsdoc` features that Prettier needs plugins for, or wiring `oxfmt --check` into CI. Triggers on mentions of oxfmt, `.oxfmtrc`, `npx oxfmt`, or the oxc formatter. Read it before running oxfmt at all: bare `oxfmt` REWRITES FILES IN PLACE, the opposite of `prettier`, which prints to stdout. This is oxfmt, the formatter — NOT oxlint (its sibling linter, a separate skill here), NOT Prettier or Biome themselves, and NOT `ruff format` (the Python formatter, also a separate skill here)."
---

# oxfmt — JS/TS (and friends) Formatter

## ⚠️ Read this first: bare `oxfmt` rewrites your files

`oxfmt --help` says `--write   Format and write files in place (default)`. That default is real and
**verified**: running `oxfmt src/` with no flags edits your tree immediately.

```console
$ printf 'const x   =    {a:1,b:2}\n' > a.js
$ oxfmt a.js              # no --write. Looks like a dry run. It is NOT.
Finished in 5ms on 1 files using 10 threads.
$ cat a.js
const x = { a: 1, b: 2 };   # file already overwritten
```

**This is inverted from Prettier.** `prettier file.js` prints to stdout and changes nothing;
`prettier --write` is the destructive one. In oxfmt, `--write` is the *default* and there is no flag
that turns it off — you pick a different **mode** instead:

| To do this | Prettier | oxfmt | Writes files? |
|---|---|---|---|
| See the formatted result | `prettier f.js` | `oxfmt --stdin-filepath=f.js < f.js` | **no** |
| List files that would change | `prettier -l f.js` | `oxfmt --list-different f.js` | **no** |
| CI gate | `prettier --check f.js` | `oxfmt --check f.js` | **no** |
| Rewrite in place | `prettier --write f.js` | `oxfmt f.js` | **yes** |

All three safe modes were confirmed to leave the input byte-identical. Use `--check` (human-readable
+ statistics) or `--list-different` (bare paths, script-friendly) to preview a whole tree, and
`--stdin-filepath` when you want the actual formatted text on stdout.

**There is no `--diff` flag** — don't go looking for one. `ruff format --diff` and `prettier`'s
stdout default have no direct equivalent here:

```console
$ oxfmt --diff messy.js
Error: `--diff` is not expected in this context
```

`--check` and `--list-different` tell you *which* files would change but never *what* would change.
**`--stdin-filepath` is the one path that shows you the content**, and it writes the result to stdout
with an empty stderr, so it pipes cleanly into `diff` for a true dry run:

```console
$ oxfmt --stdin-filepath=messy.js < messy.js | diff messy.js -
1,2c1,2
< const x   =    {a:1,   b:2}
< let y = "double"
---
> const x = { a: 1, b: 2 };
> let y = "double";
```

Verified: `messy.js` is byte-identical afterwards. That is one file at a time — for a whole tree the
review loop is `--list-different` for scope, then run oxfmt on a clean tree and read `git diff`.

`--write` is **mutually exclusive** with the preview modes — `oxfmt --check --write f.js` errors out
rather than guessing:

```console
$ oxfmt --check --write w.js
Error: `--write` cannot be used at the same time as `--check`
```

**Before the first run on a real repo: commit or stash.** A clean git tree turns an unwanted
reformat into `git checkout -- .`, and makes `git diff` your after-the-fact review of the edits.
Land a repo-wide reformat as **one isolated commit** and record it so `git blame` stays useful:

```bash
git log -1 --format=%H >> .git-blame-ignore-revs
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

> ### ⚠️ And second: oxfmt is young and moves weekly
>
> This skill documents **oxfmt 0.64.0** (released 2026-08-18). Confirm your build — note the output
> prints only a bare version, not the tool name:
>
> ```console
> $ npx --yes oxfmt@latest --version
> Version: 0.64.0
> ```
>
> oxfmt shipped `0.1.0` on 2025-09-12 and reached `0.64.0` in ~11 months: **58 releases, a minor
> bump almost every week.** It is 0.x, so under semver a *minor* may break you — and 7 of those
> releases did carry `BREAKING CHANGES`, including `0.57.0` and `0.62.0` within the last two months
> (both changed which engine formats CSS/GraphQL/YAML, i.e. they changed output). Its sibling
> **oxlint is already 1.79.0**; oxfmt is nowhere near that maturity.
>
> **Consequence: pin an exact version** (`"oxfmt": "0.64.0"`, no `^`) anywhere reproducible output
> matters, and expect a re-format diff when you bump. Because *everything* here is that new, this
> skill does not tag individual features with version numbers — verify anything surprising against
> `oxfmt --help` and the schema on your own build.

## Overview

oxfmt is the formatter of the [oxc](https://github.com/oxc-project/oxc) toolchain — a hybrid
Rust + Node CLI where most languages are formatted by native Rust crates and a few are delegated to
a bundled Prettier. Option names are deliberately Prettier-compatible, so **the differences are the
whole story**.

## The differences that will change your diff

| | Prettier | oxfmt | Why it matters |
|---|---|---|---|
| **Default action** | print to stdout | **write in place** | see the warning above |
| **`printWidth`** | `80` | **`100`** | reflows *every* file in the repo |
| **`sortPackageJson`** | plugin-only | **`true` by default** | reorders `package.json` keys on first run |
| `sortImports` | needs `prettier-plugin-organize-imports` | built in (opt-in) | no plugin install |
| `sortTailwindcss` | needs `prettier-plugin-tailwindcss` | built in (opt-in) | no plugin install |
| `jsdoc` | not available | built in (opt-in) | rewrites comment contents |
| `endOfLine: "auto"` | supported | **not supported** | migration drops it |
| Config file | `.prettierrc` | `.oxfmtrc.json` / `.jsonc` | `.jsonc` allows comments |

The `printWidth` gap surprises people. Verified on an 83-character line: oxfmt keeps it on one line
(width 100), Prettier wraps it into five (width 80) — that is a diff on nearly every file you own.

`sortPackageJson` is on by default and is **semantic**, not cosmetic. Verified: it reordered
`{version, name, scripts, license}` into oxfmt's canonical `{name, version, license, scripts}`.
`scripts` *contents* keep their order unless you set `sortPackageJson: { "sortScripts": true }`. The
ordering is **not** compatible with `prettier-plugin-sort-packagejson`, and `--migrate=prettier`
writes `"sortPackageJson": false` for you.

## Everyday commands

| Task | Command |
|------|---------|
| Format the current directory **(writes!)** | `oxfmt` |
| Format specific paths **(writes!)** | `oxfmt src/ test/` |
| Preview: which files would change | `oxfmt --list-different .` |
| Preview: CI gate + statistics | `oxfmt --check .` |
| Preview: see the formatted text | `oxfmt --stdin-filepath=f.ts < f.ts` |
| Create a config | `oxfmt --init` |
| Migrate off Prettier / Biome | `oxfmt --migrate=prettier` / `--migrate=biome` |
| Use a specific config | `oxfmt -c path/to/.oxfmtrc.json .` |
| Exclude a glob | `oxfmt 'src/**/*.js' '!src/skip.js'` (quote them) |
| Single-threaded (debugging) | `oxfmt --threads=1 .` |
| Language server | `oxfmt --lsp` |

**Exit codes** (verified): `0` clean · `1` formatting differences found (`--check`,
`--list-different`) · `2` **operational failure** — no files matched the pattern, a parse error, or
bad flags. Never treat `2` as "code needs formatting": in CI it means your invocation or your syntax
is broken. `--no-error-on-unmatched-pattern` turns the "no files matched" case back into `0`.

A file that fails to parse is **left untouched**, and the run exits `2`.

## What oxfmt actually formats

Crate existence in the oxc repo is not shipped support. Verified against `oxfmt 0.64.0`:

**Native Rust (always available, fast):**

| Language | Extensions |
|---|---|
| JS / TS | `.js .mjs .cjs .jsx .ts .mts .cts .tsx .d.ts` |
| JSON family | `.json .jsonc .json5`, `package.json` (sorted), `composer.json`, many editor `.sublime-*` |
| CSS family | `.css .scss .less .pcss .postcss .wxss` |
| YAML | `.yaml .yml`, `.prettierrc`, `.clang-format`, `CITATION.cff` |
| TOML | `.toml`, `Pipfile` (via taplo) |
| GraphQL | `.graphql .gql .graphqls` |

**Delegated to bundled Prettier** (Node build only): Markdown `.md .mdx`, HTML `.html .htm`,
Angular `*.component.html`, **Vue** `.vue`, Handlebars `.hbs`, MJML.

**Svelte is opt-in and needs your own dependency.** `.svelte` is recognized but skipped unless you
set `svelte: true` (or `{}`) in config *and* install the `svelte` package yourself — oxfmt does not
bundle it. Without that, `oxfmt file.svelte` exits `2` with "Expected at least one target file".

**Never formatted, even when named explicitly:** lock files are hard-excluded —
`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`, `deno.lock`, `Cargo.lock`,
`uv.lock`, `poetry.lock`, `composer.lock`, `flake.lock` and friends. Verified: naming one directly
exits `2` rather than reformatting it.

## Configuration

`.oxfmtrc.json` / `.oxfmtrc.jsonc` (comments allowed — oxc dogfoods a `.jsonc` on itself) or
`.ts/.mts/.cts/.js/.mjs/.cjs`. `oxfmt --init` writes a minimal `{ "ignorePatterns": [] }`, **not** a
dump of the defaults.

```jsonc
{
  "$schema": "./node_modules/oxfmt/configuration_schema.json",
  "printWidth": 100,          // oxfmt default; Prettier's is 80
  "singleQuote": false,
  "sortImports": true,        // opt-in; Prettier needs a plugin
  "ignorePatterns": ["**/dist/**", "!keep/this/**"],
  "overrides": [
    { "files": ["*.test.ts"], "options": { "printWidth": 120 } }
  ]
}
```

There are exactly **27** top-level keys — full table with defaults and applicable languages in
[references/configuration.md](references/configuration.md).

**Discovery is "nearest config wins", and it cascades into subdirectories by default** — a
`sub/.oxfmtrc.json` overrides the root one for files under `sub/`. `--disable-nested-config` makes
the root config authoritative; `-c PATH` forces one file for everything. All three verified.

**`.editorconfig` is read and overrides oxfmt's defaults** — verified: `indent_style = tab` plus
`max_line_length = 40`, with no oxfmt config present, produced tab-indented output wrapped at 40. It
maps onto `printWidth`, `tabWidth`, `useTabs`, `endOfLine`, `insertFinalNewline` and `singleQuote`.
If output disagrees with your `.oxfmtrc.json`, look for a stray `.editorconfig` first.

**Ignore files are two-tier**, and the distinction is observable:

- `.prettierignore`, `--ignore-path`, `ignorePatterns` and `!` globs are **formatter-owned** — they
  exclude a file *even when you name it explicitly*.
- `.gitignore` only **scopes directory discovery** — a gitignored file that you name on the command
  line **is still formatted**.

`node_modules/` is skipped unless you pass `--with-node-modules`.

## Sorting and JSDoc (the real differentiators)

All three are separate from formatting and each is `true`-or-object:

- **`sortImports`** (default off) — groups and sorts imports, algorithm modelled on
  `eslint-plugin-perfectionist/sort-imports`. Inserts blank lines between groups
  (`newlinesBetween: true`). Side-effect imports are **not** reordered by default
  (`sortSideEffects: false`) — reordering them can change runtime behaviour.
- **`sortPackageJson`** (default **on**) — see above.
- **`sortTailwindcss`** (default off) — same algorithm as `prettier-plugin-tailwindcss`, options
  drop the `tailwind` prefix (`config`, not `tailwindConfig`). Add `functions: ["clsx","cn","cva"]`
  and `attributes` for custom call sites; regex patterns are not yet supported.
- **`jsdoc`** (default off) — rewrites comment *contents*: `@arg`→`@param`, `@return`→`@returns`,
  descriptions capitalized, long lines wrapped. Prettier has no equivalent. Verified:

  ```diff
  - * @arg {string} a - the thing
  + * @param {string} a - The thing
  ```

## Migrating from Prettier or Biome

```bash
oxfmt --migrate=prettier    # reads .prettierrc + .prettierignore
oxfmt --migrate=biome       # reads biome.json
```

It is careful and non-destructive: it **refuses to overwrite** an existing `.oxfmtrc.json` (exit
`1`), leaves your `.prettierrc` in place, and reports each unsupported key rather than dropping it
silently. Two things it does for you, both observed in its output:

```console
$ oxfmt --migrate=prettier
  - "printWidth" is not set in Prettier config, defaulting to 80 (Oxfmt default: 100)
  - plugins: "prettier-plugin-organize-imports" is not supported, skipping...
Migrated prettier-plugin-tailwindcss options to sortTailwindcss
```

It **pins `printWidth: 80` even when your Prettier config never set it**, and writes
`"sortPackageJson": false` — so migration preserves your line width and leaves `package.json` alone.
`prettier-plugin-organize-imports` is *not* converted; enable `sortImports` yourself, in its own
commit. Full option map: [references/prettier-migration.md](references/prettier-migration.md).

## Troubleshooting

| Symptom | Cause |
|---|---|
| "It reformatted my whole repo" | Bare `oxfmt` writes. Also `printWidth` 100 vs 80. `git checkout -- .` |
| `package.json` keys moved | `sortPackageJson` defaults to `true`. Set it `false`. |
| Exit `2` in CI | Not a format failure: no files matched, parse error, or bad flags. |
| `.svelte` files skipped | Needs `svelte: true` in config **and** the `svelte` package installed. |
| Output ignores my config | An `.editorconfig`, or a nested `.oxfmtrc.json` in a subdirectory. |
| Gitignored file still formatted | Expected — `.gitignore` scopes discovery only. Use `.prettierignore`. |
| `--write cannot be used with --check` | Pick one mode; they are mutually exclusive. |

## References

- [references/cli-reference.md](references/cli-reference.md) — all 15 flags, exit codes, ignore model
- [references/configuration.md](references/configuration.md) — all 27 config keys with defaults
- [references/prettier-migration.md](references/prettier-migration.md) — option map, gotchas, CI setup

Upstream: [oxc repo](https://github.com/oxc-project/oxc) ·
[formatter docs](https://oxc.rs/docs/guide/usage/formatter)
