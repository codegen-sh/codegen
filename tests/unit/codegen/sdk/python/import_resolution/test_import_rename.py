from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_import_rename_usage(tmpdir) -> None:
    # language=python
    content1 = """
def foo1():
    return 1

def foo2():
    return 1
    """
    # language=python
    content2 = """
from file1 import foo1, foo2

def bar1():
    return foo1()
    """
    # language=python
    content3 = """
from file2 import foo2

def bar2():
    return foo2()
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2, "file3.py": content3}) as codebase:
        file2 = codebase.get_file("file2.py")
        file3 = codebase.get_file("file3.py")

        imp = file2.get_import("foo2")
        imp.rename("updated_foo2")

    assert "from file1 import foo1, updated_foo2" in file2.content
    assert "from file2 import updated_foo2" in file3.content
    assert "return updated_foo2()" in file3.content


def test_import_rename_usage_with_alias(tmpdir) -> None:
    # language=python
    content1 = """
def foo1():
    return 1

def foo2():
    return 1
    """
    # language=python
    content2 = """
from file1 import foo1, foo2

def bar1():
    return foo1()
    """
    # language=python
    content3 = """
from file2 import foo2 as f2

def bar2():
    return f2()
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2, "file3.py": content3}) as codebase:
        file2 = codebase.get_file("file2.py")
        file3 = codebase.get_file("file3.py")

        imp = file2.get_import("foo2")
        imp.rename("updated_foo2")

    assert "from file1 import foo1, updated_foo2" in file2.content
    assert "from file2 import updated_foo2" in file3.content
    assert "return f2()" in file3.content


def test_import_rename_indirect_import_usage(tmpdir) -> None:
    # language=python
    content1 = """
def foo1():
    return 1

def foo2():
    return 1
    """
    # language=python
    content2 = """
from file1 import foo1, foo2 as f2

def bar1():
    return f2()
    """
    # language=python
    content3 = """
from file2 import f2 as foo2

def bar2():
    return foo2()
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2, "file3.py": content3}) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")
        file3 = codebase.get_file("file3.py")

        imp = file2.get_import("f2")
        imp.rename("updated_foo2")

    assert file1.content == content1
    # language=python
    assert (
        file2.content
        == """
from file1 import foo1, updated_foo2 as f2

def bar1():
    return f2()
    """
    )
    # language=python
    assert (
        file3.content
        == """
from file2 import f2 as foo2

def bar2():
    return foo2()
    """
    )


def test_multi_import_rename_with_alias(tmpdir) -> None:
    """NOT the alias, just the name"""
    # =====[ Simple ]=====
    # language=python
    content = """
import a  # test one
from b.c import d  # test two
from d.f import (g as h, i as j)  # test three
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # =====[ Rename d.f ]=====
        imp = file.get_import("h")
        imp.rename("XYZ")

    assert "from d.f import (XYZ as h, i as j)  # test three" in file.content
    assert file.get_import("h").symbol_name.source == "XYZ"

    # =====[ Rename b.c ]=====
    imp = file.get_import("d")
    imp.rename("ABC")
    codebase.ctx.commit_transactions()
    assert "from b.c import ABC  # test two" in file.content
    assert file.get_import("ABC").symbol_name.source == "ABC"

    # =====[ Rename a ]=====
    imp = file.get_import("a")
    imp.rename("z")
    codebase.ctx.commit_transactions()
    assert "import z  # test one" in imp.file.content
    assert file.get_import("z").symbol_name.source == "z"


def test_import_rename_with_import_loop(tmpdir) -> None:
    # language=python
    content1 = """
from file2 import xyz
"""
    # language=python
    content2 = """
from file1 import xyz
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")

        imp = file1.get_import("xyz")
        imp.rename("zyx")

    assert "from file2 import zyx" in file1.content
    assert "from file1 import zyx" in file2.content


def test_import_rename_module_import(tmpdir) -> None:
    # language=python
    content1 = """
from dir import file3   # module import

def bar():
    return file3.foo()
    """
    # language=python
    content2 = """
from dir import file1 as f1     # module import with alias

def foo():
    return f1.bar()
    """
    # language=python
    content3 = """
from dir.file1 import file3

def buz():
    return file3.foo()
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content1, "dir/file2.py": content2, "dir/file3.py": content3}) as codebase:
        file1 = codebase.get_file("dir/file1.py")
        file2 = codebase.get_file("dir/file2.py")
        file3 = codebase.get_file("dir/file3.py")

        file1.get_import("file3").rename("renamed_file3")
        codebase.commit()
        file2.get_import("f1").rename("renamed_file1")

    # language=python
    assert (
        file1.content
        == """
from dir import renamed_file3   # module import

def bar():
    return renamed_file3.foo()
    """
    )
    # language=python
    assert (
        file2.content
        == """
from dir import renamed_file1 as f1     # module import with alias

def foo():
    return f1.bar()
    """
    )
    # language=python
    assert (
        file3.content
        == """
from dir.file1 import renamed_file3

def buz():
    return renamed_file3.foo()
    """
    )
