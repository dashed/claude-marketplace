# oxfmt Configuration Reference

Every key and default below is taken from `npm/oxfmt/configuration_schema.json` in the oxc repo at
**oxfmt 0.64.0**. The schema defines **exactly 27 top-level keys** — the complete set is listed here.
Anything not on this list is not a valid oxfmt option.

## Contents

- [Config files and discovery](#config-files-and-discovery)
- [The 27 keys at a glance](#the-27-keys-at-a-glance)
- [Layout options](#layout-options)
- [JS/TS syntax options](#jsts-syntax-options)
- [Markup and prose options](#markup-and-prose-options)
- [File selection](#file-selection)
- [overrides](#overrides)
- [sortImports](#sortimports)
- [sortPackageJson](#sortpackagejson)
- [sortTailwindcss](#sorttailwindcss)
- [jsdoc](#jsdoc)
- [svelte](#svelte)
- [.editorconfig interaction](#editorconfig-interaction)

## Config files and discovery

Accepted names: `.oxfmtrc.json`, `.oxfmtrc.jsonc`, and `.ts` / `.mts` / `.cts` / `.js` / `.mjs` /
`.cjs` variants. The `.jsonc` form allows comments and trailing commas — oxc itself uses a root
`oxfmtrc.jsonc`.

`oxfmt --init` creates a deliberately minimal file:

```json
{
  "ignorePatterns": []
}
```

**Discovery is nearest-wins and cascades into subdirectories.** A `sub/.oxfmtrc.json` takes priority
over the repository root for files under `sub/`. Use `--disable-nested-config` to make the root
authoritative, or `-c PATH` to force one file.

Add `$schema` for editor completion:

```jsonc
{ "$schema": "./node_modules/oxfmt/configuration_schema.json" }
```

## The 27 keys at a glance

| Key | Default | Applies to |
|---|---|---|
| `arrowParens` | `"always"` | JS, JSX, TS, TSX |
| `bracketSameLine` | `false` | JSX, TSX, HTML, Angular, Vue, MJML, Svelte |
| `bracketSpacing` | `true` | JS, JSX, TS, TSX, JSON, JSONC, JSON5, GraphQL, YAML |
| `embeddedLanguageFormatting` | `"auto"` | JS, JSX, TS, TSX, HTML, Vue, Angular, Svelte, Markdown, MDX |
| `endOfLine` | `"lf"` | All |
| `experimentalOperatorPosition` | `"end"` | JS, JSX, TS, TSX |
| `htmlWhitespaceSensitivity` | `"css"` | HTML, Angular, Vue, Handlebars, Svelte |
| `ignorePatterns` | `[]` | All |
| `insertFinalNewline` | `true` | All |
| `jsdoc` | **disabled** | JS, JSX, TS, TSX |
| `jsxSingleQuote` | `false` | JSX, TSX |
| `objectWrap` | `"preserve"` | JS, JSX, TS, TSX, JSON, JSONC, JSON5 |
| `overrides` | `[]` | All |
| `printWidth` | **`100`** | All |
| `proseWrap` | `"preserve"` | Markdown, MDX, YAML |
| `quoteProps` | `"as-needed"` | JS, JSX, TS, TSX |
| `semi` | `true` | JS, JSX, TS, TSX |
| `singleAttributePerLine` | `false` | JSX, TSX, HTML, Angular, Vue, MJML, Svelte |
| `singleQuote` | `false` | JS, JSX, TS, TSX, CSS, Less, SCSS, Markdown, MDX, YAML, Handlebars, Svelte |
| `sortImports` | **disabled** | JS, JSX, TS, TSX |
| `sortPackageJson` | **`true`** | `package.json` only |
| `sortTailwindcss` | **disabled** | JS, JSX, TS, TSX, HTML, Vue, Angular, Handlebars, CSS, SCSS, Less, Svelte |
| `svelte` | **disabled** | Svelte |
| `tabWidth` | `2` | All |
| `trailingComma` | `"all"` | JS, JSX, TS, TSX, JSONC, JSON5, TOML, CSS, Less, SCSS, YAML |
| `useTabs` | `false` | All |
| `vueIndentScriptAndStyle` | `false` | Vue |

Bolded defaults are where oxfmt differs from Prettier in a way that changes output.

## Layout options

| Key | Values | Default | Note |
|---|---|---|---|
| `printWidth` | integer | `100` | **Prettier's default is 80.** The single largest source of diff on adoption. |
| `tabWidth` | integer | `2` | |
| `useTabs` | boolean | `false` | |
| `endOfLine` | `"lf"`, `"crlf"`, `"cr"` | `"lf"` | **`"auto"` is not supported** — unlike Prettier. `--migrate` skips it. |
| `insertFinalNewline` | boolean | `true` | Not a Prettier option; Prettier always inserts one. |

## JS/TS syntax options

| Key | Values | Default |
|---|---|---|
| `semi` | boolean | `true` |
| `singleQuote` | boolean | `false` |
| `jsxSingleQuote` | boolean | `false` |
| `quoteProps` | `"as-needed"`, `"consistent"`, `"preserve"` | `"as-needed"` |
| `trailingComma` | `"all"`, `"es5"`, `"none"` | `"all"` |
| `bracketSpacing` | boolean | `true` |
| `bracketSameLine` | boolean | `false` |
| `arrowParens` | `"always"`, `"avoid"` | `"always"` |
| `objectWrap` | `"preserve"`, `"collapse"` | `"preserve"` |
| `singleAttributePerLine` | boolean | `false` |
| `experimentalOperatorPosition` | `"end"`, `"start"` | `"end"` |

`objectWrap: "preserve"` keeps an object multi-line when the source has a newline before the first
property — an author-controlled readability hint. `"collapse"` ignores it and packs whatever fits.

`experimentalOperatorPosition: "start"` puts operators at the beginning of wrapped lines. It is
marked *experimental*; oxc itself uses it in its own `oxfmtrc.jsonc`. It landed in **0.64.0**, so it
is one of the newest surfaces here.

## Markup and prose options

| Key | Values | Default | Note |
|---|---|---|---|
| `proseWrap` | `"preserve"`, `"always"`, `"never"` | `"preserve"` | Markdown/MDX/YAML. `"preserve"` protects linebreak-sensitive renderers (GitHub comments). |
| `htmlWhitespaceSensitivity` | `"css"`, `"ignore"`, `"strict"` | `"css"` | |
| `vueIndentScriptAndStyle` | boolean | `false` | |
| `embeddedLanguageFormatting` | `"auto"`, `"off"` | `"auto"` | Controls CSS-in-JS, JS-in-Vue, front matter, JSDoc fenced blocks. `"off"` leaves every embedded region verbatim. |

## File selection

**`ignorePatterns`** — glob array, default `[]`. Formatter-owned, so it excludes a file even when
that file is named explicitly on the command line. Supports `!` negation, and patterns are relative
to the config file's directory:

```jsonc
{
  "ignorePatterns": [
    "**/dist/**",
    "**/fixtures/**",
    "!apps/keep/fixtures/**",   // re-include
    "**/CHANGELOG.md"
  ]
}
```

## overrides

Array of `{ files, excludeFiles?, options }`. `files` is required. **Later entries win** when
several match the same file.

```jsonc
{
  "overrides": [
    { "files": ["*.md"], "options": { "proseWrap": "always", "printWidth": 80 } },
    {
      "files": ["src/**/*.ts"],
      "excludeFiles": ["src/generated/**"],
      "options": { "printWidth": 120 }
    },
    { "files": ["*.svelte"], "options": { "svelte": false } }
  ]
}
```

`options` accepts the same keys as the top level.

## sortImports

Default **disabled**. `true` enables defaults; an object customizes. Algorithm modelled on
[`eslint-plugin-perfectionist/sort-imports`](https://perfectionist.dev/rules/sort-imports).

| Field | Default | Meaning |
|---|---|---|
| `groups` | predefined | Ordered list of import groups; order here is the output order. |
| `customGroups` | `[]` | Ordered, higher priority than predefined groups; first match wins. |
| `internalPattern` | `["~/", "@/", "#"]` | Prefixes treated as internal, not third-party. |
| `newlinesBetween` | `true` | Blank line between groups. |
| `order` | `"asc"` | `"asc"` or `"desc"`. |
| `ignoreCase` | `true` | Case-insensitive comparison. |
| `sortSideEffects` | `false` | **Off for safety** — reordering `import "./polyfill"` can change runtime behaviour. |
| `partitionByComment` | `false` | Treat comments as hard partitions that sorting will not cross. |
| `partitionByNewline` | `false` | Treat blank lines as hard partitions. |

Observed with `{"sortImports": true}`:

```diff
-import z from "zzz";
-import a from "aaa";
-import { b } from "./local";
-import React from "react";
+import a from "aaa";
+import React from "react";
+import z from "zzz";
+
+import { b } from "./local";
```

Note both effects: alphabetical order *and* a group break before the relative import.

## sortPackageJson

Default **`true`** — this runs whether or not you configure anything, and it is the option most
likely to surprise a Prettier user. `false` disables; an object customizes.

| Field | Default | Meaning |
|---|---|---|
| `sortScripts` | `false` | Also alphabetize the `scripts` object. |

Key order is oxfmt's own canonical order and is **explicitly not compatible** with
`prettier-plugin-sort-packagejson`. `--migrate=prettier` therefore writes `"sortPackageJson": false`
into the generated config so migration does not silently churn your manifest.

## sortTailwindcss

Default **disabled**. Same algorithm as `prettier-plugin-tailwindcss`; option names drop the
`tailwind` prefix.

| Field | Default | Meaning |
|---|---|---|
| `config` | auto-find `tailwind.config.js` | Tailwind **v3** config path, resolved relative to the oxfmt config file. |
| `stylesheet` | installed Tailwind `theme.css` | Tailwind **v4** stylesheet path. |
| `functions` | `[]` | Extra function names whose args get sorted, e.g. `["clsx","cn","cva","tw"]`. Exact match only. |
| `attributes` | `[]` | Extra attributes beyond `class`/`className`, e.g. `["myClassProp",":class"]`. Exact match only. |
| `preserveDuplicates` | `false` | Keep duplicate classes. |
| `preserveWhitespace` | `false` | Keep whitespace around classes. |

Regex patterns are **not yet supported** for `functions` or `attributes`.

## jsdoc

Default **disabled**. Rewrites the *contents* of JSDoc comments — Prettier has no equivalent, so
this is opt-in and worth reviewing on a branch before adopting repo-wide.

| Field | Default | Meaning |
|---|---|---|
| `commentLineStrategy` | `"singleLine"` | `"singleLine"` collapses when possible, `"multiline"` always expands, `"keep"` preserves. |
| `lineWrappingStyle` | `"greedy"` | `"greedy"` re-wraps to print width; `"balance"` keeps original breaks if they fit. |
| `capitalizeDescriptions` | `true` | Capitalize the first letter of tag descriptions. |
| `addDefaultToDescription` | `true` | Append `Default is \`value\`` to `@param` descriptions. |
| `descriptionWithDot` | `false` | Add a trailing period. |
| `descriptionTag` | `false` | Emit an explicit `@description` tag. |
| `bracketSpacing` | `false` | `{string}` → `{ string }`. |
| `separateTagGroups` | `false` | Blank line between tag groups. |
| `separateReturnsFromParam` | `false` | Blank line between last `@param` and `@returns`. |
| `preferCodeFences` | `false` | Fenced blocks instead of 4-space indent for untagged code. |
| `keepUnparsableExampleIndent` | `false` | Preserve indentation in unparsable `@example` blocks. |

Tag aliases are canonicalized regardless of the sub-options — observed on `{"jsdoc": true}`:

```diff
- * @arg {string} a - the thing
- * @return {number} result
+ * @param {string} a - The thing
+ * @returns {number} Result
```

## svelte

Default **disabled**. Options for `prettier-plugin-svelte`; `true` or `{}` enables, `false` disables
(useful inside `overrides`). Setting `true` resets to defaults, dropping anything inherited from a
parent scope.

**oxfmt does not bundle or auto-install `svelte`.** The plugin needs `svelte/compiler` at runtime,
so you must add `svelte` to your own project. Until both the config key and the package are present,
`.svelte` files are skipped entirely — `oxfmt file.svelte` exits `2` with *"Expected at least one
target file"*, which reads like a path bug but is really a missing-plugin bail-out.

## .editorconfig interaction

oxfmt reads `.editorconfig`, and those values **override oxfmt's built-in defaults**:

| `.editorconfig` key | Overrides |
|---|---|
| `max_line_length` | `printWidth` |
| `indent_size` (falls back to `tab_width`) | `tabWidth` |
| `indent_style` | `useTabs` |
| `end_of_line` | `endOfLine` |
| `insert_final_newline` | `insertFinalNewline` |
| `quote_type` | `singleQuote` |

Verified: an `.editorconfig` with `indent_style = tab` and `max_line_length = 40`, with no oxfmt
config present, produced tab-indented output wrapped at 40 instead of 2-space output at 100. When
formatting disagrees with your expectations and `.oxfmtrc.json` looks right, look for a stray
`.editorconfig` before anything else.
