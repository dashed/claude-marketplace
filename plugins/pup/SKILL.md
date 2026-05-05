---
name: pup
description: Datadog CLI (pup) for observability, monitoring, logs, APM, security, and infrastructure. Use when querying Datadog metrics, searching logs, managing monitors, investigating incidents, checking SLOs, running APM traces, managing dashboards, or performing any Datadog API operation via CLI. Triggers on mentions of pup, Datadog CLI, DD_API_KEY, DD_APP_KEY, or Datadog platform commands.
---

# Pup — Datadog CLI

## Overview

Pup is Datadog's AI-agent-ready CLI covering 49 command groups and 300+ subcommands across the full Datadog platform: metrics, logs, monitors, APM, traces, dashboards, SLOs, incidents, security, infrastructure, RUM, CI/CD, costs, and more.

Key traits:
- **Self-discoverable** — `pup --help` and `pup agent schema` return structured JSON schemas
- **Agent mode auto-detected** — structured JSON output in Claude Code (no setup needed)
- **OAuth2 + API key auth** — secure browser-based login or environment variable fallback
- **Structured output** — JSON (default), YAML, or table formats

## Prerequisites

```bash
brew tap datadog-labs/pack
brew install pup
```

Or build from source:

```bash
git clone https://github.com/datadog-labs/pup.git && cd pup
cargo build --release
cp target/release/pup /usr/local/bin/pup
```

Verify installation:

```bash
pup --version
```

## Authentication

### OAuth2 (Preferred)

OAuth2 provides secure, browser-based auth with automatic token refresh. Tokens are stored in your OS keychain.

```bash
pup auth login           # Opens browser for OAuth2 flow
pup auth status          # Check token validity
pup auth refresh         # Refresh expired token (no browser needed)
pup auth logout          # Clear credentials
```

**Tokens expire after ~1 hour.** If a command returns 401/403:

```bash
pup auth refresh         # Try this first
pup auth login           # Full re-auth if refresh fails
```

### API Keys (Legacy / CI)

For headless environments or when OAuth2 is unavailable:

```bash
export DD_API_KEY="your-api-key"
export DD_APP_KEY="your-app-key"
export DD_SITE="datadoghq.com"       # Default; change for EU/other sites
```

### Authentication Priority

1. `DD_ACCESS_TOKEN` — Stateless bearer token (highest priority)
2. OAuth2 tokens (from `pup auth login`)
3. API keys (`DD_API_KEY` + `DD_APP_KEY`)

### Datadog Sites

| Site | `DD_SITE` value |
|------|-----------------|
| US1 (default) | `datadoghq.com` |
| US3 | `us3.datadoghq.com` |
| US5 | `us5.datadoghq.com` |
| EU1 | `datadoghq.eu` |
| AP1 | `ap1.datadoghq.com` |
| US1-FED | `ddog-gov.com` |

## Agent Mode

Agent mode is **auto-detected** in Claude Code via the `CLAUDE_CODE` environment variable. No setup required.

What changes in agent mode:

| Behavior | Human Mode | Agent Mode |
|----------|-----------|------------|
| `--help` output | Standard text | Structured JSON schema |
| Confirmations | Interactive prompt | Auto-approved |
| Error format | Human text | Structured JSON with error codes and suggestions |
| API responses | Raw data | Envelope with metadata (count, truncation, warnings) |

### Schema Discovery

```bash
pup --help                    # Full JSON schema (auto in agent mode)
pup logs --help               # Domain-specific schema
pup agent schema              # Explicit full schema (works in any mode)
pup agent schema --compact    # Minimal schema (fewer tokens)
pup agent guide               # Full steering guide (markdown)
```

Use `pup agent schema` when unsure about a command's flags or syntax.

## Command Patterns

All commands follow a consistent structure:

```bash
pup <domain> <action> [flags]              # Simple commands
pup <domain> <subgroup> <action> [flags]   # Nested commands
```

### CRUD Operations

```bash
pup <resource> list [--filters]            # List/search
pup <resource> get <id>                    # Get by ID
pup <resource> create [--file=data.json]   # Create from JSON
pup <resource> update <id> [--file=...]    # Update
pup <resource> delete <id> [--yes]         # Delete (--yes skips confirmation)
```

## Quick Reference

### Core Observability

