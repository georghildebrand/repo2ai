"""
Tests for CLI functionality.
"""

import tempfile

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import argparse

from repo2md.cli import (
    create_parser,
    validate_arguments,
    process_ignore_patterns,
)


class TestCLIParser(TestCase):
    """Test CLI argument parsing."""

    def setUp(self):
        """Set up test parser."""
        self.parser = create_parser()

    def test_basic_parsing(self):
        """Test basic argument parsing."""
        args = self.parser.parse_args(["."])
        self.assertEqual(args.path, ".")
        self.assertFalse(args.clipboard)
        self.assertFalse(args.stdout)
        self.assertIsNone(args.output)

    def test_output_options(self):
        """Test output option parsing."""
        args = self.parser.parse_args(["--output", "test.md", "--clipboard", "."])
        self.assertEqual(args.output, Path("test.md"))
        self.assertTrue(args.clipboard)
        self.assertFalse(args.stdout)

    def test_filtering_options(self):
        """Test filtering option parsing."""
        args = self.parser.parse_args(
            [
                "--ignore",
                "*.tmp",
                "--ignore",
                "*.log",
                "--exclude-meta-files",
                "--max-file-size",
                "500000",
                ".",
            ]
        )
        self.assertEqual(args.ignore, ["*.tmp", "*.log"])
        self.assertTrue(args.exclude_meta_files)
        self.assertEqual(args.max_file_size, 500000)

    def test_help_message(self):
        """Test that help message is properly formatted."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--help"])


class TestArgumentValidation(TestCase):
    """Test argument validation."""

    def setUp(self):
        """Set up test directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_valid_directory(self):
        """Test validation of valid directory."""
        args = argparse.Namespace(path=str(self.test_path), max_file_size=1024, output=None)

        # Should not raise exception
        validate_arguments(args)

    def test_nonexistent_directory(self):
        """Test validation of non-existent directory."""
        args = argparse.Namespace(path="/nonexistent/path", max_file_size=1024, output=None)

        with self.assertRaises(SystemExit):
            validate_arguments(args)

    def test_file_instead_of_directory(self):
        """Test validation when path is file instead of directory."""
        test_file = self.test_path / "test.txt"
        test_file.write_text("test")

        args = argparse.Namespace(path=str(test_file), max_file_size=1024, output=None)

        with self.assertRaises(SystemExit):
            validate_arguments(args)

    def test_invalid_max_file_size(self):
        """Test validation of invalid max file size."""
        args = argparse.Namespace(path=str(self.test_path), max_file_size=0, output=None)

        with self.assertRaises(SystemExit):
            validate_arguments(args)


class TestIgnorePatterns(TestCase):
    """Test ignore pattern processing."""

    def test_process_ignore_patterns(self):
        """Test processing ignore patterns."""
        args = argparse.Namespace(
            ignore=["*.tmp", "*.log"],
            exclude_meta=["README.md"],
            include_meta=None,
            exclude_meta_files=False,
        )

        patterns = process_ignore_patterns(args)
        expected = ["*.tmp", "*.log", "README.md"]
        self.assertEqual(patterns, expected)

    def test_no_ignore_patterns(self):
        """Test when no ignore patterns are specified."""
        args = argparse.Namespace(ignore=None, exclude_meta=None, include_meta=None, exclude_meta_files=False)

        patterns = process_ignore_patterns(args)
        self.assertEqual(patterns, [])


class TestCLIIntegration(TestCase):
    """Test CLI integration."""

    def setUp(self):
        """Set up test repository."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

        # Create test files
        (self.repo_path / "test.py").write_text('print("Hello")')
        (self.repo_path / "README.md").write_text("# Test Repository")

    def tearDown(self):
        """Clean up test repository."""
        import shutil

        shutil.rmtree(self.temp_dir)

    @patch("repo2md.cli.scan_repository")
    @patch("repo2md.cli.generate_markdown")
    @patch("repo2md.cli.handle_output")
    def test_main_function(self, mock_output, mock_generate, mock_scan):
        """Test main function execution."""
        from repo2md.cli import main
        from repo2md.core import ScanResult, RepoFile

        # Mock scan result
        mock_file = RepoFile(
            path=self.repo_path / "test.py",
            content='print("Hello")',
            size=15,
            language="python",
        )
        mock_scan_result = ScanResult(files=[mock_file], repo_root=self.repo_path, total_size=15)

        mock_scan.return_value = mock_scan_result
        mock_generate.return_value = "# Test Markdown"

        # Test with mocked arguments
        test_args = ["repo2md", str(self.repo_path), "--stdout"]

        with patch("sys.argv", test_args):
            main()

        # Verify mocks were called
        mock_scan.assert_called_once()
        mock_generate.assert_called_once_with(mock_scan_result)
        mock_output.assert_called_once()


if __name__ == "__main__":
    import unittest

    unittest.main()
