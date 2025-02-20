"""File-level semantic code search index."""

import logging
import pickle
from pathlib import Path

import numpy as np
import tiktoken
from openai import OpenAI
from tqdm import tqdm

from codegen.extensions.index.code_index import CodeIndex
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import File

logger = logging.getLogger(__name__)


class FileIndex(CodeIndex):
    """A semantic search index over codebase files.

    This implementation indexes entire files, splitting large files into chunks
    if they exceed the token limit.
    """

    EMBEDDING_MODEL = "text-embedding-3-small"
    MAX_TOKENS = 8000
    BATCH_SIZE = 100

    def __init__(self, codebase: Codebase):
        """Initialize the file index.

        Args:
            codebase: The codebase to index
        """
        super().__init__(codebase)
        self.client = OpenAI()
        self.encoding = tiktoken.get_encoding("cl100k_base")

    @property
    def save_file_name(self) -> str:
        return "file_index_{commit}.pkl"

    def _split_by_tokens(self, text: str) -> list[str]:
        """Split text into chunks that fit within token limit."""
        tokens = self.encoding.encode(text)
        chunks = []
        current_chunk = []
        current_size = 0

        for token in tokens:
            if current_size + 1 > self.MAX_TOKENS:
                chunks.append(self.encoding.decode(current_chunk))
                current_chunk = [token]
                current_size = 1
            else:
                current_chunk.append(token)
                current_size += 1

        if current_chunk:
            chunks.append(self.encoding.decode(current_chunk))

        return chunks

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for a batch of texts using OpenAI's API."""
        # Clean texts
        texts = [text.replace("\\n", " ") for text in texts]

        # Process in batches with progress bar
        all_embeddings = []
        for i in tqdm(range(0, len(texts), self.BATCH_SIZE), desc="Getting embeddings"):
            batch = texts[i : i + self.BATCH_SIZE]
            response = self.client.embeddings.create(model=self.EMBEDDING_MODEL, input=batch, encoding_format="float")
            all_embeddings.extend(data.embedding for data in response.data)

        return all_embeddings

    def _get_items_to_index_for_files(self, files: list[File]) -> list[tuple[str, str]]:
        """Get items to index for specific files."""
        items_to_index = []

        # Filter out binary files and files without content
        files_to_process = []
        for f in files:
            try:
                if f.content:  # This will raise ValueError for binary files
                    files_to_process.append(f)
            except ValueError:
                logger.debug(f"Skipping binary file: {f.filepath}")

        if len(files) == 1:
            logger.info(f"Processing file: {files[0].filepath}")
        else:
            logger.info(f"Found {len(files_to_process)} indexable files out of {len(files)} total files")

        # Collect all chunks that need to be processed
        for file in files_to_process:
            chunks = self._split_by_tokens(file.content)
            if len(chunks) == 1:
                items_to_index.append((file.filepath, file.content))
            else:
                # For multi-chunk files, create virtual items
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{file.filepath}#chunk{i}"
                    items_to_index.append((chunk_id, chunk))

        if items_to_index:
            logger.info(f"Total chunks to process: {len(items_to_index)}")
        return items_to_index

    def _get_items_to_index(self) -> list[tuple[str, str]]:
        """Get all files and their content chunks to index."""
        return self._get_items_to_index_for_files(list(self.codebase.files))

    def _get_changed_items(self) -> set[File]:
        """Get set of files that have changed since last index."""
        if not self.commit_hash:
            return set()

        # Get diffs between base commit and current state
        diffs = self.codebase.get_diffs(self.commit_hash)
        changed_files = set()

        for diff in diffs:
            if diff.a_path:
                file = self.codebase.get_file(diff.a_path)
                if file:
                    changed_files.add(file)
            if diff.b_path:
                file = self.codebase.get_file(diff.b_path)
                if file:
                    changed_files.add(file)

        return changed_files

    def _save_index(self, path: Path) -> None:
        """Save index data to disk."""
        with open(path, "wb") as f:
            pickle.dump({"E": self.E, "items": self.items, "commit_hash": self.commit_hash}, f)

    def _load_index(self, path: Path) -> None:
        """Load index data from disk."""
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.E = data["E"]
            self.items = data["items"]
            self.commit_hash = data["commit_hash"]

    def similarity_search(self, query: str, k: int = 5) -> list[tuple[File, float]]:
        """Find the k most similar files to a query.

        Args:
            query: The text to search for
            k: Number of results to return

        Returns:
            List of tuples (File, similarity_score) sorted by similarity
        """
        results = []
        for filepath, score in self._similarity_search_raw(query, k):
            # Handle chunked files
            base_path = filepath.split("#")[0]  # Remove chunk identifier if present
            try:
                if file := self.codebase.get_file(base_path):
                    results.append((file, score))
            except FileNotFoundError:
                pass  # Skip files that no longer exist

        return results

    def update(self) -> None:
        """Update embeddings for changed files only."""
        if self.E is None or self.items is None or self.commit_hash is None:
            msg = "No index to update. Call create() or load() first."
            raise ValueError(msg)

        # Get changed files
        changed_files = self._get_changed_items()
        if not changed_files:
            logger.info("No files have changed since last update")
            return

        logger.info(f"Found {len(changed_files)} changed files to update")

        # Get content for changed files only
        items_with_content = self._get_items_to_index_for_files(list(changed_files))

        if not items_with_content:
            logger.info("No valid content found in changed files")
            return

        items, contents = zip(*items_with_content)
        logger.info(f"Processing {len(contents)} chunks from changed files")
        new_embeddings = self._get_embeddings(contents)

        # Create mapping of items to their indices
        item_to_idx = {str(item): idx for idx, item in enumerate(self.items)}

        # Update embeddings
        num_updated = 0
        num_added = 0
        for item, embedding in zip(items, new_embeddings):
            item_key = str(item)
            if item_key in item_to_idx:
                # Update existing embedding
                self.E[item_to_idx[item_key]] = embedding
                num_updated += 1
            else:
                # Add new embedding
                self.E = np.vstack([self.E, embedding])
                self.items = np.append(self.items, item)
                num_added += 1

        logger.info(f"Updated {num_updated} existing embeddings and added {num_added} new embeddings")

        # Update commit hash
        self.commit_hash = self._get_current_commit()