| Task | Command |
|------|---------|
| Search error logs | `pup logs search --query="status:error" --from=1h` |
| Count logs by service | `pup logs aggregate --query="*" --from=1h --compute="count" --group-by="service"` |
| P99 latency by service | `pup logs aggregate --query="env:prod" --from=30m --compute="percentile(@duration, 99)" --group-by="service"` |
| Query CPU metrics | `pup metrics query --query="avg:system.cpu.user{*}" --from=1h` |
| List metrics | `pup metrics list --filter="system.*"` |
| Search traces | `pup traces search --query="service:api AND @duration:>1000000000" --from=1h` |
| List APM services | `pup apm services list --env=production` |

### Monitoring & Alerting

| Task | Command |
|------|---------|
| List monitors | `pup monitors list` |
| Filter by tags | `pup monitors list --tags="env:production"` |
| Search monitors | `pup monitors search --query="status:Alert"` |
| List dashboards | `pup dashboards list` |
| Get dashboard URL | `pup dashboards url abc-123 --from=now-1w --to=now --live=true` |
| List SLOs | `pup slos list` |
| SLO status | `pup slos status slo-123 --from=30d --to=now` |
| Synthetics tests | `pup synthetics tests list` |

### Incidents & Operations

| Task | Command |
|------|---------|
| List incidents | `pup incidents list` |
| Get incident | `pup incidents get <incident-id>` |
| List events | `pup events list --from=4h` |
| On-call teams | `pup on-call teams list` |
| Service context | `pup idp assist my-service` |
| Service dependencies | `pup idp deps my-service` |
| Who owns a service | `pup idp owner my-service` |

### Security

| Task | Command |
|------|---------|
| Security signals | `pup security signals list --from=24h` |
| Security rules | `pup security rules list` |
| Critical findings | `pup security findings search --query="@severity:critical"` |
| Audit logs | `pup audit-logs list --from=7d` |

### Infrastructure

| Task | Command |
|------|---------|
| List hosts | `pup infrastructure hosts list` |
| Filter hosts | `pup infrastructure hosts list --filter="env:production"` |
| Host tags | `pup tags list` |
| Containers | `pup containers list` |
| Fleet agents | `pup fleet agents list --filter="hostname:my-host"` |

### Live Debugger

| Task | Command |
|------|---------|
| Find probe-able methods | `pup symdb search --service=my-svc --query=MyController --view=probe-locations` |
| Create log probe | `pup debugger probes create --service=my-svc --env=prod --probe-location="com.example.MyClass:myMethod" --capture="request.id" --ttl=1h` |
| Watch probe events | `pup debugger probes watch <probe-id> --fields="message,captures,timestamp" --limit=10` |

## Output Formats

```bash
pup monitors list --output=json    # JSON (default, best for agents)
pup monitors list --output=table   # Human-readable table
pup monitors list --output=yaml    # YAML
pup monitors list --fields="id,name,status"  # Custom field selection
```

## Time Range Formats

All `--from` and `--to` flags accept these formats:

| Format | Example |
|--------|---------|
| Relative short | `1h`, `30m`, `7d`, `5s`, `1w` |
| Relative long | `5min`, `2hours`, `3days` |
| With spaces | `"5 minutes"`, `"2 hours"` |
| RFC3339 | `2024-01-01T00:00:00Z` |
| Unix ms | `1704067200000` |
| Keyword | `now` |

## Query Syntax

### Logs

```
status:error                        # Filter by status
service:web-app                     # Filter by service
@user.id:12345                      # Custom attribute (@ prefix)
host:i-*                            # Wildcard matching
"exact error message"               # Exact phrase
status:error AND service:web        # Boolean AND
status:error OR status:warn         # Boolean OR
-status:info                        # Negation
@http.status_code:[400 TO 599]     # Numeric range
```

### Metrics

```
avg:system.cpu.user{env:prod} by {host}       # CPU by host
sum:trace.servlet.request.hits{service:web}   # Request count
max:system.mem.used{*} by {host}              # Max memory
```

### APM / Traces

**CRITICAL: Durations are in NANOSECONDS**
- 1ms = 1,000,000 ns
- 1s = 1,000,000,000 ns
- 5s = 5,000,000,000 ns

```
service:api-gateway                            # Filter by service
resource_name:/api/v1/users                    # Filter by endpoint
@duration:>5000000000                          # Duration > 5s (nanoseconds!)
status:error                                   # Error spans only
env:production                                 # Filter by environment
```

## Error Handling

| Status | Meaning | Fix |
|--------|---------|-----|
| 401 | Authentication failed | `pup auth refresh` or check `DD_API_KEY`/`DD_APP_KEY` |
| 403 | Insufficient permissions | Verify API/App key scopes |
| 404 | Resource not found | Check the resource ID |
| 429 | Rate limited | Wait and retry with backoff |
| 5xx | Server error | Retry after delay; check `https://status.datadoghq.com/` |

