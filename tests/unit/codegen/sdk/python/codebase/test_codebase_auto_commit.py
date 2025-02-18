import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


@pytest.mark.skip(reason="We are disabling auto commit for performance reasons")
def test_auto_reparse(tmpdir) -> None:
    # language=python
    file0 = """
from file2 import bar

def square(x):
    return x * x
    """
    # language=python
    file1 = """
from dir.file0 import square

class MyClass:
    def foo(self, arg1, arg2):
        return arg1 + square(arg2)
    """
    # file2 has an indirect import to file0
    # language=python
    file2 = """
from dir.file1 import square

def bar(x):
    return square(x)
    """
    # language=python
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file0.py": file0, "dir/file1.py": file1, "file2.py": file2}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file0 = codebase.get_file("dir/file0.py")
        file1 = codebase.get_file("dir/file1.py")
        file2 = codebase.get_file("file2.py")

        for symbol in codebase.symbols:
            symbol.rename(f"{symbol.name}_updated")

        file0.commit()
        file1.commit()
        file2.commit()
        assert file0.content.strip("\n") == file0.source
        assert file1.content.strip("\n") == file1.source
        assert file2.content.strip("\n") == file2.source

        assert (
            file0.content
            == """
from file2 import bar_updated

def square_updated(x):
    return x * x
    """
        )

        assert (
            file1.content
            == """
from dir.file0 import square_updated

class MyClass_updated:
    def foo(self, arg1, arg2):
        return arg1 + square_updated(arg2)
    """
        )

        assert (
            file2.content
            == """
from dir.file1 import square_updated

def bar_updated(x):
    return square_updated(x)
    """
        )
