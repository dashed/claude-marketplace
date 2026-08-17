# Changelog - uv

All notable changes to the uv skill in this marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.1.0] - 2026-08-16

Re-verified the skill against the **uv 0.12.x** line (`uv 0.12.5`, released 2026-08-14) — it was previously documented against 0.11.x with examples verified on `uv 0.11.2`. uv is `0.x`, so **0.12.0 shipped breaking changes in a minor bump**; this is a correctness pass over that delta, not a rewrite. Structure, voice, and the "four surfaces over one binary" mental model are unchanged.

### Fixed
- **`uv init` was documented with the pre-0.12 flat layout.** `uv 0.12.0` made projects **packaged by default** (`uv_build` `[build-system]` + `src/<name>/` + a `[project.scripts]` entry), so `SKILL.md`'s `uv init demo` file list, its `uv run main.py` example, and `projects.md`'s `--app` table row and init example were all wrong. Corrected and re-verified empirically, with `--no-package` documented as the way back to the old layout.
- **`--prerelease` default was stale.** `pip-config.md` listed the modes without flagging that `0.12.0` changed the default from `if-necessary-or-explicit` to `if-necessary` (and demoted the old name to a deprecated alias) — a resolution-affecting change, since transitively-discovered pre-release requirements now resolve where they used to fail.
- **`uv tool upgrade` was said to have no `--reinstall`.** Verified on 0.12.5: `--reinstall` and `--reinstall-package` are present. (`--upgrade-package` is still genuinely absent — that half of the claim stands.)
- **`--torch-backend` CUDA/ROCm values were stale.** Newest CUDA is now `cu132` (was documented as `cu130`) and ROCm reaches `rocm7.2`; also corrected the command list to `uv tool run`/`uv tool install` rather than a loose "uvx / uv tool".
- **`uv cache size` was documented as an ordinary command** — it is still a **preview** feature on 0.12.5.
- **`uv format` was described as "still preview in 0.11.x"** — re-pinned to 0.12.x (it remains preview).
- Removed a stale "not on a 0.11.2 box" caveat on per-index keys and re-pinned `uv lock`'s "no `--locked`/`--frozen`" note to 0.12.5.

### Added
- **`uv check`** *(preview, uv 0.11.18+)* — the ty-backed project type checker, previously absent from the skill. Documented in `SKILL.md`'s command list with `--fix`, `--package`/`--all-packages`, and `--script`, and explicitly distinguished from a lockfile check.
- **A "upgrading to 0.12? four things bite" troubleshooting entry** covering the packaged-`init` default, the `--prerelease` default, `uv venv --clear` needing `--force` for non-virtualenv directories, and `--project` path validation becoming an error.
- **12 new rows in `version-features.md`'s breaking table for the `0.12.0` batch** — packaged init, prerelease default, stricter `--project`, `uv venv --clear`, script-relative `uv run` discovery, PEP 625 archive-format rejection, hash-checking hardening (`--require-hashes` in requirements files; MD5 rejected), `--reinstall` no longer upgrading Python, `--upgrade-group` validation, `--directory`-relative indexes, and absolute-path preservation in `uv add`.
- **21 new rows in the feature → minimum-version table** spanning `0.11.18`→`0.12.3`: `uv check` (+ `--fix`, `--package`/`--all-packages`), `uv tool audit`, `uv init --no-package`, `uv venv --force`, `uv pip --cert`, `--prerelease-package`, `uv tree --format json`, `uv pip compile --emit-build-options`, `TY`/`RUFF` binary-path env vars, `preview-features` in `uv.toml`/`pyproject.toml`, `uv audit` SARIF output, scoped dependency overrides/exclusions, `UV_RUN_RLIMIT_NOFILE`, `uv cache size --output-format`, Xonsh `activate.xsh`, and CUDA 13.2. The hidden `uv upgrade` command is now recorded as a row marked **hidden** rather than silently omitted.
- **Per-feature preview opt-out** documented (`--preview-features format-command|check-command|audit-command|cache-size|workspace-metadata`), plus `uv workspace dir`/`list` in the command list.
- New `pip-config.md` sections for **hash checking (changed in 0.12.0)** and `--directory`-relative index resolution.

