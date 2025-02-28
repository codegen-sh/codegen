import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import File
from codegen.sdk.enums import EdgeType
from tests.unit.codegen.sdk.python.utils.test_file_contents import file1_content, file2_content


@pytest.fixture(scope="function")
def mock_codebase_setup(tmpdir) -> tuple[Codebase, File, File]:
    tmpdir.mkdir("test_reparse")
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": file1_content, "file2.py": file2_content}) as mock_code_base:
        yield mock_code_base, mock_code_base.get_file("file1.py"), mock_code_base.get_file("file2.py")


def test_file_reparse_rename_global_var(mock_codebase_setup: tuple[Codebase, File, File]) -> None:
    codebase, file1, file2 = mock_codebase_setup

    ctx = codebase.ctx
    init_nodes = ctx.get_nodes()
    init_edges = ctx.get_edges()
    assert [x.name for x in file2.classes] == ["MyClass2"]
    assert [x.name for x in file2.get_class("MyClass2").methods] == ["__init__", "square_plus_constant", "cube_plus_constant", "sin_plus_constant"]

    file2.get_class("MyClass2").rename("MyClass3")
    codebase.ctx.commit_transactions()

    assert [x.name for x in file2.classes] == ["MyClass3"]
    assert [x.name for x in file2.get_class("MyClass3").methods] == ["__init__", "square_plus_constant", "cube_plus_constant", "sin_plus_constant"]
    assert len(ctx.nodes) == len(init_nodes)
    assert len(ctx.edges) == len(init_edges)


def test_file_reparse_rename_referenced_class(mock_codebase_setup: tuple[Codebase, File, File]) -> None:
    codebase, file1, file2 = mock_codebase_setup

    ctx = codebase.ctx
    init_nodes = ctx.get_nodes()
    init_edges = ctx.get_edges()
    assert [x.name for x in file1.classes] == ["MyClass1"]
    assert [x.name for x in file1.get_class("MyClass1").methods] == ["__init__", "square", "cube", "sin"]

    symbol_to_rename = file1.get_class("MyClass1")
    symbol_to_rename.rename("ReferencedClass")
    codebase.ctx.commit_transactions()

    assert [x.name for x in file1.classes] == ["ReferencedClass"]
    assert [x.name for x in file1.get_class("ReferencedClass").methods] == ["__init__", "square", "cube", "sin"]
    assert len(ctx.nodes) == len(init_nodes)
    assert len(ctx.edges) == len(init_edges)
    assert "MyClass1" not in file2.source
    assert "MyClass1" not in file2.content
    assert "MyClass1" not in file1.source
    assert "MyClass1" not in file1.content


def test_file_reparse_add_new_import(mock_codebase_setup: tuple[Codebase, File, File]) -> None:
    codebase, file1, file2 = mock_codebase_setup

    ctx = codebase.ctx
    init_nodes = ctx.get_nodes()
    init_edges = ctx.get_edges()
    init_file1_imports = file1.imports

    new_content = file1.content + "\n\n" + "from datetime import datetime"
    file1.edit(new_content)
    file1.commit()

    # Assert that file1 ts_node and graph have been properly updated
    assert len(file1.imports) == len(init_file1_imports) + 1
    assert "datetime" in [x.alias.source for x in file1.imports]
    assert "from datetime import datetime" in file1.source

    # Assert that the new import has been added an external module as well as new import
    nodes_diff = set(ctx.get_nodes()) - set(init_nodes)
    external_module = next((x for x in nodes_diff if type(x).__name__ == "ExternalModule" and x.name == "datetime"), None)
    imp = next((x for x in nodes_diff if type(x).__name__ == "PyImport" and x.name == "datetime"), None)
    assert len(nodes_diff) == 2
    assert external_module is not None
    assert imp is not None

    # Assert that new edges have been created to incorporate the new import and external module nodes
    edges_diff = set(ctx.get_edges()) - set(init_edges)
    imp_resolution_edge = next(
        ((u, v, edge_type, usage_type) for (u, v, edge_type, usage_type) in edges_diff if edge_type == EdgeType.IMPORT_SYMBOL_RESOLUTION and u == imp.node_id and v == external_module.node_id), None
    )
    assert imp_resolution_edge is not None


def test_file_reparse_move_global_var(mock_codebase_setup: tuple[Codebase, File, File]) -> None:
    codebase, file1, file2 = mock_codebase_setup

    ctx = codebase.ctx

    # Move GLOBAL_CONSTANT_1 from file1 to file2
    global_var1 = file1.get_global_var("GLOBAL_CONSTANT_1")
    global_var1.remove()
    global_var2 = file2.get_global_var("GLOBAL_CONSTANT_2")
    global_var2.insert_before(global_var1.source)
    file1.add_import(global_var1)

    # Remove the import to GLOBAL_CONSTANT_1 from file2
    imp_to_remove = file2.get_import("GLOBAL_CONSTANT_1")
    imp_to_remove.remove()

    codebase.ctx.commit_transactions()

    assert file1.get_symbol("GLOBAL_CONSTANT_1") is None
    assert file2.get_symbol("GLOBAL_CONSTANT_1") is not None
    assert file1.get_import("GLOBAL_CONSTANT_1") is not None
    assert file2.get_import("GLOBAL_CONSTANT_1") is None


def test_reparse_returns_indirectly_imported_files(tmpdir) -> None:
    # language=python
    file0 = """
from file2 import bar

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
    # file2 has an indirect import to file0
    # language=python
    file2 = """
from dir.file1 import square

def bar(x):
    return square(x)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file0.py": file0, "dir/file1.py": file1, "file2.py": file2}) as codebase:
        file0 = codebase.get_file("dir/file0.py")
        file1 = codebase.get_file("dir/file1.py")
        file2 = codebase.get_file("file2.py")

        ctx = codebase.ctx
        init_nodes = ctx.get_nodes()
        init_edges = ctx.get_edges()

        square_func = file0.get_function("square")
        square_func.rename("triangle")

    assert len(ctx.get_nodes()) == len(init_nodes)
    assert len(ctx.get_edges()) == len(init_edges)
    assert "square" not in file0.source
    assert "square" not in file0.content
    assert "triangle" in file0.source
    assert "triangle" in file0.content
    assert "square" not in file1.source
    assert "square" not in file1.content
    assert "triangle" in file1.source
    assert "triangle" in file1.content
    assert "square" not in file2.source
    assert "square" not in file2.content
    assert "triangle" in file2.source
    assert "triangle" in file2.content
