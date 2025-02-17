from pathlib import Path

import numpy as np
import pytest

from codegen.extensions.index.file_index import FileIndex
from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_file_index_lifecycle(tmpdir) -> None:
    # language=python
    content1 = """
def hello():
    print("Hello, world!")

def goodbye():
    print("Goodbye, world!")
"""

    # language=python
    content2 = """
def greet(name: str):
    print(f"Hi {name}!")
"""

    with get_codebase_session(tmpdir=tmpdir, files={"greetings.py": content1, "hello.py": content2}) as codebase:
        # Test construction and initial indexing
        index = FileIndex(codebase)
        index.create()

        # Verify initial state
        assert index.E is not None
        assert index.items is not None
        assert len(index.items) == 2  # Both files should be indexed
        assert index.commit_hash is not None

        # Test similarity search
        results = index.similarity_search("greeting someone", k=2)
        assert len(results) == 2
        # The greet function should be most relevant to greeting
        assert any("hello.py" in file.filepath for file, _ in results)

        # Test saving
        save_dir = Path(tmpdir) / ".codegen"
        index.save()
        assert save_dir.exists()
        saved_files = list(save_dir.glob("file_index_*.pkl"))
        assert len(saved_files) == 1

        # Test loading
        new_index = FileIndex(codebase)
        new_index.load(saved_files[0])
        assert np.array_equal(index.E, new_index.E)
        assert np.array_equal(index.items, new_index.items)
        assert index.commit_hash == new_index.commit_hash

        # Test updating after file changes
        # Add a new function to greetings.py
        greetings_file = codebase.get_file("greetings.py")
        new_content = greetings_file.content + "\n\ndef welcome():\n    print('Welcome!')\n"
        greetings_file.edit(new_content)

        # Update the index
        index.update()

        # Verify the update
        assert len(index.items) >= 2  # Should have at least the original files

        # Search for the new content
        results = index.similarity_search("welcome message", k=2)
        assert len(results) == 2
        # The updated greetings.py should be relevant now
        assert any("greetings.py" in file.filepath for file, _ in results)


def test_file_index_empty_file(tmpdir) -> None:
    """Test that the file index handles empty files gracefully."""
    with get_codebase_session(tmpdir=tmpdir, files={"empty.py": ""}) as codebase:
        index = FileIndex(codebase)
        index.create()
        assert len(index.items) == 0  # Empty file should be skipped


def test_file_index_large_file(tmpdir) -> None:
    """Test that the file index handles files larger than the token limit."""
    # Create a large file by repeating a simple function many times
    large_content = "def f():\n    print('test')\n\n" * 10000

    with get_codebase_session(tmpdir=tmpdir, files={"large.py": large_content}) as codebase:
        index = FileIndex(codebase)
        index.create()

        # Should have multiple chunks for the large file
        assert len([item for item in index.items if "large.py" in item]) > 1

        # Test searching in large file
        results = index.similarity_search("function that prints test", k=1)
        assert len(results) == 1
        assert "large.py" in results[0][0].filepath


def test_file_index_invalid_operations(tmpdir) -> None:
    """Test that the file index properly handles invalid operations."""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": "print('test')"}) as codebase:
        index = FileIndex(codebase)

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


def test_file_index_binary_files(tmpdir) -> None:
    """Test that the file index properly handles binary files."""
    # Create a binary file
    binary_content = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])  # PNG header
    binary_path = Path(tmpdir) / "test.png"
    binary_path.write_bytes(binary_content)

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": "print('test')", "test.png": binary_content}) as codebase:
        index = FileIndex(codebase)
        index.create()

        # Should only index the Python file
        assert len(index.items) == 1
        assert all("test.py" in item for item in index.items)
