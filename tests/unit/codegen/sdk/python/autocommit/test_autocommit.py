import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.autocommit.constants import NodeNotFoundError, OutdatedNodeError
from codegen.sdk.core.statements.statement import StatementType


@pytest.mark.skip("No Autocommit")
def test_autocommit_rename_move(tmpdir) -> None:
    file1_name = "file1.py"
    # language=python
    content1 = """
def external_dep():
    return 42
"""
    file2_name = "file2.py"
    # language=python
    content2 = """
from file1 import external_dep

def bar():
    return external_dep() + 1
"""
    file3_name = "file3.py"
    content3 = ""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1, file2_name: content2, file3_name: content3}) as codebase:
        file1 = codebase.get_file(file1_name)
        file2 = codebase.get_file(file2_name)
        file3 = codebase.get_file(file3_name)
        external_dep = file1.get_function("external_dep")
        external_dep.rename("baz")
        bar = file2.get_function("bar")
        bar.rename("bar2")
        bar.move_to_file(file3, strategy="update_all_imports", include_dependencies=True)

    # language=python
    assert (
        file1.content
        == """
def baz():
    return 42
"""
    )
    # language=python
    assert (
        file2.content
        == """
from file1 import baz
"""
    )

    # language=python
    assert (
        file3.content
        == """from file1 import baz


def bar2():
    return baz() + 1"""
    )


@pytest.mark.skip("No Autocommit")
def test_autocommit_move_rename(tmpdir) -> None:
    file1_name = "file1.py"
    # language=python
    content1 = """
def external_dep():
    return 42
"""
    file2_name = "file2.py"
    # language=python
    content2 = """
from file1 import external_dep

def bar():
    return external_dep() + 1
"""
    file3_name = "file3.py"
    content3 = ""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1, file2_name: content2, file3_name: content3}) as codebase:
        file1 = codebase.get_file(file1_name)
        file2 = codebase.get_file(file2_name)
        file3 = codebase.get_file(file3_name)
        external_dep = file1.get_function("external_dep")
        external_dep.rename("baz")
        bar = file2.get_function("bar")
        bar.move_to_file(file3, strategy="update_all_imports", include_dependencies=True)
        bar.rename("bar2")

    # language=python
    assert (
        file1.content
        == """
def baz():
    return 42
"""
    )
    # language=python
    assert (
        file2.content
        == """
from file1 import baz
"""
    )

    # language=python
    assert (
        file3.content
        == """from file1 import baz


def bar2():
    return baz() + 1"""
    )


@pytest.mark.skip("No Autocommit")
def test_autocommit_insert_remove(tmpdir) -> None:
    file1_name = "file1.py"
    content1 = ""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1}) as codebase:
        file1 = codebase.get_file(file1_name)
        file1.edit("a")
        file1.edit(file1.content)

    assert file1.content == "a"


@pytest.mark.skip("No Autocommit")
@pytest.mark.skip(reason="wip")
@pytest.mark.parametrize("edit_block", [True, False])
def test_autocommit_file_edit(tmpdir, edit_block: bool) -> None:
    file1_name = "file1.py"
    # language=python
    content1 = """
def a():
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1}) as codebase:
        autocommit = codebase.ctx._autocommit
        file1 = codebase.get_file(file1_name)
        fun = file1.get_function("a")
        file1.add_import("import os")
        assert fun.node_id not in autocommit._nodes
        if edit_block:
            block = fun.code_block
            assert fun.node_id not in autocommit._nodes
            block.insert_before("a", fix_indentation=True)
            assert fun.node_id in autocommit._nodes
            block.insert_before("a", fix_indentation=True)
            assert fun.node_id in autocommit._nodes
        fun.remove()
        assert fun.node_id in autocommit._nodes

    assert file1.content.strip() == "import os"


@pytest.mark.skip("No Autocommit")
@pytest.mark.skip(reason="wip")
@pytest.mark.parametrize("edit_block", [True, False])
def test_autocommit_param_edit(tmpdir, edit_block: bool) -> None:
    file1_name = "file1.py"
    # language=python
    content1 = """
def a(a: int):
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1}) as codebase:
        autocommit = codebase.ctx._autocommit
        file1 = codebase.get_file(file1_name)
        fun = file1.get_function("a")
        param = fun.parameters[0]
        assert fun.node_id not in autocommit._nodes
        param.edit("try_to_break_this: str")
        assert fun.node_id in autocommit._nodes
        if edit_block:
            block = fun.code_block
            block.insert_before("a", fix_indentation=True)
            block.insert_before("a", fix_indentation=True)
        fun.remove()

    assert file1.content.strip() == ""


@pytest.mark.skip("No Autocommit")
@pytest.mark.skip(reason="wip")
@pytest.mark.parametrize("edit_block", [True, False])
def test_autocommit_param_edit_file(tmpdir, edit_block: bool) -> None:
    file1_name = "file1.py"
    # language=python
    content1 = """
def a(a: int):
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1}) as codebase:
        autocommit = codebase.ctx._autocommit
        file1 = codebase.get_file(file1_name)
        fun = file1.get_function("a")
        param = fun.parameters[0]
        assert fun.node_id not in autocommit._nodes
        param.edit("try_to_break_this: str")
        file1.add_import("import os")
        assert fun.node_id in autocommit._nodes
        if edit_block:
            block = fun.code_block
            block.insert_before("a", fix_indentation=True)
            block.insert_before("a", fix_indentation=True)
        fun.remove()

    assert file1.content.strip() == "import os"


@pytest.mark.skip("No Autocommit")
@pytest.mark.skip(reason="wip")
def test_autocommit_param_edit_other(tmpdir) -> None:
    file1_name = "file1.py"
    # language=python
    content1 = """
