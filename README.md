# Repo2Markdown

A minimal Python CLI tool that exports Git repository contents to structured Markdown files. Perfect for creating comprehensive repository documentation, code reviews, or feeding codebases to AI tools.

## Features

- **Git Integration**: Automatically scans Git-tracked files using `git ls-files`
- **Smart Filtering**: Respects `.gitignore` patterns and excludes binary files
- **Language Detection**: Automatically detects 25+ programming languages for syntax highlighting
- **Multiple Output Options**: File, clipboard, or stdout (combinable)
- **Configurable Filtering**: Custom ignore patterns, file size limits, meta file handling
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### From PyPI (when published)
```bash
pip install repo-to-markdown
```

### From Source
```bash
git clone https://github.com/georghildebrand/Repo2Markdown.git
cd Repo2Markdown
poetry install
```

## Quick Start

```bash
# Export current directory to stdout
repo-to-md .

# Export to a file
repo-to-md . --output my-repo.md

# Copy to clipboard
repo-to-md . --clipboard

# Exclude README, LICENSE, etc.
repo-to-md . --exclude-meta-files

# Combine outputs
repo-to-md . --output docs.md --clipboard
```

## Usage

```
repo-to-md [PATH] [OPTIONS]

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
repo-to-md .

# Export specific directory
repo-to-md ./my-project
```

### Output Options
```bash
# Save to file
repo-to-md . --output repository-export.md

# Copy to clipboard for pasting elsewhere
repo-to-md . --clipboard

# Both file and clipboard
repo-to-md . --output backup.md --clipboard
```

### Filtering
```bash
# Exclude meta files (README, LICENSE, etc.)
repo-to-md . --exclude-meta-files

# Custom ignore patterns
repo-to-md . --ignore "*.log" --ignore "temp/*"

# Limit file size (500KB max)
repo-to-md . --max-file-size 500000

# Include only specific files, ignore others
repo-to-md . --exclude-meta-files --include-meta README.md
```

## Output Format

The generated Markdown includes:

1. **Repository Summary**: File count, total size, root path
2. **File Structure**: Directory tree with file listings
3. **File Contents**: Each file with syntax highlighting

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
poetry run pytest

# Format code
poetry run black .

# Type checking
poetry run mypy src/

# Use Makefile for common tasks
make test          # Run tests
make lint          # Run linting
make format        # Format code
make all-checks    # Run all quality checks
make render-diagrams # Render PlantUML diagrams
make docs          # Generate all documentation
make all           # Run everything (format, lint, test, docs, build)
```

## Supported Languages

The tool automatically detects and provides syntax highlighting for:

**Programming Languages:** Python, JavaScript, TypeScript, Java, C/C++, C#, Go, Rust, PHP, Ruby, Swift, Kotlin, Scala

**Web Technologies:** HTML, CSS, SCSS/Sass, JSX, TSX

**Data/Config:** JSON, YAML, TOML, XML, SQL

**Scripts/Shell:** Bash, Zsh, Fish, PowerShell

**Documentation:** Markdown, Text

**Special Files:** Dockerfile, Makefile, .gitignore

## Requirements

- Python 3.8+
- Git (for repository scanning)
- pyperclip (for clipboard functionality)

## Architecture

The tool follows a modular design based on C4 architecture model:

### System Overview
- **Core Module**: Repository scanning, filtering, and Markdown generation
- **CLI Module**: Command-line interface and argument handling  
- **Output Module**: File, clipboard, and stdout output handling

### Architecture Diagrams

The system architecture is documented using C4 diagrams:

1. **[System Context](docs/architecture/c4/01-system-context.puml)** - High-level system interactions
2. **[Container Diagram](docs/architecture/c4/02-container-diagram.puml)** - Internal system structure  
3. **[Component Diagram](docs/architecture/c4/03-component-diagram.puml)** - Detailed component breakdown

> **Viewing Diagrams**: Use the [PlantUML VS Code extension](https://marketplace.visualstudio.com/items?itemName=jebbs.plantuml) or [online PlantUML server](http://www.plantuml.com/plantuml/uml/) to render the diagrams.

### Rendering Diagrams Locally

If you have PlantUML installed:

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run `make all-checks` to ensure quality
5. Submit a pull request

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