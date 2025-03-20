"""Client for web browsing functionality."""

import os
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from codegen.extensions.web.types import WebImage, WebPage, WebSearchResult
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class WebClient:
    """Client for web browsing functionality."""

    def __init__(self, user_agent: Optional[str] = None, max_retries: int = 3, timeout: int = 10):
        """Initialize the web client.

        Args:
            user_agent: Custom user agent string. If None, a default one will be used.
            max_retries: Maximum number of retries for failed requests.
            timeout: Timeout in seconds for requests.
        """
        self.timeout = timeout

        # Set up a session with retry logic
        self.session = requests.Session()

        # Configure retries
        adapter = requests.adapters.HTTPAdapter(max_retries=max_retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set user agent
        if not user_agent:
            user_agent = os.getenv("WEB_USER_AGENT", "Codegen Web Browser Tool/1.0")
        self.session.headers.update({"User-Agent": user_agent})

    def browse_page(self, url: str) -> WebPage:
        """Browse a web page and extract its content.

        Args:
            url: URL of the web page to browse.

        Returns:
            WebPage object containing the page content.

        Raises:
            ValueError: If the URL is invalid or the page cannot be accessed.
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                msg = f"Invalid URL: {url}"
                raise ValueError(msg)

            # Make the request
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title
            title = soup.title.string if soup.title else "No title"

            # Extract main content (simplified approach)
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Get text content
            content = soup.get_text(separator="\n", strip=True)

            # Truncate content if too long (100k chars max)
            if len(content) > 100000:
                content = content[:100000] + "... [content truncated]"

            return WebPage(url=url, title=title, content=content, status_code=response.status_code)

        except requests.exceptions.RequestException as e:
            logger.exception(f"Error browsing page {url}: {e!s}")
            msg = f"Failed to access URL: {e!s}"
            raise ValueError(msg)
        except Exception as e:
            logger.exception(f"Error processing page {url}: {e!s}")
            msg = f"Error processing page: {e!s}"
            raise ValueError(msg)

    def search(self, query: str, num_results: int = 10) -> list[WebSearchResult]:
        """Search the web using a search engine API.

        Note: This is a placeholder. In a real implementation, you would integrate
        with a search engine API like Google Custom Search, Bing, or DuckDuckGo.

        Args:
            query: Search query string.
            num_results: Maximum number of results to return.

        Returns:
            List of WebSearchResult objects.

        Raises:
            ValueError: If the search fails.
        """
        # This is a placeholder. In a real implementation, you would:
        # 1. Call a search engine API
        # 2. Parse the results
        # 3. Return them as WebSearchResult objects

        # For now, return a message explaining this is a placeholder
        placeholder = WebSearchResult(
            title="Search Functionality Placeholder",
            url="https://example.com/search",
            snippet="This is a placeholder for search functionality. In a real implementation, this would integrate with a search engine API like Google Custom Search, Bing, or DuckDuckGo.",
        )

        return [placeholder]

    def extract_images(self, url: str, max_images: int = 20) -> list[WebImage]:
        """Extract images from a web page.

        Args:
            url: URL of the web page.
            max_images: Maximum number of images to extract.

        Returns:
            List of WebImage objects.

        Raises:
            ValueError: If the URL is invalid or the page cannot be accessed.
        """
        try:
            # Make the request
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Find all image tags
            img_tags = soup.find_all("img", limit=max_images)

            images = []
            for img in img_tags:
                # Get image URL (handle relative URLs)
                img_url = img.get("src", "")
                if img_url:
                    img_url = urljoin(url, img_url)
                else:
                    continue

                # Get alt text, width, and height
                alt_text = img.get("alt", None)
                width = int(img.get("width", 0)) or None
                height = int(img.get("height", 0)) or None

                images.append(WebImage(url=img_url, alt_text=alt_text, width=width, height=height))

            return images

        except requests.exceptions.RequestException as e:
            logger.exception(f"Error accessing page {url}: {e!s}")
            msg = f"Failed to access URL: {e!s}"
            raise ValueError(msg)
        except Exception as e:
            logger.exception(f"Error extracting images from {url}: {e!s}")
            msg = f"Error extracting images: {e!s}"
            raise ValueError(msg)
