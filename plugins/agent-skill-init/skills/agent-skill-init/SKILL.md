---
name: agent-skill-init
description: Create a repo-local Agent Skill following the open agentskills.io specification. Use when the user wants to create, scaffold, or initialize a new skill in the current repo, mentions a 'repo-local skill' or the agentskills.io spec, or needs a spec-compliant SKILL.md placed under .agents/skills/ (or .claude/skills/). Scaffolds the directory, writes valid name/description frontmatter, and validates with skills-ref.
---

# Agent Skill Init

## Overview

Scaffold a single, spec-compliant Agent Skill into the current repository — fast.
A skill is just a directory containing a `SKILL.md` (required) plus optional
`scripts/`, `references/`, and `assets/`. This skill walks you from intent to a
validated skill folder, following the open [agentskills.io](https://agentskills.io)
specification so the result works across any client that reads the spec, not just
one vendor.

The whole point is **low ceremony, high fidelity**: get a correct `name`/`description`
frontmatter, a lean body, the right placement, and a green `skills-ref validate` —
without an evaluation harness or a multi-round authoring loop.

## When to use this skill

Reach for it when the user wants to stand up a new skill in *this* repo and have it
be spec-correct on the first try:

| Use when the user… | This skill gives them… |
|---|---|
| "Create / scaffold / init a skill for X" | a ready directory + valid `SKILL.md` |
| Mentions a "repo-local skill" or "`.agents/skills`" | correct placement + precedence guidance |
| Names the **agentskills.io spec** or asks for cross-client compatibility | frontmatter that satisfies the open spec |
| Wants a copy-paste `SKILL.md` starter | the minimal template below + `assets/SKILL.md.template` |
| Asks "is my frontmatter valid?" | the field table + `skills-ref validate` |

### Not to be confused with

- **`skill-creator`** — the heavyweight authoring *loop*: draft → write test prompts →
  run evals → benchmark with variance → optimize the description. Use that when the skill's
  quality must be *measured and iterated*. Use **this** skill to get a correct skeleton on
  the ground quickly; hand off to `skill-creator` only if you then need eval-driven tuning.
- **`skill-reviewer`** — a quality *audit* of an existing skill (progressive disclosure,
  scope, mental-model language). Run that *after* a skill exists. This skill *produces* the
  skill; the reviewer *grades* it.
- **Marketplace plugin authoring** — wiring a skill into this repo's
  `.claude-plugin/marketplace.json`, changelogs, and `plugins/<name>/skills/<name>/` layout
  is a separate concern handled per `CLAUDE.md`. This skill targets a **repo-local** skill
  (`.agents/skills/<name>/`), not a published marketplace plugin.

## The create workflow

Follow these steps in order. Each one is short; explain choices to the user as you go.

### 1. Capture intent

Pin down two things before touching the filesystem:

1. **What** should the skill let Claude do? (the capability)
2. **When** should it trigger? (the user phrases, file types, and contexts)

The conversation may already contain the answer ("turn this into a skill"). Extract the
workflow, tools, and steps from history first, then confirm the gaps with the user.

### 2. Choose a name and location

The **name** must satisfy the spec rules (see the [field table](#frontmatter-field-table))
and **must match the parent directory name** exactly. Pick kebab-case, descriptive, short.

Default placement is the cross-client interoperability location:

```
<project>/.agents/skills/<name>/SKILL.md
```

For this marketplace's pragmatic Claude compatibility, `<project>/.claude/skills/<name>/`
also works. See [references/placement.md](references/placement.md) for all locations,
project-over-user precedence, and trust considerations before adopting a project-level skill.

### 3. Write the frontmatter

Open with YAML frontmatter holding at least `name` and `description`. The `description` is
the **only** thing a client reads to decide whether to load the skill, so make it carry its
weight: state what the skill does *and* the concrete triggers, keyword-rich. Skills tend to
*under*-trigger, so lean slightly pushy — name the phrases and contexts that should activate it.

### 4. Write the body

The body loads only *after* the skill triggers, so write it for the task, not for discovery.
Keep it lean — recommended under ~5000 tokens / 500 lines. Lead with the common path; push
edge cases, exhaustive flags, and long examples into `references/`.

### 5. Add resources as needed (optional)

Add only what earns its place:

- `references/` — docs loaded on demand (deep field rules, worked examples).
- `scripts/` — executable helpers the skill invokes.
- `assets/` — templates, schemas, or files the skill copies out.

Reference files **one level deep** with **relative paths** from the skill root.

### 6. Validate

This skill **vendors** the official `skills-ref` validator at `vendor/skills-ref/`, so
validation needs only `uv` — no install step. Run it from the new skill's parent directory:

```bash
uvx --from <skill-dir>/vendor/skills-ref skills-ref validate ./<name>
```

`<skill-dir>` is this skill's own directory (the one holding `SKILL.md`). `uvx` builds an
ephemeral environment, so nothing is written back. The same entrypoint also offers
`read-properties` (dump the parsed frontmatter) and `to-prompt` (render the skill as a prompt):

```bash
uvx --from <skill-dir>/vendor/skills-ref skills-ref read-properties ./<name>
uvx --from <skill-dir>/vendor/skills-ref skills-ref to-prompt ./<name>
```

Fix anything it flags, then re-run until clean. The vendored copy is an unmodified Apache-2.0
upstream snapshot (see `vendor/VENDOR.md`) — do not reformat it. If you don't want the vendored
path, a globally installed `skills-ref` is a documented fallback; both are covered in
[references/placement.md](references/placement.md).

## Minimal SKILL.md template

Copy this, replace the placeholders, and you have a valid skill. A ready copy lives at
[assets/SKILL.md.template](assets/SKILL.md.template).

```markdown
---
name: my-skill
description: <What it does in one clause.> Use when <explicit trigger phrases / contexts the user might say or do>. <Optionally: what it produces.>
---

# My Skill

## Overview
One or two sentences on what this skill does and why it exists.

## When to use
- Trigger 1
- Trigger 2

## Workflow
1. First step.
2. Second step.

## Notes
Gotchas, prerequisites, or links to references/ for detail.
```

## Frontmatter field table

| Field | Required | Constraints |
|---|---|---|
| `name` | Yes | 1–64 chars; lowercase `a–z`, `0–9`, and hyphens only; no leading/trailing hyphen; **no consecutive hyphens**; **must match the parent directory name**. |
| `description` | Yes | 1–1024 chars, non-empty. Describe **what** it does *and* **when** to use it; keyword-rich; lean slightly pushy to combat under-triggering. |
| `license` | No | SPDX identifier (e.g. `MIT`). |
| `compatibility` | No | 1–500 chars; note client/runtime requirements. Rarely needed. |
| `metadata` | No | Map of string → string (e.g. version, author). |
| `allowed-tools` | No | Space-separated tool names. Experimental. |

Full constraints, edge cases, and the source rules are in
[references/spec-reference.md](references/spec-reference.md).

## Progressive disclosure

The spec loads a skill in stages, so structure for it:

1. **Metadata** (`name` + `description`) — always loaded, ~50–100 tokens. Keep it sharp.
2. **Body** (`SKILL.md`) — loaded when the skill triggers. Keep it under ~5000 tokens / 500 lines.
3. **Resources** (`references/`, `scripts/`, `assets/`) — loaded only on demand.

Rule of thumb: if a paragraph isn't needed to handle the *common* case, move it to
`references/`. See [references/examples.md](references/examples.md) for good vs. poor
descriptions and layout examples.

## Common mistakes

- **Consecutive hyphens** in `name` (`my--skill`) — invalid. Single hyphens only.
- **`name` ≠ directory name** — the most common validation failure. They must be identical.
- **Vague description** — "Helps with files" gives the client nothing to trigger on. State
  what it does *and* the exact phrases/contexts that should activate it.
- **Deeply nested references** — `references/sub/dir/x.md` breaks the one-level-deep rule.
  Keep reference files directly under `references/`.
- **Bloated body** — a >500-line `SKILL.md` defeats progressive disclosure. Move detail out.
- **Skipping validation** — always finish with `uvx --from <skill-dir>/vendor/skills-ref skills-ref validate ./<name>`.

## References

- [references/spec-reference.md](references/spec-reference.md) — full field constraints and naming rules.
- [references/examples.md](references/examples.md) — good vs. poor descriptions; layout patterns; a worked example.
- [references/placement.md](references/placement.md) — repo-local locations, precedence, trust, and `skills-ref` install + usage.
- [assets/SKILL.md.template](assets/SKILL.md.template) — copy-paste starter.
