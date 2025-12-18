"""Tests for PR review functionality."""

import subprocess
import tempfile
from pathlib import Path
import re
from unittest import TestCase

from repo2ai.pr import (
    get_target_branch,
    get_branch_diff,
    get_changed_files,
    PRContext,
    get_pr_context,
    generate_pr_markdown,
)


class TestTargetBranchDetection(TestCase):
    """Test target branch detection logic."""

    def setUp(self):
        """Create a temporary git repository."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)

        # Initialize git repo with main branch
        subprocess.run(
            ["git", "init", "-b", "main"], cwd=self.repo_root, capture_output=True
        )
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

        # Create initial commit on main
        (self.repo_root / "file.txt").write_text("initial")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.repo_root,
            capture_output=True,
        )

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_explicit_target_used(self):
        """Test that explicit target overrides detection."""
        result = get_target_branch(self.repo_root, explicit_target="develop")
        self.assertEqual(result, "develop")

    def test_fallback_to_main(self):
        """Test fallback to main when no upstream."""
        # Create feature branch without upstream
        subprocess.run(
            ["git", "checkout", "-b", "feature"],
            cwd=self.repo_root,
            capture_output=True,
        )

        result = get_target_branch(self.repo_root, explicit_target=None)
        self.assertEqual(result, "main")


class TestDiffGeneration(TestCase):
    """Test diff generation between branches."""

    def setUp(self):
        """Create a temporary git repository with branches."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)

        # Initialize git repo
        subprocess.run(
            ["git", "init", "-b", "main"], cwd=self.repo_root, capture_output=True
        )
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

        # Create initial commit on main
        (self.repo_root / "existing.py").write_text("# existing\n")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.repo_root,
            capture_output=True,
        )

        # Create feature branch with changes
        subprocess.run(
            ["git", "checkout", "-b", "feature"],
            cwd=self.repo_root,
            capture_output=True,
        )
        (self.repo_root / "existing.py").write_text("# existing\n# modified\n")
        (self.repo_root / "new_file.py").write_text("# new file\n")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Feature changes"],
            cwd=self.repo_root,
            capture_output=True,
        )

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_get_branch_diff(self):
        """Test getting diff between branches."""
        diff = get_branch_diff(self.repo_root, "main")

        self.assertIn("+# modified", diff)
        self.assertIn("new_file.py", diff)

    def test_diff_empty_when_same(self):
        """Test empty diff when branches are same."""
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=self.repo_root,
            capture_output=True,
        )

        diff = get_branch_diff(self.repo_root, "main")
        self.assertEqual(diff, "")


class TestChangedFiles(TestCase):
    """Test changed files detection."""

    def setUp(self):
        """Create a temporary git repository with branches."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)

        # Initialize git repo
        subprocess.run(
            ["git", "init", "-b", "main"], cwd=self.repo_root, capture_output=True
        )
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

        # Create initial commit on main
        (self.repo_root / "existing.py").write_text("# existing\n")
        (self.repo_root / "unchanged.py").write_text("# unchanged\n")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.repo_root,
            capture_output=True,
        )

        # Create feature branch with changes
        subprocess.run(
            ["git", "checkout", "-b", "feature"],
            cwd=self.repo_root,
            capture_output=True,
        )
        (self.repo_root / "existing.py").write_text("# existing\n# modified\n")
        (self.repo_root / "new_file.py").write_text("# new file\n")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Feature changes"],
            cwd=self.repo_root,
            capture_output=True,
        )

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_get_changed_files(self):
        """Test getting list of changed files."""
        files = get_changed_files(self.repo_root, "main")

        self.assertEqual(len(files), 2)
        self.assertIn(self.repo_root / "existing.py", files)
        self.assertIn(self.repo_root / "new_file.py", files)
        self.assertNotIn(self.repo_root / "unchanged.py", files)


class TestPRContext(TestCase):
    """Test PR context generation."""

    def setUp(self):
        """Create a temporary git repository with branches."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)

        # Initialize git repo
        subprocess.run(
            ["git", "init", "-b", "main"], cwd=self.repo_root, capture_output=True
        )
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

        # Create initial commit on main
        (self.repo_root / "file.py").write_text("# original\n")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.repo_root,
            capture_output=True,
        )

        # Create feature branch
        subprocess.run(
            ["git", "checkout", "-b", "my-feature"],
            cwd=self.repo_root,
            capture_output=True,
        )
        (self.repo_root / "file.py").write_text("# modified\n")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "My feature"],
            cwd=self.repo_root,
            capture_output=True,
        )

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_get_pr_context(self):
        """Test getting full PR context."""
        context = get_pr_context(self.repo_root, target_branch=None)

        self.assertEqual(context.current_branch, "my-feature")
        self.assertEqual(context.target_branch, "main")
        self.assertIn("+# modified", context.diff)
        self.assertEqual(len(context.changed_files), 1)


class TestPRMarkdown(TestCase):
    """Test PR markdown generation."""

    def test_generate_pr_markdown(self):
        """Test markdown generation from PR context."""
        context = PRContext(
            current_branch="feature-x",
            target_branch="main",
            diff="--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new",
            changed_files={Path("/repo/file.py")},
            commit_count=2,
        )

        # Mock file content
        markdown = generate_pr_markdown(
            context,
            file_contents={"file.py": "# new content"},
        )

        # Check structure
        self.assertIn("# PR Review: feature-x → main", markdown)
        self.assertIn("## Summary", markdown)
        self.assertTrue(re.search(r"Branch.*`feature-x`", markdown))
        self.assertTrue(re.search(r"Target.*`main`", markdown))
        self.assertTrue(re.search(r"Commits.*2", markdown))
        self.assertIn("## Diff", markdown)
        self.assertIn("```diff", markdown)
        self.assertIn("+new", markdown)
        self.assertIn("## Changed Files", markdown)
        self.assertIn("### file.py", markdown)
