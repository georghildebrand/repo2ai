# Contributing to repo2ai

Thank you for your interest in contributing to repo2ai!

## Prerequisites

- Python 3.11+
- Poetry for dependency management
- Make for task automation
- PlantUML for diagram generation (optional)

## Development Setup

```bash
git clone https://github.com/georghildebrand/repo2ai.git
cd repo2ai
make setup  # Install dependencies + dev tools
```

## Development Workflow

### Daily Development

```bash
make format     # Format code with Black
make lint       # Run linting (flake8 + mypy)
make test       # Run tests
make test-cov   # Run tests with coverage
```

### Before Committing

```bash
make ci         # Run all CI checks locally
```

### Full Pipeline

```bash
make all        # Complete pipeline (format + lint + test + docs + build)
```

## Available Make Targets

| Target | Description |
|--------|-------------|
| `make setup` | Complete development environment setup |
| `make install` | Install dependencies only |
| `make format` | Format code with Black |
| `make format-check` | Check formatting without changes |
| `make lint` | Run linting (flake8 + mypy) |
| `make test` | Run tests |
| `make test-cov` | Run tests with coverage |
| `make docs` | Render PlantUML diagrams |
| `make ci` | Run CI checks locally |
| `make all` | Complete pipeline |
| `make clean` | Clean build artifacts |
| `make build` | Build wheel and sdist |

## Code Quality Standards

- **Code Formatting**: Black with 180 character line length
- **Linting**: Flake8 for PEP8 compliance
- **Type Checking**: MyPy with strict settings on `src/repo2ai/`
- **Testing**: Pytest with high coverage requirements
- **Documentation**: Comprehensive docstrings and architecture diagrams

## Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run single test file
poetry run pytest tests/test_core.py -v

# Run single test class
poetry run pytest tests/test_core.py::TestLanguageDetection -v
```

## Contribution Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run quality checks: `make ci`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## Guidelines

- Follow the existing code style (enforced by Black)
- Add tests for new functionality
- Update documentation for user-facing changes
- Ensure all CI checks pass
- Update architecture diagrams if adding new modules
