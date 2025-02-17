"""Symbol-level semantic code search index."""

import pickle
from pathlib import Path

import tiktoken
from openai import OpenAI
from tqdm import tqdm

from codegen import Codebase
from codegen.extensions.index.code_index import CodeIndex
from codegen.sdk.core.symbol import Symbol


class SymbolIndex(CodeIndex):
    """A semantic search index over codebase symbols.

    This implementation indexes individual symbols (functions, classes, etc.)
    rather than entire files. This allows for more granular search results
    and better context preservation.
    """

    EMBEDDING_MODEL = "text-embedding-3-small"
    MAX_TOKENS = 8000
    BATCH_SIZE = 100

    def __init__(self, codebase: Codebase):
        """Initialize the symbol index.

        Args:
            codebase: The codebase to index
        """
        super().__init__(codebase)
        self.client = OpenAI()
        self.encoding = tiktoken.get_encoding("cl100k_base")

    @property
    def save_file_name(self) -> str:
        return "symbol_index_{commit}.pkl"

    def _get_symbol_content(self, symbol: Symbol) -> str:
        """Get the content to embed for a symbol.

        This includes:
        1. The symbol's code
        2. Its docstring if available
        3. The symbol's name and type
        4. Parent class/module context if applicable
        """
        content_parts = []

        # Add symbol type and name
        content_parts.append(f"Type: {symbol.symbol_type.value}")
        content_parts.append(f"Name: {symbol.name}")

        # Add parent context if available
        if hasattr(symbol, "parent") and symbol.parent:
            content_parts.append(f"Parent: {symbol.parent.name}")

        # Add docstring if available
        if hasattr(symbol, "docstring") and symbol.docstring:
            content_parts.append(f"Documentation: {symbol.docstring}")

        # Add the actual code
        if hasattr(symbol, "code"):
            content_parts.append(f"Code: {symbol.code}")

        return "\n".join(content_parts)

    def _split_by_tokens(self, text: str) -> list[str]:
        """Split text into chunks that fit within token limit."""
        tokens = self.encoding.encode(text)
        if len(tokens) <= self.MAX_TOKENS:
            return [text]

        # For symbols, we don't split - we truncate
        # This is because splitting a symbol's content could break context
        truncated_tokens = tokens[: self.MAX_TOKENS]
        return [self.encoding.decode(truncated_tokens)]

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for a batch of texts using OpenAI's API."""
        # Clean texts
        texts = [text.replace("\\n", " ") for text in texts]

        response = self.client.embeddings.create(model=self.EMBEDDING_MODEL, input=texts, encoding_format="float")
        return [data.embedding for data in response.data]

    def _get_items_to_index(self) -> list[tuple[str, str]]:
        """Get all symbols and their content to index."""
        items_to_index = []

        for file in tqdm(self.codebase.files, desc="Collecting symbols"):
            for symbol in file.symbols:
                content = self._get_symbol_content(symbol)
                if not content:  # Skip empty symbols
                    continue

                # Get the potentially truncated content
                processed_content = self._split_by_tokens(content)[0]
                # Store symbol identifier (could be filepath + symbol name or a unique id)
                symbol_id = f"{file.filepath}::{symbol.name}"
                items_to_index.append((symbol_id, processed_content))

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
                    changed_symbols.update(file.symbols)

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
                    if symbol.name == symbol_name:
                        results.append((symbol, score))
                        break

        return results
