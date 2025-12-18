# Architecture

repo2ai follows a clean, modular architecture with clear separation of concerns.

## System Overview

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Developer │───▶│  repo2ai CLI │───▶│ AI Services │
└─────────────┘    └──────────────┘    └─────────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │ Git Repository│
                  └──────────────┘
```

## Core Modules

```
src/repo2ai/
├── cli.py      # Entry point, argument parsing, orchestration
├── core.py     # Repository scanning, filtering, markdown generation
├── scope.py    # Scope filtering (recent commits, uncommitted, glob patterns)
├── output.py   # File/clipboard/stdout output handling
└── browser.py  # AI chat integration (ChatGPT, Claude, Gemini)
```

### Module Responsibilities

- **CLI Module** (`cli.py`): Command-line interface with argument parsing and validation. Orchestrates the data flow between other modules.

- **Core Module** (`core.py`): Repository scanning using `git ls-files`, binary file detection, filtering logic, and Markdown generation. Contains key data structures:
  - `RepoFile`: NamedTuple holding path, content, size, language
  - `ScanResult`: NamedTuple with files list, repo_root, total_size, ignored/included files

- **Scope Module** (`scope.py`): Scope filtering for focused exports. Provides three filtering strategies:
  - Git commit-based: Files changed in recent N commits (`--recent`)
  - Uncommitted changes: Staged, unstaged, and untracked files (`--uncommitted`)
  - Glob patterns: File matching via glob patterns (`--include`)
  Contains:
  - `ScopeConfig`: Dataclass for scope configuration
  - Helper functions for each filtering strategy

- **Output Module** (`output.py`): Handles file writing, clipboard integration via pyperclip, and stdout handling.

- **Browser Module** (`browser.py`): AI chat integration and browser automation for ChatGPT, Claude, and Gemini.

## Data Flow

```
CLI parses args → Scope determines file whitelist (optional) → Core scans repo → Core generates markdown → Output handles destinations → Browser opens AI services (optional)
```

## Default Filtering Behavior

- Respects `.gitignore` via `git ls-files`
- Skips binary files (null byte detection)
- Default 1MB file size limit
- Excludes: `.git/`, `__pycache__/`, `node_modules/`, `.venv/`, `.env*`

## Architecture Diagrams

The project includes comprehensive C4 model diagrams in `/docs/architecture/`:

- **System Context**: High-level system interactions
- **Container Diagram**: Internal module architecture
- **Component Diagram**: Detailed component relationships
- **Development Workflow**: Development and CI/CD processes

Generate diagrams with: `make docs`
