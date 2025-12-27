"""PR review functionality for generating AI-friendly PR context."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Set


def get_target_branch(
    repo_root: Path,
    explicit_target: Optional[str] = None,
) -> str:
    """
    Determine the target branch for PR comparison.

    Priority:
    1. Explicit target if provided
    2. Remote default branch (origin/HEAD) if not current branch
    3. Common base branches (main, master, develop) if they exist and are not current
    4. Upstream tracking branch if it's different from current
    5. Fallback to 'main'

    Args:
        repo_root: Path to repository root
        explicit_target: User-specified target branch

    Returns:
        Target branch name
    """
    if explicit_target:
        return explicit_target

    current = get_current_branch(repo_root)

    # 1. Try to get remote default branch (origin/HEAD)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "origin/HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        target = result.stdout.strip()
        if target.startswith("origin/"):
            target = target[len("origin/") :]
        if target and target != current:
            # Check if this branch actually exists locally or remotely
            subprocess.run(
                ["git", "rev-parse", "--verify", target],
                cwd=repo_root,
                capture_output=True,
                check=True,
            )
            return target
    except subprocess.CalledProcessError:
        pass

    # 2. Check common base branches
    for candidate in ["main", "master", "develop", "dev"]:
        if candidate == current:
            continue
        try:
            # Check if candidate exists locally
            subprocess.run(
                ["git", "rev-parse", "--verify", candidate],
                cwd=repo_root,
                capture_output=True,
                check=True,
            )
            return candidate
        except subprocess.CalledProcessError:
            try:
                # Check if candidate exists on origin
                subprocess.run(
                    ["git", "rev-parse", "--verify", f"origin/{candidate}"],
                    cwd=repo_root,
                    capture_output=True,
                    check=True,
                )
                return candidate
            except subprocess.CalledProcessError:
                continue

    # 3. Try upstream tracking branch if it's different
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        upstream = result.stdout.strip()
        if upstream:
            # Extract branch name from origin/branch format
            if "/" in upstream:
                upstream_name = upstream.split("/", 1)[1]
            else:
                upstream_name = upstream

            if upstream_name != current:
                return upstream_name
    except subprocess.CalledProcessError:
        pass

    return "main"


def get_branch_diff(
    repo_root: Path,
    target_branch: str,
) -> str:
    """
    Get the diff between current branch and target branch.

    Args:
        repo_root: Path to repository root
        target_branch: Branch to compare against

    Returns:
        Unified diff string
    """
    try:
        result = subprocess.run(
            ["git", "diff", f"{target_branch}...HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_changed_files(
    repo_root: Path,
    target_branch: str,
) -> Set[Path]:
    """
    Get files changed between current branch and target branch.

    Args:
        repo_root: Path to repository root
        target_branch: Branch to compare against

    Returns:
        Set of absolute file paths that changed
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{target_branch}...HEAD"],
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
    except subprocess.CalledProcessError:
        return set()


@dataclass
class PRContext:
    """Context for PR review."""

    current_branch: str
    target_branch: str
    diff: str
    changed_files: Set[Path]
    commit_count: int


def get_current_branch(repo_root: Path) -> str:
    """Get the current branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def get_commit_count(repo_root: Path, target_branch: str) -> int:
    """Get number of commits between target and HEAD."""
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", f"{target_branch}...HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return 0


def get_pr_context(
    repo_root: Path,
    target_branch: Optional[str] = None,
) -> PRContext:
    """
    Get full PR context for review.

    Args:
        repo_root: Path to repository root
        target_branch: Optional explicit target branch

    Returns:
        PRContext with all review information
    """
    target = get_target_branch(repo_root, target_branch)
    current = get_current_branch(repo_root)

    return PRContext(
        current_branch=current,
        target_branch=target,
        diff=get_branch_diff(repo_root, target),
        changed_files=get_changed_files(repo_root, target),
        commit_count=get_commit_count(repo_root, target),
    )


def generate_pr_markdown(
    context: PRContext,
    file_contents: Dict[str, str],
) -> str:
    """
    Generate annotated markdown for PR review.

    Args:
        context: PR context with diff and metadata
        file_contents: Dict mapping relative paths to file contents

    Returns:
        Formatted markdown string
    """
    lines = []

    # Header
    lines.append(f"# PR Review: {context.current_branch} → {context.target_branch}")
    lines.append("")

    # Summary section
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Branch:** `{context.current_branch}`")
    lines.append(f"- **Target:** `{context.target_branch}`")
    lines.append(f"- **Changed files:** {len(context.changed_files)}")
    lines.append(f"- **Commits:** {context.commit_count}")
    lines.append("")

    # Diff section
    lines.append("## Diff")
    lines.append("")
    lines.append(
        "*This shows exactly what changed. Review for correctness, style, and potential issues.*"
    )
    lines.append("")
    lines.append("```diff")
    lines.append(context.diff)
    lines.append("```")
    lines.append("")

    # Changed files section
    lines.append("## Changed Files (Full Context)")
    lines.append("")
    lines.append(
        "*Full content of changed files for understanding the broader context.*"
    )
    lines.append("")

    for rel_path, content in sorted(file_contents.items()):
        lines.append(f"### {rel_path}")
        lines.append("")

        # Detect language from extension
        ext = Path(rel_path).suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
        }
        lang = lang_map.get(ext, "")

        lines.append(f"```{lang}")
        lines.append(content)
        lines.append("```")
        lines.append("")

    return "\n".join(lines)
