"""
Browser automation for opening AI chat services.
"""

import webbrowser
import time
import sys
from typing import List, Optional

# AI Service URLs
AI_SERVICES = {
    "chatgpt": "https://chat.openai.com/",
    "claude": "https://claude.ai/",
    "gemini": "https://gemini.google.com/",
}

# Browser commands
BROWSERS = {
    "chrome": "google-chrome",
    "firefox": "firefox",
    "safari": "safari",
    "edge": "microsoft-edge",
}


def get_browser_controller(browser_name: str) -> webbrowser.BaseBrowser:
    """Get browser controller for the specified browser."""
    if browser_name == "default":
        return webbrowser.get()

    try:
        if browser_name in BROWSERS:
            return webbrowser.get(BROWSERS[browser_name])
        else:
            return webbrowser.get(browser_name)
    except webbrowser.Error:
        print(
            f"Warning: Browser '{browser_name}' not found, using default",
            file=sys.stderr,
        )
        return webbrowser.get()


def create_chat_url(service: str, prompt: Optional[str] = None) -> str:
    """Create URL for starting a new chat with optional prompt."""
    base_url = AI_SERVICES.get(service)
    if not base_url:
        raise ValueError(f"Unknown AI service: {service}")

    # For most services, we just open the main page
    # The user will need to manually start a new chat and paste content
    return base_url


def show_instructions(service: str, prompt: Optional[str] = None) -> None:
    """Show instructions for using the AI service."""
    service_names = {"chatgpt": "ChatGPT", "claude": "Claude", "gemini": "Gemini"}

    service_name = service_names.get(service, service.upper())

    print(f"\n📋 Instructions for {service_name}:", file=sys.stderr)
    print("1. New chat session opened in your browser", file=sys.stderr)

    if prompt:
        print("2. Repository content + prompt copied to clipboard", file=sys.stderr)
        print("3. Paste everything with Ctrl+V (Cmd+V on Mac)", file=sys.stderr)
        print(f"4. Your prompt: '{prompt}'", file=sys.stderr)
    else:
        print("2. Repository content copied to clipboard", file=sys.stderr)
        print("3. Paste content with Ctrl+V (Cmd+V on Mac)", file=sys.stderr)


def open_ai_chat(
    services: List[str],
    prompt: Optional[str] = None,
    browser: str = "default",
    verbose: bool = False,
) -> bool:
    """
    Open AI chat service(s) in browser.

    Args:
        services: List of AI services to open
        prompt: Optional prompt to show instructions for
        browser: Browser to use
        verbose: Whether to show detailed output

    Returns:
        True if at least one service was opened successfully
    """
    browser_controller = get_browser_controller(browser)
    success_count = 0

    for service in services:
        if service not in AI_SERVICES:
            print(f"Warning: Unknown AI service '{service}', skipping", file=sys.stderr)
            continue

        try:
            url = create_chat_url(service, prompt)

            if verbose:
                print(f"Opening {service} at {url}", file=sys.stderr)

            browser_controller.open_new_tab(url)
            success_count += 1

            # Show instructions
            show_instructions(service, prompt)

            # Small delay between opening multiple tabs
            if len(services) > 1:
                time.sleep(1)

        except Exception as e:
            print(f"Error opening {service}: {e}", file=sys.stderr)

    return success_count > 0


def check_clipboard_content() -> bool:
    """Check if clipboard contains content (requires pyperclip)."""
    try:
        import pyperclip

        content = pyperclip.paste()
        return bool(content and content.strip())
    except ImportError:
        return False
