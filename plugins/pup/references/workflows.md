# Common Operational Workflows

Step-by-step pup command sequences for common Datadog operational scenarios.

## Table of Contents

1. [Error Investigation](#1-error-investigation)
2. [Performance Investigation](#2-performance-investigation)
3. [Incident Response](#3-incident-response)
4. [Security Audit](#4-security-audit)
5. [Service Health Overview](#5-service-health-overview)
6. [Infrastructure Review](#6-infrastructure-review)
7. [Cost Analysis](#7-cost-analysis)
8. [IDP-based Service Investigation](#8-idp-based-service-investigation)
9. [Live Debugger Workflow](#9-live-debugger-workflow)
10. [Runbook Execution](#10-runbook-execution)

---

## 1. Error Investigation

Aggregate errors to find patterns, then drill into specifics.

**Step 1: Get error counts by service**
```bash
pup logs aggregate --query="status:error" --from="1h" --compute="count" --group-by="service"
```

**Step 2: Drill into the affected service**
```bash
pup logs search --query="status:error AND service:<name>" --from="1h" --limit=20
```

**Step 3: Check monitors for that service**
```bash
pup monitors list --tag="service:<name>"
```

**Step 4: Check recent infrastructure events**
```bash
pup events list --from="4h"
```

**Step 5: Check error tracking for grouped issues**
```bash
pup error-tracking issues search --query="service:<name>" --from="24h"
```

---

## 2. Performance Investigation

Identify latency issues from metrics down to individual traces.

**Step 1: Check service latency metrics**
```bash
pup metrics query --query="avg:trace.servlet.request.duration{service:<name>} by {resource_name}" --from="1h"
```

**Step 2: Find slow traces (durations in nanoseconds: 1s = 1,000,000,000ns)**
```bash
pup traces search --query="service:<name> AND @duration:>5000000000" --from="1h"
```

**Step 3: Aggregate p99 latency by resource**
```bash
pup traces aggregate --query="service:<name>" --compute="percentile(@duration, 99)" --group-by="resource_name" --from="1h"
```

**Step 4: Check resource utilization for the service hosts**
```bash
pup metrics query --query="avg:system.cpu.user{service:<name>} by {host}" --from="1h"
```

**Step 5: Check profiling for hot code paths (requires API keys)**
```bash
pup profiling analytics --service <name> --env prod --from="1h"
```

---

## 3. Incident Response

Create an incident, investigate, and coordinate response.

**Step 1: Create the incident**
```bash
pup incidents create --title="<description>" --severity="SEV-2" --customer-impacted=true
```

**Step 2: Search logs for root cause**
```bash
pup logs search --query="status:error service:<name>" --from="1h" --limit=100
```

**Step 3: Check alerting monitors**
```bash
pup monitors list --tag="service:<name>"
pup monitors search --query="status:Alert"
```

**Step 4: Check who is on-call**
```bash
pup on-call teams list
```

**Step 5: Review recent deployment events**
```bash
pup events search --query="source:deploy" --from="4h"
```

**Step 6: Update incident status**
```bash
pup incidents update "<incident-id>" --status="investigating"
```

---

## 4. Security Audit

Review security posture: signals, rules, findings, and audit trail.

**Step 1: List recent security signals**
```bash
pup security signals list --from="24h"
```

**Step 2: Check active security rules**
```bash
pup security rules list
```

**Step 3: Search for critical findings**
```bash
pup security findings search --query="@severity:critical"
```

**Step 4: Analyze cloud security findings via DDSQL**
```bash
pup security findings analyze --query="SELECT severity, COUNT(*) FROM findings GROUP BY severity"
```

**Step 5: Review audit logs for suspicious activity**
```bash
pup audit-logs search --query="@action:user.login" --from="7d"
```

**Step 6: Check entity risk scores**
```bash
pup security risk-scores list
```

---

## 5. Service Health Overview

Quick health check across SLOs, monitors, and incidents.

**Step 1: Check SLO status**
```bash
pup slos list
pup slos status <slo-id> --from="30d" --to="now"
```

**Step 2: List alerting monitors for the team**
```bash
pup monitors list --tag="team:<team_name>"
pup monitors search --query="status:Alert"
```

**Step 3: Check active incidents**
```bash
pup incidents list --status="active"
```

**Step 4: Review synthetics test results**
```bash
pup synthetics tests list
```

**Step 5: Check service scorecards**
```bash
pup scorecards rules list
pup scorecards outcomes list
```

---

## 6. Infrastructure Review

Audit host inventory, tags, and resource metrics.

**Step 1: List hosts with filters**
```bash
pup infrastructure hosts list --filter="env:production" --output=table
```

**Step 2: Review host tags**
```bash
pup tags list --output=table
pup tags get "host-name"
```

**Step 3: Check resource metrics**
```bash
pup metrics query --query="avg:system.cpu.user{env:prod} by {host}" --from="1h"
pup metrics query --query="avg:system.mem.used{env:prod} by {host}" --from="1h"
```

**Step 4: Review containers**
```bash
pup containers list --filter-tags="env:production"
```

**Step 5: Check fleet agent health**
```bash
pup fleet agents list --filter "env:prod"
pup fleet agents versions
```

**Step 6: Review network flows**
```bash
pup network flows list
pup network devices list
```

---

## 7. Cost Analysis

Review projected costs, attribution, and optimization opportunities.

**Step 1: Get projected cost for current month**
```bash
pup costs datadog projected
```

**Step 2: Check cost attribution**
```bash
pup costs datadog attribution --start="2024-01-01T00:00:00Z"
```

**Step 3: Break down costs by organization**
```bash
pup costs datadog by-org --start-month="2024-01-01T00:00:00Z" --end-month="2024-03-01T00:00:00Z"
```

**Step 4: Review cloud cost budgets**
```bash
pup costs ccm budgets list
pup costs ccm budgets get <budget-id> --actual --forecast
```

**Step 5: Check commitment utilization (RI/Savings Plans)**
```bash
pup costs ccm commitments utilization --provider=aws --product=EC2 \
  --from=2024-01-01T00:00:00Z --to=2024-02-01T00:00:00Z
```

**Step 6: Find on-demand hotspots (unreserved spend)**
```bash
pup costs ccm commitments hotspots --provider=aws --product=EC2 \
  --from=2024-01-01T00:00:00Z --to=2024-02-01T00:00:00Z
```

**Step 7: Review usage summary**
```bash
pup usage summary
```

---

## 8. IDP-based Service Investigation

Use IDP commands for full service context from the Service Catalog.

**Step 1: Get full service context (owner, on-call, health, deps, gaps)**
```bash
pup idp assist <service-name>
```

**Step 2: Check who owns the service and who is on-call**
```bash
pup idp owner <service-name>
```

**Step 3: Review upstream/downstream dependencies**
```bash
pup idp deps <service-name>
```

**Step 4: Search for related services**
```bash
pup idp find <query>
```

**Step 5: Check monitors for the service**
```bash
pup monitors list --tag="service:<service-name>"
```

**Step 6: Register or update service definition if metadata is missing**
```bash
pup idp register service.datadog.yaml
pup idp assist <service-name>  # verify registration
```

---

## 9. Live Debugger Workflow

Inspect runtime values without redeploying. Create probes, capture data, and watch events.

**Step 1: Check service context (verify environment has active instances)**
```bash
pup debugger context my-service
pup debugger context my-service --env staging --fields service,language,envs
```

**Step 2: Search for probe-able methods via Symbol Database**
```bash
pup symdb search --service my-service --query MyController --view probe-locations
```

**Step 3: Create a log probe with capture expressions**
```bash
pup debugger probes create \
  --service my-service \
  --env staging \
  --probe-location "com.example.MyController:handleRequest" \
  --capture "request.id" --capture "user.name" \
  --ttl 1h
```

**Step 4: Watch probe events (stream captured data)**
```bash
pup debugger probes watch <probe-id> \
  --fields "message,captures,timestamp" \
  --wait 30 --limit 10
```

**Step 5: Clean up when done**
```bash
pup debugger probes delete <probe-id>
```

**Pipeline shortcut (search → create → watch):**
```bash
pup symdb search --service my-service --query MyController --view probe-locations \
  | head -1 \
  | xargs -I{} pup debugger probes create --service my-service --env staging --probe-location {} --capture --ttl 1h \
  | jq -r .data.id \
  | xargs -I{} pup debugger probes watch {} --fields "message,captures,timestamp" --wait 30 --limit 5
```

---

## 10. Runbook Execution

Execute predefined multi-step operational procedures.

**Step 1: List available runbooks**
```bash
pup runbooks list
pup runbooks list --tag=type:deployment
```

**Step 2: Inspect the runbook's steps before running**
```bash
pup runbooks describe <runbook-name>
```

**Step 3: Dry-run to preview execution**
```bash
pup runbooks run <runbook-name> --dry-run
```

**Step 4: Execute with required variables**
```bash
pup runbooks run deploy-service --arg SERVICE=payments --arg VERSION=1.2.3
```

**Step 5: Import a new runbook from file**
```bash
pup runbooks import ./my-runbook.yaml
```

**Step 6: Validate a runbook before importing**
```bash
pup runbooks validate ./my-runbook.yaml
```

---

## Workflow Tips

- **Always specify `--from`** — most commands default to 1h but being explicit avoids surprises.
- **Start narrow, widen later** — begin with `1h`, expand to `24h` or `7d` only if needed.
- **Use `aggregate` before `search`** — find patterns first, then drill into specifics.
- **Filter at the API level** — use `--tags`, `--query`, `--name` instead of fetching everything.
- **APM durations are in nanoseconds** — 1s = 1,000,000,000ns, 1ms = 1,000,000ns.
- **Chain queries** — pipe JSON output through `jq` for further filtering.
