"""
Repo2md: Export Git repository contents to structured Markdown files.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package not installed, fallback to a dev default
    __version__ = "0.0.0+dev"

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
