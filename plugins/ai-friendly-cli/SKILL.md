---
name: ai-friendly-cli
description: Build and refactor CLIs for AI agent compatibility. Use when making command-line interfaces machine-readable, adding structured JSON output, hardening inputs against hallucinations, implementing safety rails like dry-run flags, adding schema introspection, or designing multi-surface architectures (CLI + MCP).
---

# AI-Friendly CLI

## Overview

Human DX optimizes for discoverability and forgiveness. Agent DX optimizes for predictability and defense-in-depth. These require fundamentally different design approaches.

This skill provides 8 principles for building or refactoring command-line interfaces so that AI agents can invoke them reliably, safely, and efficiently. The core insight: agents hallucinate inputs, pay per token, and can't read interactive prompts. Your CLI must defend against all three.

## When to Use

Use this skill when:

- **Adding AI/agent support** to an existing CLI tool
- **Building a new CLI** that agents will invoke
- **Wrapping an API** as a CLI tool (REST, GraphQL, gRPC)
- **Designing MCP servers** alongside CLI interfaces
- **Hardening inputs** against hallucinated or malformed agent inputs
- **Reducing token cost** by limiting response sizes
- **Adding structured output** (JSON, NDJSON) to human-oriented CLIs

## The 8 Principles

### 1. Structured JSON I/O

Support `--json` for structured input payloads and `--output json` for machine-readable output. When stdout is not a TTY, default to NDJSON.

**Why**: Agents parse structured data. Tabular or prose output requires brittle regex parsing that breaks across versions.

**Example** -- instead of 10 separate flags:
```bash
# Human-friendly (many flags)
cli create-issue --title "Bug" --assignee alice --priority high --label bug

# Agent-friendly (single structured payload)
cli create-issue --json '{"title":"Bug","assignee":"alice","priority":"high","labels":["bug"]}'
```

Both should produce structured output:
```bash
cli create-issue --json '{"title":"Bug"}' --output json
# {"id":"ISS-42","title":"Bug","status":"open","url":"https://..."}
```

### 2. Schema Introspection

Make the CLI self-documenting with machine-readable method signatures. Add a `schema` subcommand or `--describe` flag that returns parameters, types, and constraints as JSON.

**Why**: Agents need to know what parameters exist, what types they accept, and what values are valid -- without parsing `--help` prose.

**Example**:
```bash
cli schema issues.create
# {
#   "method": "issues.create",
#   "params": {
#     "title": {"type": "string", "required": true},
#     "assignee": {"type": "string", "enum": ["alice","bob"]},
#     "priority": {"type": "string", "enum": ["low","medium","high"]}
#   }
# }
```

The CLI becomes the canonical source of truth, eliminating stale documentation.

### 3. Context Window Discipline

Agents pay per token. API responses can be massive. Support field masks and streaming pagination to keep responses lean.

**Key patterns**:
- `--fields "id,name,status"` -- return only specified fields
- `--page-all` -- stream all pages as NDJSON instead of buffering entire arrays
- `--limit N` -- cap result count

**Example**:
```bash
# Without field mask: 50 fields per issue, 100 issues = thousands of tokens
cli issues list --output json

# With field mask: 3 fields per issue = fraction of tokens
cli issues list --output json --fields "id,title,status"
```

### 4. Input Hardening

Agents hallucinate. The CLI is the last line of defense before bad data reaches your API or filesystem.

**Validate and reject**:
- **Path traversals**: `../../etc/passwd`, `../.ssh/id_rsa`
- **Control characters**: bytes 0x00-0x1F in any string input
- **Malformed resource IDs**: values containing `?`, `#`, `%`
- **URL injection**: always percent-encode path segments; never use string interpolation

**Example**:
```bash
# Agent hallucinates a path traversal
cli files get --path "../../.ssh/id_rsa"
# {"error":"invalid_path","code":"PATH_TRAVERSAL","message":"path must not contain '..'"}

# Agent hallucinates control characters
cli issues create --json '{"title":"test\x00inject"}'
# {"error":"invalid_input","code":"CONTROL_CHAR","message":"input contains control characters"}
```

### 5. Safety Rails

Provide mechanisms for agents to validate operations before executing them, and for defending against prompt injection in response data.

**Key patterns**:
- `--dry-run` -- validate inputs and show what would happen, without executing
- `--sanitize` -- strip or escape potentially dangerous content from responses (prompt injection defense)
- Always confirm with the user before mutations

**Example**:
```bash
# Dry-run: validate and preview without side effects
cli issues delete ISS-42 --dry-run
# {"action":"delete","target":"ISS-42","status":"valid","would_delete":true}

# Sanitize: defend against prompt injection in response data
cli issues get ISS-42 --sanitize template
# Strips sequences like "IGNORE ALL PREVIOUS INSTRUCTIONS" from response fields
```

