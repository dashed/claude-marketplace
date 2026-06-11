# uv Projects Reference

The practical reference for the **uv project interface**: a `pyproject.toml` + a committed
**universal `uv.lock`** + an auto-managed `.venv`. Covers `uv init`, `uv add`/`remove`,
`uv sync`, `uv lock`, `uv run`, `uv tree`, `uv export`, dependency groups vs extras,
workspaces, `uv version`, and `uv build`/`uv publish`. For PEP 723 scripts, tools (`uvx`),
and Python version management see [scripts-tools-python.md](scripts-tools-python.md); for the
`uv pip` interface, indexes, caching, and configuration see [pip-config.md](pip-config.md).

> **Version annotations.** uv is a `0.x` tool, so **breaking changes land in MINOR bumps**.
> Features at or before **uv 0.4.0** are treated as long-standing and left unannotated; later
> additions carry a `(uv 0.X+)` tag. Everything here was **verified against the installed
> `uv 0.11.2` binary** (`uv <cmd> --help` plus `/tmp` sandboxes) on 2026-06-11 unless a note
> says otherwise. Flag sets change between releases — confirm with `uv --version` and
> `uv <cmd> --help`, and never assume a flag exists.

## Contents

- [The project model](#the-project-model)
- [`uv init`](#uv-init)
- [`uv add` / `uv remove`](#uv-add--uv-remove)
- [Dependency sources (`[tool.uv.sources]`)](#dependency-sources-tooluvsources)
- [`uv sync`](#uv-sync)
- [`uv lock`](#uv-lock)
- [`uv run`](#uv-run)
- [`uv tree`](#uv-tree)
- [`uv export`](#uv-export)
- [Dependency groups (PEP 735) vs extras](#dependency-groups-pep-735-vs-extras)
- [Workspaces](#workspaces)
- [`uv version`](#uv-version)
- [`uv build`](#uv-build)
- [`uv publish`](#uv-publish)
- [`requires-python` and universal resolution](#requires-python-and-universal-resolution)
- [The `uv.lock` model](#the-uvlock-model)

---

## The project model

A uv **project** is a directory with a `pyproject.toml`. uv resolves the whole dependency set
into a single **universal `uv.lock`** (one lockfile, all platforms) and materialises it into an
auto-managed `.venv`. The mutating project commands — `uv add`, `uv remove`, `uv sync`,
`uv run`, `uv version` — **lock and sync automatically** before acting, so you rarely call
`uv lock` or `uv sync` by hand.

- **Commit `uv.lock`**; `.venv` is gitignored and rebuilt on demand.
- `uv.lock` is uv-specific (not consumable by pip/other tools) — emit interop formats with
  `uv export`.
- The `uv pip` interface is a separate world: it operates on the active/`.venv` environment and
  never touches `pyproject.toml` or `uv.lock` (see [pip-config.md](pip-config.md)).

## `uv init`

Creates a new project. The **default is an application** (`--app`): a flat layout with **no
`[build-system]`**, so the project itself is not installed — only its dependencies are. A
default `uv init demo` creates `pyproject.toml`, `main.py`, `README.md`, `.python-version`,
plus `.git`/`.gitignore`.

| Variant | Effect |
|---|---|
| `--app` (default) | Flat application, no build-system, `main.py` entry script |
| `--package` | Packaged app: `src/<mod>/__init__.py`, a `[build-system]` (uv_build), a `[project.scripts]` entry point |
| `--lib` | Library (implies `--package`); adds `py.typed` and a `hello()` API function |
| `--script` | A standalone PEP 723 script — **not** a project (see [scripts-tools-python.md](scripts-tools-python.md)) |
| `--bare` | Only `pyproject.toml` — no `README`, `.python-version`, VCS, or `src/` |

```bash
uv init demo --python 3.13     # app: pyproject + main.py + README + .python-version + .git
uv init mylib --lib            # src-layout library, packaged, py.typed
uv init mytool --package       # packaged app with a console-script entry point
uv init --bare                 # just a pyproject.toml in the current dir
```

> **Verified on 0.11.2:** `uv init demo --python 3.13` produces the five files above; `uv init
> --bare app1` produces a directory containing only `pyproject.toml`.

**Other flags:** `--name <NAME>`, `-p`/`--python <VER>`, `--vcs <git|none>` (note: it is
`--vcs none`, there is **no** `--no-vcs`), `--build-backend <uv|hatch|flit|pdm|poetry|setuptools|maturin|scikit>`
(env `UV_INIT_BUILD_BACKEND`), `--no-readme`, `--no-pin-python`, `--no-workspace`,
`--description <TEXT>`/`--no-description`, `--author-from <auto|git|none>`, `--package`/`--no-package`.
The `maturin` and `scikit` backends scaffold **extension-module** projects (imply `--package`,
add Cargo/C scaffolding and `tool.uv.cache-keys`).

**Skew to expect:** the generated `uv_build` build-system pin tracks the running uv version
(`uv_build>=0.11.2,<0.12.0` on this box), and the generated `requires-python` reflects the
Python uv resolved for the project.

## `uv add` / `uv remove`

`uv add` appends to `[project.dependencies]` with a **lower bound** (`requests>=2.34.2`),
re-locks, and syncs `.venv` automatically. `--bounds <lower|major|minor|exact>` controls the
bound style; `--raw` adds the requirement verbatim with no auto-bound. Inline PEP 508
constraints work directly: `uv add "httpx>=0.20,<0.28"`.

```bash
uv add requests                      # → requests>=X in [project.dependencies], locks + syncs
uv add "httpx>=0.20"                 # explicit constraint
uv add --dev pytest ruff             # dev dependency group
uv add --group docs mkdocs           # named PEP 735 group
uv add --optional cli rich           # → [project.optional-dependencies] extra "cli"
uv add "jax; sys_platform=='linux'"  # platform marker (or -m/--marker)
uv remove requests                   # remove + re-lock + sync; prunes its source entry
```

**Target tables:**

| Flag | Writes to |
|---|---|
| (default) | `[project.dependencies]` |
| `--dev` | the `dev` dependency group (== `--group dev`) — PEP 735 `[dependency-groups]` |
| `--group <NAME>` | the named dependency group |
| `--optional <EXTRA>` | `[project.optional-dependencies]` under that extra |
| `--extra <EXTRA>` | enables extras **on the dependency being added** (e.g. `flask[dotenv]`) |
| `-m`/`--marker <MARKER>` | applies an environment marker to the added requirements |

**Other flags:** `--no-sync` (env `UV_NO_SYNC` — edit files but don't install), `--frozen`
(env `UV_FROZEN` — add without re-locking), `--locked` (env `UV_LOCKED` — assert the lock won't
change), `-r`/`--requirements <FILE>`, `-c`/`--constraints <FILE>` (env `UV_CONSTRAINT`),
`--package <PKG>` (target a workspace member), `--script <SCRIPT>` (add to a PEP 723 script
instead of the project), `-U`/`--upgrade`, `-P`/`--upgrade-package <PKG>`, `--editable`,
`--no-sources`. `uv remove` mirrors the target/source flags and **prunes the `[tool.uv.sources]`
entry** when no longer referenced.

## Dependency sources (`[tool.uv.sources]`)

uv resolves a requirement from a non-default location by recording it in `[tool.uv.sources]`.
The `[project.dependencies]` entry stays standards-compliant (publishable); the source is a
uv-only override.

| Source | Command | Notes |
|---|---|---|
| **Git** | `uv add git+https://github.com/encode/httpx` | add `--rev`/`--tag`/`--branch`; `--lfs` (env `UV_GIT_LFS`); `#subdirectory=...` for monorepos |
| **URL** | `uv add "https://files.example.com/pkg-0.27.0.tar.gz"` | direct sdist/wheel URL |
| **Path** | `uv add ./pkg-1.0-py3-none-any.whl` or `uv add ../bar/` | not editable by default; `--editable`/`--no-editable`. A source with `package = false` installs only its dependencies (a "virtual" dependency) |
| **Index** | `uv add torch --index pytorch=https://download.pytorch.org/whl/cpu` | writes `[[tool.uv.index]]` + `torch = { index = "pytorch" }`; `explicit = true` confines an index to packages that name it |
| **Workspace** | `uv add --workspace ../sibling` | inter-member dependency, **always editable** |

```toml
[tool.uv.sources]
httpx   = { git = "https://github.com/encode/httpx", tag = "0.27.0" }
mylib   = { path = "../mylib", editable = true }
torch   = { index = "pytorch" }
shared  = { workspace = true }
```

A source value can be a **list** disambiguated by `marker = "..."` (different source per
platform) or scoped via `extra = "cpu"`. See [pip-config.md](pip-config.md) for named-index
definition and resolution precedence.

## `uv sync`

Brings `.venv` into line with `uv.lock`. **By default** it locks if needed, installs the
project plus its dependencies plus the **`dev` group**, and is **exact** — it *removes*
anything not in the lock. **Extras are not synced by default.**

```bash
uv sync                       # default: project + deps + dev group, exact
uv sync --frozen              # install straight from uv.lock, never re-lock (CI)
uv sync --locked              # error if uv.lock is out of date instead of re-locking (CI)
uv sync --no-dev --extra cli  # skip dev group, include the "cli" extra
uv sync --only-group docs     # just the docs group; excludes project + default groups
```

- **Groups:** `--group <N>`, `--all-groups`, `--no-group <N>`, `--only-group <N>` (that group
  only — excludes the project and default groups), `--no-default-groups`, `--no-dev`,
  `--only-dev`. **Exclusion wins over inclusion.** (There is no `--dev` flag on `uv sync` in
  0.11.2; the `dev` group is on by default — opt out with `--no-dev`.)
- **Extras:** `--extra <E>`, `--all-extras`, `--no-extra <E>`.
- **Extraneous handling:** the default is exact; pass `--inexact` to keep packages that aren't
  in the lock. (There is no explicit `--exact` flag — exact is the default.)
- **Partial installs (Docker layer caching):** `--no-install-project`, `--no-install-workspace`,
  `--no-install-package <PKG>`, `--no-install-local` — each still installs *dependencies*, just
  not the named code. The matching env vars `UV_NO_INSTALL_PROJECT` / `UV_NO_INSTALL_WORKSPACE`
  / `UV_NO_INSTALL_LOCAL` are `(uv 0.11.20+)`.
- **Other:** `--no-editable` (deployable install), `--frozen`, `--locked`, `--dry-run`,
  `--check`, `--output-format <text|json>`, `--all-packages`, `--package <PKG>`,
  `--script <SCRIPT>`, `--active` (prefer the active venv over the project's `.venv`).

## `uv lock`

Creates or updates the universal `uv.lock`. You rarely run it directly (mutating commands
re-lock), but it is the CI assertion command.

```bash
uv lock                       # create/update uv.lock
uv lock --check               # assert the lock is up to date — fails CI if not
uv lock --check-exists        # assert a uv.lock merely exists (don't check freshness)
uv lock --upgrade             # re-resolve, allowing all upgrades
uv lock --upgrade-package requests  # upgrade just one package
uv lock --dry-run             # show what would change without writing
```

> **Flag correction:** on `uv lock` itself the assertion flags are **`--check`** and
> **`--check-exists`** — there is **no** `--locked` or `--frozen` on `uv lock` in 0.11.2.
> `--check` is the equivalent of `--locked` on the consuming commands (`sync`/`run`/`add`).
> `--check-exists` reuses env `UV_FROZEN`.

**Other flags:** `-U`/`--upgrade`, `-P`/`--upgrade-package <PKG[==VER]>`, `--script <SCRIPT>`,
and the resolver knobs `--resolution`, `--prerelease`, `--fork-strategy`, `--exclude-newer`,
`--no-sources` (see [pip-config.md](pip-config.md)).

**Resolution model:** the lock **prefers previously-locked versions** and only changes when a
constraint changes or you pass `--upgrade`. A new upstream release does **not** make the lock
"outdated" — the lock is outdated only when it no longer satisfies `pyproject.toml`.

## `uv run`

Runs a command in the auto-synced project environment (it locks and syncs first, **inexact** by
default so it won't churn your venv).

```bash
uv run main.py                       # run a script in the project env
uv run pytest                        # run an installed tool
uv run --with rich python app.py     # add an ephemeral dependency just for this run
uv run --no-project --with httpie http GET example.com   # one-off, ignore the project
uv run --frozen pytest               # CI: run without re-resolving
```

- **Ephemeral deps:** `-w`/`--with <PKG>` (repeatable; constraints allowed),
  `--with-editable <PATH>`, `--with-requirements <FILE>`.
- **Environment layering:** `--no-project` (ignore the project entirely — pair with `--with`
  for one-offs), `--isolated` (env `UV_ISOLATED` — a fresh throwaway env), `--no-sync` (use the
  venv as-is, don't sync), `--frozen` (don't re-lock), `--locked` (error if the lock is stale),
  `--exact`.
- **Groups/extras:** same family as `uv sync` (`--group`/`--no-group`/`--only-group`/
  `--all-groups`/`--no-default-groups`/`--no-dev`/`--only-dev`/`--extra`/`--all-extras`/
  `--no-extra`). As with sync, there is no `--dev` flag — the `dev` group is on by default.
- **Other:** `-m`/`--module`, `-s`/`--script` and `--gui-script` (force PEP 723 interpretation),
  `--all-packages`/`--package <PKG>`, `--env-file <FILE>`/`--no-env-file` (dotenv loading),
  `--no-editable`, `--active`.

> **Verified on 0.11.2:** `uv run --with <pkg>` resolves and injects the extra dependency for
> the single invocation without touching `pyproject.toml`/`uv.lock`.

## `uv tree`

Renders the project's dependency tree from the lock.

```bash
uv tree                       # full tree
uv tree --depth 1             # direct dependencies only
uv tree --invert --package requests   # who depends on requests (reverse deps)
uv tree --outdated            # annotate packages with newer available versions
```

**Flags:** `-d`/`--depth <N>` (default 255), `--prune <PKG>`, `--package <PKG>`, `--invert`
(reverse dependencies), `--outdated`, `--no-dedupe`, `--show-sizes`, `--universal` (show the
full multi-platform tree), `--script <SCRIPT>`, plus `--group`/`--no-group`/`--only-group`/
`--all-groups`/`--no-default-groups`/`--no-dev`/`--only-dev`.

## `uv export`

Exports `uv.lock` to an interoperable format. Prints to stdout unless you pass
`-o`/`--output-file`.

```bash
uv export --format requirements.txt -o requirements.txt
uv export --format requirements.txt --no-hashes        # leaner output
uv export --format pylock.toml -o pylock.toml          # PEP 751 (uv 0.6.15+)
```

- **`--format <requirements.txt | pylock.toml | cyclonedx1.5>`.** `pylock.toml` (PEP 751) is
  `(uv 0.6.15+)`; `cyclonedx1.5` is a preview SBOM format (use the exact string `cyclonedx1.5`).
- **Trim output:** `--no-hashes`, `--no-annotate`, `--no-header`, `--no-editable`,
  `--no-emit-project`, `--no-emit-workspace`, `--no-emit-local`, `--no-emit-package <PKG>`,
  `--prune <PKG>`.
- **Selection:** the same group/extra family as `uv sync`; `--all-packages`/`--package <PKG>`;
  `--frozen`/`--locked`; `--script <SCRIPT>`.

uv recommends against maintaining both `uv.lock` and a `requirements.txt` — export on demand
(e.g. in CI) rather than committing both.

## Dependency groups (PEP 735) vs extras

Two distinct mechanisms, often confused:

| | **Extras** | **Dependency groups** `(uv 0.4.27+)` |
|---|---|---|
| Table | `[project.optional-dependencies]` | `[dependency-groups]` (PEP 735) |
| Published? | **Yes** — consumer-facing (`pip install pkg[extra]`) | **No** — local-only, never published (dev tooling) |
| Add | `uv add --optional <EXTRA> PKG` | `uv add --group <NAME> PKG` / `uv add --dev PKG` |
| Sync | `--extra`/`--all-extras` | `--group`/`--no-dev`/`--only-group`/… |

- The **`dev` group is special-cased** and synced by default. `--dev` (on `uv add`) is exactly
  `--group dev`.
- Enable groups by default with `[tool.uv] default-groups = ["dev", "docs"]` or
  `default-groups = "all"` `(uv 0.6.8+)`; disable per-run with `--no-default-groups`
  `(uv 0.5.23+)`.
- **Nest** groups with `{ include-group = "lint" }`. Per-group `requires-python` via
  `[tool.uv.dependency-groups]` `(uv 0.7.14+)`.
- The legacy `[tool.uv] dev-dependencies` table merges into `dependency-groups.dev` (slated for
  deprecation — prefer `[dependency-groups]`).
- uv resolves **all groups together** into one lock; genuinely incompatible groups need a
  `[tool.uv] conflicts` declaration.

## Workspaces

A workspace is multiple packages sharing **one `uv.lock`** and one resolution. Declare it on the
root:

```toml
[tool.uv.workspace]
members = ["packages/*"]      # globs allowed
exclude = ["packages/legacy"]
```

- The **root is also a member**. `uv lock` always resolves the **whole workspace**.
- `uv run`/`uv sync` default to the **root** package; target one member with
  `--package <MEMBER>`, or operate on all with `--all-packages`.
- Inter-member dependencies use `{ workspace = true }` in `[tool.uv.sources]` (always editable);
  the member must be listed under `members`.
- A workspace has a **single `requires-python`** — the **intersection** of all members' ranges.
- **Trade-off:** when members need genuinely conflicting requirements or separate virtual
  environments, use path dependencies (`{ path = "packages/x" }`) instead of a workspace — at
  the cost of `uv run --package` no longer targeting them.

## `uv version`

> **Correction `(uv 0.7.0+)`:** `uv version` reports and edits the **project's** version (the
> static `version` in `pyproject.toml`). Before 0.7.0 it printed uv's own version — that moved
> to **`uv self version`** (a breaking change in 0.7.0). Outside a project, `uv version` errors
> and hints to use `uv self version`.

```bash
uv version                    # → "demo 0.1.0"
uv version --short            # → "0.1.0"
uv version --output-format json   # keys: package_name, version, commit_info
uv version 1.0.0              # set an explicit version
uv version --bump minor       # 0.1.0 → 0.2.0
uv version --bump minor --dry-run   # show the change, don't write
```

- **`--bump <major|minor|patch|stable|alpha|beta|rc|post|dev>`** — applied largest-to-smallest
  if combined; an explicit value form `--bump dev=N` is supported `(uv 0.9.9+)`. Pre-release
  bumps (`alpha`/`beta`/`rc`/`post`/`dev`) are `(uv 0.7.21+)`.
- `--dry-run`, `--package <PKG>` (workspace member), `--frozen`, `--no-sync`, `--active`,
  `-U`/`--upgrade`, `-P`/`--upgrade-package`.
- There is no dynamic-version flag — `uv version` reads/writes the **static** `version` field.

> **Verified on 0.11.2:** `uv version --bump minor --dry-run` reports `0.1.0 => 0.2.0` and
> leaves `pyproject.toml` untouched; running `uv version` outside a project errors with the
> `uv self version` hint.

## `uv build`

Builds distributions via the frontend → backend protocol. The default builds an **sdist, then a
wheel from that sdist**, into `dist/`.

```bash
uv build                      # sdist + wheel into ./dist
uv build --wheel              # wheel only
uv build --no-sources         # build as a consumer would — ignore [tool.uv.sources] (pre-publish)
uv build --package mylib      # build one workspace member
```

**Flags:** `--sdist`, `--wheel`, `-o`/`--out-dir <DIR>`, `--package <PKG>`/`--all-packages`,
`[SRC]` positional, `--clear`, `--no-build-logs`, `--force-pep517`,
`-b`/`--build-constraints <FILE>` (env `UV_BUILD_CONSTRAINT`).

**The `uv_build` backend** (`build-backend = "uv_build"`): stable `(uv 0.7.19+)` and the
**default backend** for `uv init --package`/`--lib` `(uv 0.8.0+)` (it was hatchling before).
It is **pure-Python only**. Configure it under `[tool.uv.build-backend]` with keys `module-name`,
`module-root` (default `src`), `namespace`, `data`, `source-include`/`source-exclude`/
`default-excludes`. Use **hatchling** when you need build scripts; **maturin**/**scikit** for
extension modules.

> Always run `uv build --no-sources` before publishing — it builds against the publishable
> metadata as a downstream consumer would see it, rather than your local sources.

## `uv publish`

Uploads built distributions (default target `dist/*`).

```bash
uv publish                                  # upload dist/* to PyPI
uv publish -t "$PYPI_TOKEN"                  # token auth (UV_PUBLISH_TOKEN)
uv publish --index testpypi                  # named index (needs publish-url configured)
uv publish --trusted-publishing automatic    # from CI, no stored credentials
```

- **Credentials:** `-t`/`--token` (env `UV_PUBLISH_TOKEN`), or `-u`/`--username` +
  `-p`/`--password` (env `UV_PUBLISH_USERNAME`/`UV_PUBLISH_PASSWORD`). PyPI requires a token.
- **Trusted publishing** `--trusted-publishing <automatic|always|never>` — from GitHub Actions
  to PyPI with no stored credentials (implemented `(uv 0.4.16+)`; GitLab CI support
  `(uv 0.8.18+)`).
- **Index/URL:** `--index <NAME>` (env `UV_PUBLISH_INDEX`; the index needs a `publish-url`),
  `--publish-url <URL>` (env `UV_PUBLISH_URL`), `--check-url <URL>` (env `UV_PUBLISH_CHECK_URL`
  — skip already-uploaded files / make retries safe), `--dry-run`, `--no-attestations` (env
  `UV_PUBLISH_NO_ATTESTATIONS`).
- **Guard against accidental upload** of a private package with
  `classifiers = ["Private :: Do Not Upload"]` in `pyproject.toml`.

## `requires-python` and universal resolution

`[project] requires-python = ">=3.12"` must be a **subset** of every dependency's supported
range during universal resolution. uv picks the latest compatible version *per supported Python*
— so older Python versions may pin older dependency versions in the same lock. uv **ignores
upper bounds** on a dependency's own `requires-python` (it treats `>=3.8,<4` as `>=3.8`).

Project resolution is always **universal** (platform-independent). Platform-specific resolution
only happens in the `uv pip` interface, via `--python-platform`/`--python-version` (see
[pip-config.md](pip-config.md)).

## The `uv.lock` model

- **Universal / cross-platform** TOML. A single package may appear **multiple times** with
  different versions or URLs, disambiguated by environment markers — this is more constrained
  than a single-platform resolve.
- **uv-specific** — not consumable by pip or other tools. Emit interop formats with `uv export`.
- **Commit it**; `.venv` is gitignored and rebuilt from the lock.
- Created/updated by `uv sync`, `uv run`, `uv add`/`uv remove`, and `uv lock`. It carries an
  internal `revision`/version field.
- **Restrict the solved set** with `[tool.uv] environments = [ ... ]` (a list of disjoint PEP
  508 markers); **force wheels** for given platforms with `required-environments`.
- PEP 751 `pylock.toml` is an **export target only** `(uv 0.6.15+)` — uv keeps `uv.lock` as its
  internal source of truth.
