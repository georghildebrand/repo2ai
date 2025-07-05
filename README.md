# Repo2Markdown

A minimal Python CLI tool that exports Git repository contents to structured Markdown files. Perfect for creating comprehensive repository documentation, code reviews, or feeding codebases to AI tools.

## Features

- **Git Integration**: Automatically scans Git-tracked files using `git ls-files`
- **Smart Filtering**: Respects `.gitignore` patterns and excludes binary files
- **Language Detection**: Automatically detects 25+ programming languages for syntax highlighting
- **Multiple Output Options**: File, clipboard, or stdout (combinable)
- **Configurable Filtering**: Custom ignore patterns, file size limits, meta file handling
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Zero Dependencies**: Only uses Python stdlib + optional `pyperclip` for clipboard functionality

## Installation

Currently only building form source is supported. No install from pypi atm!
### From Source

```bash
git clone https://github.com/georghildebrand/Repo2Markdown.git
cd Repo2Markdown
poetry install
```

or via pip:

Build and install the wheel!

```bash
 install-wheel
```

### Development Setup
```bash
# Full development environment
make dev-setup

# Or manually
poetry install
poetry shell
```

## Quick Start

```bash
# Export current directory to stdout
repo2md .

# Export to a file
repo2md . --output my-repo.md

# Copy to clipboard
repo2md . --clipboard

# Exclude README, LICENSE, etc.
repo2md . --exclude-meta-files

# Combine outputs
repo2md . --output docs.md --clipboard
```

## Usage

```
repo2md [PATH] [OPTIONS]

Arguments:
  PATH                  Path to repository (default: current directory)

Output Options:
  --output, -o PATH     Write to file
  --clipboard, -c       Copy to clipboard
  --stdout, -s          Output to stdout (default)

Filtering Options:
  --ignore PATTERN      Additional ignore patterns (repeatable)
  --exclude-meta-files  Exclude README, LICENSE, .gitignore, etc.
  --max-file-size SIZE  Maximum file size in bytes (default: 1MB)
  --include-meta FILES  Include specific meta files
  --exclude-meta FILES  Exclude specific meta files
```

## Examples

### Basic Export
```bash
# Export current repository
repo2md .

# Export specific directory
repo2md ./my-project

# Export with custom output path
repo2md . --output repository-export.md
```

### Output Options
```bash
# Copy to clipboard for pasting elsewhere
repo2md . --clipboard

# Both file and clipboard
repo2md . --output backup.md --clipboard

# Output to stdout for piping
repo2md . --stdout | less
```

### Advanced Filtering
```bash
# Exclude meta files (README, LICENSE, etc.)
repo2md . --exclude-meta-files

# Custom ignore patterns
repo2md . --ignore "*.log" --ignore "temp/*" --ignore "*.tmp"

# Limit file size (500KB max)
repo2md . --max-file-size 500000

# Include only specific files, ignore others
repo2md . --exclude-meta-files --include-meta README.md

# Complex filtering for AI tools
repo2md . --exclude-meta-files --ignore "*.test.js" --ignore "dist/*" --max-file-size 100000 --clipboard
```

## Output Format

The generated Markdown includes:

1. **Repository Summary**: File count, total size, root path
2. **File Structure**: Directory tree organized by folders
3. **File Contents**: Each file with syntax highlighting and metadata

Example output structure:
```markdown
# MyProject

## Repository Summary
- **Files:** 15
- **Total Size:** 0.25 MB
- **Repository Root:** `/path/to/MyProject`

## File Structure

### Root Directory
- main.py
- requirements.txt

### src/
- __init__.py
- core.py

## File Contents

### main.py
**Size:** 1024 bytes
**Language:** python

```python
def main():
    print("Hello World")
```
```

## Development

This project uses Poetry for dependency management:

```bash
# Install dependencies
poetry install

# Run tests
make test              # Run all tests
make test-cov          # Run tests with coverage

# Code quality
make format            # Format code with Black
make lint              # Run flake8 + mypy
make all-checks        # Run format-check + lint + test

# Build and package
make build             # Build wheel + source dist
make clean             # Clean build artifacts

# Local testing
make run               # Run tool on current directory
make run-example       # Generate example_output.md
make ci-local          # Run full CI pipeline locally
```

### Testing Commands

```bash
# Run specific test files
poetry run pytest tests/test_core.py -v
poetry run pytest tests/test_cli.py -v

# Test with coverage
poetry run pytest --cov=src/repo_to_markdown --cov-report=html

# Integration testing
poetry run repo2md . --output test.md
poetry run repo2md --help
```

## Supported Languages

The tool automatically detects and provides syntax highlighting for:

**Programming Languages:** Python, JavaScript, TypeScript, Java, C/C++, C#, Go, Rust, PHP, Ruby, Swift, Kotlin, Scala

