from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_directory_file_move_simple(tmpdir) -> None:
    # language=python
    content1 = """
def a():
    pass
    """
    # language=python
    content2 = """
def b():
    pass
    """
    # language=python
    content3 = """
def c():
    pass
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content1, "dir/file2.py": content2, "dir/subdir/file3.py": content3}) as codebase:
        assert codebase.get_file("dir/file1.py") is not None
        assert codebase.get_file("dir/file2.py") is not None
        assert codebase.get_file("dir/subdir/file3.py") is not None
        assert codebase.get_directory("dir") is not None
        assert codebase.get_directory("dir/subdir") is not None
        assert {f.filepath for f in codebase.get_directory("dir").files(recursive=True)} == {"dir/file1.py", "dir/file2.py", "dir/subdir/file3.py"}
        assert {d.dirpath for d in codebase.directories} == {"", "dir", "dir/subdir"}
        codebase.get_directory("dir").remove()
        codebase.commit()
        assert codebase.get_directory("dir", optional=True) is None
        assert codebase.get_directory("dir/subdir", optional=True) is None
        assert {f.filepath for f in codebase.files} == set()
        assert {d.dirpath for d in codebase.directories} == set()


def test_directory_root_file(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": ""}) as codebase:
        assert codebase.get_file("file1.py") is not None
        assert codebase.get_directory("") is not None
        codebase.get_file("file1.py").remove()
        codebase.commit()
        assert {f.filepath for f in codebase.files} == set()
        assert {d.dirpath for d in codebase.directories} == set()
