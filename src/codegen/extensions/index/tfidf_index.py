"""TF-IDF based code search index using pure numpy."""

import logging
import pickle
import re
from collections import Counter
from pathlib import Path

import numpy as np

from codegen import Codebase
from codegen.extensions.index.code_index import CodeIndex
from codegen.sdk.core.file import File

logger = logging.getLogger(__name__)


class TfidfVectorizer:
    """Simple TF-IDF vectorizer implementation using numpy."""

    def __init__(self, max_features: int = 10000, min_df: int = 1):
        """Initialize the vectorizer.

        Args:
            max_features: Maximum number of features (words) to keep
            min_df: Minimum document frequency for a word to be kept
        """
        self.max_features = max_features
        self.min_df = min_df
        self.vocabulary_ = {}
        self.idf_ = None
        # Match:
        # 1. CamelCase -> split into words (e.g., AuthenticationManager -> Authentication, Manager)
        # 2. snake_case -> split into words
        # 3. Preserve numbers in identifiers
        # 4. Handle acronyms (e.g., JWT, HTTP)
        self._word_pattern = re.compile(r"(?:[A-Z][a-z]+)|(?:[A-Z]{2,}(?=[A-Z][a-z]|\d|\W|$))|(?:[A-Z]{2,})|(?:[a-z]+)|(?:[A-Z](?=[a-z]))")

    def _tokenize(self, text: str) -> list[str]:
        """Convert text to tokens, handling code-specific patterns."""
        words = []
        for line in text.split("\n"):
            # Skip comments and empty lines
            line = line.strip()
            if line.startswith(("#", "//", "/*", "*", '"""', "'''")):
                continue

            # Find all word-like tokens
            for token in self._word_pattern.findall(line):
                if "_" in token:
                    # Handle snake_case
                    words.extend(part.lower() for part in token.split("_") if part)
                else:
                    # Handle CamelCase and other patterns
                    words.append(token.lower())

        return words

    def fit_transform(self, texts: list[str]) -> np.ndarray:
        """Build vocabulary and transform texts to TF-IDF matrix."""
        # Count words in each document
        doc_words = [Counter(self._tokenize(text)) for text in texts]

        # Build vocabulary with document frequency filtering
        word_doc_freq = Counter()
        for doc in doc_words:
            word_doc_freq.update(doc.keys())

        # Filter by document frequency and take top features
        valid_words = {word for word, freq in word_doc_freq.items() if freq >= self.min_df}
        top_words = sorted(valid_words, key=lambda w: word_doc_freq[w], reverse=True)[: self.max_features]

        # Create vocabulary mapping
        self.vocabulary_ = {word: idx for idx, word in enumerate(top_words)}

        # Create TF matrix
        X = np.zeros((len(texts), len(self.vocabulary_)))
        for i, text in enumerate(texts):
            word_counts = Counter(self._tokenize(text))
            doc_length = sum(word_counts.values())
            if doc_length > 0:  # Avoid division by zero
                for word, count in word_counts.items():
                    if word in self.vocabulary_:
                        idx = self.vocabulary_[word]
                        X[i, idx] = count / doc_length

        # Calculate and apply IDF
        n_docs = len(texts)
        self.idf_ = np.zeros(len(self.vocabulary_))
        for word, idx in self.vocabulary_.items():
            doc_freq = word_doc_freq[word]
            self.idf_[idx] = np.log(n_docs / (1 + doc_freq)) + 1

        X *= self.idf_

        # Normalize rows
        norms = np.linalg.norm(X, axis=1)
        norms[norms == 0] = 1  # Avoid division by zero
        X /= norms[:, np.newaxis]

        return X

    def transform(self, texts: list[str]) -> np.ndarray:
        """Transform texts to TF-IDF matrix."""
        if not self.vocabulary_:
            msg = "Vocabulary not built. Call fit_transform first."
            raise ValueError(msg)

        # Create TF matrix
        X = np.zeros((len(texts), len(self.vocabulary_)))
        for i, text in enumerate(texts):
            word_counts = Counter(self._tokenize(text))
            doc_length = sum(word_counts.values())
            if doc_length > 0:  # Avoid division by zero
                for word, count in word_counts.items():
                    if word in self.vocabulary_:
                        idx = self.vocabulary_[word]
                        X[i, idx] = count / doc_length

        # Apply IDF weights
        X *= self.idf_

        # Normalize rows
        norms = np.linalg.norm(X, axis=1)
        norms[norms == 0] = 1  # Avoid division by zero
        X /= norms[:, np.newaxis]

        return X

    @property
    def vocabulary(self) -> dict[str, int]:
        """Get the current vocabulary mapping."""
        if not self.vocabulary_:
            msg = "Vocabulary not built. Call fit_transform first."
            raise ValueError(msg)
        return dict(self.vocabulary_)  # Return a copy to prevent modification


