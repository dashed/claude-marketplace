# Query Syntax Reference

Complete query syntax for all Datadog domains accessible through Pup CLI.

## Table of Contents

- [Logs](#logs)
- [Log Aggregation](#log-aggregation)
- [Log Storage Tiers](#log-storage-tiers)
- [Metrics](#metrics)
- [APM / Traces](#apm--traces)
- [Monitors](#monitors)
- [RUM (Real User Monitoring)](#rum-real-user-monitoring)
- [Security](#security)
- [Events](#events)
- [DBM (Database Monitoring)](#dbm-database-monitoring)
- [DDSQL](#ddsql)
- [Time Range Formats](#time-range-formats)

---

## Logs

Pup uses Datadog's log search syntax. Queries go in `--query`.

### Basic Filters

```
status:error                        # Filter by log status
service:web-app                     # Filter by service name
host:i-0abc123                      # Filter by hostname
source:nginx                        # Filter by log source
```

### Custom Attributes

Prefix custom (non-reserved) attributes with `@`:

```
@user.id:12345                      # Custom attribute match
@http.status_code:500               # HTTP status code
@request.duration:>1000             # Numeric comparison
@environment:production             # Custom environment tag
```

### Wildcards and Exact Match

```
host:i-*                            # Wildcard matching
service:api-*                       # Service prefix wildcard
"exact error message"               # Exact phrase (quoted)
"connection timeout"                # Exact multi-word phrase
```

### Boolean Operators

```
status:error AND service:web        # Explicit AND
status:error service:web            # Implicit AND (space = AND)
status:error OR status:warn         # OR
-status:info                        # Negation (exclude)
NOT status:info                     # Negation (alternative)
```

### Numeric Ranges

```
@http.status_code:[400 TO 599]     # Inclusive range
@duration:>1000                     # Greater than
@duration:<500                      # Less than
@duration:[100 TO 500]             # Between 100 and 500
```

### Combining Filters

```
status:error AND service:api AND @http.status_code:[500 TO 599]
(status:error OR status:warn) AND service:payments
service:api AND -status:info AND @duration:>1000
```

### Search Commands

```bash
# Basic search
pup logs search --query="status:error" --from=1h

# Combined filters
pup logs search --query="status:error AND service:api" --from=1h --limit=100

# Custom attributes
pup logs search --query="@user.id:12345 status:error" --limit=100

# Absolute time range
pup logs search --query="service:api" --from="2024-02-04T10:00:00Z" --to="2024-02-04T11:00:00Z"
```

---

## Log Aggregation

Use `pup logs aggregate` for counting and statistics. Always prefer this over fetching all logs and counting locally.

### Compute Functions

| Function | Example | Description |
|----------|---------|-------------|
| `count` | `--compute="count"` | Count matching logs |
| `avg` | `--compute="avg(@duration)"` | Average of a numeric field |
| `sum` | `--compute="sum(@bytes_sent)"` | Sum of a numeric field |
| `min` | `--compute="min(@duration)"` | Minimum value |
| `max` | `--compute="max(@duration)"` | Maximum value |
| `percentile` | `--compute="percentile(@duration, 99)"` | Percentile (p50, p75, p90, p95, p99) |

### Group By

```bash
# Count errors by service
pup logs aggregate --query="status:error" --from=1h --compute="count" --group-by="service"

# Average duration by service
pup logs aggregate --query="service:web-app" --from=1h --compute="avg(@duration)" --group-by="service"

# P99 latency by service
pup logs aggregate --query="env:prod" --from=30m --compute="percentile(@duration, 99)" --group-by="service"

# Multiple computes and group-bys (comma-separated)
pup logs aggregate --query="service:web-app" --from=1h \
  --compute="count,avg(@duration),percentile(@duration, 95)" \
  --group-by="service,status"
```

---

## Log Storage Tiers

Datadog stores logs across different tiers. Use `--storage` to target a specific tier:

| Tier | Flag | Use Case | Typical Retention |
|------|------|----------|-------------------|
| Standard indexes | `--storage="indexes"` | Recent, fast queries (default) | Days to weeks |
| Flex | `--storage="flex"` | Cost-optimized storage | Weeks to months |
| Online Archives | `--storage="online-archives"` | Long-term storage | Months to years |

```bash
# Search Flex logs
pup logs search --query="service:api" --from=7d --storage="flex"

# Search online archives
pup logs search --query="status:error" --from=30d --storage="online-archives"

# Standard indexes (default behavior)
pup logs search --query="service:web-app" --from=1h --storage="indexes"
```

---

## Metrics

Metrics queries use the format: `<aggregation>:<metric_name>{<filter>} by {<group>}`

### Aggregations

| Aggregation | Description |
|-------------|-------------|
| `avg` | Average across sources |
| `sum` | Sum across sources |
| `min` | Minimum across sources |
| `max` | Maximum across sources |

### Query Format

```
avg:system.cpu.user{*}                          # All hosts
avg:system.cpu.user{env:prod}                   # Filter by tag
avg:system.cpu.user{env:prod} by {host}         # Group by host
sum:trace.servlet.request.hits{service:web}     # Request count
max:system.mem.used{*} by {host}                # Max memory per host
avg:system.cpu.user{env:prod,region:us-east}    # Multiple filters
```

### Filter Syntax

Inside `{...}`:

```
{*}                                 # All (no filter)
{env:prod}                          # Single tag filter
{env:prod,service:api}              # Multiple tags (AND)
{host:web-*}                        # Wildcard
{!env:staging}                      # Negation
```

### Commands

```bash
# V2 timeseries query (recommended)
pup metrics query --query="avg:system.cpu.user{*}" --from=1h

# V2 with grouping
pup metrics query --query="avg:system.cpu.user{env:prod} by {host}" --from=1h

# V1 classic search
pup metrics search --query="avg:system.cpu.user{*}" --from=1h

# List available metrics
pup metrics list --filter="system.*"

# Get metric metadata
pup metrics get <metric-name>
```

---

## APM / Traces

### CRITICAL: Durations Are in NANOSECONDS

This is the most common gotcha when working with APM data:

| Human Duration | Nanoseconds | Common Mistake |
|----------------|-------------|----------------|
| 1 ms | 1,000,000 | Using `1` (= 1 nanosecond) |
| 100 ms | 100,000,000 | Using `100` |
| 1 second | 1,000,000,000 | Using `1000` (= 1 microsecond) |
| 5 seconds | 5,000,000,000 | Using `5000` |
| 30 seconds | 30,000,000,000 | Using `30000` |

### Trace Query Syntax

```
service:api-gateway                            # Filter by service
resource_name:/api/v1/users                    # Filter by endpoint/resource
@duration:>1000000000                          # Duration > 1 second
@duration:>5000000000                          # Duration > 5 seconds
status:error                                   # Error spans only
env:production                                 # Filter by environment
operation_name:express.request                 # Filter by operation
@http.method:POST                              # Filter by HTTP method
@http.status_code:[500 TO 599]                # Server errors
```

### Combining Trace Filters

```
service:api AND @duration:>1000000000          # Slow API calls (>1s)
service:api AND status:error AND env:prod      # Production API errors
resource_name:/checkout AND @duration:>5000000000  # Slow checkout (>5s)
```

### Commands

```bash
# Search traces
pup traces search --query="service:api-gateway" --from=1h

# Find slow traces (>1 second)
pup traces search --query="service:api AND @duration:>1000000000" --from=1h

# Find error traces
pup traces search --query="service:api AND status:error" --from=1h

# Aggregate trace data
pup traces aggregate --query="service:api" --compute="avg(@duration)" --group-by="resource_name" --from=1h

# List APM services
pup apm services list --env=production

# Service operations and resources
pup apm services operations --env=production --service=my-service
pup apm services resources --env=production --service=my-service --name=http.request
```

---

## Monitors

Monitors use a different search syntax from logs.

### List Filters

```bash
# Filter by tags
pup monitors list --tags="env:production"
pup monitors list --tags="team:backend"
pup monitors list --tags="env:prod" --tags="service:api"  # Multiple tags

# Filter by name substring
pup monitors list --name="CPU"
```

### Full-Text Search

```bash
# Search by status
pup monitors search --query="status:Alert"
pup monitors search --query="status:Warn"
pup monitors search --query="status:OK"

# Search by type
pup monitors search --query="type:metric"
pup monitors search --query="type:log"
pup monitors search --query="type:apm"

# Search by name
pup monitors search --query="High CPU"

# Combined
pup monitors search --query="status:Alert type:metric"
```

---

## RUM (Real User Monitoring)

RUM queries use the same general syntax as logs, with RUM-specific attributes.

### Common Filters

```
@type:error                         # Error events
@type:view                          # Page views
@type:action                        # User actions
@type:resource                      # Resource loads
@type:long_task                     # Long tasks
@view.loading_time:>3000            # Slow pages (milliseconds)
@session.type:user                  # Real users (not synthetic)
@application.id:abc-123             # Specific application
@view.url_path:/checkout            # Specific page
@error.source:source                # Source errors
@action.type:click                  # Click actions
```

### Commands

```bash
# List RUM applications
pup rum apps list

# Get application details
pup rum apps get "abc-123"

# Search sessions
pup rum sessions search --query="@application.id:abc-123" --from=1h

# Search with RUM-specific filters
pup rum sessions search --query="@type:error AND @session.type:user" --from=1h
```

---

## Security

### Security Signals

```bash
# List recent signals
pup security signals list --from=24h

# Filter by severity
pup security signals list --query="severity:critical" --from=24h
pup security signals list --query="severity:high" --from=24h
```

### Security Findings

```bash
# Search by severity
pup security findings search --query="@severity:critical"
pup security findings search --query="@severity:high"

# DDSQL analytics for cloud security
pup security findings analyze --query="SELECT * FROM findings WHERE severity = 'critical' LIMIT 10"
```

### Security Rules

```bash
pup security rules list
pup security rules get "rule-id"
```

---

## Events

### Event Search

```bash
# List recent events
pup events list --from=24h

# Filter by tags
pup events list --tags="source:deploy" --from=24h

# Full-text search
pup events search --query="deploy" --from=24h
pup events search --query="@user.id:12345"

# Get specific event
pup events get <event-id>
```

---

## DBM (Database Monitoring)

### Query Sample Search

DBM queries use a combination of reserved and custom attributes:

```
dbm_type:activity                   # Activity samples
dbm_type:plan                       # Query plan samples
service:orders                      # Filter by service
env:prod                            # Filter by environment
db.hostname:primary-db              # Filter by database host
@db.statement_type:select           # Filter by SQL statement type
```

### Commands

```bash
# Search recent activity samples
pup dbm samples search --query="dbm_type:activity service:orders env:prod" --from=1h --limit=10

# Filter by database host
pup dbm samples search --query="db.hostname:primary-db service:checkout" --from=30m --sort=asc

# Filter by statement type with time window
pup dbm samples search \
  --query="service:payments @db.statement_type:select" \
  --from="2024-02-04T10:00:00Z" \
  --to="2024-02-04T11:00:00Z" \
  --limit=25
```

---

## DDSQL

DDSQL uses SQL-like syntax for querying Datadog data:

```bash
# Table query
pup ddsql table --query="SELECT host, avg(cpu) FROM metrics WHERE env = 'prod' GROUP BY host"

# Time-series query
pup ddsql time-series --query="SELECT avg(cpu) FROM metrics WHERE env = 'prod'"

# Schema discovery
pup ddsql schema tables
pup ddsql schema columns --table=<table-name>
```

---

## Time Range Formats

All `--from` and `--to` flags across every domain accept these formats:

### Relative (Short)

| Format | Meaning |
|--------|---------|
| `5s` | 5 seconds ago |
| `30m` | 30 minutes ago |
| `1h` | 1 hour ago |
| `4h` | 4 hours ago |
| `7d` | 7 days ago |
| `1w` | 1 week ago |

### Relative (Long)

| Format | Meaning |
|--------|---------|
| `5min` | 5 minutes ago |
| `2hours` | 2 hours ago |
| `3days` | 3 days ago |
| `"5 minutes"` | 5 minutes ago (quoted with space) |
| `"2 hours"` | 2 hours ago (quoted with space) |

### Absolute

| Format | Example |
|--------|---------|
| RFC3339 | `2024-01-01T00:00:00Z` |
| RFC3339 with offset | `2024-01-01T00:00:00-05:00` |
| Unix milliseconds | `1704067200000` |

### Special

| Format | Meaning |
|--------|---------|
| `now` | Current time |

### Usage Examples

```bash
# Relative short
pup logs search --query="status:error" --from=1h

# Relative long
pup logs search --query="status:error" --from=2hours

# Absolute window
pup logs search --query="status:error" --from="2024-02-04T10:00:00Z" --to="2024-02-04T11:00:00Z"

# From a point to now
pup metrics query --query="avg:system.cpu.user{*}" --from=1h --to=now
```

### Best Practices for Time Ranges

1. **Always specify `--from`** — omitting it may produce unexpected results or errors
2. **Start with `1h`** — widen to `24h` or `7d` only if you need more data
3. **Don't default to `30d`** — large time ranges are slow and may hit API limits
4. **Use `--to=now` explicitly** when you want current data (though it's usually the default)
