# Vendored: skills-ref

This directory contains a **verbatim, unmodified** vendored copy of the
`skills-ref` reference library — the official validator for the
[Agent Skills specification](https://agentskills.io/specification.md).

The `agent-skill-init` skill uses it to validate the skills it scaffolds,
so validation works without requiring a separate global install.

## Provenance

| | |
|---|---|
| Upstream | https://github.com/agentskills/agentskills/tree/main/skills-ref |
| Commit | `5d4c1fda3f786fff826c7f56b6cb3341e7f3a911` |
| Vendored on | 2026-06-19 |
| Package version | `0.1.0` (see `skills-ref/pyproject.toml`) |
| License | Apache-2.0 (see `skills-ref/LICENSE`) |
| Modifications | **None.** Copied verbatim from upstream, except `uv.lock` is not tracked (see below). |

Because this is an upstream verbatim copy, it is intentionally **out of scope**
for this repo's `ruff`/`black`/`ty` targets — do not reformat it. To update,
re-copy from upstream and bump the commit SHA above.

> **Note on `uv.lock`:** this repo's root `.gitignore` ignores `**/uv.lock`, so
> the upstream lockfile is not committed. Dependency resolution therefore uses the
> `pyproject.toml` constraints (`click>=8.0`, `strictyaml>=1.7.3`) at run time. If
> you want fully pinned resolution, force-add the upstream `uv.lock`
> (`git add -f .../vendor/skills-ref/uv.lock`).

## Usage

Runs through `uv` (the only prerequisite), resolving dependencies (`click`,
`strictyaml`) from the bundled `pyproject.toml`:

```bash
# Validate a skill directory (no persistent venv created):
uvx --from <path-to>/vendor/skills-ref skills-ref validate ./path/to/skill

# Other bundled commands:
uvx --from <path-to>/vendor/skills-ref skills-ref read-properties ./path/to/skill
uvx --from <path-to>/vendor/skills-ref skills-ref to-prompt ./path/to/skill
```

`uvx` builds the package into an ephemeral environment, so nothing is written
back into this directory. (`uv run` from inside `skills-ref/` also works but
creates a local `.venv/`, which is git-ignored.)
