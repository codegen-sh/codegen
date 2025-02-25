from pathlib import Path

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_directory_init(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"mock_dir/example.py": "", "mock_dir/subdir/empty.py": ""},
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        # Get the directory and check its attributes
        directory = codebase.get_directory("mock_dir")
        assert directory.path == Path(tmpdir) / "mock_dir"
        assert directory.dirpath == "mock_dir"
        assert directory.parent is not None
        assert len(directory.items) == 2
        assert set(directory.item_names) == {"example.py", "subdir"}


def test_name_property(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"mock_dir/example.py": ""},
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        # Get the directory and check its name
        directory = codebase.get_directory("mock_dir")
        assert directory.name == "mock_dir"


def test_add_and_file(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"mock_dir/example.py": ""},
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        # Create a new file
        codebase.create_file("mock_dir/example_2.py", "print('Hello, world!')")
        codebase.commit()

        # Check that the file was added
        directory = codebase.get_directory("mock_dir")
        assert len(directory.files) == 2
        assert "example_2.py" in directory.item_names


def test_remove_file(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"mock_dir/example.py": ""},
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        # Remove the file
        file = codebase.get_file("mock_dir/example.py")
        file.remove()
        codebase.commit()

        # Check that the file was removed
        directory = codebase.get_directory("mock_dir", optional=True)
        assert directory is None


def test_get_file(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"mock_dir/example.py": ""},
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        # Get the directory and get the file
        directory = codebase.get_directory("mock_dir")
        mock_file = codebase.get_file("mock_dir/example.py")
        retrieved_file = directory.get_file("example.py")
        assert retrieved_file is mock_file

        # Case-insensitive match
        retrieved_file_ci = directory.get_file("EXAMPLE.PY", ignore_case=True)
        assert retrieved_file_ci is mock_file


def test_get_file_not_found(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"mock_dir/example.py": ""}) as codebase:
        # Get the directory and check that the file is not found
        directory = codebase.get_directory("mock_dir")
        assert directory.get_file("nonexistent.py", ignore_case=True) is None


def test_add_subdirectory(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"mock_dir/example.py": ""}) as codebase:
        # Get the directory and add a file in a subdirectory
        directory = codebase.get_directory("mock_dir")
        codebase.create_file("mock_dir/subdir/example.py", "print('Hello, world!')")
        codebase.commit()

        # Get the directory and check that the file is in the subdirectory
        directory = codebase.get_directory("mock_dir")
        assert directory.get_file("subdir/example.py") is not None

        # Get the subdirectory and check that the file is in the subdirectory
        subdir = codebase.get_directory("mock_dir/subdir")
        assert subdir.get_file("example.py") is not None


def test_remove_subdirectory(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"mock_dir/subdir/empty.py": ""}) as codebase:
        # Get the directory and remove the subdirectory
        directory = codebase.get_directory("mock_dir")
        subdir = codebase.get_directory("mock_dir/subdir")
        directory.remove()
        codebase.commit()

        # Check that the subdirectory was removed
        assert codebase.get_directory("mock_dir/subdir", optional=True) is None


def test_get_subdirectory(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"mock_dir/subdir/empty.py": ""}) as codebase:
        # Get the directory and get the subdirectory
        directory = codebase.get_directory("mock_dir")
        sub_dir = codebase.get_directory("mock_dir/subdir")
        retrieved_subdir = directory.get_subdirectory("subdir")
        assert retrieved_subdir is sub_dir


def test_update_filepath(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"mock_dir/example.py": ""}) as codebase:
        # Get the directory and update the filepath
        directory = codebase.get_directory("mock_dir")
        directory.update_filepath("new_mock_dir/new_mock_subdir")
        codebase.commit()

        # Check that the directory was updated
        directory = codebase.get_directory("new_mock_dir/new_mock_subdir")
        assert directory is not None
        assert codebase.get_directory("mock_dir", optional=True) is None
        assert directory.dirpath == "new_mock_dir/new_mock_subdir"
        assert directory.name == "new_mock_subdir"
        assert directory.path == Path(tmpdir) / "new_mock_dir/new_mock_subdir"
        assert directory.parent is not None
        assert len(directory.items) == 1
        assert "example.py" in directory.item_names

        # Check that the file was updated
        file = codebase.get_file("new_mock_dir/new_mock_subdir/example.py")
        assert file is not None
        assert codebase.get_file("mock_dir/example.py", optional=True) is None


def test_remove(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"mock_dir/example.py": ""}) as codebase:
        # Get the directory and remove it
        directory = codebase.get_directory("mock_dir")
        directory.remove()
        codebase.commit()

        # Check that the directory was removed
        assert codebase.get_directory("mock_dir", optional=True) is None
        assert codebase.get_file("mock_dir/example.py", optional=True) is None


def test_rename(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"mock_dir/example.py": ""}) as codebase:
        # Get the directory and rename it
        directory = codebase.get_directory("mock_dir")
        directory.rename("renamed_dir")
        codebase.commit()
        # Check that the directory was renamed
        directory = codebase.get_directory("renamed_dir")
        assert directory is not None
        assert codebase.get_directory("mock_dir", optional=True) is None
        assert directory.dirpath == "renamed_dir"
        assert directory.name == "renamed_dir"
        assert directory.path == Path(tmpdir) / "renamed_dir"
        assert directory.parent is not None
        assert len(directory.items) == 1
        assert "example.py" in directory.item_names

        # Check that the file was renamed
        file = codebase.get_file("renamed_dir/example.py")
        assert file is not None
        assert codebase.get_file("mock_dir/example.py", optional=True) is None


def test_contains(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"mock_dir/example.py": "", "mock_dir/subdir/empty.py": ""}) as codebase:
        # Get the directory and check the contains
        directory = codebase.get_directory("mock_dir")
        assert "subdir" in directory
        assert "example.py" in directory


def test_len(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"mock_dir/example.py": "", "mock_dir/subdir/empty.py": ""}) as codebase:
        # Get the directory and check the length
        directory = codebase.get_directory("mock_dir")
        assert len(directory) == 2


def test_unicode_in_filename(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"ascii.py": "print('Hello, world!')", "test/我很喜欢冰激淋/test-file 12'3_🍦.py": "print('Hello, world!')"},
        programming_language=ProgrammingLanguage.PYTHON,
        verify_output=True,
    ) as codebase:
        # Get the file and check the content
        file = codebase.get_file("test/我很喜欢冰激淋/test-file 12'3_🍦.py")
        assert file is not None
        assert file.content == "print('Hello, world!')"
