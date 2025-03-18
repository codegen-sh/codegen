from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.expressions import Name, Value

if TYPE_CHECKING:
    from codegen.sdk.python import PyFile


def test_with_statement_single_var(tmpdir):
    # language=python
    content = """
def foo():
    print("hello")
    with context_manager:
        print("world")
    print("goodbye")
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file: PyFile = codebase.get_file("file.py")
        with_statement = file.get_function("foo").code_block.with_statements[0]
        with_clause = with_statement.clause
        assert len(with_clause.expressions) == 1
        assert isinstance(with_clause.expressions[0], Name)
        assert with_clause.source == "context_manager"
        with_statement.code_block.unwrap()

    # language=python
    assert (
        file.content
        == """
def foo():
    print("hello")
    print("world")
    print("goodbye")
    """
    )


def test_with_statement_aliased_var(tmpdir):
    # language=python
    content = """
def foo():
    print("hello")
    with context_manager as var:
        print(var)
    print("goodbye")
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file: PyFile = codebase.get_file("file.py")
        with_statement = file.get_function("foo").code_block.with_statements[0]
        with_clause = with_statement.clause
        assert len(with_clause.expressions) == 1
        assert isinstance(with_clause.expressions[0], Value)
        assert with_clause.source == "context_manager as var"
        with_statement.code_block.unwrap()
    # language=python
    assert (
        file.content
        == """
def foo():
    print("hello")
    print(var)
    print("goodbye")
    """
    )


def test_with_statement_multiple_vars(tmpdir):
    # language=python
    content = """
def foo():
    print("hello")
    with context_manager1 as var1, context_manager2 as var2:
        print(var1, var2)
    print("goodbye")
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file: PyFile = codebase.get_file("file.py")
        with_statement = file.get_function("foo").code_block.with_statements[0]
        with_clause = with_statement.clause
        assert len(with_clause.expressions) == 2
        assert [x.source for x in with_clause.expressions] == ["context_manager1 as var1", "context_manager2 as var2"]
        assert with_clause.source == "context_manager1 as var1, context_manager2 as var2"
        with_statement.code_block.unwrap()
    # language=python
    assert (
        file.content
        == """
def foo():
    print("hello")
    print(var1, var2)
    print("goodbye")
    """
    )


def test_with_statement_multiline_vars(tmpdir):
    # language=python
    content = """
def foo():
    print("hello")
    with (context_manager1 as var1,
          context_manager2,
          context_manager3 as var3):
        print(var1, context_manager2, var3)
    print("goodbye")
    """
    # language=python
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file: PyFile = codebase.get_file("file.py")
        with_statement = file.get_function("foo").code_block.with_statements[0]
        with_clause = with_statement.clause
        assert len(with_clause.expressions) == 3
        assert [x.source for x in with_clause.expressions] == [
            "context_manager1 as var1",
            "context_manager2",
            "context_manager3 as var3",
        ]
        assert (
            with_clause.source
            == """context_manager1 as var1,
          context_manager2,
          context_manager3 as var3"""
        )
        with_statement.code_block.unwrap()
    # language=python
    assert (
        file.content
        == """
def foo():
    print("hello")
    print(var1, context_manager2, var3)
    print("goodbye")
    """
    )


def test_with_statement_function_call(tmpdir):
    # language=python
    content = """
def foo():
    print("hello")
    with open('file.txt'):
        print("world")
    print("goodbye")
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file: PyFile = codebase.get_file("file.py")
        with_statement = file.get_function("foo").code_block.with_statements[0]
        with_clause = with_statement.clause
        assert len(with_clause.expressions) == 1
        assert isinstance(with_clause.expressions[0], FunctionCall)
        assert with_clause.source == "open('file.txt')"
        with_statement.code_block.unwrap()
    # language=python
    assert (
        file.content
        == """
def foo():
    print("hello")
    print("world")
    print("goodbye")
    """
    )