**Web Technologies:** HTML, CSS, SCSS/Sass, JSX, TSX

**Data/Config:** JSON, YAML, TOML, XML, SQL, INI

**Scripts/Shell:** Bash, Zsh, Fish, PowerShell

**Documentation:** Markdown, Text

**Special Files:** Dockerfile, Makefile, .gitignore

## Architecture

The tool follows a clean, modular design based on C4 architecture principles:

### System Overview
- **Core Module**: Repository scanning, filtering, and Markdown generation
- **CLI Module**: Command-line interface and argument handling
- **Output Module**: File, clipboard, and stdout output handling

### Key Design Decisions
- **Minimal Dependencies**: Only `pyperclip` for clipboard functionality
- **Standard Library Focus**: Uses `subprocess`, `fnmatch`, `argparse` instead of heavy dependencies
- **Git Integration**: Leverages `git ls-files` for accurate file discovery
- **Binary File Detection**: Automatically excludes binary files from output

### Architecture Diagrams

The system architecture is documented using C4 diagrams in `docs/architecture/c4/`:

1. **[System Context](docs/architecture/c4/01-system-context.puml)** - High-level system interactions
2. **[Container Diagram](docs/architecture/c4/02-container-diagram.puml)** - Internal system structure
3. **[Component Diagram](docs/architecture/c4/03-component-diagram.puml)** - Detailed component breakdown

> **Viewing Diagrams**: Use the [PlantUML VS Code extension](https://marketplace.visualstudio.com/items?itemName=jebbs.plantuml) or [online PlantUML server](http://www.plantuml.com/plantuml/uml/) to render the diagrams.

### Rendering Diagrams Locally

```bash
# Install PlantUML (macOS)
brew install plantuml

# Install PlantUML (Ubuntu/Debian)
sudo apt-get install plantuml

# Render diagrams to PNG
make render-diagrams

# Generate all documentation
make docs
```

## Requirements

- **Python 3.11+** (uses modern type hints)
- **Git** (for repository scanning)
- **pyperclip** (for clipboard functionality - only dependency)

## Performance

- **Fast scanning**: Leverages Git for efficient file discovery
- **Memory efficient**: Processes files individually, not all in memory
- **Smart filtering**: Multiple layers of filtering reduce processing overhead
- **Binary detection**: Quick binary file detection prevents unnecessary processing

Typical performance:
- Small projects (< 100 files): < 1 second
- Medium projects (100-1000 files): 1-5 seconds
- Large projects (1000+ files): 5-30 seconds (depending on file sizes and filtering)

## Troubleshooting

### Common Issues

**"Git not found" or empty output:**
```bash
# Make sure you're in a Git repository
git status

# Or scan directory without Git integration
repo2md . --ignore ".git/*"
```

**"Pyperclip not available" error:**
```bash
# Install clipboard support
poetry install
# or
pip install pyperclip
```

**Large output files:**
```bash
# Reduce file size with filtering
repo2md . --exclude-meta-files --max-file-size 50000 --ignore "*.log" --ignore "dist/*"
```

**Permission errors:**
```bash
# Check file permissions
ls -la output-file.md

# Use different output directory
repo2md . --output ~/Documents/repo-export.md
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Run quality checks: `make all-checks`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Submit a pull request

### Development Workflow

The project uses GitHub Actions for CI/CD:

- **CI Pipeline**: Runs on every push and PR
  - Tests on Python 3.8-3.12
  - Code formatting and linting checks
  - Cross-platform integration tests (Ubuntu, Windows, macOS)
  - Security scanning with safety and bandit
  - Architecture diagram rendering

- **Documentation**: Auto-updates on doc changes
  - Renders PlantUML diagrams to PNG
  - Validates markdown links
  - Generates API documentation

- **Release Pipeline**: Triggered on version tags
  - Publishes to PyPI automatically
  - Creates GitHub releases with changelog
  - Includes rendered architecture diagrams

### Local Development Commands

```bash
make all             # Run complete pipeline (format, lint, test, docs, build)
make ci-local        # Run full CI simulation locally
make validate-workflows # Validate GitHub Actions syntax
make render-diagrams # Render architecture diagrams
make docs           # Generate all documentation
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Related Projects

- [GitHub's repository export tools](https://docs.github.com/en/repositories)
- [Tree command](https://tree.mama.indstate.edu/) for directory visualization
- [Sourcegraph](https://sourcegraph.com/) for code search and navigation
- [DocToc](https://github.com/thlorenz/doctoc) for table of contents generation

## Changelog

### v0.1.0 (Current)
- Initial release
- Core repository scanning functionality
- Markdown export with syntax highlighting
- Multiple output options (file, clipboard, stdout)
- Smart filtering with .gitignore integration
- Cross-platform support
- Comprehensive test suite
- Architecture documentation