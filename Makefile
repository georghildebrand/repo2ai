.PHONY: help install test lint format clean build run docs

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	poetry install --with dev

install-wheel:  ## Build and install wheel package
	poetry build
	pip install dist/*.whl --force-reinstall

install-dev:  ## Development installation with all dependencies
	poetry install --with dev
	poetry shell || true

install-system:  ## Install system-wide (use with caution)
	pip uninstall -y repo2md || true
	pip install --upgrade . --user

uninstall:  ## Uninstall package
	pip uninstall repo2md -y || true

test-install:  ## Test installation in clean environment
	python -m venv test_env
	test_env/bin/pip install .
	test_env/bin/repo2md --help
	rm -rf test_env

test:  ## Run tests
	poetry run python -m pytest tests/ -v

test-cov:  ## Run tests with coverage
	poetry run python -m pytest tests/ -v --cov=src/repo2md --cov-report=html --cov-report=term-missing

lint:  ## Run linting
	poetry run flake8 src/ tests/
	poetry run mypy src/repo2md/

format:  ## Format code
	poetry run black src/ tests/

format-check:  ## Check code formatting
	poetry run black --check src/ tests/

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build package
	poetry build

run:  ## Run the CLI tool on current directory
	poetry run repo2md .

run-help:  ## Show CLI help
	poetry run repo2md --help

run-example:  ## Run example with output to file
	poetry run repo2md . --output example_output.md

dev-setup:  ## Set up development environment
	poetry install --with dev
	poetry run pre-commit install || echo "pre-commit not configured"

all-checks:  ## Run all checks (format, lint, test)
	make format-check
	make lint
	make test

render-diagrams:  ## Render PlantUML diagrams to PNG
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


docs:  ## Generate all documentation
	make render-diagrams

validate-workflows:  ## Validate GitHub Actions workflows
	@echo "Validating GitHub Actions workflows..."
	@if command -v actionlint >/dev/null 2>&1; then \
		actionlint .github/workflows/*.yml; \
		echo "✓ Workflows validated"; \
	else \
		echo "⚠ actionlint not found. Skipping workflow validation."; \
		echo "  Install with: curl -L https://github.com/rhymond/actionlint/releases/download/v1.6.27/actionlint_1.6.27_linux_amd64.tar.gz | tar -xz && sudo mv actionlint /usr/local/bin/"; \
	fi

ci-local:  ## Run CI checks locally (simulate GitHub Actions)
	@echo "Running local CI simulation..."
	make format-check
	make lint
	make test
	@echo "✓ Local CI checks passed"

all:  ## Run everything (format, lint, test, docs, build)
	@echo "Running complete build pipeline..."
	make format
	make lint
	make test
	make docs
	make build
	@echo "✓ Complete pipeline finished successfully"