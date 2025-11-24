#!/usr/bin/env bash
#
# time_utils.sh - Time utility functions
#
# Provides functions for time-related operations, such as converting
# ISO 8601 timestamps to human-readable "time ago" strings.

# Get human-readable time ago from ISO8601 timestamp
# Args:
#   $1 - ISO 8601 timestamp (e.g., "2025-11-23T21:16:42Z" or "2025-11-23T21:16:42+0000")
# Returns:
#   Human-readable string like "30s ago", "5m ago", "2h ago", "7d ago", or "unknown"
# Environment:
#   NOW_EPOCH - Optional: Override current time for deterministic testing
time_ago() {
  local timestamp="$1"

  # Normalize 'Z' to explicit UTC offset for cross-platform compatibility
  local ts_normalized="${timestamp/Z/+0000}"

  # Convert ISO8601 to epoch (cross-platform)
  # macOS: TZ=UTC ensures proper UTC interpretation with %z format
  # Linux: date -d handles both 'Z' and '+0000' correctly
  local ts_epoch
  ts_epoch=$(TZ=UTC date -j -f "%Y-%m-%dT%H:%M:%S%z" "$ts_normalized" "+%s" 2>/dev/null || \
             date -d "$timestamp" "+%s" 2>/dev/null || \
             date -d "$ts_normalized" "+%s" 2>/dev/null || echo "0")

  if [[ "$ts_epoch" == "0" ]]; then
    echo "unknown"
    return
  fi

  local now_epoch
  # Support NOW_EPOCH env var for deterministic testing
  now_epoch=${NOW_EPOCH:-$(date "+%s")}
  local diff=$((now_epoch - ts_epoch))

  if [[ $diff -lt 60 ]]; then
    echo "${diff}s ago"
  elif [[ $diff -lt 3600 ]]; then
    echo "$((diff / 60))m ago"
  elif [[ $diff -lt 86400 ]]; then
    echo "$((diff / 3600))h ago"
  else
    echo "$((diff / 86400))d ago"
  fi
}
