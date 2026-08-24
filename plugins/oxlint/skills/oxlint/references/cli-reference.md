# oxlint CLI Reference

Every flag below was extracted from `oxlint --help` on **1.79.0** and cross-checked string by
string. oxlint has **no subcommands** — one binary, one invocation shape:

```
oxlint [-c=<./.oxlintrc.json>] [FLAGS]... [PATH]...
```

`PATH` is a single file, a directory, or a list; the default is the current directory.

## Contents

- [Exit codes](#exit-codes)
- [Basic configuration](#basic-configuration)
- [Allowing / denying rules and categories](#allowing--denying-rules-and-categories)
- [Plugin switches](#plugin-switches)
- [Fixing](#fixing)
- [Ignore files](#ignore-files)
- [Warnings and failure](#warnings-and-failure)
- [Output](#output)
- [Inline configuration comments](#inline-configuration-comments)
- [Miscellaneous](#miscellaneous)
- [Type-aware linting](#type-aware-linting)
- [Agent auto-detection](#agent-auto-detection)
- [What oxlint does NOT have](#what-oxlint-does-not-have)

## Exit codes

**There are exactly two.** From `apps/oxlint/src/result.rs`, every outcome maps to
`ExitCode::SUCCESS` (0) or `ExitCode::FAILURE` (1). There is **no exit 2** — a broken config, an
unknown rule name, an unrecognised flag, "no files found", and genuine lint errors are
indistinguishable by exit code. Always read stderr in CI.

| Exit | Cases |
|---|---|
| `0` | Lint succeeded (including **warnings-only**); `--print-config`; `--init` succeeded |
| `1` | Lint found errors; max-warnings exceeded; `--deny-warnings` with warnings; no files found; unpruned suppressions; invalid config; invalid CLI options; JS-plugin setup failure; tsgolint error |

Verified matrix on a file with 4 correctness violations:

| Invocation | Exit | Notes |
|---|---|---|
| `oxlint` | **0** | 4 warnings — the default CI trap |
| `oxlint -D correctness` | 1 | 4 errors |
| `oxlint --deny-warnings` | 1 | stays *warning* severity, but fails |
| `oxlint --max-warnings 2` | 1 | 4 > 2 |
| `oxlint --max-warnings 0` | 1 | |
| `oxlint --max-warnings 10` | 0 | 4 ≤ 10 |
| `oxlint --quiet` | 0 | warnings hidden entirely |
| `oxlint --quiet -D correctness` | 1 | errors still shown |
| `oxlint <path matching nothing>` | 1 | `No files found to lint.` |
| `oxlint --no-error-on-unmatched-pattern <same>` | 0 | |

## Basic configuration

| Flag | Notes |
|---|---|
| `-c`, `--config=<PATH>` | Root config. `.json`/`.jsonc` everywhere; JS/TS configs experimental, Node only; comments allowed; "tries to be compatible with ESLint v8's format". **Also disables nested-config discovery.** |
| `--tsconfig=<PATH>` | Override the tsconfig used for import resolution. oxlint auto-discovers the relevant `tsconfig.json` per file — use this only for non-standard names/locations. |
| `--init` | Write `.oxlintrc.json` with defaults. ⚠️ **Silently overwrites an existing file.** |
| `--disable-nested-config` | Stop auto-loading `.oxlintrc.json` files from subdirectories. |

## Allowing / denying rules and categories

| Flag | Meaning |
|---|---|
| `-A`, `--allow=NAME` | Suppress the rule or category |
| `-W`, `--warn=NAME` | Emit a warning |
| `-D`, `--deny=NAME` | Emit an error |

`NAME` is a rule name or a category. **They accumulate left to right**, and a later flag overrides
an earlier one for overlapping scope:

```bash
oxlint -D correctness -A no-debugger    # deny the category, then exempt one rule
oxlint -A all -D no-debugger            # allow everything, then re-deny one rule
oxlint -D no-debugger -A all            # ← 0 findings: the trailing -A all wins
```

Categories: `correctness` (default), `suspicious`, `pedantic`, `perf`, `style`, `restriction`,
`nursery`, and `all` — "all categories listed above except `nursery`. Does not enable plugins
automatically."

## Plugin switches

Turn the three optional default-on plugins off:

`--disable-unicorn-plugin` · `--disable-oxc-plugin` · `--disable-typescript-plugin`

Turn off-by-default plugins on:

`--import-plugin` · `--react-plugin` · `--jsdoc-plugin` · `--jest-plugin` · `--vitest-plugin` ·
`--jsx-a11y-plugin` · `--nextjs-plugin` · `--react-perf-plugin` · `--promise-plugin` ·
`--node-plugin` · `--vue-plugin`

(`eslint` has no switch — it is always on.) Enabling a plugin does not enable its non-`correctness`
rules; you still need a category or explicit `rules` entries.

## Fixing

| Flag | Applies | Help text |
|---|---|---|
| `--fix` | safe fixes | "Fix as many issues as possible. Only unfixed issues are reported in the output." |
| `--fix-suggestions` | suggestions | "Apply auto-fixable suggestions. **May change program behavior.**" |
| `--fix-dangerously` | everything | "Apply dangerous fixes and suggestions" |

Additive bitmask; `--fix-dangerously` subsumes the other two. **All three rewrite files in place,
and none changes the exit code** — a fixing run and a clean run look identical.

There is **no preview**: no `--diff`, no `--check`, no `--dry-run`, no `--stdin`. Commit first,
then read `git diff`. Details and verified examples in
[rules-and-categories.md](rules-and-categories.md#fix-safety-taxonomy).

## Ignore files

| Flag | Notes |
|---|---|
| `--ignore-path=PATH` | Use this file as your `.eslintignore` |
| `--ignore-pattern=PAT` | Extra ignore glob (repeatable) |
| `--no-ignore` | Disable `.eslintignore`, `--ignore-path`, `--ignore-pattern`. **Does not disable `.gitignore`** |

`.gitignore` is always honored, even outside a git repo, and there is no way to turn it off.
`node_modules` is not special-cased — it is skipped only because your `.gitignore` lists it.

## Warnings and failure

| Flag | Notes |
|---|---|
| `--quiet` | Hide warnings; only errors are reported. Does not change the exit code by itself |
| `--deny-warnings` | Warnings produce a non-zero exit (severity stays "warning" in the output) |
| `--max-warnings=INT` | Exit non-zero if warning count exceeds INT. `0` fails on any warning |
| `--silent` | Print no diagnostics at all (exit code still meaningful) |

## Output

`-f`, `--format=ARG` — one of `default`, `agent`, `json`, `github`, `gitlab`, `checkstyle`,
`junit`, `sarif`, `stylish`, `unix`. All ten verified rendering.

| Format | Shape |
|---|---|
| `default` | Rich miette output with source excerpt and labelled spans |
| `agent` | `file:line:col: severity plugin(rule): message help: …` — one line per diagnostic |
| `json` | `{ "diagnostics": [...], "number_of_files", "number_of_rules", "threads_count", "start_time" }`; each diagnostic carries `code`, `severity`, `url`, `help`, `filename`, `labels[].span` |
| `github` | `::error file=…,line=…,col=…,title=eslint(no-dupe-keys)::…` workflow annotations |
| `gitlab` | Code Quality JSON with `fingerprint` and `severity: critical` |
| `sarif` | SARIF 2.1.0 |
| `junit` | JUnit XML `<testsuites>` |
| `checkstyle` | Checkstyle 4.3 XML |
| `stylish` | ESLint's familiar grouped-by-file output |
| `unix` | `file:line:col: message [Error/plugin(rule)]` |

`--debug=OPTIONS` (comma-separated): `files` — print the file list that would be linted, then exit;
`timings` — per-rule timing information.

## Inline configuration comments

| Flag | Notes |
|---|---|
| `--report-unused-disable-directives` | Report `oxlint-disable*`/`eslint-disable*` comments that suppress nothing. **Defaults to `warn`, so it exits 0** |
| `--report-unused-disable-directives-severity=SEVERITY` | Same, with an explicit severity. **Mutually exclusive** with the flag above |

Use `--report-unused-disable-directives-severity deny` if you want CI to fail. This flag finds
*dead* directives only — it is not a check on directives that hide real violations. See
[rules-and-categories.md](rules-and-categories.md#the-unused-directive-ratchet-and-what-it-does-not-do).

## Miscellaneous

| Flag | Notes |
|---|---|
| `--print-config` | Print the resolved configuration and exit without linting. Only config-related options are valid alongside it |
| `--rules` | List all registered rules. **Renders only under `--format json` or `--format default`** |
| `--lsp` | Start the language server |
| `--threads=INT` | Worker threads; `1` pins to a single core |
| `--no-error-on-unmatched-pattern` | Do not exit 1 when no files are selected |
| `-h`, `--help` / `-V`, `--version` | `--version` prints `Version: 1.79.0` — the number only, no tool name |

## Type-aware linting

| Flag | Notes |
|---|---|
| `--type-aware` | Enable the 59 rules that need type information |
| `--type-check` | Experimental type checking, including TypeScript compiler diagnostics |

Both require the separate **`oxlint-tsgolint`** npm package; without it `--type-aware` exits 1 with
`Failed to find tsgolint executable`. `--type-check` without `--type-aware` is rejected. Config
equivalents: `"options": { "typeAware": true, "typeCheck": true }`.

## Agent auto-detection

`apps/oxlint/src/agent_detection.rs` inspects the environment and, when it recognises an AI coding
agent, switches the default output format to `agent`. Recognised signals include `AI_AGENT` (any
value), `CLAUDECODE` / `CLAUDE_CODE`, `REPL_ID`, `GEMINI_CLI`, `CODEX_SANDBOX` /
`CODEX_THREAD_ID`, `COPILOT_CLI`, `OPENCODE`, `JUNIE_DATA` / `JUNIE_SHIM_PATH`, `CURSOR_AGENT`,
a `.pi/agent` segment in `PATH`, and `EDITOR` containing `devin`.

Verified on 1.79.0 with `CLAUDECODE=1` set:

```bash
$ oxlint src/f.js
src/f.js:1:13: error eslint(no-dupe-keys): Duplicate key 'a' help: Consider removing …

$ env -u CLAUDECODE -u CLAUDE_CODE -u AI_AGENT oxlint src/f.js
  x eslint(no-dupe-keys): Duplicate key 'a'
   ,-[src/f.js:1:13]
 1 | const o = { a: 1, a: 2 };
   :             |     |
   :             `-- Key is first defined here
```

The practical consequences:

- Output you see will not match upstream documentation screenshots. That is expected.
- **`oxlint --rules` writes zero bytes** under an agent, because the `agent` formatter has no
  renderer for it. Same for `stylish`, `unix` and `github`. Use `--rules --format json`.
- Pass `-f default` explicitly if you want the rich span output.

## What oxlint does NOT have

Worth knowing so you do not go looking:

- **No subcommands.** No `oxlint check`, no `oxlint rule <name>`, no `oxlint explain`.
- **No dry-run / diff / check mode** for fixes.
- **No stdin input.**
- **No cache flag.** (It is fast enough that there is nothing to cache.)
- **No formatter.** That is **oxfmt**, a separate binary and a separate skill.
- **No exit code 2.** Config errors and lint errors both exit 1.
- **No `--recommended` / preset flag.** Categories do that job.
