# Revsets Reference

Revsets are a functional language for selecting commits in jj. This reference covers all operators, functions, and patterns.

## Table of Contents

- [Basic Symbols](#basic-symbols)
- [Symbol Resolution Priority](#symbol-resolution-priority)
- [Operators](#operators)
- [Functions](#functions)
- [String Patterns](#string-patterns)
- [Date Patterns](#date-patterns)
- [Revset Aliases](#revset-aliases)
- [Common Patterns](#common-patterns)
- [Deprecations](#deprecations-037038)

## Basic Symbols

| Symbol | Description |
|--------|-------------|
| `@` | Working copy commit |
| `<workspace>@` | Working copy in another workspace |
| `root()` | Repository root (empty commit) |
| `<change_id>` | Commit by change ID (e.g., `kntqzsqt`) |
| `<commit_id>` | Commit by commit hash (prefix ok) |
| `<bookmark>` | Commit at bookmark (e.g., `main`) |
| `<bookmark>@<remote>` | Remote bookmark (e.g., `main@origin`) |
| `<tag>` | Commit at tag |

## Symbol Resolution Priority

jj resolves a symbol in this order:

1. Tag name
2. Bookmark name
3. Git ref
4. Commit ID or change ID

To override, use `commit_id(abc)` or `change_id(abc)` explicitly — useful in scripts where a bookmark might shadow a commit ID.

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
| `all()` | All visible commits |
| `none()` | Empty set |
| `visible_heads()` | Visible branch heads |
| `heads(x)` | Commits in x with no descendants in x |
| `roots(x)` | Commits in x with no ancestors in x |
| `latest(x, [count])` | Latest `count` commits from x by committer timestamp (default: 1) |
| `fork_point(x)` | Common ancestor(s) of all commits in x. Equivalent to `heads(::x_1 & ::x_2 & ... & ::x_N)`. Single commit resolves to itself |
| `bisect(x)` | Finds commits where roughly half of x are descendants — useful for bisection workflows |
| `exactly(x, count)` | Returns x, errors if set size is not exactly `count`. Use `exactly(x, 1)` to assert single commit |
| `merges()` | Merge commits (multiple parents) |

### Bookmarks and Tags

| Function | Description |
|----------|-------------|
| `bookmarks([pattern])` | All local bookmark targets, optionally filtered by pattern |
| `remote_bookmarks([name], [remote=pattern])` | All remote bookmark targets. Use `remote="git"` or `remote="*"` to include `@git` bookmarks |
| `tracked_remote_bookmarks([name], [remote=pattern])` | Tracked remote bookmarks, same optional args as `remote_bookmarks()` |
| `untracked_remote_bookmarks([name], [remote=pattern])` | Untracked remote bookmarks, same optional args as `remote_bookmarks()` |
| `tags([pattern])` | All tag targets |
| `remote_tags([name], [remote=pattern])` | Remote tags (0.38+) |
| `trunk()` | Main branch (main, master, trunk) |

### Author/Committer

| Function | Description |
|----------|-------------|
| `author(pattern)` | Match author name or email. Equivalent to `author_name(p) \| author_email(p)` |
| `author_name(pattern)` | Match author name only |
| `author_email(pattern)` | Match author email only |
| `author_date(pattern)` | Match author date (see [Date Patterns](#date-patterns)) |
| `committer(pattern)` | Match committer name or email. Equivalent to `committer_name(p) \| committer_email(p)` |
| `committer_name(pattern)` | Match committer name only |
| `committer_email(pattern)` | Match committer email only |
| `committer_date(pattern)` | Match committer date (see [Date Patterns](#date-patterns)) |
| `mine()` | Commits by configured user email. Equivalent to `author_email(exact-i:<user-email>)` |

### Content

| Function | Description |
|----------|-------------|
| `description(pattern)` | Match commit description. Note: non-empty descriptions usually end with newline |
| `subject(pattern)` | Match first line of description only (without trailing newline) |
| `empty()` | Empty commits (no file changes). Includes `merges()` without user modifications and `root()` |
| `files(expression)` | Commits modifying paths matching fileset expression. Paths relative to cwd |
| `diff_lines(text, [files])` | Commits with matching diff content (renamed from `diff_contains()` in 0.38) |
| `diff_lines_added(text, [files])` | Match content on added side of diff only (0.40+) |
| `diff_lines_removed(text, [files])` | Match content on removed side of diff only (0.40+) |

### Conflicts and Status

| Function | Description |
|----------|-------------|
| `conflicts()` | Commits containing conflicts |
| `divergent()` | Divergent changes — multiple visible commits with the same change ID (0.38+) |
| `signed()` | Cryptographically signed commits |
| `working_copies()` | All working copy commits across all workspaces |
| `at_operation(op, x)` | Evaluate revset x at a specific operation. E.g., `at_operation(@-, visible_heads())` returns heads at the previous operation |

### Mutability

| Function | Description |
|----------|-------------|
| `mutable()` | Commits that can be rewritten (`~immutable()`) |
| `immutable()` | Protected commits (`::(immutable_heads() \| root())`) |
| `immutable_heads()` | Heads of immutable set (default: `trunk() \| tags() \| untracked_remote_bookmarks()`) |

### Ancestry and Navigation

| Function | Description |
|----------|-------------|
| `ancestors(x, [depth])` | Same as `::x`. With depth, limits ancestor traversal |
| `descendants(x, [depth])` | Same as `x::`. With depth, limits descendant traversal |
| `parents(x, [depth])` | Parents of x. With depth, `parents(x, 3)` is equivalent to `x---` |
| `children(x, [depth])` | Children of x. With depth, `children(x, 3)` is equivalent to `x+++` |
| `first_parent(x, [depth])` | Like `parents(x)`, but only returns first parent of merges. `first_parent(x, 2)` = `first_parent(first_parent(x))` |
| `first_ancestors(x, [depth])` | Like `ancestors(x)`, but only traverses first parent of each commit. Useful for following the merge-target branch, excluding changes from other branches |
| `connected(x)` | Same as `x::x` — all commits both descended from and ancestral to commits in x |
| `reachable(srcs, domain)` | All commits reachable from srcs within domain, traversing parent and child edges. **Key pattern:** `reachable(@, mutable())` returns your working stack |

### Identity and Utility

| Function | Description |
|----------|-------------|
| `change_id(prefix)` | Commits with given change ID prefix (handles divergent changes) |
| `commit_id(prefix)` | Commits with given commit ID prefix |
| `present(x)` | x if all commits exist, else `none()` — prevents errors on unknown bookmarks |
| `coalesce(revsets...)` | First non-empty revset from the list. If all empty, returns `none()` |

## String Patterns

Used in functions like `bookmarks()`, `description()`, `author()`.

Since 0.37, the default pattern type is `glob` (previously `substring`). Use explicit prefixes to be clear:

| Pattern | Description | Example |
|---------|-------------|---------|
| `glob:"pattern"` | Glob pattern (default since 0.37) | `bookmarks("feature-*")` |
| `substring:"text"` | Contains text | `description(substring:"fix")` |
| `exact:"text"` | Exact match | `description(exact:"")` |
| `regex:"pattern"` | Regular expression | `author(regex:"^J.*")` |

### Case-Insensitive Matching

Append `-i` after the pattern kind to match case-insensitively:

```
glob-i:"fix*jpeg*"
exact-i:"TODO"
regex-i:"error|warning"
substring-i:"refactor"
```

### Pattern Logical Operators

String patterns support logical operators for combining:

| Operator | Description | Example |
|----------|-------------|---------|
| `~x` | Not matching x | `bookmarks(~glob:"ci/*")` |
| `x & y` | Matching both x and y | `bookmarks(glob:"feature-*" & ~glob:"*wip*")` |
| `x ~ y` | Matching x but not y | `bookmarks(glob:"release-*" ~ glob:"*rc*")` |
| `x \| y` | Matching x or y | `bookmarks(glob:"fix-*" \| glob:"bug-*")` |

### Pattern Aliases (0.39+)

Define custom pattern prefixes in the config:

```toml
[revset-aliases]
'grep:x' = 'description(regex:x)'
```

Then use as `grep:"pattern"` in revset expressions.

## Date Patterns

For `author_date()` and `committer_date()`:

| Pattern | Description | Example |
|---------|-------------|---------|
| `after:"date"` | At or after the given date | `author_date(after:"2024-01-01")` |
| `before:"date"` | Before (not including) the given date | `committer_date(before:"yesterday")` |

### Supported Date Formats

| Format | Example |
|--------|---------|
| Date only | `2024-02-01` |
| Date and time | `2024-02-01T12:00:00` |
| With timezone | `2024-02-01T12:00:00-08:00` |
| Space separator | `2024-02-01 12:00:00` |
| Relative | `2 days ago`, `5 minutes ago` |
| Named relative | `yesterday`, `yesterday 5pm`, `yesterday 15:30` |

## Revset Aliases

Define custom symbols, functions, and patterns in the config:

```toml
[revset-aliases]
HEAD = '@-'
'user()' = 'user("me@example.org")'
'user(x)' = 'author(x) | committer(x)'
```

Alias functions can be overloaded by number of parameters.

### Alias with Documentation

Aliases can include descriptions surfaced in shell completions:

```toml
[revset-aliases]
HEAD = { definition = '@-', doc = 'Parent of working copy' }
```

### Pattern Aliases (0.39+)

Custom `<name>:<value>` patterns can be defined as aliases:

```toml
[revset-aliases]
'grep:x' = 'description(regex:x)'
```

### Built-in Aliases

| Alias | Default Definition |
|-------|-------------------|
| `trunk()` | Head of default bookmark on default remote (falls back to `main`/`master`/`trunk` on `upstream`/`origin`) |
| `immutable_heads()` | `trunk() \| tags() \| untracked_remote_bookmarks()` |
| `immutable()` | `::(immutable_heads() \| root())` |
| `mutable()` | `~immutable()` |
| `builtin_immutable_heads()` | Same as default `immutable_heads()` — override `immutable_heads()` instead of this |

Override `trunk()` for custom setups:

```toml
[revset-aliases]
'trunk()' = 'your-bookmark@your-remote'
```

## Common Patterns

### Working with Current Work

```bash
# My work in progress
jj log -r 'trunk()..@'

# My working stack (all connected mutable commits)
jj log -r 'reachable(@, mutable())'

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

# Bookmarks not matching a pattern
jj log -r 'bookmarks(~glob:"ci/*")'
```

### Finding Commits

```bash
# Commits touching specific file
jj log -r 'files("src/main.rs")'

# Commits containing "TODO" in diff
jj log -r 'diff_lines("TODO")'

# Commits by specific author
jj log -r 'author("alice@")'

# Commits by author name only
jj log -r 'author_name("Alice")'

# Commits from last week
jj log -r 'committer_date(after:"1 week ago")'

# Search first line of commit message
jj log -r 'subject(glob:"fix*")'

# Signed commits in my branch
jj log -r 'signed() & trunk()..@'
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

### Operation History

```bash
# Heads visible at the previous operation
jj log -r 'at_operation(@-, visible_heads())'

# What changed since last operation
jj log -r 'at_operation(@-, @) ~ @'
```

### Safety and Assertions

```bash
# Ensure exactly one commit matches (errors otherwise)
jj log -r 'exactly(bookmarks("release-*"), 1)'

# Use present() to avoid errors on missing bookmarks
jj log -r 'present(feature-branch) | trunk()'

# First non-empty of several fallback revsets
jj log -r 'coalesce(bookmarks("main"), bookmarks("master"), trunk())'
```

## Combining Expressions

Complex queries combine operators and functions:

```bash
# My non-empty commits on feature branch, excluding conflicts
jj log -r '(mine() & feature::@) ~ (empty() | conflicts())'

# Latest 5 commits touching src/ by any author
jj log -r 'latest(files("src/**"), 5)'

# All commits between two tags
jj log -r 'v1.0::v2.0'
```

## Deprecations (0.37–0.38)

| Deprecated | Replacement |
|------------|-------------|
| `diff_contains(pattern)` | `diff_lines(pattern)` (0.38) |
| `git_head()` | `first_parent(@)` in colocated repos (0.37) |
| `git_refs()` | `remote_bookmarks(remote=glob:*) \| tags()` (0.37) |
| `all:` global config (`ui.always-allow-large-revsets`) | Removed in 0.38 — multi-revset now default for most commands |
| `file(pattern)` | `files(expression)` — now takes fileset expressions |

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

# Fork point of multiple branches:
jj log -r 'fork_point(feature-a | feature-b)'
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

### Navigating Merge History

```bash
# Follow only first-parent lineage (like git log --first-parent):
jj log -r 'first_ancestors(@, 20)'

# First parent of a merge commit:
jj log -r 'first_parent(@)'

# Commits on the merge-target branch only:
jj log -r 'first_ancestors(@) & trunk()..@'
```

### Finding Merge Commits

```bash
# All merge commits in your branch:
jj log -r 'merges() & trunk()..@'

# Commits with merge descriptions in your branch:
jj log -r 'trunk()..@ & description(glob:"*merge*")'
```

### The `all:` Prefix for Multi-Commit Arguments

Some command flags (like `-b` in rebase) expect a single commit. If your revset resolves to multiple commits, prefix with `all:`:

```bash
# ERROR: "resolved to more than one revision"
jj rebase -b wip -d main

# WORKS: prefix with all:
jj rebase -b all:wip -d main       # Rebase ALL matching branches onto main
```

Useful WIP revset alias to combine with this:

```toml
[revset-aliases]
'wip' = 'description(regex:"^\\[(wip|WIP|todo|TODO)\\]|(wip|WIP|todo|TODO):?")'
```

Then: `jj rebase -b all:wip -d main` rebases every WIP-tagged branch at once.

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
