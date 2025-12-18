# Scoped Filtering Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add scope-limiting options and streamline CLI filtering for focused AI analysis.

**Architecture:** New filtering module (`scope.py`) handles git-based and glob-based scope filtering. CLI is streamlined: `--ignore` → `--exclude`, meta options consolidated to `--no-meta`. Three scope modes: `--recent N`, `--uncommitted`, `--include PATTERN`.

**Tech Stack:** Python subprocess for git commands, glob for patterns, existing argparse CLI structure.

**Breaking Changes:** This is a beta (0.1.1) release. Old options `--ignore`, `--exclude-meta-files`, `--include-meta`, `--exclude-meta` are replaced.

---

## Task 1: Rename --ignore to --exclude in CLI

**Files:**
- Modify: `src/repo2ai/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Update test to expect --exclude**

In `tests/test_cli.py`, find tests using `--ignore` and update to `--exclude`:

```python
# Change from:
args = parser.parse_args([".", "--ignore", "*.log"])
self.assertEqual(args.ignore, ["*.log"])

# Change to:
args = parser.parse_args([".", "--exclude", "*.log"])
self.assertEqual(args.exclude, ["*.log"])
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_cli.py -k "ignore" -v`
Expected: FAIL with AttributeError (args.exclude doesn't exist)

**Step 3: Update CLI argument**

In `src/repo2ai/cli.py`, change:

```python
# From:
filter_group.add_argument(
    "--ignore",
    action="append",
    help="Additional ignore patterns (can be used multiple times)",
)

# To:
filter_group.add_argument(
    "--exclude",
    action="append",
    metavar="PATTERN",
    help="Exclude files matching pattern (can be used multiple times)",
)
```

**Step 4: Update process_ignore_patterns function**

```python
def process_exclude_patterns(args: argparse.Namespace) -> List[str]:
    """Process and combine exclude patterns from arguments."""
    patterns = []

    if args.exclude:
        patterns.extend(args.exclude)

    return patterns
```

**Step 5: Update main() to use new function name**

Change `process_ignore_patterns(args)` to `process_exclude_patterns(args)`.

**Step 6: Run tests to verify they pass**

Run: `poetry run pytest tests/test_cli.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add src/repo2ai/cli.py tests/test_cli.py
git commit -m "refactor(cli): rename --ignore to --exclude

BREAKING CHANGE: --ignore is now --exclude for consistency
with the new --include option."
```

---

## Task 2: Consolidate Meta File Options to --no-meta

**Files:**
- Modify: `src/repo2ai/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Update tests for --no-meta**

In `tests/test_cli.py`, update meta file tests:

```python
# Change from:
args = parser.parse_args([".", "--exclude-meta-files"])
self.assertTrue(args.exclude_meta_files)

# Change to:
args = parser.parse_args([".", "--no-meta"])
self.assertTrue(args.no_meta)
```

Remove any tests for `--include-meta` and `--exclude-meta`.

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_cli.py -k "meta" -v`
Expected: FAIL

**Step 3: Replace three meta options with single --no-meta**

In `src/repo2ai/cli.py`, remove these three arguments:

```python
# REMOVE these:
filter_group.add_argument(
    "--exclude-meta-files",
    action="store_true",
    help="Exclude meta files like .gitignore, README, LICENSE",
)
filter_group.add_argument(
    "--include-meta",
    action="append",
    help="Include specific meta files (overrides --exclude-meta-files)",
)
filter_group.add_argument(
    "--exclude-meta", action="append", help="Exclude specific meta files"
)
```

Replace with:

```python
filter_group.add_argument(
    "--no-meta",
    action="store_true",
    help="Exclude meta files (.gitignore, README, LICENSE, CHANGELOG, etc.)",
)
```

**Step 4: Update main() to use args.no_meta**

Change `exclude_meta_files=args.exclude_meta_files` to `exclude_meta_files=args.no_meta`.

**Step 5: Update process_exclude_patterns to remove exclude_meta handling**

```python
def process_exclude_patterns(args: argparse.Namespace) -> List[str]:
    """Process and combine exclude patterns from arguments."""
    patterns = []

    if args.exclude:
        patterns.extend(args.exclude)

    return patterns
```

**Step 6: Run tests to verify they pass**

Run: `poetry run pytest tests/test_cli.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add src/repo2ai/cli.py tests/test_cli.py
git commit -m "refactor(cli): consolidate meta options to --no-meta

