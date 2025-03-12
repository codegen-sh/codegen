import os

from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_file_remove_after_create(tmpdir) -> None:
    # language=python
    content = """
def foo(bar):
    return bar
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        filepath = file.filepath
        new_filepath = "new_file.py"
        new_file = file.create_from_filepath(new_filepath, codebase.ctx)

    ctx = codebase.ctx
    assert ctx.get_node(file.node_id) == file
    assert ctx.get_node(new_file.node_id) == new_file
    assert ctx.has_node(file.node_id)
    assert ctx.has_node(new_file.node_id)
    assert os.path.exists(tmpdir / file.filepath)
    assert os.path.exists(tmpdir / new_file.filepath)

    # Delete the original
    file.remove()
    codebase.ctx.commit_transactions()
    assert not os.path.exists(tmpdir / filepath)
    assert os.path.exists(tmpdir / new_filepath)
