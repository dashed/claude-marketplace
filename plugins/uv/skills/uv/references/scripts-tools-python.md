# uv Scripts, Tools & Python Reference

The three "single-file / standalone" surfaces of uv that sit beside the project workflow:
**PEP 723 scripts** (`uv run script.py` with inline dependency metadata and ephemeral envs),
**tools** (`uvx` / `uv tool` — pipx-style isolated CLI installs), and **Python toolchain
management** (`uv python` — downloading and pinning CPython/PyPy/GraalPy). It closes with the
low-level **`uv venv`** for ad-hoc virtual environments.

> **Verification & version annotations.** Every command, flag, and behavior below was confirmed
> against the installed **`uv 0.11.2`** (`uv <cmd> --help` plus live `/tmp` sandbox runs on
> 2026-06-11). Features at or before **uv 0.4.0** are **bedrock** and left unannotated; only
> additions in 0.5.0→0.11.x carry a `(uv 0.X+)` tag, sourced from the uv `CHANGELOG`. uv is a
> `0.x` project, so breaking changes land in **minor** bumps — confirm your build with
> `uv --version` (or `uv self version`, itself `0.7.0+`).

## Table of Contents

- [PEP 723 inline-metadata scripts](#pep-723-inline-metadata-scripts)
- [Tools (`uvx` / `uv tool`)](#tools-uvx--uv-tool)
- [Python version management (`uv python`)](#python-version-management-uv-python)
- [Ad-hoc virtual environments (`uv venv`)](#ad-hoc-virtual-environments-uv-venv)
- [Gotchas](#gotchas)

---

## PEP 723 inline-metadata scripts

A single `.py` file can declare its own dependencies and Python requirement in a TOML block
embedded in a comment. `uv run` reads that block, builds an **ephemeral** environment with those
deps, and runs the script — no project, no `pyproject.toml`, no manual venv.

### The inline block

The metadata lives in a `# /// script` … `# ///` comment, with each line prefixed by `# `:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich", "requests<3"]
# ///
import requests
from rich import print
print(requests.__version__)
```

- **`dependencies` must be present** — use `[]` for a no-dependency script. A no-dependency
  script creates **no environment** at all (uv runs it against a bare interpreter).
- **`requires-python`** selects (and, if managed and missing, downloads) the interpreter. uv picks
  the latest compatible managed Python — e.g. a `>=3.12` script resolves to 3.13 if that is the
  newest installed/available managed CPython.
- Inside a project directory, a script **with** an inline block is still run **isolated**: project
  dependencies are ignored and you do **not** need `--no-project`.

### Running a script

```bash
uv run demo.py                       # ephemeral env from the inline block, then run
uv run demo.py arg1 arg2             # trailing args pass through to the script
uv run -s demo.py                    # -s/--script forces script interpretation
uv run --gui-script demo.pyw         # run as a Windows GUI script (pythonw)
uv run - <<'EOF'                     # read the script from stdin
print("hi")
EOF
```

`-s`/`--script` is the explicit form when the filename alone wouldn't be treated as a script;
`--gui-script` is its GUI counterpart. (`uv run --script` flag: `uv 0.4.19+`.)

### Managing the inline metadata

Let uv edit the block for you rather than hand-writing TOML:

```bash
uv init --script demo.py --python 3.12   # scaffold a new script + empty block  (uv 0.4.17+)
uv add --script demo.py "requests<3"     # insert/merge a dep (kept alphabetized, multiline)
uv add --index URL --script demo.py pkg  # also writes a commented [[tool.uv.index]] block
uv remove --script demo.py requests      # drop a dep from the block
```

Verified: `uv add --script` rewrites the block as a multiline, sorted list, e.g.

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests<3",
# ]
# ///
```

### Ad-hoc dependencies (without editing the file)

```bash
uv run --with rich demo.py                       # add a dep just for this run (-w/--with)
uv run --with "httpx>=0.27" --with rich demo.py  # repeatable; constraints allowed
uv run --with-requirements extra.txt demo.py     # pull deps from a requirements file
uv run --with-editable ../mylib demo.py          # inject a local package in editable mode
```

`--with` deps are layered on top of whatever the inline block (or project) already provides.

### Shebang — make the script directly executable

```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = []
# ///
print("runs via ./script.py after chmod +x")
```

```bash
chmod +x script.py
./script.py
```

The `env -S` splits the single argument so `uv run --script` is passed correctly. (Verified
end-to-end on 0.11.2.)

### Script lockfiles, export & tree `(uv 0.5.17+)`

A PEP 723 script can have its own lockfile for reproducible runs:

```bash
uv lock --script demo.py        # writes demo.py.lock ADJACENT to the script  (uv 0.5.17+)
uv run --script demo.py         # subsequent runs reuse demo.py.lock if present
uv add --script demo.py rich    # add/lock updates demo.py.lock too
uv export --script demo.py      # requirements-style output for the script    (uv 0.5.17+)
uv tree --script demo.py        # dependency tree for the script              (uv 0.5.17+)
uv python find --script demo.py # print the interpreter uv would use
```

Verified: `uv lock --script demo.py` produces a `demo.py.lock` (~25 KB for a `requests` script)
sitting next to the source file; `uv export --script` emits a hash-pinned requirements listing.

### Reproducibility — `exclude-newer`

Pin resolution to a point in time by adding a `[tool.uv]` sub-table to the inline block, so the
script resolves the same set of versions regardless of newer releases:

```python
# /// script
# dependencies = ["requests"]
#
# [tool.uv]
# exclude-newer = "2023-10-16T00:00:00Z"
# ///
```

`exclude-newer` ignores any distribution published after the given RFC 3339 timestamp (a bare
`YYYY-MM-DD` date is also accepted). The same effect is available per-invocation with the
`--exclude-newer DATE` flag on `uv run`/`uv lock`.

---

## Tools (`uvx` / `uv tool`)

Tools are Python CLIs (ruff, httpie, black, …) run from **isolated** environments — uv's answer
to pipx. **`uvx` is exactly `uv tool run`.** Both prefer an already-installed version of the tool
over re-fetching it.

### One-off runs with `uvx`

```bash
uvx ruff check .                       # ephemeral isolated env, run ruff, discard
uvx --from httpie http GET example.com # command name != package name → use --from
uvx ruff@0.6.0 check                   # pin an EXACT version (@version)
uvx ruff@latest check                  # always use the newest release
uvx --with mkdocs-material mkdocs build  # inject a plugin/extra into the tool's env
uvx --isolated black --version         # ignore any installed tool, force a fresh env
```

- **`@`-syntax pins an exact version only** (`ruff@0.6.0`, `ruff@latest`). For a *range*
  (`'ruff>=0.6,<0.7'`) you must use `--from`.
- **`--from`** also disambiguates when the executable's name differs from the distribution name
  (the classic `httpie` → `http` case), and accepts sources (`--from git+https://…`).

### Persistent installs with `uv tool install`

Installs **all** of a package's entry points onto your `PATH` (in `~/.local/bin`):

```bash
uv tool install ruff                       # install onto PATH
uv tool install 'httpie>0.1.0'             # version constraint (no --from needed here)
uv tool install ruff@0.6.0                 # exact pin
uv tool install git+https://github.com/…   # from a Git/URL/local source
uv tool install mkdocs --with mkdocs-material   # -w/--with: bundle plugins into the env
uv tool install -e ./mypkg                 # -e/--editable: editable install
uv tool install ruff --force               # overwrite a clashing (non-uv) executable
```

Other install flags: `--with-executables-from PKG` (also expose another package's entry points),
`--with-requirements FILE`, `-c/--constraints FILE`, `-b/--build-constraints FILE`.

### Upgrade, list, uninstall

```bash
uv tool upgrade ruff          # upgrade one tool, RESPECTING its original constraints/settings
uv tool upgrade --all         # upgrade every installed tool
uv tool list                  # list installed tools and their entry points
uv tool list --outdated       # also show which are out of date
uv tool list --show-paths --show-version-specifiers --show-with --show-python
uv tool uninstall ruff        # remove one tool
uv tool uninstall --all       # remove all tools
```

- **Upgrade semantics:** `uv tool upgrade` respects the version constraints and settings the tool
  was installed with — it upgrades *within* them. To **change** the constraints, re-run
  `uv tool install`. `uv tool upgrade` accepts `--python` (re-pin the interpreter) and resolver
  knobs (`--index`, `--exclude-newer`), but on 0.11.2 it has **no** `--upgrade-package` or
  `--reinstall` flags.
- `uv tool list` display flags: `--show-paths`, `--show-version-specifiers`, `--show-with`,
  `--show-extras`, `--show-python`, `--outdated`.

### Tool directories & PATH

```bash
uv tool dir          # → ~/.local/share/uv/tools   (one venv per installed tool)
uv tool dir --bin    # → ~/.local/bin              (where entry points are linked)
uv tool update-shell # ensure the tool bin dir is on PATH (edits your shell profile)
```

(Verified on 0.11.2: `uv tool dir` → `~/.local/share/uv/tools`, `--bin` → `~/.local/bin`.) Override
with `UV_TOOL_DIR` / `UV_TOOL_BIN_DIR`. If freshly-installed tools aren't found, run
`uv tool update-shell` and restart the shell.

### Tool interpreter selection

`--python X.Y` pins the interpreter for a tool's environment. Tool environments are **global** and
**ignore** project-scoped Python requests — a local `.python-version` or a project's
`requires-python` does **not** influence which interpreter a tool runs on.

---

## Python version management (`uv python`)

uv downloads and manages standalone interpreters (Astral's
[`python-build-standalone`](https://github.com/astral-sh/python-build-standalone) CPython builds,
PyPy from PyPy upstream, GraalPy `(uv 0.7.3+)`, Pyodide/WASM). Subcommands:

```
list  install  upgrade  find  pin  dir  uninstall  update-shell
```

### Install

```bash
uv python install 3.12 3.13          # download one or more managed versions
uv python install 3.12.7             # an exact patch
uv python install '>=3.10,<3.12'     # a specifier
uv python install pypy@3.10          # a specific implementation
uv python install 3.13 --default     # also create `python`/`python3` shims (experimental)
```

Install flags: `--default` (experimental — installs unversioned `python`/`python3` shims),
`-r/--reinstall`, `-f/--force`, `-U/--upgrade` (upgrade to the latest patch), `-i/--install-dir`,
`--mirror` / `--pypy-mirror`, `--compile-bytecode`. The exact patch versions offered are **frozen
per uv release**.

### List

```bash
uv python list                       # installed (with resolved paths) + <download available>
uv python list --all-versions        # every patch, not just the latest per minor
uv python list --only-installed      # hide downloadable entries
uv python list --all-platforms --all-arches
```

Output shows variants inline: `+freethreaded`, `pypy-`, `graalpy-` (verified — e.g.
`cpython-3.14.3+freethreaded-…`, `pypy-3.11.15-…`). Other flags: `--only-downloads`,
`--show-urls`, `--output-format`.

### Find

```bash
uv python find                       # print the interpreter uv would use here
uv python find --script demo.py      # the interpreter for a PEP 723 script
uv python find '>=3.12'              # the path satisfying a request
uv python find --system              # only consider system interpreters
```

Flags: `--script`, `--system`, `--show-version`, `--resolve-links`, `--no-project`.

### Pin (`.python-version`)

```bash
uv python pin 3.12       # write `.python-version` in the cwd
uv python pin --global 3.12   # write the user-level default pin     (uv 0.6.7+)
uv python pin --rm       # remove the pin                            (uv 0.7.12+)
uv python pin --resolved 3.12 # write the resolved interpreter path, not the request
```

`.python-version` is discovered in the current and **parent** directories (the parent-dir search
is a `0.5.0` change). `--no-project` skips validating the pin against the project's
`requires-python`.

### Upgrade `(uv 0.10.0+, preview since 0.7.14)`

```bash
uv python upgrade        # upgrade managed CPython to the latest PATCH
uv python upgrade 3.12   # upgrade just the 3.12 line
```

- **Patch-only:** moves `3.13.4 → 3.13.5`; it **never** crosses a minor (won't take 3.12 → 3.13).
- Virtual environments created against a *minor* request (e.g. `3.13`) **auto-track** the new patch
  via a minor-version symlink directory; venvs pinned to an explicit patch (`3.13.4`) do not.
- Applies to **uv-managed CPython only**. (Stabilized in `uv 0.10.0`; was a preview feature from
  `0.7.14`.)

### Uninstall & dir

```bash
uv python uninstall 3.12     # remove a managed version
uv python uninstall --all
uv python dir                # → ~/.local/share/uv/python
uv python dir --bin          # → ~/.local/bin
```

### Request forms

A "Python request" can be any of:

| Form | Example |
|------|---------|
| Major / minor / patch | `3`, `3.12`, `3.12.3` |
| Version specifier | `>=3.12,<3.13` |
| Free-threaded | `3.13t`, `3.13+freethreaded` |
| Debug / GIL toggles | `3.12.0+debug`, `3.13d`, `3.14+gil` |
| Implementation | `cpython`/`cp`, `pypy`/`pp`, `graalpy`/`gp`, `pyodide` |
| Implementation + version | `pypy@3.10`, `pypy-3.10` |
| Full key | `cpython-3.12.3-macos-aarch64-none` |

**Free-threaded builds:** Python **3.13 requires the explicit `3.13t`** opt-in; **3.14+ can be used
without explicit opt-in** (the GIL build is still preferred; force a GIL build with `+gil`) — this
relaxation landed in `uv 0.9.0`.

### Settings & discovery

- **`python-downloads`** (`UV_PYTHON_DOWNLOADS`): `automatic` (default) / `manual` / `never`. The
  `--no-python-downloads` flag is equivalent to `never`.
- **`python-preference`** (`UV_PYTHON_PREFERENCE`): `managed` (default) / `only-managed`
  (= `--managed-python` `(uv 0.6.8+)`) / `system` / `only-system` (= `--no-managed-python`).
- **Discovery order:** uv-managed install directory → `python` / `python3` / `python3.x` on `PATH`
  → (Windows) the registry / Microsoft Store; if none satisfies the request and downloads are
  allowed, uv downloads a managed build.
- **How `uv run --python X` resolves:** `--python` (or `UV_PYTHON`) sets the request; uv finds an
  existing interpreter matching it per the discovery order above, otherwise downloads a managed one
  (subject to `python-downloads`/`python-preference`). Verified: a `>=3.12` script resolved to the
  newest managed 3.13.
- **Env vars:** `UV_PYTHON`, `UV_PYTHON_INSTALL_DIR`, `UV_PYTHON_DOWNLOADS`,
  `UV_MANAGED_PYTHON` / `UV_NO_MANAGED_PYTHON`.

---

## Ad-hoc virtual environments (`uv venv`)

For pip-style / non-project work, create a plain virtual environment:

```bash
uv venv                       # create .venv in the cwd (the default name)
uv venv myenv                 # create at a custom path
uv venv --python 3.12         # -p/--python: use (and download on demand) a specific version
uv venv --seed                # also install pip/setuptools/wheel into the env  (env: UV_VENV_SEED)
uv venv --clear               # -c/--clear: overwrite an existing env at the path
```

Other flags: `--system-site-packages`, `--relocatable` (`UV_VENV_RELOCATABLE`), `--prompt PREFIX`,
`--allow-existing`, `--no-project`, plus index / `--exclude-newer` / `--link-mode` resolver options.
`--seed` installs `pip`, `setuptools`, and `wheel` for environments that need a real `pip`.

### Activation vs. `uv run` (and `VIRTUAL_ENV` discovery)

You generally do **not** need to activate the venv:

```bash
source .venv/bin/activate     # classic activation (sets VIRTUAL_ENV) — optional
uv run python script.py       # or: just use uv run, which auto-detects .venv
uv pip install requests       # uv pip also auto-detects .venv
```

`uv run` and `uv pip` **auto-detect** the environment by walking the current and parent directories
for a `.venv`, or by honoring an active `VIRTUAL_ENV`. Discovery precedence: **`VIRTUAL_ENV` →
`CONDA_PREFIX` → a `.venv` in cwd/parents**.

**When to use what:** reach for `uv venv` + `uv pip` for ad-hoc or pip-migration work; for actual
projects, prefer the managed workflow (`uv init`/`add`/`sync`/`run`), where uv creates and keeps
`.venv` in sync for you automatically.

---

## Gotchas

- **`dependencies` is mandatory in a PEP 723 block** — omit it and uv won't treat the comment as a
  script block. Use `dependencies = []` for a no-dep script (which then runs with **no** env).
- **`@` pins are exact only.** `uvx ruff@0.6.0` works; for a range use
  `uvx --from 'ruff>=0.6,<0.7' ruff`. Likewise `uv tool install ruff@0.6.0` vs.
  `uv tool install 'ruff>0.6'`.
- **`--from` when the command ≠ the package.** `uvx --from httpie http …`, not `uvx http …`. The
  tool's *executable* name and its *distribution* name can differ.
- **`uv tool upgrade` respects original constraints.** It upgrades within the version range you
  installed with; to widen/narrow that range, re-run `uv tool install`. There is no
  `--upgrade-package`/`--reinstall` on `upgrade` in 0.11.2.
- **Tool envs ignore project Python.** A `.python-version` or a project's `requires-python` does not
  affect the interpreter a tool runs on; use `uv tool install --python X.Y` to pin it.
- **Installed tools not on PATH?** Run `uv tool update-shell` and restart your shell (entry points
  live in `~/.local/bin`).
- **`uv python upgrade` is patch-only** and managed-CPython-only — it will not jump minor versions
  and won't touch system Python.
- **Free-threaded 3.13 needs `3.13t`;** plain `3.13` gives the GIL build. From 3.14 the free-threaded
  variant is available without the explicit `t`.
- **`uv venv` won't clobber silently.** As of `uv 0.10.0` it requires `--clear` (or
  `--allow-existing`) to reuse/overwrite an existing path.
