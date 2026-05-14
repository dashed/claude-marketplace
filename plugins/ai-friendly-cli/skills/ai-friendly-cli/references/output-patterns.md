# Output Patterns

How to design CLI output that AI agents can reliably parse and act on.

## Table of Contents

- [JSON Output by Default](#json-output-by-default)
- [Dual Channel Pattern](#dual-channel-pattern)
- [NDJSON Pagination](#ndjson-pagination)
- [Field Masks](#field-masks)
- [Alternative Formats](#alternative-formats)
- [Output Flattening](#output-flattening)

## JSON Output by Default

The single most important pattern: machine-parseable output must be the default for programmatic use.

**Flag:** `--output json` (or `-o json`)

**Auto-detection:** When stdout is not a TTY, default to JSON automatically:

```python
import sys, json

def get_output_format(args):
    if args.output:
        return args.output
    if not sys.stdout.isatty():
        return "json"
    return os.environ.get("OUTPUT_FORMAT", "table")
```

**Environment variable override:** `OUTPUT_FORMAT=json` forces JSON globally, useful for wrapper scripts and agent environments. Same pattern applies in Rust, Go, Node.js -- check flag, then TTY, then env var.

**Reference:** `gws` uses `--format json` and auto-detects TTY for all commands.

## Dual Channel Pattern

Machine-parseable data goes to stdout. Human-friendly hints go to stderr. This lets agents pipe stdout into `jq` or parse it directly while ignoring stderr.

```python
import sys, json

# stdout: machine-parseable
result = {"status": "created", "id": "proj-123", "url": "https://..."}
print(json.dumps(result))

# stderr: human-friendly context
print("Created project proj-123. Open in browser: https://...", file=sys.stderr)
```

```go
// stdout: machine-parseable
json.NewEncoder(os.Stdout).Encode(result)

// stderr: human-friendly
fmt.Fprintln(os.Stderr, "Tip: use --dry-run to preview changes")
```

**Error output** also follows dual channel:

```python
# stdout: structured error
print(json.dumps({
    "error": {"code": 400, "message": "Name already exists", "reason": "conflict"}
}))

# stderr: actionable hint
print("Try a different name, or use --force to overwrite", file=sys.stderr)
```

**Key rule:** Never mix prose into stdout when `--output json` is active. An agent parsing JSON will break on unexpected text.

## NDJSON Pagination

For paginated API responses, emit one JSON object per line (Newline-Delimited JSON). This enables streaming without buffering the entire result set.

```bash
# Each line is a complete JSON object
cli list items --page-all --output json
{"id": "1", "name": "alpha"}
{"id": "2", "name": "beta"}
{"id": "3", "name": "gamma"}
```

**Implementation pattern:**

```python
def list_all_pages(client, endpoint):
    page_token = None
    while True:
        resp = client.get(endpoint, params={"pageToken": page_token})
        for item in resp["items"]:
            print(json.dumps(item), flush=True)  # flush for streaming
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
```

**Why NDJSON over JSON arrays:**
- Stream-processable: agent can act on each line as it arrives
- Memory-efficient: no need to buffer thousands of results
- Composable: `| head -5` works, `| jq 'select(.status == "active")'` works

**Reference:** `gws` uses `--page-all` to auto-paginate and emit NDJSON.

## Field Masks

Limit response fields to reduce context window consumption. Critical when an agent processes many API responses in sequence.

```bash
# Only return id and name fields
cli list files --fields "id,name"

# Nested field selection
cli list files --fields "files(id,name,mimeType)"

# Deep nesting
cli get user --fields "user(email,profile(avatar,bio))"
```

**Impact on context window:**

| Fields | Response Size | Tokens (approx) |
|--------|--------------|-----------------|
| All fields | 2.4 KB | ~800 |
| `id,name,status` | 120 B | ~40 |
| `id` only | 30 B | ~10 |

**Implementation:**

```python
def apply_field_mask(obj, fields):
    if not fields:
        return obj
    mask = parse_field_mask(fields)
    return {k: v for k, v in obj.items() if k in mask}
```

**Reference:** `gws` supports Google-style field masks via `--fields` on all list/get commands.

## Alternative Formats

Beyond JSON, support formats that are useful in different contexts:

| Format | Flag | Use Case |
|--------|------|----------|
| `json` | `--output json` | Agent parsing, piping to jq |
| `table` | `--output table` | Human reading in terminal |
| `csv` | `--output csv` | Spreadsheet import, data analysis |
| `yaml` | `--output yaml` | Config files, readability |
| `value` | `--output value` | Single-value extraction for shell scripts |

```bash
# Table: aligned columns for humans
cli list users --output table
ID      NAME        EMAIL
u-1     Alice       alice@example.com
u-2     Bob         bob@example.com

# CSV: for data pipelines
cli list users --output csv
id,name,email
u-1,Alice,alice@example.com

# Value: single field for shell assignment
USER_ID=$(cli get user --output value --fields id)
```

## Output Flattening

Nested JSON is hard to render in tabular formats. Flatten using dot notation:

```bash
# JSON output (nested):
{"user": {"email": "alice@co.com", "profile": {"role": "admin"}}}

# Table output (flattened):
USER.EMAIL          USER.PROFILE.ROLE
alice@co.com        admin

# CSV output (flattened headers):
user.email,user.profile.role
alice@co.com,admin
```

**Implementation:**

```python
def flatten(obj, prefix=""):
    flat = {}
    for k, v in obj.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            flat.update(flatten(v, key))
        else:
            flat[key] = v
    return flat
```

**When to flatten:** Only in table and CSV modes. JSON and YAML output should preserve the original structure. Flattening is a presentation concern, not a data concern.

**Reference:** `gws` auto-flattens nested responses for `--format table` and `--format csv`, preserving full structure in `--format json`.
