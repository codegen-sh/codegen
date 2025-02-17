"""Semantic search over codebase files."""

from typing import Any, Optional

from codegen import Codebase
from codegen.extensions.index.file_index import FileIndex


def semantic_search(
    codebase: Codebase,
    query: str,
    k: int = 5,
    preview_length: int = 200,
    index_path: Optional[str] = None,
) -> dict[str, Any]:
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
        Dict containing search results or error information. Format:
        {
            "status": "success",
            "query": str,
            "results": [
                {
                    "filepath": str,
                    "score": float,
                    "preview": str
                },
                ...
            ]
        }
        Or on error:
        {
            "error": str
        }
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
        for filepath, score in results:
            try:
                file = codebase.get_file(filepath)
                preview = file.content[:preview_length].replace("\n", " ").strip()
                if len(file.content) > preview_length:
                    preview += "..."

                formatted_results.append({"filepath": filepath, "score": float(score), "preview": preview})
            except Exception as e:
                # Skip files that can't be read
                print(f"Warning: Could not read file {filepath}: {e}")
                continue

        return {"status": "success", "query": query, "results": formatted_results}

    except Exception as e:
        return {"error": f"Failed to perform semantic search: {e!s}"}