### Changed
- **Disambiguation note now cross-references the real sibling skills.** `ruff` and `ty` are shipped as their own marketplace skills in this release, so the note points at them for rules/config/diagnostics and states that uv merely shells out — `uv format` wraps `ruff format`, `uv check` wraps `ty check` (both preview). No content is duplicated from those skills.
- Version pin moved to the 0.12.x line throughout; provenance labels now distinguish what was originally verified on 0.11.2 from what was re-verified on 0.12.5.
- **Flag audit:** every one of the ~203 flag strings the skill documented was mechanically cross-checked against `uv help <command>` captures for 54 subcommands on 0.12.5. **Zero flags failed verification** — no flag was renamed or removed. The errors found were behavioral (defaults, layouts, values), which is what a changelog-only review would have missed in the other direction.

## [1.0.0] - 2026-06-11

### Added
- Initial addition to the marketplace — a skill for **uv**, Astral's fast Python package & project manager (one binary replacing pip/pipx/pyenv/poetry/virtualenv). Authored against the uv source (dev tree past **0.11.20**), with the repo's per-release `CHANGELOG.md` as the primary version source; every flag and workflow empirically verified on the installed **uv 0.11.2** (sandboxed in /tmp).
- `SKILL.md`: the four-surface mental model (projects / PEP 723 scripts / tools / Python toolchains), install + `uv self update`, six verified core workflows (new project + add/run, inline-dependency scripts, `uvx` one-off tools, Python install/pin, pip migration via `uv pip`, sync/lock in CI), quick-reference, troubleshooting (incl. the 0.7.0 `uv version` repurposing).
- `references/projects.md`: `uv init` variants, `uv add`/`remove` (extras, groups, git/path/url/workspace sources, `[tool.uv.sources]`), `uv sync` semantics, `uv lock` (+ `--check`/`--check-exists`), `uv run` env layering, `uv tree`, `uv export` (requirements.txt / `pylock.toml` 0.6.15+ / CycloneDX), PEP 735 dependency groups vs extras, workspaces, `uv version` + `--bump` (0.7.0+), `uv build`/`uv publish` (+ trusted publishing), and the universal-lockfile model.
- `references/scripts-tools-python.md`: PEP 723 scripts (`uv init/add/lock --script`, shebang, `--with`), script lockfiles (0.5.17+), `uvx`/`uv tool` (install/upgrade/list/dir, `--from`, `--with`), `uv python` (install/list/find/pin/upgrade (0.10.0+), `.python-version`, free-threaded/PyPy variants), and `uv venv` vs `uv run`.
- `references/pip-config.md`: the `uv pip` interface with pip-compat philosophy + deviations, caching (`uv cache clean/prune/size`, `--refresh`), configuration discovery (`[tool.uv]` vs `uv.toml`, user-level, `UV_*` env-var table), named indexes (`[[tool.uv.index]]`, 0.4.23+) + index strategy + auth (`uv auth login/logout/token/dir`, 0.8.15+), resolution (`--resolution`, `--prerelease`, overrides/constraints/build-constraints, `--exclude-newer` incl. duration syntax), `--torch-backend` (on `uv pip`/`uvx`, not `uv add`), and `--python-platform`/`--python-version` cross-targeting.
- `references/version-features.md`: 37 source-cited `feature → minimum uv version` rows (0.4.x→0.11.x; preview features like `uv format` and `uv audit` clearly labeled), a "Breaking/renamed across 0.x minors" subsection (`uv version` repurposed 0.7.0; `--index-url`/`--extra-index-url` deprecated for named indexes 0.4.23; `uv_build` default backend 0.8.0; installer dir 0.5.0; TLS/`--system-certs` 0.11.0), and a version-check closer.
- Inline `(uv 0.X+)` version annotations sourced from the repo `CHANGELOG.md` (+ archived `changelogs/0.*.md`), cross-checked with git tags and empirical binary tests; bedrock (≤0.4.0, Aug 2024) left unannotated ("unlisted = long-standing").
- Live-binary verification corrected several details over the research dossier: `uv auth` subcommands are `login/logout/token/dir` (no `helper`); `uv sync`/`uv run` expose only `--no-dev`/`--only-dev` (no `--dev` — the dev group is on by default); `uv sync` has no `--exact` flag (exact is the default; `--inexact` opts out); `uv tool upgrade` has no `--upgrade-package`/`--reinstall`; `--exclude-newer` duration syntax already works on 0.11.2. The hidden, 0.11.20-only `uv upgrade` command was deliberately left undocumented.
