"""Abstract base class for code indexing implementations."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, TypeVar

import numpy as np

from codegen.sdk.core.codebase import Codebase

T = TypeVar("T")  # Type of the items being indexed (e.g., File, Symbol)


class CodeIndex(ABC):
    """Abstract base class for semantic code search indices.

    This class defines the interface for different code indexing implementations.
    Implementations can index at different granularities (files, symbols, etc.)
    and use different embedding strategies.

    Attributes:
        codebase (Codebase): The codebase being indexed
        E (Optional[np.ndarray]): The embeddings matrix
        items (Optional[np.ndarray]): Array of items corresponding to embeddings
        commit_hash (Optional[str]): Git commit hash when index was last updated
    """

    DEFAULT_SAVE_DIR = ".codegen"

    def __init__(self, codebase: Codebase):
        """Initialize the code index.

        Args:
            codebase: The codebase to index
        """
        self.codebase = codebase
        self.E: Optional[np.ndarray] = None
        self.items: Optional[np.ndarray] = None
        self.commit_hash: Optional[str] = None

    @property
    @abstractmethod
    def save_file_name(self) -> str:
        """The filename template for saving the index."""
        pass

    @abstractmethod
    def _get_embeddings(self, items: list[T]) -> list[list[float]]:
        """Get embeddings for a list of items.

        Args:
            items: List of items to get embeddings for

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def _get_items_to_index(self) -> list[tuple[T, str]]:
        """Get all items that should be indexed and their content.

        Returns:
            List of tuples (item, content_to_embed)
        """
        pass

    @abstractmethod
    def _get_changed_items(self) -> set[T]:
        """Get set of items that have changed since last index update.

        Returns:
            Set of changed items
        """
        pass

    def _get_current_commit(self) -> str:
        """Get the current git commit hash."""
        current = self.codebase.current_commit
        if current is None:
            msg = "No current commit found. Repository may be empty or in a detached HEAD state."
            raise ValueError(msg)
        return current.hexsha

    def _get_default_save_path(self) -> Path:
        """Get the default save path for the index."""
        save_dir = Path(self.codebase.repo_path) / self.DEFAULT_SAVE_DIR
        save_dir.mkdir(exist_ok=True)

        if self.commit_hash is None:
            self.commit_hash = self._get_current_commit()

        filename = self.save_file_name.format(commit=self.commit_hash[:8])
        return save_dir / filename

    def create(self) -> None:
        """Create embeddings for all indexed items."""
        self.commit_hash = self._get_current_commit()

        # Get items and their content
        items_with_content = self._get_items_to_index()
        if not items_with_content:
            self.E = np.array([])
            self.items = np.array([])
            return

        # Split into separate lists
        items, contents = zip(*items_with_content)

        # Get embeddings
        embeddings = self._get_embeddings(contents)

        # Store embeddings and item identifiers
        self.E = np.array(embeddings)
        self.items = np.array([str(item) for item in items])  # Store string identifiers

    def update(self) -> None:
        """Update embeddings for changed items only."""
        if self.E is None or self.items is None or self.commit_hash is None:
            msg = "No index to update. Call create() or load() first."
            raise ValueError(msg)

        # Get changed items
        changed_items = self._get_changed_items()
        if not changed_items:
            return

        # Get content for changed items
        items_with_content = [(item, content) for item, content in self._get_items_to_index() if item in changed_items]

        if not items_with_content:
            return

        items, contents = zip(*items_with_content)
        new_embeddings = self._get_embeddings(contents)

        # Create mapping of items to their indices
        item_to_idx = {str(item): idx for idx, item in enumerate(self.items)}

        # Update embeddings
        for item, embedding in zip(items, new_embeddings):
            item_key = str(item)
            if item_key in item_to_idx:
                # Update existing embedding
                self.E[item_to_idx[item_key]] = embedding
            else:
                # Add new embedding
                self.E = np.vstack([self.E, embedding])
                self.items = np.append(self.items, item)

        # Update commit hash
        self.commit_hash = self._get_current_commit()

    def save(self, save_path: Optional[str] = None) -> None:
        """Save the index to disk."""
        if self.E is None or self.items is None:
            msg = "No embeddings to save. Call create() first."
            raise ValueError(msg)

        save_path = Path(save_path) if save_path else self._get_default_save_path()
        save_path.parent.mkdir(parents=True, exist_ok=True)

        self._save_index(save_path)

    def load(self, load_path: Optional[str] = None) -> None:
        """Load the index from disk."""
        load_path = Path(load_path) if load_path else self._get_default_save_path()

        if not load_path.exists():
            msg = f"No index found at {load_path}"
            raise FileNotFoundError(msg)

        self._load_index(load_path)

    @abstractmethod
    def _save_index(self, path: Path) -> None:
        """Save index data to disk."""
        pass

    @abstractmethod
    def _load_index(self, path: Path) -> None:
        """Load index data from disk."""
        pass

    def _similarity_search_raw(self, query: str, k: int = 5) -> list[tuple[str, float]]:
        """Internal method to find the k most similar items by their string identifiers.

        Args:
            query: The text to search for
            k: Number of results to return

        Returns:
            List of tuples (item_identifier, similarity_score) sorted by similarity
        """
        if self.E is None or self.items is None:
            msg = "No embeddings available. Call create() or load() first."
            raise ValueError(msg)

        # Get query embedding
        query_embeddings = self._get_embeddings([query])
        query_embedding = query_embeddings[0]

        # Compute cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        E_norm = self.E / np.linalg.norm(self.E, axis=1)[:, np.newaxis]
        similarities = np.dot(E_norm, query_norm)

        # Get top k indices
        top_indices = np.argsort(similarities)[-k:][::-1]

        # Return items and similarity scores
        return [(str(self.items[idx]), float(similarities[idx])) for idx in top_indices]

    @abstractmethod
    def similarity_search(self, query: str, k: int = 5) -> list[tuple[T, float]]:
        """Find the k most similar items to a query.

        Args:
            query: The text to search for
            k: Number of results to return

        Returns:
            List of tuples (item, similarity_score) sorted by similarity
        """
        pass