### 6. Structured Errors

Return JSON errors with codes and reasons on stdout. Print human-friendly hints on stderr. Agents parse stdout; humans read stderr. Never mix prose with JSON on the same stream.

**Example**:
```bash
cli issues get NONEXISTENT --output json
# stdout: {"error":"not_found","code":"ISSUE_NOT_FOUND","message":"Issue NONEXISTENT does not exist"}
# stderr: Hint: Run `cli issues list` to see available issues.
# exit code: 1
```

**Error JSON structure**:
```json
{
  "error": "category_name",
  "code": "SPECIFIC_ERROR_CODE",
  "message": "Human-readable description",
  "details": {}
}
```

### 7. Agent Documentation

Ship documentation alongside the CLI that encodes invariants an agent cannot discover from `--help` alone.

**Key files**:
- `SKILL.md` -- Activation triggers and common workflows
- `AGENTS.md` or `CONTEXT.md` -- Non-obvious rules, gotchas, required sequences
- Schema introspection (Principle 2) for runtime discovery

**What to document**:
- "Always use `--dry-run` before any mutation"
- "Always use `--fields` for list operations to control token cost"
- "Never pass user-provided strings directly as `--json` without escaping"
- Required ordering of operations (e.g., authenticate before query)
- Rate limits and retry semantics

### 8. Multi-Surface Architecture

One core binary, multiple interfaces: CLI for humans, MCP (JSON-RPC over stdio) for agents, environment variables for headless authentication.

**Architecture**:
```
           +------------------+
           |   Core Library   |
           +------------------+
          /         |          \
      CLI       MCP Server    REST API
   (humans)    (agents)      (services)
```

**Key patterns**:
- CLI and MCP share the same validation, business logic, and error handling
- CLI reads flags/args; MCP reads JSON-RPC params; both call the same core
- Auth via `CLI_TOKEN` env var (headless) or interactive OAuth (human)
- MCP enables richer agent integration (streaming, tool registration)

## Implementation Priority

Start here, in order. Each step builds on the previous:

1. **Add `--output json`** for machine-readable output on all commands
2. **Validate all inputs** -- reject control characters, path traversals, embedded query params
3. **Add `schema` or `--describe`** command for runtime introspection
4. **Support `--fields`** to limit response size and token cost
5. **Add `--dry-run`** for validation before any mutation
6. **Ship `CONTEXT.md`** or skill files encoding non-obvious invariants
7. **Expose MCP surface** for API-wrapping CLIs

## Quick Reference

| Flag / Pattern | Purpose | Example |
|----------------|---------|---------|
| `--output json` | Machine-readable output | `cli list --output json` |
| `--json '{...}'` | Structured input payload | `cli create --json '{"title":"Bug"}'` |
| `--fields` | Field masks (limit response) | `cli list --fields "id,name"` |
| `--dry-run` | Validate without executing | `cli delete --dry-run` |
| `--page-all` | Stream all pages as NDJSON | `cli list --page-all` |
| `schema` / `--describe` | Schema introspection | `cli schema method.name` |
| `--sanitize` | Response sanitization | `cli get --sanitize template` |
| `--limit N` | Cap result count | `cli list --limit 50` |

## Anti-Patterns

Avoid these when building agent-friendly CLIs:

- **Mixing prose with JSON on stdout** -- agents cannot reliably parse mixed output
- **Trusting agent inputs** -- validate everything; agents hallucinate paths, IDs, and parameters
- **String interpolation for URLs** -- use URL builders to prevent injection
- **Auto-executing destructive operations** -- always require confirmation or `--dry-run` first
- **Outputting secrets to stdout** -- tokens, keys, and passwords should never appear in structured output
- **Creating alias-only helpers** -- wrappers must add real value (validation, structured output), not just alias existing commands
- **Unbounded responses** -- always support field masks and pagination; agents pay per token
- **Interactive prompts** -- agents cannot respond to interactive stdin; use flags or `--json` instead

## Advanced Reference

For detailed patterns and implementation guidance, see:

- [Output Patterns](references/output-patterns.md) -- JSON, NDJSON, field masks, dual-channel (stdout/stderr)
- [Input Hardening](references/input-hardening.md) -- Path safety, URL encoding, control character validation
- [Safety Patterns](references/safety-patterns.md) -- Dry-run implementation, sanitization, confirmation flows
- [Architecture](references/architecture.md) -- Multi-surface design, schema introspection, MCP integration

## Attribution

- Blog: "Rewrite your CLI for AI Agents" by Justin Poehnelt
- Reference implementation: Google Workspace CLI (gws)
