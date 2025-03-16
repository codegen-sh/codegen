"""Web page viewing tool for the code agent."""

from typing import Optional

import requests
from bs4 import BeautifulSoup

from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.result import Result


def web_page_view(
    codebase: Codebase,
    url: str,
    selector: Optional[str] = None,
    max_length: int = 10000,
) -> Result:
    """Extract content from a web page.

    Args:
        codebase: The codebase (not used but required for consistency)
        url: URL of the web page to view
        selector: Optional CSS selector to extract specific content
        max_length: Maximum length of content to return (default: 10000)

    Returns:
        Result object with web page content
    """
    try:
        # Set user agent to avoid being blocked
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

        # Make the request
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Extract content based on selector if provided
        if selector:
            content_elements = soup.select(selector)
            if not content_elements:
                return Result(
                    success=False,
                    message=f"No elements found matching selector '{selector}'",
                    data=None,
                )
            content = "\n".join([elem.get_text(strip=True) for elem in content_elements])
        else:
            # Get the main content (try common content containers)
            main_content = soup.find("main") or soup.find("article") or soup.find("div", {"id": "content"}) or soup.find("div", {"class": "content"})

            if main_content:
                content = main_content.get_text(strip=True)
            else:
                # Fall back to the entire page text
                content = soup.get_text(strip=True)

        # Truncate if too long
        if len(content) > max_length:
            content = content[:max_length] + "... [content truncated]"

        # Get the page title
        title = soup.title.string if soup.title else "Unknown Title"

        return Result(
            success=True,
            message=f"Successfully extracted content from {url}",
            data={
                "url": url,
                "title": title,
                "content": content,
                "content_length": len(content),
            },
        )
    except requests.RequestException as e:
        return Result(
            success=False,
            message=f"Error fetching web page: {e!s}",
            data=None,
        )
    except Exception as e:
        return Result(
            success=False,
            message=f"Error processing web page: {e!s}",
            data=None,
        )
