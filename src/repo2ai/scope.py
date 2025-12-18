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
        # Use git log to get files changed in last N commits
        # This approach handles repos with fewer commits than N
        result = subprocess.run(
            ["git", "log", "--name-only", "--pretty=format:", f"-{num_commits}"],
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
