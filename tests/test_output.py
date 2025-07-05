"""
Tests for output functionality.
"""

import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from io import StringIO

from repo_to_markdown.output import (
    handle_output,
    get_default_output_filename,
)


class TestOutputHandling(TestCase):
    """Test output handling functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_content = "# Test Markdown\n\nThis is a test."

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_file_output(self):
        """Test writing to file."""
        output_file = Path(self.temp_dir) / "test.md"

        with patch("sys.stderr", new_callable=StringIO):
            handle_output(
                content=self.test_content,
                output_file=output_file,
                to_clipboard=False,
                to_stdout=False,
            )

        # Check file was created with correct content
        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_text(), self.test_content)

    def test_stdout_output(self):
        """Test output to stdout."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.stderr", new_callable=StringIO):
                handle_output(content=self.test_content, to_stdout=True)

        self.assertEqual(mock_stdout.getvalue().strip(), self.test_content)

    def test_default_stdout(self):
        """Test default behavior outputs to stdout."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.stderr", new_callable=StringIO):
                handle_output(content=self.test_content)

        self.assertEqual(mock_stdout.getvalue().strip(), self.test_content)

    @patch("repo_to_markdown.output.PYPERCLIP_AVAILABLE", True)
    @patch("repo_to_markdown.output.pyperclip")
    def test_clipboard_output(self, mock_pyperclip):
        """Test clipboard output."""
        with patch("sys.stderr", new_callable=StringIO):
            handle_output(content=self.test_content, to_clipboard=True, to_stdout=False)

        mock_pyperclip.copy.assert_called_once_with(self.test_content)

    @patch("repo_to_markdown.output.PYPERCLIP_AVAILABLE", False)
    def test_clipboard_unavailable(self):
        """Test clipboard output when pyperclip is unavailable."""
        with patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit):
                handle_output(content=self.test_content, to_clipboard=True, to_stdout=False)

    def test_multiple_outputs(self):
        """Test multiple output options."""
        output_file = Path(self.temp_dir) / "test.md"

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.stderr", new_callable=StringIO):
                with patch("repo_to_markdown.output.PYPERCLIP_AVAILABLE", True):
                    with patch("repo_to_markdown.output.pyperclip") as mock_pyperclip:
                        handle_output(
                            content=self.test_content,
                            output_file=output_file,
                            to_clipboard=True,
                            to_stdout=True,
                        )

        # Check all outputs were used
        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_text(), self.test_content)
        self.assertEqual(mock_stdout.getvalue().strip(), self.test_content)
        mock_pyperclip.copy.assert_called_once_with(self.test_content)

    def test_file_output_creates_directory(self):
        """Test that file output creates parent directories."""
        output_file = Path(self.temp_dir) / "subdir" / "test.md"

        with patch("sys.stderr", new_callable=StringIO):
            handle_output(content=self.test_content, output_file=output_file, to_stdout=False)

        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_text(), self.test_content)

    def test_file_output_error(self):
        """Test file output error handling."""
        # Try to write to a directory instead of file
        output_file = Path(self.temp_dir)

        with patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit):
                handle_output(content=self.test_content, output_file=output_file, to_stdout=False)


class TestDefaultFilename(TestCase):
    """Test default filename generation."""

    def test_get_default_output_filename(self):
        """Test generating default output filename."""
        repo_path = Path("/home/user/my-project")
        filename = get_default_output_filename(repo_path)

        self.assertEqual(filename, Path("my-project_export.md"))

    def test_get_default_output_filename_special_chars(self):
        """Test generating default filename with special characters."""
        repo_path = Path("/home/user/my project with spaces")
        filename = get_default_output_filename(repo_path)

        self.assertEqual(filename, Path("my project with spaces_export.md"))


if __name__ == "__main__":
    import unittest

    unittest.main()
