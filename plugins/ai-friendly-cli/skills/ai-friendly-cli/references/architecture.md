# Architecture

Structural patterns for building CLIs that serve both humans and AI agents from a single codebase.

## Table of Contents

- [Multi-Surface Model](#multi-surface-model)
- [Schema Introspection](#schema-introspection)
- [Dynamic Discovery](#dynamic-discovery)
- [Two-Phase Parsing](#two-phase-parsing)
- [MCP Integration](#mcp-integration)
- [Helper and Plugin Injection](#helper-and-plugin-injection)
- [Environment Variable Design](#environment-variable-design)

## Multi-Surface Model

One core binary exposes multiple interfaces. The API logic is written once; the surface layer adapts it to each consumer.

```
                 +------------------+
                 |  API Schema /    |
                 |  Discovery Doc   |
                 +--------+---------+
                          |
                 +--------v---------+
                 |   Core Binary    |
                 +-+----+----+----+-+
                   |    |    |    |
                   v    v    v    v
                 CLI   MCP  Ext  Env
```

**Surfaces:**

| Surface | Consumer | Transport |
|---------|----------|-----------|
| CLI | Humans, shell scripts, agents | stdin/stdout/stderr |
| MCP | AI agents (Claude, etc.) | JSON-RPC over stdio |
| Extension | IDE plugins, web UIs | Language bindings |
| Env vars | CI/CD, containers | Process environment |

**Key principle:** Each surface is a thin adapter over the same core request/response pipeline. Business logic (validation, auth, request building, response formatting) lives in the core, not in surface-specific code.

**Reference:** `gws` is a single Go binary that serves as CLI, MCP server, and library depending on invocation.

## Schema Introspection

Expose complete method signatures as structured data. This allows agents to discover capabilities at runtime rather than relying on hardcoded knowledge.

```bash
cli schema drive.files.list
```

```json
{
  "id": "drive.files.list",
  "httpMethod": "GET",
  "path": "drive/v3/files",
  "parameters": {
    "q": {"type": "string", "description": "Search query", "location": "query"},
    "fields": {"type": "string", "description": "Field selector", "location": "query"},
    "pageSize": {"type": "integer", "minimum": 1, "maximum": 1000, "location": "query"}
  }
}
```

An agent calls `cli schema <method>` to learn exactly what parameters a command accepts, their types, and constraints -- then constructs a valid invocation without guessing.

**Reference:** `gws` builds schemas dynamically from Google API Discovery Documents.

## Dynamic Discovery

Build the CLI command tree from API schemas at runtime. No hardcoded API surfaces means the CLI automatically supports new APIs without code changes.

```bash
# List all available services
cli services list

# List methods for a service
cli services methods drive

# Get details for a method
cli schema drive.files.create
```

**How it works:**

1. Fetch or cache API schema (Discovery Document, OpenAPI spec)
2. Parse schema into internal command tree
3. Map API methods to CLI subcommands dynamically

```python
def build_command_tree(schema):
    tree = {}
    for resource_name, resource in schema["resources"].items():
        for method_name, method in resource["methods"].items():
            cmd_path = f"{resource_name}.{method_name}"
            tree[cmd_path] = Command(
                name=cmd_path,
                http_method=method["httpMethod"],
                path=method["path"],
                parameters=method.get("parameters", {}),
            )
    return tree
```

**Benefits:**
- New API version? Update the schema, CLI adapts automatically
- New service? Add its schema, get full CLI support
- Agent discovers commands at runtime -- no stale documentation

## Two-Phase Parsing

When commands are dynamic, argument parsing happens in two phases:

**Phase 1: Identify the service and method**

```
cli drive files list --query "name contains 'report'"
     ^     ^     ^
     |     |     +-- method
     |     +-------- resource
     +-------------- service
```

Parse just enough to identify which API method the user wants. No validation of method-specific arguments yet.

**Phase 2: Fetch schema, build dynamic parser, re-parse**

```python
def main(argv):
    # Phase 1: identify service + method
    service, method = parse_service_method(argv)

    # Phase 2: fetch schema, build parser, parse args
    schema = fetch_schema(service)
    method_schema = schema.get_method(method)
    parser = build_dynamic_parser(method_schema)
    args = parser.parse_args(argv)

    # Execute
    response = execute(method_schema, args)
    format_output(response, args.output_format)
```

**Why two phases:** You cannot build the argument parser until you know which method is being called. The method's schema defines what arguments are valid.

## MCP Integration

Expose CLI commands as MCP (Model Context Protocol) tools, giving agents typed invocation without shell escaping.

```bash
# Start MCP server exposing specific services
cli mcp --services drive,calendar,gmail
```

The CLI becomes a JSON-RPC server on stdio. Each API method becomes an MCP tool with typed `inputSchema` derived from the API schema.

**Advantages over shell invocation:**
- No shell escaping (JSON values, not string arguments)
- Typed parameters with validation from schema
- Structured errors instead of exit codes + stderr parsing

**Reference:** `gws` supports `mcp` subcommand that serves selected Google API services as MCP tools.

## Helper and Plugin Injection

Add service-specific convenience commands that go beyond raw API mapping. Use a trait/interface pattern so helpers are modular and optional.

```python
class ServiceHelper:
    def register(self, parser): ...
    def execute(self, args): ...

class DriveHelper(ServiceHelper):
    def register(self, parser):
        sub = parser.add_parser("upload", help="Upload a file to Drive")
        sub.add_argument("file", type=Path)
        sub.add_argument("--folder", help="Target folder ID")

    def execute(self, args):
        mime = detect_mime_type(args.file)
        metadata = {"name": args.file.name, "parents": [args.folder]}
        return self.client.upload(metadata, args.file, mime)
```

**When to add a helper -- "High Usefulness" test:**

| Add Helper | Skip Helper |
|------------|-------------|
| Complex multi-API orchestration (upload = create + upload + set permissions) | Simple alias (`ls` for `files.list`) |
| Format conversion (export Sheet as CSV) | Flag shorthand (`-v` for `--verbose`) |
| Non-obvious workflows (share file with specific permissions) | Renaming API concepts |

**Reference:** `gws` provides helpers for Drive upload/download, Gmail send, and Calendar quick-add -- operations that require multiple API calls or format handling.

## Environment Variable Design

Environment variables configure the CLI for headless and agent environments. Follow a consistent naming scheme.

**Naming convention:** `CLI_<CATEGORY>_<SETTING>`

| Variable | Purpose | Example |
|----------|---------|---------|
| `CLI_TOKEN` | Auth token for API access | `export CLI_TOKEN="ya29.a0..."` |
| `CLI_CREDENTIALS_FILE` | Path to credential file | `export CLI_CREDENTIALS_FILE="~/.config/cli/creds.json"` |
| `CLI_SERVICE_ACCOUNT` | Service account key file | `export CLI_SERVICE_ACCOUNT="/secrets/sa.json"` |
| `CLI_PROJECT` | Default project/workspace | `export CLI_PROJECT="my-project"` |
| `OUTPUT_FORMAT` | Default output format | `export OUTPUT_FORMAT="json"` |
| `CLI_LOG_LEVEL` | Logging verbosity | `export CLI_LOG_LEVEL="warn"` |
| `NO_COLOR` | Disable colored output | `export NO_COLOR=1` |

**Precedence (highest to lowest):**

1. Explicit CLI flags (`--output json`)
2. Environment variables (`OUTPUT_FORMAT=json`)
3. Config file (`~/.config/cli/config.yaml`)
4. Built-in defaults

```python
def resolve_config(args):
    return {
        "output": args.output
            or os.environ.get("OUTPUT_FORMAT")
            or load_config().get("output")
            or ("json" if not sys.stdout.isatty() else "table"),
        "project": args.project
            or os.environ.get("CLI_PROJECT")
            or load_config().get("project"),
    }
```

**`NO_COLOR` standard:** Respect the [no-color.org](https://no-color.org) convention. When `NO_COLOR` is set (to any value), suppress all ANSI color codes. This prevents garbled output when agents parse CLI responses.

**Reference:** `gws` follows the `CLOUDSDK_*` env var naming pattern for Google Cloud configuration, and respects `NO_COLOR`.
