# Template Language Reference

## Overview

Templates customize jj command output via the `-T`/`--template` flag. The language has literals, keywords, operators, functions, and methods. Use `self` to reference the top-level object.

In `jj log`, all 0-argument methods of the `Commit` type are available as keywords (e.g., `commit_id` equals `self.commit_id()`). In `jj op log`, `Operation` methods work the same way.

## Operators

Listed by binding power (strongest to weakest):

| Precedence | Operator | Description |
|---|---|---|
| 1 | `x.f()`, `f(x)` | Method / function call |
| 2 | `-x` | Negate integer |
| 2 | `!x` | Logical not |
| 3 | `p:x` | String pattern (or pattern alias `p`) |
| 4 | `x * y`, `x / y`, `x % y` | Multiply / divide / remainder (Integer) |
| 5 | `x + y`, `x - y` | Add / subtract (Integer) |
| 6 | `>=`, `>`, `<=`, `<` | Comparison (Integer) |
| 7 | `==`, `!=` | Equality (Boolean, ByteString, Integer, String) |
| 8 | `x && y` | Logical and (short-circuit) |
| 9 | `x \|\| y` | Logical or (short-circuit) |
| 10 | `x ++ y` | Template concatenation |

Same-precedence infix operators are left-to-right. Use parentheses to override.

## String Literals

- Double-quoted (`"..."`) — supports escapes: `\"`, `\\`, `\t`, `\r`, `\n`, `\0`, `\e`, `\xHH`
- Single-quoted (`'...'`) — no escapes, cannot contain `'`

## Global Functions

| Function | Description |
|---|---|
| `fill(width, content)` | Fill/wrap lines at given width |
| `indent(prefix, content)` | Indent non-empty lines with prefix |
| `pad_start(width, content, [fill_char])` | Right-justify content |
| `pad_end(width, content, [fill_char])` | Left-justify content |
| `pad_centered(width, content, [fill_char])` | Center content |
| `truncate_start(width, content, [ellipsis])` | Truncate from start |
| `truncate_end(width, content, [ellipsis])` | Truncate from end |
| `hash(content)` | Hash input, return hex string |
| `label(label, content)` | Apply color label (space-separated names) |
| `hyperlink(url, text, [fallback])` | OSC 8 hyperlink (requires color) |
| `raw_escape_sequence(content)` | Preserve escape sequences, strip labels |
| `replace(pattern, content, \|caps\| replacement)` | Replace pattern matches in template content (0.41+) |
| `stringify(content)` | Convert to string (strips color labels) |
| `json(value)` | Serialize value as JSON |
| `if(condition, then, [else])` | Conditional evaluation |
| `coalesce(content...)` | First non-empty content |
| `concat(content...)` | Same as `c1 ++ ... ++ cn` |
| `join(separator, content...)` | Join with separator |
| `separate(separator, content...)` | Join non-empty items with separator |
| `surround(prefix, suffix, content)` | Wrap non-empty content with prefix/suffix |
| `config(name)` | Look up config value (returns `Option<ConfigValue>`) |
| `git_web_url([remote])` | Convert git remote URL to HTTPS web URL (0.38+) |

## Key Types

### Commit

Used in `jj log` templates. Cannot be printed directly.

| Method | Return | Description |
|---|---|---|
| `.description()` | String | Commit message (usually trailing `\n`) |
| `.trailers()` | List\<Trailer> | Parsed `Key: Value` trailers from description |
| `.change_id()` | ChangeId | |
| `.commit_id()` | CommitId | |
| `.parents()` | List\<Commit> | |
| `.author()` | Signature | |
| `.committer()` | Signature | |
| `.signature()` | Option\<CryptographicSignature> | Crypto signature if signed |
| `.mine()` | Boolean | True if author email matches current user |
| `.working_copies()` | List\<WorkspaceRef> | Workspaces with this as working copy |
| `.current_working_copy()` | Boolean | True if working copy of current workspace |
| `.bookmarks()` | List\<CommitRef> | Local + remote bookmarks (tracked only if diverged) |
| `.local_bookmarks()` | List\<CommitRef> | |
| `.remote_bookmarks()` | List\<CommitRef> | |
| `.tags()` | List\<CommitRef> | Local + remote tags |
| `.local_tags()` | List\<CommitRef> | |
| `.remote_tags()` | List\<CommitRef> | |
| `.divergent()` | Boolean | Multiple visible commits share this change ID |
| `.hidden()` | Boolean | Abandoned commit |
| `.change_offset()` | Option\<Integer> | Change offset (may not be available) |
| `.immutable()` | Boolean | In immutable commit set |
| `.contained_in(revset)` | Boolean | True if in given revset (literal string) |
| `.conflict()` | Boolean | Has merge conflicts |
| `.empty()` | Boolean | Modifies no files |
| `.diff([files])` | TreeDiff | Changes from parents (optional fileset filter) |
| `.files([files])` | List\<TreeEntry> | Files in commit (optional fileset filter) |
| `.conflicted_files()` | List\<TreeEntry> | Conflicted files |
| `.root()` | Boolean | True if root commit |

