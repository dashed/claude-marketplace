# Input Hardening

Defensive input validation for CLIs that accept arguments from AI agents. Agents hallucinate. The CLI is the last line of defense.

## Table of Contents

- [Why Harden](#why-harden)
- [Path Traversal Prevention](#path-traversal-prevention)
- [Control Character Rejection](#control-character-rejection)
- [Resource Name Validation](#resource-name-validation)
- [URL Path Encoding](#url-path-encoding)
- [Enum Validation](#enum-validation)
- [Testing Agent Mistake Patterns](#testing-agent-mistake-patterns)

## Why Harden

AI agents generate CLI arguments from natural language. They make systematic mistakes:

- Hallucinate resource IDs that look plausible but contain query fragments (`item-123?admin=true`)
- Construct paths with `../` to reach files they've seen in other contexts
- Embed control characters from copy-pasted user content
- Double-encode URL segments when building paths from parts

A human would notice `rm -rf /` in a terminal. An agent will not. Every argument the CLI accepts from an agent must be validated as if it came from an untrusted network.

## Path Traversal Prevention

Any argument that becomes a filesystem path must be sandboxed.

```python
from pathlib import Path

def validate_safe_output_dir(dir_path: str) -> Path:
    resolved = Path(dir_path).resolve()
    cwd = Path.cwd().resolve()
    if not str(resolved).startswith(str(cwd) + "/") and resolved != cwd:
        raise ValueError(f"Path resolves outside current directory: {dir_path}")
    return resolved
```

```rust
use std::path::Path;

fn validate_safe_path(input: &str) -> Result<PathBuf, String> {
    let resolved = Path::new(input).canonicalize()
        .map_err(|e| format!("Invalid path: {e}"))?;
    let cwd = std::env::current_dir().unwrap().canonicalize().unwrap();
    if !resolved.starts_with(&cwd) {
        return Err(format!("Path escapes working directory: {input}"));
    }
    Ok(resolved)
}
```

**Checks to apply:**

| Check | Rejects | Example |
|-------|---------|---------|
| Canonicalize + sandbox | `../../../etc/passwd` | Path resolves outside CWD |
| Reject absolute paths | `/tmp/evil` | Agent should not write to arbitrary locations |
| Reject `..` segments | `uploads/../secrets/key` | Directory traversal |
| Check symlink targets | `link -> /etc/shadow` | Symlink escape |

**When to skip:** Read-only operations on paths the user explicitly provided. But never skip for agent-generated output paths.

## Control Character Rejection

Reject ASCII control characters (0x00-0x1F, 0x7F) in all string arguments. These can corrupt filenames, break terminal output, or exploit downstream parsers.

```python
import re

CONTROL_CHARS = re.compile(r'[\x00-\x1f\x7f]')

def validate_no_control_chars(value: str, field_name: str) -> str:
    if CONTROL_CHARS.search(value):
        raise ValueError(
            f"{field_name} contains control characters. "
            f"Rejected bytes: {[hex(ord(c)) for c in value if ord(c) < 0x20 or ord(c) == 0x7f]}"
        )
    return value
```

```go
func validateNoControlChars(value, fieldName string) error {
    for i, r := range value {
        if r < 0x20 || r == 0x7f {
            return fmt.Errorf("%s contains control character 0x%02x at position %d", fieldName, r, i)
        }
    }
    return nil
}
```

**Common injection vectors:** Null bytes (`\x00`) truncate C strings. Newlines (`\x0a`) inject HTTP headers. Carriage returns (`\x0d`) enable response splitting.

## Resource Name Validation

API resource names and IDs often end up in URLs. Reject characters that would alter URL semantics.

```python
UNSAFE_CHARS = set('?#%')

def validate_resource_name(name: str) -> str:
    for char in UNSAFE_CHARS:
        if char in name:
            raise ValueError(
                f"Resource name contains '{char}' which could cause "
                f"{'query injection' if char == '?' else 'fragment injection' if char == '#' else 'double-encoding'}. "
                f"Rejected: {name!r}"
            )
    return name
```

**What each character enables:**

| Character | Attack | Example |
|-----------|--------|---------|
| `?` | Query injection | `item-123?admin=true` adds query params |
| `#` | Fragment injection | `item-123#/admin` alters URL fragment |
| `%` | Double-encoding | `item%2F123` decodes to `item/123`, traverses path |

**Reference:** `gws` validates all resource name arguments before constructing API URLs.

## URL Path Encoding

When constructing API URLs from user-provided values, percent-encode all non-alphanumeric characters in path segments.

```python
import urllib.parse

def safe_url_segment(value: str) -> str:
    # Encode everything except unreserved chars (RFC 3986)
    return urllib.parse.quote(value, safe='')

# Usage in URL construction
base = "https://api.example.com"
project_id = safe_url_segment(user_input)
url = f"{base}/projects/{project_id}/files"
```

```go
import "net/url"

func safeURLSegment(value string) string {
    return url.PathEscape(value)
}
```

**Never** use string concatenation without encoding:

```python
# WRONG: agent-provided name goes directly into URL
url = f"https://api.example.com/items/{name}"

# RIGHT: encode the segment
url = f"https://api.example.com/items/{urllib.parse.quote(name, safe='')}"
```

## Enum Validation

For arguments with a defined set of valid values, reject anything outside that set with a clear error listing allowed values.

```python
VALID_FORMATS = {"json", "table", "csv", "yaml", "value"}

def validate_format(value: str) -> str:
    if value not in VALID_FORMATS:
        raise ValueError(
            f"Invalid format: {value!r}. "
            f"Must be one of: {', '.join(sorted(VALID_FORMATS))}"
        )
    return value
```

**Why explicit enumeration matters:** Agents learn valid values from error messages. A clear "must be one of: json, table, csv" teaches the agent to self-correct on the next attempt.

## Testing Agent Mistake Patterns

Fuzz your CLI with the specific mistakes AI agents make. These are not random -- they follow predictable patterns.

**Test vectors by category:**

| Category | Vectors |
|----------|---------|
| Path traversal | `../../../etc/passwd`, `/tmp/evil`, `uploads/../../escape` |
| Query injection | `resource-123?admin=true`, `name#fragment` |
| Double encoding | `resource%2F123`, `resource%252F123`, `name%3Fadmin%3Dtrue` |
| Control chars | `name\x00truncated`, `header\r\ninjection` |
| Oversized | `"a" * 10000`, `"nested/" * 500` |

**Integration test pattern:**

```python
def test_path_traversal_rejected():
    result = subprocess.run(
        ["cli", "export", "--output-dir", "../../../tmp/evil"],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "outside current directory" in result.stderr
```

Build these vectors into CI. Agents make these mistakes predictably, and your CLI should reject them with clear, parseable error messages.
