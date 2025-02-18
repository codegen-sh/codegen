from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.python.file import PyFile


def test_reduce_binary_simple(tmpdir):
    # language=python
    content = """
def foo():
    a = False
    result = a and b
    print(result)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        foo = file.get_function("foo")
        assign = foo.code_block.assignments[0]
        assert assign.name == "a"
        assign.reduce_condition(False)
    # language=python
    assert (
        file.content
        == """
def foo():
    print(False)
    """
    )


def test_reduce_binary_complex_condition(tmpdir):
    # language=python
    content = """
def bar():
    x = True
    y = False
    result = (x or y) and b
    print(result)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file2.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file2.py")
        bar = file.get_function("bar")
        assign_x = bar.code_block.assignments[0]
        assign_y = bar.code_block.assignments[1]
        assign_x.reduce_condition(True)
        assign_y.reduce_condition(False)
    # language=python
    assert (
        file.content
        == """
def bar():
    result = b
    print(result)
    """
    )


def test_reduce_negation_condition(tmpdir):
    # language=python
    content = """
def baz():
    a = True
    notA = not a
    result = notA or b
    print(result)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file3.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file3.py")
        baz = file.get_function("baz")
        assign_notA = baz.code_block.assignments[1]
        assign_notA.reduce_condition(False)
    # language=python
    assert (
        file.content
        == """
def baz():
    a = True
    result = b
    print(result)
    """
    )


def test_reduce_binary_with_string(tmpdir):
    # language=python
    content = """
def qux():
    isActive = True
    result = "active" if isActive else "inactive"
    print(result)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file4.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file4.py")
        qux = file.get_function("qux")
        assign_isActive = qux.code_block.assignments[0]
        assign_isActive.reduce_condition(True)
    # language=python
    assert (
        file.content
        == """
def qux():
    result = "active"
    print(result)
    """
    )


def test_reduce_complex_condition_with_string(tmpdir):
    # language=python
    content = """
def quux():
    isActive = True
    result = "active" if isActive else "inactive"
    print(result)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file5.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file5.py")
        quux = file.get_function("quux")
        assign_isActive = quux.code_block.assignments[0]
        assign_isActive.reduce_condition(True)
    # language=python
    assert (
        file.content
        == """
def quux():
    result = "active"
    print(result)
    """
    )
