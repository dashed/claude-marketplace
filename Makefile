.PHONY: help sync validate validate-strict validate-yaml validate-json validate-structure clean test test-tmux-build test-tmux test-tmux-local test-tmux-shell lint format

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
	@grep -E '^(sync|init):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Validation:$(NC)"
	@grep -E '^validate.*:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@grep -E '^(test|lint|format|clean):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
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
	@uv run pytest tests/ -v

test-cov: ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	@uv run pytest tests/ -v --cov=scripts --cov-report=html --cov-report=term

# Docker configuration for tmux tests
DOCKER_IMAGE := tmux-tests
DOCKER_RUN_OPTS ?= --rm -t
DOCKER_RUN := docker run $(DOCKER_RUN_OPTS) -v $(PWD):/workspace:ro -w /workspace $(DOCKER_IMAGE)

test-tmux-build: ## Build Docker image for tmux tests
	@echo "$(CYAN)Building Docker image for tmux tests...$(NC)"
	docker build -f tests/Dockerfile.tests -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)✓ Docker image built: $(DOCKER_IMAGE)$(NC)"

test-tmux: test-tmux-build ## Run all tmux tool tests in Docker
	@echo "$(CYAN)Running all tmux tests in Docker...$(NC)"
	@echo ""
	@echo "$(YELLOW)Running pane-health.sh tests...$(NC)"
	$(DOCKER_RUN) tests/bash/test-pane-health.sh
	@echo ""
	@echo "$(YELLOW)Running wait-for-text.sh tests...$(NC)"
	$(DOCKER_RUN) tests/bash/test-wait-for-text.sh
	@echo ""
	@echo "$(YELLOW)Running find-sessions.sh tests...$(NC)"
	$(DOCKER_RUN) tests/bash/test-find-sessions.sh
	@echo ""
	@echo "$(GREEN)✓ All tmux tests passed$(NC)"

test-tmux/%: test-tmux-build ## Run specific tmux test (e.g., make test-tmux/pane-health)
	@echo "$(CYAN)Running tmux test: $*$(NC)"
	$(DOCKER_RUN) tests/bash/test-$*.sh

test-tmux-local: ## Run tmux tests locally (without Docker)
	@echo "$(CYAN)Running tmux tests locally...$(NC)"
	@echo ""
	@echo "$(YELLOW)Running pane-health.sh tests...$(NC)"
	tests/bash/test-pane-health.sh
	@echo ""
	@echo "$(YELLOW)Running wait-for-text.sh tests...$(NC)"
	tests/bash/test-wait-for-text.sh
	@echo ""
	@echo "$(YELLOW)Running find-sessions.sh tests...$(NC)"
	tests/bash/test-find-sessions.sh
	@echo ""
	@echo "$(GREEN)✓ All tmux tests passed$(NC)"

test-tmux-shell: test-tmux-build ## Open interactive shell in tmux test container
	@echo "$(CYAN)Opening shell in tmux test container...$(NC)"
	@echo "$(YELLOW)Run tests with: ./tests/bash/test-*.sh$(NC)"
	@docker run --rm -it -v $(PWD):/workspace:ro -w /workspace $(DOCKER_IMAGE) /bin/bash

lint: ## Run linting checks (ruff)
	@echo "$(CYAN)Running linting checks...$(NC)"
	@uv run ruff check scripts/ tests/

lint-fix: ## Fix linting issues automatically
	@echo "$(CYAN)Fixing linting issues...$(NC)"
	@uv run ruff check --fix scripts/ tests/

format: ## Format code with black
	@echo "$(CYAN)Formatting code with black...$(NC)"
	@uv run black scripts/ tests/

format-check: ## Check code formatting without making changes
	@echo "$(CYAN)Checking code formatting...$(NC)"
	@uv run black --check scripts/ tests/

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
ci: validate-strict test lint format-check ## Run all CI/CD checks (strict mode)
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
