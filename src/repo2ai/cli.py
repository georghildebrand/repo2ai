"""
Command line interface for repo2ai with browser automation.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .core import scan_repository, generate_markdown
from .output import handle_output
from .browser import open_ai_chat
from .scope import ScopeConfig
from .pr import get_pr_context, generate_pr_markdown


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
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

PR review (generate context for AI code review):
  repo2ai . --pr-review                       # PR context against main/upstream
  repo2ai . --pr-review develop               # PR context against develop branch
  repo2ai . --pr-review --open-chat claude    # PR review with Claude

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
        "--exclude",
        action="append",
        metavar="PATTERN",
        help="Exclude files matching pattern (can be used multiple times)",
    )
    filter_group.add_argument(
        "--no-meta",
        action="store_true",
        help="Exclude meta files (.gitignore, README, LICENSE, CHANGELOG, etc.)",
    )
    filter_group.add_argument(
        "--max-file-size",
        type=int,
        default=1024 * 1024,  # 1MB
        help="Maximum file size in bytes (default: 1MB)",
    )

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
    scope_group.add_argument(
        "--pr-review",
        nargs="?",
        const="auto",
        metavar="TARGET",
        help="Generate PR review context (diff + changed files). TARGET defaults to main or upstream.",
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


def process_exclude_patterns(args: argparse.Namespace) -> List[str]:
    """Process and combine exclude patterns from arguments."""
    patterns = []

    if args.exclude:
        patterns.extend(args.exclude)

    return patterns


def build_scope_config(args: argparse.Namespace) -> Optional[ScopeConfig]:
    """Build ScopeConfig from CLI arguments."""
    if not args.recent and not args.uncommitted and not args.include:
        return None

    return ScopeConfig(
        recent=args.recent,
        uncommitted=args.uncommitted,
        include_patterns=args.include or [],
    )


def handle_pr_review(args: argparse.Namespace, repo_path: Path) -> str:
    """Handle PR review mode and return markdown content."""
    target = None if args.pr_review == "auto" else args.pr_review

    print("Generating PR review context...", file=sys.stderr)

    # Get PR context
    context = get_pr_context(repo_path, target)

    print(
        f"  Branch: {context.current_branch} → {context.target_branch}", file=sys.stderr
    )
    print(f"  Changed files: {len(context.changed_files)}", file=sys.stderr)
    print(f"  Commits: {context.commit_count}", file=sys.stderr)

    # Read file contents
    file_contents = {}
    for file_path in context.changed_files:
        try:
            rel_path = file_path.relative_to(repo_path)
            content = file_path.read_text(encoding="utf-8", errors="replace")
            file_contents[str(rel_path)] = content
        except Exception:
            pass  # Skip files that can't be read

    return generate_pr_markdown(context, file_contents)


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate arguments
    validate_arguments(args)

    # Process exclude patterns
    ignore_patterns = process_exclude_patterns(args)
    scope_config = build_scope_config(args)

    try:
        repo_path = Path(args.path).resolve()

        # PR review mode
        if args.pr_review:
            # Enable clipboard by default for PR review
            if not args.clipboard and not args.output and not args.stdout:
                args.clipboard = True
                print("Info: Enabling clipboard mode for PR review", file=sys.stderr)

            markdown_content = handle_pr_review(args, repo_path)

            # Handle output
            handle_output(
                content=markdown_content,
                output_file=args.output,
                to_clipboard=args.clipboard,
                to_stdout=args.stdout,
                prompt=args.prompt if (args.open_chat or args.chat_all) else None,
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
                    print(
                        "Warning: Could not open any AI chat service", file=sys.stderr
                    )

            print("✓ PR review context ready", file=sys.stderr)
            return
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

        # Scan repository
        print("Scanning repository...", file=sys.stderr)
        scan_result = scan_repository(
            repo_path=Path(args.path),
            ignore_patterns=ignore_patterns,
            exclude_meta_files=args.no_meta,
            max_file_size=args.max_file_size,
            verbose=args.verbose,
            scope_config=scope_config,
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
