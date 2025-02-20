"""Tests covering the core abstractions of GraphSitter. Should run very fast since it only parses strings"""

import itertools

from codegen.sdk.codebase.codebase_context import CodebaseContext
from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.enums import EdgeType


def test_codebase_with_wrapper(tmpdir) -> None:
    # language=python
    content = """
from some_file import x, y, z
import numpy as np

global_var_1 = 1
global_var_2 = 2

def foo():
    return bar()

def bar():
    return 42

class MyClass:
    def __init__(self):
        pass

class MySubClass(MyClass):
    def __init__(self):
        super().__init__()
        pass
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        assert codebase is not None
        assert isinstance(codebase.ctx, CodebaseContext)
        # assert set(codebase.ctx.nodes) == {
        #     "<PyAssignment>test.py::global_var_1:51-67",
        #     "<PyAssignment>test.py::global_var_2:68-84",
        #     "<PyClass>test.py::MyClass:141-192",
        #     "<PyClass>test.py::MySubClass:194-284",
        #     "<PyFunction>test.py::bar:115-139",
        #     "<PyFunction>test.py::__init__:160-192",
        #     "<PyFunction>test.py::__init__:225-284",
        #     "<PyFunction>test.py::foo:86-113",
        #     "external_module__6f11581db2",
        #     "external_module__6f250a0cd3",
        #     "import__np__from__numpy__to__test.py",
        #     "import__x__from__some_file__to__test.py",
        #     "import__y__from__some_file__to__test.py",
        #     "import__z__from__some_file__to__test.py",
        #     "test.py",
        # }
        import_resolution_edges = [edge for edge in codebase.ctx.edges if edge[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION]
        file_contains_node_edges = list(itertools.chain.from_iterable(file.get_nodes() for file in codebase.files))
        symbol_usage_edges = [edge for edge in codebase.ctx.edges if edge[2].type == EdgeType.SYMBOL_USAGE]

        assert len(import_resolution_edges) == 4
        assert len(file_contains_node_edges) == 14
        assert len(symbol_usage_edges) == 6


def test_codebase_broken_file(tmpdir) -> None:
    # language=python
    content = """
from some_file import x, y, z
import numpy as np

global_var_1 = 1
global_var_2 = 2

def foo():
    return bar()

def bar():
    return 42

class MyClass:
    def __init__(self):
        pass

class MySubClass(MyClass):
    def __init__(self):
        super().__init__()
        pass
    """
    content_broken = bytes("你好", "big5hkscs")
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content, "test2.py": content_broken}) as codebase:
        assert codebase is not None
        assert isinstance(codebase.ctx, CodebaseContext)
        import_resolution_edges = [edge for edge in codebase.ctx.edges if edge[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION]
        file_contains_node_edges = list(itertools.chain.from_iterable(file.get_nodes() for file in codebase.files))
        symbol_usage_edges = [edge for edge in codebase.ctx.edges if edge[2].type == EdgeType.SYMBOL_USAGE]

        assert len(import_resolution_edges) == 4
        assert len(file_contains_node_edges) == 14
        assert len(symbol_usage_edges) == 6
