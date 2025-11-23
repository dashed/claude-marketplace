#!/usr/bin/env bash
set -euo pipefail

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TOOL_PATH="$REPO_ROOT/plugins/tmux/tools/wait-for-text.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
SOCKET_DIR="${TMPDIR:-/tmp}/tmux-test-$$"
SOCKET="$SOCKET_DIR/test-wait-for-text.sock"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Helper function to run test
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

# Cleanup function
cleanup() {
    echo -e "\n${BLUE}Cleaning up test resources...${NC}"
    tmux -S "$SOCKET" kill-server 2>/dev/null || true
    rm -rf "$SOCKET_DIR"
}

# Ensure cleanup on exit
trap cleanup EXIT

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Comprehensive wait-for-text.sh Test Suite         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Tool path: $TOOL_PATH"
echo "Socket: $SOCKET"
echo ""

mkdir -p "$SOCKET_DIR"

# ============================================================================
# TEST 1: Missing required arguments
# ============================================================================

run_test "Missing target argument" 1 \
    "$TOOL_PATH" -p "test"

run_test "Missing pattern argument" 1 \
    "$TOOL_PATH" -t "test:0.0"

# ============================================================================
# TEST 2: Pattern found immediately
# ============================================================================

# Create a session with static text
tmux -S "$SOCKET" new-session -d -s static-test "echo 'Ready to start' && sleep 60"
sleep 0.5  # Let output appear

run_test "Find pattern immediately - regex" 0 \
    "$TOOL_PATH" -S "$SOCKET" -t static-test:0.0 -p "Ready" -T 5

run_test "Find pattern immediately - fixed string" 0 \
    "$TOOL_PATH" -S "$SOCKET" -t static-test:0.0 -p "Ready to start" -F -T 5

# ============================================================================
# TEST 3: Pattern found after delay
# ============================================================================

# Create a session that outputs after a delay
tmux -S "$SOCKET" new-session -d -s delay-test "sleep 2 && echo 'DONE' && sleep 60"

run_test "Find pattern after delay" 0 \
    "$TOOL_PATH" -S "$SOCKET" -t delay-test:0.0 -p "DONE" -T 10 -i 0.3

# ============================================================================
# TEST 4: Timeout when pattern not found
# ============================================================================

# Create a session with text that doesn't match
tmux -S "$SOCKET" new-session -d -s timeout-test "echo 'Hello World' && sleep 60"
sleep 0.5

run_test "Timeout when pattern not found" 1 \
    "$TOOL_PATH" -S "$SOCKET" -t timeout-test:0.0 -p "NOTFOUND" -T 2 -i 0.5

# ============================================================================
# TEST 5: Regex patterns
# ============================================================================

tmux -S "$SOCKET" new-session -d -s regex-test "echo 'Log entry [ERROR] Something failed' && sleep 60"
sleep 0.5

run_test "Regex pattern - with brackets" 0 \
    "$TOOL_PATH" -S "$SOCKET" -t regex-test:0.0 -p "\[ERROR\]" -T 5

run_test "Regex pattern - with wildcards" 0 \
    "$TOOL_PATH" -S "$SOCKET" -t regex-test:0.0 -p "entry.*failed" -T 5

# ============================================================================
# TEST 6: Multiple lines and history
# ============================================================================

# Create a session with multiple lines of output
tmux -S "$SOCKET" new-session -d -s multiline-test "for i in {1..10}; do echo \"Line \$i\"; done && echo 'COMPLETE' && sleep 60"
sleep 1

run_test "Find pattern in multiline output" 0 \
    "$TOOL_PATH" -S "$SOCKET" -t multiline-test:0.0 -p "COMPLETE" -T 5

run_test "Find pattern in earlier line" 0 \
    "$TOOL_PATH" -S "$SOCKET" -t multiline-test:0.0 -p "Line 5" -T 5 -l 20

# ============================================================================
# TEST 7: Custom polling interval
# ============================================================================

# Create session that outputs after 1 second
tmux -S "$SOCKET" new-session -d -s interval-test "sleep 1 && echo 'READY' && sleep 60"

# Test with fast polling (should find it quickly)
run_test "Fast polling interval (0.2s)" 0 \
    "$TOOL_PATH" -S "$SOCKET" -t interval-test:0.0 -p "READY" -T 5 -i 0.2

# ============================================================================
# TEST 8: Different target formats
# ============================================================================

# Create session with named window
tmux -S "$SOCKET" new-session -d -s format-test -n mywindow "echo 'Window output' && sleep 60"
sleep 0.5

run_test "Target format: session:window.pane" 0 \
    "$TOOL_PATH" -S "$SOCKET" -t format-test:mywindow.0 -p "Window output" -T 5

run_test "Target format: session:number.pane" 0 \
    "$TOOL_PATH" -S "$SOCKET" -t format-test:0.0 -p "Window output" -T 5

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
