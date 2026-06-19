# Examples

Concrete patterns to copy when scaffolding a skill: descriptions that trigger well, directory
layouts that respect progressive disclosure, and one fully worked example skill.

## Contents

- [Good vs. poor descriptions](#good-vs-poor-descriptions)
- [Progressive-disclosure layouts](#progressive-disclosure-layouts)
- [A fully worked example skill](#a-fully-worked-example-skill)

## Good vs. poor descriptions

The `description` is the only thing a client reads to decide whether to load the skill. Name
what it does *and* the concrete triggers.

| Poor | Why it fails | Better |
|---|---|---|
| `Helps with PDFs.` | No triggers; too vague to match on. | `Edit and manipulate PDF files. Use when rotating pages, extracting text, merging documents, or splitting PDFs.` |
| `A skill for git.` | Nothing actionable; over-broad. | `Manage chains of dependent Git branches (stacked branches). Use when working with multiple dependent PRs or rebasing a whole branch chain.` |
| `Formats commit messages.` | Misses the trigger phrases users actually say. | `Format git commit messages per Conventional Commits 1.0.0. Use when the user asks to commit changes, create a commit, or mentions committing code.` |

Pattern that works: **`<what it does>. Use when <trigger phrases / file types / contexts>. <what it produces>.`**
Lean slightly pushy — list the words the user might actually type.

## Progressive-disclosure layouts

Keep the common path in `SKILL.md`; push depth into `references/`.

**Minimal (single file is enough):**

```
csv-tidy/
└── SKILL.md
```

**Typical (some depth + a script):**

```
pdf-editor/
├── SKILL.md
├── references/
│   ├── operations.md      # all flags / sub-commands
│   └── troubleshooting.md
└── scripts/
    └── merge.py
```

**With a template asset:**

```
report-gen/
├── SKILL.md
├── references/
│   └── format-spec.md
└── assets/
    └── report.md.template
```

Reference files stay **one level deep** under `references/` with **relative** links from
`SKILL.md` (`references/operations.md`).

## A fully worked example skill

A small but complete, spec-valid skill. Directory and `name` match (`changelog-bump`).

**`changelog-bump/SKILL.md`:**

```markdown
---
name: changelog-bump
description: Move the Unreleased section of a Keep a Changelog file into a dated, versioned section. Use when cutting a release, bumping a version, or when the user mentions updating CHANGELOG.md, "release notes", or "move Unreleased". Produces the rewritten changelog and the version comparison links.
license: MIT
metadata:
  version: "1.0.0"
---

# Changelog Bump

## Overview
Promote `## [Unreleased]` in a Keep a Changelog file into `## [X.Y.Z] - YYYY-MM-DD`,
leaving a fresh empty Unreleased section and updating the comparison links.

## When to use
- Cutting a release / bumping a version.
- The user says "update the changelog", "move Unreleased", or "release notes".

## Workflow
1. Read CHANGELOG.md and confirm the target version and today's date.
2. Rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD`.
3. Insert a new empty `## [Unreleased]` above it.
4. Update the comparison links at the bottom (see references/links-format.md).
5. Show the diff for confirmation.

## Notes
Follows Keep a Changelog 1.0.0. Link format details: references/links-format.md.
```

**`changelog-bump/references/links-format.md`:**

```markdown
# Comparison Links

At the bottom of CHANGELOG.md, maintain:

    [Unreleased]: https://…/compare/vX.Y.Z...HEAD
    [X.Y.Z]: https://…/compare/vPREV...vX.Y.Z

Update the Unreleased link to point at the new tag, and add one line for the
new version comparing the previous tag to the new one.
```

Validate it with:

```bash
skills-ref validate ./changelog-bump
```
