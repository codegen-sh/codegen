from pathlib import Path

import numpy as np
import pytest

from codegen.extensions.index.tfidf_index import TfidfIndex
from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_tfidf_index_lifecycle(tmpdir) -> None:
    # language=python
    content1 = """
def authenticate_user(username: str, password: str):
    '''Authenticate a user with username and password'''
    if check_credentials(username, password):
        return create_session(username)
    raise AuthenticationError("Invalid credentials")
"""

    # language=python
    content2 = """
def process_payment(amount: float, user_id: str):
    '''Process a payment for the given amount'''
    if validate_payment(amount):
        return charge_user(user_id, amount)
    raise PaymentError("Invalid payment amount")
"""

    with get_codebase_session(tmpdir=tmpdir, files={"auth.py": content1, "payment.py": content2}) as codebase:
        # Test construction and initial indexing
        index = TfidfIndex(codebase)
        index.create()

        # Verify initial state
        assert index.E is not None
        assert index.items is not None
        assert len(index.items) == 2  # Both files should be indexed
        assert index.commit_hash is not None
        assert hasattr(index.vectorizer, "vocabulary_")  # Vectorizer should be fitted

        # Test similarity search
        results = index.similarity_search("user authentication login", k=2)
        assert len(results) == 2
        # The auth file should be most relevant to authentication
        assert results[0][0].filepath == "auth.py"
        assert results[0][1] > results[1][1]  # Higher similarity score

        # Test saving
        save_dir = Path(tmpdir) / ".codegen"
        index.save()
        assert save_dir.exists()
        saved_files = list(save_dir.glob("tfidf_index_*.pkl"))
        assert len(saved_files) == 1

        # Test loading
        new_index = TfidfIndex(codebase)
        new_index.load(saved_files[0])
        assert np.array_equal(index.E, new_index.E)
        assert np.array_equal(index.items, new_index.items)
        assert index.commit_hash == new_index.commit_hash
        assert hasattr(new_index.vectorizer, "vocabulary_")
        assert new_index.vectorizer.vocabulary_ == index.vectorizer.vocabulary_

        # Test updating after file changes
        auth_file = codebase.get_file("auth.py")
        new_content = auth_file.content + "\n\ndef logout_user(session_id: str):\n    '''End user session'''\n"
        auth_file.edit(new_content)

        # Update the index
        index.update()

        # Verify the update
        assert len(index.items) == 2  # Should still have same number of files

        # Search for the new content
        results = index.similarity_search("user logout session", k=2)
        assert len(results) == 2
        # The auth file should be most relevant to logout
        assert results[0][0].filepath == "auth.py"


def test_tfidf_index_empty_file(tmpdir) -> None:
    """Test that the TF-IDF index handles empty files gracefully."""
    with get_codebase_session(tmpdir=tmpdir, files={"empty.py": ""}) as codebase:
        index = TfidfIndex(codebase)
        index.create()
        assert len(index.items) == 0  # Empty file should be skipped


def test_tfidf_index_large_file(tmpdir) -> None:
    """Test that the TF-IDF index handles large files."""
    # Create a large file by repeating a simple function many times
    large_content = "def authenticate():\n    print('auth')\n\n" * 1000

    with get_codebase_session(tmpdir=tmpdir, files={"large.py": large_content}) as codebase:
        index = TfidfIndex(codebase)
        index.create()

        # Test searching in large file
        results = index.similarity_search("authentication function", k=1)
        assert len(results) == 1
        assert results[0][0].filepath == "large.py"


def test_tfidf_index_invalid_operations(tmpdir) -> None:
    """Test that the TF-IDF index properly handles invalid operations."""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": "print('test')"}) as codebase:
        index = TfidfIndex(codebase)

        # Test searching before creating index
        with pytest.raises(ValueError, match="No embeddings available"):
            index.similarity_search("test")

        # Test saving before creating index
        with pytest.raises(ValueError, match="No embeddings to save"):
            index.save()

        # Test updating before creating index
        with pytest.raises(ValueError, match="No index to update"):
            index.update()

        # Test loading from non-existent path
        with pytest.raises(FileNotFoundError):
            index.load("nonexistent.pkl")


def test_tfidf_index_binary_files(tmpdir) -> None:
    """Test that the TF-IDF index properly handles binary files."""
    # Create a binary file
    binary_content = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])  # PNG header
    binary_path = Path(tmpdir) / "test.png"
    binary_path.write_bytes(binary_content)

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": "print('test')", "test.png": binary_content}) as codebase:
        index = TfidfIndex(codebase)
        index.create()

        # Should only index the Python file
        assert len(index.items) == 1
        assert all("test.py" in item for item in index.items)


def test_tfidf_tokenization(tmpdir) -> None:
    """Test that the TF-IDF tokenizer properly handles code patterns."""
    # language=python
    content1 = """
class AuthenticationManager:
    '''Handles user authentication'''

    def check_credentials(self, user_name: str, password_hash: str) -> bool:
        return self._validate_user_credentials(user_name, password_hash)
"""

    # language=python
    content2 = """
def authenticate_user(username: str, password: str):
    '''Authenticate a user with username and password'''
    if check_credentials(username, password):
        return create_session(username)
    raise AuthenticationError("Invalid credentials")
"""

    with get_codebase_session(tmpdir=tmpdir, files={"auth.py": content1, "login.py": content2}) as codebase:
        index = TfidfIndex(codebase)
        index.create()

        # Check that the vocabulary contains expected tokens
        vocab = index.vocabulary
        expected_tokens = {
            "authentication",
            "manager",  # CamelCase class name
            "check",
            "credentials",  # snake_case function name
            "user",
            "name",  # parameter names
            "password",
            "hash",
            "validate",
            "authenticate",  # Mixed case and abbreviations
            "session",
            "return",
            "self",
            "def",
            "class",  # Common Python keywords
        }

        # All expected tokens should be in vocabulary
        assert all(token in vocab for token in expected_tokens), f"Missing tokens: {expected_tokens - set(vocab.keys())}"

        # Test searching with different word forms
        results = index.similarity_search("user authentication", k=1)
        assert len(results) == 1
        assert results[0][0].filepath in {"auth.py", "login.py"}

        results = index.similarity_search("validate credentials", k=1)
        assert len(results) == 1
        assert results[0][0].filepath in {"auth.py", "login.py"}
