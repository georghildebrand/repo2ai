"""
Output handling for file, clipboard, and stdout.
"""

import sys
from pathlib import Path
from typing import Optional

try:
    import pyperclip

    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

# TODO: add logging


def handle_output(
    content: str,
    output_file: Optional[Path] = None,
    to_clipboard: bool = False,
    to_stdout: bool = False,
) -> None:
    """
    Handle output to file, clipboard, and/or stdout.

    Args:
        content: The content to output
        output_file: Path to output file (optional)
        to_clipboard: Whether to copy to clipboard
        to_stdout: Whether to output to stdout
    """
    # Default to stdout if no output options specified
    if not output_file and not to_clipboard and not to_stdout:
        to_stdout = True

    # Write to file
    if output_file:
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f" Markdown exported to: {output_file}", file=sys.stderr)
        except (IOError, OSError) as e:
            print(f" Error writing to file {output_file}: {e}", file=sys.stderr)
            sys.exit(1)

    # Copy to clipboard
    if to_clipboard:
        if not PYPERCLIP_AVAILABLE:
            print(
                " Error: pyperclip not available. Install with: pip install pyperclip",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            pyperclip.copy(content)
            print(" Markdown copied to clipboard", file=sys.stderr)
        except Exception as e:
            print(f" Error copying to clipboard: {e}", file=sys.stderr)
            sys.exit(1)

    # Output to stdout
    if to_stdout:
        print(content)


def get_default_output_filename(repo_path: Path) -> Path:
    """
    Get default output filename based on repository name.

    Args:
        repo_path: Path to repository

    Returns:
        Default output filename
    """
    repo_name = repo_path.name
    return Path(f"{repo_name}_export.md")
