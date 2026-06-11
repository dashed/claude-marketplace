# uv: pip Interface, Caching, Configuration & Indexes

The `uv pip` pip-compatible interface, the uv cache, configuration-file discovery
and precedence, the `UV_*` environment variables, and how uv resolves packages
across indexes (auth, resolution strategy, cross-platform targeting). For the
project interface (`uv add`/`sync`/`lock`), scripts, and tools, see
[SKILL.md](../SKILL.md) and the other references.

> **Verification & version annotations.** Every flag, subcommand, and enum value
> below was confirmed against the installed **`uv 0.11.2`**
> (`uv 0.11.2 (02036a8ba 2026-03-26 aarch64-apple-darwin)`) via `uv <cmd> --help`
> / `uv help <cmd>`. Confirm your own build with `uv --version`. Most of `uv pip`,
> the cache, and the config system is **bedrock** (stable at/before uv 0.4.0) and
> left unannotated; only items with a real changelog source carry a `(uv 0.X+)`
> tag. uv is **0.x**, so minor bumps can break — the canonical, always-current
> settings/env lists live in the *generated* `docs.astral.sh/uv/reference/`
> (`settings.md` / `environment.md`); the env table here was reconstructed from
> the binary's own `[env: …]` annotations.

## Table of Contents

- [The `uv pip` interface](#the-uv-pip-interface)
- [Caching](#caching)
- [Configuration files & precedence](#configuration-files--precedence)
- [UV_* environment variables](#uv_-environment-variables)
- [Indexes & resolution](#indexes--resolution)
- [Cross-platform targeting](#cross-platform-targeting)

---

## The `uv pip` interface

`uv pip` is a faster, **mostly** drop-in replacement for `pip` *and* `pip-tools`.
It operates on the **active / discovered virtual environment** and **never**
touches `pyproject.toml` or `uv.lock` — it is deliberately separate from the
project interface (`uv add`/`sync`/`lock`).

| Subcommand | Replaces / does |
|------------|-----------------|
| `uv pip install` | `pip install` — add packages to the env (does **not** remove extraneous) |
| `uv pip uninstall` | `pip uninstall` |
| `uv pip list` | `pip list` (tabular) |
| `uv pip show` | `pip show` — info on installed packages |
| `uv pip freeze` | `pip freeze` (requirements format) |
| `uv pip tree` | `pip tree` — dependency tree of the env |
| `uv pip check` | `pip check` — verify installed deps are compatible |
| `uv pip compile` | `pip-compile` — lock a `requirements.in` → `requirements.txt`/`pylock.toml` |
| `uv pip sync` | `pip-sync` — make the env **exactly** match a requirements/lock file (removes extraneous) |

### pip-compatibility philosophy & notable deviations

uv targets pip's *interface*, not byte-for-byte behavior. Key differences to know:

- **Environment, not global.** Installs into the active venv or a discovered
  `.venv` (searching cwd then parents) — never a global/system site by default.
  Discovery order: **`VIRTUAL_ENV` → `CONDA_PREFIX` → `.venv`**. For a non-venv
  target use `--system` (`UV_SYSTEM_PYTHON`) or `--python PATH`. `--break-system-packages`
  overrides PEP 668 marker files.
- **Ignores pip config.** uv does **not** read `pip.conf` or `PIP_*` env vars; it
  uses `UV_*` env vars plus `uv.toml` / `[tool.uv.pip]`.
- **`--user` is not supported.** The flag is accepted on the command line but uv
  has no per-user install scheme — use `--target` / `--prefix` / a venv instead.
- **Build isolation on by default** (PEP 517). Escape with `--no-build-isolation`
  (or `--no-build-isolation-package PKG`).
- **No bytecode compilation by default.** Opt in with `--compile-bytecode`
  (`UV_COMPILE_BYTECODE`).
- **Keyring is opt-in and limited.** Only `--keyring-provider subprocess` (the
  other value is `disabled`, the default).
- **`first-index` resolution by default** (confusion-safe) instead of pip's
  cross-index "best match" — see [Indexes & resolution](#indexes--resolution).
- **`--constraint` does not constrain build deps** — use `--build-constraints`/`-b`
  for those.
- **Names are normalized** for display (PEP 503).
- **`uv pip sync` removes extraneous packages**; `uv pip install` does not.
- **`uv pip compile` writes nothing without `-o`/`--output-file`**, defaults to
  `--strip-extras`, and does **not** emit index URLs unless you pass
  `--emit-index-url`.

### `uv pip install` — key flags

```bash
uv pip install -r requirements.txt          # from a requirements file
uv pip install "flask[dotenv]"              # extras
uv pip install "ruff @ ./projects/ruff"     # local path (PEP 508 direct ref)
uv pip install "git+https://github.com/x/y@v0.2.0"
uv pip install -r pyproject.toml --extra foo   # extras from a pyproject
uv pip install -r pyproject.toml --group dev   # PEP 735 group
```

| Flag | Purpose |
|------|---------|
| `-r, --requirements FILE` | install from a requirements/pyproject file |
| `-e, --editable` | install a project in editable mode |
| `-c, --constraints` (`UV_CONSTRAINT`) | constrain versions (does **not** cover build deps) |
| `--overrides` (`UV_OVERRIDE`) | force versions, overriding declared ranges |
| `-b, --build-constraints` (`UV_BUILD_CONSTRAINT`) | constrain **build**-time deps |
| `--extra E` / `--all-extras` / `--group G` | enable extras / groups |
| `--no-deps` | install listed packages only |
| `--require-hashes` / `--no-verify-hashes` | hash-checking mode |
| `--system` (`UV_SYSTEM_PYTHON`) / `--break-system-packages` | non-venv target |
| `-t, --target DIR` / `--prefix DIR` | install to a directory / prefix |
| `--no-build` / `--no-binary` / `--only-binary` | source vs wheel policy |
| `--exact` / `--strict` / `--dry-run` | exact env match / strict consistency check / preview |
| `-U, --upgrade` / `-P, --upgrade-package PKG` | upgrade all / one |
| `--reinstall` / `--reinstall-package PKG` | force reinstall |
| `--no-build-isolation[-package PKG]` | disable PEP 517 isolation |
| `-C, --config-setting KEY=VAL` | pass a build-backend setting |
| `--link-mode` (`UV_LINK_MODE`) | how files land in the env (clone/hardlink/copy/symlink) |
| `--torch-backend` | PyTorch index inference — see [below](#torch-backend) |

Resolver/index flags (`--resolution`, `--prerelease`, `--exclude-newer`,
`--index`, `--index-strategy`, …) are shared — see [Indexes & resolution](#indexes--resolution).

### `uv pip compile` — pip-tools replacement

```bash
uv pip compile requirements.in -o requirements.txt          # lock to a txt
uv pip compile pyproject.toml -o requirements.txt --universal
uv pip compile requirements.in -o requirements.txt --generate-hashes
```

- Sources: `.in` files, `pyproject.toml`/`setup.py`/`setup.cfg`, or `-` (stdin).
- `-o, --output-file FILE` — **required to write output** (else prints nothing useful).
- `--format <requirements.txt | pylock.toml>` (PEP 751 `pylock.toml` export `(uv 0.6.15+)`).
- `--universal` — cross-platform output with environment markers (vs the
  platform-specific default).
- `--generate-hashes`, `--no-strip-extras` (default strips), `--no-strip-markers`,
  `--no-annotate`, `--no-header`, `--annotation-style <line|split>`.
- `--emit-index-url` / `--emit-find-links` / `--emit-index-annotation` (off by default).
- `--no-emit-package PKG`, `--custom-compile-command` (`UV_CUSTOM_COMPILE_COMMAND`,
  rewrites the header comment).
- `--python-platform` / `--python-version` set the *resolution* target (see
  [cross-targeting](#cross-platform-targeting)).
- Existing pins in the output file are **preserved** unless you pass `--upgrade`.

### `uv pip sync`

Makes the environment match the file **exactly** (installs missing, removes
extraneous):

```bash
uv pip sync requirements.txt        # or a pylock.toml
```

`--allow-empty-requirements`, `--require-hashes`, `--reinstall[-package]`,
`--strict`, plus the install-style index/build flags — but a **leaner resolver**
(no `--resolution`/`--prerelease`/`--upgrade`; the file is already pinned).

### Inspection: `list` / `freeze` / `show` / `tree` / `check`

```bash
uv pip list --format json            # columns (default) | freeze | json
uv pip list --outdated
uv pip freeze                        # requirements format
uv pip tree --depth 2 --invert       # reverse deps
uv pip check                         # report broken/incompatible installs
```

- **`list`**: `--format <columns|freeze|json>`, `--outdated`, `-e/--editable`,
  `--exclude-editable`, `--exclude PKG`.
- **`freeze`**: `--exclude-editable`, `--exclude PKG`, `--path DIR`.
- **`tree`**: `-d/--depth N` (default **255**), `--invert`, `--outdated`,
  `--show-sizes`, `--no-dedupe`, `--prune PKG`.
- **`check`** flags missing/incompatible deps **and multiple installed versions**
  of the same package (something pip does not detect).
- All inspection subcommands accept `--system` to target the system Python env.

---

## Caching

uv maintains a global, append-only, concurrency-safe cache that backs every
download and build.

```bash
uv cache dir                  # print the cache directory (e.g. ~/.cache/uv)
uv cache size -H              # show cache size, -H = human-readable
uv cache clean                # remove ALL cache entries
uv cache clean requests       # remove entries for one package
uv cache prune                # remove unreachable/unused objects
uv cache prune --ci           # CI mode: drop pre-built wheels, KEEP source builds
```

| Command | Purpose |
|---------|---------|
| `uv cache dir` | print the cache directory |
| `uv cache size [-H/--human]` | report cache size |
| `uv cache clean [PKG…]` | clear everything, or just the named packages; `--force` ignores in-use checks |
| `uv cache prune [--ci]` | remove unreachable objects; `--ci` keeps source builds but drops cached wheels; `--force` ignores in-use checks |

**Cache-directory resolution** (high → low):
`--no-cache` (temp dir for the run) → `--cache-dir` / `UV_CACHE_DIR` /
`tool.uv.cache-dir` → `$XDG_CACHE_HOME/uv` → `~/.cache/uv`
(Windows `%LOCALAPPDATA%\uv\cache`). Keep the cache on the **same filesystem as
the target venv** so uv can hardlink instead of copy.

**Busting / bypassing the cache:**

- `--refresh` / `--refresh-package PKG` — re-fetch metadata for everything / one
  package (the **preferred** way to pick up a new release; keeps the rest cached).
- `--reinstall` / `--reinstall-package PKG` — force reinstall (implies refresh).
- `--no-cache` / `-n` (`UV_NO_CACHE`) — read/write nothing; use a temp cache.

**What is cached & how it invalidates:** registry responses (via HTTP headers),
direct URLs, **Git dependencies pinned to a commit hash**, local files (by mtime),
and local directories (by manifest mtime). Define `[tool.uv.cache-keys]` to add
custom invalidation triggers. Concurrent processes coordinate via a lock whose
wait is bounded by `UV_LOCK_TIMEOUT` (default 5 minutes).

**CI tip:** persist the directory pointed to by `UV_CACHE_DIR` across job runs,
and end each job with `uv cache prune --ci` to shrink it (dropping wheels that
are cheap to re-download while keeping expensive source builds).

---

## Configuration files & precedence

uv reads configuration from a **project** file and from **user/system** files.

**Project file discovery** (searching cwd, then parent directories):

- `pyproject.toml` — settings under the **`[tool.uv]`** table.
- `uv.toml` — same keys but **top-level** (no `[tool.uv]` prefix).

> **If both exist in the same directory, `uv.toml` wins** and the `[tool.uv]`
> table in `pyproject.toml` is ignored *entirely* (not merged). In a workspace,
> the search starts at the workspace root. `uv tool` commands ignore local
> project config.

**User & system files** (these **must** be in `uv.toml` format — the
`[tool.uv]`/pyproject form is invalid here):

| Scope | Path (Unix) | Path (Windows) |
|-------|-------------|----------------|
| User | `~/.config/uv/uv.toml` (`$XDG_CONFIG_HOME/uv/uv.toml`) | `%APPDATA%\uv\uv.toml` |
| System | `/etc/uv/uv.toml` (`$XDG_CONFIG_DIRS`) | `%PROGRAMDATA%\uv\uv.toml` |

**Precedence (high → low): CLI flags > environment variables > project file >
user file > system file.** For scalar settings the higher-priority source wins;
for array settings the values are **concatenated** (higher-priority entries first).

**Overriding discovery:**

- `--config-file PATH` (`UV_CONFIG_FILE`) — use exactly this `uv.toml`, ignoring
  all discovered files.
- `--no-config` (`UV_NO_CONFIG`) — skip every config file.

**Scoping note:** `[tool.uv.pip]` (or the `[pip]` table in `uv.toml`) configures
**only the `uv pip` subcommands**, not the project interface.

**Dotenv (`uv run` only):** `--env-file` / `UV_ENV_FILE` load variables from a
`.env`; `--no-env-file` / `UV_NO_ENV_FILE` disable it.

---

## UV_* environment variables

Reconstructed from the binary's `[env: …]` annotations on uv 0.11.2. The
canonical exhaustive list is the generated `reference/environment.md` on
docs.astral.sh.

| Env var | Maps to / effect |
|---------|------------------|
| `UV_PYTHON` | `--python` (interpreter request) |
| `UV_SYSTEM_PYTHON` | `--system` |
| `UV_MANAGED_PYTHON` / `UV_NO_MANAGED_PYTHON` | `--managed-python` / `--no-managed-python` `(uv 0.6.8+)` |
| `UV_PYTHON_DOWNLOADS` | `automatic` / `manual` / `never` |
| `UV_PYTHON_PREFERENCE` | `only-managed` / `managed` / `system` / `only-system` |
| `UV_PYTHON_INSTALL_DIR` / `UV_PYTHON_BIN_DIR` | managed-Python install / bin dirs |
| `UV_CACHE_DIR` / `UV_NO_CACHE` | cache directory / disable cache |
| `UV_LOCK_TIMEOUT` | cache-lock wait, seconds (default 300) |
| `UV_INDEX` / `UV_DEFAULT_INDEX` | `--index` / `--default-index` |
| `UV_INDEX_URL` / `UV_EXTRA_INDEX_URL` | legacy (deprecated) index URLs |
| `UV_FIND_LINKS` / `UV_INDEX_STRATEGY` | `--find-links` / `--index-strategy` |
| `UV_INDEX_<NAME>_USERNAME` / `_PASSWORD` | per-named-index credentials |
| `UV_KEYRING_PROVIDER` | `--keyring-provider` (`disabled` / `subprocess`) |
| `UV_CONSTRAINT` / `UV_OVERRIDE` / `UV_BUILD_CONSTRAINT` / `UV_EXCLUDE` | resolver inputs |
| `UV_RESOLUTION` / `UV_PRERELEASE` / `UV_FORK_STRATEGY` / `UV_EXCLUDE_NEWER` | resolver knobs |
| `UV_NO_SOURCES` | `--no-sources` |
| `UV_LINK_MODE` / `UV_COMPILE_BYTECODE` / `UV_NO_BUILD_ISOLATION` | installer / build behavior |
| `UV_TORCH_BACKEND` | `--torch-backend` |
| `UV_FROZEN` / `UV_LOCKED` / `UV_NO_SYNC` | project lock/sync control |
| `UV_PROJECT` / `UV_WORKING_DIR` / `UV_PROJECT_ENVIRONMENT` | project dir / working dir / `.venv` location |
| `UV_TOOL_DIR` / `UV_TOOL_BIN_DIR` | tool install / bin dirs |
| `UV_PUBLISH_TOKEN` / `_USERNAME` / `_PASSWORD` / `_URL` / `_INDEX` | `uv publish` credentials/target |
| `UV_CONFIG_FILE` / `UV_NO_CONFIG` | config-file override / disable discovery |
| `UV_OFFLINE` / `UV_NO_PROGRESS` / `UV_SYSTEM_CERTS` / `UV_INSECURE_HOST` | global behavior |
| `UV_PREVIEW_FEATURES` | enable named preview features (e.g. `native-auth`) |
| `NETRC` | path to the `.netrc` file |

---

## Indexes & resolution

### Named indexes vs legacy URL flags

The modern way to declare an index is a named `[[tool.uv.index]]` entry
`(uv 0.4.23+)`:

```toml
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"
# default  = true   # replace PyPI as the implicit fallback (always lowest priority)
# explicit = true   # only used when a package is pinned to it via tool.uv.sources
# format   = "flat"  # a "find-links"-style flat listing (else PEP 503 Simple)
```

Per-index keys added `(uv 0.11.20+)` — likely **not** on a 0.11.2 box: `authenticate`,
`ignore-error-codes`, `cache-control`, `exclude-newer`.

On the CLI / via env (using `name=url` syntax for named indexes):

- `--index URL` (`UV_INDEX`) — add an index (extra index, searched before the default).
- `--default-index URL` (`UV_DEFAULT_INDEX`) — replace the implicit PyPI fallback.
- Definition **order = priority**; CLI-provided indexes outrank config.

**Legacy, deprecated (still functional):**

- `-i, --index-url URL` (`UV_INDEX_URL`) → behaves like `--default-index`.
- `--extra-index-url URL` (`UV_EXTRA_INDEX_URL`) → behaves like `--index`.
- `-f, --find-links` (flat page/dir of links), `--no-index` (use only `--find-links`).

> `(uv 0.10.0+)` It is an error to declare **multiple** `default = true` indexes.

### Pinning a package to an index

```toml
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"

[tool.uv.sources]
torch = { index = "pytorch" }     # only this index supplies torch
```

The source value may be a list disambiguated by `marker = "…"`. A named index used
in `[tool.uv.sources]` must be defined in the **same project's** `pyproject.toml`.

### `--index-strategy`

`--index-strategy` (`UV_INDEX_STRATEGY`), confirmed values:

| Strategy | Behavior |
|----------|----------|
| `first-index` | **Default.** Take a package from the first index that has it (dependency-confusion–safe) |
| `unsafe-first-match` | Consider all indexes but prefer the earliest index with any match |
| `unsafe-best-match` | pip-like: pick the best version across **all** indexes |

uv stops on a `401`/`403` from an index (with a known PyTorch `403` exception) and
continues past `404`.

### Authentication

Credential precedence: **URL-embedded creds → `.netrc` (`NETRC` env or `~/.netrc`)
→ uv's credential store → keyring**. Keyring is **off** unless you pass
`--keyring-provider subprocess` (`UV_KEYRING_PROVIDER`; the only other value is
`disabled`). uv attaches known credentials *proactively* (it does not wait for a
`401`). Per-index credentials via env: `UV_INDEX_<NAME>_USERNAME` /
`UV_INDEX_<NAME>_PASSWORD`, where `<NAME>` is the index name uppercased with
non-alphanumerics replaced by `_`.

**`uv auth` `(uv 0.8.15+)`** — manage stored credentials. On 0.11.2 the
subcommands are:

```bash
uv auth login <SERVICE> --token <TOKEN>      # or -u/--username + --password
uv auth token <SERVICE>                      # print the stored token
uv auth logout <SERVICE>
uv auth dir                                  # path to the credentials directory
```

Credentials are stored under uv's credentials directory
(`~/.local/share/uv/credentials/credentials.toml`). Multiple username/password
pairs per host are supported `(uv 0.10.0+)`. Set
`UV_PREVIEW_FEATURES=native-auth` to back the store with the OS keychain.

### Resolution strategy & pre-releases

- `--resolution` (`UV_RESOLUTION`): **`highest`** (default) / `lowest` /
  `lowest-direct` (lowest for direct deps, highest for transitive).
- `--prerelease` (`UV_PRERELEASE`): `disallow` / `allow` / `if-necessary` /
  `explicit` / `if-necessary-or-explicit`.
- `--fork-strategy` (`UV_FORK_STRATEGY`): `requires-python` / `fewest`.

### Overrides, constraints, build-constraints

- **Overrides** — `--overrides FILE` (`UV_OVERRIDE`) / `[tool.uv] override-dependencies`.
  Absolute: they *replace* a package's declared requirements and can **expand** the
  allowed set.
- **Constraints** — `-c/--constraints` (`UV_CONSTRAINT`) /
  `[tool.uv] constraint-dependencies`. Additive and **narrowing only** — they never
  add a package, only bound versions of ones already in the graph.
- **Build constraints** — `-b/--build-constraints` (`UV_BUILD_CONSTRAINT`) /
  `[tool.uv] build-constraint-dependencies`. Constrain packages used during PEP 517
  builds (regular `--constraints` do **not** reach build deps).

### `--exclude-newer`

`--exclude-newer DATE` (`UV_EXCLUDE_NEWER`) limits candidates to those uploaded
before a cutoff — for reproducible resolutions. On 0.11.2 it accepts:

- An RFC 3339 timestamp — `2006-12-02T02:07:43Z`.
- A local date — `2006-12-02` (resolved in the system time zone).
- A "friendly" duration — `24 hours`, `1 week`, `30 days`.
- An ISO 8601 duration — `PT24H`, `P7D`, `P30D`.

Durations are a fixed number of seconds (a day = 24h, DST ignored); calendar units
(months/years) are not allowed. Per-package override:
`--exclude-newer-package PKG=DATE`.

### `--torch-backend`

`--torch-backend` (`UV_TORCH_BACKEND`) tells uv which PyTorch ecosystem index to
fetch from. It is **experimental-introduced `(uv 0.6.9+)`, preview label removed
`(uv 0.7.14+)`**, and on 0.11.2 lives on **`uv pip install` / `uv pip compile` /
`uv pip sync`** (and on `uvx` / `uv tool`) — **NOT on `uv add`**.

```bash
uv pip install torch --torch-backend auto    # infer CPU/CUDA/ROCm from the machine
uv pip install torch --torch-backend cpu
uv pip install torch --torch-backend cu128
```

Confirmed values on 0.11.2: `auto`, `cpu`, CUDA `cu130 … cu80` (newest is `cu130`;
note there is no `cu127`), ROCm `rocm7.1 … rocm4.0.1`, and `xpu`.

---

## Cross-platform targeting

The `uv pip` interface resolves **for the current platform/Python by default**.
Two flags retarget it (also available on `uv lock`/`uv tree`):

- `--python-platform` — e.g. `windows`, `linux`, `macos`, or a full target triple
  such as `x86_64-unknown-linux-gnu`, `aarch64-apple-darwin`, a `manylinux…` tag,
  or `wasm32-pyodide2024`.
- `--python-version <X.Y[.Z]>` — on `compile` this is the **resolution** version;
  on `install`/`sync` it is the **minimum** supported version; in platform-specific
  resolution it pins the exact version.

```bash
# Resolve a Linux/3.10 requirements set from a different host:
uv pip compile --python-platform linux --python-version 3.10 requirements.in -o requirements.txt
```

For a single cross-platform output with environment markers (rather than one
platform), use `uv pip compile --universal`. (The project interface resolves
universally already — see [SKILL.md](../SKILL.md).)