BREAKING CHANGE: --exclude-meta-files, --include-meta, --exclude-meta
are replaced by single --no-meta flag. Use --include/--exclude patterns
for fine-grained control."
```

---

## Task 3: Add Scope Module with Git Commit Filtering

**Files:**
- Create: `src/repo2ai/scope.py`
- Create: `tests/test_scope.py`

**Step 1: Write the failing test for getting files from recent commits**

Create `tests/test_scope.py`:

```python
"""
Tests for scope filtering functionality.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase

from repo2ai.scope import get_files_from_recent_commits


class TestGitCommitScope(TestCase):
    """Test git commit-based scope filtering."""

    def setUp(self):
        """Create a temporary git repository with commits."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=self.repo_root,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=self.repo_root,
            capture_output=True,
        )

        # Create initial file and commit
        (self.repo_root / "old_file.py").write_text("# old")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.repo_root,
            capture_output=True,
        )

        # Create recent file and commit
        (self.repo_root / "recent_file.py").write_text("# recent")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Recent commit"],
            cwd=self.repo_root,
            capture_output=True,
        )

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_get_files_from_last_commit(self):
        """Test getting files changed in last N commits."""
        files = get_files_from_recent_commits(self.repo_root, num_commits=1)

        self.assertEqual(len(files), 1)
        self.assertIn(self.repo_root / "recent_file.py", files)
        self.assertNotIn(self.repo_root / "old_file.py", files)

    def test_get_files_from_multiple_commits(self):
        """Test getting files from multiple recent commits."""
        files = get_files_from_recent_commits(self.repo_root, num_commits=2)

        self.assertEqual(len(files), 2)
        self.assertIn(self.repo_root / "recent_file.py", files)
        self.assertIn(self.repo_root / "old_file.py", files)

    def test_non_git_repo_returns_empty(self):
        """Test that non-git repos return empty set."""
        with tempfile.TemporaryDirectory() as non_git_dir:
            files = get_files_from_recent_commits(Path(non_git_dir), num_commits=1)
            self.assertEqual(files, set())
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_scope.py::TestGitCommitScope::test_get_files_from_last_commit -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'repo2ai.scope'"

**Step 3: Write minimal implementation**

Create `src/repo2ai/scope.py`:

```python
"""
Scope filtering functionality for repository exports.

Provides filtering by:
- Recent git commits (--recent N)
- Uncommitted changes (--uncommitted)
- Glob patterns (--include PATTERN)
"""

import subprocess
from pathlib import Path
from typing import Set


def get_files_from_recent_commits(
    repo_root: Path,
    num_commits: int = 1,
) -> Set[Path]:
    """
    Get files changed in the most recent N commits.

    Args:
        repo_root: Path to repository root
        num_commits: Number of recent commits to include

    Returns:
        Set of absolute file paths changed in recent commits
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"HEAD~{num_commits}", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )

        files = set()
        for line in result.stdout.strip().split("\n"):
            if line:
                file_path = repo_root / line
                if file_path.exists():
                    files.add(file_path)

        return files
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
```

**Step 4: Run test to verify it passes**

Run: `poetry run pytest tests/test_scope.py::TestGitCommitScope -v`
Expected: PASS (all 3 tests)

**Step 5: Commit**

```bash
git add src/repo2ai/scope.py tests/test_scope.py
git commit -m "feat(scope): add git commit-based file filtering

Add get_files_from_recent_commits() to filter repository exports
to only files changed in the last N commits."
```

---

## Task 4: Add Uncommitted Changes Scope

**Files:**
- Modify: `src/repo2ai/scope.py`
- Modify: `tests/test_scope.py`

**Step 1: Write the failing test for uncommitted changes**

Add to `tests/test_scope.py`:

