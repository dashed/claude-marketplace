---
name: uv
description: uv — Astral's single, fast (Rust) binary that replaces pip, pip-tools, pipx, pyenv, poetry/pdm, and virtualenv for Python packaging and project management. Use when managing a Python project with `pyproject.toml` + a universal `uv.lock` (`uv init/add/remove/sync/lock/run`), running PEP 723 inline-metadata scripts (`uv run script.py`), running one-off tools with `uvx` or installing them with `uv tool install`, installing/pinning Python versions (`uv python install/pin/list`), using `uv pip` as a faster drop-in pip/pip-tools replacement, creating venvs (`uv venv`), or building/publishing packages (`uv build`/`uv publish`). Triggers on mentions of uv, the `uv` command, `uvx`, `uv.lock`, `tool.uv`, `uv add/sync/run`, PEP 723 `# /// script` blocks, or "fast Python package manager". This is the **uv CLI by Astral** — NOT ruff (linter/formatter) or ty (type checker), which are separate Astral tools, and NOT poetry/pip/pyenv themselves.
---

# uv - Python Package & Project Manager

## Overview

uv is **a single, fast (Rust) binary** from Astral that replaces the whole Python tooling stack —
`pip`, `pip-tools`, `pipx`, `pyenv`, `poetry`/`pdm`, and `virtualenv` — behind one command. It is
**project-centric**: a project is a `pyproject.toml` plus a committed **universal `uv.lock`**
(multi-platform, cross-OS resolution) plus an auto-managed `.venv`, and the everyday commands
auto-sync that environment for you.

**What uv replaces:**

| Replaces | uv surface |
|----------|------------|
| `pip` | `uv pip install/...` (and, in a project, `uv add`) |
| `pip-tools` (`pip-compile`/`pip-sync`) | `uv pip compile` / `uv pip sync`, or `uv lock` / `uv sync` |
| `pipx` | `uv tool install` / `uvx` |
| `poetry` / `pdm` (project mgmt) | `uv init/add/sync/lock/run/build/publish` + `uv.lock` |
| `pyenv` | `uv python install/pin/list` |
| `virtualenv` / `venv` | `uv venv` (auto-managed `.venv` in projects) |

### Mental model (read this first)

uv exposes **four surfaces** over one binary:

1. **Projects** (recommended) — `pyproject.toml` + a **universal `uv.lock`** + an auto-managed
   `.venv`. `uv add/sync/run/lock` operate here; resolution is **platform-independent** (one
   lockfile resolves for every OS/Python). Commit `uv.lock`; `.venv` is gitignored.
2. **Scripts** — **PEP 723** inline-metadata scripts (`# /// script` blocks). `uv run script.py`
   builds an **ephemeral** environment from the script's declared deps and runs it.
3. **Tools** — `uvx` (ephemeral, one-off) and `uv tool install` (persistent, onto PATH) for
   command-line apps like `ruff`, `httpie`, `mkdocs`.
4. **Python** — `uv python install/pin/list` downloads and manages CPython (via Astral's
   `python-build-standalone`) so you never touch a system Python.

There is also a separate **pip interface** (`uv pip ...`): a faster, *mostly* drop-in
pip/pip-tools that operates on the **active / `.venv` environment**, is **platform-specific by
default**, and does **NOT** touch `pyproject.toml` or `uv.lock`. Reach for it when migrating an
existing pip workflow; reach for the project interface for new work.

> **Disambiguation:** This skill is the **uv CLI itself**. **ruff** (linter/formatter) and **ty**
> (type checker) are *separate* Astral tools with their own skills — `uv format` is a (preview) uv
> command that *wraps* Ruff but belongs to uv. uv is a CLI, not an MCP/agent server.

## Prerequisites

**CRITICAL**: verify uv is installed and check the version:

```bash
uv --version          # e.g. "uv 0.11.2 (02036a8ba 2026-03-26 ...)"
uv self version       # same, since 0.7.0 (older uv printed this via `uv version`)
```

**Version note:** This skill is documented against the uv **0.11.x** line (current latest 0.11.20;
examples verified on **0.11.2**). uv is **0.x**, so **breaking changes can land in MINOR bumps** —
features stable at or before **uv 0.4.0** are "bedrock" and shown **unannotated**; later additions
are tagged inline as `(uv 0.X+)` only where sourced. See
[references/version-features.md](references/version-features.md) for the full feature → version map
with CHANGELOG citations. Always confirm on the running build with `uv --version`.

## Install

```bash
# Standalone installer (recommended — macOS/Linux); installs uv into ~/.local/bin
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip / pipx / Homebrew
pip install uv            # pipx install uv ; brew install uv

uv --version
uv self update            # update a standalone-installed uv
```