### String / ByteString

Both support the same methods. String is UTF-8 guaranteed; ByteString is ASCII-compatible but not guaranteed UTF-8. Both convert to Boolean (empty = false).

| Method | Return | Description |
|---|---|---|
| `.len()` | Integer | Length in bytes |
| `.contains(needle)` | Boolean | Substring check |
| `.match(pattern)` | String | First match (empty if none) |
| `.starts_with(needle)` | Boolean | |
| `.ends_with(needle)` | Boolean | |
| `.remove_prefix(needle)` | String | Remove prefix if present |
| `.remove_suffix(needle)` | String | Remove suffix if present |
| `.trim()` | String | Remove leading/trailing whitespace |
| `.trim_start()` | String | |
| `.trim_end()` | String | |
| `.substr(start, [end])` | String | 0-based, end exclusive, negatives from end |
| `.first_line()` | String | |
| `.lines()` | List\<String> | Split excluding newlines |
| `.split(pattern, [limit])` | List\<String> | Split by pattern; limit caps element count |
| `.replace(pattern, replacement, [limit])` | String | Replace matches; supports `$0`, `$1` capture groups |
| `.upper()` | String | |
| `.lower()` | String | |
| `.escape_json()` | String | JSON-serialize the string (String type only) |

### List

Converts to Boolean (empty = false).

| Method | Return | Description |
|---|---|---|
| `.len()` | Integer | Element count |
| `.join(separator)` | Template | Concatenate with separator |
| `.filter(\|item\| expr)` | List | Filter by predicate |
| `.map(\|item\| expr)` | AnyList | Transform each element |
| `.any(\|item\| expr)` | Boolean | True if any element matches |
| `.all(\|item\| expr)` | Boolean | True if all elements match |
| `.first()` | T | First element; errors if empty (0.39+) |
| `.last()` | T | Last element; errors if empty (0.39+) |
| `.get(index)` | T | 0-based index; errors if out of bounds (0.39+) |
| `.reverse()` | List | Reversed copy (0.39+) |
| `.skip(count)` | List | Skip first N elements (0.39+) |
| `.take(count)` | List | Take first N elements (0.39+) |

`List<Trailer>` also has `.contains_key(key) -> Boolean`.

### Operation

Used in `jj op log` templates. Cannot be printed directly.

| Method | Return | Description |
|---|---|---|
| `.current_operation()` | Boolean | |
| `.description()` | String | |
| `.id()` | OperationId | |
| `.attributes()` | String | Operation attributes (0.41+, replaces `.tags()`) |
| `.time()` | TimestampRange | |
| `.user()` | String | |
| `.snapshot()` | Boolean | True if snapshot operation |
| `.workspace_name()` | String | Workspace name (empty if none) (0.40+) |
| `.root()` | Boolean | True if root operation |
| `.parents()` | List\<Operation> | |

### Timestamp

| Method | Return | Description |
|---|---|---|
| `.ago()` | String | Relative time (e.g., "2 hours ago") |
| `.format(fmt)` | String | strftime-like format string |
| `.utc()` | Timestamp | Convert to UTC |
| `.local()` | Timestamp | Convert to local timezone |
| `.after(date)` | Boolean | At or after given date |
| `.before(date)` | Boolean | Before given date |
| `.since(start)` | TimestampRange | Range from start to self (0.39+) |

### TimestampRange

| Method | Return | Description |
|---|---|---|
| `.start()` | Timestamp | |
| `.end()` | Timestamp | |
| `.duration()` | String | Human-friendly duration |

### CommitRef

Represents bookmarks and tags.

