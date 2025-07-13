"""
Tests for core functionality.
"""

import tempfile
import os
from pathlib import Path
from unittest import TestCase

from repo2md.core import (
    RepoFile,
    ScanResult,
    scan_repository,
    generate_markdown,
    _get_language_from_extension,
    _parse_gitignore,
    _should_ignore_file,
    _is_binary_file,
)


class TestLanguageDetection(TestCase):
    """Test language detection from file extensions."""

    def test_python_files(self):
        """Test Python file detection."""
        self.assertEqual(_get_language_from_extension(Path("test.py")), "python")

    def test_javascript_files(self):
        """Test JavaScript file detection."""
        self.assertEqual(_get_language_from_extension(Path("test.js")), "javascript")
        self.assertEqual(_get_language_from_extension(Path("test.ts")), "typescript")
        self.assertEqual(_get_language_from_extension(Path("test.jsx")), "jsx")
        self.assertEqual(_get_language_from_extension(Path("test.tsx")), "tsx")

    def test_markup_files(self):
        """Test markup file detection."""
        self.assertEqual(_get_language_from_extension(Path("test.md")), "markdown")
        self.assertEqual(_get_language_from_extension(Path("test.html")), "html")
        self.assertEqual(_get_language_from_extension(Path("test.xml")), "xml")

    def test_config_files(self):
        """Test configuration file detection."""
        self.assertEqual(_get_language_from_extension(Path("test.json")), "json")
        self.assertEqual(_get_language_from_extension(Path("test.yaml")), "yaml")
        self.assertEqual(_get_language_from_extension(Path("test.yml")), "yaml")
        self.assertEqual(_get_language_from_extension(Path("test.toml")), "toml")

    def test_special_files(self):
        """Test special file detection."""
        self.assertEqual(_get_language_from_extension(Path("Dockerfile")), "dockerfile")
        self.assertEqual(_get_language_from_extension(Path("Makefile")), "makefile")
        self.assertEqual(_get_language_from_extension(Path("README.md")), "markdown")
        self.assertEqual(_get_language_from_extension(Path("readme.txt")), "markdown")

    def test_unknown_files(self):
        """Test unknown file extensions."""
        self.assertIsNone(_get_language_from_extension(Path("test.unknown")))
        self.assertIsNone(_get_language_from_extension(Path("test")))


class TestGitignoreParser(TestCase):
    """Test .gitignore parsing."""

    def test_parse_gitignore(self):
        """Test parsing .gitignore content."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".gitignore") as f:
            f.write(
                """# Comment
*.pyc
__pycache__/
.env