```python
from repo2ai.scope import get_files_from_recent_commits, get_uncommitted_files


class TestUncommittedScope(TestCase):
    """Test uncommitted changes scope filtering."""

    def setUp(self):
        """Create a temporary git repository with uncommitted changes."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=self.repo_root,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=self.repo_root,
            capture_output=True,
        )

        # Create committed file
        (self.repo_root / "committed.py").write_text("# committed")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.repo_root,
            capture_output=True,
        )

        # Create uncommitted changes
        (self.repo_root / "committed.py").write_text("# modified")
        (self.repo_root / "new_file.py").write_text("# new")

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_get_uncommitted_modified_files(self):
        """Test getting files with uncommitted modifications."""
        files = get_uncommitted_files(self.repo_root)

        self.assertIn(self.repo_root / "committed.py", files)

    def test_get_uncommitted_new_files(self):
        """Test getting untracked files."""
        files = get_uncommitted_files(self.repo_root)

        self.assertIn(self.repo_root / "new_file.py", files)

    def test_staged_files_included(self):
        """Test that staged files are included."""
        subprocess.run(
            ["git", "add", "new_file.py"], cwd=self.repo_root, capture_output=True
        )

        files = get_uncommitted_files(self.repo_root)

        self.assertIn(self.repo_root / "new_file.py", files)
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_scope.py::TestUncommittedScope::test_get_uncommitted_modified_files -v`
Expected: FAIL with "ImportError: cannot import name 'get_uncommitted_files'"

**Step 3: Write minimal implementation**

Add to `src/repo2ai/scope.py`:

```python
def get_uncommitted_files(repo_root: Path) -> Set[Path]:
    """
    Get files with uncommitted changes (staged, unstaged, and untracked).

    Args:
        repo_root: Path to repository root

    Returns:
        Set of absolute file paths with uncommitted changes
    """
    files = set()

    try:
        # Get modified/deleted files (unstaged)
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.strip().split("\n"):
            if line:
                file_path = repo_root / line
                if file_path.exists():
                    files.add(file_path)

        # Get staged files
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.strip().split("\n"):
            if line:
                file_path = repo_root / line
                if file_path.exists():
                    files.add(file_path)

        # Get untracked files
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.strip().split("\n"):
            if line:
                file_path = repo_root / line
                if file_path.exists():
                    files.add(file_path)

        return files
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
```

**Step 4: Run test to verify it passes**

Run: `poetry run pytest tests/test_scope.py::TestUncommittedScope -v`
Expected: PASS (all 3 tests)

**Step 5: Commit**

```bash
git add src/repo2ai/scope.py tests/test_scope.py
git commit -m "feat(scope): add uncommitted changes filtering

Add get_uncommitted_files() to filter repository exports
to only files with uncommitted changes (staged, unstaged, untracked)."
```

---

## Task 5: Add Glob Pattern Include Scope

**Files:**
- Modify: `src/repo2ai/scope.py`
- Modify: `tests/test_scope.py`

**Step 1: Write the failing test for glob include patterns**

Add to `tests/test_scope.py`:

```python
from repo2ai.scope import (
    get_files_from_recent_commits,
    get_uncommitted_files,
    get_files_from_glob_patterns,
)


class TestGlobScope(TestCase):
    """Test glob pattern scope filtering."""

    def setUp(self):
        """Create a temporary directory with files."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)

        # Create directory structure
        (self.repo_root / "src").mkdir()
        (self.repo_root / "src" / "module").mkdir()
        (self.repo_root / "tests").mkdir()

        # Create files
        (self.repo_root / "src" / "main.py").write_text("# main")
        (self.repo_root / "src" / "module" / "core.py").write_text("# core")
        (self.repo_root / "src" / "module" / "utils.py").write_text("# utils")
        (self.repo_root / "tests" / "test_main.py").write_text("# test")
        (self.repo_root / "README.md").write_text("# readme")

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_recursive_glob_pattern(self):
        """Test **/*.py recursive glob pattern."""
        files = get_files_from_glob_patterns(self.repo_root, ["**/*.py"])

        self.assertEqual(len(files), 4)
        self.assertIn(self.repo_root / "src" / "main.py", files)
        self.assertIn(self.repo_root / "src" / "module" / "core.py", files)
        self.assertIn(self.repo_root / "tests" / "test_main.py", files)

    def test_directory_scoped_pattern(self):
        """Test src/**/*.py directory-scoped pattern."""
        files = get_files_from_glob_patterns(self.repo_root, ["src/**/*.py"])

        self.assertEqual(len(files), 3)
        self.assertIn(self.repo_root / "src" / "main.py", files)
        self.assertIn(self.repo_root / "src" / "module" / "core.py", files)
        self.assertNotIn(self.repo_root / "tests" / "test_main.py", files)

    def test_multiple_glob_patterns(self):
        """Test multiple glob patterns combined."""
        files = get_files_from_glob_patterns(
            self.repo_root, ["src/module/*.py", "*.md"]
        )

        self.assertEqual(len(files), 3)
        self.assertIn(self.repo_root / "src" / "module" / "core.py", files)
        self.assertIn(self.repo_root / "src" / "module" / "utils.py", files)
        self.assertIn(self.repo_root / "README.md", files)
        self.assertNotIn(self.repo_root / "src" / "main.py", files)

    def test_single_directory_pattern(self):
        """Test tests/* single-level pattern."""
        files = get_files_from_glob_patterns(self.repo_root, ["tests/*"])

        self.assertEqual(len(files), 1)
        self.assertIn(self.repo_root / "tests" / "test_main.py", files)
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_scope.py::TestGlobScope::test_recursive_glob_pattern -v`
Expected: FAIL with "ImportError: cannot import name 'get_files_from_glob_patterns'"

