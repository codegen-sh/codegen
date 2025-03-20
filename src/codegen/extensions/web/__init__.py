"""Web browsing functionality."""

from codegen.extensions.web.web import (
    web_browse_page_tool,
    web_extract_images_tool,
    web_search_tool,
)
from codegen.extensions.web.web_client import WebClient

__all__ = [
    "WebClient",
    "web_browse_page_tool",
    "web_extract_images_tool",
    "web_search_tool",
]
