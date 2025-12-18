"""
Tests for scope filtering functionality.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase

from repo2ai.scope import (
    get_files_from_recent_commits,
    get_uncommitted_files,
    get_files_from_glob_patterns,
    get_scoped_files,
    ScopeConfig,
)


class TestGitCommitScope(TestCase):
    """Test git commit-based scope filtering."""

    def setUp(self):
        """Create a temporary git repository with commits."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.repo_root, capture_output=True)
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

        # Create initial file and commit
        (self.repo_root / "old_file.py").write_text("# old")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.repo_root,
            capture_output=True,
        )

        # Create recent file and commit
        (self.repo_root / "recent_file.py").write_text("# recent")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Recent commit"],
            cwd=self.repo_root,
            capture_output=True,
        )

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_get_files_from_last_commit(self):
        """Test getting files changed in last N commits."""
        files = get_files_from_recent_commits(self.repo_root, num_commits=1)

        self.assertEqual(len(files), 1)
        self.assertIn(self.repo_root / "recent_file.py", files)
        self.assertNotIn(self.repo_root / "old_file.py", files)

    def test_get_files_from_multiple_commits(self):
        """Test getting files from multiple recent commits."""
        files = get_files_from_recent_commits(self.repo_root, num_commits=2)

        self.assertEqual(len(files), 2)
        self.assertIn(self.repo_root / "recent_file.py", files)
        self.assertIn(self.repo_root / "old_file.py", files)

    def test_non_git_repo_returns_empty(self):
        """Test that non-git repos return empty set."""
        with tempfile.TemporaryDirectory() as non_git_dir:
            files = get_files_from_recent_commits(Path(non_git_dir), num_commits=1)
            self.assertEqual(files, set())


class TestUncommittedScope(TestCase):
    """Test uncommitted changes scope filtering."""

    def setUp(self):
        """Create a temporary git repository with uncommitted changes."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.repo_root, capture_output=True)
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

        # Create committed file
        (self.repo_root / "committed.py").write_text("# committed")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.repo_root,
            capture_output=True,
        )

        # Create uncommitted changes
        (self.repo_root / "committed.py").write_text("# modified")
        (self.repo_root / "new_file.py").write_text("# new")

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_get_uncommitted_modified_files(self):
        """Test getting files with uncommitted modifications."""
        files = get_uncommitted_files(self.repo_root)

        self.assertIn(self.repo_root / "committed.py", files)

    def test_get_uncommitted_new_files(self):
        """Test getting untracked files."""
        files = get_uncommitted_files(self.repo_root)

        self.assertIn(self.repo_root / "new_file.py", files)

    def test_staged_files_included(self):
        """Test that staged files are included."""
        subprocess.run(
            ["git", "add", "new_file.py"], cwd=self.repo_root, capture_output=True
        )

        files = get_uncommitted_files(self.repo_root)

        self.assertIn(self.repo_root / "new_file.py", files)


class TestGlobScope(TestCase):
    """Test glob pattern scope filtering."""

    def setUp(self):
        """Create a temporary directory with files."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)

        # Create directory structure
        (self.repo_root / "src").mkdir()
        (self.repo_root / "src" / "module").mkdir()
        (self.repo_root / "tests").mkdir()

        # Create files
        (self.repo_root / "src" / "main.py").write_text("# main")
        (self.repo_root / "src" / "module" / "core.py").write_text("# core")
        (self.repo_root / "src" / "module" / "utils.py").write_text("# utils")
        (self.repo_root / "tests" / "test_main.py").write_text("# test")
        (self.repo_root / "README.md").write_text("# readme")

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_recursive_glob_pattern(self):
        """Test **/*.py recursive glob pattern."""
        files = get_files_from_glob_patterns(self.repo_root, ["**/*.py"])

        self.assertEqual(len(files), 4)
        self.assertIn(self.repo_root / "src" / "main.py", files)
        self.assertIn(self.repo_root / "src" / "module" / "core.py", files)
        self.assertIn(self.repo_root / "tests" / "test_main.py", files)

    def test_directory_scoped_pattern(self):
        """Test src/**/*.py directory-scoped pattern."""
        files = get_files_from_glob_patterns(self.repo_root, ["src/**/*.py"])

        self.assertEqual(len(files), 3)
        self.assertIn(self.repo_root / "src" / "main.py", files)
        self.assertIn(self.repo_root / "src" / "module" / "core.py", files)
        self.assertNotIn(self.repo_root / "tests" / "test_main.py", files)

    def test_multiple_glob_patterns(self):
        """Test multiple glob patterns combined."""
        files = get_files_from_glob_patterns(
            self.repo_root, ["src/module/*.py", "*.md"]
        )

        self.assertEqual(len(files), 3)
        self.assertIn(self.repo_root / "src" / "module" / "core.py", files)
        self.assertIn(self.repo_root / "src" / "module" / "utils.py", files)
        self.assertIn(self.repo_root / "README.md", files)
        self.assertNotIn(self.repo_root / "src" / "main.py", files)

    def test_single_directory_pattern(self):
        """Test tests/* single-level pattern."""
        files = get_files_from_glob_patterns(self.repo_root, ["tests/*"])

        self.assertEqual(len(files), 1)
        self.assertIn(self.repo_root / "tests" / "test_main.py", files)


class TestCombinedScope(TestCase):
    """Test combined scope filtering."""

    def test_scope_config_defaults(self):
        """Test ScopeConfig has sensible defaults."""
        config = ScopeConfig()

        self.assertIsNone(config.recent)
        self.assertFalse(config.uncommitted)
        self.assertEqual(config.include_patterns, [])

    def test_get_scoped_files_no_scope_returns_none(self):
        """Test that no scope returns None (include all files)."""
        config = ScopeConfig()

        result = get_scoped_files(Path("/fake"), config)

        self.assertIsNone(result)

    def test_get_scoped_files_with_include_patterns(self):
        """Test scope with include patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "a.py").write_text("# a")
            (repo_root / "b.py").write_text("# b")
            (repo_root / "c.txt").write_text("# c")

            config = ScopeConfig(include_patterns=["*.py"])

            result = get_scoped_files(repo_root, config)

            self.assertIsNotNone(result)
            self.assertEqual(len(result), 2)
            self.assertIn(repo_root / "a.py", result)
            self.assertIn(repo_root / "b.py", result)
            self.assertNotIn(repo_root / "c.txt", result)

    def test_is_scoped_property(self):
        """Test is_scoped property."""
        self.assertFalse(ScopeConfig().is_scoped)
        self.assertTrue(ScopeConfig(recent=1).is_scoped)
        self.assertTrue(ScopeConfig(uncommitted=True).is_scoped)
        self.assertTrue(ScopeConfig(include_patterns=["*.py"]).is_scoped)