The standalone installer puts uv in `~/.local/bin` (since uv 0.5.0; it was `~/.cargo/bin` before).

## Core Workflows

All examples below were verified on uv 0.11.2.

### 1. New project + add a dependency + run

```bash
uv init demo --python 3.13   # pyproject.toml, main.py, README.md, .python-version, .git
cd demo
uv add requests              # adds requests>=X to [project.dependencies], updates uv.lock, syncs .venv
uv run python -c "import requests; print(requests.__version__)"
uv run main.py
```

`uv add` writes a lower-bound (e.g. `requests>=2.34.2`), re-resolves `uv.lock`, and installs into
`.venv` automatically — no manual activation. `uv remove PKG` reverses it. Variants of `uv init`:
`--app` (default, flat), `--package`/`--lib` (packaged, gets a `[build-system]`), `--script`
(a standalone PEP 723 script), `--bare` (just `pyproject.toml`).

### 2. PEP 723 inline-metadata script

```bash
cat > demo.py <<'EOF'
# /// script
# requires-python = ">=3.11"
# dependencies = ["cowsay"]
# ///
import cowsay; cowsay.cow("hi from uv")
EOF

uv run demo.py                       # auto-creates an ephemeral env with cowsay, runs
uv add --script demo.py "requests<3" # edit the inline block without hand-writing TOML
```

`uv run` builds an ephemeral environment from the script's declared deps (a script with no deps
creates no env). Make it self-running with the shebang `#!/usr/bin/env -S uv run --script` then
`chmod +x`. You can also lock a script: `uv lock --script demo.py` writes a `demo.py.lock`
adjacent (uv 0.5.17+).

### 3. uvx one-off tools

```bash
uvx ruff check .                       # ephemeral; uvx == `uv tool run`
uvx --from httpie http GET example.com # when the command name != the package name
uvx ruff@0.6.0 check                   # pin an exact version (@version / @latest)
uv tool install ruff                   # persistent install onto PATH (~/.local/bin)
uv tool list ; uv tool upgrade --all   # list / upgrade installed tools (keeps original constraints)
```

`uvx` runs a tool in a throwaway isolated env; `uv tool install` persists it. Inject plugins with
`--with` (`uvx --with mkdocs-material mkdocs`).

### 4. Install / pin Python versions

```bash
uv python install 3.12 3.13   # download managed CPython(s)
uv python list                # installed + downloadable (incl. +freethreaded / pypy- / graalpy-)
uv python pin 3.12            # writes .python-version (--global for the user-wide default)
uv run python --version       # uses the pinned/managed Python, downloading on demand
```

uv downloads CPython from Astral's `python-build-standalone` — no system Python or pyenv required.
`uv python upgrade 3.13` does **patch** upgrades only (uv 0.10.0+).

### 5. Migrate from pip (the `uv pip` interface)

```bash
uv venv                                 # create .venv (no activation needed for uv pip / uv run)
uv pip install -r requirements.txt
uv pip compile requirements.in -o requirements.txt   # replaces pip-compile
uv pip sync requirements.txt            # exact env match (removes extraneous) — replaces pip-sync
uv pip list ; uv pip freeze
```

`uv pip` operates on the active / discovered `.venv`, **not** a uv project — it never touches
`pyproject.toml` or `uv.lock`, and it ignores `pip.conf` / `PIP_*` (it reads `UV_*` instead).
For non-venv targets pass `--system` or `--python PATH`.

### 6. Lock & sync in CI

```bash
uv sync --frozen          # install exactly from uv.lock; do NOT re-resolve
uv lock --check           # assert the lockfile is up to date (fail CI if not)
uv run --frozen pytest    # run without re-resolving or re-syncing
uv cache prune --ci       # shrink the cache for caching between CI runs
```

`uv.lock` is **universal** (one resolution covers all platforms) and only goes "out of date" when
`pyproject.toml` changes — new upstream releases do **not** invalidate it (update deliberately with
`uv lock --upgrade` / `uv lock --upgrade-package PKG`). Set and persist `UV_CACHE_DIR` across CI
runs. Note that on `uv lock` itself the flags are `--check` / `--check-exists`; `--frozen` /
`--locked` live on the consuming commands (`sync`, `run`, `add`).

## Other useful commands

- **`uv tree`** — show the dependency tree (`--depth N`, `--invert` for reverse deps, `--outdated`).
- **`uv export`** — emit `uv.lock` to another format: `uv export --format requirements.txt -o requirements.txt`
  (also `pylock.toml`). uv recommends *not* maintaining both `uv.lock` and `requirements.txt`.
- **`uv build`** — build sdist + wheel into `dist/`; pre-publish use `uv build --no-sources`.
- **`uv publish`** — upload to PyPI (token via `-t`/`UV_PUBLISH_TOKEN`) or via GitHub Actions
  trusted publishing (`--trusted-publishing automatic`).
