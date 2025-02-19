from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_directory_creation(tmpdir) -> None:
    # language=python
    content1 = """
def a():
    pass
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir_a/dir_b/dir_c/file1.py": content1}) as codebase:
        assert codebase.get_directory("", optional=True) is not None
        assert codebase.get_directory("dir_a", optional=True) is not None
        assert codebase.get_directory("dir_a/dir_b", optional=True) is not None
        assert codebase.get_directory("dir_a/dir_b/dir_c", optional=True) is not None
        assert codebase.get_directory("dir_something_else", optional=True) is None
        assert codebase.get_directory("dir_a/dir_b/dir_c/file1.py", optional=True) is None
        assert {d.dirpath for d in codebase.directories} == {"", "dir_a", "dir_a/dir_b", "dir_a/dir_b/dir_c"}


def test_directory_simple(tmpdir) -> None:
    # language=python
    content1 = """
def a():
    pass

class A:
    pass
    """
    # language=python
    content2 = """
def b():
    pass

class B:
    pass
    """
    # language=python
    content3 = """
def c():
    pass

class C:
    pass
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content1, "dir/file2.py": content2, "dir/file3.py": content3}) as codebase:
        directory = codebase.get_directory("dir")
        assert directory.name == "dir"
        assert directory.parent == codebase.get_directory("")
        assert len(directory.files) == 3
        assert len(directory.subdirectories) == 0
        assert {f.filepath for f in directory.files} == {"dir/file1.py", "dir/file2.py", "dir/file3.py"}
        assert directory.symbols == codebase.symbols
        assert directory.global_vars == codebase.global_vars
        assert directory.classes == codebase.classes
        assert directory.functions == codebase.functions
        assert {d.dirpath for d in codebase.directories} == {"", "dir"}
        assert directory.get_file("file1.py") is not None
        assert directory.get_file("file2.py") is not None
        assert directory.get_file("file3.py") is not None
        # Test ignore_case
        assert directory.get_file("FILE1.PY", ignore_case=True) is not None
        assert directory.get_file("file1.py", ignore_case=True) is not None
        assert directory.get_file("FiLe1.Py", ignore_case=True) is not None
        assert directory.get_file("FILE2.PY", ignore_case=True) is not None
        assert directory.get_file("file2.py", ignore_case=True) is not None
        assert directory.get_file("FiLe2.Py", ignore_case=True) is not None
        assert directory.get_file("FILE3.PY", ignore_case=True) is not None
        assert directory.get_file("file3.py", ignore_case=True) is not None
        assert directory.get_file("FiLe3.Py", ignore_case=True) is not None

        # Test ignore_case=False (default)
        assert directory.get_file("FILE1.PY", ignore_case=False) is None
        assert directory.get_file("FiLe1.Py", ignore_case=False) is None
        assert directory.get_file("FILE2.PY", ignore_case=False) is None
        assert directory.get_file("FiLe2.Py", ignore_case=False) is None
        assert directory.get_file("FILE3.PY", ignore_case=False) is None
        assert directory.get_file("FiLe3.Py", ignore_case=False) is None


def test_directory_subdirectory(tmpdir) -> None:
    # language=python
    content1 = """
def a():
    pass

class A:
    pass
    """
    # language=python
    content2 = """
def b():
    pass

class B:
    pass
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content1, "dir/subdir/file2.py": content2}) as codebase:
        directory = codebase.get_directory("dir")
        assert directory.name == "dir"
        assert directory.parent == codebase.get_directory("")
        assert len(directory.files) == 2
        assert len(directory.subdirectories) == 1
        assert {f.filepath for f in directory.files} == {"dir/file1.py", "dir/subdir/file2.py"}
        assert directory.symbols == codebase.symbols
        assert directory.global_vars == codebase.global_vars
        assert directory.classes == codebase.classes
        assert directory.functions == codebase.functions
        subdir = codebase.get_directory("dir/subdir")
        assert subdir.name == "subdir"
        assert subdir.parent == directory
        assert {d.dirpath for d in codebase.directories} == {"", "dir", "dir/subdir"}
        assert subdir.get_file("file2.py") is not None
        assert subdir.get_file("file1.py") is None
        assert directory.get_file("file1.py") is not None
        assert directory.get_file("file2.py") is None
        assert directory.get_subdirectory("subdir") is not None


def test_multiple_directories(tmpdir) -> None:
    # language=python
    content1 = """
def a():
    pass

class A:
    pass
    """
    # language=python
    content2 = """
def b():
    pass

class B:
    pass
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir1/file1.py": content1, "dir2/file2.py": content2}) as codebase:
        directory1 = codebase.get_directory("dir1")
        file1 = codebase.get_file("dir1/file1.py")
        assert directory1.name == "dir1"
        assert directory1.parent == codebase.get_directory("")
        assert len(directory1.files) == 1
        assert len(directory1.subdirectories) == 0
        assert {f.filepath for f in directory1.files} == {"dir1/file1.py"}
        assert directory1.symbols == file1.symbols
        assert directory1.global_vars == file1.global_vars
        assert directory1.classes == file1.classes
        assert directory1.functions == file1.functions
        assert {d.dirpath for d in codebase.directories} == {"", "dir1", "dir2"}


def test_subdirectories_listing_odd_filetypes(tmpdir) -> None:
    # language=python
    files = {"docs/sub/test_fil``e1.mdx": "", "docs/sub/file2.txt": "", "docs/test.py": "", "docs/py/test.py": "", "docs/json/test.json": "", "docs/rand/odd/1.py": "", "docs/rand/even/2.txt": ""}
    expected_tree = {"docs/rand": ["odd", "even"], "docs/rand/odd": ["1.py"], "docs/rand/even": [], "docs/py": ["test.py"], "docs/json": [], "docs/sub": []}
    with get_codebase_session(tmpdir=tmpdir, files=files) as codebase:
        docs = codebase.get_directory("docs")
        subdirectories = docs.subdirectories
        for subdir in subdirectories:
            assert subdir.dirpath in expected_tree.keys()
            assert list(subdir.items.keys()) == expected_tree[subdir.dirpath]
