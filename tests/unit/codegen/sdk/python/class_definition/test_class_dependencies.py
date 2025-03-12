from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.dataclasses.usage import UsageKind, UsageType
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import SymbolType


def test_class_dependencies(tmpdir) -> None:
    # language=python
    content = """
import time
from a.b import c
from d import E

class B:
    pass

class A(B, c.D):
    def __init__(self):
        b_new = B()
        e_new = E()

def f(a: A, b: int, c):
    a_new = A()
    b_new = B()
    time.sleep(10)
    pass

def g(tmpdir):
    time.sleep(10)
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # =====[ Symbols ]=====]
        A = file.get_symbol("A")
        B = file.get_symbol("B")
        f = file.get_symbol("f")

        # ==== [ Imports ] ====
        time = file.get_import("time")
        c = file.get_import("c")
        E = file.get_import("E")

        # =====[ Symbol types ]=====
        assert A.symbol_type == SymbolType.Class
        assert B.symbol_type == SymbolType.Class
        assert f.symbol_type == SymbolType.Function

        # =====[ A ]=====
        edges = A.dependencies
        assert any((isinstance(edge, Symbol) and edge.name == "B") for edge in edges)
        assert any((isinstance(edge, Import) and edge.alias.source == "c") for edge in edges)
        assert any((isinstance(edge, Import) and edge.alias.source == "E") for edge in edges)

        # =====[ f ]=====
        edges = f.dependencies
        assert any((isinstance(edge, Symbol) and edge.name == "A") for edge in edges)
        assert any((isinstance(edge, Import) and edge.alias.source == "time") for edge in edges)
        assert len(edges) == 4

        # =====[ Edge Test ] =====
        edge_data = codebase.ctx.get_edge_data(f.node_id, A.node_id)
        types = [edge.usage.kind for edge in edge_data]
        assert len(types) == 1
        assert types[0] == UsageKind.TYPE_ANNOTATION

        f_body_assignment = f.code_block.statements[0].assignments[0]
        edge_data = codebase.ctx.get_edge_data(f_body_assignment.node_id, A.node_id)
        types = [edge.usage.kind for edge in edge_data]
        assert len(types) == 1
        assert UsageKind.BODY in types


def test_class_dependencies_in_decorators(tmpdir) -> None:
    # language=python
    content = """
from d.e.f import MyType
from a.b.c import my_decorator
from g.h.i import my_module
from dataclasses import dataclass

@dataclass
class A:
    b: int
    c: MyType
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        A_deps = file.get_class("A").dependencies
        assert any((isinstance(dep, Import) and dep.alias.source == "MyType") for dep in A_deps)
        assert any((isinstance(dep, Import) and dep.alias.source == "dataclass") for dep in A_deps)


def test_class_dependencies_in_attribute(tmpdir) -> None:
    # language=python
    content = """
from a import Foo

class Bar(Baz):
    var = ma.Nested(Foo)
"""

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        assert len(file.symbols) == 1
        bar = file.get_class("Bar")
        assert bar.name == "Bar"
        assert set(dep.name for dep in bar.dependencies) == {"Foo"}


def test_class_dependencies_with_local_decorators(tmpdir) -> None:
    # language=python
    content = """
def decorator_a(cls):
    return cls

def decorator_b(cls):
    return cls

@decorator_a
@decorator_b
class MyClass:
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")
        my_class = file.get_class("MyClass")
        assert len(my_class.dependencies) == 2
        assert set(my_class.dependencies) == {
            file.get_function("decorator_a"),
            file.get_function("decorator_b"),
        }


def test_class_dependencies_with_imported_decorators(tmpdir) -> None:
    # language=python
    content1 = """
from file2 import decorator_a, decorator_b

@decorator_a
@decorator_b
class MyClass:
    pass
"""
    # language=python
    content2 = """
def decorator_a(cls):
    return cls

def decorator_b(cls):
    return cls
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file1 = codebase.get_file("file1.py")
        my_class = file1.get_class("MyClass")
        assert len(my_class.dependencies) == 2
        assert set(my_class.dependencies) == {
            file1.get_import("decorator_a"),
            file1.get_import("decorator_b"),
        }


