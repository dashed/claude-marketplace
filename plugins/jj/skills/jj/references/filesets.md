# Fileset Reference

## Overview

Filesets select files in jj commands using a functional language. Many commands accept fileset expressions as positional arguments. The language consists of file patterns, operators, and functions.

## File Patterns

By default, bare paths are parsed as `prefix-glob:` patterns (CWD-relative prefix match).

| Pattern | Description | Example |
|---------|-------------|---------|
| (default) `prefix-glob:` | CWD-relative path prefix (recursive) | `jj diff src` |
| `cwd:"path"` | CWD-relative path prefix (recursive) | `cwd:"src/lib"` |
| `file:"path"` / `cwd-file:` | Exact file match (CWD-relative) | `file:"README.md"` |
| `glob:"pattern"` / `cwd-glob:` | Unix shell wildcard (CWD-relative) | `glob:"*.rs"` |
| `prefix-glob:"pattern"` | Glob + directory recursion | `prefix-glob:"*.d"` |
| `root:"path"` | Workspace-relative prefix (recursive) | `root:"src"` |
| `root-file:"path"` | Workspace-relative exact match | `root-file:"Cargo.toml"` |
| `root-glob:"pattern"` | Workspace-relative glob | `root-glob:"**/*.py"` |
| `root-prefix-glob:"pattern"` | Workspace-relative glob + recursion | `root-prefix-glob:"*.d"` |

### Case-Insensitive Matching

Append `-i` to any glob pattern name: `glob-i:"*.TXT"` matches both `file.txt` and `FILE.TXT`.

## Operators

Listed strongest to weakest binding power. Same-precedence infix operators are left-associative.

| Precedence | Operator | Description |
|------------|----------|-------------|
| 1 (strongest) | `f(x)` | Function call |
| 2 | `p:x` | File pattern or pattern alias |
| 3 | `~x` | Negation — matches everything except `x` |
| 4 | `x & y` | Intersection — matches both `x` and `y` |
| 4 | `x ~ y` | Difference — matches `x` but not `y` |
| 5 (weakest) | `x \| y` | Union — matches `x` or `y` (or both) |

Use parentheses to override precedence: `(x | y) & z`.

Note: `x ~ y & z` parses as `(x ~ y) & z` (same precedence, left-to-right).

## Functions

- `all()` — matches every file
- `none()` — matches no files

## Aliases (0.39+)

Define custom symbols, functions, and `<name>:<value>` patterns in config:

```toml
[fileset-aliases]
LOCK = '**/Cargo.lock | **/package-lock.json | **/uv.lock'
'not:x' = '~x'
```

Alias functions can be overloaded by parameter count. Builtins are shadowed by name.

### Alias Descriptions

Add documentation visible in shell completions:

```toml
[fileset-aliases]
LOCK = { definition = '**/Cargo.lock | **/package-lock.json', doc = 'Lockfiles' }
```

## Quoting Rules

Quotes around file names are optional if the expression has no operators or function calls:

- `jj diff 'Foo Bar'` — shell quotes needed, inner quotes optional
- `jj diff '~"Foo Bar"'` — both shell and inner quotes needed (has `~` operator)
- `jj diff '"Foo(1)"'` — both needed (parentheses are meta characters)

Glob characters (`*`, `?`) are not meta characters but still need shell quoting:

- `jj diff '~glob:**/*.rs'`

## Practical Examples

```bash
# Show diff excluding a lock file
jj diff '~Cargo.lock'

# List files in src/ excluding Rust sources
jj file list 'src ~ glob:"**/*.rs"'

# Split revision, putting foo into the second commit
jj split '~foo'

# Show only Python files in current directory
jj diff 'glob:"*.py"'

# Show all test files workspace-wide
jj diff 'root-glob:"**/test_*.py"'

# Combine patterns: Rust files but not tests
jj diff 'glob:"**/*.rs" ~ glob:"**/tests/**"'

# Use a custom alias after defining LOCK in config
jj diff '~LOCK'

# Case-insensitive match for markdown files
jj file list 'glob-i:"*.MD"'
```
