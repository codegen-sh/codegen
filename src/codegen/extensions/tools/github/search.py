"""Tools for searching GitHub issues and pull requests."""

from typing import ClassVar

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from ..observation import Observation


class SearchResultObservation(Observation):
    """Response from searching issues and pull requests."""

    query: str = Field(
        description="The search query that was used",
    )
    results: list[dict] = Field(
        description="List of matching issues/PRs with their details. Use is:pr in query to search for PRs, is:issue for issues.",
    )

    str_template: ClassVar[str] = "Found {total} results matching query: {query}"

    @property
    def total(self) -> int:
        return len(self.results)


def search(
    codebase: Codebase,
    query: str,
    max_results: int = 20,
) -> SearchResultObservation:
    """Search for GitHub issues and pull requests using the provided query.

    To search for pull requests specifically, include 'is:pr' in your query.
    To search for issues specifically, include 'is:issue' in your query.
    If neither is specified, both issues and PRs will be included in results.

    Args:
        codebase: The codebase to operate on
        query: Search query string (e.g. "is:pr label:bug", "is:issue is:open")
        state: Filter by state ("open", "closed", or "all")
        max_results: Maximum number of results to return
    """
    try:
        # Get the GitHub repo object
        repo = codebase._op.remote_git_repo

        # Search using PyGitHub's search_issues (which searches both issues and PRs)
        results = []
        for item in repo.search_issues(query)[:max_results]:
            result = {
                "title": item.title,
                "number": item.number,
                "state": item.state,
                "labels": [label.name for label in item.labels],
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
                "url": item.html_url,
                "is_pr": item.pull_request is not None,
            }
            results.append(result)

        return SearchResultObservation(
            status="success",
            query=query,
            results=results,
        )

    except Exception as e:
        return SearchResultObservation(
            status="error",
            error=f"Failed to search: {e!s}",
            query=query,
            results=[],
        )
