# Commands Reference

Comprehensive reference for all pup CLI command groups, organized by domain category.

Run `pup --help` for the live command list, or `pup agent schema --compact` for machine-readable output.

## Table of Contents

- [Command Pattern](#command-pattern)
- [Global Flags](#global-flags)
- [Core Observability](#core-observability)
- [Monitoring & Alerting](#monitoring--alerting)
- [Security & Compliance](#security--compliance)
- [Infrastructure & Cloud](#infrastructure--cloud)
- [Incident & Operations](#incident--operations)
- [CI/CD & Development](#cicd--development)
- [Organization & Access](#organization--access)
- [Platform & Configuration](#platform--configuration)

## Command Pattern

```
pup <domain> <action> [options]
pup <domain> <subgroup> <action> [options]
```

## Global Flags

| Flag | Description | Default |
|------|-------------|---------|
| `-o, --output` | Output format: `json`, `table`, `yaml` | `json` |
| `-y, --yes` | Skip confirmation prompts | `false` |
| `--config` | Config file path | `~/.config/pup/config.yaml` |
| `--site` | Datadog site | `datadoghq.com` |
| `--verbose` | Enable verbose logging | `false` |
| `--read-only` | Block all write operations | `false` |
| `--agent` | Force agent mode (structured JSON output) | auto-detected |

---

## Core Observability

### metrics

Time-series metrics — query, list, get, search.

| Subcommand | Description |
|------------|-------------|
| `query` | Timeseries formula query (v2 API) |
| `list` | List available metrics |
| `get` | Get metric metadata |
| `search` | Classic query syntax (v1 API) |

```bash
pup metrics query --query="avg:system.cpu.user{env:prod} by {host}" --from="1h"
pup metrics list --filter="system.*"
```

### logs

Log search and analysis — search, list, aggregate.

| Subcommand | Description |
|------------|-------------|
| `search` | Search logs with query syntax |
| `list` | List log entries |
| `aggregate` | Compute statistics (count, avg, percentile) |

```bash
pup logs search --query="status:error AND service:api" --from="1h" --limit=100
pup logs aggregate --query="service:api" --from="1h" --compute="count" --group-by="service"
```

Supports storage tiers: `--storage="flex"`, `--storage="online-archives"`, `--storage="indexes"`.

### events

Infrastructure event management — list, search, get.

| Subcommand | Description |
|------------|-------------|
| `list` | List events with time filter |
| `search` | Search events by query |
| `get` | Get event by ID |

```bash
pup events list --from="24h"
pup events search --query="@user.id:12345"
```

### rum

Real User Monitoring — apps, sessions, metrics, retention, playlists, heatmaps.

| Subcommand | Description |
|------------|-------------|
| `apps` | List/get RUM applications |
| `sessions` | Search RUM sessions |
| `metrics` | List/get RUM metrics |
| `retention-filters` | List/get retention filters |
| `playlists` | Session replay playlists |
| `heatmaps` | Heatmap data |

```bash
pup rum apps list
pup rum sessions search --query="@application.id:abc-123" --from="1h"
```

### apm

APM services — list, stats, operations, resources, entities, dependencies, flow maps.

| Subcommand | Description |
|------------|-------------|
| `services list` | List services (requires `--env`) |
| `services stats` | Service statistics |
| `services operations` | List operations for a service |
| `services resources` | List resources for an operation |
| `entities list` | Entity queries |
| `dependencies list` | Service dependencies |
| `flow-map` | Service flow visualization |
| `troubleshooting list` | Instrumentation errors for a host |
| `service-config get` | Service instance metadata |
| `service-library-config get` | Tracer configuration across instances |

```bash
pup apm services list --env production
pup apm services operations --env production --service api-gateway
```

### traces

APM span search and aggregation.

| Subcommand | Description |
|------------|-------------|
| `search` | Search traces (durations in nanoseconds!) |
| `aggregate` | Aggregate trace statistics |
| `metrics` | Span-based metric definitions (list, get, create, update, delete) |

```bash
pup traces search --query="service:api AND @duration:>1000000000" --from="1h"
pup traces aggregate --query="service:api" --compute="avg(@duration)" --group-by="resource_name" --from="1h"
```

### profiling

Continuous Profiler data. Requires `DD_API_KEY` + `DD_APP_KEY` (no OAuth2).

| Subcommand | Description |
|------------|-------------|
| `aggregate` | Aggregate profiling data |
| `analysis` | Profiling analysis |
| `analytics` | Analytics queries |
| `breakdown` | Breakdown views |
| `callgraph` | Call graph data |
| `download` | Download profiles |
| `fields` | Available fields |
| `info` | Profile info |
| `list` | List profiles |
| `timeline` | Timeline view |
| `save-favorite` | Save a favorite query |

```bash
pup profiling aggregate --service my-service --env prod --from="1h"
pup profiling analytics --service my-service --env prod --from="1h"
```

### dbm

Database Monitoring query samples.

| Subcommand | Description |
|------------|-------------|
| `samples search` | Search DBM query samples |

```bash
pup dbm samples search --query="dbm_type:activity service:orders env:prod" --from="1h" --limit=10
pup dbm samples search --query="db.hostname:primary-db" --from="30m"
```

### ddsql

DDSQL queries and schema discovery.

| Subcommand | Description |
|------------|-------------|
| `table` | Run a DDSQL table query |
| `time-series` | Run a DDSQL time-series query |
| `spec` | Query specification |
| `schema tables` | List available tables |
| `schema columns` | List columns for a table |

```bash
pup ddsql table --query="SELECT * FROM security_findings LIMIT 10"
pup ddsql schema tables
```

---

## Monitoring & Alerting

### monitors

Monitor management — list, get, delete, search.

| Subcommand | Description |
|------------|-------------|
| `list` | List monitors (supports `--tag`, `--name` filters) |
| `get` | Get monitor by ID |
| `delete` | Delete monitor (use `--yes` to skip confirmation) |
| `search` | Full-text search across monitors |

```bash
pup monitors list --tag="env:prod" --tag="service:api"
pup monitors search --query="status:Alert"
```

### dashboards

Dashboard management — list, get, delete, url.

| Subcommand | Description |
|------------|-------------|
| `list` | List all dashboards |
| `get` | Get dashboard details |
| `delete` | Delete dashboard |
| `url` | Generate shareable dashboard URL |

```bash
pup dashboards list --output=table
pup dashboards url "abc-123-def" --from=now-1w --to=now --live=true
```

### slos

Service Level Objectives — list, get, delete, status.

| Subcommand | Description |
|------------|-------------|
| `list` | List SLOs (supports `--query`, `--tags-query`) |
| `get` | Get SLO details |
| `delete` | Delete SLO |
| `status` | Query SLO status (v2 API) |

```bash
pup slos list --tags-query="team:slo-app"
pup slos status slo-123 --from 30d --to now
```

### synthetics

Synthetic monitoring — tests, locations, suites.

| Subcommand | Description |
|------------|-------------|
| `tests list` | List synthetic tests |
| `tests get` | Get test details |
| `tests search` | Search tests by text |
| `locations list` | List test locations |
| `suites` | V2 suites management (search, get, create, update, delete) |

```bash
pup synthetics tests list
pup synthetics tests search --text "login"
```

### downtime

Monitor downtime management.

| Subcommand | Description |
|------------|-------------|
| `list` | List downtimes |
| `get` | Get downtime details |
| `cancel` | Cancel a downtime |

```bash
pup downtime list
pup downtime cancel abc-123-def
```

### notebooks

Investigation notebooks.

| Subcommand | Description |
|------------|-------------|
| `list` | List notebooks |
| `get` | Get notebook details |
| `delete` | Delete notebook |

```bash
pup notebooks list
pup notebooks get 12345
```

### status-pages

Status pages with components and degradation management.

| Subcommand | Description |
|------------|-------------|
| `pages` | Status page CRUD |
| `components` | Component management |
| `degradations` | Degradation tracking |

```bash
pup status-pages pages list
pup status-pages components list
```

### workflows

Workflow Automation — full CRUD plus run and instance management. Requires `DD_API_KEY` + `DD_APP_KEY`.

| Subcommand | Description |
|------------|-------------|
| `get` | Get workflow details |
| `create` | Create workflow from JSON file |
| `update` | Update existing workflow |
| `delete` | Delete workflow |
| `run` | Execute workflow (supports `--wait`, `--timeout`, `--payload`) |
| `instances list` | List workflow executions |
| `instances get` | Get instance details |
| `instances cancel` | Cancel running instance |
| `connections` | Connection management (get, create, update, delete) |

```bash
pup workflows run <workflow-id> --payload '{"key": "value"}' --wait --timeout 2m
pup workflows instances list <workflow-id>
```

### runbooks

Local YAML-defined runbook execution engine.

| Subcommand | Description |
|------------|-------------|
| `list` | List available runbooks (supports `--tag`) |
| `describe` | Inspect a runbook's steps |
| `run` | Execute runbook with `--arg KEY=VALUE` (supports `--dry-run`) |
| `import` | Copy a runbook YAML into `~/.config/pup/runbooks/` |
| `validate` | Validate runbook syntax without running |

```bash
pup runbooks run deploy-service --arg SERVICE=payments --arg VERSION=1.2.3
pup runbooks run incident-triage --dry-run
```

---

## Security & Compliance

### security

Security monitoring — rules, signals, findings, content packs, risk scores.

| Subcommand | Description |
|------------|-------------|
| `rules list/get` | Security detection rules |
| `signals list` | Security signals (with `--from` filter) |
| `findings search` | Search security findings |
| `findings analyze` | DDSQL analytics for cloud/app security findings |
| `findings schema` | Finding schema discovery |
| `content-packs` | Content pack management (list, activate, deactivate) |
| `risk-scores` | Entity risk scores |
| `asm-custom-rules` | WAF custom rules |
| `asm-exclusions` | WAF exclusion filters |

```bash
pup security signals list --from="24h"
pup security findings search --query="@severity:critical"
```

### static-analysis

Code security analysis.

| Subcommand | Description |
|------------|-------------|
| `ast` | AST analysis |
| `custom-rulesets` | Custom ruleset management (get, update, delete) |
| `custom-rules` | Custom rule management (get, create, delete, revisions) |
| `sca` | Software Composition Analysis |
| `coverage` | Analysis coverage |

```bash
pup static-analysis custom-rulesets list
pup static-analysis sca list
```

### audit-logs

Audit trail search.

| Subcommand | Description |
|------------|-------------|
| `list` | List audit log entries |
| `search` | Search audit logs |

```bash
pup audit-logs list --from="7d"
pup audit-logs search --query="@action:user.login"
```

### data-governance

Sensitive data scanning.

| Subcommand | Description |
|------------|-------------|
| `scanner-rules list` | List sensitive data scanner rules |

```bash
pup data-governance scanner-rules list
```

### csm-threats

Cloud Security Management threat detection.

| Subcommand | Description |
|------------|-------------|
| (various) | Threat rules and agent rules management |

```bash
pup csm-threats rules list
```

### agentless-scanning

Cloud agentless scanning configuration.

| Subcommand | Description |
|------------|-------------|
| `aws` | AWS scanning config (list, get, create, update, delete) |
| `gcp list` | GCP scanning config |
| `azure list` | Azure scanning config |

```bash
pup agentless-scanning aws list
pup agentless-scanning gcp list
```

### logs-restriction

Fine-grained log access control.

| Subcommand | Description |
|------------|-------------|
| `list` | List restriction queries |
| `get` | Get restriction details |
| `create` | Create restriction |
| `update` | Update restriction |
| `delete` | Delete restriction |
| `roles list/add` | Manage role associations |

```bash
pup logs-restriction list
pup logs-restriction create --file restriction.json
```

### data-deletion

GDPR/compliance data deletion requests.

| Subcommand | Description |
|------------|-------------|
| `requests list` | List deletion requests |
| `requests create` | Create deletion request |
| `requests cancel` | Cancel pending request |

```bash
pup data-deletion requests list
pup data-deletion requests create --file request.json
```

---

## Infrastructure & Cloud

### infrastructure

Host inventory management.

| Subcommand | Description |
|------------|-------------|
| `hosts list` | List hosts (supports `--filter`) |
| `hosts get` | Get host details |

```bash
pup infrastructure hosts list --filter="env:production"
pup infrastructure hosts get "host-name"
```

### network

Network monitoring — flows, devices, interfaces.

| Subcommand | Description |
|------------|-------------|
| `flows list` | List network flows |
| `devices list/get` | Device inventory |
| `devices interfaces` | Device interfaces |
| `devices tags` | Device tags |
| `interfaces list/update` | Interface management |

```bash
pup network flows list
pup network devices list
```

### tags

Host tag operations.

| Subcommand | Description |
|------------|-------------|
| `list` | List all host tags |
| `get` | Get tags for a host |
| `add` | Add tags to a host |
| `update` | Update host tags |
| `delete` | Delete tags from a host |

```bash
pup tags list
pup tags add "host-name" --tag="env:production" --tag="team:backend"
```

### cloud

Cloud provider integrations.

| Subcommand | Description |
|------------|-------------|
| `aws list` | AWS integrations |
| `aws cloud-auth persona-mappings` | AWS persona mapping CRUD |
| `gcp list` | GCP integrations |
| `azure list` | Azure integrations |
| `oci` | Oracle Cloud tenancy configs and products |

```bash
pup cloud aws list
pup cloud gcp list
```

### containers

Container inventory.

| Subcommand | Description |
|------------|-------------|
| `list` | List containers (supports `--filter-tags`, `--group-by`) |
| `images list` | List container images |

```bash
pup containers list --filter-tags="env:production"
pup containers images list
```

### processes

Process inventory.

| Subcommand | Description |
|------------|-------------|
| `list` | List processes |

```bash
pup processes list
```

---

## Incident & Operations

### incidents

Incident management.

| Subcommand | Description |
|------------|-------------|
| `list` | List incidents (supports `--status` filter) |
| `get` | Get incident details |
| `attachments` | Incident attachment management |
| `settings` | Global incident settings |
| `handles` | Incident handle management |
| `postmortem-templates` | Postmortem template management |
| `services` | Incident service CRUD |
| `teams` | Incident team CRUD |

```bash
pup incidents list --status="active"
pup incidents create --title="API Down" --severity="SEV-1"
```

### on-call

On-call team management.

| Subcommand | Description |
|------------|-------------|
| `teams` | Team CRUD with membership and role management |

```bash
pup on-call teams list
pup on-call teams get <team-id>
```

### cases

Case management with external integrations.

| Subcommand | Description |
|------------|-------------|
| `create` | Create a case |
| `get` | Get case details |
| `search` | Search cases |
| `assign` | Assign a case |
| `archive` | Archive a case |
| `projects` | Case project management |
| `jira` | Link case to Jira |
| `servicenow` | Link case to ServiceNow |
| `move` | Move case between projects |

```bash
pup cases search --query="status:open"
pup cases create --file case.json
```

### error-tracking

Error issue management.

| Subcommand | Description |
|------------|-------------|
| `issues search` | Search error tracking issues |
| `issues get` | Get error issue details |

```bash
pup error-tracking issues search --query="service:api" --from="24h"
```

### service-catalog

Service registry management.

| Subcommand | Description |
|------------|-------------|
| `list` | List services |
| `get` | Get service details |

```bash
pup service-catalog list
pup service-catalog get my-service
```

### idp

Agent-native Service Catalog access (IDP commands).

| Subcommand | Description |
|------------|-------------|
| `assist` | Full context: owner, on-call, health, deps, metadata gaps |
| `find` | Search entities by name |
| `owner` | Ownership and on-call responders |
| `deps` | Upstream/downstream dependencies |
| `register` | Register a service definition |

```bash
pup idp assist my-service
pup idp deps my-service
```

### scorecards

Service quality scoring.

| Subcommand | Description |
|------------|-------------|
| `rules list/create/update/delete` | Scorecard rule management |
| `outcomes list/batch-create` | Scorecard outcome management |

```bash
pup scorecards rules list
pup scorecards outcomes list
```

### fleet

Fleet Automation — agents, deployments, schedules, tracers, clusters.

| Subcommand | Description |
|------------|-------------|
| `agents list/get` | Agent management (supports `--filter`) |
| `agents versions` | Agent version inventory |
| `agents tracers` | Tracers for a specific agent |
| `deployments list/get/configure/upgrade/cancel` | Deployment management |
| `schedules` | Schedule CRUD (list, get, create, update, delete, trigger) |
| `tracers list` | List tracers across fleet |
| `clusters list` | List Kubernetes clusters |
| `instrumented-pods list` | List SSI-instrumented pods |

```bash
pup fleet agents list --filter "hostname:my-host"
pup fleet tracers list --filter "env:prod"
pup fleet clusters list
```

### hamr

High Availability Multi-Region connections.

| Subcommand | Description |
|------------|-------------|
| `connections get` | Get HAMR connection |
| `connections create` | Create HAMR connection |

```bash
pup hamr connections get <connection-id>
```

### investigations

Bits AI SRE investigation management.

| Subcommand | Description |
|------------|-------------|
| `list` | List investigations |
| `get` | Get investigation details |
| `trigger` | Trigger a new investigation |

```bash
pup investigations list
pup investigations trigger --file investigation.json
```

### change-requests

Change request management.

| Subcommand | Description |
|------------|-------------|
| `create` | Create change request |
| `get` | Get change request details |
| `update` | Update change request |
| `create-branch` | Create branch for change request |
| `decisions update/delete` | Manage decisions |

```bash
pup change-requests create --file change.json
pup change-requests get <request-id>
```

### debugger

Live Debugger — remote log probe management.

| Subcommand | Description |
|------------|-------------|
| `context` | Get service context (environments, instances, probe support) |
| `probes list` | List log probes |
| `probes get` | Get probe details |
| `probes create` | Create log probe with captures/conditions |
| `probes delete` | Delete a probe |
| `probes watch` | Stream probe events |

```bash
pup debugger probes create --service my-svc --env staging --probe-location "com.example.MyClass:myMethod" --capture "request.id"
pup debugger probes watch <probe-id> --fields "message,captures,timestamp" --wait 10
```

### symdb

Symbol Database — search for probe-able methods.

| Subcommand | Description |
|------------|-------------|
| `search` | Search scopes by service/query (supports `--view names/probe-locations/full`) |

```bash
pup symdb search --service my-svc --query MyController --view probe-locations
```

### software-catalog

Software Catalog (next-gen entity management).

| Subcommand | Description |
|------------|-------------|
| `entities list` | List catalog entities |
| `entities upsert` | Create/update entities |
| `kinds list` | List entity kinds |
| `relations list` | List entity relations |

```bash
pup software-catalog entities list
pup software-catalog kinds list
```

---

## CI/CD & Development

### cicd

CI/CD visibility — pipelines, events, tests, DORA, flaky tests.

| Subcommand | Description |
|------------|-------------|
| `pipelines list` | List CI/CD pipelines |
| `events list` | List CI/CD events |
| `tests` | Test events and management |
| `dora` | DORA deployment patching |
| `flaky-tests` | Flaky test management |

```bash
pup cicd pipelines list
pup cicd flaky-tests list
```

### code-coverage

Code coverage summaries.

| Subcommand | Description |
|------------|-------------|
| `branch-summary` | Branch-level coverage |
| `commit-summary` | Commit-level coverage |

```bash
pup code-coverage branch-summary --repo my-repo --branch main
pup code-coverage commit-summary --repo my-repo --sha abc123
```

### deployment-gates

Deployment gate management.

| Subcommand | Description |
|------------|-------------|
| `gates` | Gate CRUD |
| `evaluations` | Trigger gate evaluations |
| `rules` | Gate rule management |

```bash
pup deployment-gates gates list
pup deployment-gates evaluations trigger <gate-id>
```

### test-optimization

Test Optimization API.

| Subcommand | Description |
|------------|-------------|
| (various) | Test optimization queries and management |

```bash
pup test-optimization list
```

---

## Organization & Access

### users

User and role management.

| Subcommand | Description |
|------------|-------------|
| `list` | List users |
| `get` | Get user details |
| `roles` | Role management |
| `seats` | Seat assignment |
| `service-accounts` | Service account management (create, app-keys CRUD) |

```bash
pup users list
pup users roles list
```

### organizations

Organization settings.

| Subcommand | Description |
|------------|-------------|
| `get` | Get org details |
| `list` | List organizations |

```bash
pup organizations get
```

### api-keys

API key management.

| Subcommand | Description |
|------------|-------------|
| `list` | List API keys |
| `get` | Get key details |
| `create` | Create API key |
| `delete` | Delete API key |

```bash
pup api-keys list
pup api-keys create --name="CI/CD Key"
```

### app-keys

Application key management.

| Subcommand | Description |
|------------|-------------|
| `list` | List app keys |
| `get` | Get key details |
| `create` | Create app key |
| `update` | Update app key |
| `delete` | Delete app key |

```bash
pup app-keys list
pup app-keys create --name="My App"
```

### authn-mappings

SAML/IdP attribute-to-role authentication mappings.

| Subcommand | Description |
|------------|-------------|
| `list` | List mappings |
| `get` | Get mapping details |
| `create` | Create mapping |
| `update` | Update mapping |
| `delete` | Delete mapping |

```bash
pup authn-mappings list
pup authn-mappings create --file mapping.json
```

---

## Platform & Configuration

### usage

Usage and billing metrics.

| Subcommand | Description |
|------------|-------------|
| `summary` | Usage summary |
| `hourly` | Hourly usage breakdown |

```bash
pup usage summary
pup usage hourly --from="24h"
```

### costs

Cost management — Datadog usage costs and Cloud Cost Management.

| Subcommand | Description |
|------------|-------------|
| `datadog projected` | Projected cost for current month |
| `datadog attribution` | Monthly cost attribution |
| `datadog by-org` | Cost breakdown by organization |
| `datadog aws-config` | AWS CUR config (list, get, create, delete) |
| `datadog azure-config` | Azure UC config |
| `datadog gcp-config` | GCP usage cost config |
| `ccm custom-costs` | Custom cost uploads (list, get, upload, delete) |
| `ccm tag-descriptions` | Tag descriptions (list, get, generate, upsert, delete) |
| `ccm tag-metadata` | Tag metadata (list, tag-sources, metrics, orchestrators, currency) |
| `ccm tags` | CCM tags (list) |
| `ccm tag-keys` | Tag keys (list, get) |
| `ccm budgets` | Budget management (list, get, upsert, delete, validate) |
| `ccm commitments` | RI/Savings Plans (utilization, coverage, savings, hotspots, list, time-series) |

```bash
pup costs datadog projected
pup costs datadog attribution --start="2024-01-01T00:00:00Z"
pup costs ccm budgets list
```

### product-analytics

Server-side product analytics.

| Subcommand | Description |
|------------|-------------|
| `events send` | Send analytics events |
| `query` | Query analytics (scalar/timeseries) |

```bash
pup product-analytics events send --file events.json
pup product-analytics query --file query.json
```

### integrations

Third-party integrations.

| Subcommand | Description |
|------------|-------------|
| `slack` | Slack integration management |
| `pagerduty` | PagerDuty integration |
| `webhooks` | Webhook management |
| `jira` | Jira integration (accounts, templates) |
| `servicenow` | ServiceNow integration (instances, templates, users) |
| `google-chat` | Google Chat integration |
| `ms-teams` | Microsoft Teams integration |

```bash
pup integrations slack list
pup integrations pagerduty list
```

### feature-flags

Feature flag management.

| Subcommand | Description |
|------------|-------------|
| `flags` | Flag management |
| `environments` | Environment configuration |
| `allocations` | Allocation management |
| `exposure` | Exposure tracking |
| `enable` | Enable a flag |
| `disable` | Disable a flag |

```bash
pup feature-flags flags list
pup feature-flags enable my-flag --env prod
```

### kafka

Kafka cluster inspection (experimental).

| Subcommand | Description |
|------------|-------------|
| `topic-configs` | Topic configuration |
| `broker-configs` | Broker configuration |
| `client-configs` | Client configuration |
| `read-messages` | Read Kafka messages |

```bash
pup kafka topic-configs list
pup kafka read-messages --topic my-topic
```

### datasets

Restricted dataset management for data access control.

| Subcommand | Description |
|------------|-------------|
| `list` | List datasets |
| `get` | Get dataset details |
| `create` | Create dataset |
| `update` | Update dataset |
| `delete` | Delete dataset |

```bash
pup datasets list
pup datasets create --file dataset.json
```

### obs-pipelines

Observability Pipelines — full CRUD and validation.

| Subcommand | Description |
|------------|-------------|
| `list` | List pipelines |
| `get` | Get pipeline details |
| `create` | Create pipeline |
| `update` | Update pipeline |
| `delete` | Delete pipeline |
| `validate` | Validate pipeline config |

```bash
pup obs-pipelines list
pup obs-pipelines validate --file pipeline.json
```

### llm-obs

LLM Observability — projects, experiments, datasets, spans.

| Subcommand | Description |
|------------|-------------|
| `projects create/list` | Project management |
| `experiments` | Experiment CRUD (create, list, update, delete, summary, events, metric-values, dimension-values) |
| `datasets create/list` | Dataset management |
| `spans search` | Span search |

```bash
pup llm-obs projects list
pup llm-obs experiments list --filter-project-id <project-id>
```

### reference-tables

Reference tables for log enrichment.

| Subcommand | Description |
|------------|-------------|
| `list` | List reference tables |
| `get` | Get table details |
| `create` | Create reference table |
| `batch-query` | Batch query against tables |

```bash
pup reference-tables list
pup reference-tables create --file table.json
```

### misc

Miscellaneous utilities.

| Subcommand | Description |
|------------|-------------|
| `ip-ranges` | Datadog IP ranges |
| `status` | Datadog service status |

```bash
pup misc ip-ranges
pup misc status
```

### app-builder

Low-code app management.

| Subcommand | Description |
|------------|-------------|
| `list` | List apps |
| `get` | Get app details |
| `create` | Create app |
| `update` | Update app |
| `delete` | Delete app |
| `delete-batch` | Batch delete apps |
| `publish` | Publish app |
| `unpublish` | Unpublish app |

```bash
pup app-builder list
pup app-builder publish <app-id>
```

### skills

Pup embedded skills and agents.

| Subcommand | Description |
|------------|-------------|
| `list` | List available skills/agents |
| `install` | Install skills for an AI assistant |
| `path` | Show skills directory path |

```bash
pup skills list
pup skills install --target-agent=claude-code
```

### auth

Authentication management.

| Subcommand | Description |
|------------|-------------|
| `login` | OAuth2 browser-based login |
| `logout` | Clear credentials |
| `status` | Check auth status |
| `refresh` | Refresh access token |

```bash
pup auth login
pup auth status
```

### acp

ACP server for AI agent integration.

| Subcommand | Description |
|------------|-------------|
| `serve` | Start local ACP + OpenAI-compatible server |

```bash
pup acp serve
pup acp serve --agent-id <uuid> --port 9099
```