def a(a: int):
    pass
def b(a: int):
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1}) as codebase:
        autocommit = codebase.ctx._autocommit
        file1 = codebase.get_file(file1_name)
        fun = file1.get_function("a")
        funb = file1.get_function("b")
        param = fun.parameters[0]
        assert fun.node_id not in autocommit._nodes
        param.edit("try_to_break_this: str")
        file1.add_import("import os")
        assert fun.node_id in autocommit._nodes
        block = funb.code_block
        block.insert_before("a", fix_indentation=True)
        block.insert_before("a", fix_indentation=True)
        funb.remove()
        fun.remove()

    assert file1.content.strip() == "import os"


@pytest.mark.skip("No Autocommit")
@pytest.mark.skip("Log propagate is off")
def test_autocommit_remove_edit(tmpdir, caplog) -> None:
    file1_name = "file1.py"
    # language=python
    content1 = """
def a():
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1}) as codebase:
        file1 = codebase.get_file(file1_name)
        fun = file1.get_function("a")
        fun.remove()
        fun.prepend_statements("a")
        assert "Editing a removed node" in caplog.text


@pytest.mark.skip("No Autocommit")
@pytest.mark.skip(reason="wip")
def test_autocommit_not_found(tmpdir) -> None:
    file1_name = "file1.py"
    # language=python
    content1 = """
def a():
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1}) as codebase:
        file1 = codebase.get_file(file1_name)
        fun = file1.get_function("a")
        fun.edit("")

        with pytest.raises(NodeNotFoundError):
            fun.prepend_statements("a")


@pytest.mark.skip("No Autocommit")
def test_autocommit_outdated(tmpdir) -> None:
    file1_name = "file1.py"
    # language=python
    content1 = """
    def external_dep():
        return 42
    """
    file2_name = "file2.py"
    # language=python
    content2 = """
    from file1 import external_dep

    def bar():
        a = 1
        return external_dep() + 1
    """
    file3_name = "file3.py"
    content3 = ""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1, file2_name: content2, file3_name: content3}) as codebase:
        file1 = codebase.get_file(file1_name)
        file2 = codebase.get_file(file2_name)
        file3 = codebase.get_file(file3_name)
        external_dep = file1.get_function("external_dep")
        external_dep.rename("baz")
        bar = file2.get_function("bar")
        statement = bar.code_block.statements[0]
        bar.move_to_file(file3, strategy="update_all_imports", include_dependencies=True)
        bar.rename("bar2")
        with pytest.raises(OutdatedNodeError):
            statement.remove()


@pytest.mark.skip("No Autocommit")
@pytest.mark.skip("Log propagate is off")
def test_autocommit_nocommit_edit(tmpdir, caplog) -> None:
    """Test ability to handle transaction errors and switch to autocommit."""
    file1_name = "file1.py"
    # language=python
    content1 = """
def a():
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1}, commit=True) as codebase:
        file1 = codebase.get_file(file1_name)
        fun = file1.get_function("a")
        assert "Running autocommit" not in caplog.text
        assert "Committing" not in caplog.text
        # Please don't do this
        fun.insert_after("a")
        fun.insert_after("a")
        fun.insert_after("a")
        assert "Running autocommit" not in caplog.text
        assert "Committing" not in caplog.text
    assert "Committing" in caplog.text


@pytest.mark.skip("No Autocommit")
def test_autocommit_repr(tmpdir) -> None:
    file1_name = "file1.py"
    # language=python
    content1 = """
def a():
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1}) as codebase:
        file1 = codebase.get_file(file1_name)
        fun = file1.get_function("a")
        repr(fun)


@pytest.mark.skip("No Autocommit")
def test_autocommit_double_edit(tmpdir) -> None:
    file1_name = "file1.py"
    # language=python
    content1 = """
def a():
    def b():
        return a
"""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1}) as codebase:
        for function in codebase.functions:
            for statement in function.code_block.statements:
                if statement.statement_type == StatementType.RETURN_STATEMENT:
                    statement.edit(function.name)
            function.commit()


@pytest.mark.skip("No Autocommit")
@pytest.mark.skip("Log propagate is off")
def test_autocommit_ignore_removed(tmpdir, caplog) -> None:
    """Test ability for removes to not mess up ordering."""
    file1_name = "file1.py"
    # language=python
    content1 = """
def a():
    b = 1
    c = 2
    d = 3
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1}, commit=True) as codebase:
        file1 = codebase.get_file(file1_name)
        fun = file1.get_function("a")
        b = fun.code_block.statements[0]
        c = fun.code_block.statements[1]
        d = fun.code_block.statements[2]
        c.remove()
        assert d.name == "d"
        assert b.name == "b"
