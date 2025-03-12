from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_import_insert_before(tmpdir) -> None:
    # language=python
    content1 = """
def foo1(x, y):
    return x + y

def foo2(x, y):
    return x - y
    """
    # language=python
    content2 = """
from file1 import foo1

def bar(a, b):
    return a * b + foo1(a, b)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")

        file2.insert_before("from file1 import foo2")

    # language=python
    assert (
        file2.content
        == """from file1 import foo2

from file1 import foo1

def bar(a, b):
    return a * b + foo1(a, b)
    """
    )

    file1.insert_before("import numpy as np\n", fix_indentation=True)
    codebase.ctx.commit_transactions()
    # language=python
    assert (
        file1.content
        == """import numpy as np


def foo1(x, y):
    return x + y

def foo2(x, y):
    return x - y
    """
    )


def test_import_multi_remove_inline(tmpdir) -> None:
    # language=python
    content1 = """
def foo1():
    pass

def foo2():
    pass

def foo3():
    pass

def foo4():
    pass

def foo5():
    pass
"""
    # language=python
    content2 = """
from file1 import foo1, foo2, foo3, foo4

def bar(a, b):
    foo1()
    foo2()
    foo3()
    foo4()
    foo5()
    """

    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file2 = codebase.get_file("file2.py")

        remove_list = ["foo1", "foo2", "foo3"]

        for imp in file2.imports:
            if imp.name in remove_list:
                imp.remove()
    # language=python
    assert (
        file2.content
        == """
from file1 import foo4

def bar(a, b):
    foo1()
    foo2()
    foo3()
    foo4()
    foo5()
    """
    )


def test_import_multi_remove_inline_middle_nodes(tmpdir) -> None:
    # language=python
    content1 = """
def foo1():
    pass

def foo2():
    pass

def foo3():
    pass

def foo4():
    pass

def foo5():
    pass
"""
    # language=python
    content2 = """
from file1 import foo1, foo2, foo3, foo4

def bar(a, b):
    foo1()
    foo2()
    foo3()
    foo4()
    foo5()
    """

    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file2 = codebase.get_file("file2.py")

        remove_list = ["foo2", "foo3"]

        for imp in file2.imports:
            if imp.name in remove_list:
                imp.remove()
    # language=python
    assert (
        file2.content
        == """
from file1 import foo1, foo4

def bar(a, b):
    foo1()
    foo2()
    foo3()
    foo4()
    foo5()
    """
    )


def test_import_multi_remove_inline_end_nodes(tmpdir) -> None:
    # language=python
    content1 = """
def foo1():
    pass

def foo2():
    pass

def foo3():
    pass

def foo4():
    pass

def foo5():
    pass
"""
    # language=python
    content2 = """
from file1 import foo1, foo2, foo3, foo4

def bar(a, b):
    foo1()
    foo2()
    foo3()
    foo4()
    foo5()
    """

    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file2 = codebase.get_file("file2.py")

        remove_list = ["foo3", "foo4"]

        for imp in file2.imports:
            if imp.name in remove_list:
                imp.remove()
    # language=python
    assert (
        file2.content
        == """
from file1 import foo1, foo2

def bar(a, b):
    foo1()
    foo2()
    foo3()
    foo4()
    foo5()
    """
    )


def test_import_multi_remove_multiline(tmpdir) -> None:
    # language=python
    content1 = """
def foo1():
    pass

def foo2():
    pass

def foo3():
    pass

def foo4():
    pass

def foo5():
    pass
"""
    # language=python
    content2 = """
from file1 import (
    foo1,
    foo2,
    foo3,
    foo4
)

def bar(a, b):
    foo1()
    foo2()
    foo3()
    foo4()
    foo5()
    """

    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file2 = codebase.get_file("file2.py")

        remove_list = ["foo1", "foo2"]

        for imp in file2.imports:
            if imp.name in remove_list:
                imp.remove()

    # language=python
    assert (
        file2.content
        == """
from file1 import (
    foo3,
    foo4
)

def bar(a, b):
    foo1()
    foo2()
    foo3()
    foo4()
    foo5()
    """
    )
