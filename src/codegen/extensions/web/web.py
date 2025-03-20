"""Tools for web browsing functionality."""

from typing import ClassVar

import requests
from pydantic import Field

from codegen.extensions.tools.observation import Observation
from codegen.extensions.web.web_client import WebClient


class WebBrowsePageObservation(Observation):
    """Response from browsing a web page."""

    url: str = Field(description="URL of the browsed page")
    title: str = Field(description="Title of the web page")
    content: str = Field(description="Content of the web page")
    status_code: int = Field(description="HTTP status code")

    str_template: ClassVar[str] = "Browsed page: {title} ({url})"


class WebSearchObservation(Observation):
    """Response from web search."""

    query: str = Field(description="Search query used")
    results: list[dict] = Field(description="List of search results")

    str_template: ClassVar[str] = "Found {result_count} results for '{query}'"

    def _get_details(self) -> dict[str, str | int]:
        """Get details for string representation."""
        return {
            "result_count": len(self.results),
            "query": self.query,
        }


class WebExtractImagesObservation(Observation):
    """Response from extracting images from a web page."""

    url: str = Field(description="URL of the web page")
    images: list[dict] = Field(description="List of extracted images")

    str_template: ClassVar[str] = "Extracted {image_count} images from {url}"

    def _get_details(self) -> dict[str, str | int]:
        """Get details for string representation."""
        return {
            "image_count": len(self.images),
            "url": self.url,
        }


def web_browse_page_tool(client: WebClient, url: str) -> WebBrowsePageObservation:
    """Browse a web page and extract its content.

    Args:
        client: WebClient instance
        url: URL of the web page to browse

    Returns:
        WebBrowsePageObservation with the page content
    """
    try:
        page = client.browse_page(url)
        return WebBrowsePageObservation(
            status="success",
            url=page.url,
            title=page.title,
            content=page.content,
            status_code=page.status_code,
        )
    except requests.exceptions.RequestException as e:
        # Network-related errors
        return WebBrowsePageObservation(
            status="error",
            error=f"Network error when browsing page: {e!s}",
            url=url,
            title="Error",
            content="",
            status_code=0,
        )
    except ValueError as e:
        # Input validation errors
        return WebBrowsePageObservation(
            status="error",
            error=f"Invalid input: {e!s}",
            url=url,
            title="Error",
            content="",
            status_code=0,
        )
    except Exception as e:
        # Catch-all for other errors
        return WebBrowsePageObservation(
            status="error",
            error=f"Failed to browse page: {e!s}",
            url=url,
            title="Error",
            content="",
            status_code=0,
        )


def web_search_tool(client: WebClient, query: str, num_results: int = 10) -> WebSearchObservation:
    """Search the web using a search engine.

    Args:
        client: WebClient instance
        query: Search query string
        num_results: Maximum number of results to return

    Returns:
        WebSearchObservation with search results
    """
    try:
        results = client.search(query, num_results)
        return WebSearchObservation(
            status="success",
            query=query,
            results=[result.dict() for result in results],
        )
    except requests.exceptions.RequestException as e:
        # Network-related errors
        return WebSearchObservation(
            status="error",
            error=f"Network error when searching: {e!s}",
            query=query,
            results=[],
        )
    except ValueError as e:
        # Input validation errors
        return WebSearchObservation(
            status="error",
            error=f"Invalid input: {e!s}",
            query=query,
            results=[],
        )
    except Exception as e:
        # Catch-all for other errors
        return WebSearchObservation(
            status="error",
            error=f"Failed to search: {e!s}",
            query=query,
            results=[],
        )


def web_extract_images_tool(client: WebClient, url: str, max_images: int = 20) -> WebExtractImagesObservation:
    """Extract images from a web page.

    Args:
        client: WebClient instance
        url: URL of the web page
        max_images: Maximum number of images to extract

    Returns:
        WebExtractImagesObservation with extracted images
    """
    try:
        images = client.extract_images(url, max_images)
        return WebExtractImagesObservation(
            status="success",
            url=url,
            images=[image.dict() for image in images],
        )
    except requests.exceptions.RequestException as e:
        # Network-related errors
        return WebExtractImagesObservation(
            status="error",
            error=f"Network error when extracting images: {e!s}",
            url=url,
            images=[],
        )
    except ValueError as e:
        # Input validation errors
        return WebExtractImagesObservation(
            status="error",
            error=f"Invalid input: {e!s}",
            url=url,
            images=[],
        )
    except Exception as e:
        # Catch-all for other errors
        return WebExtractImagesObservation(
            status="error",
            error=f"Failed to extract images: {e!s}",
            url=url,
            images=[],
        )
