---
name: conventional-commits
description: "Format git commit messages following Conventional Commits 1.0.0 specification. Use when the user asks to commit changes, create a git commit, or mentions committing code. Ensures consistent, semantic commit messages that support automated changelog generation and semantic versioning."
license: MIT
---

# Conventional Commits

Format all git commit messages according to the [Conventional Commits 1.0.0](https://www.conventionalcommits.org/) specification.

## Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Type Reference

| Type | When to Use | SemVer |
|------|-------------|--------|
| `feat` | New feature | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Documentation only | - |
| `style` | Formatting, whitespace (no code change) | - |
| `refactor` | Code restructuring (no feature/fix) | - |
| `perf` | Performance improvement | - |
| `test` | Adding/fixing tests | - |
| `build` | Build system, dependencies | - |
| `ci` | CI/CD configuration | - |
| `chore` | Maintenance, tooling | - |
| `revert` | Reverting previous commit | - |

## Decision Framework

When determining commit type, ask:

- Does it add new functionality? → `feat`
- Does it fix broken functionality? → `fix`
- Does it only affect documentation? → `docs`
- Does it improve performance? → `perf`
- Does it restructure code without changing behavior? → `refactor`
- Does it only change code style/formatting? → `style`
- Does it add/modify tests? → `test`
- Does it change build system or dependencies? → `build`
- Does it change CI/CD configuration? → `ci`
- Is it maintenance or tooling? → `chore`

## Message Best Practices

### Description (first line)
- Keep under 50 characters
- Use imperative mood ("add" not "added")
- Don't capitalize first letter
- No period at end

### Scope
- Use clear, consistent names: `feat(auth):`, `fix(api):`, `docs(readme):`

### Body
- Include when change requires explanation
- Explain why the change was made
- Describe what problem it solves
- Wrap at 72 characters per line

### Footers
- `Fixes #123` - Reference issues
- `Co-authored-by: Name <email>` - Credit contributors
- `BREAKING CHANGE: description` - Breaking changes
- `Refs: #456, #789` - Related issues

## Breaking Changes

Indicate breaking changes using either method:

```
feat!: remove deprecated API endpoint

feat(api)!: change authentication flow

fix: update validation logic

BREAKING CHANGE: validation now rejects empty strings
```

## Command Execution

**Critical**: Use single quotes to avoid shell escaping issues with `!`:

```bash
# Correct - single quotes
git commit -m 'feat!: add new authentication flow'

# Incorrect - backslash escaping (DO NOT USE)
git commit -m "feat\!: add new authentication flow"
```

For multi-line messages, use HEREDOC:

```bash
git commit -m "$(cat <<'EOF'
feat(auth): add OAuth2 support

Implement OAuth2 authentication flow with support for
Google and GitHub providers.

BREAKING CHANGE: removes legacy session-based auth
EOF
)"
```

## Workflow

1. Check for staged changes: `git diff --cached --stat`
2. If nothing staged: stage with `git add` first
3. Review changes: `git diff --cached`
4. Check recent style: `git log --oneline -5`
5. Determine type using decision framework
6. Write message following best practices
7. Execute commit with single quotes
8. Verify: `git log -1`

## Quality Checks

Before committing, verify:

- [ ] Message accurately describes the changes
- [ ] Type correctly categorizes the change
- [ ] Scope (if used) is meaningful and consistent
- [ ] Breaking changes are properly marked with `!` or footer
- [ ] Description is clear and under 50 characters
- [ ] Body wraps at 72 characters (if present)

## Examples

**Simple fix:**
```
fix: prevent null pointer in user lookup
```

**Feature with scope:**
```
feat(api): add rate limiting to endpoints
```

**With body:**
```
refactor: extract validation into separate module

Move validation logic from controllers to dedicated
validator classes for better testability and reuse.
```

**Breaking change:**
```
feat!: upgrade to v2 API format

BREAKING CHANGE: response structure changed from
{data: [...]} to {items: [...], meta: {...}}
```

**With issue reference:**
```
fix(auth): resolve token refresh race condition

Fixes #234
```

## Full Specification

For the complete Conventional Commits 1.0.0 specification including all rules and FAQ, see [references/full-spec.md](references/full-spec.md).
