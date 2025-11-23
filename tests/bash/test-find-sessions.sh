#!/usr/bin/env bash
set -euo pipefail

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TOOL_PATH="$REPO_ROOT/plugins/tmux/tools/find-sessions.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
SOCKET_DIR="${TMPDIR:-/tmp}/tmux-test-$$"
SOCKET1="$SOCKET_DIR/test1.sock"
SOCKET2="$SOCKET_DIR/test2.sock"
SOCKET_NAME="test-find-sessions-$$"  # Named socket for -L testing

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Helper function to run test that checks exit code
run_test() {
    local test_name="$1"
    local expected_exit="$2"
    shift 2
    local cmd=("$@")

    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Test $TESTS_TOTAL: $test_name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "Command: ${cmd[*]}"
    echo ""

    # Run command and capture output and exit code
    set +e
    output=$("${cmd[@]}" 2>&1)
    actual_exit=$?
    set -e

    echo "Output:"
    echo "$output"
    echo ""
    echo "Expected exit code: $expected_exit"
    echo "Actual exit code: $actual_exit"

    if [[ "$actual_exit" == "$expected_exit" ]]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Helper function to run test that checks output contains expected text
run_test_contains() {
    local test_name="$1"
    local expected_text="$2"
    shift 2
    local cmd=("$@")

    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Test $TESTS_TOTAL: $test_name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "Command: ${cmd[*]}"
    echo "Expected to contain: '$expected_text'"
    echo ""

    # Run command and capture output
    set +e
    output=$("${cmd[@]}" 2>&1)
    exit_code=$?
    set -e

    echo "Output:"
    echo "$output"
    echo ""

    if echo "$output" | grep -q "$expected_text"; then
        echo -e "${GREEN}✓ PASSED (found expected text)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAILED (expected text not found)${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Cleanup function
cleanup() {
    echo -e "\n${BLUE}Cleaning up test resources...${NC}"
    tmux -S "$SOCKET1" kill-server 2>/dev/null || true
    tmux -S "$SOCKET2" kill-server 2>/dev/null || true
    tmux -L "$SOCKET_NAME" kill-server 2>/dev/null || true
    rm -rf "$SOCKET_DIR"
}

# Ensure cleanup on exit
trap cleanup EXIT

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Comprehensive find-sessions.sh Test Suite         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Tool path: $TOOL_PATH"
echo "Socket dir: $SOCKET_DIR"
echo ""

mkdir -p "$SOCKET_DIR"

# ============================================================================
# TEST 1: No server running on socket
# ============================================================================

run_test "No server on non-existent socket" 1 \
    "$TOOL_PATH" -S "$SOCKET1"

# ============================================================================
# TEST 1.5: Named socket with -L option (SUCCESS CASES)
# ============================================================================

# Create sessions on named socket using -L
tmux -L "$SOCKET_NAME" new-session -d -s named-session-1 "sleep 60"
tmux -L "$SOCKET_NAME" new-session -d -s named-session-2 "sleep 60"
tmux -L "$SOCKET_NAME" new-session -d -s other-session "sleep 60"

run_test_contains "Find sessions on named socket (-L)" "named-session-1" \
    "$TOOL_PATH" -L "$SOCKET_NAME"

run_test_contains "Verify multiple sessions found (-L)" "named-session-2" \
    "$TOOL_PATH" -L "$SOCKET_NAME"

run_test "Verify exit code 0 when sessions found (-L)" 0 \
    "$TOOL_PATH" -L "$SOCKET_NAME"

# Test query filtering with -L
run_test_contains "Query filter with -L option" "named-session" \
    "$TOOL_PATH" -L "$SOCKET_NAME" -q named

# Verify query excludes non-matching sessions with -L
output=$("$TOOL_PATH" -L "$SOCKET_NAME" -q named 2>&1 || true)
if echo "$output" | grep -q "other-session"; then
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗ FAILED: -L query filter should exclude non-matching sessions${NC}"
else
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓ PASSED: -L query filter correctly excludes non-matching sessions${NC}"
fi

# ============================================================================
# TEST 2: Single session on specific socket
# ============================================================================

# Create session on socket 1
tmux -S "$SOCKET1" new-session -d -s test-session "sleep 60"

run_test_contains "Find session on specific socket (-S)" "test-session" \
    "$TOOL_PATH" -S "$SOCKET1"

run_test "Verify exit code 0 when sessions found" 0 \
    "$TOOL_PATH" -S "$SOCKET1"

# ============================================================================
# TEST 3: Multiple sessions on same socket
# ============================================================================

# Create more sessions on socket 1
tmux -S "$SOCKET1" new-session -d -s python-repl "sleep 60"
tmux -S "$SOCKET1" new-session -d -s debug-session "sleep 60"

run_test_contains "Find multiple sessions" "test-session" \
    "$TOOL_PATH" -S "$SOCKET1"

run_test_contains "Find python session" "python-repl" \
    "$TOOL_PATH" -S "$SOCKET1"

run_test_contains "Find debug session" "debug-session" \
    "$TOOL_PATH" -S "$SOCKET1"

# ============================================================================
# TEST 4: Query filtering
# ============================================================================

run_test_contains "Filter sessions with query 'python'" "python-repl" \
    "$TOOL_PATH" -S "$SOCKET1" -q python

run_test_contains "Filter sessions with query 'debug'" "debug-session" \
    "$TOOL_PATH" -S "$SOCKET1" -q debug

# Verify query excludes non-matching sessions
output=$("$TOOL_PATH" -S "$SOCKET1" -q python 2>&1 || true)
if echo "$output" | grep -q "test-session"; then
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗ FAILED: Query filter should exclude non-matching sessions${NC}"
else
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓ PASSED: Query filter correctly excludes non-matching sessions${NC}"
fi

# ============================================================================
# TEST 5: Scan all sockets mode (--all)
# ============================================================================

# Create sessions on second socket
tmux -S "$SOCKET2" new-session -d -s socket2-session1 "sleep 60"
tmux -S "$SOCKET2" new-session -d -s socket2-session2 "sleep 60"

# Set environment variable to point to our test socket directory
export CLAUDE_TMUX_SOCKET_DIR="$SOCKET_DIR"

run_test_contains "Scan all sockets - find socket1 sessions" "test-session" \
    "$TOOL_PATH" --all

run_test_contains "Scan all sockets - find socket2 sessions" "socket2-session1" \
    "$TOOL_PATH" --all

# ============================================================================
# TEST 6: Scan all with query filter
# ============================================================================

run_test_contains "Scan all with query 'python'" "python-repl" \
    "$TOOL_PATH" --all -q python

run_test_contains "Scan all with query 'socket2'" "socket2-session" \
    "$TOOL_PATH" --all -q socket2

# ============================================================================
# TEST 7: Invalid option combinations
# ============================================================================

run_test "Reject --all with -S" 1 \
    "$TOOL_PATH" --all -S "$SOCKET1"

run_test "Reject --all with -L" 1 \
    "$TOOL_PATH" --all -L test

run_test "Reject both -L and -S" 1 \
    "$TOOL_PATH" -L test -S "$SOCKET1"

# ============================================================================
# TEST 8: Session state detection (attached/detached)
# ============================================================================

# All sessions should be detached
run_test_contains "Sessions show detached state" "detached" \
    "$TOOL_PATH" -S "$SOCKET1"

# ============================================================================
# Final Summary
# ============================================================================

echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                      Test Summary                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Total tests run: ${BLUE}$TESTS_TOTAL${NC}"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              ALL TESTS PASSED! 🎉                          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║              SOME TESTS FAILED ❌                          ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