# Another comment
node_modules/
dist/
"""
            )
            f.flush()

            patterns = _parse_gitignore(Path(f.name))
            expected = ["*.pyc", "__pycache__/", ".env", "node_modules/", "dist/"]
            self.assertEqual(patterns, expected)

            os.unlink(f.name)

    def test_nonexistent_gitignore(self):
        """Test handling of non-existent .gitignore."""
        patterns = _parse_gitignore(Path("/nonexistent/.gitignore"))
        self.assertEqual(patterns, [])


class TestFileFiltering(TestCase):
    """Test file filtering logic."""

    def test_should_ignore_file(self):
        """Test file ignore patterns."""
        repo_root = Path("/repo")

        # Test exact match
        self.assertTrue(_should_ignore_file(Path("/repo/test.pyc"), repo_root, ["*.pyc"]))

        # Test directory pattern
        self.assertTrue(_should_ignore_file(Path("/repo/__pycache__/test.py"), repo_root, ["__pycache__/"]))

        # Test no match
        self.assertFalse(_should_ignore_file(Path("/repo/test.py"), repo_root, ["*.pyc"]))

    def test_binary_file_detection(self):
        """Test binary file detection."""
        # Create a text file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("This is a text file")
            text_file = Path(f.name)

        # Create a binary file
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(b"\x00\x01\x02\x03")
            binary_file = Path(f.name)

        try:
            self.assertFalse(_is_binary_file(text_file))
            self.assertTrue(_is_binary_file(binary_file))
        finally:
            os.unlink(text_file)
            os.unlink(binary_file)


class TestRepositoryScanning(TestCase):
    """Test repository scanning functionality."""

    def setUp(self):
        """Set up test repository."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

        # Create test files
        (self.repo_path / "test.py").write_text('print("Hello")')
        (self.repo_path / "test.js").write_text('console.log("Hello")')
        (self.repo_path / "README.md").write_text("# Test Repository")
        (self.repo_path / ".gitignore").write_text("*.pyc\n__pycache__/")

        # Create subdirectory
        (self.repo_path / "subdir").mkdir()
        (self.repo_path / "subdir" / "test.txt").write_text("Test content")

        # Create binary file
        (self.repo_path / "binary.bin").write_bytes(b"\x00\x01\x02\x03")

    def tearDown(self):
        """Clean up test repository."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_scan_repository(self):
        """Test basic repository scanning."""
        result = scan_repository(self.repo_path)

        self.assertIsInstance(result, ScanResult)
        # Use resolve() to handle symlinks consistently
        self.assertEqual(result.repo_root, self.repo_path.resolve())
        self.assertGreater(len(result.files), 0)

        # Check that binary file is excluded
        file_paths = [f.path.name for f in result.files]
        self.assertNotIn("binary.bin", file_paths)

    def test_exclude_meta_files(self):
        """Test excluding meta files."""
        result = scan_repository(self.repo_path, exclude_meta_files=True)

        file_paths = [f.path.name for f in result.files]
        self.assertNotIn("README.md", file_paths)
        self.assertNotIn(".gitignore", file_paths)

    def test_file_size_limit(self):
        """Test file size limiting."""
        # Create a large file
        large_content = "x" * 1000
        (self.repo_path / "large.txt").write_text(large_content)

        result = scan_repository(self.repo_path, max_file_size=500)

        file_paths = [f.path.name for f in result.files]
        self.assertNotIn("large.txt", file_paths)

    def test_additional_ignore_patterns(self):
        """Test additional ignore patterns."""
        result = scan_repository(self.repo_path, ignore_patterns=["*.js"])

        file_paths = [f.path.name for f in result.files]
        self.assertNotIn("test.js", file_paths)


class TestMarkdownGeneration(TestCase):
    """Test markdown generation."""

    def test_generate_markdown(self):
        """Test markdown generation."""
        repo_root = Path("/test/repo")
        test_file = RepoFile(
            path=repo_root / "test.py",
            content='print("Hello")',
            size=15,
            language="python",
        )

        scan_result = ScanResult(files=[test_file], repo_root=repo_root, total_size=15)

        markdown = generate_markdown(scan_result)

        self.assertIn("# repo", markdown)
        self.assertIn("## Repository Summary", markdown)
        self.assertIn("## File Structure", markdown)
        self.assertIn("## File Contents", markdown)
        self.assertIn("### test.py", markdown)
        self.assertIn("```python", markdown)
        self.assertIn('print("Hello")', markdown)

    def test_generate_markdown_multiple_files(self):
        """Test markdown generation with multiple files."""
        repo_root = Path("/test/repo")
        files = [
            RepoFile(
                path=repo_root / "test.py",
                content='print("Hello")',
                size=15,
                language="python",
            ),
            RepoFile(
                path=repo_root / "test.js",
                content='console.log("Hello")',
                size=20,
                language="javascript",
            ),
        ]

        scan_result = ScanResult(files=files, repo_root=repo_root, total_size=35)

        markdown = generate_markdown(scan_result)

        self.assertIn("**Files:** 2", markdown)
        self.assertIn("### test.py", markdown)
        self.assertIn("### test.js", markdown)
        self.assertIn("```python", markdown)
        self.assertIn("```javascript", markdown)


if __name__ == "__main__":
    import unittest

    unittest.main()
