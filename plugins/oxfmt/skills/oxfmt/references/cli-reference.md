# oxfmt CLI Reference

Every flag below is cross-checked against `oxfmt --help` on **oxfmt 0.64.0**. The help output has
exactly 15 long flags and 3 short aliases; all 15 are documented here.

## Contents

- [Invocation](#invocation)
- [Mode options](#mode-options)
- [Output options — the destructive default](#output-options--the-destructive-default)
- [Config options](#config-options)
- [Ignore options](#ignore-options)
- [Runtime options](#runtime-options)
- [Positional paths and globs](#positional-paths-and-globs)
- [Exit codes](#exit-codes)
- [The two-tier ignore model](#the-two-tier-ignore-model)
- [CI recipes](#ci-recipes)

## Invocation

```text
Usage: [-c=PATH] [PATH]...
```

```bash
npx --yes oxfmt@latest --check .   # no install
npm i -D oxfmt@0.64.0              # pin exactly; 0.x minors may break
```

`--version` prints a bare `Version: 0.64.0` — **it does not print the tool name**, so don't parse it
expecting `oxfmt 0.64.0`.

## Mode options

| Flag | Effect |
|---|---|
| `--init` | Write `.oxfmtrc.json`. Produces a minimal `{ "ignorePatterns": [] }`, not a dump of defaults. |
| `--migrate=SOURCE` | Convert config from `prettier` or `biome`. Refuses to overwrite an existing `.oxfmtrc.json` (exit `1`). |
| `--lsp` | Start the language server. |
| `--stdin-filepath=PATH` | Read source from stdin, use `PATH` only to pick the parser. Writes the result to **stdout**. |

`--stdin-filepath` is the closest thing to Prettier's default behaviour, and the only mode that
hands you the formatted text:

```bash
oxfmt --stdin-filepath=src/a.ts < src/a.ts        # formatted text on stdout
oxfmt --stdin-filepath=src/a.ts < src/a.ts | diff src/a.ts -   # true dry-run diff
```

The named file is not opened for writing — verified byte-identical afterwards.

## Output options — the destructive default

| Flag | Effect | Writes files? |
|---|---|---|
| `--write` | Format and write in place. **This is the default when no output flag is given.** | **yes** |
| `--check` | Report unformatted files plus statistics. | no |
| `--list-different` | Print the path of each file that would change, one per line. | no |

`oxfmt src/` and `oxfmt --write src/` are the same command. There is no `--no-write`; to avoid
writing, choose `--check`, `--list-different`, or `--stdin-filepath`.

**There is also no `--diff`.** Prettier's stdout default and `ruff format --diff` have no direct
counterpart, and the flag is rejected outright:

```console
$ oxfmt --diff messy.js
Error: `--diff` is not expected in this context
```

`--check` and `--list-different` report *which* files differ, never *what* differs. The only mode
that emits formatted content is `--stdin-filepath` (below); for a whole tree, review `git diff`
after running on a clean working tree.

`--write` cannot be combined with a preview mode — oxfmt errors instead of silently picking one:

```console
$ oxfmt --check --write w.js
Error: `--write` cannot be used at the same time as `--check`
$ oxfmt --list-different --write w.js
Error: `--write` cannot be used at the same time as `--list-different`
```

`--list-different` prints bare paths with **no trailing newline** after the last entry, so pipe it
carefully (`| while read -r f; ...` is fine; `$(...)` strips it anyway).

## Config options

| Flag | Effect |
|---|---|
| `-c PATH`, `--config=PATH` | Use exactly this config. Accepts `.json .jsonc .ts .mts .cts .js .mjs .cjs`. |
| `--disable-nested-config` | Do not look for configs in subdirectories; the root config applies everywhere. |

By default oxfmt searches upward *and* honours per-directory configs, so `sub/.oxfmtrc.json` beats
the repository root for files under `sub/`. Verified with `printWidth` 40 vs 120:

```console
$ oxfmt --stdin-filepath=sub/t.js < sub/t.js         # wraps at 40 (sub config)
$ oxfmt --disable-nested-config --stdin-filepath=sub/t.js < sub/t.js   # width 120 (root)
$ oxfmt -c /tmp/w40.json --stdin-filepath=sub/t.js < sub/t.js          # width 40 (forced)
```

`.editorconfig` is also read and overrides oxfmt's built-in defaults for `printWidth`, `tabWidth`,
`useTabs`, `endOfLine`, `insertFinalNewline` and `singleQuote`.

## Ignore options

| Flag | Effect |
|---|---|
| `--ignore-path=PATH` | Use this ignore file. Repeatable. Replaces the default `.prettierignore` slot. |
| `--with-node-modules` | Also format inside `node_modules/` (skipped by default). |

Help text: *"If not specified, `.gitignore` and `.prettierignore` in the current directory are
used."*

## Runtime options

| Flag | Effect |
|---|---|
| `--no-error-on-unmatched-pattern` | Turn the "no files matched" failure (exit `2`) into exit `0`. |
| `--threads=INT` | Thread count. `--threads=1` for deterministic, single-core runs. |
| `-h`, `--help` | Help. |
| `-V`, `--version` | Version. |

## Positional paths and globs

Files, directories, or glob patterns. With no path, the current working directory is used —
**`oxfmt` alone formats and rewrites everything under `.`**.

Quote globs so your shell does not expand them first, and use a `!` prefix to exclude:

```bash
oxfmt 'src/**/*.js' '!src/skip.js'
```

## Exit codes

All verified by running the tool:

| Code | Meaning |
|---|---|
| `0` | Success. Files formatted, or `--check` / `--list-different` found nothing to change. |
| `1` | Formatting differences found (`--check`, `--list-different`), or `--migrate` refused because `.oxfmtrc.json` already exists. |
| `2` | Operational failure: no files matched, a parse error, or invalid flags. |

`2` is **not** "code needs formatting". A syntax error yields `2` and the file is **left
unmodified**:

```console
$ oxfmt bad.js
  x Unexpected token
Error occurred when checking code style in the above files.
$ echo $?
2                       # and bad.js is byte-identical
```

Guard CI accordingly — `if oxfmt --check .; then ...` conflates `1` and `2`. Prefer:

```bash
oxfmt --check .
status=$?
case $status in
  0) echo "formatted" ;;
  1) echo "run oxfmt to fix"; exit 1 ;;
  *) echo "oxfmt itself failed (exit $status)"; exit "$status" ;;
esac
```

## The two-tier ignore model

oxfmt splits ignores into two categories with genuinely different semantics (documented in the oxc
repo's `apps/oxfmt/AGENTS.md`, and confirmed by running it):

**Formatter-owned — exclude a file even when you name it explicitly:**
`.prettierignore`, `--ignore-path`, config `ignorePatterns`, `!` glob patterns.

```console
$ cat .prettierignore
pi/
$ oxfmt --list-different pi/p.js
Expected at least one target file. All matched files may have been excluded by ignore rules.
$ echo $?
2
```

**Git-derived — scope directory discovery only:** `.gitignore`, `.git/info/exclude`. A gitignored
file is skipped during a directory walk but **is still formatted if you name it**:

```console
$ cat .gitignore
gi/
$ oxfmt --list-different .        # gi/ not walked
keep.js
$ oxfmt --list-different gi/g.js  # but explicit path wins
gi/g.js
$ echo $?
1
```

If you need a path to be untouchable, put it in `.prettierignore` or `ignorePatterns` — not
`.gitignore`.

**Hard-excluded lock files** are a third category, unconditional and not configurable.
`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`, `deno.lock`, `composer.lock`,
`Pipfile.lock`, `flake.lock`, `MODULE.bazel.lock`, `Package.resolved`, `Cargo.lock`, `Gopkg.lock`,
`pdm.lock`, `poetry.lock`, `uv.lock` — plus `mcmod.info`, the one non-lock entry on the same
list. Naming any of them directly exits `2` rather than reformatting the file.

## CI recipes

```yaml
# GitHub Actions
- run: npx --yes oxfmt@0.64.0 --check .
```

```jsonc
// package.json — note the pinned version and the explicit modes
{
  "scripts": {
    "format": "oxfmt .",              // rewrites
    "format:check": "oxfmt --check ." // CI gate
  },
  "devDependencies": { "oxfmt": "0.64.0" }
}
```

Pre-commit style, formatting only what is staged. **Do not pipe straight into `xargs`** — with no
staged files, GNU `xargs` still runs the command once with no arguments, and a bare `oxfmt` formats
the whole working directory. (`--no-run-if-empty` fixes that on GNU but is undocumented on BSD/macOS
`xargs`.) Guard with an explicit emptiness check instead:

```bash
files=$(git diff --cached --name-only --diff-filter=ACM)
if [ -n "$files" ]; then
  printf '%s\n' "$files" | tr '\n' '\0' | xargs -0 oxfmt --no-error-on-unmatched-pattern
  printf '%s\n' "$files" | tr '\n' '\0' | xargs -0 git add
fi
```
