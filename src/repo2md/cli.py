"""
Command line interface for repo2md.
"""

import argparse
import sys
from pathlib import Path
from typing import List

from .core import scan_repository, generate_markdown
from .output import handle_output


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="repo2md",
        description="Export Git repository contents to structured Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  repo2md .                           # Export current directory to stdout
  repo2md ./project --output docs.md # Export to file
  repo2md . --clipboard               # Copy to clipboard
  repo2md . --stdout --clipboard      # Both stdout and clipboard
  repo2md . --exclude-meta-files      # Exclude README, LICENSE, etc.
  repo2md . --max-file-size 500000    # Limit file size to 500KB
        """,
    )

    # Positional argument
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to repository (default: current directory)",
    )

    # Output options
    output_group = parser.add_argument_group("output options")
    output_group.add_argument("--output", "-o", type=Path, help="Output file path")
    output_group.add_argument("--clipboard", "-c", action="store_true", help="Copy output to clipboard")
    output_group.add_argument(
        "--stdout",
        "-s",
        action="store_true",
        help="Output to stdout (default if no other output specified)",
    )

    # Filtering options
    filter_group = parser.add_argument_group("filtering options")
    filter_group.add_argument(
        "--ignore",
        action="append",
        help="Additional ignore patterns (can be used multiple times)",
    )
    filter_group.add_argument(
        "--exclude-meta-files",
        action="store_true",
        help="Exclude meta files like .gitignore, README, LICENSE",
    )
    filter_group.add_argument(
        "--max-file-size",
        type=int,
        default=1024 * 1024,  # 1MB
        help="Maximum file size in bytes (default: 1MB)",
    )

    # Include/exclude specific files
    filter_group.add_argument(
        "--include-meta",
        action="append",
        help="Include specific meta files (overrides --exclude-meta-files)",
    )
    filter_group.add_argument("--exclude-meta", action="append", help="Exclude specific meta files")

    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    # Check if repository path exists
    repo_path = Path(args.path).resolve()
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}", file=sys.stderr)
        sys.exit(1)

    if not repo_path.is_dir():
        print(f"Error: Repository path is not a directory: {repo_path}", file=sys.stderr)
        sys.exit(1)

    # Check max file size
    if args.max_file_size <= 0:
        print("Error: Max file size must be positive", file=sys.stderr)
        sys.exit(1)

    # Check output file parent directory
    if args.output:
        output_path = Path(args.output)
        if output_path.parent != Path(".") and not output_path.parent.exists():
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, IOError) as e:
                print(f"Error: Cannot create output directory: {e}", file=sys.stderr)
                sys.exit(1)


def process_ignore_patterns(args: argparse.Namespace) -> List[str]:
    """Process and combine ignore patterns from arguments."""
    patterns = []

    # Add patterns from --ignore
    if args.ignore:
        patterns.extend(args.ignore)

    # Add patterns from --exclude-meta
    if args.exclude_meta:
        patterns.extend(args.exclude_meta)

    # Handle --include-meta (remove from exclude patterns)
    if args.include_meta and args.exclude_meta_files:
        # This is a bit complex - we need to modify the exclude_meta_files behavior
        # For now, we'll handle this in the core module
        pass

    return patterns


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate arguments
    validate_arguments(args)

    # Process ignore patterns
    ignore_patterns = process_ignore_patterns(args)

    try:
        # Scan repository
        print("Scanning repository...", file=sys.stderr)
        scan_result = scan_repository(
            repo_path=Path(args.path),
            ignore_patterns=ignore_patterns,
            exclude_meta_files=args.exclude_meta_files,
            max_file_size=args.max_file_size,
        )

        # Generate markdown
        print("Generating markdown...", file=sys.stderr)
        markdown_content = generate_markdown(scan_result)

        # Handle output
        handle_output(
            content=markdown_content,
            output_file=args.output,
            to_clipboard=args.clipboard,
            to_stdout=args.stdout,
        )

        # Print summary
        file_count = len(scan_result.files)
        size_mb = scan_result.total_size / (1024 * 1024)
        print(f" Processed {file_count} files ({size_mb:.2f} MB)", file=sys.stderr)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