**Step 3: Write minimal implementation**

Add to `src/repo2ai/scope.py`:

```python
import glob as glob_module


def get_files_from_glob_patterns(
    repo_root: Path,
    patterns: list[str],
) -> Set[Path]:
    """
    Get files matching glob patterns.

    Supports:
    - **/*.py - all Python files recursively
    - src/**/*.py - Python files under src/
    - *.md - markdown files in root
    - tests/* - files directly in tests/

    Args:
        repo_root: Path to repository root
        patterns: List of glob patterns

    Returns:
        Set of absolute file paths matching any pattern
    """
    files = set()

    for pattern in patterns:
        full_pattern = str(repo_root / pattern)
        for match in glob_module.glob(full_pattern, recursive=True):
            file_path = Path(match)
            if file_path.is_file():
                files.add(file_path)

    return files
```

**Step 4: Run test to verify it passes**

Run: `poetry run pytest tests/test_scope.py::TestGlobScope -v`
Expected: PASS (all 4 tests)

**Step 5: Commit**

```bash
git add src/repo2ai/scope.py tests/test_scope.py
git commit -m "feat(scope): add glob pattern include filtering

Add get_files_from_glob_patterns() to filter repository exports
to only files matching specified glob patterns like **/*.py."
```

---

## Task 6: Add Combined Scope Helper with ScopeConfig

**Files:**
- Modify: `src/repo2ai/scope.py`
- Modify: `tests/test_scope.py`

**Step 1: Write the failing test for combined scope**

Add to `tests/test_scope.py`:

```python
from repo2ai.scope import (
    get_files_from_recent_commits,
    get_uncommitted_files,
    get_files_from_glob_patterns,
    get_scoped_files,
    ScopeConfig,
)


class TestCombinedScope(TestCase):
    """Test combined scope filtering."""

    def test_scope_config_defaults(self):
        """Test ScopeConfig has sensible defaults."""
        config = ScopeConfig()

        self.assertIsNone(config.recent)
        self.assertFalse(config.uncommitted)
        self.assertEqual(config.include_patterns, [])

    def test_get_scoped_files_no_scope_returns_none(self):
        """Test that no scope returns None (include all files)."""
        config = ScopeConfig()

        result = get_scoped_files(Path("/fake"), config)

        self.assertIsNone(result)

    def test_get_scoped_files_with_include_patterns(self):
        """Test scope with include patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "a.py").write_text("# a")
            (repo_root / "b.py").write_text("# b")
            (repo_root / "c.txt").write_text("# c")

            config = ScopeConfig(include_patterns=["*.py"])

            result = get_scoped_files(repo_root, config)

            self.assertIsNotNone(result)
            self.assertEqual(len(result), 2)
            self.assertIn(repo_root / "a.py", result)
            self.assertIn(repo_root / "b.py", result)
            self.assertNotIn(repo_root / "c.txt", result)

    def test_is_scoped_property(self):
        """Test is_scoped property."""
        self.assertFalse(ScopeConfig().is_scoped)
        self.assertTrue(ScopeConfig(recent=1).is_scoped)
        self.assertTrue(ScopeConfig(uncommitted=True).is_scoped)
        self.assertTrue(ScopeConfig(include_patterns=["*.py"]).is_scoped)
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_scope.py::TestCombinedScope::test_scope_config_defaults -v`
Expected: FAIL with "ImportError: cannot import name 'ScopeConfig'"

**Step 3: Write minimal implementation**

Update `src/repo2ai/scope.py` (full file):

