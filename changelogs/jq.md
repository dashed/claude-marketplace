# Changelog - jq

All notable changes to the jq skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-06-08

### Added
- Initial addition to the marketplace — a skill for **jq**, the command-line JSON processor and its filter language, scoped to the CLI + filter language + builtin library. Authored against the jq source (jqlang/jq, dev tree past jq-1.8.2rc1); every example verified on the installed CLI **jq-1.7.1**.
- `SKILL.md`: the filter/stream mental model (a jq program is a filter mapping an input stream of JSON values to an output stream; `|` pipes, `,` forks); install; invocation; seven runnable core workflows (pretty/validate, extract with `-r`, `select`/`map`, reshape objects, `@csv`/`@tsv` + raw input, slurp+aggregate/`group_by`, `--arg`/`--argjson`/`$ENV`/`-f`); agent-usage patterns; quick-reference; troubleshooting.
- `references/cli.md`: invocation forms; every command-line flag (verified against `jq --help` on 1.7.1); I/O & slurp modes; the full exit-code set (0/1/2/3/4/5); argument passing & `$ARGS`/`$ENV`; the module search path; non-interactive/agent patterns; verbatim `jq --help` appendix.
- `references/language.md`: identity & path expressions, pipe/comma, object/array construction, operators, the alternative `//`, `if`/`try`/`?`, `reduce`/`foreach`, variables & destructuring + `?//`, `def`/recursion/closures, `label`/`break`, string interpolation, the assignment operators + path-expression semantics (including `(...)|=empty` deletion), path builtins, and modules.
- `references/builtins.md`: the builtin function library grouped by category — types/inspection, arrays/objects (`group_by`/`unique_by`/`INDEX`/`IN`/`walk`/`pick`), strings + regex (`test`/`match`/`capture`/`scan`/`sub`/`gsub`/`splits`), format strings, math, dates (with the verified `gmtime` array order), streaming (`tostream`/`fromstream`/`inputs`), SQL-style, and debug/`halt_error`.
- `references/version-features.md`: 35 source-cited `feature → minimum jq version` rows (1.7 / 1.7.1 / 1.8), grouped by area, plus a labeled "Removed" subsection (`--argfile`, `leaf_paths`, `recurse_down` in 1.7; `pow10` in 1.8).
- Inline `(jq 1.X+)` version annotations sourced from the repo's `NEWS.md` cross-checked with the versioned manuals (`docs/content/manual/v1.6`→`v1.8`), git blame on `src/builtin.jq`, and empirical CLI boundary tests (1.8 builtins like `trim`/`trimstr`/`toboolean`/`@urid` confirmed to error on 1.7.1); bedrock (≤1.6, 2018) left unannotated ("unlisted = long-standing").
- Documents three commonly-assumed features that do **not** exist in any jq version (`@base32`/`@base32d`, `toarray`, `dateadd` — empirically confirmed and absent from source/manuals), steering users to the real alternatives.
