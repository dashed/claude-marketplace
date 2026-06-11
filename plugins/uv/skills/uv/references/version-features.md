# uv Feature → Minimum Version

A consolidated lookup of **which uv release introduced a command, flag, project/script
capability, or behavior** this skill documents, so you know what works on an older (or newer)
uv. Use it to answer "is my uv new enough for X?" and "what do I need to upgrade to?"

**How to read this:**

- These are **uv release versions** (`MAJOR.MINOR.PATCH`, e.g. `0.11.2`). The `0.7.0+` form
  means "the 0.7.0 release and later." Each row's version is the **earliest release in which the
  feature is available**. uv is still **`0.x`**, so — unlike a post-1.0 project — a **minor bump
  can break existing behavior**; the breaking renames are called out separately below and kept
  *out* of the min-version table.
- Annotations are sourced from uv's repo **`CHANGELOG.md`** (covers `0.10.0`→`0.11.20`) plus the
  per-minor archives under **`changelogs/0.*.md`** (`0.1.x`→`0.9.x`), each row carrying the
  enclosing `## X.Y.Z` CHANGELOG header (and a PR number where one exists). These are
  cross-checked against the **git release tags** (`0.0.5`→`0.11.20`, 284 tags) and **empirical
  runs on the installed binary `uv 0.11.2`**. **No version is guessed:** a feature with no clean
  "added in vX" source is treated as long-standing and left out of the table.
- **Features not listed here are long-standing** — present at or before **uv 0.4.0**
  (**August 2024**) and treated as **bedrock**, so they carry no version tag. This includes
  essentially the everyday surface: the core `uv init` / `uv add` / `uv remove` / `uv sync`
  (incl. `--frozen` / `--locked` / `--exact` / `--inexact`) / `uv lock` / `uv run` / `uv tree`
  workflow; the whole `uv tool` suite and the **`uvx`** alias (incl. `uv tool upgrade --all`);
  `uv python install/list/find/pin/uninstall`; `uv venv` (incl. `--seed`); the `uv pip`
  interface; `[tool.uv.sources]` (git/path/url/workspace); `--exclude-newer`; universal
  multi-platform `uv.lock`; `uv cache prune` / `--prune`; PyPy install support; `uv self update`;
  `uv publish` core; and resolver knobs like `--resolution lowest/lowest-direct` and
  `--prerelease`. This file omits them to stay signal-rich.
- **Preview commands are labeled.** `uv format` (a Ruff-backed Python formatter) and `uv audit`
  (an OSV vulnerability scan) are real but still ship under **"Preview features"** in the 0.11.x
  line — do not treat them as stable everyday commands.
