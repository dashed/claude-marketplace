#!/usr/bin/env bash
#
# Test suite for tools/list-sessions.sh
#

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$SCRIPT_DIR/../../plugins/tmux/tools"
LIST_SESSIONS="$TOOLS_DIR/list-sessions.sh"
CREATE_SESSION="$TOOLS_DIR/create-session.sh"
REGISTRY_LIB="$TOOLS_DIR/lib/registry.sh"

# Test-specific socket directory (isolated from system)
export CLAUDE_TMUX_SOCKET_DIR="${TMPDIR:-/tmp}/tmux-test-list-$$"
# shellcheck disable=SC2034  # Used by sourced registry.sh library
REGISTRY_FILE="$CLAUDE_TMUX_SOCKET_DIR/.sessions.json"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Cleanup function
# shellcheck disable=SC2329  # Function is invoked via trap below
cleanup() {
    # Kill any tmux sessions we created
    shopt -s nullglob
    for socket in "$CLAUDE_TMUX_SOCKET_DIR"/*.sock; do
        tmux -S "$socket" kill-server 2>/dev/null || true
    done
    shopt -u nullglob
    # Remove test directory
    rm -rf "$CLAUDE_TMUX_SOCKET_DIR"
}
trap cleanup EXIT

# Source the registry library
# shellcheck source=../../plugins/tmux/tools/lib/registry.sh
source "$REGISTRY_LIB"

#------------------------------------------------------------------------------
# Test utilities
#------------------------------------------------------------------------------

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    TESTS_RUN=$((TESTS_RUN + 1))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    if [[ -n "${2:-}" ]]; then
        echo "  Expected: $2"
    fi
    if [[ -n "${3:-}" ]]; then
        echo "  Got: $3"
    fi
    TESTS_FAILED=$((TESTS_FAILED + 1))
    TESTS_RUN=$((TESTS_RUN + 1))
}

# Reset test environment
reset_test_env() {
    # Clean up any existing sessions
    shopt -s nullglob
    for socket in "$CLAUDE_TMUX_SOCKET_DIR"/*.sock; do
        tmux -S "$socket" kill-server 2>/dev/null || true
    done
    shopt -u nullglob
    # Reset registry
    rm -rf "$CLAUDE_TMUX_SOCKET_DIR"
    mkdir -p "$CLAUDE_TMUX_SOCKET_DIR"
}

#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

test_empty_registry() {
    echo -e "\n${YELLOW}Testing empty registry${NC}"

    # Test 1: Empty registry shows appropriate message (table format)
    reset_test_env
    local result
    result=$("$LIST_SESSIONS" 2>&1)
    if echo "$result" | grep -q "No sessions registered"; then
        pass "Empty registry shows 'No sessions registered' message"
    else
        fail "Empty registry message incorrect" "No sessions registered" "$result"
    fi

    # Test 2: Empty registry JSON output
    reset_test_env
    result=$("$LIST_SESSIONS" --json 2>&1)
    local total
    total=$(echo "$result" | jq -r '.total' 2>/dev/null || echo "error")
    if [[ "$total" == "0" ]]; then
        pass "Empty registry JSON shows total=0"
    else
        fail "Empty registry JSON total incorrect" "0" "$total"
    fi

    # Test 3: Empty registry JSON has empty sessions array
    local sessions_length
    sessions_length=$(echo "$result" | jq '.sessions | length' 2>/dev/null || echo "error")
    if [[ "$sessions_length" == "0" ]]; then
        pass "Empty registry JSON has empty sessions array"
    else
        fail "Empty registry sessions array incorrect" "0" "$sessions_length"
    fi
}

test_single_session() {
    echo -e "\n${YELLOW}Testing single session listing${NC}"

    # Test 4: Single session appears in table output
    reset_test_env
    "$CREATE_SESSION" -n "test-single" --shell >/dev/null 2>&1
    local result
    result=$("$LIST_SESSIONS" 2>&1)
    if echo "$result" | grep -q "test-single"; then
        pass "Single session appears in table output"
    else
        fail "Single session not found in table" "test-single in output" "$result"
    fi

    # Test 5: Single session JSON output
    result=$("$LIST_SESSIONS" --json 2>&1)
    local total
    total=$(echo "$result" | jq -r '.total' 2>/dev/null || echo "error")
    if [[ "$total" == "1" ]]; then
        pass "Single session JSON shows total=1"
    else
        fail "Single session JSON total incorrect" "1" "$total"
    fi

    # Test 6: Single session JSON has correct name
    local session_name
    session_name=$(echo "$result" | jq -r '.sessions[0].name' 2>/dev/null || echo "error")
    if [[ "$session_name" == "test-single" ]]; then
        pass "Single session JSON has correct name"
    else
        fail "Single session name incorrect" "test-single" "$session_name"
    fi
}

test_multiple_sessions() {
    echo -e "\n${YELLOW}Testing multiple sessions listing${NC}"

    # Test 7: Multiple sessions appear in output
    reset_test_env
    "$CREATE_SESSION" -n "test-multi-1" --shell >/dev/null 2>&1
    "$CREATE_SESSION" -n "test-multi-2" --python >/dev/null 2>&1
    "$CREATE_SESSION" -n "test-multi-3" --shell >/dev/null 2>&1
    local result
    result=$("$LIST_SESSIONS" 2>&1)
    if echo "$result" | grep -q "test-multi-1" && \
       echo "$result" | grep -q "test-multi-2" && \
       echo "$result" | grep -q "test-multi-3"; then
        pass "All multiple sessions appear in table output"
    else
        fail "Not all sessions found in table" "All 3 sessions" "$result"
    fi

    # Test 8: Multiple sessions JSON count
    result=$("$LIST_SESSIONS" --json 2>&1)
    local total
    total=$(echo "$result" | jq -r '.total' 2>/dev/null || echo "error")
    if [[ "$total" == "3" ]]; then
        pass "Multiple sessions JSON shows total=3"
    else
        fail "Multiple sessions JSON total incorrect" "3" "$total"
    fi

    # Test 9: Multiple sessions JSON array length
    local sessions_length
    sessions_length=$(echo "$result" | jq '.sessions | length' 2>/dev/null || echo "error")
    if [[ "$sessions_length" == "3" ]]; then
        pass "Multiple sessions JSON array has 3 elements"
    else
        fail "Multiple sessions array length incorrect" "3" "$sessions_length"
    fi
}

test_health_status() {
    echo -e "\n${YELLOW}Testing health status detection${NC}"

    # Test 10: Alive session shows correct status
    reset_test_env
    "$CREATE_SESSION" -n "test-health" --shell >/dev/null 2>&1
    local result
    result=$("$LIST_SESSIONS" --json 2>&1)
    local status
    status=$(echo "$result" | jq -r '.sessions[0].status' 2>/dev/null || echo "error")
    if [[ "$status" == "alive" ]]; then
        pass "Alive session shows status=alive"
    else
        fail "Alive session status incorrect" "alive" "$status"
    fi

    # Test 11: Alive count is correct
    local alive_count
    alive_count=$(echo "$result" | jq -r '.alive' 2>/dev/null || echo "error")
    if [[ "$alive_count" == "1" ]]; then
        pass "Alive count is correct"
    else
        fail "Alive count incorrect" "1" "$alive_count"
    fi

    # Test 12: Dead count is zero for alive session
    local dead_count
    dead_count=$(echo "$result" | jq -r '.dead' 2>/dev/null || echo "error")
    if [[ "$dead_count" == "0" ]]; then
        pass "Dead count is zero for alive sessions"
    else
        fail "Dead count incorrect" "0" "$dead_count"
    fi
}

test_json_fields() {
    echo -e "\n${YELLOW}Testing JSON output fields${NC}"

    # Test 13: JSON output includes all required fields
    reset_test_env
    "$CREATE_SESSION" -n "test-json-fields" --shell >/dev/null 2>&1
    local result
    result=$("$LIST_SESSIONS" --json 2>&1)
    local session
    session=$(echo "$result" | jq '.sessions[0]' 2>/dev/null)

    local has_all_fields=true
    for field in name socket socket_basename target type status created_at; do
        if ! echo "$session" | jq -e ".$field" >/dev/null 2>&1; then
            has_all_fields=false
            break
        fi
    done

    if [[ "$has_all_fields" == true ]]; then
        pass "JSON output includes all required fields"
    else
        fail "JSON output missing fields" "All fields present" "$session"
    fi

    # Test 14: Socket basename is extracted correctly
    local socket_path
    socket_path=$(echo "$session" | jq -r '.socket')
    local socket_basename
    socket_basename=$(echo "$session" | jq -r '.socket_basename')
    local expected_basename
    expected_basename=$(basename "$socket_path")
    if [[ "$socket_basename" == "$expected_basename" ]]; then
        pass "Socket basename is extracted correctly"
    else
        fail "Socket basename incorrect" "$expected_basename" "$socket_basename"
    fi

    # Test 15: Session type is included
    local session_type
    session_type=$(echo "$session" | jq -r '.type')
    if [[ "$session_type" == "shell" ]]; then
        pass "Session type is included in JSON output"
    else
        fail "Session type incorrect" "shell" "$session_type"
    fi
}

test_table_output_format() {
    echo -e "\n${YELLOW}Testing table output format${NC}"

    # Test 16: Table has correct headers
    reset_test_env
    "$CREATE_SESSION" -n "test-table" --shell >/dev/null 2>&1
    local result
    result=$("$LIST_SESSIONS" 2>&1)
    if echo "$result" | grep -q "NAME" && \
       echo "$result" | grep -q "SOCKET" && \
       echo "$result" | grep -q "TARGET" && \
       echo "$result" | grep -q "STATUS" && \
       echo "$result" | grep -q "PID" && \
       echo "$result" | grep -q "CREATED"; then
        pass "Table output has all required headers"
    else
        fail "Table headers incomplete" "All headers present" "$result"
    fi

    # Test 17: Table includes summary line
    if echo "$result" | grep -q "Total:.*Alive:.*Dead:"; then
        pass "Table output includes summary line"
    else
        fail "Table summary line missing" "Total: X | Alive: Y | Dead: Z" "$result"
    fi
}

test_pid_handling() {
    echo -e "\n${YELLOW}Testing PID handling${NC}"

    # Test 18: PID is numeric for alive sessions
    reset_test_env
    "$CREATE_SESSION" -n "test-pid" --python >/dev/null 2>&1
    local result
    result=$("$LIST_SESSIONS" --json 2>&1)
    local pid
    pid=$(echo "$result" | jq -r '.sessions[0].pid' 2>/dev/null || echo "error")
    if [[ "$pid" =~ ^[0-9]+$ ]]; then
        pass "PID is numeric for alive sessions"
    else
        fail "PID format incorrect" "numeric PID" "$pid"
    fi
}

test_statistics() {
    echo -e "\n${YELLOW}Testing session statistics${NC}"

    # Test 19: Statistics are accurate with multiple sessions
    reset_test_env
    "$CREATE_SESSION" -n "test-stats-1" --shell >/dev/null 2>&1
    "$CREATE_SESSION" -n "test-stats-2" --shell >/dev/null 2>&1
    "$CREATE_SESSION" -n "test-stats-3" --shell >/dev/null 2>&1
    local result
    result=$("$LIST_SESSIONS" --json 2>&1)

    local total
    total=$(echo "$result" | jq -r '.total')
    local alive
    alive=$(echo "$result" | jq -r '.alive')
    local dead
    dead=$(echo "$result" | jq -r '.dead')

    if [[ "$total" == "3" ]] && [[ "$alive" == "3" ]] && [[ "$dead" == "0" ]]; then
        pass "Session statistics are accurate"
    else
        fail "Session statistics incorrect" "total=3, alive=3, dead=0" "total=$total, alive=$alive, dead=$dead"
    fi

    # Test 20: Total equals alive + dead
    if [[ $((alive + dead)) == "$total" ]]; then
        pass "Total equals alive + dead"
    else
        fail "Statistics don't add up" "alive + dead = total" "alive=$alive, dead=$dead, total=$total"
    fi
}

test_time_ago() {
    echo -e "\n${YELLOW}Testing time_ago() UTC timestamp parsing${NC}"

    # Source time_utils library to get time_ago function
    TIME_UTILS="$TOOLS_DIR/lib/time_utils.sh"
    # shellcheck source=../../plugins/tmux/tools/lib/time_utils.sh
    source "$TIME_UTILS"

    # Fixed NOW for deterministic testing
    # 2024-11-23T21:00:00Z = 1732395600 epoch
    export NOW_EPOCH=1732395600

    # Test 21: Parse UTC timestamp with 'Z' suffix (seconds ago)
    local result
    result=$(time_ago "2024-11-23T20:59:30Z")  # 30 seconds ago
    if [[ "$result" == "30s ago" ]]; then
        pass "time_ago() parses Z timestamp for seconds"
    else
        fail "time_ago() seconds parsing" "30s ago" "$result"
    fi

    # Test 22: Parse UTC timestamp with 'Z' suffix (minutes ago)
    result=$(time_ago "2024-11-23T20:34:00Z")  # 26 minutes ago
    if [[ "$result" == "26m ago" ]]; then
        pass "time_ago() parses Z timestamp for minutes"
    else
        fail "time_ago() minutes parsing" "26m ago" "$result"
    fi

    # Test 23: Parse UTC timestamp with 'Z' suffix (hours ago)
    result=$(time_ago "2024-11-23T16:00:00Z")  # 5 hours ago
    if [[ "$result" == "5h ago" ]]; then
        pass "time_ago() parses Z timestamp for hours"
    else
        fail "time_ago() hours parsing" "5h ago" "$result"
    fi

    # Test 24: Parse UTC timestamp with 'Z' suffix (days ago)
    result=$(time_ago "2024-11-16T21:00:00Z")  # 7 days ago
    if [[ "$result" == "7d ago" ]]; then
        pass "time_ago() parses Z timestamp for days"
    else
        fail "time_ago() days parsing" "7d ago" "$result"
    fi

    # Test 25: Parse UTC timestamp with '+0000' suffix
    result=$(time_ago "2024-11-23T20:34:00+0000")  # 26 minutes ago
    if [[ "$result" == "26m ago" ]]; then
        pass "time_ago() parses +0000 timestamp format"
    else
        fail "time_ago() +0000 parsing" "26m ago" "$result"
    fi

    # Test 26: UTC midnight boundary (ensures no local TZ shift)
    # 2024-11-23T00:05:00Z is 20h 55m before our NOW (21:00:00Z)
    result=$(time_ago "2024-11-23T00:05:00Z")  # 20h 55m = 20 hours ago
    if [[ "$result" == "20h ago" ]]; then
        pass "time_ago() handles UTC midnight boundary correctly"
    else
        fail "time_ago() midnight boundary" "20h ago" "$result"
    fi

    # Test 27: Invalid timestamp returns "unknown"
    result=$(time_ago "invalid-timestamp")
    if [[ "$result" == "unknown" ]]; then
        pass "time_ago() returns 'unknown' for invalid timestamp"
    else
        fail "time_ago() invalid handling" "unknown" "$result"
    fi

    # Test 28: Empty timestamp returns "unknown"
    result=$(time_ago "")
    if [[ "$result" == "unknown" ]]; then
        pass "time_ago() returns 'unknown' for empty timestamp"
    else
        fail "time_ago() empty handling" "unknown" "$result"
    fi

    # Test 29: Timestamp exactly at NOW
    result=$(time_ago "2024-11-23T21:00:00Z")  # 0 seconds ago
    if [[ "$result" == "0s ago" ]]; then
        pass "time_ago() handles timestamp exactly at NOW"
    else
        fail "time_ago() NOW handling" "0s ago" "$result"
    fi

    # Test 30: Very recent timestamp (less than 60s)
    result=$(time_ago "2024-11-23T20:59:45Z")  # 15 seconds ago
    if [[ "$result" == "15s ago" ]]; then
        pass "time_ago() handles very recent timestamps"
    else
        fail "time_ago() recent handling" "15s ago" "$result"
    fi

    unset NOW_EPOCH
}

#------------------------------------------------------------------------------
# Run all tests
#------------------------------------------------------------------------------

echo -e "${YELLOW}===========================================${NC}"
echo -e "${YELLOW}Running list-sessions.sh Test Suite${NC}"
echo -e "${YELLOW}===========================================${NC}"

test_empty_registry
test_single_session
test_multiple_sessions
test_health_status
test_json_fields
test_table_output_format
test_pid_handling
test_statistics
test_time_ago

#------------------------------------------------------------------------------
# Summary
#------------------------------------------------------------------------------

echo -e "\n${YELLOW}===========================================${NC}"
echo -e "${YELLOW}Test Summary${NC}"
echo -e "${YELLOW}===========================================${NC}"
echo -e "Tests run:    $TESTS_RUN"
echo -e "${GREEN}Tests passed: $TESTS_PASSED${NC}"
if [[ $TESTS_FAILED -gt 0 ]]; then
    echo -e "${RED}Tests failed: $TESTS_FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
