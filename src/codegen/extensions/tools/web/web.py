"""Tools for browsing the web."""

from typing import ClassVar

import requests
from bs4 import BeautifulSoup
from pydantic import Field

from ..observation import Observation


class WebSearchObservation(Observation):
    """Response from searching the web."""

    query: str = Field(description="Search query used")
    results: list[dict] = Field(description="List of search results")

    str_template: ClassVar[str] = "Found {result_count} results for '{query}'"

    def _get_details(self) -> dict[str, str | int]:
        """Get details for string representation."""
        return {
            "result_count": len(self.results),
            "query": self.query,
        }


class WebPageObservation(Observation):
    """Response from viewing a web page."""

    url: str = Field(description="URL of the web page")
    title: str = Field(description="Title of the web page")
    content: str = Field(description="Content of the web page")

    str_template: ClassVar[str] = "Viewed web page: {title}"


def web_search_tool(query: str, num_results: int = 5) -> WebSearchObservation:
    """Search the web and get content snippets from search results.

    Args:
        query: Search query string
        num_results: Maximum number of results to return (default: 5)

    Returns:
        WebSearchObservation with search results
    """
    try:
        # Note: In a real implementation, this would use a search API like Google Custom Search API,
        # Bing Search API, or a similar service. For this example, we'll return mock data.
        # The actual implementation would require API keys and proper error handling.

        # Mock search results for demonstration
        mock_results = [
            {
                "title": f"Result {i + 1} for {query}",
                "url": f"https://example.com/result{i + 1}",
                "snippet": f"This is a snippet of content for result {i + 1} related to {query}...",
            }
            for i in range(min(num_results, 5))
        ]

        return WebSearchObservation(
            status="success",
            query=query,
            results=mock_results,
        )
    except requests.exceptions.RequestException as e:
        # Network-related errors
        return WebSearchObservation(
            status="error",
            error=f"Network error when searching: {e!s}",
            query=query,
            results=[],
        )
    except Exception as e:
        # Catch-all for other errors
        return WebSearchObservation(
            status="error",
            error=f"Failed to search the web: {e!s}",
            query=query,
            results=[],
        )


def web_view_page_tool(url: str, max_length: int = 10000) -> WebPageObservation:
    """View the content of a specific webpage.

    Args:
        url: URL of the webpage to view
        max_length: Maximum length of content to return (default: 10000)

    Returns:
        WebPageObservation with page content
    """
    try:
        # Send a GET request to the URL
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses

        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract the title
        title = soup.title.string if soup.title else "No title found"

        # Extract the main content (simplified approach)
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Get text content
        text = soup.get_text(separator="\n", strip=True)

        # Truncate if necessary
        if len(text) > max_length:
            text = text[:max_length] + "... [content truncated]"

        return WebPageObservation(
            status="success",
            url=url,
            title=title,
            content=text,
        )
    except requests.exceptions.RequestException as e:
        # Network-related errors
        return WebPageObservation(
            status="error",
            error=f"Network error when fetching page: {e!s}",
            url=url,
            title="",
            content="",
        )
    except Exception as e:
        # Catch-all for other errors
        return WebPageObservation(
            status="error",
            error=f"Failed to view web page: {e!s}",
            url=url,
            title="",
            content="",
        )
