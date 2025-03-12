import os
import sys

import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.file import File, SourceFile
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_file(tmpdir) -> None:
    file1_source = "Hello world!"
    file2_source = "print(123)"
    file3_source = b"\x89PNG"
    with get_codebase_session(tmpdir=tmpdir, files={"file1.txt": file1_source, "file2.py": file2_source, "file3.bin": file3_source}) as codebase:
        file1 = codebase.get_file("file1.txt")
        assert isinstance(file1, File)
        assert not isinstance(file1, SourceFile)
        assert file1 is not None
        assert file1.filepath == "file1.txt"
        assert file1.content == file1_source
        assert file1.is_binary is False

        file2 = codebase.get_file("file2.py")
        assert isinstance(file2, SourceFile)
        assert file2 is not None
        assert file2.filepath == "file2.py"
        assert file2.content == file2_source
        assert file2.is_binary is False

        file3 = codebase.get_file("file3.bin")
        assert isinstance(file3, File)
        assert not isinstance(file3, SourceFile)
        assert file3 is not None
        assert file3.filepath == "file3.bin"
        assert file3.is_binary is True
        assert file3.content_bytes == file3_source
        with pytest.raises(ValueError):
            codebase.get_file("file4.txt")
        with pytest.raises(ValueError):
            codebase.get_directory("file4/")


def test_codebase_files(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": "print(123)", "file2.py": "print(456)", "file3.bin": b"\x89PNG", "file4": "Hello world!"}) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")
        file3 = codebase.get_file("file3.bin")
        file4 = codebase.get_file("file4")

        assert len(codebase.files) == 2
        assert {f for f in codebase.files} == {file1, file2}

        assert len(codebase.files(extensions="*")) == 4
        assert {f for f in codebase.files(extensions="*")} == {file1, file2, file3, file4}

        assert len(codebase.files(extensions=[".py"])) == 2
        assert {f for f in codebase.files(extensions=[".py"])} == {file1, file2}

        assert len(codebase.files(extensions=[".bin"])) == 1
        assert {f for f in codebase.files(extensions=[".bin"])} == {file3}


def test_codebase_files_other_language(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir, files={"file1.py": "print(123)", "file2.py": "print(456)", "file3.bin": b"\x89PNG", "file4": "Hello world!"}, programming_language=ProgrammingLanguage.OTHER
    ) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")
        file3 = codebase.get_file("file3.bin")
        file4 = codebase.get_file("file4")

        assert len(codebase.files) == 4  # Match all files if the language is OTHER
        assert {f for f in codebase.files} == {file1, file2, file3, file4}

        assert len(codebase.files(extensions="*")) == 4
        assert {f for f in codebase.files(extensions="*")} == {file1, file2, file3, file4}

        assert len(codebase.files(extensions=[".py"])) == 2
        assert {f for f in codebase.files(extensions=[".py"])} == {file1, file2}

        assert len(codebase.files(extensions=[".bin"])) == 1
        assert {f for f in codebase.files(extensions=[".bin"])} == {file3}


@pytest.mark.skipif(sys.platform == "darwin", reason="macOS is case-insensitive")
def test_file_extensions_ignore_case(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": "print(123)", "file2.py": "print(456)", "file3.bin": b"\x89PNG", "file4": "Hello world!"}) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")
        file3 = codebase.get_file("file3.bin")
        file4 = codebase.get_file("file4")

        assert len(codebase.files(extensions=[".pyi"])) == 0
        assert {f for f in codebase.files(extensions=[".pyi"])} == set()
        # Test ignore_case
        file1_upper = codebase.get_file("FILE1.PY", ignore_case=True)
        assert file1_upper is not None
        assert file1_upper == file1

        file2_mixed = codebase.get_file("FiLe2.Py", ignore_case=True)
        assert file2_mixed is not None
        assert file2_mixed == file2

        file3_upper = codebase.get_file("FILE3.BIN", ignore_case=True)
        assert file3_upper is not None
        assert file3_upper == file3

        # Test ignore_case=False (default)
        assert codebase.get_file("FILE1.PY", ignore_case=False, optional=True) is None
        assert codebase.get_file("FiLe2.Py", ignore_case=False, optional=True) is None
        assert codebase.get_file("FILE3.BIN", ignore_case=False, optional=True) is None


