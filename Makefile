.PHONY: help sync validate validate-strict validate-yaml validate-json validate-structure clean test test-tmux-build test-tmux test-tmux-local test-tmux-shell test-session-registry test-session-registry-local test-registry test-create-session test-list-sessions test-cleanup-sessions test-session-integration test-playwright-build test-playwright test-playwright-local test-playwright-shell lint lint-python lint-python-fix lint-shellcheck lint-shellcheck-strict lint-fix type-check format format-check format-playwright format-playwright-check lint-playwright

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(CYAN)Claude Marketplace - Makefile Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@grep -E '^(sync|init):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-30s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Validation:$(NC)"
	@grep -E '^validate.*:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-30s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@grep -E '^test.*:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-30s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@grep -E '^(lint|format|clean)(-[a-z]+)*:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-30s$(NC) %s\n", $$1, $$2}'
	@echo ""

sync: ## Sync dependencies with uv (manual - uv run does this automatically)
	@echo "$(CYAN)Syncing dependencies with uv...$(NC)"
	uv sync
	@echo "$(GREEN)✓ Dependencies synced$(NC)"

validate: ## Run all validation checks
	@echo "$(CYAN)Running all validation checks...$(NC)"
	@uv run scripts/validators/validate_all.py

validate-strict: ## Run all validation checks in strict mode (fail on warnings)
	@echo "$(CYAN)Running all validation checks (strict mode)...$(NC)"
	@uv run scripts/validators/validate_all.py --strict

validate-yaml: ## Validate YAML frontmatter in SKILL.md files
	@echo "$(CYAN)Validating YAML frontmatter...$(NC)"
	@uv run scripts/validators/validate_yaml.py

validate-yaml-strict: ## Validate YAML frontmatter (strict mode)
	@echo "$(CYAN)Validating YAML frontmatter (strict mode)...$(NC)"
	@uv run scripts/validators/validate_yaml.py --strict

validate-json: ## Validate JSON manifests (plugin.json, marketplace.json)
	@echo "$(CYAN)Validating JSON manifests...$(NC)"
	@uv run scripts/validators/validate_json.py --all

validate-json-strict: ## Validate JSON manifests (strict mode)
	@echo "$(CYAN)Validating JSON manifests (strict mode)...$(NC)"
	@uv run scripts/validators/validate_json.py --all --strict

validate-structure: ## Validate file structure and naming conventions
	@echo "$(CYAN)Validating file structure...$(NC)"
	@uv run scripts/validators/validate_structure.py

validate-structure-strict: ## Validate file structure (strict mode)
	@echo "$(CYAN)Validating file structure (strict mode)...$(NC)"
	@uv run scripts/validators/validate_structure.py --strict

test: ## Run pytest tests
	@echo "$(CYAN)Running tests...$(NC)"
	@if find tests -name 'test_*.py' -type f | grep -q .; then \
		uv run pytest tests/ -v; \
	else \
		echo "$(YELLOW)No Python tests found - skipping pytest$(NC)"; \
		echo "$(YELLOW)Bash tests are located in tests/bash/ (run with make test-tmux)$(NC)"; \
	fi

test-cov: ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	@if find tests -name 'test_*.py' -type f | grep -q .; then \
		uv run pytest tests/ -v --cov=scripts --cov-report=html --cov-report=term; \
	else \
		echo "$(YELLOW)No Python tests found - skipping pytest with coverage$(NC)"; \
		echo "$(YELLOW)Bash tests are located in tests/bash/ (run with make test-tmux)$(NC)"; \
	fi

# Docker configuration for tmux tests
DOCKER_IMAGE := tmux-tests
DOCKER_RUN_OPTS ?= --rm -t
DOCKER_RUN := docker run $(DOCKER_RUN_OPTS) -v $(PWD):/workspace:ro -w /workspace $(DOCKER_IMAGE)

# Tmux test groups
TMUX_BASE_TESTS := pane-health wait-for-text find-sessions safe-send
TMUX_SESSION_REGISTRY_TESTS := registry create-session list-sessions cleanup-sessions kill-session session-integration
TMUX_TESTS := $(TMUX_BASE_TESTS) $(TMUX_SESSION_REGISTRY_TESTS)

# Helper macros for running tests
define run_test_docker
	@echo ""
	@echo "$(YELLOW)Running $1.sh tests...$(NC)"
	$(DOCKER_RUN) tests/bash/test-$1.sh
endef

define run_test_local
	@echo ""
	@echo "$(YELLOW)Running $1.sh tests...$(NC)"
	tests/bash/test-$1.sh
endef

test-tmux-build: ## Build Docker image for tmux tests
	@echo "$(CYAN)Building Docker image for tmux tests...$(NC)"
	docker build -f tests/Dockerfile.tests -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)✓ Docker image built: $(DOCKER_IMAGE)$(NC)"

