"""Semantic search over codebase files."""

from typing import ClassVar, Optional

from pydantic import Field

from codegen.extensions.index.file_index import FileIndex
from codegen.sdk.core.codebase import Codebase

from .observation import Observation


class SearchResult(Observation):
    """Information about a single search result."""

    filepath: str = Field(
        description="Path to the matching file",
    )
    score: float = Field(
        description="Similarity score of the match",
    )
    preview: str = Field(
        description="Preview of the file content",
    )

    str_template: ClassVar[str] = "{filepath} (score: {score})"


class SemanticSearchObservation(Observation):
    """Response from semantic search over codebase."""

    query: str = Field(
        description="The search query that was used",
    )
    results: list[SearchResult] = Field(
        description="List of search results",
    )

    str_template: ClassVar[str] = "Found {result_count} results for '{query}'"

    def _get_details(self) -> dict[str, str | int]:
        """Get details for string representation."""
        return {
            "result_count": len(self.results),
            "query": self.query,
        }


def semantic_search(
    codebase: Codebase,
    query: str,
    k: int = 5,
    preview_length: int = 200,
    index_path: Optional[str] = None,
) -> SemanticSearchObservation:
    """Search the codebase using semantic similarity.

    This function provides semantic search over a codebase by using OpenAI's embeddings.
    Currently, it loads/saves the index from disk each time, but could be optimized to
    maintain embeddings in memory for frequently accessed codebases.

    TODO(CG-XXXX): Add support for maintaining embeddings in memory across searches,
    potentially with an LRU cache or similar mechanism to avoid recomputing embeddings
    for frequently searched codebases.

    Args:
        codebase: The codebase to search
        query: The search query in natural language
        k: Number of results to return (default: 5)
        preview_length: Length of content preview in characters (default: 200)
        index_path: Optional path to a saved vector index

    Returns:
        SemanticSearchObservation containing search results or error information.
    """
    try:
        # Initialize vector index
        index = FileIndex(codebase)

        # Try to load existing index
        try:
            if index_path:
                index.load(index_path)
            else:
                index.load()
        except FileNotFoundError:
            # Create new index if none exists
            index.create()
            index.save(index_path)

        # Perform search
        results = index.similarity_search(query, k=k)

        # Format results with previews
        formatted_results = []
        for file, score in results:
            preview = file.content[:preview_length].replace("\n", " ").strip()
            if len(file.content) > preview_length:
                preview += "..."

            formatted_results.append(
                SearchResult(
                    status="success",
                    filepath=file.filepath,
                    score=float(score),
                    preview=preview,
                )
            )

        return SemanticSearchObservation(
            status="success",
            query=query,
            results=formatted_results,
        )

    except Exception as e:
        return SemanticSearchObservation(
            status="error",
            error=f"Failed to perform semantic search: {e!s}",
            query=query,
            results=[],
        )
