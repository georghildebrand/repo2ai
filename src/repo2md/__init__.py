"""
Repo2md: Export Git repository contents to structured Markdown files.
"""

__version__ = "0.1.0"
__author__ = "Georg Hildebrand"
__email__ = "noreply@github.com"

from .core import RepoFile, ScanResult, scan_repository, generate_markdown
from .output import handle_output

__all__ = [
    "RepoFile",
    "ScanResult",
    "scan_repository",
    "generate_markdown",
    "handle_output",
]
