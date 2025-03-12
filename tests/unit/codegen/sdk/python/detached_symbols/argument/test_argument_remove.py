import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session


@pytest.mark.skip("BROKEN! todo @edward")
def test_argument_remove_multiline_params(tmpdir) -> None:
    # language=python
    content = """
a = foo(
    x,
    something,
    else = 1
)
"""

    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")

        # Test remove something


def test_argument_remove(tmpdir) -> None:
    # language=python
    content1 = """
def foo(a, b, c):
    return a + b + c

def bar(x):
    return x
    """
    # language=python
    content2 = """
from file1 import bar, foo

def test():
    foo(1, 2, 3)
    foo(1,
        2, # some comment here
        3
    )
    bar("asdf")
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")
        foo = file1.get_function("foo")
        bar = file1.get_function("bar")

        bar_call_sites = bar.call_sites
        assert len(bar_call_sites) == 1
        bar_call_sites[0].args[0].remove()

    assert "bar()" in file2.content

    foo_calls = foo.call_sites
    assert len(foo_calls) == 2
    foo_calls = sorted(foo_calls, key=lambda x: x.ts_node.start_byte)
    foo_calls[1].args[2].remove()
    codebase.ctx.commit_transactions()
    # language=python
    assert (
        file2.content
        == """
from file1 import bar, foo

def test():
    foo(1, 2, 3)
    foo(1,
        2, # some comment here
    )
    bar()
    """
    )
    foo_calls[1].args[0].remove()
    codebase.ctx.commit_transactions()
    # language=python
    assert (
        file2.content
        == """
from file1 import bar, foo

def test():
    foo(1, 2, 3)
    foo(2, # some comment here
    )
    bar()
    """
    )

    foo_calls[0].args[2].remove()
    codebase.ctx.commit_transactions()
    assert "foo(1, 2)" in file2.content
    foo_calls[0].args[1].remove()
    codebase.ctx.commit_transactions()
    assert "foo(1)" in file2.content
    foo_calls[0].args[0].remove()
    codebase.ctx.commit_transactions()
    assert "foo()" in file2.content
