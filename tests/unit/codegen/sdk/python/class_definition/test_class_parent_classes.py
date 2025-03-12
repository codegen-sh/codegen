from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_class_definition_parent_classes_single(tmpdir) -> None:
    SUBCLASS = "cube.py"
    # language=python
    SUBCLASS_CONTENT = """
from shape import Shape
class Cube(Shape):
    side_length: int

    def __init__(self, color: str, side_length: int):
        super().__init__(color)
        self.side_length = side_length
"""
    PARENT = "shape.py"
    # language=python
    PARENT_CONTENT = """
class Shape:
    def __init__(self, color: str):
        self.color = color
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={SUBCLASS: SUBCLASS_CONTENT.strip(), PARENT: PARENT_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(SUBCLASS)
        cls = file.get_class("Cube")
        parent_classes = cls.superclasses

        assert parent_classes
        assert len(parent_classes) == 1
        assert [x.name for x in parent_classes] == ["Shape"]


def test_class_definition_parent_classes_multiple(tmpdir) -> None:
    SUBCLASS = "cube.py"
    # language=python
    SUBCLASS_CONTENT = """
from shape import Shape
class Cube(Shape):
    side_length: int

    def __init__(self, color: str, side_length: int):
        super().__init__(color)
        self.side_length = side_length
"""
    PARENT = "shape.py"
    # language=python
    PARENT_CONTENT = """
class ShapeBase:
    def cat():
        pass
class Shape(ShapeBase):
    color: bool

    def __init__(self, color: str):
        self.color = color

    def bar():
        pass

"""

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={SUBCLASS: SUBCLASS_CONTENT.strip(), PARENT: PARENT_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(SUBCLASS)
        cls = file.get_class("Cube")
        assert cls.get_method("bar")
        assert cls.get_method("cat")
        assert cls.get_attribute("color")


def test_class_definition_parent_classes_mro(tmpdir) -> None:
    SUBCLASS = "cube.py"
    # language=python
    SUBCLASS_CONTENT = """
from shape import B,C

class A(B,C):
    pass
    """
    PARENT = "shape.py"
    # language=python
    PARENT_CONTENT = """
class E:
    pass

class B(D):
    def a():
        pass

class D(E):
    pass

class C(E):
    def a():
        pass
    """

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={SUBCLASS: SUBCLASS_CONTENT.strip(), PARENT: PARENT_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(SUBCLASS)
        file2 = codebase.get_file(PARENT)
        a = file.get_class("A")
        b = file2.get_class("B")
        c = file2.get_class("C")
        d = file2.get_class("D")
        e = file2.get_class("E")
        assert a.superclasses == [b, c, d, e]
        assert a.superclasses(max_depth=1) == [b, c]
        assert a.get_method("a") == b.get_method("a")


def test_class_definition_parent_classes_external(tmpdir) -> None:
    SUBCLASS = "cube.py"
    # language=python
    SUBCLASS_CONTENT = """
from enum import Enum


class MyEnum(Enum):
    FOO = "foo"
    BAR = "bar"
    BAZ = "baz"

"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={SUBCLASS: SUBCLASS_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(SUBCLASS)
        cls = file.get_class("MyEnum")
        assert len(cls.superclasses) == 1
        assert cls.superclasses[0].name == "Enum"


def test_class_definition_parent_classes_external_nested(tmpdir) -> None:
    SUBCLASS = "cube.py"
    # language=python
    SUBCLASS_CONTENT = """
from enum import Enum

def test():
    with x:
        class MyEnum(Enum):
            FOO = "foo"
            BAR = "bar"
            BAZ = "baz"
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={SUBCLASS: SUBCLASS_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(SUBCLASS)
        enum = file.imports[0]
        assert len(enum.usages) == 1
        codebase.get_symbol("test").rename("hi")
    codebase.reset()


def test_superclasses_implementation(tmpdir) -> None:
    filename = "cube.py"
    # language=python
    content = """

class A:
    def __init__(self):
        pass

class B(A):
    def __init__(self):
        pass

class C:
    def __init__(self):
        pass

class D(A[B, C]):  # only inherits A
    pass
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={filename: content.strip()},
    ) as codebase:
        file = codebase.get_file(filename)
        cls = file.get_class("D")
        assert len(cls.parent_class_names) == 1
        assert len(cls.superclasses) == 1
        assert cls.superclasses[0].name == "A"
