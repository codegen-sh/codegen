from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_function_remove(tmpdir) -> None:
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
        file.get_function("foo").remove()

    # language=python
    assert (
        file.content
        == """
import os
import numpy

global_var = 1

def bar():
    return 2
        """
    )

    codebase.reset()
    file.get_function("bar").remove()
    codebase.ctx.commit_transactions()
    # language=python
    assert (
        file.content
        == """
import os
import numpy

global_var = 1

def foo():
    return 1
        """
    )


def test_function_remove_multiple(tmpdir) -> None:
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
        file.get_function("foo").remove()
        file.get_function("bar").remove()

    # language=python
    assert (
        file.content
        == """
import os
import numpy

global_var = 1
        """
    )
