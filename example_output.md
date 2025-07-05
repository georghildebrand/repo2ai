# Repo2Markdown

## Repository Summary

- **Files:** 3
- **Total Size:** 0.01 MB
- **Repository Root:** `/Users/georg.hildebrand/workspace/github.com/Repo2Markdown`

## File Structure

### Root Directory

- .gitignore
- LICENSE
- README.md

## File Contents

### .gitignore

**Size:** 4688 bytes

```
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[codz]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py.cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
#   For a library or package, you might want to ignore these files since the code is
#   intended to run in multiple environments; otherwise, check them in:
# .python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or not
#   install all needed dependencies.
#Pipfile.lock

# UV
#   Similar to Pipfile.lock, it is generally recommended to include uv.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
#uv.lock

# poetry
#   Similar to Pipfile.lock, it is generally recommended to include poetry.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
#   https://python-poetry.org/docs/basic-usage/#commit-your-poetrylock-file-to-version-control
#poetry.lock
#poetry.toml

# pdm
#   Similar to Pipfile.lock, it is generally recommended to include pdm.lock in version control.
#   pdm recommends including project-wide configuration in pdm.toml, but excluding .pdm-python.
#   https://pdm-project.org/en/latest/usage/project/#working-with-version-control
#pdm.lock
#pdm.toml
.pdm-python
.pdm-build/

# pixi
#   Similar to Pipfile.lock, it is generally recommended to include pixi.lock in version control.
#pixi.lock
#   Pixi creates a virtual environment in the .pixi directory, just like venv module creates one
#   in the .venv directory. It is recommended not to include this directory in version control.
.pixi

# PEP 582; used by e.g. github.com/David-OConnor/pyflow and github.com/pdm-project/pdm
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.envrc
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# PyCharm
#  JetBrains specific template is maintained in a separate JetBrains.gitignore that can
#  be found at https://github.com/github/gitignore/blob/main/Global/JetBrains.gitignore
#  and can be added to the global gitignore or merged into this file.  For a more nuclear
#  option (not recommended) you can uncomment the following to ignore the entire idea folder.
#.idea/

# Abstra
# Abstra is an AI-powered process automation framework.
# Ignore directories containing user credentials, local state, and settings.
# Learn more at https://abstra.io/docs
.abstra/

# Visual Studio Code
#  Visual Studio Code specific template is maintained in a separate VisualStudioCode.gitignore 
#  that can be found at https://github.com/github/gitignore/blob/main/Global/VisualStudioCode.gitignore
#  and can be added to the global gitignore or merged into this file. However, if you prefer, 
#  you could uncomment the following to ignore the entire vscode folder
# .vscode/

# Ruff stuff:
.ruff_cache/

# PyPI configuration file
.pypirc

# Cursor
#  Cursor is an AI-powered code editor. `.cursorignore` specifies files/directories to
#  exclude from AI features like autocomplete and code analysis. Recommended for sensitive data
#  refer to https://docs.cursor.com/context/ignore-files
.cursorignore
.cursorindexingignore

# Marimo
marimo/_static/
marimo/_lsp/
__marimo__/

```

### LICENSE

**Size:** 1068 bytes

```
MIT License

Copyright (c) 2025 ghildebrand

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

```

### README.md

**Size:** 4864 bytes
**Language:** markdown

```markdown
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

The tool follows a modular design:

- **Core Module**: Repository scanning, filtering, and Markdown generation
- **CLI Module**: Command-line interface and argument handling  
- **Output Module**: File, clipboard, and stdout output handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run `make all-checks` to ensure quality
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Related Projects

- [GitHub's repository export tools](https://docs.github.com/en/repositories)
- [Tree command](https://tree.mama.indstate.edu/) for directory visualization
- [Sourcegraph](https://sourcegraph.com/) for code search and navigation
```
