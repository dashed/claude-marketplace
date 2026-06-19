# Agent Skill Spec Reference

Full field constraints and naming rules for a spec-compliant Agent Skill, per the open
[agentskills.io specification](https://agentskills.io/specification.md). Keep this consistent
with the field table in `SKILL.md`; this file is the deep version loaded on demand.

## Contents

- [Skill anatomy](#skill-anatomy)
- [Frontmatter fields](#frontmatter-fields)
  - [name](#name)
  - [description](#description)
  - [license](#license)
  - [compatibility](#compatibility)
  - [metadata](#metadata)
  - [allowed-tools](#allowed-tools)
- [Naming rules in detail](#naming-rules-in-detail)
- [Progressive disclosure budget](#progressive-disclosure-budget)
- [Resource directories](#resource-directories)
- [Validation](#validation)

## Skill anatomy

A skill is a directory. The only required member is `SKILL.md`:

```
<name>/
├── SKILL.md          # required: YAML frontmatter + Markdown body
├── references/       # optional: docs loaded on demand
├── scripts/          # optional: executable helpers
└── assets/           # optional: templates / files copied out
```

`SKILL.md` is YAML frontmatter (between `---` fences) followed by a Markdown body.

## Frontmatter fields

### name

- **Required.**
- Length: **1–64 characters.**
- Allowed characters: lowercase `a–z`, digits `0–9`, and hyphens (`-`) only.
- **No leading or trailing hyphen.**
- **No consecutive hyphens** (`a--b` is invalid).
- **Must match the parent directory name exactly.** If the directory is `pdf-tools/`, the
  `name` must be `pdf-tools`.

Valid: `git-chain`, `pdf-editor`, `skill-creator`, `a`, `tool2`.
Invalid: `My-Skill` (uppercase), `-skill` / `skill-` (edge hyphen), `my--skill` (double
hyphen), `my_skill` (underscore), a name that differs from its folder.

### description

- **Required.**
- Length: **1–1024 characters**, non-empty.
- Content: describe **what the skill does** *and* **when to use it**. This string is the sole
  signal a client uses to decide whether to load the skill.
- Make it **keyword-rich** and lean **slightly pushy** — skills tend to *under*-trigger, so
  name the concrete phrases, file types, and contexts that should activate it.

A useful shape: `<what it does>. Use when <triggers/contexts>. <what it produces>.`

### license

- **Optional.**
- An SPDX license identifier, e.g. `MIT`, `Apache-2.0`.

### compatibility

- **Optional.**
- Length: **1–500 characters.**
- Free text noting client/runtime requirements (e.g. a required binary or platform).
- Rarely needed — omit unless a real constraint exists.

### metadata

- **Optional.**
- A map of **string → string** (e.g. `version: "1.0.0"`, `author: "Name"`).
- Values must be strings; nested structures are out of scope.

### allowed-tools

- **Optional, experimental.**
- A **space-separated** list of tool names the skill is permitted to use.
- Treat as advisory; support varies by client.

## Naming rules in detail

The `name` ↔ directory match is the single most common validation failure. When you rename a
skill, rename **both** the directory and the `name` field together. The character rules exist
so names are safe as path segments and identifiers across clients — that is why uppercase,
underscores, spaces, and doubled hyphens are rejected.

## Progressive disclosure budget

The spec loads a skill in tiers so context stays small:

| Tier | What loads | When | Target size |
|---|---|---|---|
| Metadata | `name` + `description` | always | ~50–100 tokens |
| Body | `SKILL.md` Markdown | on trigger | < ~5000 tokens / < 500 lines |
| Resources | `references/`, `scripts/`, `assets/` | on demand | unbounded, but split by topic |

If content isn't needed to handle the common case, push it down a tier.

## Resource directories

- **`references/`** — Markdown docs the skill points to for depth. Reference them with
  **relative paths, one level deep** (`references/foo.md`, not `references/sub/foo.md`).
  Self-contained, one topic per file; add a table of contents when a file exceeds ~100 lines.
- **`scripts/`** — executables the skill runs. Keep the executable bit / shebang if relevant.
- **`assets/`** — templates, schemas, or files the skill copies into a target project.

## Validation

Validate against the spec with the reference tool:

```bash
skills-ref validate ./<name>
```

It checks frontmatter presence and types, the `name` rules, the `name`↔directory match,
description length, and structural constraints. Install instructions and usage notes are in
[placement.md](placement.md).
