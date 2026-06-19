# Placement & Validation

Where a repo-local skill lives, how locations take precedence, the trust implications of
project-level skills, and how to run the `skills-ref` validator.

## Contents

- [Locations](#locations)
- [Precedence](#precedence)
- [Trust considerations](#trust-considerations)
- [Validating a skill](#validating-a-skill)
  - [Vendored validator (primary)](#vendored-validator-primary)
  - [Global install (fallback)](#global-install-fallback)

## Locations

A skill is discovered by directory. The open spec defines these locations:

| Location | Scope | Notes |
|---|---|---|
| `<project>/.agents/skills/<name>/` | Project | **Default.** Cross-client interoperability location — the recommended home for a repo-local skill. |
| `<project>/.<client>/skills/<name>/` | Project | Client-specific (e.g. a particular vendor's folder). Use when you intentionally target one client. |
| `~/.agents/skills/<name>/` | User | Available across all of that user's projects. |
| `<project>/.claude/skills/<name>/` | Project | Pragmatic Claude compatibility — works today and is a fine choice in this ecosystem. |

For a skill meant to travel with the repository and work in any spec-aware client, prefer
`<project>/.agents/skills/<name>/`. The `<name>` directory must equal the skill's `name`
frontmatter (see [spec-reference.md](spec-reference.md)).

## Precedence

When the same skill name exists at more than one level, **project-level overrides
user-level.** A skill checked into the repo therefore wins over a personal one in
`~/.agents/skills/`, so a project can pin the exact behavior its contributors get. Among
project-level locations, follow your client's documented order; keep a given skill in **one**
location to avoid ambiguity.

## Trust considerations

A project-level skill runs with the same reach as the agent that loads it — including any
`scripts/` it ships and any `allowed-tools` it requests. Treat adding a project-level skill
like adding executable code to the repo:

- Review `scripts/` before trusting a skill from an external source.
- Be deliberate about `allowed-tools` — request only what the skill genuinely needs.
- Because project skills override user skills, a malicious or careless project skill can
  shadow a trusted personal one. Inspect skills you didn't author before relying on them.

## Validating a skill

`skills-ref` is the spec's reference validator. It checks: frontmatter is present and
well-typed; `name` obeys the character and length rules; `name` matches the directory;
`description` is within 1–1024 chars; and structural constraints hold. Fix every reported
issue and re-run until it passes — a clean validate is the finish line for scaffolding a skill.

### Vendored validator (primary)

This `agent-skill-init` skill **bundles** `skills-ref` at `vendor/skills-ref/`, so the only
prerequisite is `uv`. Run it from the new skill's parent directory:

```bash
uvx --from <skill-dir>/vendor/skills-ref skills-ref validate ./<name>
```

`<skill-dir>` is this skill's own directory (the one holding `SKILL.md`). `uvx` builds an
ephemeral environment, resolving dependencies from the bundled `pyproject.toml`, and nothing
is written back into the directory. The same entrypoint exposes two more bundled subcommands:

```bash
uvx --from <skill-dir>/vendor/skills-ref skills-ref read-properties ./<name>   # dump parsed frontmatter
uvx --from <skill-dir>/vendor/skills-ref skills-ref to-prompt ./<name>         # render skill as a prompt
```

The vendored tree is an **unmodified, verbatim Apache-2.0 upstream snapshot** (provenance and
commit SHA in `vendor/VENDOR.md`) — it is intentionally out of scope for this repo's
formatters and must not be reformatted. To refresh it, re-copy from upstream and bump the SHA.

### Global install (fallback)

If you'd rather not use the vendored copy, install `skills-ref` globally from
`github.com/agentskills/agentskills/tree/main/skills-ref`:

```bash
git clone https://github.com/agentskills/agentskills
cd agentskills/skills-ref
# follow the tool's README to install (e.g. via its package manifest)
skills-ref --help        # confirm it's on your PATH
```

Then validate with the bare command:

```bash
skills-ref validate ./<name>
```
