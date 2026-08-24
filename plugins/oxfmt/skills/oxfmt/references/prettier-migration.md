# Migrating to oxfmt from Prettier or Biome

Documented against **oxfmt 0.64.0**. Every console transcript below was produced by running the
tool.

## Contents

- [The two-minute version](#the-two-minute-version)
- [What `--migrate=prettier` actually does](#what---migrateprettier-actually-does)
- [What `--migrate=biome` does](#what---migratebiome-does)
- [Behavioural differences the migrator cannot fix](#behavioural-differences-the-migrator-cannot-fix)
- [Prettier option map](#prettier-option-map)
- [Replacing Prettier plugins](#replacing-prettier-plugins)
- [Language coverage compared](#language-coverage-compared)
- [A safe adoption sequence](#a-safe-adoption-sequence)
- [Keeping Prettier for the gaps](#keeping-prettier-for-the-gaps)

## The two-minute version

```bash
npx --yes oxfmt@0.64.0 --migrate=prettier   # writes .oxfmtrc.json, leaves .prettierrc alone
npx --yes oxfmt@0.64.0 --check .            # preview: what would change, writes nothing
npx --yes oxfmt@0.64.0 .                    # apply (this WRITES)
```

The middle step is not optional. `oxfmt` with no output flag writes in place, so `--check` (or
`--list-different`) is your only look-before-you-leap.

## What `--migrate=prettier` actually does

It reads `.prettierrc` (and `.prettierignore`), writes `.oxfmtrc.json`, and narrates every decision:

```console
$ oxfmt --migrate=prettier
Found Prettier configuration at: /path/.prettierrc
  - "endOfLine: auto" is not supported, skipping...
  - plugins: "prettier-plugin-organize-imports" is not supported, skipping...
Migrated prettier-plugin-tailwindcss options to sortTailwindcss
Migrated ignore patterns from `.prettierignore`
Created `.oxfmtrc.json`.
```

Four properties worth knowing:

1. **It is non-destructive.** Your `.prettierrc` and `.prettierignore` stay on disk. Delete them
   yourself once you are satisfied.
2. **It refuses to clobber.** If `.oxfmtrc.json` exists it stops with exit `1`:
   `Oxfmt configuration file already exists.`
3. **It pins `printWidth` even when Prettier did not set it** — this is the migrator protecting you
   from the 80 → 100 default change:

   ```console
   $ cat .prettierrc
   { "singleQuote": true }
   $ oxfmt --migrate=prettier
     - "printWidth" is not set in Prettier config, defaulting to 80 (Oxfmt default: 100)
   $ cat .oxfmtrc.json
   { "singleQuote": true, "printWidth": 80, "sortPackageJson": false, "ignorePatterns": [] }
   ```

4. **It writes `"sortPackageJson": false`.** oxfmt sorts `package.json` by default; Prettier does
   not. The migrator disables it so migration does not reorder your manifest as a side effect. If
   you *want* the sorting, delete that line afterwards and review the diff separately.

Unsupported keys are reported, never silently dropped — read the output.

## What `--migrate=biome` does

```console
$ oxfmt --migrate=biome
Found Biome configuration at: /path/biome.json
Created `.oxfmtrc.json`.
```

From `{ formatter: { indentStyle: "space", indentWidth: 4, lineWidth: 120 },
javascript: { formatter: { quoteStyle: "single", semicolons: "asNeeded" } } }` it produced a fully
explicit config:

```json
{
  "useTabs": false, "tabWidth": 4, "printWidth": 120,
  "singleQuote": true, "jsxSingleQuote": false, "quoteProps": "as-needed",
  "trailingComma": "all", "semi": false, "arrowParens": "always",
  "bracketSameLine": false, "bracketSpacing": true, "ignorePatterns": []
}
```

Biome key mapping: `lineWidth`→`printWidth`, `indentWidth`→`tabWidth`, `indentStyle`→`useTabs`,
`quoteStyle`→`singleQuote`, `semicolons: "asNeeded"`→`semi: false`. Note it did **not** add
`sortPackageJson: false` here — check your `package.json` diff separately after a Biome migration.

## Behavioural differences the migrator cannot fix

| Difference | Effect | What to do |
|---|---|---|
| **Bare command writes** | `oxfmt src/` rewrites; `prettier src/` printed to stdout | Retrain the habit; use `--check` / `--list-different` / `--stdin-filepath` |
| **`printWidth` 100 vs 80** | Whole-repo reflow | Migrator pins 80. Change it deliberately, in its own commit |
| **`sortPackageJson` on** | `package.json` keys reordered | Migrator sets `false` for Prettier; verify after Biome |
| **`endOfLine: "auto"` unsupported** | Key skipped | Choose `"lf"` (default) or `"crlf"` explicitly |
| **`.editorconfig` is read** | Silently overrides defaults | Audit for a stray `.editorconfig` |
| **Nested configs cascade** | `sub/.oxfmtrc.json` wins under `sub/` | `--disable-nested-config` for one global style |
| **`.gitignore` only scopes discovery** | Named gitignored files still get formatted | Put true exclusions in `.prettierignore` / `ignorePatterns` |
| **Formatting output is not byte-identical** | Even at matching options, oxfmt is a reimplementation | Expect a review diff; land it as one "reformat" commit |

That last row is the one to communicate to your team. oxfmt tracks Prettier's style closely and runs
a conformance suite against it, but it is a separate implementation — some constructs print
differently. Do not promise a no-op diff.

## Prettier option map

Options that carry over with the same name and same meaning: `printWidth` (**different default**),
`tabWidth`, `useTabs`, `semi`, `singleQuote`, `jsxSingleQuote`, `quoteProps`, `trailingComma`,
`bracketSpacing`, `bracketSameLine`, `arrowParens`, `objectWrap`, `proseWrap`,
`htmlWhitespaceSensitivity`, `vueIndentScriptAndStyle`, `singleAttributePerLine`,
`embeddedLanguageFormatting`, `endOfLine` (**no `"auto"`**), `experimentalOperatorPosition`,
`overrides`.

Renamed or oxfmt-only: `ignorePatterns` (Prettier used `.prettierignore` only), `insertFinalNewline`
(Prettier always inserts), `sortImports`, `sortPackageJson`, `sortTailwindcss`, `jsdoc`, `svelte`.

Prettier options with **no oxfmt equivalent**: `parser` (inferred from the path, or set with
`--stdin-filepath`), `filepath`, `rangeStart` / `rangeEnd`, `requirePragma` / `insertPragma`,
`plugins` (oxfmt has no plugin system — the built-in sort options replace the common ones).

## Replacing Prettier plugins

| Prettier plugin | oxfmt equivalent | Auto-migrated? |
|---|---|---|
| `prettier-plugin-tailwindcss` | `sortTailwindcss` | **yes** — options converted |
| `prettier-plugin-organize-imports` | `sortImports` | **no** — reported as unsupported; enable it yourself |
| `prettier-plugin-sort-packagejson` / `-packagejson` | `sortPackageJson` | no — and the key order is deliberately **not** compatible |
| `prettier-plugin-svelte` | `svelte: true` + install `svelte` yourself | no |
| `prettier-plugin-jsdoc` | `jsdoc` | no |
| anything else | none | oxfmt has no plugin API |

Turning on `sortImports` after migrating:

```jsonc
{
  "sortImports": true,
  // or tune it:
  // "sortImports": { "internalPattern": ["~/", "@/"], "newlinesBetween": true }
}
```

Land that as its own commit — it moves lines across the whole codebase and side-effect imports are
deliberately left alone (`sortSideEffects: false`), so a reviewer needs to see it in isolation.

## Language coverage compared

oxfmt formats natively in Rust: **JS/TS/JSX/TSX**, **JSON / JSONC / JSON5**, **CSS / SCSS / Less**,
**YAML**, **TOML**, **GraphQL**. It delegates to a bundled Prettier for **Markdown / MDX**, **HTML**,
**Angular templates**, **Vue**, **Handlebars**, **MJML**. **Svelte** needs opt-in config plus your
own `svelte` dependency.

Two things Prettier handles that oxfmt does not: TOML is *not* a Prettier language at all (oxfmt
adds it), and Prettier's wider plugin ecosystem (PHP, Java, XML, Ruby…) has no oxfmt counterpart.

## A safe adoption sequence

```bash
git status --porcelain          # must be clean; oxfmt writes in place
npx --yes oxfmt@0.64.0 --migrate=prettier
cat .oxfmtrc.json               # read every line the migrator wrote

npx --yes oxfmt@0.64.0 --check .          # exit 1 = work to do, 2 = invocation broken
npx --yes oxfmt@0.64.0 --list-different . | wc -l    # blast radius

npx --yes oxfmt@0.64.0 src/     # apply to one directory first
git diff                        # review the reimplementation differences

npx --yes oxfmt@0.64.0 .        # then the rest
git commit -am "style: reformat with oxfmt 0.64.0"

# keep git blame useful across the reformat commit
git log -1 --format=%H >> .git-blame-ignore-revs
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

There is no `--diff` flag, so `git diff` on a clean tree *is* the review step — which is why the
commit/stash in step one is not optional.

Then, in **separate** commits: raise `printWidth` to 100 if you want oxfmt's default; enable
`sortImports`; enable `sortPackageJson`.

Finally pin it and remove Prettier:

```jsonc
{
  "devDependencies": { "oxfmt": "0.64.0" },
  "scripts": { "format": "oxfmt .", "format:check": "oxfmt --check ." }
}
```

Pin the **exact** version, no `^`. oxfmt ships a minor roughly weekly and, being 0.x, minors have
carried breaking output changes (`0.57.0`, `0.62.0`). An unpinned range means a dependency update
can reformat your repo.

## Keeping Prettier for the gaps

The two coexist — oxfmt reads `.prettierignore` by default, so shared exclusions keep working. Route
files by extension and let each tool own its set:

```jsonc
{
  "scripts": {
    "format": "oxfmt . && prettier --write '**/*.{php,xml}'",
    "format:check": "oxfmt --check . && prettier --check '**/*.{php,xml}'"
  }
}
```

Make sure the two never claim the same extension, or they will fight on every run. Add anything
Prettier owns to oxfmt's `ignorePatterns` to be certain.
