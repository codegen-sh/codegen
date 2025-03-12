# TODO: this file needs to be broken up into API specific tests
from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session

if TYPE_CHECKING:
    from codegen.sdk.python import PyFunction


def test_basic(tmpdir) -> None:
    # language=python
    content = """
from a.b import (c as d, e as f)

def foo():  # none returned
    return 5

def bar(x, y, z):  # trivial case
    return foo(1, 2)

def bar2(x, y, z):  # composition
    x = foo() + bar()
    y = foo(bar())

def baz():  # less trivial - includes composition etc.
    if True:
        return f(1, 2, 3)  # simple case
    else:
        return d(f(1, 2, 3), 5, 6)

"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # =====[ foo - none returned ]=====
        f: PyFunction = file.get_function("foo")
        calls = f.function_calls
        assert len(calls) == 0

        # =====[ bar - one returned ]=====
        g: PyFunction = file.get_function("bar")
        calls = g.function_calls
        assert len(calls) == 1
        call = calls[0]
        assert call.name == "foo"
        assert len(call.args) == 2

        # =====[ bar2 - composition ]=====
        h: PyFunction = file.get_function("bar2")
        calls = h.function_calls
        assert len(calls) == 4
        call = calls[0]
        assert call.name == "foo"
        assert len(call.args) == 0
        call = calls[1]
        assert call.name == "bar"
        assert len(call.args) == 0
        call = calls[2]
        assert call.name == "foo"
        assert len(call.args) == 1
        call = calls[3]
        assert call.name == "bar"
        assert len(call.args) == 0


def test_get_arg_kwarg_found(tmpdir) -> None:
    # language=python
    content = """
from a.b import (c as d, e as f)

def foo(arg1, arg2):
    return arg1

def bar(x, y, z):  # trivial case
    return foo(arg1=1, arg2=2)
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        g = file.get_function("bar")
        calls = g.function_calls
        assert len(calls) == 1
        call = calls[0]
        first_arg = call.get_arg_by_parameter_name("arg1")
        assert first_arg.index == 0
        assert first_arg.value == "1"
        assert first_arg.name == "arg1"


def test_set_kwarg(tmpdir) -> None:
    # language=python
    content = """
from a.b import (c as d, e as f)

def foo(arg0, arg1, arg2, arg3 = None,*, arg4 = None, arg5 = None, arg6 = None, arg8 = None):
    return arg1

def bar(x, y, z):  # trivial case
    return foo(0, 1, arg2=2, arg7=3, arg8=8)
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        g = file.get_function("bar")
        calls = g.function_calls
        assert len(calls) == 1
        call = calls[0]
        call.set_kwarg("arg0", "2", override_existing=False)
        call.set_kwarg("arg1", "2")
        call.set_kwarg("arg2", "3", override_existing=False)
        call.set_kwarg("arg4", "4", create_on_missing=False)
        call.set_kwarg("arg5", "5", create_on_missing=True)
        call.set_kwarg("arg7", "8")
    # language=python
    assert (
        file.content.strip()
        == """
from a.b import (c as d, e as f)

def foo(arg0, arg1, arg2, arg3 = None,*, arg4 = None, arg5 = None, arg6 = None, arg8 = None):
    return arg1

def bar(x, y, z):  # trivial case
    return foo(arg0=0, arg1=2, arg2=2, arg7=8, arg5=5, arg8=8)
    """.strip()
    )


def test_get_arg_kwarg_not_found(tmpdir) -> None:
    # language=python
    content = """
from a.b import (c as d, e as f)

def foo(arg1, arg2):
    return arg1

def bar(x, y, z):  # trivial case
    return foo(arg1=1, arg2=2)
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        g: PyFunction = file.get_function("bar")
        calls = g.function_calls
        assert len(calls) == 1
        call = calls[0]
        bad_arg = call.get_arg_by_parameter_name("arg3")
        assert bad_arg is None


