#!/usr/bin/env bash
#
# list-sessions.sh - List all registered tmux sessions
#
# Lists all sessions in the registry with health status information.
# Supports both human-readable table format and JSON output.
#
# Usage:
#   ./list-sessions.sh [--json]
#
# Options:
#   --json            Output as JSON instead of table
#   -h, --help        Show this help message
#
# Exit codes:
#   0  - Success
#   1  - Error

set -euo pipefail

# Get script directory to source libraries
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/registry.sh
source "$SCRIPT_DIR/lib/registry.sh"
# shellcheck source=lib/time_utils.sh
source "$SCRIPT_DIR/lib/time_utils.sh"

# Path to pane-health tool
PANE_HEALTH="$SCRIPT_DIR/pane-health.sh"

#------------------------------------------------------------------------------
# Configuration
#------------------------------------------------------------------------------

output_format="table"

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------

usage() {
  cat << EOF
Usage: $(basename "$0") [--json]

List all registered tmux sessions with health status.

Options:
  --json            Output as JSON instead of table format
  -h, --help        Show this help message

Output Formats:
  Table (default):
    NAME            SOCKET          TARGET          STATUS    PID    CREATED
    my-python       claude.sock     my-python:0.0   alive     1234   2h ago
    my-gdb          claude.sock     my-gdb:0.0      dead      -      1h ago

  JSON (--json):
    {
      "sessions": [
        {"name": "my-python", "socket": "...", "status": "alive", ...}
      ],
      "total": 2,
      "alive": 1,
      "dead": 1
    }

Health Status:
  alive    - Session is running and healthy
  dead     - Pane is marked as dead
  missing  - Session/pane not found
  zombie   - Process not running
  server   - Tmux server not running

Examples:
  # List sessions in table format
  $(basename "$0")

  # List sessions as JSON
  $(basename "$0") --json

Exit codes:
  0  - Success
  1  - Error
EOF
}

# Get health status for a session
# Returns: status string (alive, dead, missing, zombie, server)
get_health_status() {
  local socket="$1"
  local target="$2"

  if [[ ! -x "$PANE_HEALTH" ]]; then
    echo "unknown"
    return
  fi

  # Call pane-health.sh and interpret exit code
  if "$PANE_HEALTH" -S "$socket" -t "$target" --format text >/dev/null 2>&1; then
    echo "alive"
  else
    local exit_code=$?
    case $exit_code in
      1) echo "dead" ;;
      2) echo "missing" ;;
      3) echo "zombie" ;;
      4) echo "server" ;;
      *) echo "unknown" ;;
    esac
  fi
}

#------------------------------------------------------------------------------
# Argument parsing
#------------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json)
      output_format="json"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

#------------------------------------------------------------------------------
# Get sessions from registry
#------------------------------------------------------------------------------

registry_data=$(registry_list_sessions)
session_names=$(echo "$registry_data" | jq -r '.sessions | keys[]' 2>/dev/null || echo "")

# Count sessions
total_count=0
alive_count=0
dead_count=0

# Build session list with health info
sessions_with_health=()

if [[ -n "$session_names" ]]; then
  while IFS= read -r name; do
    [[ -z "$name" ]] && continue

    # Get session data
    socket=$(echo "$registry_data" | jq -r ".sessions[\"$name\"].socket")
    target=$(echo "$registry_data" | jq -r ".sessions[\"$name\"].target")
    type=$(echo "$registry_data" | jq -r ".sessions[\"$name\"].type")
    pid=$(echo "$registry_data" | jq -r ".sessions[\"$name\"].pid // \"\"")
    created=$(echo "$registry_data" | jq -r ".sessions[\"$name\"].created_at")

    # Get health status
    status=$(get_health_status "$socket" "$target")

    # Update counters
    total_count=$((total_count + 1))
    if [[ "$status" == "alive" ]]; then
      alive_count=$((alive_count + 1))
    else
      dead_count=$((dead_count + 1))
    fi

    # Store session info
    sessions_with_health+=("$name|$socket|$target|$status|$pid|$created|$type")
  done <<< "$session_names"
fi

#------------------------------------------------------------------------------
# Output results
#------------------------------------------------------------------------------

if [[ "$output_format" == "json" ]]; then
  # JSON output
  echo "{"
  echo "  \"sessions\": ["

  first=true
  for session_info in "${sessions_with_health[@]+"${sessions_with_health[@]}"}"; do
    IFS='|' read -r name socket target status pid created type <<< "$session_info"

    if [[ "$first" == false ]]; then
      echo ","
    fi
    first=false

    # Get basename of socket for cleaner output
    socket_basename=$(basename "$socket")

    cat << EOF
    {
      "name": "$name",
      "socket": "$socket",
      "socket_basename": "$socket_basename",
      "target": "$target",
      "type": "$type",
      "status": "$status",
      "pid": ${pid:-null},
      "created_at": "$created"
    }
EOF
  done

  echo ""
  echo "  ],"
  echo "  \"total\": $total_count,"
  echo "  \"alive\": $alive_count,"
  echo "  \"dead\": $dead_count"
  echo "}"
else
  # Table output
  if [[ $total_count -eq 0 ]]; then
    echo "No sessions registered."
    exit 0
  fi

  # Print header
  printf "%-20s %-20s %-20s %-10s %-8s %-15s\n" \
    "NAME" "SOCKET" "TARGET" "STATUS" "PID" "CREATED"
  printf "%-20s %-20s %-20s %-10s %-8s %-15s\n" \
    "----" "------" "------" "------" "---" "-------"

  # Print sessions
  for session_info in "${sessions_with_health[@]+"${sessions_with_health[@]}"}"; do
    IFS='|' read -r name socket target status pid created type <<< "$session_info"

    # Get basename of socket for cleaner output
    socket_basename=$(basename "$socket")

    # Format time ago
    time_str=$(time_ago "$created")

    # Truncate long values
    name_trunc="${name:0:20}"
    socket_trunc="${socket_basename:0:20}"
    target_trunc="${target:0:20}"

    printf "%-20s %-20s %-20s %-10s %-8s %-15s\n" \
      "$name_trunc" "$socket_trunc" "$target_trunc" "$status" "${pid:--}" "$time_str"
  done

  # Print summary
  echo ""
  echo "Total: $total_count | Alive: $alive_count | Dead: $dead_count"
fi

exit 0
