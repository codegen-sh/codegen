import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.codebase.validation import get_edges
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_codebase_reset_exception(tmpdir, caplog) -> None:
    # language=python
    file0_content = """
from file2 import bar

def square(x):
    return x * x
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file0.py": file0_content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file0 = codebase.get_file("dir/file0.py")
        file0.write("aui")
        codebase.reset()
        assert "Directly called file write without calling commit_transactions" in caplog.text


def test_codebase_reset_basic(tmpdir) -> None:
    # language=python
    file0_content = """
a = 1

def square(x: a):
    return x * x
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file0.py": file0_content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file0 = codebase.get_file("dir/file0.py")
        codebase.symbols[-1].rename("test")
        codebase.commit(sync_graph=True)
        codebase.reset()


def test_reset_exception(tmpdir) -> None:
    # language=python
    file0_content = """
    from file2 import bar

    def square(x):
        return x * x
        """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file0.py": file0_content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:

        class mockme:
            change_type: str = "ab"
            path: str = "mypath"

        mm = mockme()
        codebase.ctx.all_syncs = [mm]
        try:
            codebase.reset()
        except Exception as e:
            pytest.fail(f'Exception raised: "{e}" when nothing should have happened')


def test_codebase_reset(tmpdir) -> None:
    # language=python
    file0_content = """
from file2 import bar

def square(x):
    return x * x
    """.strip()
    # language=python
    file1_content = """
from dir.file0 import square

class MyClass:
    def foo(self, arg1, arg2):
        return arg1 + square(arg2)
    """.strip()
    # language=python
    file2_content = """
from dir.file1 import square

def bar(x):
    return square(x)
    """.strip()
    with get_codebase_session(
        tmpdir=tmpdir, files={"dir/file0.py": file0_content, "dir/file1.py": file1_content, "dir/file2.py": file2_content}, programming_language=ProgrammingLanguage.PYTHON, commit=True
    ) as codebase:
        file0 = codebase.get_file("dir/file0.py", optional=True)
        file2 = codebase.get_file("dir/file2.py", optional=True)

        init_nodes = codebase.ctx.get_nodes()
        init_edges = codebase.ctx.get_edges()

        file0.update_filepath("dir/file0_updated.py")
        codebase.create_file("dir/new_file.py", "some_var = 1")
        file2.remove()

    assert codebase.get_file("dir/new_file.py", optional=True) is not None
    assert codebase.get_file("dir/file0_updated.py", optional=True) is not None
    assert codebase.get_file("dir/file0.py", optional=True) is None

    codebase.reset()
    assert codebase.get_file("dir/new_file.py", optional=True) is None
    assert codebase.get_file("dir/file0_updated.py", optional=True) is None

    file0 = codebase.get_file("dir/file0.py", optional=True)
    file1 = codebase.get_file("dir/file1.py", optional=True)
    file2 = codebase.get_file("dir/file2.py", optional=True)
    assert file0.content == file0_content
    assert file1.content == file1_content
    assert file2.content == file2_content
    assert file0.source == file0_content[file0.ts_node.start_byte :]
    assert file1.source == file1_content[file0.ts_node.start_byte :]
    assert file2.source == file2_content[file0.ts_node.start_byte :]

    assert len(codebase.ctx.get_nodes()) == len(init_nodes)
    assert set(codebase.ctx.get_nodes()) == set(init_nodes)
    assert set(codebase.ctx.get_nodes()) == set(codebase.ctx.old_graph.nodes())
    assert len(codebase.ctx.get_edges()) == len(init_edges)
    assert set(get_edges(codebase.ctx._graph)) == set(get_edges(codebase.ctx.old_graph))


def test_codebase_reset_gitignore(tmpdir: str) -> None:
    gitignore_content = """
dir/file0.py
    """
    # language=python
    file0_content = """
a = 1

def square(x: a):
    return x * x
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file0.py": file0_content, ".gitignore": gitignore_content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        assert len(codebase.files) == 0
        codebase.reset()
        codebase.checkout(branch="test-branch", create_if_missing=True)
        codebase.commit(sync_graph=True)
        codebase.reset()
