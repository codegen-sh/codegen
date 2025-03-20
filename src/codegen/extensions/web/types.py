"""Types for web browsing functionality."""

from pydantic import BaseModel, Field


class WebPage(BaseModel):
    """Represents a web page."""

    url: str = Field(description="URL of the web page")
    title: str = Field(description="Title of the web page")
    content: str = Field(description="Main content of the web page")
    status_code: int = Field(description="HTTP status code of the response")


class WebSearchResult(BaseModel):
    """Represents a single search result."""

    title: str = Field(description="Title of the search result")
    url: str = Field(description="URL of the search result")
    snippet: str = Field(description="Snippet or description of the search result")


class WebImage(BaseModel):
    """Represents an image from a web page."""

    url: str = Field(description="URL of the image")
    alt_text: str | None = Field(None, description="Alternative text for the image")
    width: int | None = Field(None, description="Width of the image in pixels")
    height: int | None = Field(None, description="Height of the image in pixels")