| Method | Return | Description |
|---|---|---|
| `.name()` | RefSymbol | Local bookmark/tag name |
| `.remote()` | Option\<RefSymbol> | Remote name (if remote ref) |
| `.present()` | Boolean | Ref points to a commit |
| `.conflict()` | Boolean | Ref is conflicted |
| `.normal_target()` | Option\<Commit> | Target if not conflicted |
| `.removed_targets()` | List\<Commit> | Old targets (if conflicted) |
| `.added_targets()` | List\<Commit> | New targets |
| `.tracked()` | Boolean | Tracked by a local ref |
| `.tracking_present()` | Boolean | Tracked and local ref points to a commit |
| `.tracking_ahead_count()` | SizeHint | Commits ahead of tracking local ref |
| `.tracking_behind_count()` | SizeHint | Commits behind tracking local ref |
| `.synced()` | Boolean | Synced with tracked remote(s) |

### ChangeId / CommitId

| Method | Return | Description |
|---|---|---|
| `.short([len])` | String | Shortened ID |
| `.shortest([min_len])` | ShortestIdPrefix | Shortest unique prefix |
| `.normal_hex()` | String | Standard hex (ChangeId only) |

`ShortestIdPrefix` has `.prefix()`, `.rest()`, `.upper()`, `.lower()`.

### Other Types

**Signature**: `.name() -> String`, `.email() -> Email`, `.timestamp() -> Timestamp`

**Email**: `.local() -> String` (before `@`), `.domain() -> String` (after `@`)

**CryptographicSignature**: `.status() -> String` (`"good"`, `"bad"`, `"unknown"`, `"invalid"`), `.key() -> String`, `.display() -> String`. Note: calling these methods is slow (triggers signature verification).

**Option**: Converts to Boolean (set = true). Methods of contained type can be called directly; errors if unset.

**ConfigValue**: `.as_boolean()`, `.as_integer()`, `.as_string()`, `.as_string_list()`

**SizeHint**: `.lower() -> Integer`, `.upper() -> Option<Integer>`, `.exact() -> Option<Integer>`, `.zero() -> Boolean`

**TreeDiff**: `.files() -> List<TreeDiffEntry>`, `.color_words([context])`, `.git([context])`, `.stat([width]) -> DiffStats`, `.summary()`

**TreeDiffEntry**: `.path()`, `.display_diff_path()`, `.status()`, `.status_char()`, `.source()`, `.target()`

**DiffStats**: `.files() -> List<DiffStatEntry>`, `.total_added()`, `.total_removed()`

**Trailer**: `.key() -> String`, `.value() -> String`

## Template Aliases

Define in config under `[template-aliases]`:

```toml
[template-aliases]
sh = "commit_id.short()"
'format_field(key, value)' = 'key ++ ": " ++ value ++ "\n"'
'json:x' = 'json(x) ++ "\n"'
```

Aliases support documentation for shell completions:

```toml
[template-aliases]
sh = { definition = 'commit_id.short()', doc = 'Short commit ID' }
```

Alias functions can be overloaded by parameter count. Builtin functions are shadowed by name.

## Color Labels

Templates are automatically labeled with command name, context, and method names. Discover labels with `--color=debug`. Add manual labels with `label("name", content)`.

## Practical Examples

```bash
# Short parent commit IDs
jj log -r @ -T 'parents.map(|c| c.commit_id().short()).join(",")'

# Machine-readable commit + change IDs
jj log -T 'commit_id ++ " " ++ change_id ++ "\n"'

# Description with fallback
jj log -r @ -T 'coalesce(description, "(no description set)\n")'

# Show only commits with conflicts
jj log -T 'if(conflict, description.first_line() ++ " [CONFLICT]\n")'

# Custom bookmark display
jj log -T 'separate(" ", change_id.short(), bookmarks.join(", "), description.first_line()) ++ "\n"'

# Author date in custom format
jj log -T 'author.timestamp().format("%Y-%m-%d %H:%M") ++ " " ++ description.first_line() ++ "\n"'

# Filter trailers
jj log -r @ -T 'trailers().filter(|t| t.key() == "Reviewed-by").map(|t| t.value()).join(", ")'

# JSON output
jj log -T 'json(self) ++ "\n"'
```

## Minimum Version Requirements

| Feature | Min Version |
|---|---|
| `git_web_url()` | 0.38+ |
| `.first()`, `.last()`, `.get()` on List | 0.39+ |
| `.reverse()`, `.skip()`, `.take()` on List | 0.39+ |
| `.since()` on Timestamp | 0.39+ |
| `.workspace_name()` on Operation | 0.40+ |
| `replace()` global function | 0.41+ |
| `.attributes()` on Operation (replaces `.tags()`) | 0.41+ |
