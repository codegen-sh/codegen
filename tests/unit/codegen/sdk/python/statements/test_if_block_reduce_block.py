from typing import TYPE_CHECKING

import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.statements.statement import StatementType

if TYPE_CHECKING:
    from codegen.sdk.python import PyFile


def test_reduce_condition_to_true_elif(tmpdir):
    # language=python
    content = """
def foo():
    if a:
        print(a)
        print(a+b)
    elif b:
        print(b)
    else:
        print(c)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        function = file.get_function("foo")
        if_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        if_block.reduce_condition(True)
    # language=python
    assert (
        file.content
        == """
def foo():
    print(a)
    print(a+b)
    if b:
        print(b)
    else:
        print(c)
    """
    )


def test_reduce_condition_to_false_elif(tmpdir):
    # language=python
    content = """
def foo():
    if a:
        print(a)
        print(a+b)
    elif b:
        print(b)
    else:
        print(c)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        function = file.get_function("foo")
        if_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        if_block.reduce_condition(False)
    # language=python
    assert (
        file.content
        == """
def foo():
    if b:
        print(b)
    else:
        print(c)
    """
    )


def test_reduce_condition_to_true_else(tmpdir):
    # language=python
    content = """
def foo():
    if a:
        print(a)
        print(c)
    else:
        print(b)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        function = file.get_function("foo")
        if_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        if_block.reduce_condition(True)
    # language=python
    assert (
        file.content
        == """
def foo():
    print(a)
    print(c)
    """
    )


def test_reduce_condition_to_false_else(tmpdir):
    # language=python
    content = """
def foo():
    if a:
        print(a)
    else:
        print(b)
        print(c)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        function = file.get_function("foo")
        if_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        if_block.reduce_condition(False)
    # language=python
    assert (
        file.content
        == """
def foo():
    print(b)
    print(c)
    """
    )


def test_reduce_condition_multiple_if_blocks(tmpdir):
    # language=python
    content = """
def foo():
    if a:
        print(a)
    if b:
        print(b)
        print(b+c)
    elif c:
        print(c)
        return
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        function = file.get_function("foo")
        second_if = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[1]
        second_if.reduce_condition(False)
    # language=python
    assert (
        file.content
        == """
def foo():
    if a:
        print(a)
    if c:
        print(c)
        return
    """
    )


def test_reduce_condition_nested_if(tmpdir):
    # language=python
    content = """
class MyClass:
    def foo(self):
        if a:
            if b:
                print(b)
            print(a)
            if c:
                print(c)
                print(c+d)
            elif d:
                print(d)
                return
        else:
            print(e)
            return
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        function = file.get_class("MyClass").get_method("foo")
        top_if = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        top_if.reduce_condition(True)
        nested_if = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[2]
        nested_if.reduce_condition(False)

    # language=python
    assert (
        file.content
        == """
class MyClass:
    def foo(self):
        if b:
            print(b)
        print(a)
        if d:
            print(d)
            return
    """
    )


def test_reduce_condition_else_if_to_true(tmpdir):
    # language=python
    content = """
def foo():
    if a:
        print(a)
    elif b:
        print(b)
        print(b+c)
    elif c:
        print(c)
    else:
        print(d)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        function = file.get_function("foo")
        elif_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0].elif_statements[0]
        elif_block.reduce_condition(True)
    # language=python
    assert (
        file.content
        == """
def foo():
    if a:
        print(a)
    print(b)
    print(b+c)
    if c:
        print(c)
    else:
        print(d)
    """
    )


def test_reduce_condition_else_if_to_false(tmpdir):
    # language=python
    content = """
def foo():
    if a:
        print(a)
    elif b:
        print(b)
        print(b+c)
    elif c:
        print(c)
    else:
        print(d)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        function = file.get_function("foo")
        elif_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0].elif_statements[0]
        elif_block.reduce_condition(False)
    # language=python
    assert (
        file.content
        == """
def foo():
    if a:
        print(a)
    elif c:
        print(c)
    else:
        print(d)
    """
    )


def test_reduce_condition_second_else_if_to_true(tmpdir):
    # language=python
    content = """
def foo():
    if a:
        print(a)
    elif b:
        print(b)
    elif c:
        print(c)
    else:
        print(d)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        function = file.get_function("foo")
        elif_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0].elif_statements[1]
        elif_block.reduce_condition(True)
    # language=python
    assert (
        file.content
        == """
def foo():
    if a:
        print(a)
    elif b:
        print(b)
    print(c)
    """
    )


def test_reduce_condition_second_else_if_to_false(tmpdir):
    # language=python
    content = """
def foo():
    if a:
        print(a)
    elif b:
        print(b)
    elif c:
        print(c)
    else:
        print(d)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        function = file.get_function("foo")
        elif_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0].elif_statements[1]
        elif_block.reduce_condition(True)
    # language=python
    assert (
        file.content
        == """
def foo():
    if a:
        print(a)
    elif b:
        print(b)
    print(c)
    """
    )


def test_reduce_condition_else_statement_raises(tmpdir):
    # language=python
    content = """
def foo():
    if a:
        print(a)
    elif b:
        print(b)
    else:
        print(c)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        function = file.get_function("foo")
        else_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0].else_statement
        with pytest.raises(ValueError):
            else_block.reduce_condition(True)


def test_reduce_condition_to_true_single_if(tmpdir):
    # language=python
    content = """
def foo():
    if a:
        print(a)
    print(b)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        function = file.get_function("foo")
        if_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        if_block.reduce_condition(True)
    # language=python
    assert (
        file.content
        == """
def foo():
    print(a)
    print(b)
    """
    )


def test_reduce_condition_to_false_single_if(tmpdir):
    # language=python
    content = """
def foo():
    if a:
        print(a)
    print(b)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        function = file.get_function("foo")
        if_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        if_block.reduce_condition(False)
    # language=python
    assert (
        file.content
        == """
def foo():
    print(b)
    """
    )
