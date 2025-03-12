import os

import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import File
from tests.unit.codegen.sdk.python.utils.test_file_contents import file1_content, file2_content


@pytest.fixture(scope="function")
def mock_codebase_setup(tmpdir) -> tuple[Codebase, File, File]:
    tmpdir.mkdir("test_reparse")
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": file1_content, "file2.py": file2_content}) as mock_code_base:
        yield mock_code_base, mock_code_base.get_file("file1.py"), mock_code_base.get_file("file2.py")


def test_codebase_create_file(mock_codebase_setup: tuple[Codebase, File, File]) -> None:
    codebase, file1, file2 = mock_codebase_setup
    new_content = """
from file1 import GLOBAL_CONSTANT_1

def foo():
    return GLOBAL_CONSTANT_1
    """
    codebase.create_file("file3.py", new_content)
    file3 = codebase.get_file("file3.py")
    assert [imp.name for imp in file3.imports] == ["GLOBAL_CONSTANT_1"]
    assert [f.name for f in file3.functions] == ["foo"]


def test_codebase_create_dir(mock_codebase_setup: tuple[Codebase, File, File]) -> None:
    codebase, file1, file2 = mock_codebase_setup
    new_content = """
    from file1 import GLOBAL_CONSTANT_1

    def foo():
        return GLOBAL_CONSTANT_1
        """
    codebase.create_directory("test")
    codebase.create_file("test/file3.py", new_content)
    file3 = codebase.get_file("test/file3.py")
    assert [imp.name for imp in file3.imports] == ["GLOBAL_CONSTANT_1"]
    assert [f.name for f in file3.functions] == ["foo"]
    codebase.create_directory("test2/test3", parents=True)
    codebase.create_file("test2/test3/file3.py", new_content)
    file4 = codebase.get_file("test2/test3/file3.py")
    assert file4 is not None
    codebase.create_directory("test2/test3", exist_ok=True)
    with pytest.raises(FileExistsError):
        codebase.create_directory("test2/test3", exist_ok=False)


def test_codebase_create_then_delete_file(mock_codebase_setup: tuple[Codebase, File, File]) -> None:
    codebase, file1, file2 = mock_codebase_setup

    assert len(list(list(codebase.files))) == 2
    assert not codebase.has_file("my_file.py")

    codebase.create_file("my_file.py")
    assert codebase.has_file("my_file.py")

    file = codebase.get_file("my_file.py")
    assert file is not None
    assert len(list(list(codebase.files))) == 3

    file.remove()
    codebase.ctx.commit_transactions()
    assert not os.path.exists("my_file.py")