@pytest.mark.skipif(sys.platform == "darwin", reason="macOS is case-insensitive")
def test_file_case_sensitivity_has_file(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": "print(123)", "file2.py": "print(456)", "file3.bin": b"\x89PNG"}) as codebase:
        # Test has_file with ignore_case=True
        assert codebase.has_file("file1.py", ignore_case=True)
        assert codebase.has_file("FILE1.PY", ignore_case=True)
        assert codebase.has_file("FiLe1.Py", ignore_case=True)
        assert codebase.has_file("file2.py", ignore_case=True)
        assert codebase.has_file("FILE2.PY", ignore_case=True)
        assert codebase.has_file("FiLe2.Py", ignore_case=True)
        assert codebase.has_file("file3.bin", ignore_case=True)
        assert codebase.has_file("FILE3.BIN", ignore_case=True)
        assert codebase.has_file("FiLe3.BiN", ignore_case=True)

        # Test has_file with ignore_case=False (default)
        assert codebase.has_file("file1.py", ignore_case=False)
        assert not codebase.has_file("FILE1.PY", ignore_case=False)
        assert not codebase.has_file("FiLe1.Py", ignore_case=False)
        assert codebase.has_file("file2.py", ignore_case=False)
        assert not codebase.has_file("FILE2.PY", ignore_case=False)
        assert not codebase.has_file("FiLe2.Py", ignore_case=False)
        assert codebase.has_file("file3.bin", ignore_case=False)
        assert not codebase.has_file("FILE3.BIN", ignore_case=False)
        assert not codebase.has_file("FiLe3.BiN", ignore_case=False)


@pytest.mark.skipif(sys.platform == "darwin", reason="macOS is case-insensitive")
def test_file_case_sensitivity_get_file(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": "print(123)", "file2.py": "print(456)", "file3.bin": b"\x89PNG"}) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")
        file3 = codebase.get_file("file3.bin")

        # Test get_file with ignore_case=True
        assert codebase.get_file("FILE1.PY", ignore_case=True) == file1
        assert codebase.get_file("FiLe1.Py", ignore_case=True) == file1
        assert codebase.get_file("FILE2.PY", ignore_case=True) == file2
        assert codebase.get_file("FiLe2.Py", ignore_case=True) == file2
        assert codebase.get_file("FILE3.BIN", ignore_case=True) == file3
        assert codebase.get_file("FiLe3.BiN", ignore_case=True) == file3

        # Test get_file with ignore_case=False (default)
        assert codebase.get_file("FILE1.PY", ignore_case=False, optional=True) is None
        assert codebase.get_file("FiLe1.Py", ignore_case=False, optional=True) is None
        assert codebase.get_file("FILE2.PY", ignore_case=False, optional=True) is None
        assert codebase.get_file("FiLe2.Py", ignore_case=False, optional=True) is None
        assert codebase.get_file("FILE3.BIN", ignore_case=False, optional=True) is None
        assert codebase.get_file("FiLe3.BiN", ignore_case=False, optional=True) is None


@pytest.mark.skipif(sys.platform == "darwin", reason="macOS is case-insensitive")
def test_subdirectory_case_sensitivity(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"subdir/file1.py": "print(123)", "SUBDIR2/file2.py": "print(456)", "SubDir3/file3.py": "print(789)"}) as codebase:
        # Test has_subdirectory with ignore_case=True
        assert codebase.has_directory("subdir", ignore_case=True)
        assert codebase.has_directory("SUBDIR", ignore_case=True)
        assert codebase.has_directory("SubDir", ignore_case=True)
        assert codebase.has_directory("SUBDIR2", ignore_case=True)
        assert codebase.has_directory("subdir2", ignore_case=True)
        assert codebase.has_directory("SubDir2", ignore_case=True)
        assert codebase.has_directory("SubDir3", ignore_case=True)
        assert codebase.has_directory("SUBDIR3", ignore_case=True)
        assert codebase.has_directory("subdir3", ignore_case=True)

        # Test has_subdirectory with ignore_case=False (default)
        assert codebase.has_directory("subdir", ignore_case=False)
        assert not codebase.has_directory("SUBDIR", ignore_case=False)
        assert not codebase.has_directory("SubDir", ignore_case=False)
        assert codebase.has_directory("SUBDIR2", ignore_case=False)
        assert not codebase.has_directory("subdir2", ignore_case=False)
        assert not codebase.has_directory("SubDir2", ignore_case=False)
        assert codebase.has_directory("SubDir3", ignore_case=False)
        assert not codebase.has_directory("SUBDIR3", ignore_case=False)
        assert not codebase.has_directory("subdir3", ignore_case=False)


@pytest.mark.skipif(sys.platform == "darwin", reason="macOS is case-insensitive")
def test_files_in_subdirectories_case_sensitivity(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"subdir/file1.py": "print(123)", "SUBDIR2/FILE2.py": "print(456)", "SubDir3/File3.py": "print(789)"}) as codebase:
        # Test has_file with ignore_case=True for files in subdirectories
        assert codebase.has_file("subdir/file1.py", ignore_case=True)
        assert codebase.has_file("SUBDIR/FILE1.py", ignore_case=True)
        assert codebase.has_file("SubDir/File1.py", ignore_case=True)
        assert codebase.has_file("SUBDIR2/FILE2.py", ignore_case=True)
        assert codebase.has_file("subdir2/file2.py", ignore_case=True)
        assert codebase.has_file("SubDir2/File2.py", ignore_case=True)
        assert codebase.has_file("SubDir3/File3.py", ignore_case=True)
        assert codebase.has_file("SUBDIR3/FILE3.py", ignore_case=True)
        assert codebase.has_file("subdir3/file3.py", ignore_case=True)

        # Test has_file with ignore_case=False (default) for files in subdirectories
        assert codebase.has_file("subdir/file1.py", ignore_case=False)
        assert not codebase.has_file("SUBDIR/FILE1.py", ignore_case=False)
        assert not codebase.has_file("SubDir/File1.py", ignore_case=False)
        assert codebase.has_file("SUBDIR2/FILE2.py", ignore_case=False)
        assert not codebase.has_file("subdir2/file2.py", ignore_case=False)
        assert not codebase.has_file("SubDir2/File2.py", ignore_case=False)
        assert codebase.has_file("SubDir3/File3.py", ignore_case=False)
        assert not codebase.has_file("SUBDIR3/FILE3.py", ignore_case=False)
        assert not codebase.has_file("subdir3/file3.py", ignore_case=False)


def test_minified_file(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "file1.min.js": "console.log(123)",
            "file2.js": open(f"{os.path.dirname(__file__)}/example.min.js").read(),
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        # This should match the `*.min.js` pattern
        file1 = codebase.ctx.get_file("file1.min.js")
        assert file1 is None

        # This should match the maximum line length threshold
        file2 = codebase.ctx.get_file("file2.js")
        assert file2 is None
