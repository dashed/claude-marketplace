# Tests

Comprehensive test suite for claude-marketplace tools and plugins.

## Overview

This directory contains tests for:
- **tmux tools**: Bash-based integration tests for tmux helper scripts (pane-health.sh, wait-for-text.sh, find-sessions.sh)
- **Python validators**: pytest tests for validation scripts (coming soon)

## Directory Structure

```
tests/
├── bash/                      # Bash integration tests
│   ├── test-pane-health.sh   # Tests for pane-health.sh
│   ├── test-wait-for-text.sh # Tests for wait-for-text.sh
│   └── test-find-sessions.sh # Tests for find-sessions.sh
├── fixtures/                  # Test fixtures and configs
│   └── tmux.test.conf        # Minimal tmux config for tests
├── Dockerfile.tests          # Docker image for isolated test environment
└── README.md                 # This file
```

## Running Tests

### Quick Start (Docker - Recommended)

Run all tmux tests in an isolated Docker container:

```bash
make test-tmux
```

This will:
1. Build the Docker image (if needed)
2. Run all tmux tool tests
3. Clean up automatically

### Makefile Targets

#### Docker-based Tests (Recommended)

- **`make test-tmux`** - Run all tmux tests in Docker (builds image first)
- **`make test-tmux-build`** - Build Docker image for tests
- **`make test-tmux/pane-health`** - Run specific test (e.g., pane-health)
- **`make test-tmux/wait-for-text`** - Run wait-for-text tests
- **`make test-tmux/find-sessions`** - Run find-sessions tests
- **`make test-tmux-shell`** - Open interactive shell in test container

#### Local Tests (No Docker)

- **`make test-tmux-local`** - Run all tmux tests locally

**Requirements for local tests:**
- tmux installed
- bash
- jq (for JSON validation)
- Standard Unix tools (ps, grep, etc.)

#### Python Tests

- **`make test`** - Run pytest tests (for Python validators)
- **`make test-cov`** - Run tests with coverage report

### Running Tests Manually

#### Individual Test Scripts

All test scripts are executable and can be run directly:

```bash
# From repository root
./tests/bash/test-pane-health.sh
./tests/bash/test-wait-for-text.sh
./tests/bash/test-find-sessions.sh
```

#### In Docker Container

```bash
# Build image
docker build -f tests/Dockerfile.tests -t tmux-tests .

# Run all tests
docker run --rm -t -v $(pwd):/workspace:ro -w /workspace tmux-tests tests/bash/test-pane-health.sh
docker run --rm -t -v $(pwd):/workspace:ro -w /workspace tmux-tests tests/bash/test-wait-for-text.sh
docker run --rm -t -v $(pwd):/workspace:ro -w /workspace tmux-tests tests/bash/test-find-sessions.sh

# Interactive debugging
docker run --rm -it -v $(pwd):/workspace:ro -w /workspace tmux-tests /bin/bash
```

## Test Coverage

### tmux Tools Tests

#### test-pane-health.sh
Tests for `plugins/tmux/tools/pane-health.sh`:

- ✅ Server not running detection (exit 4)
- ✅ Session doesn't exist (exit 2)
- ✅ Pane doesn't exist (exit 2)
- ✅ Healthy pane detection (exit 0)
- ✅ Dead pane detection (exit 1)
- ✅ Different target formats (session:window.pane, session:number.pane)
- ✅ Multiple panes in same session
- ✅ JSON output validation
- ✅ Text output format
- ✅ Edge cases (missing args, invalid format)

**Total:** 18 tests

#### test-wait-for-text.sh
Tests for `plugins/tmux/tools/wait-for-text.sh`:

- ✅ Missing required arguments
- ✅ Pattern found immediately
- ✅ Pattern found after delay
- ✅ Timeout when pattern not found
- ✅ Regex patterns (anchored, character classes)
- ✅ Fixed string matching (-F flag)
- ✅ Multiline output and history
- ✅ Custom polling intervals
- ✅ Different target formats

**Total:** 14 tests

#### test-find-sessions.sh
Tests for `plugins/tmux/tools/find-sessions.sh`:

- ✅ No server running detection
- ✅ Single session on specific socket
- ✅ Multiple sessions on same socket
- ✅ Query filtering (substring search)
- ✅ Scan all sockets mode (--all)
- ✅ Scan all with query filter
- ✅ Invalid option combinations (-L + -S, --all + -S, etc.)
- ✅ Session state detection (attached/detached)

**Total:** 15 tests

### Combined Test Suite

**Total tests:** 47
**Expected pass rate:** 100%

## Docker Test Environment

### Image Details

- **Base:** debian:bookworm-slim
- **Packages:** tmux, bash, jq, curl, procps
- **Python:** uv (for future pytest integration)
- **User:** Non-root (testuser, UID 1000)
- **Locale:** UTF-8 (en_US.UTF-8)

### Configuration

- **tmux config:** `/etc/tmux.test.conf` (minimal, consistent settings)
- **Workspace:** `/workspace` (repo mounted read-only)
- **Temp dir:** `/tmp` (writable for test artifacts)

### Why Docker?

- ✅ **Isolation:** Tests don't interfere with host tmux sessions
- ✅ **Consistency:** Same tmux version and environment across machines
- ✅ **Clean state:** Each test run starts fresh
- ✅ **No pollution:** Test sockets/sessions don't persist
- ✅ **CI-ready:** Easy to run in GitHub Actions or other CI systems

## Writing New Tests

### Test Script Template

```bash
#!/usr/bin/env bash
set -euo pipefail

# Get paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TOOL_PATH="$REPO_ROOT/plugins/tmux/tools/your-tool.sh"

# Test configuration
SOCKET_DIR="${TMPDIR:-/tmp}/tmux-test-$$"
SOCKET="$SOCKET_DIR/test.sock"

# Counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Cleanup function
cleanup() {
    tmux -S "$SOCKET" kill-server 2>/dev/null || true
    rm -rf "$SOCKET_DIR"
}
trap cleanup EXIT

# Test implementation...
```

### Best Practices

1. **Isolation:** Each test creates its own tmux socket with unique PID (`$$`)
2. **Cleanup:** Always use `trap cleanup EXIT` to clean up tmux sessions
3. **Idempotent:** Tests should work regardless of host tmux state
4. **Clear output:** Use colors and formatting for readable test results
5. **Exit codes:** Exit 0 for all passed, 1 if any failed
6. **Relative paths:** Use script-relative paths, not hardcoded paths

### Adding Tests to Makefile

After creating `tests/bash/test-new-tool.sh`:

1. Make it executable: `chmod +x tests/bash/test-new-tool.sh`
2. Add to `test-tmux` target in Makefile
3. Test works: `make test-tmux/new-tool`
4. Update this README with test coverage info

## Continuous Integration

These tests are designed to run in CI environments:

```yaml
# Example GitHub Actions workflow
- name: Run tmux tests
  run: make test-tmux
```

Docker ensures consistent results across:
- Different OS versions
- Different tmux versions
- Developer machines vs CI runners

## Troubleshooting

### Tests fail locally but pass in Docker

- Check tmux version: `tmux -V`
- Check locale: `echo $LANG` (should be UTF-8)
- Try in Docker: `make test-tmux-shell` for interactive debugging

### Docker build fails

- Ensure Docker is running: `docker ps`
- Check disk space: `docker system df`
- Clean up old images: `docker system prune`

### Tests are slow

- Tests run sequentially (by design, for clarity)
- Each test creates/destroys tmux sessions (idempotent)
- Docker adds ~5-10s build time on first run (cached afterward)

### Permission errors

- Docker runs as UID 1000 by default
- Override with: `docker build --build-arg UID=$(id -u) --build-arg GID=$(id -g) ...`

## Future Enhancements

- [ ] Add pytest tests for Python validators
- [ ] Add test coverage reporting
- [ ] Add GitHub Actions workflow
- [ ] Add performance benchmarks
- [ ] Add integration tests across multiple tools
- [ ] Add fuzzing for edge cases

## Resources

- [tmux Manual](https://man7.org/linux/man-pages/man1/tmux.1.html)
- [Bash Testing Best Practices](https://github.com/bats-core/bats-core)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