```python
"""
Scope filtering functionality for repository exports.

Provides filtering by:
- Recent git commits (--recent N)
- Uncommitted changes (--uncommitted)
- Glob patterns (--include PATTERN)
"""

import glob as glob_module
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set


@dataclass
class ScopeConfig:
    """Configuration for scope filtering."""

    recent: Optional[int] = None
    uncommitted: bool = False
    include_patterns: List[str] = field(default_factory=list)

    @property
    def is_scoped(self) -> bool:
        """Check if any scope filtering is configured."""
        return bool(self.recent or self.uncommitted or self.include_patterns)


def get_files_from_recent_commits(
    repo_root: Path,
    num_commits: int = 1,
) -> Set[Path]:
    """
    Get files changed in the most recent N commits.

    Args:
        repo_root: Path to repository root
        num_commits: Number of recent commits to include

    Returns:
        Set of absolute file paths changed in recent commits
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"HEAD~{num_commits}", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )

        files = set()
        for line in result.stdout.strip().split("\n"):
            if line:
                file_path = repo_root / line
                if file_path.exists():
                    files.add(file_path)

        return files
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()


def get_uncommitted_files(repo_root: Path) -> Set[Path]:
    """
    Get files with uncommitted changes (staged, unstaged, and untracked).

    Args:
        repo_root: Path to repository root

    Returns:
        Set of absolute file paths with uncommitted changes
    """
    files = set()

    try:
        # Get modified/deleted files (unstaged)
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.strip().split("\n"):
            if line:
                file_path = repo_root / line
                if file_path.exists():
                    files.add(file_path)

        # Get staged files
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.strip().split("\n"):
            if line:
                file_path = repo_root / line
                if file_path.exists():
                    files.add(file_path)

        # Get untracked files
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.strip().split("\n"):
            if line:
                file_path = repo_root / line
                if file_path.exists():
                    files.add(file_path)

        return files
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()


def get_files_from_glob_patterns(
    repo_root: Path,
    patterns: List[str],
) -> Set[Path]:
    """
    Get files matching glob patterns.

    Supports:
    - **/*.py - all Python files recursively
    - src/**/*.py - Python files under src/
    - *.md - markdown files in root
    - tests/* - files directly in tests/

    Args:
        repo_root: Path to repository root
        patterns: List of glob patterns

    Returns:
        Set of absolute file paths matching any pattern
    """
    files = set()

    for pattern in patterns:
        full_pattern = str(repo_root / pattern)
        for match in glob_module.glob(full_pattern, recursive=True):
            file_path = Path(match)
            if file_path.is_file():
                files.add(file_path)

    return files


def get_scoped_files(
    repo_root: Path,
    config: ScopeConfig,
) -> Optional[Set[Path]]:
    """
    Get files matching scope configuration.

    Returns None if no scope is configured (meaning include all files).
    Returns a set of file paths if any scope option is set.

    Multiple scope options are combined with union (OR logic).

    Args:
        repo_root: Path to repository root
        config: Scope configuration

    Returns:
        Set of file paths to include, or None if no scope filtering
    """
    if not config.is_scoped:
        return None

    files: Set[Path] = set()

    if config.recent:
        files.update(get_files_from_recent_commits(repo_root, config.recent))

    if config.uncommitted:
        files.update(get_uncommitted_files(repo_root))

    if config.include_patterns:
        files.update(get_files_from_glob_patterns(repo_root, config.include_patterns))

    return files
```

**Step 4: Run test to verify it passes**

Run: `poetry run pytest tests/test_scope.py::TestCombinedScope -v`
Expected: PASS (all 4 tests)

**Step 5: Commit**

```bash
git add src/repo2ai/scope.py tests/test_scope.py
git commit -m "feat(scope): add ScopeConfig and combined scope helper

Add ScopeConfig dataclass with is_scoped property and get_scoped_files()
helper to combine multiple scope filters with union (OR) logic."
```

---

## Task 7: Export Scope Module from Package

**Files:**
- Modify: `src/repo2ai/__init__.py`

**Step 1: Read current __init__.py**

Run: `cat src/repo2ai/__init__.py`

**Step 2: Add scope exports**

Update `src/repo2ai/__init__.py` to include:

```python
from .scope import (
    ScopeConfig,
    get_scoped_files,
    get_files_from_recent_commits,
    get_uncommitted_files,
    get_files_from_glob_patterns,
)
```

**Step 3: Run all scope tests**