test-tmux: test-tmux-build ## Run all tmux tool tests in Docker
	@echo "$(CYAN)Running all tmux tests in Docker...$(NC)"
	$(foreach t,$(TMUX_TESTS),$(call run_test_docker,$(t)))
	@echo ""
	@echo "$(GREEN)✓ All tmux tests passed ($(words $(TMUX_TESTS)) test suites)$(NC)"

test-session-registry: test-tmux-build ## Run tmux session registry tests in Docker
	@echo "$(CYAN)Running tmux session registry tests in Docker...$(NC)"
	$(foreach t,$(TMUX_SESSION_REGISTRY_TESTS),$(call run_test_docker,$(t)))
	@echo ""
	@echo "$(GREEN)✓ Session registry tests passed ($(words $(TMUX_SESSION_REGISTRY_TESTS)) test suites)$(NC)"

test-tmux/%: test-tmux-build ## Run specific tmux test (e.g., make test-tmux/pane-health)
	@echo "$(CYAN)Running tmux test: $*$(NC)"
	$(DOCKER_RUN) tests/bash/test-$*.sh

test-tmux-local: ## Run tmux tests locally (without Docker)
	@echo "$(CYAN)Running tmux tests locally...$(NC)"
	$(foreach t,$(TMUX_TESTS),$(call run_test_local,$(t)))
	@echo ""
	@echo "$(GREEN)✓ All tmux tests passed ($(words $(TMUX_TESTS)) test suites)$(NC)"

test-session-registry-local: ## Run session registry tests locally (without Docker)
	@echo "$(CYAN)Running session registry tests locally...$(NC)"
	$(foreach t,$(TMUX_SESSION_REGISTRY_TESTS),$(call run_test_local,$(t)))
	@echo ""
	@echo "$(GREEN)✓ Session registry tests passed ($(words $(TMUX_SESSION_REGISTRY_TESTS)) test suites)$(NC)"

# Individual test targets (Docker)
test-registry: test-tmux-build ## Run registry library tests in Docker
	$(call run_test_docker,registry)

test-create-session: test-tmux-build ## Run create-session.sh tests in Docker
	$(call run_test_docker,create-session)

test-list-sessions: test-tmux-build ## Run list-sessions.sh tests in Docker
	$(call run_test_docker,list-sessions)

test-cleanup-sessions: test-tmux-build ## Run cleanup-sessions.sh tests in Docker
	$(call run_test_docker,cleanup-sessions)

test-kill-session: test-tmux-build ## Run kill-session.sh tests in Docker
	$(call run_test_docker,kill-session)

test-session-integration: test-tmux-build ## Run session integration tests in Docker
	$(call run_test_docker,session-integration)

test-tmux-shell: test-tmux-build ## Open interactive shell in tmux test container
	@echo "$(CYAN)Opening shell in tmux test container...$(NC)"
	@echo "$(YELLOW)Run tests with: ./tests/bash/test-*.sh$(NC)"
	@docker run --rm -it -v $(PWD):/workspace:ro -w /workspace $(DOCKER_IMAGE) /bin/bash

# Playwright test configuration
PLAYWRIGHT_DOCKER_IMAGE := playwright-tests
PLAYWRIGHT_DOCKER_RUN := docker run --rm -t -v $(PWD):/workspace:ro -w /workspace $(PLAYWRIGHT_DOCKER_IMAGE)

test-playwright-build: ## Build Docker image for playwright tests
	@echo "$(CYAN)Building Docker image for playwright tests...$(NC)"
	docker build -f tests/Dockerfile.playwright -t $(PLAYWRIGHT_DOCKER_IMAGE) .
	@echo "$(GREEN)✓ Docker image built: $(PLAYWRIGHT_DOCKER_IMAGE)$(NC)"

test-playwright: test-playwright-build ## Run playwright tests in Docker
	@echo "$(CYAN)Running playwright tests in Docker...$(NC)"
	$(PLAYWRIGHT_DOCKER_RUN) tests/bash/test-playwright.sh
	@echo "$(GREEN)✓ Playwright tests passed$(NC)"

test-playwright-local: ## Run playwright tests locally (requires browser installed)
	@echo "$(CYAN)Running playwright tests locally...$(NC)"
	@echo "$(YELLOW)Note: Requires playwright browsers to be installed$(NC)"
	tests/bash/test-playwright.sh
	@echo "$(GREEN)✓ Playwright tests passed$(NC)"

test-playwright-shell: test-playwright-build ## Open interactive shell in playwright test container
	@echo "$(CYAN)Opening shell in playwright test container...$(NC)"
	@docker run --rm -it -v $(PWD):/workspace:ro -w /workspace $(PLAYWRIGHT_DOCKER_IMAGE) /bin/bash

lint: ## Run all linting checks (ruff + shellcheck)
	@echo "$(CYAN)Running all linting checks...$(NC)"
	@$(MAKE) lint-python
	@$(MAKE) lint-shellcheck

lint-python: ## Run Python linting checks (ruff)
	@echo "$(CYAN)Running Python linting checks...$(NC)"
	@uv run ruff check scripts/ tests/

lint-python-fix: ## Fix Python linting issues automatically
	@echo "$(CYAN)Fixing Python linting issues...$(NC)"
	@uv run ruff check --fix scripts/ tests/

