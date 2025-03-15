"""Web browser tool for accessing web content.

This tool allows fetching web pages and extracting their content,
enabling Codegen to browse websites and retrieve information.
"""

from typing import ClassVar
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from .observation import Observation


class WebBrowserObservation(Observation):
    """Response from browsing a web page."""

    url: str = Field(
        description="The URL that was accessed",
    )
    title: str = Field(
        description="The title of the web page",
    )
    content: str = Field(
        description="The extracted content from the web page",
    )
    status_code: int = Field(
        description="HTTP status code of the response",
    )

    str_template: ClassVar[str] = "Browsed {url} (Status: {status_code})"

    def render(self) -> str:
        """Render web browser results in a readable format."""
        if self.status == "error":
            return f"[WEB BROWSER ERROR]: {self.error}"

        lines = [
            f"[WEB PAGE]: {self.url}",
            f"Status: {self.status_code}",
            f"Title: {self.title}",
            "",
            "Content:",
            "----------",
            self.content[:2000] + ("..." if len(self.content) > 2000 else ""),
            "----------",
        ]
        return "\n".join(lines)


def browse_web(
    codebase: Codebase,
    url: str,
    extract_text_only: bool = True,
    timeout: int = 10,
    max_content_length: int = 10000,
) -> WebBrowserObservation:
    """Browse a web page and extract its content.

    Args:
        codebase: The codebase to operate on (not used but required for tool interface)
        url: The URL to browse
        extract_text_only: Whether to extract only text content (default: True)
        timeout: Request timeout in seconds (default: 10)
        max_content_length: Maximum content length to return (default: 10000)

    Returns:
        WebBrowserObservation containing the web page content and metadata
    """
    # Validate URL
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return WebBrowserObservation(
            status="error",
            error=f"Invalid URL: {url}. Must include scheme (http:// or https://) and domain.",
            url=url,
            title="",
            content="",
            status_code=0,
        )

    # Add scheme if missing
    if not parsed_url.scheme:
        url = f"https://{url}"

    try:
        # Set user agent to avoid being blocked
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

        # Make the request
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title = soup.title.string if soup.title else "No title found"

        # Extract content based on preference
        if extract_text_only:
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Get text and clean it up
            text = soup.get_text()
            # Break into lines and remove leading/trailing space
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Remove blank lines
            content = "\n".join(chunk for chunk in chunks if chunk)
        else:
            # Return simplified HTML
            content = str(soup)

        # Truncate content if too long
        if len(content) > max_content_length:
            content = content[:max_content_length] + "... (content truncated)"

        return WebBrowserObservation(
            status="success",
            url=url,
            title=title,
            content=content,
            status_code=response.status_code,
        )

    except requests.exceptions.RequestException as e:
        return WebBrowserObservation(
            status="error",
            error=f"Error accessing URL: {e!s}",
            url=url,
            title="",
            content="",
            status_code=getattr(e.response, "status_code", 0) if hasattr(e, "response") else 0,
        )