def test_get_arg_no_kwargs(tmpdir) -> None:
    # language=python
    content = """
from a.b import (c as d, e as f)

def foo(arg1, arg2):
    return arg1

def bar(x, y, z):  # trivial case
    return foo(arg1=1, 2)
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        g: PyFunction = file.get_function("bar")
        calls = g.function_calls
        assert len(calls) == 1
        call = calls[0]
        first_arg = call.get_arg_by_parameter_name("arg1")
        assert first_arg.index == 0
        assert first_arg.value == "1"
        assert first_arg.name == "arg1"

        second_arg = call.get_arg_by_parameter_name("arg2")
        assert second_arg.index == 1
        assert second_arg.value == "2"
        assert second_arg.name is None


def test_get_function_definition_local_function(tmpdir) -> None:
    # language=python
    content = """
from a.b import (c as d, e as f)

def foo(arg1, arg2):
    return arg1

def bar(x, y, z):  # trivial case
    return foo(arg1=1, 2)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        bar_function: PyFunction = file.get_function("bar")
        foo_call = bar_function.function_calls[0]
        foo_def = foo_call.function_definition
        assert foo_def == file.get_symbol("foo")


def test_get_function_definition_constructor_implict(tmpdir) -> None:
    # language=python
    content = """

class Foo:
    pass
def bar(x, y, z):  # trivial case
    return Foo(arg1=1, 2)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        bar_function: PyFunction = file.get_function("bar")
        foo_call = bar_function.function_calls[0]
        foo_def = foo_call.resolved_value
        assert foo_call.function_definition == file.get_symbol("Foo")
        assert foo_def == file.get_symbol("Foo")


def test_get_function_definition_imported_function(tmpdir) -> None:
    tmpdir.mkdir("test_get_function_definition_imported_function")
    # language=python
    file1 = """
def foo(arg1, arg2):
    return arg1
        """
    # language=python
    file2 = """
from file1 import foo

def bar(x, y, z):  # trivial case
    return foo(arg1=1, 2)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": file1, "file2.py": file2}) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")

        bar_function: PyFunction = file2.get_function("bar")
        foo_call = bar_function.function_calls[0]
        foo_def = foo_call.function_definition
        assert foo_def == file1.get_symbol("foo")


def test_get_function_definition_local_method(tmpdir) -> None:
    # language=python
    content = """
from a.b import (c as d, e as f)

class MyClass:
    def foo(self, arg1, arg2):
        return arg1

def bar(x, y, z):  # trivial case
    c = MyClass()
    return c.foo(arg1=1, 2)
        """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        bar_function: PyFunction = file.get_function("bar")
        class_call = bar_function.function_calls[0]
        class_def = class_call.function_definition
        assert class_def == file.get_class("MyClass")

        method_call = bar_function.function_calls[1]
        method_def = method_call.function_definition
        # assert method_def == file.get_method("MyClass").get_method("foo") # TODO: requires local var parsing


def test_get_function_definition_imported_method(tmpdir) -> None:
    # language=python
    file1 = """
class MyClass:
    def foo(self, arg1, arg2):
        return arg1
            """
    # language=python
    file2 = """
from file1 import MyClass

def bar(x, y, z):  # trivial case
    c = MyClass()
    return c.foo(arg1=1, 2)
        """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": file1, "file2.py": file2}) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")

        bar_function: PyFunction = file2.get_function("bar")
        class_call = bar_function.function_calls[0]
        class_def = class_call.function_definition
        assert class_def == file1.get_class("MyClass")

        method_call = bar_function.function_calls[1]
        method_def = method_call.function_definition
        # assert method_def == file1.get_method("MyClass").get_method("foo") # TODO: requires local var parsing


def test_get_function_definition_imported_from_file(tmpdir) -> None:
    # language=python
    file1 = """
    class MyClass:
        def foo(self, arg1, arg2):
            return arg1
                """
    # language=python
    file2 = """
    from dir import file1

    def bar(x, y, z):  # trivial case
        c = file1.MyClass()
        return c.foo(arg1=1, 2)
            """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": file1, "file2.py": file2}) as codebase:
        file1 = codebase.get_file("dir/file1.py")
        file2 = codebase.get_file("file2.py")

        bar_function: PyFunction = file2.get_function("bar")
        class_call = bar_function.function_calls[0]
        class_def = class_call.function_definition
        assert class_def == file1.get_class("MyClass")

        method_call = bar_function.function_calls[1]
        method_def = method_call.function_definition
        # assert method_def == file1.get_method("MyClass").get_method("foo") # TODO: requires local var parsing