Run: `poetry run pytest tests/test_scope.py -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add src/repo2ai/__init__.py
git commit -m "feat(scope): export scope module from package"
```

---

## Task 8: Integrate Scope Filtering into Core Module

**Files:**
- Modify: `src/repo2ai/core.py`
- Modify: `tests/test_core.py`

**Step 1: Write the failing test for scoped scanning**

Add to `tests/test_core.py`:

```python
import shutil

from repo2ai.scope import ScopeConfig


class TestScopedScan(TestCase):
    """Test repository scanning with scope filtering."""

    def setUp(self):
        """Create a temporary directory with files."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)

        (self.repo_root / "included.py").write_text("# included")
        (self.repo_root / "excluded.py").write_text("# excluded")

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_scan_with_scope_whitelist(self):
        """Test scanning respects scope whitelist."""
        scope_config = ScopeConfig(include_patterns=["included.py"])

        result = scan_repository(
            self.repo_root,
            scope_config=scope_config,
        )

        file_names = [f.path.name for f in result.files]
        self.assertIn("included.py", file_names)
        self.assertNotIn("excluded.py", file_names)

    def test_scan_without_scope_includes_all(self):
        """Test scanning without scope includes all files."""
        result = scan_repository(self.repo_root)

        file_names = [f.path.name for f in result.files]
        self.assertIn("included.py", file_names)
        self.assertIn("excluded.py", file_names)
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_core.py::TestScopedScan::test_scan_with_scope_whitelist -v`
Expected: FAIL with "TypeError: scan_repository() got an unexpected keyword argument 'scope_config'"

**Step 3: Modify scan_repository to accept scope_config**

In `src/repo2ai/core.py`:

Add import at top:
```python
from typing import List, Optional, NamedTuple, Set

from .scope import ScopeConfig, get_scoped_files
```

Update function signature:
```python
def scan_repository(
    repo_path: Path,
    ignore_patterns: Optional[List[str]] = None,
    exclude_meta_files: bool = False,
    max_file_size: int = 1024 * 1024,
    verbose: bool = False,
    scope_config: Optional[ScopeConfig] = None,
) -> ScanResult:
```

After `repo_root` validation, add:
```python
    # Get scope whitelist if configured
    scope_whitelist: Optional[Set[Path]] = None
    if scope_config:
        scope_whitelist = get_scoped_files(repo_root, scope_config)
```

In the file processing loop, after the git files check (around line 283), add:
```python
            # If scope whitelist exists, only include whitelisted files
            if scope_whitelist is not None and file_path not in scope_whitelist:
                if verbose:
                    ignored_files.append(file_path)
                continue
```

**Step 4: Run test to verify it passes**

Run: `poetry run pytest tests/test_core.py::TestScopedScan -v`
Expected: PASS (both tests)

**Step 5: Run full test suite**

Run: `poetry run pytest tests/ -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/repo2ai/core.py tests/test_core.py
git commit -m "feat(core): integrate scope filtering into scan_repository

Add scope_config parameter to scan_repository() to support
filtering by recent commits, uncommitted changes, or glob patterns."
```

---

## Task 9: Add Scope CLI Arguments

**Files:**
- Modify: `src/repo2ai/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write the failing test for scope CLI arguments**

Add to `tests/test_cli.py`:

```python
class TestScopeArguments(TestCase):
    """Test scope filtering CLI arguments."""

    def test_recent_argument(self):
        """Test --recent argument."""
        parser = create_parser()
        args = parser.parse_args([".", "--recent", "3"])

        self.assertEqual(args.recent, 3)

    def test_uncommitted_argument(self):
        """Test --uncommitted argument."""
        parser = create_parser()
        args = parser.parse_args([".", "--uncommitted"])

        self.assertTrue(args.uncommitted)

    def test_include_argument(self):
        """Test --include argument."""
        parser = create_parser()
        args = parser.parse_args([".", "--include", "**/*.py", "--include", "*.md"])

        self.assertEqual(args.include, ["**/*.py", "*.md"])

    def test_scope_arguments_default_values(self):
        """Test scope arguments have correct defaults."""
        parser = create_parser()
        args = parser.parse_args(["."])

        self.assertIsNone(args.recent)
        self.assertFalse(args.uncommitted)
        self.assertIsNone(args.include)
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_cli.py::TestScopeArguments::test_recent_argument -v`
Expected: FAIL with "AttributeError: 'Namespace' object has no attribute 'recent'"

**Step 3: Add scope argument group to create_parser()**

In `src/repo2ai/cli.py`, add after the filter_group:

```python
    # Scope options (limit output for focused AI analysis)
    scope_group = parser.add_argument_group("scope options (limit output)")
    scope_group.add_argument(
        "--recent",
        type=int,
        metavar="N",
        help="Only include files changed in the last N commits",
    )
    scope_group.add_argument(
        "--uncommitted",
        action="store_true",
        help="Only include files with uncommitted changes",
    )
    scope_group.add_argument(
        "--include",
        action="append",
        metavar="PATTERN",
        help="Only include files matching glob pattern (e.g., **/*.py)",
    )
