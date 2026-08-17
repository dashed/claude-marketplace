# Migrating to ty from mypy or pyright

Distilled from ty's own `docs/coming-from-mypy-or-pyright.md` and `docs/reference/typing-faq.md`,
verified against **ty 0.0.72**. The upstream doc carries a ~90-row rule-mapping table; the subset
below is the part you actually reach for, plus the conceptual differences that trip people up.

## Contents

- [Migration checklist](#migration-checklist)
- [Concept mapping](#concept-mapping)
- [The strictness inversion](#the-strictness-inversion)
- [Recommended strict configs](#recommended-strict-configs)
- [Rule mapping — high-traffic subset](#rule-mapping--high-traffic-subset)
- [Checks that are Ruff's job, not ty's](#checks-that-are-ruffs-job-not-tys)
- [Things ty deliberately does not have](#things-ty-deliberately-does-not-have)

## Migration checklist

1. **Install pinned**: `uv add --dev ty`. Run it as `uv run ty check` so the venv is discovered.
2. **Get environment discovery right first.** Most of a bad first run is import resolution, not real
   type errors. If your sources aren't at the root or in `src/`, set
   `environment.root = ["./app"]`. Translate `MYPYPATH` / `stubPath` to `environment.extra-paths`.
3. **Set `python-version` deliberately.** ty defaults to the *lower bound* of
   `project.requires-python` — often older than what you actually run, producing surprising
   stdlib/syntax errors.
4. **Baseline, don't boil the ocean**: `ty check --add-ignore` on a clean tree writes
   `# ty: ignore[rule]` for every current diagnostic and exits 0. Commit that mechanically, turn on
   CI, then burn the suppressions down (`unused-ignore-comment` tells you when one is redundant).
5. **Port suppressions incrementally.** Existing `# type: ignore` comments keep working — ty honors
   PEP 484. Mixed-checker lines can use `# type: ignore[arg-type, ty:invalid-argument-type]`.
6. **Relax for tests via `[[overrides]]`**, not by globally lowering rules.
7. **Only then** consider turning on opt-in rules (see [Recommended strict configs](#recommended-strict-configs)).

## Concept mapping

| Concept | mypy | pyright | ty |
|---|---|---|---|
| Config location | `[tool.mypy]` / `mypy.ini` | `[tool.pyright]` / `pyrightconfig.json` | `[tool.ty]` / `ty.toml` (`ty.toml` wins) |
| Suppress one line | `# type: ignore[code]` | `# pyright: ignore[reportX]` | `# ty: ignore[rule]` (also honors both `# type: ignore` forms) |
| Suppress a whole file | `# mypy: ignore-errors` | `# pyright: basic` header | `# ty: ignore[rule]` on its own line before any code |
| Disable a check | `disable_error_code = [...]` | `reportX = "none"` | `<rule> = "ignore"` under `[tool.ty.rules]` |
| Severity levels | error, note | error, warning, information, hint | **`error`, `warn`, `ignore`** — map pyright's *information* and *hint* onto `warn` |
| Per-file settings | `[[tool.mypy.overrides]]` + `module` | `executionEnvironments` | `[[tool.ty.overrides]]` + `include`/`exclude` **path globs** |
| Extra search path | `MYPYPATH` | `stubPath` | `environment.extra-paths` |
| Python version | `python_version` | `pythonVersion` | `environment.python-version` |
| Target platform | `platform` | `pythonPlatform` | `environment.python-platform` |
| Interpreter / env | `python_executable` | `venvPath` + `venv` | `environment.python` |
| Custom typeshed | `custom_typeshed_dir` | `typeshedPath` | `environment.typeshed` |
| Exclude files | `exclude` (regex) | `exclude` (globs) | `src.exclude` (**anchored** gitignore globs) |
| Untyped-def bodies | `check_untyped_defs` (opt-in) | `analyzeUnannotatedFunctions` | **always on**, not configurable |
| Strict preset | `--strict` | `"strict"` | **none** — see below |
| Plugins | supported | n/a | **not supported, by design** |

Note the `exclude` difference: mypy uses a *regex*, ty uses gitignore-style globs that are
**anchored to the project root**. `exclude = ["src"]` does not exclude `tests/src`; write `**/src`
for that (at a file-discovery performance cost).

## The strictness inversion

This is the single biggest mental adjustment. In mypy and pyright, `--strict` both enables extra
error codes *and* changes inference fundamentals (`--check-untyped-defs`, `strictListInference`).

**ty has no `--strict` because those inference behaviours are its defaults and are not configurable
down.** Nearly all ty rules are on by default; the 10 that are off are off because they're
opinionated or false-positive-prone. So:

- Coming from **default mypy/pyright**, expect ty to be *noisier* on first run — it is checking
  unannotated function bodies you never had checked.
- Coming from **`--strict`**, expect ty to be comparable, minus the "require annotations" family,
  which ty does not implement at all (that's Ruff's `ANN`).

`Unknown` is what keeps this tractable: unannotated symbols infer as `Unknown` (an implicit `Any`),
so untyped code doesn't error — ty follows the typing spec's *gradual guarantee* that adding
annotations shouldn't introduce new errors. ty also permits **redeclaration** of a name at a
different type, which mypy rejects with `no-redef`:

```python
def split_paths(paths: str) -> list[Path]:
    paths: list[str] = paths.split(":")   # legal in ty; mypy: no-redef
    return [Path(p) for p in paths]
```

## Recommended strict configs

ty's own docs recommend **against** `--error=all`. Their suggested approximation of other checkers'
strict mode:

```toml
[tool.ty.rules]
missing-type-argument = "error"
possibly-unresolved-reference = "warn"
unsound-return-statement = "error"

[tool.ruff.lint]
extend-select = ["ANN", "PYI"]
preview = true
```

Going further than mypy/pyright `--strict` (upstream flags the last three as false-positive-prone —
"enable at your own risk"):

```toml
[tool.ty.rules]
blanket-ignore-comment = "error"
missing-type-argument = "error"
possibly-unresolved-reference = "warn"
unsound-return-statement = "error"
unsound-yield = "error"
unsupported-dynamic-base = "warn"

division-by-zero = "warn"
possibly-missing-attribute = "warn"
possibly-missing-import = "warn"

[tool.ty.analysis]
strict-literal-narrowing = true
strict-generic-narrowing = true

[tool.ruff.lint]
extend-select = ["ANN", "PYI", "PGH003"]
preview = true
```

> `strict-literal-narrowing` is accepted by the 0.0.72 binary but is absent from `ty.schema.json`
> and from `docs/reference/configuration.md` — verify it on your build with
> `ty check -c 'analysis.strict-literal-narrowing=true'` before committing it.

## Rule mapping — high-traffic subset

| ty rule | mypy error code | pyright diagnostic |
|---|---|---|
| `invalid-argument-type` | `arg-type`, `index`, `type-var`, `typeddict-item` | `reportArgumentType`, `reportAssignmentType` |
| `invalid-assignment` | `assignment` | `reportAssignmentType` |
| `invalid-return-type` | `return-value` | `reportReturnType` |
| `missing-argument` | `call-arg` | `reportCallIssue` |
| `unknown-argument` | `call-arg` | `reportCallIssue` |
| `too-many-positional-arguments` | `call-arg` | `reportCallIssue` |
| `parameter-already-assigned` | `misc`, `call-arg` | `reportCallIssue` |
| `no-matching-overload` | `call-overload` | `reportCallIssue` |
| `call-non-callable` | `operator` | `reportCallIssue` |
| `unresolved-import` | `import-not-found` | `reportMissingImports` |
| `unresolved-reference` | `name-defined` | `reportUndefinedVariable` |
| `unresolved-attribute` | `attr-defined`, `union-attr` | `reportAttributeAccessIssue`, `reportOptionalMemberAccess` |
| `possibly-unresolved-reference` | `possibly-undefined` | `reportPossiblyUnboundVariable` |
| `conflicting-declarations` | `no-redef` | `reportRedeclaration` |
| `invalid-method-override` | `override` | `reportIncompatibleMethodOverride` |
| `missing-override-decorator` | `explicit-override` | `reportImplicitOverride` |
| `missing-type-argument` | `type-arg` | `reportMissingTypeArgument` |
| `invalid-type-form` | `valid-type` | `reportInvalidTypeForm` |
| `invalid-type-arguments` | `misc`, `type-var` | `reportInvalidTypeArguments` |
| `unsupported-operator` | `operator` | `reportOperatorIssue` |
| `not-subscriptable` | `index` | `reportIndexIssue` |
| `not-iterable` | `misc`, `attr-defined` | `reportGeneralTypeIssues` |
| `missing-typed-dict-key` | `typeddict-item` | `reportAssignmentType` |
| `invalid-key` | `typeddict-item`, `typeddict-unknown-key` | `reportAssignmentType` |
| `redundant-cast` | `redundant-cast` | `reportUnnecessaryCast` |
| `unused-awaitable` | `unused-coroutine`, `unused-awaitable` | `reportUnusedCoroutine` |
| `unused-ignore-comment` | `unused-ignore` | `reportUnnecessaryTypeIgnoreComment` |
| `type-assertion-failure` | `assert-type` | `reportAssertTypeFailure` |
| `deprecated` | `deprecated` | `reportDeprecated` |
| `empty-body` | `empty-body` | — |
| `invalid-overload` | `no-overload-impl` | `reportNoOverloadImplementation` |
| `unsound-return-statement` | `no-any-return` | — |
| `blanket-ignore-comment` (+ Ruff `PGH003`) | `ignore-without-code` | `reportIgnoreCommentWithoutRule` (basedpyright) |
| `undefined-reveal` | `unimported-reveal` | — |
| `call-abstract-method` | — | `reportAbstractUsage` |
| `division-by-zero` | — | — |

Many mypy codes collapse into catch-alls (`misc`, `assignment`, `valid-type`) and many pyright
diagnostics into `reportGeneralTypeIssues` — those mappings are deliberately broad in both
directions. A blank cell means no direct equivalent.

For the full table, read `docs/coming-from-mypy-or-pyright.md` in the ty repo, or
<https://docs.astral.sh/ty/coming-from-mypy-or-pyright/>.

## Checks that are Ruff's job, not ty's

ty does no linting. Several familiar mypy/pyright checks have **no ty rule** and are covered by Ruff:

| You want | mypy / pyright | Use instead |
|---|---|---|
| Require annotations on defs/params/returns | `disallow_untyped_defs` / `reportMissingParameterType` | Ruff `ANN` (`ANN001`, `ANN002`, `ANN003`, `ANN201`, `ANN202`) |
| Ban bare `# type: ignore` | `ignore-without-code` | Ruff `PGH003` (or ty's opt-in `blanket-ignore-comment`) |
| Stub-file hygiene | — | Ruff `PYI` group |
| Duplicate / wildcard imports | — | Ruff `F811`, `F403`, `I001` |
| Unused expressions | — | Ruff `B018` |
| Bad `__all__` | `reportUnsupportedDunderAll` | Ruff `F822`, `PLE0604`, `PLE0605`, `PYI056` |
| `self`/`cls` naming | `reportSelfClsParameterName` | Ruff `N804`, `N805` |
| Invalid string escapes | `reportInvalidStringEscapeSequence` | Ruff `W605` |

This is why the recommended strict config pairs `[tool.ty.rules]` with `[tool.ruff.lint]` — the two
tools are designed to divide the work.

## Things ty deliberately does not have

- **No plugin system.** No equivalent of mypy's pydantic/django/SQLAlchemy plugins, and none is
  planned; Astral is adding library support natively instead (ty 0.0.7x already ships
  Pydantic-specific behaviour, e.g. the `pydantic-discarded-extra-argument` rule).
- **No `--strict`.** See [The strictness inversion](#the-strictness-inversion).
- **No "require annotations" rules.** Ruff `ANN`.
- **Limited monorepo auto-discovery.** ty resolves one project root (cwd or `--project`). Prefer
  running `ty check --project packages/a` per package over listing every package in
  `environment.root`, which flattens them into one project and makes cross-package imports resolve
  that would fail at runtime.
- **Per-script PEP 723 deps only one at a time.** A single inline-metadata script can be checked via
  `uvx --with-requirements script.py ty check script.py`; ty does not yet give several scripts in one
  workspace their own dependency sets.
