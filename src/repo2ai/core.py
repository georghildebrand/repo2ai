"""
Core functionality for repository scanning and markdown generation.
"""

import os
import fnmatch
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, NamedTuple, Set

if TYPE_CHECKING:
    from .scope import ScopeConfig

# TODO: insert logging and configure propper logger output


class RepoFile(NamedTuple):
    """Represents a file in the repository."""

    path: Path
    content: str
    size: int
    language: Optional[str]


class ScanResult(NamedTuple):
    """Result of repository scanning."""

    files: List[RepoFile]
    repo_root: Path
    total_size: int
    ignored_files: List[Path]
    included_files: List[Path]


def _get_language_from_extension(file_path: Path) -> Optional[str]:
    """Determine programming language from file extension."""
    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".php": "php",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
        ".kt": "kotlin",
        ".swift": "swift",
        ".scala": "scala",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "zsh",
        ".fish": "fish",
        ".ps1": "powershell",
        ".sql": "sql",
        ".json": "json",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "ini",
        ".conf": "ini",
        ".md": "markdown",
        ".txt": "text",
        ".log": "text",
        ".dockerfile": "dockerfile",
        ".gitignore": "gitignore",
        ".gitattributes": "gitattributes",
    }

    # Check for special files first (override extension-based detection)
    name = file_path.name.lower()
    if name == "dockerfile":
        return "dockerfile"
    elif name == "makefile":
        return "makefile"
    elif name.startswith("readme"):
        return "markdown"

    # Then check extension mapping
    suffix = file_path.suffix.lower()
    if suffix in extension_map:
        return extension_map[suffix]

    return None


def _parse_gitignore(gitignore_path: Path) -> List[str]:
    """Parse .gitignore file and return list of patterns."""
    patterns: List[str] = []

    if not gitignore_path.exists():
        return patterns

    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    patterns.append(line)
    except (IOError, UnicodeDecodeError):
        # If we can't read the file, skip it
        pass

    return patterns


def _should_ignore_file(
    file_path: Path, repo_root: Path, ignore_patterns: List[str]
) -> bool:
    """Check if file should be ignored based on patterns."""
    relative_path = file_path.relative_to(repo_root)
    relative_path_str = str(relative_path)

    for pattern in ignore_patterns:
        # Handle directory patterns
        if pattern.endswith("/"):
            # Check if file is inside this directory
            pattern_no_slash = pattern[:-1]
            if (
                fnmatch.fnmatch(relative_path_str, f"{pattern_no_slash}/*")
                or fnmatch.fnmatch(relative_path_str, f"*/{pattern_no_slash}/*")
                or relative_path_str.startswith(f"{pattern_no_slash}/")
            ):
                return True
        else:
            # Check against full path and filename
            if fnmatch.fnmatch(relative_path_str, pattern) or fnmatch.fnmatch(
                file_path.name, pattern
            ):
                return True

    return False


def _get_git_files(repo_root: Path) -> Set[Path]:
    """Get list of files tracked by Git."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )

        git_files = set()
        for line in result.stdout.strip().split("\n"):
            if line:
                git_files.add(repo_root / line)

        return git_files
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If git is not available or not a git repo, return empty set
        # TODO: log this
        return set()


def _is_binary_file(file_path: Path) -> bool:
    """Check if file is binary by reading first few bytes."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except (IOError, OSError):
        return True