```

**Step 4: Run test to verify it passes**

Run: `poetry run pytest tests/test_cli.py::TestScopeArguments -v`
Expected: PASS (all 4 tests)

**Step 5: Commit**

```bash
git add src/repo2ai/cli.py tests/test_cli.py
git commit -m "feat(cli): add scope filtering arguments

Add --recent, --uncommitted, and --include arguments
for limiting repository export scope."
```

---

## Task 10: Wire Up Scope Arguments in Main Function

**Files:**
- Modify: `src/repo2ai/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write integration test**

Add to `tests/test_cli.py`:

```python
class TestScopeIntegration(TestCase):
    """Test scope arguments integration."""

    def test_build_scope_config_from_args(self):
        """Test ScopeConfig is created from CLI arguments."""
        from repo2ai.cli import build_scope_config
        from repo2ai.scope import ScopeConfig

        parser = create_parser()
        args = parser.parse_args([
            ".",
            "--recent", "2",
            "--uncommitted",
            "--include", "src/*.py",
        ])

        config = build_scope_config(args)

        self.assertIsInstance(config, ScopeConfig)
        self.assertEqual(config.recent, 2)
        self.assertTrue(config.uncommitted)
        self.assertEqual(config.include_patterns, ["src/*.py"])

    def test_build_scope_config_none_when_no_args(self):
        """Test ScopeConfig is None when no scope arguments."""
        from repo2ai.cli import build_scope_config

        parser = create_parser()
        args = parser.parse_args(["."])

        config = build_scope_config(args)

        self.assertIsNone(config)
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_cli.py::TestScopeIntegration::test_build_scope_config_from_args -v`
Expected: FAIL with "ImportError: cannot import name 'build_scope_config'"

**Step 3: Add build_scope_config and wire up in main()**

In `src/repo2ai/cli.py`:

Add import:
```python
from typing import List, Optional

from .scope import ScopeConfig
```

Add helper function:
```python
def build_scope_config(args: argparse.Namespace) -> Optional[ScopeConfig]:
    """Build ScopeConfig from CLI arguments."""
    if not args.recent and not args.uncommitted and not args.include:
        return None

    return ScopeConfig(
        recent=args.recent,
        uncommitted=args.uncommitted,
        include_patterns=args.include or [],
    )
```

Update main() to build and use scope_config:
```python
def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    validate_arguments(args)

    ignore_patterns = process_exclude_patterns(args)
    scope_config = build_scope_config(args)

    try:
        print("Scanning repository...", file=sys.stderr)
        scan_result = scan_repository(
            repo_path=Path(args.path),
            ignore_patterns=ignore_patterns,
            exclude_meta_files=args.no_meta,
            max_file_size=args.max_file_size,
            verbose=args.verbose,
            scope_config=scope_config,
        )
        # ... rest of main() unchanged
```

**Step 4: Run test to verify it passes**

Run: `poetry run pytest tests/test_cli.py::TestScopeIntegration -v`
Expected: PASS (both tests)

**Step 5: Run full test suite**

Run: `poetry run pytest tests/ -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/repo2ai/cli.py tests/test_cli.py
git commit -m "feat(cli): wire up scope arguments in main function

Add build_scope_config() helper and integrate scope filtering
into the main CLI workflow."
```

---

## Task 11: Update CLI Help and Examples

**Files:**
- Modify: `src/repo2ai/cli.py`

**Step 1: Update epilog with comprehensive examples**

Update epilog in create_parser():

