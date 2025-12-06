#!/usr/bin/env bash
set -euo pipefail

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PLAYWRIGHT_DIR="$REPO_ROOT/plugins/playwright/scripts"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Temp directory for test artifacts
TEST_TMP="${TMPDIR:-/tmp}/playwright-test-$$"
mkdir -p "$TEST_TMP"

# Helper function to run test with expected exit code
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
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Helper function to run test and check output contains string
run_test_output_contains() {
    local test_name="$1"
    local expected_string="$2"
    shift 2
    local cmd=("$@")

    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Test $TESTS_TOTAL: $test_name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "Command: ${cmd[*]}"
    echo "Expected output to contain: $expected_string"
    echo ""

    # Run command and capture output
    set +e
    output=$("${cmd[@]}" 2>&1)
    actual_exit=$?
    set -e

    echo "Output:"
    echo "$output"
    echo ""

    if echo "$output" | grep -q "$expected_string"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED - output does not contain expected string${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Helper function to check file exists
run_test_file_exists() {
    local test_name="$1"
    local file_path="$2"
    shift 2
    local cmd=("$@")

    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Test $TESTS_TOTAL: $test_name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "Command: ${cmd[*]}"
    echo "Expected file: $file_path"
    echo ""

    # Run command
    set +e
    output=$("${cmd[@]}" 2>&1)
    actual_exit=$?
    set -e

    echo "Output:"
    echo "$output"
    echo ""

    if [[ -f "$file_path" ]]; then
        local size
        size=$(stat -f%z "$file_path" 2>/dev/null || stat -c%s "$file_path" 2>/dev/null || echo "unknown")
        echo "File exists: $file_path (size: $size bytes)"
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED - file does not exist${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Cleanup function
cleanup() {
    echo -e "\n${BLUE}Cleaning up test artifacts...${NC}"
    rm -rf "$TEST_TMP"
}

# Ensure cleanup on exit
trap cleanup EXIT

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Playwright Scripts Integration Tests             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Scripts directory: $PLAYWRIGHT_DIR"
echo "Temp directory: $TEST_TMP"
echo ""

# ============================================================================
# TEST: Scripts exist
# ============================================================================

echo -e "\n${BLUE}=== Script Existence Tests ===${NC}"

for script in check_setup.py screenshot.py navigate.py fill_form.py evaluate.py; do
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    if [[ -f "$PLAYWRIGHT_DIR/$script" ]]; then
        echo -e "${GREEN}✓${NC} $script exists"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $script missing"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
done

# ============================================================================
# TEST: check_setup.py
# ============================================================================

echo -e "\n${BLUE}=== check_setup.py Tests ===${NC}"

run_test_output_contains "check_setup.py shows browser status" \
    "Checking Playwright browser installation" \
    uv run "$PLAYWRIGHT_DIR/check_setup.py"

# ============================================================================
# TEST: screenshot.py
# ============================================================================

echo -e "\n${BLUE}=== screenshot.py Tests ===${NC}"

run_test_output_contains "screenshot.py --help shows usage" \
    "usage:" \
    uv run "$PLAYWRIGHT_DIR/screenshot.py" --help

run_test "screenshot.py without URL fails" 2 \
    uv run "$PLAYWRIGHT_DIR/screenshot.py"

SCREENSHOT_PATH="$TEST_TMP/test-screenshot.png"
run_test_file_exists "screenshot.py captures example.com" \
    "$SCREENSHOT_PATH" \
    uv run "$PLAYWRIGHT_DIR/screenshot.py" https://example.com --headless -o "$SCREENSHOT_PATH"

# ============================================================================
# TEST: navigate.py
# ============================================================================

echo -e "\n${BLUE}=== navigate.py Tests ===${NC}"

run_test_output_contains "navigate.py --help shows usage" \
    "usage:" \
    uv run "$PLAYWRIGHT_DIR/navigate.py" --help

run_test "navigate.py without URL fails" 2 \
    uv run "$PLAYWRIGHT_DIR/navigate.py"

run_test_output_contains "navigate.py shows title" \
    "Example Domain" \
    uv run "$PLAYWRIGHT_DIR/navigate.py" https://example.com --headless

run_test_output_contains "navigate.py --title extracts title" \
    "Example Domain" \
    uv run "$PLAYWRIGHT_DIR/navigate.py" https://example.com --headless --title

run_test_output_contains "navigate.py --links returns JSON" \
    '"href"' \
    uv run "$PLAYWRIGHT_DIR/navigate.py" https://example.com --headless --links

run_test_output_contains "navigate.py --text extracts text" \
    "This domain is for use in" \
    uv run "$PLAYWRIGHT_DIR/navigate.py" https://example.com --headless --text

# ============================================================================
# TEST: evaluate.py
# ============================================================================

echo -e "\n${BLUE}=== evaluate.py Tests ===${NC}"

run_test_output_contains "evaluate.py --help shows usage" \
    "usage:" \
    uv run "$PLAYWRIGHT_DIR/evaluate.py" --help

run_test_output_contains "evaluate.py returns document.title" \
    "Example Domain" \
    uv run "$PLAYWRIGHT_DIR/evaluate.py" https://example.com "document.title" --headless

run_test_output_contains "evaluate.py evaluates arithmetic" \
    "2" \
    uv run "$PLAYWRIGHT_DIR/evaluate.py" https://example.com "1+1" --headless

run_test_output_contains "evaluate.py counts links" \
    "1" \
    uv run "$PLAYWRIGHT_DIR/evaluate.py" https://example.com "document.querySelectorAll('a').length" --headless

# ============================================================================
# TEST: fill_form.py
# ============================================================================

echo -e "\n${BLUE}=== fill_form.py Tests ===${NC}"

run_test_output_contains "fill_form.py --help shows usage" \
    "usage:" \
    uv run "$PLAYWRIGHT_DIR/fill_form.py" --help

run_test "fill_form.py without URL fails" 2 \
    uv run "$PLAYWRIGHT_DIR/fill_form.py"

# ============================================================================
# SUMMARY
# ============================================================================

echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                      Test Summary                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Total tests:  $TESTS_TOTAL"
echo -e "Passed:       ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed:       ${RED}$TESTS_FAILED${NC}"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
