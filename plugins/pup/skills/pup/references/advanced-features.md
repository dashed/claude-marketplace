# Advanced Features Reference

Detailed documentation for pup's advanced capabilities beyond core CRUD commands.

## Table of Contents

- [Runbooks](#runbooks)
- [ACP Server (Datadog AI Agent)](#acp-server-datadog-ai-agent)
- [Live Debugger](#live-debugger)
- [IDP (Service Catalog)](#idp-service-catalog)
- [Fleet Management](#fleet-management)
- [Workflows](#workflows)
- [Extensions](#extensions)
- [Cost Management](#cost-management)
- [Agent Mode Details](#agent-mode-details)
- [Skills System](#skills-system)
- [WASM](#wasm)

---

## Runbooks

Local execution engine for YAML-defined multi-step operational procedures. Runbooks encode repeatable tasks — deployment gates, incident triage, service restarts — using multiple step types.

### Commands

```bash
pup runbooks list                              # List available runbooks
pup runbooks list --tag=type:deployment         # Filter by tag
pup runbooks describe incident-triage           # Inspect a runbook's steps
pup runbooks run deploy-service --arg SERVICE=payments --arg VERSION=1.2.3
pup runbooks run deploy-service --dry-run       # Preview without executing
pup runbooks import ./my-runbook.yaml           # Import into ~/.config/pup/runbooks/
pup runbooks validate ./my-runbook.yaml         # Validate without running
```

### Runbook Location

Runbooks live in `~/.config/pup/runbooks/`. Reusable templates go in `~/.config/pup/runbooks/_templates/`.

### Step Types

| Type | Description | Example Use |
|------|-------------|-------------|
| `pup` | Run a pup CLI command | `monitors list --tags="service:{{SERVICE}}"` |
| `shell` | Run a shell command | `kubectl rollout restart deployment/{{SERVICE}}` |
| `http` | Make an HTTP request | POST to a webhook, call an external API |
| `datadog-workflow` | Trigger a Datadog Workflow | Run a workflow by ID with input variables |
| `confirm` | Interactive confirmation | Pause for human approval before proceeding |

### Runbook YAML Format

```yaml
name: restart-service
description: Safely restart a service after checking monitors
vars:
  SERVICE:
    description: Service name
    required: true

steps:
  - name: Check active monitors
    kind: pup
    run: monitors list --tags="service:{{SERVICE}}"
    capture: MONITORS_JSON

  - name: Confirm restart
    kind: confirm
    message: "Restart {{SERVICE}}? Review monitors above."

  - name: Trigger restart workflow
    kind: datadog-workflow
    workflow_id: "abc-123"
    inputs:
      service: "{{SERVICE}}"
    on_failure: fail

  - name: Notify via webhook
    kind: http
    url: https://hooks.example.com/notify
    method: POST
    body: '{"text": "Restarted {{SERVICE}}"}'
    content_type: application/json
    on_failure: warn
```

### Step Features

| Feature | Syntax | Description |
|---------|--------|-------------|
| Variable interpolation | `{{VAR_NAME}}` | Replaced with `--arg KEY=VALUE` |
| Output capture | `capture: VAR_NAME` | Store stdout for use in later steps |
| Failure handling | `on_failure: fail\|warn\|ignore` | Control behavior on step failure |
| Optional steps | `optional: true` | Step failure doesn't stop runbook |
| Conditional execution | `when: on_success\|on_failure\|always` | Run based on prior step result |
| Polling | `poll.interval`, `poll.timeout`, `poll.until` | Repeat until condition met |

### HTTP Step Options

```yaml
- name: Call external API
  kind: http
  url: https://api.example.com/deploy
  method: POST                    # GET, POST, PUT, PATCH, DELETE
  body: '{"service": "{{SERVICE}}"}'
  body_file: ./payload.json       # Alternative: read body from file
  content_type: application/json
  headers:
    Authorization: "Bearer {{TOKEN}}"
  on_failure: warn
```

### Reusable Templates

Store shared steps in `~/.config/pup/runbooks/_templates/<name>.yaml`:

```yaml
# _templates/slack-notify.yaml
kind: http
url: "{{SLACK_WEBHOOK}}"
method: POST
body: '{"text": "{{MESSAGE}}"}'
content_type: application/json
on_failure: warn
```

Reference in any runbook:

```yaml
steps:
  - name: Notify Slack
    template: slack-notify
    # Override any template field as needed
```

---

## ACP Server (Datadog AI Agent)

`pup acp serve` turns pup into a local AI agent server, proxying requests to Datadog Bits AI. It speaks two protocols:

- **ACP** — [Agent Communication Protocol](https://agentcommunicationprotocol.dev/) for ACP-native clients
- **OpenAI-compatible** — `POST /chat/completions` for opencode, Cursor, and `@ai-sdk/openai-compatible` clients

### Setup

```bash
# Authenticate first (requires notebooks_read + notebooks_write scopes)
pup auth login

# Start server (auto-discovers your first Datadog Bits AI agent)
pup acp serve

# Target a specific agent
pup acp serve --agent-id <uuid>

# Custom port and bind address
pup acp serve --port 8080 --host 0.0.0.0
```

Default: `http://127.0.0.1:9099`

### Endpoints

| Method | Path | Protocol | Description |
|--------|------|----------|-------------|
| GET | `/agent.json` | ACP | Agent card / capability discovery |
| POST | `/runs` | ACP | Synchronous run |
| POST | `/runs/stream` | ACP | Streaming run (SSE) |
| GET | `/models` | OpenAI | Model list |
| POST | `/chat/completions` | OpenAI | Chat completions (sync or streaming) |

V1-prefixed paths (`/v1/models`, `/v1/chat/completions`) also work.

### Testing with curl

```bash
# ACP sync
curl -s -X POST http://127.0.0.1:9099/runs \
  -H "Content-Type: application/json" \
  -d '{"input": [{"role": "user", "content": [{"type": "text", "text": "list my monitors with status alert"}]}]}' \
  | jq .output[0].content[0].text

# OpenAI-compatible
curl -s -X POST http://127.0.0.1:9099/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "datadog-ai", "messages": [{"role": "user", "content": "how many monitors are alerting?"}]}' \
  | jq .choices[0].message.content
```

### opencode Integration

Add to `~/Library/Application Support/opencode/opencode.jsonc` (macOS):

```jsonc
{
  "provider": {
    "datadog": {
      "name": "Datadog AI",
      "npm": "@ai-sdk/openai-compatible",
      "models": { "datadog-ai": { "name": "Datadog AI Agent" } },
      "options": { "baseURL": "http://127.0.0.1:9099" }
    }
  }
}
```

---

## Live Debugger

Remote log probe management for inspecting runtime values in production without redeploying.

### Workflow: Find, Probe, Watch

```bash
# 1. Check service context (verify environment has active instances)
pup debugger context my-service
pup debugger context my-service --env prod

# 2. Search for probe-able methods
pup symdb search --service=my-service --query=MyController --view=probe-locations

# 3. Create a log probe with capture expressions
pup debugger probes create \
  --service=my-service --env=prod \
  --probe-location="com.example.MyController:handleRequest" \
  --capture="request.id" --capture="request.headers" \
  --ttl=1h

# 4. Watch probe events (compact output)
pup debugger probes watch <probe-id> \
  --fields="message,captures,timestamp" \
  --timeout=60 --limit=10 --wait=5
```

### Probe Location Formats

```
com.example.MyClass:myMethod                     # Type:Method
com.example.MyClass:myMethod(String, int)        # With signature (for overloaded methods)
```

### Probe Creation Options

| Flag | Description |
|------|-------------|
| `--service` | Target service name (required) |
| `--env` | Target environment (required) |
| `--probe-location` | Type:Method to instrument (required) |
| `--capture` | Expressions to capture (repeatable) |
| `--capture` (no args) | Full snapshot capture |
| `--template` | Custom log template: `"User {userId} called, took {@duration}ms"` |
| `--condition` | Only fire when condition is true: `"userId != null"` |
| `--depth` | Capture depth for nested objects (default: 1) |
| `--budget` | Max snapshots per second (default: 100) |
| `--ttl` | Auto-delete after duration: `1h`, `30m` |

### Watch Options

| Flag | Description |
|------|-------------|
| `--fields` | Select output fields: `message`, `captures`, `timestamp` |
| `--limit` | Max events to show |
| `--timeout` | Stop watching after N seconds |
| `--wait` | Wait N seconds for probe to become active |
| `--from` | Start from a specific time |

### SymDB Search Views

```bash
pup symdb search --service=my-service --query=MyController --view=full             # Full JSON
pup symdb search --service=my-service --query=MyController --view=names            # Scope names only
pup symdb search --service=my-service --query=MyController --view=probe-locations  # Type:Method format
```

### Pipeline: Search, Create, Watch

```bash
pup symdb search --service=my-svc --query=MyController --view=probe-locations \
  | head -1 \
  | xargs -I{} pup debugger probes create --service=my-svc --env=staging --probe-location={} --capture --ttl=1h \
  | jq -r .data.id \
  | xargs -I{} pup debugger probes watch {} --fields="message,captures,timestamp" --wait=30 --limit=5
```

### Manage Probes

```bash
pup debugger probes list --service=my-service
pup debugger probes get <probe-id>
pup debugger probes delete <probe-id>
```

---

## IDP (Service Catalog)

Agent-native access to the Datadog Service Catalog. Provides service context, ownership, and dependency information in a single call.

### Commands

```bash
# Full service context (owner, on-call, health, deps, metadata gaps, suggested actions)
pup idp assist my-service

# Search entities by name (defaults to kind:service)
pup idp find payments
pup idp find "kind:team AND name:backend"

# Ownership and on-call responders
pup idp owner my-service

# Upstream/downstream service dependencies
pup idp deps my-service

# Register a service definition
pup idp register service.datadog.yaml
```

### Incident Response with IDP

```bash
# Get full context immediately
pup idp assist payments-api

# Check alerts for the service
pup monitors list --tags="service:payments-api"

# Who is on-call?
pup idp owner payments-api

# What services might be affected?
pup idp deps payments-api
```

---

## Fleet Management

Manage Datadog Agents, deployments, schedules, and tracers across your infrastructure.

### Agents

```bash
pup fleet agents list
pup fleet agents list --filter="hostname:my-host"
pup fleet agents list --filter="(hostname:host-a OR hostname:host-b) AND env:prod"
pup fleet agents get <agent-key>
pup fleet agents versions                       # Agent version distribution
pup fleet agents tracers <agent-key>            # Tracers on a specific agent
```

### Deployments

```bash
pup fleet deployments list
pup fleet deployments get <deployment-id>
pup fleet deployments configure <deployment-id> --file=config.json
pup fleet deployments upgrade <deployment-id>
pup fleet deployments cancel <deployment-id>
```

### Schedules

```bash
pup fleet schedules list
pup fleet schedules get <schedule-id>
pup fleet schedules create --file=schedule.json
pup fleet schedules update <schedule-id> --file=schedule.json
pup fleet schedules delete <schedule-id>
pup fleet schedules trigger <schedule-id>
```

### Tracers and Clusters

```bash
pup fleet tracers list
pup fleet tracers list --filter="env:prod"
pup fleet clusters list
pup fleet clusters list --filter="cluster_name:production"
pup fleet instrumented-pods list <cluster-name>
```

---

## Workflows

Datadog Workflow Automation — create, manage, and execute workflows.

**Auth note:** All workflow commands require `DD_API_KEY` + `DD_APP_KEY`. OAuth2 bearer tokens are not supported.

### Commands

```bash
# CRUD
pup workflows get <workflow-id>
pup workflows create --file=workflow.json
pup workflows update <workflow-id> --file=workflow.json
pup workflows delete <workflow-id>

# Execute
pup workflows run <workflow-id> --payload='{"key": "value"}'
pup workflows run <workflow-id> --payload-file=params.json
pup workflows run <workflow-id> --wait                       # Wait for completion (default 5m timeout)
pup workflows run <workflow-id> --wait --timeout=2m          # Custom timeout

# Manage instances
pup workflows instances list <workflow-id>
pup workflows instances list <workflow-id> --limit=20 --page=2
pup workflows instances get <workflow-id> <instance-id>
pup workflows instances cancel <workflow-id> <instance-id>

# Manage connections
pup workflows connections get <connection-id>
pup workflows connections create --file=connection.json
pup workflows connections update <connection-id> --file=connection.json
pup workflows connections delete <connection-id>
```

---

## Extensions

Standalone executables that add new subcommands to pup. When you run `pup terraform ...`, pup looks for an installed extension named `pup-terraform` and runs it with your arguments and auth credentials.

### Managing Extensions

```bash
# Install from GitHub
pup extension install owner/repo
pup extension install owner/repo --tag v1.0.0    # Specific version

# Install from local file
pup extension install --local /path/to/pup-my-tool
pup extension install --local /path/to/pup-my-tool --link   # Symlink (dev)

# List installed
pup extension list

# Upgrade
pup extension upgrade my-tool        # Single extension
pup extension upgrade --all           # All extensions

# Remove
pup extension remove my-tool
```

### Auth Forwarding

Extensions automatically receive pup's auth credentials via environment variables:

| Variable | Set When |
|----------|----------|
| `DD_ACCESS_TOKEN` | OAuth2 auth active |
| `DD_API_KEY` | API key configured |
| `DD_APP_KEY` | App key configured |
| `DD_SITE` | Always |
| `PUP_AGENT_MODE` | Agent mode |
| `PUP_AUTO_APPROVE` | `--yes` or agent mode |
| `PUP_READ_ONLY` | Read-only mode |
| `PUP_OUTPUT` | Output format |

Pup refreshes OAuth2 tokens before passing them, so extensions always get valid credentials.

### Writing Extensions

Any executable named `pup-<name>` works (shell scripts, compiled binaries, Python scripts). Names must be lowercase letters, digits, and hyphens, starting with a letter.

---

## Cost Management

### Datadog Costs

```bash
pup costs datadog projected                      # Projected cost for current month
pup costs datadog attribution --start="2024-01-01T00:00:00Z"
pup costs datadog by-org --start-month="2024-01-01T00:00:00Z" --end-month="2024-03-01T00:00:00Z"
```

### Cloud Cost Configs

```bash
# AWS, Azure, GCP config management (list, get, create, delete each)
pup costs datadog aws-config list
pup costs datadog azure-config list
pup costs datadog gcp-config list
```

### Cloud Cost Management (CCM)

```bash
pup costs ccm custom-costs list                  # Uploaded cost files
pup costs ccm custom-costs upload --file=costs.csv
pup costs ccm tag-descriptions list              # Tag descriptions
pup costs ccm tag-metadata list --month=2024-01  # Tag metadata
pup costs ccm tags list                          # CCM tags
pup costs ccm tag-keys list                      # Tag keys
pup costs ccm budgets list                       # Budgets
pup costs ccm commitments utilization --provider=aws --product=EC2 --from=... --to=...
pup costs ccm commitments coverage --provider=aws --product=EC2 --from=... --to=...
pup costs ccm commitments savings --provider=aws --product=RDS --from=... --to=...
```

---

## Agent Mode Details

### Auto-Detection

Agent mode activates when any of these environment variables are set to `1` or `true`:

| Variable | Agent |
|----------|-------|
| `CLAUDE_CODE` or `CLAUDECODE` | Claude Code |
| `CURSOR_AGENT` | Cursor |
| `CODEX` or `OPENAI_CODEX` | OpenAI Codex |
| `AIDER` | Aider |
| `CLINE` | Cline |
| `WINDSURF_AGENT` | Windsurf |
| `GITHUB_COPILOT` | GitHub Copilot |
| `AMAZON_Q` or `AWS_Q_DEVELOPER` | Amazon Q |
| `GEMINI_CODE_ASSIST` | Gemini Code Assist |
| `SRC_CODY` | Sourcegraph Cody |
| `PI_CODING_AGENT` | pi.dev |
| `FORCE_AGENT_MODE` | Manual override |

Can also be enabled with `--agent` flag or `FORCE_AGENT_MODE=1`.

### Agent Envelope Format

Successful responses:

```json
{
  "status": "success",
  "data": [ ... ],
  "metadata": {
    "count": 42,
    "truncated": false,
    "command": "monitors list",
    "warnings": []
  }
}
```

Error responses:

```json
{
  "status": "error",
  "error_code": 401,
  "error_message": "Authentication failed",
  "operation": "list monitors",
  "suggestions": [
    "Run 'pup auth login' to re-authenticate",
    "Or set DD_API_KEY and DD_APP_KEY environment variables"
  ]
}
```

---

## Skills System

Pup ships embedded skills and agents installable to AI coding assistants.

```bash
# List available skills and agents
pup skills list
pup skills list --type=skill
pup skills list --type=agent

# Install all skills for your AI assistant
pup skills install
pup skills install --target-agent=claude-code
pup skills install --target-agent=cursor

# Install a specific skill
pup skills install dd-monitors

# Show skills installation path
pup skills path
```

For Claude Code, skills install to `.claude/skills/` and agents to `.claude/agents/`.

---

## WASM

Pup compiles to WebAssembly via `wasm32-wasip2` for WASI-compatible runtimes.

### Build

```bash
rustup target add wasm32-wasip2
cargo build --target wasm32-wasip2 --no-default-features --features wasi --release
```

### Run

```bash
# With bearer token
DD_ACCESS_TOKEN="your-token" DD_SITE="datadoghq.com" \
  wasmtime run target/wasm32-wasip2/release/pup.wasm -- monitors list

# With API keys
DD_API_KEY="key" DD_APP_KEY="key" \
  wasmtime run target/wasm32-wasip2/release/pup.wasm -- monitors list
```

### Limitations

- No keychain/file token storage — use `DD_ACCESS_TOKEN` or API keys
- No browser-based OAuth login
- Networking relies on host runtime capabilities
