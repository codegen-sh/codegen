from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.expressions.number import Number
from codegen.sdk.python.statements.assignment_statement import PyAssignmentStatement
from codegen.sdk.python.statements.attribute import PyAttribute


def test_attribute(tmpdir) -> None:
    # language=python
    content1 = """
import marshmallow as ma
from file2 import OtherClass

class MyClass(ma.Schema):
    a: int
    b: int = 1
    c: OtherClass = OtherClass()

    def __init__(self, x, y, z):
        self.a = x + y + z
"""
    # language=python
    content2 = """
class OtherClass:
    def __init__(self):
        pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file = codebase.get_file("file1.py")
        cls = file.get_class("MyClass")
        a = cls.get_attribute("a")
        b = cls.get_attribute("b")
        c = cls.get_attribute("c")

        assert a.assignment.type.source == "int"
        assert a.left.source == a.name
        assert a.name == "a"
        assert a.assignment.value is None

        assert b.assignment.type.source == "int"
        assert b.left.source == b.name
        assert b.name == "b"
        assert isinstance(b.assignment.value, Number)
        assert b.assignment.value.source == "1"

        assert c.assignment.type.source == "OtherClass"
        assert c.left.source == c.name
        assert c.name == "c"
        assert isinstance(c.assignment.value, FunctionCall)
        assert c.assignment.value.source == "OtherClass()"
        assert c.assignment.value.function_definition.file.name == "file2"


def test_attributes_with_comments(tmpdir) -> None:
    # language=python
    content = """
class A:
    '''comment'''
    b: int = 1  # comment
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        symbol = file.get_class("A")
        attrs = symbol.attributes
        assert len(attrs) == 1
        assert attrs[0].name == "b"


def test_attribute_from_code_block(tmpdir) -> None:
    # language=python
    content = """
class MyClass(ma.Schema):
    a: int
    b: int = 1
    c: OtherClass = OtherClass()

    def __init__(self, x, y, z):
        self.a = x + y + z
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        cls = file.get_class("MyClass")

        b = cls.get_attribute("b")
        assert b.parent.parent == cls
        assert isinstance(b, PyAttribute)
        assert isinstance(b, PyAssignmentStatement)
        assert b.file_node_id == cls.file_node_id
        assert b.ctx == cls.ctx