def test_get_function_definition_imported_as_alias(tmpdir) -> None:
    # language=python
    file1 = """
class MyClass:
    def foo(self, arg1, arg2):
        return arg1
    """
    # language=python
    file2 = """
from dir import file1 as f

def bar(x, y, z):  # trivial case
    c = f.MyClass()
    return c.foo(arg1=1, 2)
        """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": file1, "file2.py": file2}) as codebase:
        file1 = codebase.get_file("dir/file1.py")
        file2 = codebase.get_file("file2.py")

        bar_function: PyFunction = file2.get_function("bar")
        class_call = bar_function.function_calls[0]
        class_def = class_call.function_definition
        assert class_def == file1.get_class("MyClass")

        method_call = bar_function.function_calls[1]
        method_def = method_call.function_definition
        # assert method_def == file1.get_method("MyClass").get_method("foo") # TODO: requires local var parsing


def test_get_function_definition_indirect_import(tmpdir) -> None:
    # language=python
    file0 = """
def square(x):
    return x * x
    """
    # language=python
    file1 = """
from dir.file0 import square

class MyClass:
    def foo(self, arg1, arg2):
        return arg1
    """
    # language=python
    file2 = """
from dir.file1 import square

def bar(x):
    return square(x)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file0.py": file0, "dir/file1.py": file1, "file2.py": file2}) as codebase:
        file0 = codebase.get_file("dir/file0.py")
        file2 = codebase.get_file("file2.py")

        bar_function: PyFunction = file2.get_function("bar")
        square_call = bar_function.function_calls[0]
        square_def = square_call.function_definition
        assert square_def == file0.get_function("square")


def test_function_call_chain(tmpdir) -> None:
    # language=python
    content = """
def foo():
    a(b(c()))

def bar():
    a().b().c()

def bat():
    x.y.z.func()

def baz():
    x.a().y.b().z.c()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # Check foo
        foo = file.get_function("foo")
        calls = foo.function_calls
        assert len(calls) == 3
        a = calls[0]
        b = calls[1]
        c = calls[2]

        assert a.name == "a"
        assert b.name == "b"
        assert c.name == "c"
        assert a.source == "a(b(c()))"
        assert b.source == "b(c())"
        assert c.source == "c()"
        assert a.extended_source == "a(b(c()))"
        assert b.extended_source == "b(c())"
        assert c.extended_source == "c()"
        assert a.predecessor is None
        assert b.predecessor is None
        assert c.predecessor is None

        # Check bar
        bar = file.get_function("bar")
        calls = bar.function_calls
        assert len(calls) == 3
        c = calls[0]
        b = calls[1]
        a = calls[2]

        assert a.name == "a"
        assert b.name == "b"
        assert c.name == "c"
        assert a.source == "a()"
        assert b.source == "b()"
        assert c.source == "c()"
        assert a.extended_source == "a()"
        assert b.extended_source == "a().b()"
        assert c.extended_source == "a().b().c()"
        assert a.predecessor is None
        assert b.predecessor == a
        assert c.predecessor == b

        # Check bat
        bat = file.get_function("bat")
        calls = bat.function_calls
        assert len(calls) == 1
        func = calls[0]

        assert func.full_name == "x.y.z.func"
        assert func.source == "x.y.z.func()"
        assert func.extended_source == "x.y.z.func()"
        assert func.predecessor is None

        # Check baz
        baz = file.get_function("baz")
        calls = baz.function_calls
        assert len(calls) == 3
        c = calls[0]
        b = calls[1]
        a = calls[2]

        assert a.name == "a"
        assert b.name == "b"
        assert c.name == "c"
        assert a.source == "x.a()"
        assert b.source == "y.b()"
        assert c.source == "z.c()"
        assert a.extended_source == "x.a()"
        assert b.extended_source == "x.a().y.b()"
        assert c.extended_source == "x.a().y.b().z.c()"
        assert a.predecessor is None
        assert b.predecessor == a
        assert c.predecessor == b