- **`uv version`** *(uv 0.7.0+)* — read/set the **project** version (`uv version --bump patch`,
  `--dry-run`). Before 0.7.0 this printed uv's own version (now `uv self version`).
- **`uv auth`** *(uv 0.8.15+)* — manage private-index credentials (`login`/`logout`/`token`).
- **`uv format`** *(preview, uv 0.8.13+)* — experimental Python formatter wrapping Ruff; still a
  preview feature in 0.11.x — don't rely on it as a stable everyday command.
- **`uv audit`** *(preview, uv ~0.10.10+)* — OSV vulnerability scan; preview, surface verifying.

## Quick Reference

| Task | Command |
|------|---------|
| New project | `uv init [--app\|--lib\|--package\|--script]` |
| Add / remove dep | `uv add PKG` / `uv remove PKG` |
| Dev / group dep | `uv add --dev PKG` / `uv add --group test PKG` |
| Install env from lock | `uv sync` (exact) |
| Update lockfile | `uv lock` / `uv lock --upgrade[-package PKG]` |
| Assert lock fresh (CI) | `uv lock --check` |
| Run in project env | `uv run CMD` (auto-syncs) |
| Run a PEP 723 script | `uv run script.py` |
| One-off tool | `uvx TOOL` |
| Install a tool | `uv tool install TOOL` |
| Manage Python | `uv python install / list / pin` |
| Make a venv | `uv venv [--python 3.12]` |
| Build / publish | `uv build` / `uv publish` |
| Dependency tree | `uv tree` |
| Export requirements | `uv export --format requirements.txt -o requirements.txt` |
| pip compatibility | `uv pip install / compile / sync / list / freeze` |
| Cache | `uv cache dir / clean / prune` |
| Bump project version | `uv version --bump patch` *(uv 0.7.0+)* |

## Troubleshooting

- **"No virtual environment found" (uv pip)** — run `uv venv` first, or pass `--system`. `uv pip`
  needs an environment; the **project** commands manage `.venv` for you, so prefer `uv add`/`uv run`.
- **Lockfile out of date** — `uv lock` (or `uv sync`, which re-locks). `--locked` / `--frozen`
  *error* instead of re-locking — use them in CI to fail on drift.
- **Wrong Python picked** — `uv python pin X.Y`, or `--python X.Y` per command, or set `UV_PYTHON`.
  Inspect the resolved interpreter with `uv python find`.
- **Avoid auto-sync on `uv run`** — pass `--no-sync` or `--frozen`.
- **Stale cached package** — `uv ... --refresh` (preferred over `--no-cache`); `--reinstall` to
  force reinstall.
- **`uv version` prints/sets the wrong thing** — since uv 0.7.0 `uv version` is the **project**
  version; use `uv self version` for uv's own version.
- **`uv format` / `uv audit` "not stable"** — both are **preview** features; behavior and flags
  can change. Don't bake them into stable pipelines.
- **Private index auth** — set `UV_INDEX_<NAME>_USERNAME` / `_PASSWORD`, use `~/.netrc`, or
  `--keyring-provider subprocess`; or manage credentials with `uv auth` (uv 0.8.15+).
- **Building before publish** — `uv build --no-sources` builds as a *consumer* would (ignoring
  `tool.uv.sources`), catching deps that only resolve locally.

## References

For exhaustive detail, see the bundled reference files:

- [references/projects.md](references/projects.md) — the project interface: `uv init` variants,
  `uv add`/`remove` (sources: git/url/path/index/workspace), `sync`/`lock`/`run`, dependency groups
  (PEP 735) vs extras, workspaces, `uv version`, `uv build`/`publish`, `requires-python`, and the
  universal `uv.lock` model.
- [references/scripts-tools-python.md](references/scripts-tools-python.md) — PEP 723 scripts (inline
  metadata, script lockfiles, shebangs), tools (`uvx` / `uv tool`), Python version management
  (`uv python`, request forms, free-threaded, downloads/preference), and `uv venv`.
- [references/pip-config.md](references/pip-config.md) — the `uv pip` interface and its deviations
  from pip, caching, configuration discovery & precedence, the `UV_*` environment-variable table,
  indexes / authentication / resolution, `--torch-backend`, and platform/Python pinning.
- [references/version-features.md](references/version-features.md) — feature → minimum-version map
  with CHANGELOG citations (what's bedrock ≤0.4 vs. added in 0.5–0.11), plus notable breaking
  changes by minor release.

## Resources

- **Help**: `uv help`, `uv <command> --help`
- **Docs**: https://docs.astral.sh/uv/
- **Source / releases**: https://github.com/astral-sh/uv
