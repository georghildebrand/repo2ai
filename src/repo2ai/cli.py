"""
Command line interface for repo2ai with browser automation.
"""

import argparse
import sys
from pathlib import Path
from typing import List

from .core import scan_repository, generate_markdown
from .output import handle_output
from .browser import open_ai_chat


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="repo2ai",
        description="Export Git repository contents to structured Markdown and optionally open AI chat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  repo2ai .                                    # Export current directory to stdout
  repo2ai ./project --output docs.md          # Export to file
  repo2ai . --clipboard                       # Copy to clipboard
  repo2ai . --open-chat chatgpt               # Copy to clipboard and open ChatGPT
  repo2ai . --open-chat claude --prompt "Analyze this code"  # Open Claude with prompt
  repo2ai . --chat-all --prompt "Review this" # Try all AI services
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
    output_group.add_argument(
        "--clipboard", "-c", action="store_true", help="Copy output to clipboard"
    )
    output_group.add_argument(
        "--stdout",
        "-s",
        action="store_true",
        help="Output to stdout (default if no other output specified)",
    )

    # AI Chat options
    chat_group = parser.add_argument_group("AI chat options")
    chat_group.add_argument(
        "--open-chat",
        choices=["chatgpt", "claude", "gemini"],
        help="Open AI chat service with repo content",
    )
    chat_group.add_argument(
        "--chat-all",
        action="store_true",
        help="Try to open all available AI services",
    )
    chat_group.add_argument(
        "--prompt",
        help="Initial prompt to send with the repo content",
    )
    chat_group.add_argument(
        "--browser",
        default="default",
        help="Browser to use (default, chrome, firefox, safari, edge)",
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
    filter_group.add_argument(
        "--exclude-meta", action="append", help="Exclude specific meta files"
    )

    # Debugging options
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show lists of all files included and all files ignored (output to stderr)",
    )

    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    # Check if repository path exists
    repo_path = Path(args.path).resolve()
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}", file=sys.stderr)
        sys.exit(1)

    if not repo_path.is_dir():
        print(
            f"Error: Repository path is not a directory: {repo_path}", file=sys.stderr
        )
        sys.exit(1)

    # Check max file size
    if args.max_file_size <= 0:
        print("Error: Max file size must be positive", file=sys.stderr)
        sys.exit(1)

    # Validate chat options
    if args.prompt and not (args.open_chat or args.chat_all):
        print(
            "Warning: --prompt specified but no chat service selected. Use --open-chat or --chat-all",
            file=sys.stderr,
        )

    if (args.open_chat or args.chat_all) and not args.clipboard:
        print("Info: Enabling clipboard mode for AI chat integration", file=sys.stderr)
        args.clipboard = True

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
            verbose=args.verbose,
        )

        # Print verbose report if requested
        if args.verbose:
            print("=== Verbose File Report ===", file=sys.stderr)
            print("Included files:", file=sys.stderr)
            for p in scan_result.included_files:
                print(f"  {p}", file=sys.stderr)
            print("\nIgnored files:", file=sys.stderr)
            for p in scan_result.ignored_files:
                print(f"  {p}", file=sys.stderr)
            print("===========================", file=sys.stderr)

        # Generate markdown
        print("Generating markdown...", file=sys.stderr)
        markdown_content = generate_markdown(scan_result)

        # Handle output
        handle_output(
            content=markdown_content,
            output_file=args.output,
            to_clipboard=args.clipboard,
            to_stdout=args.stdout,
            prompt=(
                args.prompt if (args.open_chat or args.chat_all) else None
            ),  # Nur bei AI-Chat
        )

        # Open AI chat if requested
        if args.open_chat or args.chat_all:
            print("Opening AI chat...", file=sys.stderr)

            services = []
            if args.chat_all:
                services = ["chatgpt", "claude", "gemini"]
            else:
                services = [args.open_chat]

            success = open_ai_chat(
                services=services,
                prompt=args.prompt,
                browser=args.browser,
                verbose=args.verbose,
            )

            if not success:
                print("Warning: Could not open any AI chat service", file=sys.stderr)

        # Print summary
        file_count = len(scan_result.files)
        size_mb = scan_result.total_size / (1024 * 1024)
        print(f"✓ Processed {file_count} files ({size_mb:.2f} MB)", file=sys.stderr)

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
