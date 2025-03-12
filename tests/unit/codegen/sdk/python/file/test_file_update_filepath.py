import os

from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_rename_file(tmpdir) -> None:
    # language=python
    foo = """
def foo():
    return 1
"""
    # language=python
    bar = """
from foo_file import foo

def bar():
    return foo()
"""
    foo_filepath = "foo_file.py"
    bar_filepath = "bar_file.py"
    with get_codebase_session(tmpdir=tmpdir, files={foo_filepath: foo, bar_filepath: bar}, commit=True) as codebase:
        foo_file = codebase.get_file(foo_filepath)
        bar_file = codebase.get_file(bar_filepath)

        new_file = "baz_file.py"
        foo_file.rename(new_file)

    assert not os.path.exists(tmpdir / foo_filepath)
    assert os.path.exists(tmpdir / new_file)
    assert not codebase.has_file(foo_filepath)
    assert codebase.get_file(new_file).filepath == new_file
    assert codebase.get_file(new_file).content == foo
    assert len(bar_file.imports) == 1
    assert "from baz_file import foo" in bar_file.content
    codebase.reset()
    for symbol in codebase.symbols:
        assert symbol.filepath != new_file
    for c in codebase.classes:
        assert c.filepath != new_file


def test_rename_file_no_extension(tmpdir) -> None:
    # language=python
    foo = """
def foo():
    return 1
"""
    # language=python
    bar = """
from foo_file import foo

def bar():
    return foo()
"""
    foo_filepath = "foo_file.py"
    bar_filepath = "bar_file.py"
    with get_codebase_session(tmpdir=tmpdir, files={foo_filepath: foo, bar_filepath: bar}, commit=True) as codebase:
        foo_file = codebase.get_file(foo_filepath)
        bar_file = codebase.get_file(bar_filepath)

        new_file = "baz_file.py"
        foo_file.rename("baz_file")

    assert not os.path.exists(tmpdir / foo_filepath)
    assert os.path.exists(tmpdir / new_file)
    assert not codebase.has_file(foo_filepath)
    assert codebase.get_file(new_file).filepath == new_file
    assert codebase.get_file(new_file).content == foo
    assert len(bar_file.imports) == 1
    assert "from baz_file import foo" in bar_file.content
    codebase.reset()
    for symbol in codebase.symbols:
        assert symbol.filepath != new_file
    for c in codebase.classes:
        assert c.filepath != new_file


def test_rename_file_no_sync(tmpdir) -> None:
    # language=python
    foo = """
def foo():
    return 1
"""
    # language=python
    bar = """
from foo_file import foo

def bar():
    return foo()
"""
    foo_filepath = "foo_file.py"
    bar_filepath = "bar_file.py"
    with get_codebase_session(tmpdir=tmpdir, files={foo_filepath: foo, bar_filepath: bar}, commit=True, sync_graph=False) as codebase:
        foo_file = codebase.get_file(foo_filepath)

        new_file = "baz_file.py"
        foo_file.rename(new_file)

    assert not os.path.exists(tmpdir / foo_filepath)
    assert os.path.exists(tmpdir / new_file)
    codebase.reset()
    for symbol in codebase.symbols:
        assert symbol.filepath != new_file
    for c in codebase.classes:
        assert c.filepath != new_file
    assert os.path.exists(tmpdir / foo_filepath)
    assert not os.path.exists(tmpdir / new_file)


def test_rename_file_nullifies_old_file(tmpdir) -> None:
    # language=python
    foo_content = """
def foo():
    return 1
"""
    foo_filepath = "foo_file.py"
    new_filepath = "new_file.py"

    with get_codebase_session(tmpdir=tmpdir, files={foo_filepath: foo_content}, commit=True) as codebase:
        file = codebase.get_file(foo_filepath)
        file.update_filepath(new_filepath)
        codebase.commit()

        new_file = codebase.get_file(new_filepath, optional=True)

        # Check that old file reference is None
        old_file = codebase.get_file(foo_filepath, optional=True)
        new_file = codebase.get_file(new_filepath)

        assert old_file is None
        assert new_file is not None
        assert new_file.content == foo_content

        # Verify file system state
        assert not os.path.exists(tmpdir / foo_filepath)
        assert os.path.exists(tmpdir / new_filepath)