def test_function_call_chain_base(tmpdir) -> None:
    # language=python
    content = """
def foo():
    a().b().c()

def bat():
    x.y.z.func()

def baz():
    x.a().y.b().z.c()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # Check foo
        foo = file.get_function("foo")
        calls = foo.function_calls
        assert len(calls) == 3
        c = calls[0]
        b = calls[1]
        a = calls[2]

        # Check call chain
        assert c.call_chain == [a, b, c]
        assert b.call_chain == [a, b, c]
        assert a.call_chain == [a, b, c]

        # Check base
        assert c.base == a.get_name()
        assert b.base == a.get_name()
        assert a.base == a.get_name()

        # Check bat
        bat = file.get_function("bat")
        calls = bat.function_calls
        assert len(calls) == 1
        func = calls[0]

        # Check call chain and base
        assert func.call_chain == [func]
        assert func.base.source == "x"

        # Check baz
        baz = file.get_function("baz")
        calls = baz.function_calls
        assert len(calls) == 3
        c = calls[0]
        b = calls[1]
        a = calls[2]

        # Check call chain
        assert c.call_chain == [a, b, c]
        assert b.call_chain == [a, b, c]
        assert a.call_chain == [a, b, c]

        # Check base
        assert c.base.source == "x"
        assert b.base.source == "x"
        assert a.base.source == "x"


def test_function_call_chain_nested(tmpdir) -> None:
    # language=python
    content = """
def foo():
    # Nested function calls - each call should be independent
    a(b(c()))
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        foo = file.get_function("foo")
        calls = foo.function_calls
        assert len(calls) == 3
        a = calls[0]
        b = calls[1]
        c = calls[2]

        # Each call should be independent - no predecessors
        assert a.predecessor is None
        assert b.predecessor is None
        assert c.predecessor is None

        # No successors since they're nested, not chained
        assert a.successor is None
        assert b.successor is None
        assert c.successor is None

        # Call chain for each should only include itself
        assert a.call_chain == [a]
        assert b.call_chain == [b]
        assert c.call_chain == [c]

        # Verify source strings are correct
        assert a.source == "a(b(c()))"
        assert b.source == "b(c())"
        assert c.source == "c()"


def test_function_call_chain_successor(tmpdir) -> None:
    # language=python
    content = """
def foo():
    a().b().c()

def bat():
    x.y.z.func()

def baz():
    x.a().y.b().z.c()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # Check foo
        foo = file.get_function("foo")
        calls = foo.function_calls
        assert len(calls) == 3
        c = calls[0]
        b = calls[1]
        a = calls[2]

        # Check successors
        assert a.successor == b
        assert b.successor == c
        assert c.successor is None

        # Check bat
        bat = file.get_function("bat")
        calls = bat.function_calls
        assert len(calls) == 1
        func = calls[0]

        # No successor since it's a single function call
        assert func.successor is None

        # Check baz
        baz = file.get_function("baz")
        calls = baz.function_calls
        assert len(calls) == 3
        c = calls[0]
        b = calls[1]
        a = calls[2]

        # Check successors
        assert a.successor == b
        assert b.successor == c
        assert c.successor is None


def test_function_call_chain_hard(tmpdir) -> None:
    # language=python
    content = """
