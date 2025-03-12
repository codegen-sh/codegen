from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_import_remove_no_usage(tmpdir) -> None:
    # language=python
    content = """
import a  # test one
from b.c import d  # test two
from d.f import (g as h, i as j)  # test three
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # =====[ Remove a ]=====
        imp = file.get_import("a")
        imp.remove()

    assert "import a  # test one" not in file.content
    assert imp not in file.imports

    # =====[ Remove b.c ]=====
    imp = file.get_import("d")
    imp.remove()
    codebase.ctx.commit_transactions()
    assert "from b.c import d  # test two" not in file.content
    assert imp not in file.imports

    # =====[ Remove d.f ]=====
    imp = file.get_import("h")
    imp.remove()
    codebase.ctx.commit_transactions()
    assert "from d.f import (g as h, i as j)  # test three" not in file.content
    assert "from d.f import (i as j)  # test three" in file.content
    assert imp not in file.imports

    imp = file.get_import("j")
    imp.remove()
    codebase.ctx.commit_transactions()
    assert "from d.f" not in file.content


def test_import_remove_external_module_no_usage(tmpdir) -> None:
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

        file.imports[1].remove()

    # language=python
    assert (
        file.content
        == """
import os

global_var = 1

def foo():
    return 1

def bar():
    return 2
        """
    )
    codebase.reset()

    file.imports[0].remove()
    codebase.ctx.commit_transactions()
    # language=python
    assert (
        file.content
        == """
import numpy

global_var = 1

def foo():
    return 1

def bar():
    return 2
        """
    )
    codebase.reset()


def test_import_remove_multiple_single_imports(tmpdir) -> None:
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

        file.imports[1].remove()
        file.imports[0].remove()

    # language=python
    assert (
        file.content.strip()
        == """
global_var = 1

def foo():
    return 1

def bar():
    return 2
        """.strip()
    )


def test_multi_import_multiple_remove_without_alias(tmpdir) -> None:
    # language=python
    content = """
import a  # test one
from b.c import d  # test two
from d.f import (g, h, i)  # test three
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        file.get_import("g").remove()
        file.get_import("h").remove()
        file.get_import("i").remove()

    assert "from d.f" not in file.content


def test_multi_import_multiple_remove_with_alias(tmpdir) -> None:
    # language=python
    content = """
import a  # test one
from b.c import d  # test two
from d.f import (g as h, i as j, x as y)  # test three
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        file.get_import("h").remove()
        file.get_import("y").remove()
        file.get_import("j").remove()

    assert "from d.f" not in file.content

    codebase.reset()
    file.get_import("h").remove()
    file.get_import("j").remove()
    file.get_import("y").remove()
    codebase.ctx.commit_transactions()
    assert "from d.f" not in file.content

    codebase.reset()
    file.get_import("y").remove()
    file.get_import("j").remove()
    file.get_import("h").remove()
    codebase.ctx.commit_transactions()
    assert "from d.f" not in file.content

    codebase.reset()
    file.get_import("y").remove()
    file.get_import("h").remove()
    file.get_import("j").remove()
    codebase.ctx.commit_transactions()
    assert "from d.f" not in file.content

    codebase.reset()
    file.get_import("j").remove()
    file.get_import("y").remove()
    file.get_import("h").remove()
    codebase.ctx.commit_transactions()
    assert "from d.f" not in file.content

    codebase.reset()
    file.get_import("j").remove()
    file.get_import("h").remove()
    file.get_import("y").remove()
    codebase.ctx.commit_transactions()
    assert "from d.f" not in file.content


def test_multi_import_remove_import_from_multi_import(tmpdir) -> None:
    # language=python
    content = """
    from file1 import a, b, c
    from file2 import (x, y, z)
    """

    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")

        file.get_import("a").remove()

    # language=python
    assert (
        file.content
        == """
    from file1 import b, c
    from file2 import (x, y, z)
    """
    )

    file.get_import("c").remove()
    codebase.ctx.commit_transactions()
    # language=python
    assert (
        file.content
        == """
    from file1 import b
    from file2 import (x, y, z)
    """
    )

    file.get_import("b").remove()
    codebase.ctx.commit_transactions()
    # language=python
    assert (
        file.content
        == """
    from file2 import (x, y, z)
    """
    )

    file.get_import("x").remove()
    codebase.ctx.commit_transactions()
    # language=python
    assert (
        file.content
        == """
    from file2 import (y, z)
    """
    )

    file.get_import("z").remove()
    codebase.ctx.commit_transactions()
    # language=python
    assert (
        file.content
        == """
    from file2 import (y)
    """
    )

    file.get_import("y").remove()
    codebase.ctx.commit_transactions()
    assert file.content.strip() == ""


def test_import_remove_multiple_multi_import(tmpdir) -> None:
    # language=python
    content = """
from file1 import a, b, c
from file2 import (x, y, z)
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")

        file.get_import("a").remove()
        file.get_import("c").remove()
        file.get_import("b").remove()
        file.get_import("x").remove()
        file.get_import("z").remove()
        file.get_import("y").remove()

    assert file.content.strip() == ""


def test_import_remove_multiple_single_repeated(tmpdir) -> None:
    # language=python
    content = """
from file1 import a, b, c
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")
        for _ in file.imports:
            file.get_import("a").remove()

    assert file.content.strip() == "from file1 import b, c"
