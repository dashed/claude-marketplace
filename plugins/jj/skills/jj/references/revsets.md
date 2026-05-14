# Revsets Reference

Revsets are a functional language for selecting commits in jj. This reference covers all operators, functions, and patterns.

## Table of Contents

- [Basic Symbols](#basic-symbols)
- [Operators](#operators)
- [Functions](#functions)
- [String Patterns](#string-patterns)
- [Common Patterns](#common-patterns)

## Basic Symbols

| Symbol | Description |
|--------|-------------|
| `@` | Working copy commit |
| `root()` | Repository root (empty commit) |
| `<change_id>` | Commit by change ID (e.g., `kntqzsqt`) |
| `<commit_id>` | Commit by commit hash (prefix ok) |
| `<bookmark>` | Commit at bookmark (e.g., `main`) |
| `<bookmark>@<remote>` | Remote bookmark (e.g., `main@origin`) |
| `<tag>` | Commit at tag |

## Operators

### Parent/Child Navigation

| Operator | Description | Example |
|----------|-------------|---------|
| `x-` | Parents of x | `@-` (parent of working copy) |
| `x+` | Children of x | `main+` (children of main) |
| `x--` | Grandparents | `@--` |
| `x++` | Grandchildren | `main++` |

### Ancestry/Descendant

| Operator | Description | Example |
|----------|-------------|---------|
| `::x` | Ancestors of x (inclusive) | `::@` |
| `x::` | Descendants of x (inclusive) | `main::` |
| `x::y` | DAG path from x to y | `main::@` |
| `:x` | Ancestors of x (exclusive) | `:@` (excludes @) |
| `x:` | Descendants of x (exclusive) | `main:` (excludes main) |

### Range

| Operator | Description | Example |
|----------|-------------|---------|
| `x..y` | Ancestors of y minus ancestors of x | `main..@` |
| `x..` | Descendants of x minus x | `main..` |
| `..y` | Ancestors of y minus root | `..@` |

### Set Operations

| Operator | Description | Example |
|----------|-------------|---------|
| `x \| y` | Union (x or y) | `main \| develop` |
| `x & y` | Intersection (x and y) | `mine() & ::@` |
| `x ~ y` | Difference (x minus y) | `::@ ~ ::main` |
| `~x` | Complement (not x) | `~empty()` |

### Grouping

Use parentheses for grouping: `(x | y) & z`

## Functions

### Commit Selection

| Function | Description |
|----------|-------------|
| `all()` | All commits |
| `none()` | Empty set |
| `visible_heads()` | Visible branch heads |
| `heads(x)` | Commits in x with no descendants in x |
| `roots(x)` | Commits in x with no ancestors in x |
| `latest(x, n)` | Latest n commits from x by committer date |

### Bookmarks and Tags

| Function | Description |
|----------|-------------|
| `bookmarks()` | All local bookmark targets |
| `bookmarks(pattern)` | Bookmarks matching pattern |
| `remote_bookmarks()` | All remote bookmark targets |
| `remote_bookmarks(pattern)` | Remote bookmarks matching pattern |
| `tracked_remote_bookmarks()` | Tracked remote bookmarks |
| `untracked_remote_bookmarks()` | Untracked remote bookmarks |
| `tags()` | All tag targets |
| `tags(pattern)` | Tags matching pattern |
| `trunk()` | Main branch (main, master, trunk) |

### Author/Committer

| Function | Description |
|----------|-------------|
| `author(pattern)` | Commits by matching author name/email |
| `author_date(pattern)` | Commits by author date |
| `committer(pattern)` | Commits by committer |
| `committer_date(pattern)` | Commits by committer date |
| `mine()` | Commits by configured user |

### Content

| Function | Description |
|----------|-------------|
| `description(pattern)` | Match commit description |
| `description(exact:"text")` | Exact description match |
| `empty()` | Empty commits (no file changes) |
| `file(pattern)` | Commits modifying matching files |
| `diff_contains(pattern)` | Commits with matching diff content |

### Conflicts and Status

| Function | Description |
|----------|-------------|
| `conflicts()` | Commits containing conflicts |
| `signed()` | Cryptographically signed commits |
| `working_copies()` | All working copy commits |

### Mutability

| Function | Description |
|----------|-------------|
| `mutable()` | Commits that can be rewritten |
| `immutable()` | Protected commits (trunk, tags) |
| `immutable_heads()` | Heads of immutable commits |

### Ancestry

| Function | Description |
|----------|-------------|
| `ancestors(x)` | Same as `::x` |
| `ancestors(x, depth)` | Ancestors up to depth |
| `descendants(x)` | Same as `x::` |
| `descendants(x, depth)` | Descendants up to depth |
| `connected(x)` | x plus ancestors and descendants within x |
| `reachable(x, domain)` | Commits reachable from x within domain |

### Structure

| Function | Description |
|----------|-------------|
| `parents(x)` | Parents of commits in x |
| `children(x)` | Children of commits in x |
| `present(x)` | x if it exists, else empty |
| `coalesce(x, y)` | x if non-empty, else y |

## String Patterns

Used in functions like `bookmarks()`, `description()`, `author()`:

| Pattern | Description | Example |
|---------|-------------|---------|
| `substring:text` | Contains text (default) | `description("fix")` |
| `exact:text` | Exact match | `description(exact:"")` |
| `glob:pattern` | Glob pattern | `bookmarks(glob:"feature-*")` |
| `regex:pattern` | Regular expression | `author(regex:"^J.*")` |

## Common Patterns

### Working with Current Work

```bash
# My work in progress
jj log -r 'trunk()..@'

# My recent changes
jj log -r 'mine() & ancestors(@, 20)'

# Empty commits I made (WIP markers)
jj log -r 'mine() & empty()'

# Commits with empty descriptions
jj log -r 'description(exact:"")'
```

### Branch Operations

```bash
# Commits on feature branch not on main
jj log -r 'main..feature'

# All commits on any feature branch
jj log -r 'bookmarks(glob:"feature-*")::'

# Diverged commits
jj log -r 'heads(trunk()..)'
```

### Finding Commits

```bash
# Commits touching specific file
jj log -r 'file("src/main.rs")'

# Commits containing "TODO" in diff
jj log -r 'diff_contains("TODO")'

# Commits by specific author
jj log -r 'author("alice@")'

# Commits from last week
jj log -r 'committer_date(after:"1 week ago")'
```

### Conflicts

```bash
# All conflicted commits
jj log -r 'conflicts()'

# Conflicted commits in my branch
jj log -r 'conflicts() & trunk()..@'
```

### Rebasing Patterns

```bash
# Rebase entire branch onto trunk
jj rebase -s 'roots(trunk()..@)' -d trunk()

# Rebase all mutable descendants
jj rebase -s 'roots(mutable())' -d <dest>

# Find commits to squash (empty changes)
jj log -r 'empty() & trunk()..@'
```

### Working Copies (Multiple Workspaces)

```bash
# All working copy commits
jj log -r 'working_copies()'

# Current workspace's working copy
jj log -r '@'
```

## Date Patterns

For `author_date()` and `committer_date()`:

| Pattern | Example |
|---------|---------|
| `after:date` | `author_date(after:"2024-01-01")` |
| `before:date` | `committer_date(before:"yesterday")` |
| Relative | `"1 week ago"`, `"2 days ago"` |
| Absolute | `"2024-06-15"`, `"2024-06-15T10:30:00"` |

## Combining Expressions

Complex queries combine operators and functions:

```bash
# My non-empty commits on feature branch, excluding conflicts
jj log -r '(mine() & feature::@) ~ (empty() | conflicts())'

# Latest 5 commits touching src/ by any author
jj log -r 'latest(file("src/**"), 5)'

# All commits between two tags
jj log -r 'v1.0::v2.0'
```

## Advanced Recipes

### Rebasing Entire Branch Tree onto New Base

When you have multiple feature branches and want to rebase all onto new upstream:

```bash
# Find roots of all branches leading to integration commit, excluding main:
jj rebase -s 'roots(::my-integration ~ ::main)' -d main
```

This pattern works by:
1. `::my-integration` - All ancestors of integration branch
2. `~ ::main` - Subtract ancestors of main (the difference)
3. `roots(...)` - Find root commits of that set (the branch points)

jj automatically rebases all descendants when you rebase the roots.

**Example workflow:**
```bash
# Verify current state
jj log -r 'main | feature-a | feature-b | integration'

# Rebase all feature branch roots onto updated main
jj rebase -s 'roots(::integration ~ ::main)' -d main

# Handle any conflicts that arise
jj log -r 'conflicts()'
```

### Finding Branch Divergence

```bash
# Commits in feature not in main:
jj log -r '::feature ~ ::main'

# Commits that diverged (in both since common ancestor):
jj log -r '(::feature | ::main) ~ ::trunk()'

# Common ancestor of two branches:
jj log -r 'heads(::feature & ::main)'
```

### Working with Multiple Feature Branches

```bash
# All feature branch heads:
jj log -r 'heads(bookmarks(glob:"feature-*")::)'

# Commits unique to each feature branch:
jj log -r '(::feature-a ~ ::main) | (::feature-b ~ ::main)'

# Find all roots of your work (useful before complex rebase):
jj log -r 'roots(mine() & trunk()..@)'
```

### Finding Merge Commits

```bash
# Commits with merge descriptions in your branch:
jj log -r 'trunk()..@ & description(glob:"*merge*")'

# Multi-parent commits (created with jj new A B):
# Note: Direct parent count query not available, but merges usually
# have descriptive messages
jj log -r 'trunk()..@ & description(glob:"*integration*")'
```

### Complex Rebase Scenarios

```bash
# Rebase preserving branch structure (roots only):
jj rebase -s 'roots(::feature-integration ~ ::main)' -d main

# Rebase single commit without descendants:
jj rebase -r <rev> -d main

# Insert commit between two others:
jj rebase -r <commit> -A <after-this>
jj rebase -r <commit> -B <before-this>
```
