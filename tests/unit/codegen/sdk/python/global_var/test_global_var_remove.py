from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_global_var_remove(tmpdir) -> None:
    # language=python
    content = """
import os
import numpy

global_var = 1

def foo():
    return 1

def bar():
    return 2
        """
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")

        file.get_global_var("global_var").remove()

    # language=python
    assert (
        file.content
        == """
import os
import numpy

def foo():
    return 1

def bar():
    return 2
        """
    )


def test_global_var_remove_from_list(tmpdir) -> None:
    # language=python
    content = """
a = 1
b = func()
c = this_is_a_test()
d = do_something()
e = 5
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # Test remove c
        c = file.get_symbol("c")
        c.remove()

    assert "c = this_is_a_test()" not in file.source
    assert "a = 1" in file.source
    assert "b = func()" in file.source
    assert "d = do_something()" in file.source
    assert "e = 5" in file.source

    # Test remove a
    a = file.get_symbol("a")
    a.remove()
    codebase.ctx.commit_transactions()
    assert "a = 1" not in file.source
    assert "b = func()" in file.source
    assert "d = do_something()" in file.source
    assert "e = 5" in file.source

    # Test remove e
    e = file.get_symbol("e")
    e.remove()
    codebase.ctx.commit_transactions()
    assert "a = 1" not in file.source
    assert "b = func()" in file.source
    assert "d = do_something()" in file.source
    assert "e = 5" not in file.source


def test_global_var_remove_multiple_from_list(tmpdir) -> None:
    # language=python
    content = """
a = 1
b = func()
c = this_is_a_test()
d = do_something()
e = 5
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # Test remove c, a, then e
        file.get_symbol("c").remove()
        file.get_symbol("a").remove()
        file.get_symbol("e").remove()

        # Commit transactions

    assert "a = 1" not in file.source
    assert "c = this_is_a_test()" not in file.source
    assert "e = 5" not in file.source
    assert "b = func()" in file.source
    assert "d = do_something()" in file.source
    assert "e = 5" not in file.source