## Best Practices

1. **Always specify `--from`** — most commands default to 1h but be explicit
2. **Start narrow, widen later** — begin with 1h, expand to 24h/7d only if needed
3. **Filter at the API level** — use `--tags`, `--query`, `--name` flags instead of fetching everything
4. **Use `aggregate` for counts** — `pup logs aggregate --compute=count`, not fetch-all-and-count
5. **APM durations are nanoseconds** — 1s = 1,000,000,000 (not seconds or milliseconds)
6. **Chain queries** — aggregate first to find patterns, then search for specifics
7. **Use `pup agent schema`** when unsure about a command's flags

## Anti-Patterns

1. **Don't omit `--from`** on time-series queries — you'll get unexpected ranges or errors
2. **Don't use `--limit=1000` first** — start small (`--limit=20`) and refine
3. **Don't list all monitors without filters** in large orgs (>10k monitors)
4. **Don't assume durations are in seconds** — APM uses nanoseconds
5. **Don't fetch raw logs to count them** — use `pup logs aggregate --compute=count`
6. **Don't retry 401/403 errors** — re-authenticate or check permissions instead
7. **Don't use `--from=30d`** unless you specifically need a month of data

## Common Workflows

### Error Investigation

```bash
# 1. Get error counts by service
pup logs aggregate --query="status:error" --from=1h --compute="count" --group-by="service"

# 2. Drill into affected service
pup logs search --query="status:error AND service:<name>" --from=1h --limit=20

# 3. Check monitors for that service
pup monitors list --tags="service:<name>"

# 4. Check recent events
pup events list --from=4h
```

### Performance Investigation

```bash
# 1. Check service latency
pup metrics query --query="avg:trace.servlet.request.duration{service:<name>} by {resource_name}" --from=1h

# 2. Find slow traces (>5 seconds — note nanoseconds!)
pup traces search --query="service:<name> AND @duration:>5000000000" --from=1h

# 3. Check resource utilization
pup metrics query --query="avg:system.cpu.user{service:<name>} by {host}" --from=1h
```

### Service Health Overview

```bash
pup idp assist <service-name>       # Full context: owner, on-call, health, deps
pup slos list                       # Check SLO compliance
pup monitors list --tags="team:<team>"
pup incidents list --query="status:active"
```

## Global Flags

| Flag | Description |
|------|-------------|
| `-o, --output` | Output format: `json`, `table`, `yaml` (default: `json`) |
| `-y, --yes` | Skip confirmation prompts for destructive operations |
| `--read-only` | Block all write operations (create, update, delete) |
| `--verbose` | Enable verbose logging |
| `--site` | Datadog site override (default: `datadoghq.com`) |
| `--config` | Config file path (default: `~/.config/pup/config.yaml`) |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DD_ACCESS_TOKEN` | Bearer token for stateless auth (highest priority) |
| `DD_API_KEY` | Datadog API key |
| `DD_APP_KEY` | Datadog Application key |
| `DD_SITE` | Datadog site (default: `datadoghq.com`) |
| `DD_AUTO_APPROVE` | Auto-approve destructive operations (`true`/`false`) |
| `DD_TOKEN_STORAGE` | Token storage backend: `keychain` or `file` |
| `DD_READ_ONLY` | Block all write operations (`true`/`false`) |

## Advanced Usage

For detailed documentation beyond this quick reference, see:

- [references/commands-reference.md](references/commands-reference.md) — Full command reference across all 49 command groups
- [references/workflows.md](references/workflows.md) — Operational workflows: incident response, security audit, infrastructure review, runbooks
- [references/query-syntax.md](references/query-syntax.md) — Complete query syntax for logs, metrics, traces, RUM, and monitors
- [references/advanced-features.md](references/advanced-features.md) — Runbooks, ACP server, Live Debugger, IDP, fleet management, workflows, cost management

### Runbooks (Local Execution Engine)

YAML-defined multi-step operational procedures stored in `~/.config/pup/runbooks/`:

```bash
pup runbooks list                                              # List available runbooks
pup runbooks describe incident-triage                          # Inspect steps
pup runbooks run deploy-service --arg SERVICE=payments --arg VERSION=1.2.3
pup runbooks run deploy-service --dry-run                      # Preview without executing
```

### ACP Server (Datadog AI Agent Integration)

Turns pup into a local AI agent server for Bits AI:

```bash
pup acp serve                        # Start server (auto-discovers Bits AI agent)
pup acp serve --agent-id <uuid>      # Target specific agent
```

Exposes ACP and OpenAI-compatible endpoints at `http://127.0.0.1:9099`.