class TfidfIndex(CodeIndex):
    """A TF-IDF based search index over codebase files.

    This implementation uses a pure numpy-based TF-IDF vectorizer,
    making it fast and lightweight with no additional dependencies.
    """

    def __init__(self, codebase: Codebase):
        """Initialize the TF-IDF index."""
        super().__init__(codebase)
        self.vectorizer = TfidfVectorizer(
            max_features=10000,  # Limit vocabulary size
            min_df=1,  # Allow words that appear in just one document
        )

    @property
    def save_file_name(self) -> str:
        return "tfidf_index_{commit}.pkl"

    @property
    def vocabulary(self) -> dict[str, int]:
        """Get the current vocabulary mapping."""
        return self.vectorizer.vocabulary

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get TF-IDF embeddings for a batch of texts."""
        # If this is the first time, fit the vectorizer
        if not hasattr(self.vectorizer, "vocabulary_") or not self.vectorizer.vocabulary_:
            logger.info("Building vocabulary and computing initial embeddings...")
            return self.vectorizer.fit_transform(texts)

        logger.info("Computing embeddings with existing vocabulary...")
        return self.vectorizer.transform(texts)

    def _get_items_to_index(self) -> list[tuple[str, str]]:
        """Get all files and their content to index."""
        items_to_index = []
        # Only process text files
        files_to_process = []
        for file in self.codebase.files:
            try:
                if file.content and not file.filepath.startswith(".codegen"):
                    files_to_process.append(file)
            except ValueError:
                # Skip binary files that raise ValueError on content access
                continue

        logger.info(f"Found {len(files_to_process)} files to index")

        # Process each file
        for file in files_to_process:
            items_to_index.append((file.filepath, file.content))

        logger.info(f"Total files to process: {len(items_to_index)}")
        return items_to_index

    def _get_changed_items(self) -> set[File]:
        """Get set of files that have changed since last index."""
        if not self.commit_hash:
            return set()

        # Get diffs between base commit and current state
        diffs = self.codebase.get_diffs(self.commit_hash)
        changed_files = set()

        # Get all changed files
        for diff in diffs:
            for path in [diff.a_path, diff.b_path]:
                if not path:
                    continue
                file = self.codebase.get_file(path)
                # Only include non-binary files
                if file and not getattr(file, "_binary", False) and not file.filepath.startswith(".codegen") and file.content:
                    changed_files.add(file)

        logger.info(f"Found {len(changed_files)} changed files")
        return changed_files

    def _save_index(self, path: Path) -> None:
        """Save index data to disk."""
        with open(path, "wb") as f:
            pickle.dump({"E": self.E, "items": self.items, "commit_hash": self.commit_hash, "vectorizer": self.vectorizer}, f)

    def _load_index(self, path: Path) -> None:
        """Load index data from disk."""
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.E = data["E"]
            self.items = data["items"]
            self.commit_hash = data["commit_hash"]
            self.vectorizer = data["vectorizer"]

    def similarity_search(self, query: str, k: int = 5) -> list[tuple[File, float]]:
        """Find the k most similar files to a query."""
        results = []
        for filepath, score in self._similarity_search_raw(query, k):
            if file := self.codebase.get_file(filepath):
                results.append((file, score))

        return results

    def _similarity_search_raw(self, query: str, k: int = 5) -> list[tuple[str, float]]:
        """Find the k most similar items to a query.

        This implementation uses cosine similarity between TF-IDF vectors.
        """
        if self.E is None or self.items is None:
            msg = "No embeddings available. Call create() or load() first."
            raise ValueError(msg)

        # Get query embedding
        query_embedding = self.vectorizer.transform([query])[0]  # Already dense, no need for toarray()

        # Calculate cosine similarities
        similarities = np.dot(self.E, query_embedding) / (np.linalg.norm(self.E, axis=1) * np.linalg.norm(query_embedding))

        # Get top k results
        top_k_indices = np.argsort(similarities)[-k:][::-1]

        return [(self.items[i], float(similarities[i])) for i in top_k_indices]
