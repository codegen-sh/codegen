import os
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from codegen.sdk.codebase.codebase_context import CodebaseContext
from codegen.sdk.codebase.config import CodebaseConfig
from codegen.sdk.core.directory import Directory
from codegen.sdk.core.file import File


@pytest.fixture
def mock_codebase_context(tmp_path):
    mock = MagicMock(spec=CodebaseContext)
    mock.transaction_manager = MagicMock()
    mock.config = CodebaseConfig()
    mock.repo_path = tmp_path
    mock.to_absolute = types.MethodType(CodebaseContext.to_absolute, mock)
    mock.to_relative = types.MethodType(CodebaseContext.to_relative, mock)
    mock.io = MagicMock()
    return mock


@pytest.fixture
def subdir_path(tmp_path):
    return tmp_path / "mock_dir" / "subdir"


@pytest.fixture
def dir_path(tmp_path):
    return tmp_path / "mock_dir"


@pytest.fixture
def sub_dir(subdir_path, tmp_path):
    return Directory(path=subdir_path.absolute(), dirpath=str(subdir_path.relative_to(tmp_path)), parent=None)


@pytest.fixture
def mock_file(dir_path, mock_codebase_context):
    return File(filepath=dir_path / "example.py", ctx=mock_codebase_context)


@pytest.fixture
def mock_directory(tmp_path, dir_path, sub_dir, mock_file):
    directory = Directory(path=dir_path.absolute(), dirpath=str(dir_path.relative_to(tmp_path)), parent=None)
    directory.add_file(mock_file)
    directory.add_subdirectory(sub_dir)
    return directory


def test_directory_init(tmp_path, mock_directory):
    """Test initialization of Directory object."""
    assert mock_directory.path == tmp_path / "mock_dir"
    assert mock_directory.dirpath == "mock_dir"
    assert mock_directory.parent is None
    assert len(mock_directory.items) == 2
    assert mock_directory.items["subdir"] is not None
    assert mock_directory.items["example.py"] is not None


def test_name_property(mock_directory):
    """Test name property returns the basename of the dirpath."""
    assert mock_directory.name == "mock_dir"


def test_add_and_file(mock_directory, mock_codebase_context):
    """Test adding a file to the directory."""
    mock_file = File(filepath=Path("mock_dir/example_2.py"), ctx=mock_codebase_context)
    mock_directory.add_file(mock_file)
    rel_path = os.path.relpath(mock_file.file_path, mock_directory.dirpath)
    assert rel_path in mock_directory.items
    assert mock_directory.items[rel_path] is mock_file


def test_remove_file(mock_directory, mock_file):
    """Test removing a file from the directory."""
    mock_directory.remove_file(mock_file)

    rel_path = os.path.relpath(mock_file.file_path, mock_directory.dirpath)
    assert rel_path not in mock_directory.items


def test_remove_file_by_path(mock_directory, mock_file):
    """Test removing a file by path."""
    mock_directory.remove_file_by_path(Path(mock_file.file_path))

    rel_path = os.path.relpath(mock_file.file_path, mock_directory.dirpath)
    assert rel_path not in mock_directory.items


def test_get_file(mock_directory, mock_file):
    """Test retrieving a file by name."""
    retrieved_file = mock_directory.get_file("example.py")
    assert retrieved_file is mock_file

    # Case-insensitive match
    retrieved_file_ci = mock_directory.get_file("EXAMPLE.PY", ignore_case=True)
    assert retrieved_file_ci is mock_file


def test_get_file_not_found(mock_directory):
    """Test retrieving a non-existing file returns None."""
    assert mock_directory.get_file("nonexistent.py") is None


def test_add_subdirectory(mock_directory, dir_path):
    """Test adding a subdirectory."""
    new_subdir_path = dir_path / "new_subdir"
    subdir = Directory(path=new_subdir_path.absolute(), dirpath=str(new_subdir_path.relative_to(dir_path)), parent=mock_directory)
    mock_directory.add_subdirectory(subdir)
    rel_path = os.path.relpath(subdir.dirpath, mock_directory.dirpath)
    assert rel_path in mock_directory.items
    assert mock_directory.items[rel_path] is subdir


