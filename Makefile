.PHONY: help setup install build clean test lint format docs run demo validate all ci all-checks

# =============================================================================
# HELP & INFO
# =============================================================================

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# SETUP & INSTALLATION
# =============================================================================

setup:  ## Set up complete development environment
	poetry install --with dev
	poetry run pre-commit install || echo "pre-commit not configured"

install:  ## Install dependencies
	poetry install --with dev

install-wheel:  ## Build and install wheel package locally
	poetry build
	pip install dist/*.whl --force-reinstall

install-system:  ## Install system-wide (use with caution)
	pip uninstall -y repo2ai || true
	pip install --upgrade . --user

uninstall:  ## Uninstall package
	pip uninstall repo2ai -y || true

# =============================================================================
# BUILD & PACKAGING
# =============================================================================

build:  ## Build package
	poetry build

clean:  uninstall ## Clean build artifacts and cache
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# =============================================================================
# CODE QUALITY
# =============================================================================

format:  ## Format code with black
	poetry run black src/ tests/

format-check:  ## Check code formatting without changes
	poetry run black --check src/ tests/

lint:  ## Run linting (flake8 + mypy)
	poetry run flake8 src/ tests/
	poetry run mypy src/repo2ai/


# =============================================================================
# TESTING
# =============================================================================

test:  ## Run tests
	poetry run python -m pytest tests/ -v

test-cov:  ## Run tests with coverage report
	poetry run python -m pytest tests/ -v --cov=src/repo2ai --cov-report=html --cov-report=term-missing

test-install:  ## Test installation in clean environment
	python -m venv test_env
	test_env/bin/pip install .
	test_env/bin/repo2ai --help
	rm -rf test_env

# =============================================================================
# DOCUMENTATION
# =============================================================================

docs:  ## Generate documentation (render diagrams)
	@echo "Rendering PlantUML diagrams..."
	@if command -v plantuml >/dev/null 2>&1; then \
		mkdir -p docs/images && \
		cd docs && \
		plantuml -tpng architecture/c4/*.puml -o ../images/ && \
		echo "✓ Diagrams rendered to docs/images/"; \
	elif [ -f plantuml.jar ]; then \
		mkdir -p docs/images && \
		cd docs && \
		java -jar plantuml.jar -tpng architecture/c4/*.puml -o ../images/ && \
		echo "✓ Diagrams rendered to docs/images/"; \
	else \
		echo '⚠ PlantUML not found. Install with: brew install plantuml (macOS) or apt-get install plantuml (Ubuntu)'; \
		echo '  Alternative: Download plantuml.jar and run: java -jar plantuml.jar -tpng docs/architecture/c4/*.puml -o docs/images/'; \
	fi

# =============================================================================
# RUNNING & DEMOS
# =============================================================================

run:  ## Run CLI on current directory
	poetry run repo2ai .

run-help:  ## Show CLI help
	poetry run repo2ai --help

run-clipboard: ## Run CLI in clipboard mode
	poetry run repo2ai . --clipboard

run-file:  ## Run with file output
	poetry run repo2ai . --output example_output.md

run-chat-gpt:  ## Run with ChatGPT integration
	poetry run repo2ai . --open-chat chatgpt --prompt "Please analyze this repository structure"

run-chat-claude:  ## Run with ChatGPT integration
	poetry run repo2ai . --open-chat claude --prompt "Please analyze this repository structure"

run-chat-gemini:  ## Run with ChatGPT integration
	poetry run repo2ai . --open-chat gemini --prompt "Please analyze this repository structure"

run-chat-all:  ## Run with all AI services
	poetry run repo2ai . --chat-all --prompt "Review this codebase"

demo:  ## Demonstrate key features
	@echo "🚀 Demonstrating repo2ai features..."
	@echo "\n1. Basic export:"
	poetry run repo2ai . --max-file-size 1000 --output demo.md
	@echo "\n2. With AI integration:"
	@echo "   Run: make run-chat"
	@echo "\n3. All features:"
	@echo "   Run: make run-chat-all"

# =============================================================================
# VALIDATION & CI
# =============================================================================

validate:  ## Validate project configuration
	@echo "Validating GitHub Actions workflows..."
	@if command -v actionlint >/dev/null 2>&1; then \
		actionlint .github/workflows/*.yml; \
		echo "✓ Workflows validated"; \
	else \
		echo "⚠ actionlint not found. Install with: go install github.com/rhymond/actionlint/cmd/actionlint@latest"; \
	fi

ci:  ## Run CI checks locally (format-check, lint, test)
	@echo "Running local CI simulation..."
	make format-check
	make lint
	make test
	@echo "✓ Local CI checks passed"

all-checks:  ## Run all quality checks (format-check, lint, test)
	@echo "Running all quality checks..."
	make format-check
	make lint
	make test
	@echo "✓ All checks passed"

# =============================================================================
# COMPLETE WORKFLOWS
# =============================================================================

all:  ## Complete end-to-end pipeline (format, lint, test, docs, build)
	@echo "Running complete build pipeline..."
	make format
	make lint
	make test
	make docs
	make build
	@echo "✓ Complete pipeline finished successfully"

dev-check:  ## Quick development check (format-check + lint + test)
	make format-check
	make lint
	make test

full-check:  ## Full validation (ci + validate + test-install)
	make ci
	make validate
	make test-install