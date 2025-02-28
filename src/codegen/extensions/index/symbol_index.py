"""Symbol-level semantic code search index."""

import pickle
from pathlib import Path

import tiktoken
from openai import OpenAI
from tqdm import tqdm

from codegen.extensions.index.code_index import CodeIndex
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.symbol import Symbol
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


# TODO: WIP!
class SymbolIndex(CodeIndex):
    """A semantic search index over codebase symbols.

    This implementation indexes individual symbols (functions, classes, etc.)
    rather than entire files. This allows for more granular search results.
    """

    EMBEDDING_MODEL = "text-embedding-3-small"
    MAX_TOKENS_PER_TEXT = 8000  # Max tokens per individual text
    MAX_BATCH_TOKENS = 32000  # Max total tokens per API call
    BATCH_SIZE = 100  # Max number of texts per API call

    def __init__(self, codebase: Codebase):
        """Initialize the symbol index."""
        super().__init__(codebase)
        self.client = OpenAI()
        self.encoding = tiktoken.get_encoding("cl100k_base")

    @property
    def save_file_name(self) -> str:
        return "symbol_index_{commit}.pkl"

    def _batch_texts_by_tokens(self, texts: list[str]) -> list[list[str]]:
        """Batch texts to maximize tokens per API call while respecting limits.

        This tries to pack as many texts as possible into each batch while ensuring:
        1. No individual text exceeds MAX_TOKENS_PER_TEXT
        2. Total tokens in batch doesn't exceed MAX_BATCH_TOKENS
        3. Number of texts doesn't exceed BATCH_SIZE
        """
        batches = []
        current_batch = []
        current_tokens = 0

        for text in texts:
            # Get token count for this text
            tokens = self.encoding.encode(text)
            n_tokens = len(tokens)

            # If text is too long, truncate it
            if n_tokens > self.MAX_TOKENS_PER_TEXT:
                tokens = tokens[: self.MAX_TOKENS_PER_TEXT]
                text = self.encoding.decode(tokens)
                n_tokens = self.MAX_TOKENS_PER_TEXT

            # Check if adding this text would exceed batch limits
            if len(current_batch) + 1 > self.BATCH_SIZE or current_tokens + n_tokens > self.MAX_BATCH_TOKENS:
                # Current batch is full, start a new one
                if current_batch:
                    batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            # Add text to current batch
            current_batch.append(text)
            current_tokens += n_tokens

        # Add the last batch if not empty
        if current_batch:
            batches.append(current_batch)

        return batches

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for a batch of texts using OpenAI's API."""
        # Clean texts
        texts = [text.replace("\\n", " ") for text in texts]

        # Batch texts efficiently
        batches = self._batch_texts_by_tokens(texts)
        logger.info(f"Processing {len(texts)} texts in {len(batches)} batches")

        # Process batches with progress bar
        all_embeddings = []
        for batch in tqdm(batches, desc="Getting embeddings"):
            response = self.client.embeddings.create(model=self.EMBEDDING_MODEL, input=batch, encoding_format="float")
            all_embeddings.extend(data.embedding for data in response.data)

        return all_embeddings

    def _get_items_to_index(self) -> list[tuple[str, str]]:
        """Get all symbols and their content to index."""
        items_to_index = []
        symbols_to_process = [s for s in self.codebase.symbols if s.source]
        logger.info(f"Found {len(symbols_to_process)} symbols to index")

        # Process each symbol - no need to pre-truncate since _batch_texts_by_tokens handles it
        for symbol in symbols_to_process:
            symbol_id = f"{symbol.file.filepath}::{symbol.name}"
            items_to_index.append((symbol_id, symbol.source))

        logger.info(f"Total symbols to process: {len(items_to_index)}")
        return items_to_index

    def _get_changed_items(self) -> set[Symbol]:
        """Get set of symbols that have changed since last index."""
        if not self.commit_hash:
            return set()

        # Get diffs between base commit and current state
        diffs = self.codebase.get_diffs(self.commit_hash)
        changed_symbols = set()

        # Get all symbols from changed files
        for diff in diffs:
            for path in [diff.a_path, diff.b_path]:
                if not path:
                    continue
                file = self.codebase.get_file(path)
                if file:
                    changed_symbols.update(s for s in file.symbols if s.source)

        logger.info(f"Found {len(changed_symbols)} changed symbols")
        return changed_symbols

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

    def similarity_search(self, query: str, k: int = 5) -> list[tuple[Symbol, float]]:
        """Find the k most similar symbols to a query."""
        results = []
        for symbol_id, score in self._similarity_search_raw(query, k):
            # Parse the symbol identifier
            filepath, symbol_name = symbol_id.split("::")
            # Get the file and find the symbol
            if file := self.codebase.get_file(filepath):
                for symbol in file.symbols:
                    if symbol.name == symbol_name and symbol.source:
                        results.append((symbol, score))
                        break

        return results