def foo():
    select(Table).where(
        condition1 = 1,
        condition2 = thing().other_thing().get_thing()
    ).group_by(
        column1,
        column2
    ).order_by(
        column1,
        column2
    ).limit(10)
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # Check foo
        foo = file.get_function("foo")
        calls = foo.function_calls
        assert len(calls) == 8

        limit = calls[0]
        order_by = calls[1]
        group_by = calls[2]
        where = calls[3]
        select = calls[4]

        # Check names
        assert limit.name == "limit"
        assert order_by.name == "order_by"
        assert group_by.name == "group_by"
        assert where.name == "where"
        assert select.name == "select"

        # Check predecessors
        assert limit.predecessor == order_by
        assert order_by.predecessor == group_by
        assert group_by.predecessor == where
        assert where.predecessor == select
        assert select.predecessor is None

        # Check sources
        assert limit.source == "limit(10)"
        assert "order_by(" in order_by.source
        assert "group_by(" not in order_by.source

        # Check extended sources
        assert "order_by(" in order_by.extended_source
        assert "group_by(" in order_by.extended_source

        # Check parameters
        assert limit.args[0].value == "10"
        assert len(order_by.args) == 2
        assert select.args[0].value == "Table"
        assert where.args[0].name == "condition1"
        assert where.args[0].value == "1"


def test_imported_function_call_in_decorator(tmpdir) -> None:
    # language=python
    def_content = """
def generate_data() -> list[tuple[str, int]]:
    data = [("a", 1), ("b", 2)]
    return data
    """
    # language=python
    usage_content = """
from def import generate_data

@pytest.mark.parametrize(
    "str_val, int_val",
    generate_data(),  # <-- Not getting caught
)
def test_something(str_val: str, int_val: int) -> None:
    assert isinstance(str_val, str)
    assert isinstance(int_val, int)"""
    with get_codebase_session(tmpdir=tmpdir, files={"def.py": def_content, "usage.py": usage_content}) as codebase:
        def_file = codebase.get_file("def.py")
        usage_file = codebase.get_file("usage.py")

        func_def = def_file.get_function("generate_data")
        assert len(func_def.call_sites) == 1
        assert func_def.call_sites[0].file == usage_file


def test_local_function_call_in_decorator(tmpdir) -> None:
    # language=python
    content = """
def generate_data() -> list[tuple[str, int]]:
    data = [("a", 1), ("b", 2)]
    return data

@pytest.mark.parametrize(
    "str_val, int_val",
    generate_data(),  # <-- Not getting caught
)
def test_something(str_val: str, int_val: int) -> None:
    assert isinstance(str_val, str)
    assert isinstance(int_val, int)"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")

        func_def = file.get_function("generate_data")
        assert len(func_def.call_sites) == 1
        assert func_def.call_sites[0].file == file


def test_named_parameters(tmpdir) -> None:
    # language=python
    content = """
def foo(arg1, arg2):
    return arg1 + arg2

def bar(x, y, z):
    a = foo(arg1=x, y)
    return a
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")
        funcs = file.get_symbol("foo")
        calls = funcs.call_sites
        assert len(calls) == 1
        assert calls[0].args[0].name == "arg1"
        assert calls[0].args[1].name is None
        assert calls[0].args[0].value == "x"
        assert calls[0].args[1].value == "y"
        assert calls[0].args[0].is_named is True
        assert calls[0].args[1].is_named is False


def test_insert_after(tmpdir) -> None:
    # language=python
    content = """
def foo():  # none returned
    return 5

def bar(x, y, z):  # trivial case
    foo(1, 2)

def bar2(x, y, z):  # composition
    foo()
    bar()
    y = foo(bar())
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        bar: PyFunction = file.get_function("bar")
        bar.function_calls[0].insert_after("a = 1", fix_indentation=True)
        bar2: PyFunction = file.get_function("bar2")
        bar2.function_calls[1].insert_after("a = 1", fix_indentation=True)
    # language=python
    assert (
        file.content
        == """
def foo():  # none returned
    return 5

def bar(x, y, z):  # trivial case
    foo(1, 2)
    a = 1

def bar2(x, y, z):  # composition
    foo()
    bar()
    a = 1
    y = foo(bar())
"""
    ), file.content


def test_function_call_chain_rename(tmpdir) -> None:
    # language=python
    content = """
def foo():
    a(
        a(),
        a(),
    ).a(
    )
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        for call in file.function_calls:
            call.set_name("b")
    # language=python
    assert (
        file.content
        == """
def foo():
    b(
        b(),
        b(),
    ).b(
    )
"""
    )
