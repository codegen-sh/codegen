from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_rename_and_type_annotation(tmpdir) -> None:
    # language=python
    content1 = """
def foo(x, y=1):
    return x

def bar(y: int):
    return y

def baz(x: int, y: str, z: list[int]) -> str:
    return str(x) + y + z[0]
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1}) as codebase:
        file1 = codebase.get_file("file1.py")

        # =====[ Trivial case ]=====
        foo = file1.get_function("foo")
        param = foo.parameters[0]
        param.rename("x_new")
        param.set_type_annotation("int")
        param = foo.parameters[1]
        param.rename("y_new")
        param.set_type_annotation("int")
    foo = file1.get_function("foo")
    param = foo.parameters[0]
    assert param.type == "int"
    assert param.source == "x_new: int"
    param = foo.parameters[1]
    assert param.type == "int"
    assert param.source == "y_new: int=1"
    assert "def foo(x_new: int, y_new: int=1):" in foo.source

    # =====[ Already has a parameter ]=====
    bar = file1.get_function("bar")
    param = bar.parameters[0]
    param.set_type_annotation("str")
    param.rename("y_new")
    codebase.ctx.commit_transactions()
    bar = file1.get_function("bar")
    param = bar.parameters[0]
    assert param.type == "str"
    assert param.source == "y_new: str"
    assert "def bar(y_new: str):" in bar.source

    # =====[ Multiple parameters - replace middle one ]=====
    baz = file1.get_function("baz")
    param = baz.parameters[0]
    param.rename("x_new")
    param.set_type_annotation("str")
    param = baz.parameters[1]
    param.set_type_annotation("int")
    param.rename("y_new")
    codebase.ctx.commit_transactions()
    baz = file1.get_function("baz")
    param = baz.parameters[1]
    assert param.type == "int"
    assert "def baz(x_new: str, y_new: int, z: list[int]) -> str:" in baz.source


def test_parameter_rename_updates_call_sites_and_decorators(tmpdir) -> None:
    # language=python
    content1 = """
global_var = foo(a=12, b=34) + foo(a=56, b=78)

def foo(a, b):
    a = a + 1
    return a + b

@foo(a=global_var, b=foo(a=1, b=2))
def fizz(a, b):
    return foo(a=a, b=b) + foo(a=b, b=a)
"""
    # language=python
    content2 = """
from file1 import foo

my_global_var = foo(a=1, b=2) + foo(a=3, b=4)

@foo(a=1, b=foo(a=1, b=2))
def bar(x, y):
    return foo(a=123, b=321) + foo(a=321, b=123)

@foo(a=1, b=foo(a=1, b=2))
class MyClass:
    attr: int

    @foo(a=1, b=foo(a=1, b=2))
    def __init__(self):
        self.attr = foo(a=1, b=2) + foo(a=3, b=4)
"""
    # language=python
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")
        foo = file1.get_function("foo")

        foo.parameters[0].rename("renamed_a")
        foo.parameters[1].rename("renamed_b")
        codebase.commit()

        assert (
            file1.content
            == """
global_var = foo(renamed_a=12, renamed_b=34) + foo(renamed_a=56, renamed_b=78)

def foo(renamed_a, renamed_b):
    a = renamed_a + 1
    return a + renamed_b

@foo(renamed_a=global_var, renamed_b=foo(renamed_a=1, renamed_b=2))
def fizz(a, b):
    return foo(renamed_a=a, renamed_b=b) + foo(renamed_a=b, renamed_b=a)
"""
        )
        assert (
            file2.content
            == """
from file1 import foo

my_global_var = foo(renamed_a=1, renamed_b=2) + foo(renamed_a=3, renamed_b=4)

@foo(renamed_a=1, renamed_b=foo(renamed_a=1, renamed_b=2))
def bar(x, y):
    return foo(renamed_a=123, renamed_b=321) + foo(renamed_a=321, renamed_b=123)

@foo(renamed_a=1, renamed_b=foo(renamed_a=1, renamed_b=2))
class MyClass:
    attr: int

    @foo(renamed_a=1, renamed_b=foo(renamed_a=1, renamed_b=2))
    def __init__(self):
        self.attr = foo(renamed_a=1, renamed_b=2) + foo(renamed_a=3, renamed_b=4)
"""
        )


def test_parameter_rename_not_updates_nested_decorators(tmpdir) -> None:
    # language=python
    content1 = """
global_var = foo(a=12, b=34) + foo(a=56, b=78)

def foo(a, b):
    a = a + 1
    return a + b

@foo(a=global_var, b=foo(a=1, b=2))
def fizz(a, b):
    return foo(a=a, b=b) + foo(a=b, b=a)
"""
    # language=python
    content2 = """
from file1 import foo

my_global_var = foo(a=1, b=2) + x.foo(a=3, b=4)

@x.foo(a=1, b=foo(a=1, b=2))
def bar(x, y):
    return foo(a=123, b=321) + x.foo(a=321, b=123)

@foo(a=1, b=x.foo(a=1, b=2))
class MyClass:
    attr: int

    @foo(a=1, b=foo(a=1, b=2))
    def __init__(self):
        self.attr = x.foo(a=1, b=2) + foo(a=3, b=4)
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")
        foo = file1.get_function("foo")

        foo.parameters[0].rename("renamed_a")
        foo.parameters[1].rename("renamed_b")

    # language=python
    assert (
        file2.content
        == """
from file1 import foo

my_global_var = foo(renamed_a=1, renamed_b=2) + x.foo(a=3, b=4)

@x.foo(a=1, b=foo(renamed_a=1, renamed_b=2))
def bar(x, y):
    return foo(renamed_a=123, renamed_b=321) + x.foo(a=321, b=123)

@foo(renamed_a=1, renamed_b=x.foo(a=1, b=2))
class MyClass:
    attr: int

    @foo(renamed_a=1, renamed_b=foo(renamed_a=1, renamed_b=2))
    def __init__(self):
        self.attr = x.foo(a=1, b=2) + foo(renamed_a=3, renamed_b=4)
"""
    )