- This skill is documented and verified against the installed CLI **`uv 0.11.2`**. The current
  released line is **0.11.x** (latest `0.11.20`). Always confirm on the running system — see
  [Checking your version](#checking-your-version).

Breaking renames live in their own section so they don't pollute the "minimum version" table —
see [Breaking / renamed across 0.x minors](#breaking--renamed-across-0x-minors) below.

## Contents

- [Versioned features (ascending by uv release)](#versioned-features-ascending-by-uv-release)
- [Breaking / renamed across 0.x minors](#breaking--renamed-across-0x-minors)
- [Checking your version](#checking-your-version)

## Versioned features (ascending by uv release)

Sorted ascending by minimum uv release; within a release, grouped by **Area**
(projects / scripts / tools / python / pip-resolution / CLI-misc).

| Min version | Feature | Area |
|---|---|---|
| 0.4.1+ | `uv export --format requirements-txt` (just past bedrock) | projects |
| 0.4.16+ | Trusted publishing for `uv publish` (just past bedrock) | projects |
| 0.4.17+ | `uv init --script` — add PEP 723 inline metadata to a script | scripts |
| 0.4.19+ | `uv run --script` flag | scripts |
| 0.4.23+ | Named indexes: `[[tool.uv.index]]`, `--index`, `--default-index` (just past bedrock) | pip-resolution |
| 0.4.27+ | PEP 735 dependency groups (`[dependency-groups]`, `--group`) (just past bedrock) | projects |
| 0.5.5+ | `uv export --prune` | projects |
| 0.5.17+ | `uv lock --script` — lockfiles for PEP 723 scripts | scripts |
| 0.5.17+ | `uv export --script` / `uv tree --script` | scripts |
| 0.5.23+ | `--no-default-groups` flag | projects |
| 0.6.7+ | `uv python pin --global` — set the global default Python | python |
| 0.6.8+ | `default-groups = "all"` (enable all dependency groups by default) | projects |
| 0.6.8+ | `--managed-python` / `--no-managed-python` flags | python |
| 0.6.9+ | `--torch-backend` (experimental; infer the PyTorch index, e.g. `=auto`) | pip-resolution |
| 0.6.15+ | `uv export` PEP 751 `pylock.toml` output | projects |
| 0.7.0+ | `uv version` repurposed to show/update the **project** version (`--bump`, `--short`) — see Breaking section | projects |
| 0.7.3+ | GraalPy download support | python |
| 0.7.12+ | `uv python pin --rm` — remove a pin | python |
| 0.7.14+ | `--torch-backend` **stabilized** (preview label removed) | pip-resolution |
| 0.7.14+ | `uv python upgrade` introduced (preview; transparent patch upgrades) | python |
| 0.7.14+ | Per-group `requires-python` (`[tool.uv.dependency-groups].<g>.requires-python`) | projects |
| 0.7.19+ | `uv_build` backend **stabilized** | projects |
| 0.7.21+ | `uv version --bump` pre-release support | projects |
| 0.8.13+ | `uv format` — Ruff-backed Python formatter (**PREVIEW**, still preview in 0.11.x) | CLI-misc |
| 0.8.15+ | `uv auth` — credential-management commands | CLI-misc |
| 0.8.18+ | Trusted publishing — GitLab CI/CD publisher | projects |
| 0.9.0+ | Free-threaded Python 3.14+ usable without explicit opt-in | python |
| 0.9.9+ | `uv version --bump` explicit values | projects |
| 0.10.0+ | `uv auth` — multiple credentials per host | CLI-misc |
| 0.10.0+ | `uv python upgrade` / `uv python install --upgrade` **stabilized** | python |
| 0.10.3+ | `uv format` — ruff version constraints + `exclude-newer` (**PREVIEW**) | CLI-misc |
| 0.10.10+ | `uv audit` — OSV vulnerability scan (**PREVIEW**) | CLI-misc |
| 0.10.12+ | `uv audit` shown in the CLI help (**PREVIEW**) | CLI-misc |
| 0.11.0+ | `uv audit --service-format` / `--service-url` (**PREVIEW**) | CLI-misc |
| 0.11.3+ | `uv audit --ignore` / `--ignore-until-fixed` (**PREVIEW**) | CLI-misc |
| 0.11.15+ | `uv audit` JSON output (**PREVIEW**) | CLI-misc |
| 0.11.20+ | `uv export --emit-index-url` / `--emit-find-links` | projects |

## Breaking / renamed across 0.x minors

Because uv is pre-1.0, these **minor** releases changed existing behavior or moved a command.
Review uv's `CHANGELOG.md` for the release before upgrading. They are listed here for migration
only and are **not** part of the "minimum version" table above.

| Release | Change | Migration / note |
|---|---|---|
| 0.4.23 | `--index-url` / `--extra-index-url` **deprecated** | Still work (backwards-compatible); prefer `--index` / `--default-index` and `[[tool.uv.index]]` |
| 0.5.0 | Installer directory → `~/.local/bin` (was `~/.cargo/bin`) | Also: `.python-version` now discovered in parent dirs; `allow-insecure-host` became global |
| 0.6.0 | `uv init` creates `main.py` (was `hello.py`) | Also: `uv publish` left preview; uv sets the `UV` env var to its own path |
| 0.7.0 | **`uv version` repurposed** to display/update the *project* version | uv's own version moved to `uv self version`; `--version` removed from subcommands; Python 3.7 downloads dropped |
| 0.8.0 | **`uv_build` becomes the default build backend** in `uv init --package` / `--lib` (was hatchling) | Also: `uv version` errors outside a project; `--check` returns exit 1; removing a global Python pin requires `--global` |
| 0.9.0 | **Python 3.14 is now the default stable** | Free-threaded 3.14+ usable without explicit opt-in |
| 0.10.0 | `uv venv` requires `--clear` to overwrite an existing environment | Also: error on multiple `default = true` indexes; `uv python upgrade` / add-bounds / `uv workspace dir`/`list` stabilized |
| 0.11.0 | **TLS overhaul** (rustls-platform-verifier; aws-lc) | **`--native-tls` deprecated → `--system-certs`** (same behavior) |

## Checking your version

Check what you are running:

```
uv --version          # e.g. uv 0.11.2 (02036a8ba 2026-03-26 ...)
uv self version       # uv's own version (since 0.7.0; before that, `uv version`)
```

Note the 0.7.0 split: **`uv version`** now reports/updates the **project's** version, while
**`uv self version`** reports uv's own. On a pre-0.7.0 binary, `uv version` still prints uv's
version.

To upgrade a standalone (installer-based) uv:

```
uv self update        # updates the standalone binary in place
```

The current released line is **0.11.x** (latest `0.11.20`); **bedrock is 0.4.0** (August 2024),
the floor below which everything is treated as long-standing. Because uv is **`0.x`**, a minor
bump can both add features *and* break behavior — so the "Min version" column is a hard floor
(a feature tagged `0.8.13+` is not present on 0.7.x), and you should also scan the
[Breaking / renamed](#breaking--renamed-across-0x-minors) section before jumping minors.