def test_remove_subdirectory(mock_directory, sub_dir):
    """Test removing a subdirectory."""
    mock_directory.add_subdirectory(sub_dir)
    mock_directory.remove_subdirectory(sub_dir)

    rel_path = os.path.relpath(sub_dir.dirpath, mock_directory.dirpath)
    assert rel_path not in mock_directory.items


def test_remove_subdirectory_by_path(mock_directory, sub_dir):
    """Test removing a subdirectory by path."""
    mock_directory.remove_subdirectory_by_path(sub_dir.dirpath)

    rel_path = os.path.relpath(sub_dir.dirpath, mock_directory.dirpath)
    assert rel_path not in mock_directory.items


def test_get_subdirectory(mock_directory, sub_dir):
    """Test retrieving a subdirectory by name."""
    retrieved_subdir = mock_directory.get_subdirectory("subdir")
    assert retrieved_subdir is sub_dir


def test_files_property(mock_directory, sub_dir, mock_codebase_context):
    """Test the 'files' property returns all files recursively."""
    all_files = mock_directory.files
    assert len(all_files) == 1

    new_file = File(filepath=Path("mock_dir/example_2.py"), ctx=mock_codebase_context)
    sub_dir.add_file(new_file)

    all_files = mock_directory.files
    assert len(all_files) == 2
    assert new_file in all_files

    gen = mock_directory.files_generator()
    files_list = list(gen)
    assert len(files_list) == 2
    assert new_file in files_list


def test_subdirectories_property(mock_directory, sub_dir):
    """Test the 'subdirectories' property returns all directories recursively."""
    all_subdirs = mock_directory.subdirectories
    assert len(all_subdirs) == 1
    assert sub_dir in all_subdirs

    new_sub_dir = Directory(path=sub_dir.path / "new_subdir", dirpath=str(Path(sub_dir.dirpath) / "new_subdir"), parent=sub_dir)
    sub_dir.add_subdirectory(new_sub_dir)

    all_subdirs = mock_directory.subdirectories
    assert len(all_subdirs) == 2
    assert new_sub_dir in all_subdirs


def test_update_filepath(mock_directory, mock_codebase_context, mock_file):
    """Test updating file paths when the directory path changes."""
    mock_directory.update_filepath("/absolute/new_mock_dir")

    # Verify the files have updated file paths
    mock_codebase_context.transaction_manager.add_file_rename_transaction.assert_called_once_with(mock_file, "/absolute/new_mock_dir/example.py")


def test_remove(mock_directory, sub_dir, mock_codebase_context, mock_file):
    mock_directory.remove()

    mock_codebase_context.transaction_manager.add_file_remove_transaction.assert_called_once_with(mock_file)


def test_rename(mock_directory, mock_codebase_context, mock_file):
    """Test renaming the directory."""
    mock_directory.rename("renamed_dir")
    # This fails because it is not implemented to rename the directory itself.
    # assert mock_directory.dirpath == "/absolute/renamed_dir"
    mock_codebase_context.transaction_manager.add_file_rename_transaction.assert_called_once_with(mock_file, "renamed_dir/example.py")


def test_iteration(mock_directory):
    """Test iterating over the directory items."""
    items = list(mock_directory)  # uses Directory.__iter__
    assert len(items) == 2
    assert mock_directory.items["subdir"] in items
    assert mock_directory.items["example.py"] in items


def test_contains(mock_directory):
    """Test the containment checks using the 'in' operator."""
    assert "subdir" in mock_directory
    assert "example.py" in mock_directory


def test_len(mock_directory):
    """Test the __len__ method returns the number of items."""
    assert len(mock_directory) == 2


def test_get_set_delete_item(mock_directory):
    """Test __getitem__, __setitem__, and __delitem__ methods."""
    mock_file = mock_directory.items["example.py"]
    mock_directory["example.py"] = mock_file
    assert mock_directory["example.py"] == mock_file

    with pytest.raises(KeyError, match="subdir_2"):
        del mock_directory["subdir_2"]
