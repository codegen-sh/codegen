"""File-level semantic code search index."""

import pickle
from pathlib import Path
from typing import Optional

import modal
import numpy as np
import tiktoken
from openai import OpenAI
from tqdm import tqdm

from codegen.extensions.index.code_index import CodeIndex
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import File
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class FileIndex(CodeIndex):
    """A semantic search index over codebase files.

    This implementation indexes entire files, splitting large files into chunks
    if they exceed the token limit.
    """

    EMBEDDING_MODEL = "text-embedding-3-small"
    MAX_TOKENS = 8000
    BATCH_SIZE = 100
    USE_MODAL_DICT = True  # Flag to control whether to use Modal Dict

    def __init__(self, codebase: Codebase):
        """Initialize the file index.

        Args:
            codebase: The codebase to index
        """
        super().__init__(codebase)
        self.client = OpenAI()
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def set_use_modal_dict(self, use_modal: bool) -> None:
        """Set whether to use Modal Dict for storage.

        Args:
            use_modal: Whether to use Modal Dict for storage
        """
        self.USE_MODAL_DICT = use_modal
        logger.info(f"Modal Dict storage {'enabled' if use_modal else 'disabled'}")

    @property
    def save_file_name(self) -> str:
        return "file_index_{commit}.pkl"

    @property
    def modal_dict_id(self) -> str:
        """Get the Modal Dict ID based on the same naming convention as the pickle file."""
        if not self.commit_hash:
            return "file_index_latest"
        return f"file_index_{self.commit_hash}"

    def delete_modal_dict(self) -> bool:
        """Delete the Modal Dict storage for this index.

        Returns:
            bool: True if successfully deleted, False otherwise
        """
        if not self.USE_MODAL_DICT:
            logger.warning("Modal Dict storage is disabled")
            return False

        try:
            dict_id = self.modal_dict_id
            logger.info(f"Deleting Modal Dict: {dict_id}")

            # Check if the dict exists before trying to delete
            try:
                # Use modal.Dict.delete to properly delete the dict
                modal.Dict.delete(dict_id)
                logger.info(f"Successfully deleted Modal Dict: {dict_id}")
                return True
            except Exception as e:
                logger.info(f"Modal Dict {dict_id} does not exist or cannot be deleted: {e}")
                return False
        except Exception as e:
            logger.exception(f"Failed to delete Modal Dict: {e}")
            return False

    def modal_dict_exists(self, commit_hash: Optional[str] = None) -> bool:
        """Check if a Modal Dict exists for a specific commit.

        Args:
            commit_hash: The commit hash to check, or None to use the current commit

        Returns:
            bool: True if the Modal Dict exists, False otherwise
        """
        if not self.USE_MODAL_DICT:
            return False

        try:
            # Use provided commit hash or current one
            old_commit = self.commit_hash
            if commit_hash is not None:
                self.commit_hash = commit_hash

            dict_id = self.modal_dict_id

            # Restore original commit hash
            if commit_hash is not None:
                self.commit_hash = old_commit

            try:
                # Try to access the dict - this will raise an exception if it doesn't exist
                modal_dict = modal.Dict.from_name(dict_id, create_if_missing=False)
                # Check if our data is in the dict
                return "index_data" in modal_dict
            except Exception:
                return False
        except Exception:
            return False

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
        """Save index data to disk and optionally to Modal Dict."""
        # Save to local pickle file
        with open(path, "wb") as f:
            pickle.dump({"E": self.E, "items": self.items, "commit_hash": self.commit_hash}, f)

        # Save to Modal Dict if enabled
        if self.USE_MODAL_DICT:
            try:
                dict_id = self.modal_dict_id
                logger.info(f"Saving index to Modal Dict: {dict_id}")

                # Convert numpy arrays to lists for JSON serialization
                modal_data = {"E": self.E.tolist() if self.E is not None else None, "items": self.items.tolist() if self.items is not None else None, "commit_hash": self.commit_hash}

                # Create or update Modal Dict
                # Note: from_name is lazy, so we need to explicitly set the data
                modal_dict = modal.Dict.from_name(dict_id, create_if_missing=True)
                modal_dict["index_data"] = modal_data

                logger.info(f"Successfully saved index to Modal Dict: {dict_id}")
            except Exception as e:
                logger.exception(f"Failed to save index to Modal Dict: {e}")

    def _load_index(self, path: Path) -> None:
        """Load index data from disk or Modal Dict."""
        # Try loading from Modal Dict first if enabled
        if self.USE_MODAL_DICT:
            try:
                dict_id = self.modal_dict_id
                logger.info(f"Attempting to load index from Modal Dict: {dict_id}")

                # from_name is lazy, so we need to check if the dict exists first
                try:
                    modal_dict = modal.Dict.from_name(dict_id, create_if_missing=False)
                    # Check if the dict contains our data
                    if "index_data" in modal_dict:
                        data = modal_dict["index_data"]

                        # Convert lists back to numpy arrays
                        self.E = np.array(data["E"]) if data["E"] is not None else None
                        self.items = np.array(data["items"]) if data["items"] is not None else None
                        self.commit_hash = data["commit_hash"]

                        logger.info(f"Successfully loaded index from Modal Dict: {dict_id}")
                        return
                    else:
                        logger.info(f"No index data found in Modal Dict: {dict_id}")
                except Exception as e:
                    logger.warning(f"Modal Dict {dict_id} not found or error accessing it: {e}")
            except Exception as e:
                logger.warning(f"Failed to load index from Modal Dict, falling back to local file: {e}")

        # Fall back to loading from local file
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
                self.E = data["E"]
                self.items = data["items"]
                self.commit_hash = data["commit_hash"]
                logger.info(f"Loaded index from local file: {path}")
        except Exception as e:
            logger.exception(f"Failed to load index from local file: {e}")
            raise

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

        # Save updated index to Modal Dict if enabled
        if self.USE_MODAL_DICT and (num_updated > 0 or num_added > 0):
            try:
                dict_id = self.modal_dict_id
                logger.info(f"Updating index in Modal Dict: {dict_id}")

                # Convert numpy arrays to lists for JSON serialization
                modal_data = {"E": self.E.tolist() if self.E is not None else None, "items": self.items.tolist() if self.items is not None else None, "commit_hash": self.commit_hash}

                # Create or update Modal Dict
                modal_dict = modal.Dict.from_name(dict_id, create_if_missing=True)
                modal_dict["index_data"] = modal_data

                logger.info(f"Successfully updated index in Modal Dict: {dict_id}")
            except Exception as e:
                logger.exception(f"Failed to update index in Modal Dict: {e}")