def scan_repository(
    repo_path: Path,
    ignore_patterns: Optional[List[str]] = None,
    exclude_meta_files: bool = False,
    max_file_size: int = 1024 * 1024,  # 1MB
    verbose: bool = False,
    scope_config: Optional["ScopeConfig"] = None,
) -> ScanResult:
    """
    Scan repository and return filtered files.

    Args:
        repo_path: Path to repository root
        ignore_patterns: Additional patterns to ignore
        exclude_meta_files: Whether to exclude meta files like .gitignore, README
        max_file_size: Maximum file size in bytes
        verbose: Whether to track ignored and included files for reporting
        scope_config: Optional scope configuration for filtering files

    Returns:
        ScanResult with filtered files and optional verbose tracking
    """
    repo_root = Path(repo_path).resolve()

    if not repo_root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_root}")

    # Get scope whitelist if configured
    scope_whitelist: Optional[Set[Path]] = None
    if scope_config:
        from .scope import get_scoped_files

        scope_whitelist = get_scoped_files(repo_root, scope_config)

    # Get patterns from .gitignore
    gitignore_patterns = _parse_gitignore(repo_root / ".gitignore")

    # Combine with additional patterns
    all_patterns = gitignore_patterns + (ignore_patterns or [])

    # Add default patterns
    default_patterns = [
        ".git/*",
        ".git/**/*",
        "__pycache__/*",
        "__pycache__/**/*",
        "*.pyc",
        "*.pyo",
        ".DS_Store",
        "Thumbs.db",
        "*.log",
        "*.tmp",
        "*.temp",
        "node_modules/*",
        "node_modules/**/*",
        ".venv/*",
        ".venv/**/*",
        "venv/*",
        "venv/**/*",
        ".env",
        ".env.*",
    ]

    # Add meta file patterns if requested
    if exclude_meta_files:
        meta_patterns = [
            ".gitignore",
            ".gitattributes",
            "README*",
            "readme*",
            "LICENSE*",
            "license*",
            "CHANGELOG*",
            "changelog*",
            "CONTRIBUTING*",
            "contributing*",
            ".github/*",
            ".github/**/*",
        ]
        all_patterns.extend(meta_patterns)

    all_patterns.extend(default_patterns)

    # Get Git-tracked files if available
    git_files = _get_git_files(repo_root)

    files = []
    total_size = 0
    ignored_files: List[Path] = []
    included_files: List[Path] = []

    # Walk through directory
    for root, dirs, filenames in os.walk(repo_root):
        root_path = Path(root)

        # Skip directories that match ignore patterns
        dirs[:] = [
            d
            for d in dirs
            if not _should_ignore_file(root_path / d, repo_root, all_patterns)
        ]

        for filename in filenames:
            file_path = root_path / filename

            # Skip if file matches ignore patterns
            if _should_ignore_file(file_path, repo_root, all_patterns):
                if verbose:
                    ignored_files.append(file_path)
                continue

            # If we have Git files, only include tracked files
            if git_files and file_path not in git_files:
                if verbose:
                    ignored_files.append(file_path)
                continue

            # If scope whitelist exists, only include whitelisted files
            if scope_whitelist is not None and file_path not in scope_whitelist:
                if verbose:
                    ignored_files.append(file_path)
                continue

            # Check file size
            try:
                file_size = file_path.stat().st_size
                if file_size > max_file_size:
                    if verbose:
                        ignored_files.append(file_path)
                    continue
            except (OSError, IOError):
                if verbose:
                    ignored_files.append(file_path)
                continue

            # Skip binary files
            if _is_binary_file(file_path):
                if verbose:
                    ignored_files.append(file_path)
                continue

            # Read file content
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except (IOError, UnicodeDecodeError):
                # Skip files we can't read
                if verbose:
                    ignored_files.append(file_path)
                continue

            # Determine language
            language = _get_language_from_extension(file_path)

            repo_file = RepoFile(
                path=file_path, content=content, size=file_size, language=language
            )

            files.append(repo_file)
            total_size += file_size
            if verbose:
                included_files.append(file_path)

    return ScanResult(
        files=files,
        repo_root=repo_root,
        total_size=total_size,
        ignored_files=ignored_files,
        included_files=included_files,
    )


def generate_markdown(scan_result: ScanResult) -> str:
    """
    Generate Markdown from scan result.

    Args:
        scan_result: Result from scan_repository

    Returns:
        Generated Markdown content
    """
    lines = []

    # Header
    repo_name = scan_result.repo_root.name
    lines.append(f"# {repo_name}")
    lines.append("")

    # Summary
    file_count = len(scan_result.files)
    size_mb = scan_result.total_size / (1024 * 1024)
    lines.append("## Repository Summary")
    lines.append("")
    lines.append(f"- **Files:** {file_count}")
    lines.append(f"- **Total Size:** {size_mb:.2f} MB")
    lines.append(f"- **Repository Root:** `{scan_result.repo_root}`")
    lines.append("")

    # File structure
    lines.append("## File Structure")
    lines.append("")

    # Group files by directory
    dirs: dict[Path, list[str]] = {}
    for file in scan_result.files:
        relative_path = file.path.relative_to(scan_result.repo_root)
        dir_path = relative_path.parent

        if dir_path not in dirs:
            dirs[dir_path] = []
        dirs[dir_path].append(relative_path.name)

    # Sort directories
    sorted_dirs = sorted(dirs.keys())

    for dir_path in sorted_dirs:
        if str(dir_path) == ".":
            lines.append("### Root Directory")
        else:
            lines.append(f"### {dir_path}/")
        lines.append("")

        for filename in sorted(dirs[dir_path]):
            lines.append(f"- {filename}")
        lines.append("")

    # File contents
    lines.append("## File Contents")
    lines.append("")

    # Sort files by path
    sorted_files = sorted(scan_result.files, key=lambda f: f.path)

    for file in sorted_files:
        relative_path = file.path.relative_to(scan_result.repo_root)
        lines.append(f"### {relative_path}")
        lines.append("")

        # Add file info
        lines.append(f"**Size:** {file.size} bytes")
        if file.language:
            lines.append(f"**Language:** {file.language}")
        lines.append("")

        # Add content in code block
        if file.language:
            lines.append(f"```{file.language}")
        else:
            lines.append("```")
        lines.append(file.content)
        lines.append("```")
        lines.append("")

    return "\n".join(lines)