lint-shellcheck: ## Run shellcheck on all bash scripts (report only)
	@echo "$(CYAN)Running shellcheck on bash scripts...$(NC)"
	@echo "$(YELLOW)Checking plugin scripts...$(NC)"
	@find plugins/*/tools -name "*.sh" -type f -print0 | xargs -0 shellcheck --color=auto || true
	@echo "$(YELLOW)Checking test scripts...$(NC)"
	@find tests/bash -name "*.sh" -type f -print0 2>/dev/null | xargs -0 shellcheck --color=auto || true
	@echo "$(GREEN)✓ Shellcheck completed$(NC)"

lint-shellcheck-strict: ## Run shellcheck on all bash scripts (fail on issues)
	@echo "$(CYAN)Running shellcheck on bash scripts (strict mode)...$(NC)"
	@echo "$(YELLOW)Checking plugin scripts...$(NC)"
	@find plugins/*/tools -name "*.sh" -type f -print0 | xargs -0 shellcheck --color=auto
	@echo "$(YELLOW)Checking test scripts...$(NC)"
	@find tests/bash -name "*.sh" -type f -print0 2>/dev/null | xargs -0 shellcheck --color=auto
	@echo "$(GREEN)✓ All shellcheck checks passed$(NC)"

lint-fix: lint-python-fix ## Fix linting issues automatically (Python only)

type-check: ## Run type checking with ty
	@echo "$(CYAN)Running type checks with ty...$(NC)"
	@uv run ty check scripts/ tests/

format: ## Format code with black
	@echo "$(CYAN)Formatting code with black...$(NC)"
	@uv run black scripts/ tests/

format-check: ## Check code formatting without making changes
	@echo "$(CYAN)Checking code formatting...$(NC)"
	@uv run black --check scripts/ tests/

# Playwright Python scripts
PLAYWRIGHT_SCRIPTS := plugins/playwright/scripts

format-playwright: ## Format playwright scripts with ruff
	@echo "$(CYAN)Formatting playwright scripts with ruff...$(NC)"
	@uv run ruff format $(PLAYWRIGHT_SCRIPTS)/
	@echo "$(GREEN)✓ Playwright scripts formatted$(NC)"

format-playwright-check: ## Check playwright script formatting
	@echo "$(CYAN)Checking playwright script formatting...$(NC)"
	@uv run ruff format --check $(PLAYWRIGHT_SCRIPTS)/

lint-playwright: ## Type check playwright scripts with ty
	@echo "$(CYAN)Type checking playwright scripts with ty...$(NC)"
	@uv run ty check $(PLAYWRIGHT_SCRIPTS)/

clean: ## Clean up generated files
	@echo "$(CYAN)Cleaning up...$(NC)"
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Cleaned up$(NC)"

# CI/CD target for continuous integration
ci: validate-strict test lint type-check format-check test-tmux ## Run all CI/CD checks (strict mode)
	@echo "$(GREEN)✓ All CI/CD checks passed$(NC)"

# Quick check target for development
check: validate test ## Quick validation and test (non-strict)
	@echo "$(GREEN)✓ Quick checks passed$(NC)"

# Show project status
status: ## Show project validation status
	@echo "$(CYAN)Project Validation Status$(NC)"
	@echo ""
	@echo "$(YELLOW)Plugins:$(NC)"
	@ls -1 plugins/ 2>/dev/null || echo "  No plugins found"
	@echo ""
	@echo "$(YELLOW)Skills:$(NC)"
	@find plugins -name "SKILL.md" -type f 2>/dev/null | wc -l | xargs echo "  SKILL.md files:"
	@echo ""
	@echo "$(YELLOW)Manifests:$(NC)"
	@find . -name "plugin.json" -type f 2>/dev/null | wc -l | xargs echo "  plugin.json files:"
	@find . -name "marketplace.json" -type f 2>/dev/null | wc -l | xargs echo "  marketplace.json files:"

# Initialize development environment
init: ## Initialize development environment
	@echo "$(CYAN)Initializing development environment...$(NC)"
	@echo "$(YELLOW)1. Syncing dependencies with uv...$(NC)"
	uv sync
	@echo "$(YELLOW)2. Setting up pre-commit hooks...$(NC)"
	@if [ -f .git/hooks/pre-commit ]; then \
		echo "  Pre-commit hook already exists"; \
	else \
		echo '#!/bin/sh' > .git/hooks/pre-commit; \
		echo 'make validate-strict' >> .git/hooks/pre-commit; \
		chmod +x .git/hooks/pre-commit; \
		echo "  $(GREEN)✓ Pre-commit hook installed$(NC)"; \
	fi
	@echo "$(GREEN)✓ Development environment ready$(NC)"
	@echo ""
	@echo "$(CYAN)Next steps:$(NC)"
	@echo "  • Run 'make validate' to check your marketplace"
	@echo "  • Run 'make test' to run tests"
	@echo "  • Run 'make help' to see all available commands"
