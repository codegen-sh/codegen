"""LangChain tools for web browsing."""

from typing import ClassVar

from langchain_core.tools.base import BaseTool
from pydantic import BaseModel, Field

from codegen.extensions.web.web import (
    web_browse_page_tool,
    web_extract_images_tool,
    web_search_tool,
)
from codegen.extensions.web.web_client import WebClient


class WebBrowsePageInput(BaseModel):
    """Input for browsing a web page."""

    url: str = Field(..., description="URL of the web page to browse")


class WebBrowsePageTool(BaseTool):
    """Tool for browsing web pages."""

    name: ClassVar[str] = "web_browse_page"
    description: ClassVar[str] = "Browse a web page and extract its content"
    args_schema: ClassVar[type[BaseModel]] = WebBrowsePageInput
    client: WebClient = Field(exclude=True)

    def __init__(self, client: WebClient) -> None:
        super().__init__(client=client)

    def _run(self, url: str) -> str:
        result = web_browse_page_tool(self.client, url)
        return result.render()


class WebSearchInput(BaseModel):
    """Input for web search."""

    query: str = Field(..., description="Search query string")
    num_results: int = Field(default=10, description="Maximum number of results to return")


class WebSearchTool(BaseTool):
    """Tool for searching the web."""

    name: ClassVar[str] = "web_search"
    description: ClassVar[str] = "Search the web using a search engine"
    args_schema: ClassVar[type[BaseModel]] = WebSearchInput
    client: WebClient = Field(exclude=True)

    def __init__(self, client: WebClient) -> None:
        super().__init__(client=client)

    def _run(self, query: str, num_results: int = 10) -> str:
        result = web_search_tool(self.client, query, num_results)
        return result.render()


class WebExtractImagesInput(BaseModel):
    """Input for extracting images from a web page."""

    url: str = Field(..., description="URL of the web page")
    max_images: int = Field(default=20, description="Maximum number of images to extract")


class WebExtractImagesTool(BaseTool):
    """Tool for extracting images from web pages."""

    name: ClassVar[str] = "web_extract_images"
    description: ClassVar[str] = "Extract images from a web page"
    args_schema: ClassVar[type[BaseModel]] = WebExtractImagesInput
    client: WebClient = Field(exclude=True)

    def __init__(self, client: WebClient) -> None:
        super().__init__(client=client)

    def _run(self, url: str, max_images: int = 20) -> str:
        result = web_extract_images_tool(self.client, url, max_images)
        return result.render()