```python
    parser = argparse.ArgumentParser(
        prog="repo2ai",
        description="Export Git repository contents to structured Markdown and optionally open AI chat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  repo2ai .                                    # Export current directory
  repo2ai ./project --output docs.md          # Export to file
  repo2ai . --clipboard                       # Copy to clipboard
  repo2ai . --open-chat claude --prompt "Review this code"

Scope filtering (reduce output for focused AI analysis):
  repo2ai . --recent 3                        # Files from last 3 commits
  repo2ai . --uncommitted                     # Files with uncommitted changes
  repo2ai . --include "**/*.py"               # All Python files
  repo2ai . --include "src/**" --exclude "*.test.py"  # src/ without tests
  repo2ai . --recent 1 --include "**/*.py"    # Recent Python changes

Pattern examples:
  **/*.py      All Python files recursively
  src/**/*.py  Python files under src/
  *.md         Markdown files in root only
  tests/*      Files directly in tests/ (not subdirs)
        """,
    )
```

**Step 2: Test help output**

Run: `poetry run repo2ai --help`
Expected: Help shows new options and examples

**Step 3: Commit**

```bash
git add src/repo2ai/cli.py
git commit -m "docs(cli): update help with scope filtering examples"
```

---

## Task 12: Add Verbose Output for Scope Filtering

**Files:**
- Modify: `src/repo2ai/cli.py`

**Step 1: Add scope info to verbose output**

In main(), after building scope_config and before scanning:

```python
        # Print scope info if verbose
        if args.verbose and scope_config and scope_config.is_scoped:
            print("=== Scope Filtering ===", file=sys.stderr)
            if scope_config.recent:
                print(f"  Recent commits: {scope_config.recent}", file=sys.stderr)
            if scope_config.uncommitted:
                print("  Uncommitted changes: Yes", file=sys.stderr)
            if scope_config.include_patterns:
                for pattern in scope_config.include_patterns:
                    print(f"  Include: {pattern}", file=sys.stderr)
            print("=======================", file=sys.stderr)
```

**Step 2: Test verbose output**

Run: `poetry run repo2ai . --recent 1 --include "**/*.py" -v 2>&1 | head -20`
Expected: Shows scope filtering info

**Step 3: Commit**

```bash
git add src/repo2ai/cli.py
git commit -m "feat(cli): add verbose output for scope filtering"
```

---

## Task 13: Run Final Validation

**Step 1: Run full test suite with coverage**

Run: `make test-cov`
Expected: All tests pass

**Step 2: Run linting**

Run: `make lint`
Expected: No errors

**Step 3: Run format check**

Run: `make format-check`
Expected: No issues (or run `make format`)

**Step 4: Run CI checks**

Run: `make ci`
Expected: All checks pass

**Step 5: Test CLI manually**

```bash
# Test --recent
poetry run repo2ai . --recent 1 -v

# Test --include
poetry run repo2ai . --include "**/*.py" -v

# Test --uncommitted
poetry run repo2ai . --uncommitted -v

# Test combined
poetry run repo2ai . --recent 2 --include "src/**" -v
```

**Step 6: Final commit if needed**

```bash
git add -A
git commit -m "chore: final cleanup and formatting"
```

---

## Summary

### Breaking Changes (Beta 0.1.1)

| Old | New |
|-----|-----|
| `--ignore PATTERN` | `--exclude PATTERN` |
| `--exclude-meta-files` | `--no-meta` |
| `--include-meta` | *(removed)* Use `--include` |
| `--exclude-meta` | *(removed)* Use `--exclude` |

### New Options

| Option | Description |
|--------|-------------|
| `--recent N` | Only files changed in last N commits |
| `--uncommitted` | Only files with uncommitted changes |
| `--include PATTERN` | Only files matching glob (repeatable) |

### Usage Examples

```bash
# Focused on recent work
repo2ai . --recent 3

# Only Python files
repo2ai . --include "**/*.py"

# Uncommitted changes only
repo2ai . --uncommitted

# Combined: recent Python in src/
repo2ai . --recent 1 --include "src/**/*.py"

# Exclude test files
repo2ai . --include "**/*.py" --exclude "**/test_*.py"
```

### New Module

`src/repo2ai/scope.py` with:
- `ScopeConfig` dataclass
- `get_files_from_recent_commits()`
- `get_uncommitted_files()`
- `get_files_from_glob_patterns()`
- `get_scoped_files()`

---

Plan complete and saved to `docs/plans/2025-12-17-scoped-filtering.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with `/superpowers:execute-plan`, batch execution with checkpoints

**Which approach?**
