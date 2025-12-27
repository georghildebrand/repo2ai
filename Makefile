SHELL           := bash
.SHELLFLAGS     := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS      += --warn-undefined-variables
MAKEFLAGS      += --no-builtin-rules


ifeq ($(origin .RECIPEPREFIX), undefined)
  $(error This Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif
.RECIPEPREFIX = >
.DEFAULT_GOAL := help

.PHONY: help setup install build clean distclean format format-check lint test test-cov \
        test-install run run-help demo docs validate check ci all \
        install-system uninstall-system

# =============================================================================
# GLOBAL CONTRACTS
# =============================================================================

POETRY := poetry
PYTHON_SYSTEM ?= python3.12
PYTHON_POETRY := $(shell $(POETRY) run which python)

# =============================================================================
# HELP
# =============================================================================

help:  ## Show this help message
> @echo "Available commands:"
> @grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
> 	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'


# =============================================================================
# SETUP & INSTALLATION (DEV)
# =============================================================================

setup:  ## Set up development environment (Poetry + pre-commit)
> $(POETRY) install --with dev --sync
> $(POETRY) run pre-commit install || true

install:  ## Install dependencies
> $(POETRY) install --with dev --sync

# =============================================================================
# BUILD & PACKAGING
# =============================================================================

build:  ## Build wheel and sdist
> $(POETRY) build

clean:  ## Remove build artifacts and caches
> rm -rf build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage .test_env
> find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
> find . -type f -name "*.pyc" -delete

distclean: clean  ## Deep clean including virtualenv
> $(POETRY) env remove --all || true

# =============================================================================
# CODE QUALITY
# =============================================================================

format:  ## Auto-format code
> $(POETRY) run black src/ tests/

format-check:  ## Check formatting
> $(POETRY) run black --check src/ tests/

lint:  ## Lint and type-check
> $(POETRY) run flake8 src/ tests/
> $(POETRY) run mypy src/repo2ai/

# =============================================================================
# TESTING
# =============================================================================

test:  ## Run tests (Poetry environment)
> $(POETRY) run pytest tests/ -v

test-cov:  ## Run tests with coverage
> $(POETRY) run pytest tests/ -v \
> > --cov=src/repo2ai --cov-report=html --cov-report=term-missing

test-install:  ## Test wheel install in isolated virtualenv
> $(POETRY) build
> $(PYTHON_SYSTEM) -m venv .test_env
> .test_env/bin/pip install dist/*.whl
> .test_env/bin/repo2ai --help
> rm -rf .test_env

# =============================================================================
# DOCUMENTATION
# =============================================================================

docs:  ## Render PlantUML diagrams (requires plantuml)
> plantuml -tpng docs/architecture/c4/*.puml -o docs/images/

# =============================================================================
# RUNNING & DEMOS
# =============================================================================

run:  ## Run CLI on current directory
> $(POETRY) run repo2ai .

run-help:  ## Show CLI help
> $(POETRY) run repo2ai --help

demo:  ## Generate demo output
> $(POETRY) run repo2ai . --max-file-size 1000 --output demo.md

# =============================================================================
# SYSTEM INSTALL (DEV-ONLY)
# =============================================================================

install-system: build  ## Install built wheel into user site-packages (dev-only)
> $(PYTHON_SYSTEM) -m pip install --user dist/*.whl --force-reinstall

uninstall-system:  ## Remove system installation
> $(PYTHON_SYSTEM) -m pip uninstall -y repo2ai || true

# =============================================================================
# VALIDATION & CI
# =============================================================================

validate:  ## Validate GitHub Actions workflows (requires actionlint)
> actionlint .github/workflows/*.yml

check:  ## Canonical quality gate (format-check + lint + test)
> make format-check
> make lint
> make test

ci: check  ## Alias for CI systems

all:  ## Full pipeline (check + docs + build)
> make check
> make docs
> make build
