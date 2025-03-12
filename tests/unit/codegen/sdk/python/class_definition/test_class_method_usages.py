from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_class_definition_parent_class_names_single(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class Point:
    def scale(self, n: int):
        pass
    def double(self):
        self.scale(2)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        double = point.get_method("double")
        assert scale.symbol_usages == [double]
        assert len(scale.usages) == 1


def test_class_definition_nested_classes(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class Point:
    class Child:
        @staticmethod
        def scale(self, n: int):
            pass
    def double(self):
        Point.Child.scale(2)

"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        child = point.nested_classes[0]
        scale = child.get_method("scale")
        assert child == point.get_nested_class("Child")
        double = point.get_method("double")
        assert scale.symbol_usages == [double]
        assert len(scale.usages) == 1


def test_class_definition_parent_class_names_class_method(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class Point:
    @classmethod
    def scale(cls, n: int):
        pass
    @classmethod
    def double(cls):
        cls.scale(2)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        double = point.get_method("double")
        assert scale.symbol_usages == [double]
        assert len(scale.usages) == 1


def test_class_definition_parent_class_names_static(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class Point:
    def scale(self, n: int):
        pass
    @staticmethod
    def double(self):
        self.scale(2)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        assert scale.symbol_usages == []
        assert len(scale.usages) == 0


def test_class_definition_usages_parameter(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class Point:
    def scale(cls, n: int):
        pass
def foo(a: Point):
    a.scale(2)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        foo = file.get_symbol("foo")
        assert scale.symbol_usages == [foo]
        assert len(scale.usages) == 1


def test_class_definition_usages_union(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class OtherPoint:
    def scale(cls, n: int):
        pass
class Point:
    def scale(cls, n: int):
        pass
def foo(a: Point | OtherPoint):
    a.scale(2)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        otherpoint = file.get_symbol("OtherPoint")
        otherscale = otherpoint.get_method("scale")
        foo = file.get_symbol("foo")
        assert scale.symbol_usages == [foo]
        assert len(scale.usages) == 1
        assert otherscale.symbol_usages == [foo]
        assert len(scale.usages) == 1


def test_class_definition_usages_parameter_default(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class Point:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
def foo(a = Point()):
    a.scale(2)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        foo = file.get_symbol("foo")
        assert scale.symbol_usages == [foo]
        assert len(scale.usages) == 1


def test_class_definition_usages_local_var(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class Point:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
def foo():
    a = Point()
    a.scale(2)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        foo = file.get_symbol("foo")
        assert scale.symbol_usages == [foo]
        assert len(scale.usages) == 1
        scale.rename("scale2")
    # language=python
    assert (
        file.content.strip()
        == """
class Point:
    def __init__(self):
        pass
    def scale2(cls, n: int):
        pass
def foo():
    a = Point()
    a.scale2(2)
""".strip()
    )


def test_class_definition_usages_local_var_multi_file(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class Point:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
def foo():
    a = Point()
    a.scale(2)
"""
    FILENAME2 = "test2.py"
    # language=python
    FILE_CONTENT2 = """
from test import Point
def foo():
    a = Point()
    a.scale(2)
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip(), FILENAME2: FILE_CONTENT2.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        file2 = codebase.get_file(FILENAME2)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        foo = file.get_symbol("foo")
        foo2 = file2.get_symbol("foo")
        assert scale.symbol_usages == [foo, foo2]
        assert len(scale.usages) == 2
        scale.rename("scale2")
    # language=python
    assert (
        file.content.strip()
        == """
class Point:
    def __init__(self):
        pass
    def scale2(cls, n: int):
        pass
def foo():
    a = Point()
    a.scale2(2)
""".strip()
    )
    # language=python
    assert (
        file2.content.strip()
        == """
from test import Point
def foo():
    a = Point()
    a.scale2(2)
""".strip()
    )


def test_class_definition_usages_generic_function(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
from typing import TypeVar, Generic
class Point:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
T = TypeVar("T")
def pop(a: T) -> T:
    ...
pop(Point).scale(1)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        usage = file.code_block.statements[-1].value
        assert isinstance(usage, FunctionCall)
        assert usage.predecessor.resolved_value == point
        assert len(scale.usages) == 1
        scale.rename("scale2")
    # language=python
    assert (
        file.content.strip()
        == """
from typing import TypeVar, Generic
class Point:
    def __init__(self):
        pass
    def scale2(cls, n: int):
        pass
T = TypeVar("T")
def pop(a: T) -> T:
    ...
pop(Point).scale2(1)
""".strip()
    )


def test_class_definition_usages_generic_class(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
from typing import TypeVar, Generic
class Point:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
T = TypeVar("T")
class List(Generic[T]):
    def pop(self) -> T:
        ...
l: List[Point] = []
l.pop().scale(1)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        usage = file.code_block.statements[-1].value
        assert isinstance(usage, FunctionCall)
        assert usage.predecessor.resolved_value == point
        assert len(scale.usages) == 1
        scale.rename("scale2")
    # language=python
    assert (
        file.content.strip()
        == """
from typing import TypeVar, Generic
class Point:
    def __init__(self):
        pass
    def scale2(cls, n: int):
        pass
T = TypeVar("T")
class List(Generic[T]):
    def pop(self) -> T:
        ...
l: List[Point] = []
l.pop().scale2(1)
""".strip()
    )


def test_class_definition_usages_generic_class_new_syntax(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class Point:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
class List[T]:
    def pop(self) -> T:
        ...
l: List[Point] = []
l.pop().scale(1)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        list = file.get_symbol("List")
        scale = point.get_method("scale")
        usage = file.code_block.statements[-1].value
        assert isinstance(usage, FunctionCall)
        assert len(list.type_parameters) == 1
        assert len(list.generics) == 1
        assert usage.predecessor.resolved_value == point
        assert len(scale.usages) == 1
        scale.rename("scale2")
    # language=python
    assert (
        file.content.strip()
        == """
class Point:
    def __init__(self):
        pass
    def scale2(cls, n: int):
        pass
class List[T]:
    def pop(self) -> T:
        ...
l: List[Point] = []
l.pop().scale2(1)
""".strip()
    )


def test_class_definition_usages_stdlib_generic(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class Point:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
l: list[Point] = []
l.pop().scale(1)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        usage = file.code_block.statements[-1].value
        assert isinstance(usage, FunctionCall)
        assert usage.predecessor.resolved_types[0] == point
        assert len(scale.usages) == 1
        scale.rename("scale2")
    # language=python
    assert (
        file.content.strip()
        == """
class Point:
    def __init__(self):
        pass
    def scale2(cls, n: int):
        pass
l: list[Point] = []
l.pop().scale2(1)
""".strip()
    )


def test_class_definition_usages_stdlib_generic_for_loop(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class Point:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
l: list[Point] = []
for i in l:
    i.scale(1)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        usage = file.code_block.statements[-1].code_block.statements[0].value
        assert isinstance(usage, FunctionCall)
        assert usage.get_name().object.resolved_types[0] == point
        assert len(scale.usages) == 1
        scale.rename("scale2")
    # language=python
    assert (
        file.content.strip()
        == """
class Point:
    def __init__(self):
        pass
    def scale2(cls, n: int):
        pass
l: list[Point] = []
for i in l:
    i.scale2(1)
""".strip()
    )


def test_class_definition_usages_stdlib_generic_dict(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class Point:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
class Point2:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass

l: dict[Point, Point2] = {}
for k, v in l.items():
    k.scale(1)
    v.scale(1)

"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        point2 = file.get_symbol("Point2")
        scale = point.get_method("scale")
        scale2 = point2.get_method("scale")
        assert len(scale.usages) == 1
        assert len(scale2.usages) == 1
        scale.rename("scale2")
        scale2.rename("scale3")
    # language=python
    assert (
        file.content.strip()
        == """
class Point:
    def __init__(self):
        pass
    def scale2(cls, n: int):
        pass
class Point2:
    def __init__(self):
        pass
    def scale3(cls, n: int):
        pass

l: dict[Point, Point2] = {}
for k, v in l.items():
    k.scale2(1)
    v.scale3(1)
""".strip()
    )


def test_class_definition_usages_stdlib_generic_dict_values(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
class Point:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
class Point2:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass

l: dict[Point, Point2] = {}
for v in l.values():
    v.scale(1)

"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        point2 = file.get_symbol("Point2")
        scale = point.get_method("scale")
        scale2 = point2.get_method("scale")
        assert len(scale.usages) == 0
        assert len(scale2.usages) == 1
        scale.rename("scale2")
        scale2.rename("scale3")
    # language=python
    assert (
        file.content.strip()
        == """
class Point:
    def __init__(self):
        pass
    def scale2(cls, n: int):
        pass
class Point2:
    def __init__(self):
        pass
    def scale3(cls, n: int):
        pass

l: dict[Point, Point2] = {}
for v in l.values():
    v.scale3(1)
""".strip()
    )


def test_class_definition_usages_stdlib_generic_dict_alias(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
from typing import TypeAlias

class Point:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
class Point2:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
Alias: TypeAlias = dict[Point, Point2]
l: Alias = {}
for k, v in l.items():
    k.scale(1)
    v.scale(1)

"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        point2 = file.get_symbol("Point2")
        scale = point.get_method("scale")
        scale2 = point2.get_method("scale")
        assert len(scale.usages) == 1
        assert len(scale2.usages) == 1
        scale.rename("scale2")
        scale2.rename("scale3")
    # language=python
    assert (
        file.content.strip()
        == """
from typing import TypeAlias

class Point:
    def __init__(self):
        pass
    def scale2(cls, n: int):
        pass
class Point2:
    def __init__(self):
        pass
    def scale3(cls, n: int):
        pass
Alias: TypeAlias = dict[Point, Point2]
l: Alias = {}
for k, v in l.items():
    k.scale2(1)
    v.scale3(1)
""".strip()
    )


def test_class_definition_usages_stdlib_generic_dict_alias_dataclass(tmpdir) -> None:
    FILENAME = "test.py"
    # language=python
    FILE_CONTENT = """
from typing import TypeAlias

class Point:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
class Point2:
    def __init__(self):
        pass
    def scale(cls, n: int):
        pass
Alias: TypeAlias = dict[Point, Point2]
class Wrapper:
    elems: Alias
l: Wrapper = Wrapper()
for k, v in l.elems.items():
    k.scale(1)
    v.scale(1)

"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        point2 = file.get_symbol("Point2")
        scale = point.get_method("scale")
        scale2 = point2.get_method("scale")
        assert len(scale.usages) == 1
        assert len(scale2.usages) == 1
        scale.rename("scale2")
        scale2.rename("scale3")
    # language=python
    assert (
        file.content.strip()
        == """
from typing import TypeAlias

class Point:
    def __init__(self):
        pass
    def scale2(cls, n: int):
        pass
class Point2:
    def __init__(self):
        pass
    def scale3(cls, n: int):
        pass
Alias: TypeAlias = dict[Point, Point2]
class Wrapper:
    elems: Alias
l: Wrapper = Wrapper()
for k, v in l.elems.items():
    k.scale2(1)
    v.scale3(1)
""".strip()
    )
