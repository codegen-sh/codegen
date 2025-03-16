"""Web search tool for the code agent."""

import json
import os

import requests

from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.result import Result


def web_search(
    codebase: Codebase,
    query: str,
    num_results: int = 5,
    search_engine: str = "google",
) -> Result:
    """Search the web for information.

    Args:
        codebase: The codebase (not used but required for consistency)
        query: The search query
        num_results: Number of results to return (default: 5)
        search_engine: Search engine to use (default: "google")

    Returns:
        Result object with search results
    """
    # Get API key from environment variable
    api_key = os.environ.get("SERP_API_KEY")
    if not api_key:
        return Result(
            success=False,
            message="SERP_API_KEY environment variable not set. Please set it to use the web search tool.",
            data=None,
        )

    # Prepare the API request
    base_url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": api_key,
        "engine": search_engine,
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract organic search results
        results = []
        if "organic_results" in data:
            for result in data["organic_results"][:num_results]:
                results.append(
                    {
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                    }
                )

        return Result(
            success=True,
            message=f"Found {len(results)} results for query: {query}",
            data={
                "query": query,
                "results": results,
            },
        )
    except requests.RequestException as e:
        return Result(
            success=False,
            message=f"Error performing web search: {e!s}",
            data=None,
        )
    except json.JSONDecodeError:
        return Result(
            success=False,
            message="Error parsing search results",
            data=None,
        )