def test_class_dependencies_with_chained_imports(tmpdir) -> None:
    # language=python
    content1 = """
import file2

@file2.decorator_a
@file2.decorator_b
class MyClass:
    pass
"""
    # language=python
    content2 = """
def decorator_a(cls):
    return cls

def decorator_b(cls):
    return cls
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file1 = codebase.get_file("file1.py")
        my_class = file1.get_class("MyClass")
        assert set(my_class.dependencies) == {file1.imports[0]}
        assert len(my_class.dependencies) == 1


def test_class_dependencies_in_attribute_with_import_conflict(tmpdir) -> None:
    # language=python
    content = """
xyz = 1

class A:
    xyz: int = 2  # should not match `xyz` above
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        symbol = file.get_symbol("A")
        deps = symbol.dependencies
        assert len(deps) == 0


def test_class_method_dependencies(tmpdir) -> None:
    # language=python
    content = """
from a.b.c import imp as imp_rename

def f(tmpdir):
    pass

class A(tmpdir):
    def my_func(tmpdir):
        f()
        imp_rename.test()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        symbol = file.get_class("A")
        method = symbol.get_method("my_func")
        assert len(method.dependencies) == 2


def test_class_dependencies_with_usage_types(tmpdir) -> None:
    # language=python
    content1 = """
from file2 import ClassA as RenamedClass
import file2

class LocalClass:
    def method(self):
        # Direct usage
        obj = RenamedClass()
        # Direct usage of file2, chained usage of ClassB
        other = file2.ClassB()
"""
    # language=python
    content2 = """
class ClassA:
    pass

class ClassB:
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file1 = codebase.get_file("file1.py")
        local_class = file1.get_class("LocalClass")
        method = local_class.get_method("method")

        # Test DIRECT dependencies (RenamedClass and file2)
        direct_deps = method.dependencies(UsageType.DIRECT)
        assert len(direct_deps) == 2
        assert any(dep.name == "RenamedClass" for dep in direct_deps)
        assert any(dep.name == "file2" for dep in direct_deps)

        # Test CHAINED dependencies (ClassB accessed through file2)
        chained_deps = method.dependencies(UsageType.CHAINED)
        assert len(chained_deps) == 1
        assert any(dep.name == "ClassB" for dep in chained_deps)

        # Test combined DIRECT | CHAINED
        all_deps = method.dependencies(UsageType.DIRECT | UsageType.CHAINED)
        assert len(all_deps) == 3


def test_class_dependencies_with_aliased_imports(tmpdir) -> None:
    # language=python
    content1 = """
from file2 import BaseClass as AliasedBase
from file2 import HelperClass as AliasedHelper

class MyClass(AliasedBase):
    def method(self):
        return AliasedHelper()
"""
    # language=python
    content2 = """
class BaseClass:
    pass

class HelperClass:
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file1 = codebase.get_file("file1.py")
        my_class = file1.get_class("MyClass")

        # Test class DIRECT dependencies (both base class and helper used in method)
        direct_deps = my_class.dependencies(UsageType.DIRECT)
        assert len(direct_deps) == 2  # Both AliasedBase and AliasedHelper
        assert any(dep.name == "AliasedBase" for dep in direct_deps)
        assert any(dep.name == "AliasedHelper" for dep in direct_deps)

        # Test method dependencies (only helper used directly in method)
        method = my_class.get_method("method")
        method_deps = method.dependencies(UsageType.DIRECT)
        assert len(method_deps) == 1  # Just AliasedHelper
        assert any(dep.name == "AliasedHelper" for dep in method_deps)


def test_class_dependencies_with_indirect_usage(tmpdir) -> None:
    # language=python
    content1 = """
from file2 import BaseClass

class MyClass(BaseClass):  # INDIRECT usage of BaseClass through import
    pass

class AnotherClass(MyClass):  # DIRECT usage of MyClass (same file)
    pass
"""
    # language=python
    content2 = """
class BaseClass:
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file1 = codebase.get_file("file1.py")
        another_class = file1.get_class("AnotherClass")
        my_class = file1.get_class("MyClass")

        # Test MyClass dependencies
        my_class_deps = my_class.dependencies(UsageType.INDIRECT)
        assert len(my_class_deps) == 1  # BaseClass through import
        assert any(dep.name == "BaseClass" for dep in my_class_deps)

        # Test AnotherClass dependencies
        direct_deps = another_class.dependencies(UsageType.DIRECT)
        assert len(direct_deps) == 1  # MyClass in same file
        assert any(dep.name == "MyClass" for dep in direct_deps)

        indirect_deps = another_class.dependencies(UsageType.INDIRECT)
        assert len(indirect_deps) == 0  # BaseClass through import
