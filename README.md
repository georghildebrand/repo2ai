# Repo2AI

[![CI/CD Pipeline](https://github.com/georghildebrand/repo2ai/actions/workflows/ci.yml/badge.svg)](https://github.com/georghildebrand/repo2ai/actions/workflows/ci.yml)
[![Documentation](https://github.com/georghildebrand/repo2ai/actions/workflows/docs.yml/badge.svg)](https://github.com/georghildebrand/repo2ai/actions/workflows/docs.yml)
[![Development Status](https://img.shields.io/badge/status-development-orange.svg)](https://github.com/georghildebrand/repo2ai)

Export Git repository contents to structured Markdown with **AI Chat Integration**. Perfect for code analysis, documentation, and getting AI assistance with your projects.

## 🚀 Quick Start

```bash
# Install from PyPI
pip install repo2ai

# Basic export
repo2ai .

# Copy to clipboard and open ChatGPT
repo2ai . --open-chat chatgpt

# Open Claude with a specific prompt
repo2ai . --open-chat claude --prompt "Please analyze this codebase and suggest improvements"

# Try all AI services with a prompt
repo2ai . --chat-all --prompt "Review this repository structure"
```

## ✨ Features

- **📁 Smart Repository Scanning** - Respects .gitignore, filters binary files, handles large codebases
- **🤖 AI Chat Integration** - Automatic browser integration with ChatGPT, Claude, and Gemini
- **📋 Multiple Output Options** - File, clipboard, stdout, or combinations
- **🎯 Intelligent Filtering** - Configurable ignore patterns, file size limits, meta file handling
- **🔍 Language Detection** - Syntax highlighting for 25+ programming languages
- **⚡ Git Integration** - Only includes tracked files, respects Git ignore patterns

## 🤖 AI Chat Integration

repo2ai now supports automatic browser integration with popular AI services, making it easy to share your repository with AI assistants for code analysis, review, and assistance.

### Quick Start with AI Chat

```bash
# Copy repo to clipboard and open ChatGPT
repo2ai . --open-chat chatgpt

# Open Claude with a specific prompt
repo2ai . --open-chat claude --prompt "Please analyze this codebase and suggest improvements"

# Try all AI services with a prompt
repo2ai . --chat-all --prompt "Review this repository structure"

# Use specific browser
repo2ai . --open-chat chatgpt --browser firefox
```

### AI Chat Options

```
--open-chat SERVICE       Open specific AI service (chatgpt, claude, gemini)
--chat-all                Try to open all available AI services
--prompt TEXT             Initial prompt to use with the AI service
--browser BROWSER         Browser to use (default, chrome, firefox, safari, edge)
```

### Supported AI Services

- **ChatGPT** (`chatgpt`) - OpenAI's ChatGPT at chat.openai.com
- **Claude** (`claude`) - Anthropic's Claude at claude.ai
- **Gemini** (`gemini`) - Google's Gemini at gemini.google.com

### How It Works

1. **Repository Export**: Scans and exports your repository to markdown
2. **Clipboard Copy**: Automatically copies the content to your clipboard
3. **Browser Launch**: Opens the specified AI service in a new browser tab
4. **Instructions**: Shows helpful instructions for pasting content and adding your prompt

## 📖 Usage Examples

### Basic Export
```bash
repo2ai .                                    # Export current directory to stdout
repo2ai ./project --output docs.md          # Export to file
repo2ai . --clipboard                       # Copy to clipboard
```

### AI Chat Integration
```bash
# Code Analysis
repo2ai . --open-chat claude --prompt "Analyze this code for potential security vulnerabilities"

# Architecture Review
repo2ai . --open-chat chatgpt --prompt "Review the architecture and suggest improvements"

# Documentation Help
repo2ai . --open-chat gemini --prompt "Help me write better documentation for this project"

# Quick Questions
repo2ai . --chat-all --prompt "Where are logs written in this application?"
```

### Advanced Filtering
```bash
# Exclude sensitive files when sharing with AI
repo2ai . --open-chat claude --ignore "*.env" --ignore "secrets/*" --prompt "Review this code"

# Large repositories with size limits
repo2ai . --max-file-size 50000 --exclude-meta-files

# Custom ignore patterns
repo2ai . --ignore "*.log" --ignore "temp/*" --ignore "*.tmp"
```

## 🛠️ Installation

> **Note**: This project is currently in development. No PyPI package is available yet.

### From Source (Current Method)
```bash
git clone https://github.com/georghildebrand/repo2ai.git
cd Repo2Markdown
make install

# Run with poetry
repo2ai --help
```

### Development Setup
```bash
git clone https://github.com/georghildebrand/repo2ai.git
cd Repo2Markdown
make setup  # Complete development environment
```

### Future PyPI Installation (Planned)
```bash
# Will be available after first release
pip install repo2ai
```

## 📋 CLI Options

### Basic Options
```
positional arguments:
  path                  Path to repository (default: current directory)

output options:
  --output, -o          Output file path
  --clipboard, -c       Copy output to clipboard
  --stdout, -s          Output to stdout (default if no other output specified)
```

### AI Chat Options
```
AI chat options:
  --open-chat           Open specific AI service (chatgpt, claude, gemini)
  --chat-all            Try to open all available AI services
  --prompt              Initial prompt to send with the repo content
  --browser             Browser to use (default, chrome, firefox, safari, edge)
```

### Filtering Options
```
filtering options:
  --ignore              Additional ignore patterns (can be used multiple times)
  --exclude-meta-files  Exclude meta files like .gitignore, README, LICENSE
  --max-file-size       Maximum file size in bytes (default: 1MB)
  --include-meta        Include specific meta files (overrides --exclude-meta-files)
  --exclude-meta        Exclude specific meta files
  -v, --verbose         Show lists of all files included and ignored
```

## 🏗️ Architecture

The project follows a clean, modular architecture with clear separation of concerns:

### System Overview
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Developer │───▶│  Repo2md CLI │───▶│ AI Services │
└─────────────┘    └──────────────┘    └─────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │ Git Repository│
                   └──────────────┘
```

### Core Modules

- **CLI Module**: Command-line interface with argument parsing and validation
- **Core Module**: Repository scanning, filtering, and Markdown generation
- **Output Module**: File writing, clipboard integration, stdout handling
- **Browser Module**: AI chat integration and browser automation

### Architecture Diagrams

The project includes comprehensive C4 model diagrams:

- **System Context**: High-level system interactions
- **Container Diagram**: Internal module architecture
- **Component Diagram**: Detailed component relationships
- **Development Workflow**: Development and CI/CD processes

Generate diagrams with: `make docs`

## 🔧 Development

### Prerequisites
- Python 3.11+
- Poetry for dependency management
- Make for task automation
- PlantUML for diagram generation (optional)

### Development Workflow

1. **Setup Development Environment**
   ```bash
   git clone https://github.com/georghildebrand/repo2ai.git
   cd Repo2Markdown
   make setup  # Install dependencies + dev tools
   ```

2. **Development Tasks**
   ```bash
   make format     # Format code with Black
   make lint       # Run linting (flake8 + mypy)
   make test       # Run tests
   make test-cov   # Run tests with coverage
   ```

3. **Quality Assurance**
   ```bash
   make ci         # Run all CI checks locally
   make all        # Complete pipeline (format + lint + test + docs + build)
   ```

4. **Documentation**
   ```bash
   make docs       # Render PlantUML diagrams
   ```

5. **Testing & Demo**
   ```bash
   make run        # Demo on current directory
   make demo       # Feature demonstration
   make run-chat   # Test AI integration
   ```

### Available Make Targets

| Target | Description |
|--------|-------------|
| `make setup` | Complete development environment setup |
| `make install` | Install dependencies only |
| `make format` | Format code with Black |
| `make lint` | Run linting (flake8 + mypy) |
| `make test` | Run tests |
| `make test-cov` | Run tests with coverage |
| `make docs` | Render PlantUML diagrams |
| `make ci` | Run CI checks locally |
| `make all` | Complete pipeline |
| `make clean` | Clean build artifacts |

### Code Quality Standards

- **Code Formatting**: Black with 180 character line length
- **Linting**: Flake8 for PEP8 compliance
- **Type Checking**: MyPy with strict settings
- **Testing**: Pytest with high coverage requirements
- **Documentation**: Comprehensive docstrings and architecture diagrams

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run quality checks: `make ci`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Contribution Guidelines

- Follow the existing code style (enforced by Black)
- Add tests for new functionality
- Update documentation for user-facing changes
- Ensure all CI checks pass
- Update architecture diagrams if adding new modules

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PlantUML** for architecture diagram generation
- **Poetry** for excellent dependency management
- **GitHub Actions** for robust CI/CD
- **AI Services** (OpenAI, Anthropic, Google) for making code analysis accessible

## 🔗 Links

- [GitHub Repository](https://github.com/georghildebrand/repo2ai)
- [Documentation](https://github.com/georghildebrand/repo2ai/tree/main/docs)
- [Architecture Diagrams](https://github.com/georghildebrand/repo2ai/tree/main/docs/images)
- [PyPI Package](https://pypi.org/project/repo2ai/)

