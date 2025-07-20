"""
Tests for browser automation functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

from repo2md.browser import (
    create_chat_url,
    open_ai_chat,
    get_browser_controller,
    show_instructions,
    check_clipboard_content,
    AI_SERVICES,
)


class TestBrowserAutomation(unittest.TestCase):
    """Test browser automation functionality."""

    def test_create_chat_url(self):
        """Test chat URL creation."""
        # Test valid services
        for service in AI_SERVICES:
            url = create_chat_url(service)
            self.assertEqual(url, AI_SERVICES[service])

        # Test with prompt (should not change URL for basic implementation)
        url_with_prompt = create_chat_url("chatgpt", "test prompt")
        self.assertEqual(url_with_prompt, AI_SERVICES["chatgpt"])

        # Test invalid service
        with self.assertRaises(ValueError):
            create_chat_url("invalid_service")

    @patch("repo2md.browser.webbrowser")
    def test_get_browser_controller(self, mock_webbrowser):
        """Test browser controller selection."""
        mock_browser = MagicMock()
        mock_webbrowser.get.return_value = mock_browser

        # Test default browser
        get_browser_controller("default")
        mock_webbrowser.get.assert_called_once_with()

        # Test specific browser
        mock_webbrowser.reset_mock()
        get_browser_controller("chrome")
        mock_webbrowser.get.assert_called_with("google-chrome")

    def test_show_instructions(self):
        """Test instruction display."""
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            show_instructions("chatgpt", "test prompt")

        output = mock_stderr.getvalue()
        self.assertIn("CHATGPT", output.upper())
        self.assertIn("New chat", output)
        self.assertIn("test prompt", output)

    @patch("repo2md.browser.webbrowser")
    def test_open_ai_chat(self, mock_webbrowser):
        """Test opening AI chat services."""
        mock_browser = MagicMock()
        mock_webbrowser.get.return_value = mock_browser

        with patch("sys.stderr", new_callable=StringIO):
            # Test single service
            success = open_ai_chat(["chatgpt"])
            self.assertTrue(success)
            mock_browser.open_new_tab.assert_called_once()

            # Test multiple services
            mock_browser.reset_mock()
            success = open_ai_chat(["chatgpt", "claude"])
            self.assertTrue(success)
            self.assertEqual(mock_browser.open_new_tab.call_count, 2)

            # Test invalid service
            mock_browser.reset_mock()
            success = open_ai_chat(["invalid_service"])
            self.assertFalse(success)
            mock_browser.open_new_tab.assert_not_called()

    @patch("pyperclip.paste")
    def test_check_clipboard_content(self, mock_paste):
        """Test clipboard content checking."""
        # Test with content
        mock_paste.return_value = "test content"
        self.assertTrue(check_clipboard_content())

        # Test without content
        mock_paste.return_value = ""
        self.assertFalse(check_clipboard_content())

        # Test with only whitespace
        mock_paste.return_value = "   \n  "
        self.assertFalse(check_clipboard_content())

    @patch("builtins.__import__", side_effect=ImportError)
    def test_check_clipboard_content_no_pyperclip(self, mock_import):
        """Test clipboard checking when pyperclip is not available."""
        # mock_import is used by the decorator to simulate ImportError
        self.assertFalse(check_clipboard_content())


if __name__ == "__main__":
    unittest.main()
