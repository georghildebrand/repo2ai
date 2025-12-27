# Repo2AI

[![CI/CD Pipeline](https://github.com/georghildebrand/repo2ai/actions/workflows/ci.yml/badge.svg)](https://github.com/georghildebrand/repo2ai/actions/workflows/ci.yml)
[![Documentation](https://github.com/georghildebrand/repo2ai/actions/workflows/docs.yml/badge.svg)](https://github.com/georghildebrand/repo2ai/actions/workflows/docs.yml)
[![PyPI](https://img.shields.io/pypi/v/repo2ai.svg)](https://pypi.org/project/repo2ai/)

Export Git repositories to structured Markdown with **AI Chat Integration**. Perfect for code analysis, documentation, and getting AI assistance with your projects.

## Quick Start

```bash
pip install repo2ai

# Basic export to stdout
repo2ai .

# Copy to clipboard and open ChatGPT
repo2ai . --open-chat chatgpt

# Open Claude with a specific prompt
repo2ai . --open-chat claude --prompt "Analyze this codebase and suggest improvements"
```

## Features

- **Smart Repository Scanning** - Respects .gitignore, filters binary files, handles large codebases
- **AI Chat Integration** - Automatic browser integration with ChatGPT, Claude, and Gemini
- **Scope Filtering** - Focus on recent commits, uncommitted changes, or specific file patterns
- **Multiple Output Options** - File, clipboard, stdout, or combinations
- **Intelligent Filtering** - Configurable exclude patterns, file size limits, meta file handling
- **Language Detection** - Syntax highlighting for 25+ programming languages
- **Git Integration** - Only includes tracked files, respects Git ignore patterns

## Usage Examples

### Basic Export

```bash
repo2ai .                              # Export to stdout
repo2ai ./project --output docs.md     # Export to file
repo2ai . --clipboard                  # Copy to clipboard
repo2ai . -s                           # Short summary output
```

### AI Chat Integration

Open your repository directly in ChatGPT, Claude, or Gemini:

```bash
repo2ai . --open-chat chatgpt
repo2ai . --open-chat claude --prompt "Review for security vulnerabilities"
repo2ai . --open-chat gemini --prompt "Help me write documentation"
repo2ai . --chat-all --prompt "Explain this codebase"
repo2ai . --open-chat chatgpt --browser firefox
```

Supported services: `chatgpt`, `claude`, `gemini`

### PR Review Mode

Generate AI-friendly context for code reviews. This mode is specifically optimized to give an AI everything it needs to understand your changes: the **metadata**, the **actual diff**, and the **full content** of every changed file.

#### 1. Automatic Target Detection
If you don't specify a target branch, `repo2ai` automatically detects the best merge target:
- It checks for the remote default branch (`origin/HEAD`).
- It looks for common base branches (`main`, `master`, `develop`, `dev`).
- It uses the upstream tracking branch if it's different from your current branch.

```bash
# Auto-detect target (e.g., compares feature → main)
repo2ai . --pr-review
```

#### 2. Specific Targets
You can compare against any local or remote branch:

```bash
# PR context against specific local branch
repo2ai . --pr-review develop

# PR context against remote main branch
repo2ai . --pr-review origin/main

# PR review with Claude and a custom prompt
repo2ai . --pr-review --open-chat claude --prompt "Analyze for logic errors and performance"
```

#### 3. What's Included?
The generated Markdown report contains:
- **Summary:** Source and target branches, number of changed files, and total commit count.
- **Unified Diff:** The exact code changes for concise review.
- **Full File Context:** The complete current content of every changed file, enabling the AI to understand the impact of your changes on the surrounding code.

### Scope Filtering (Focused Analysis)

Limit export to specific files for focused AI analysis:

```bash
# Files from last 3 commits
repo2ai . --recent 3

# Only uncommitted changes
repo2ai . --uncommitted

# All Python files
repo2ai . --include "**/*.py"

# Combined: recent Python changes in src/
repo2ai . --recent 1 --include "src/**/*.py"

# Python files, excluding tests
repo2ai . --include "**/*.py" --exclude "**/test_*.py"
```

### Advanced Filtering

```bash
# Exclude sensitive files
repo2ai . --exclude "*.env" --exclude "secrets/*"

# Large repositories with size limits
repo2ai . --max-file-size 50000 --no-meta

# Custom exclude patterns
repo2ai . --exclude "*.log" --exclude "temp/*"
```

## CLI Options

Run `repo2ai --help` for complete options. Key flags:

| Option | Description |
|--------|-------------|
| `--output, -o` | Save to file |
| `--clipboard, -c` | Copy to clipboard |
| `--stdout, -s` | Output to stdout (default) |
| `--open-chat SERVICE` | Open AI service (chatgpt, claude, gemini) |
| `--chat-all` | Open all AI services |
| `--prompt TEXT` | Initial prompt for AI service |
| `--browser BROWSER` | Browser to use (chrome, firefox, safari, edge) |
| `--exclude PATTERN` | Exclude files matching pattern |
| `--no-meta` | Exclude README, LICENSE, etc. |
| `--max-file-size BYTES` | Maximum file size (default: 1MB) |
| `--recent N` | Only files from last N commits |
| `--uncommitted` | Only uncommitted changes |
| `--include PATTERN` | Only files matching glob pattern |
| `--pr-review [TARGET]` | Generate PR review context (diff + changed files) |
| `-v, --verbose` | Show detailed file lists |

## Contributing

```bash
git clone https://github.com/georghildebrand/repo2ai.git
cd repo2ai

# Setup
make setup         # Install dependencies + dev tools + pre-commit hooks
make install       # Install dependencies only

# Development
make format        # Auto-format code with Black
make lint          # Run flake8 + mypy
make test          # Run tests
make test-cov      # Run tests with coverage report

# Validation
make ci            # Run all checks (format-check, lint, test)
make check         # Same as ci
make install-system # Install built wheel into user site-packages (dev-only)
make uninstall-system # Remove system installation

# Release & Versioning
make version       # Show current project version
make release PART=patch  # Level release (patch, minor, or major)

# Build & Clean
make build         # Build wheel and sdist
make clean         # Remove build artifacts and caches
make distclean     # Deep clean including virtualenv

# Full pipeline
make all           # Run check + docs + build
```

### Releasing a New Version

The project uses automated GitHub Actions for releases. To trigger a new release:

1.  Run `make release PART=patch` (or `minor`/`major`).
2.  The command will automatically:
    - Run the quality gate (`make check`).
    - Bump the version in `pyproject.toml`.
    - Create a Git tag (e.g., `v0.2.1`).
    - Push the tag and code to GitHub.
3.  GitHub Actions will then build the package, publish it to PyPI, and create a GitHub Release with documentation.

See [Contributing Guidelines](docs/CONTRIBUTING.md) for details.

## Architecture

The tool follows a modular architecture: CLI parsing, repository scanning, scope filtering, PR review context generation, markdown generation, and output handling. See [Architecture Documentation](docs/ARCHITECTURE.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [GitHub Repository](https://github.com/georghildebrand/repo2ai)
- [PyPI Package](https://pypi.org/project/repo2ai/)
- [Architecture Diagrams](docs/architecture/)
