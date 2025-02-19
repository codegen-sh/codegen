import pytest

from codegen.sdk.core.codebase import Codebase


@pytest.mark.parametrize(
    "original, expected",
    [
        ({"a.py": "a", "b.py": "b"}, {"a.py": "b", "b.py": "b"}),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset(codebase: Codebase, assert_expected, tmp_path):
    # External change should be preserved
    (tmp_path / "a.py").write_text("b")
    # Programmatic change should be reset
    codebase.get_file("b.py").edit("changed")
    codebase.commit()
    codebase.reset()
    assert_expected(codebase)


@pytest.mark.parametrize(
    "original, expected",
    [
        ({"a.py": "a"}, {"a.py": "b"}),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset_external_changes(codebase: Codebase, assert_expected):
    # External change should be preserved
    codebase.get_file("a.py").path.write_text("b")
    codebase.commit()
    codebase.reset()
    assert_expected(codebase)


@pytest.mark.parametrize(
    "original, expected",
    [
        ({"a.py": "a"}, {"a.py": "a", "new.py": "new content"}),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset_manual_file_add(codebase: Codebase, assert_expected, tmp_path):
    # Manually create a new file - should be preserved
    new_file = tmp_path / "new.py"
    new_file.write_text("new content")
    # Make programmatic change that should be reset
    codebase.get_file("a.py").edit("changed")
    codebase.commit()
    codebase.reset()
    assert_expected(codebase)


@pytest.mark.parametrize(
    "original, expected",
    [
        ({"a.py": "a", "b.py": "b"}, {"a.py": "a"}),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset_manual_file_delete(codebase: Codebase, assert_expected):
    # Manual deletion should be preserved
    codebase.get_file("b.py").path.unlink()
    # Programmatic change should be reset
    codebase.get_file("a.py").edit("changed")
    codebase.commit()
    codebase.reset()
    assert_expected(codebase)


@pytest.mark.parametrize(
    "original, expected",
    [
        ({"old.py": "content"}, {"new.py": "content"}),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset_manual_file_rename(codebase: Codebase, tmp_path, assert_expected):
    # Manual rename should be preserved
    old_path = codebase.get_file("old.py").path
    new_path = tmp_path / "new.py"
    old_path.rename(new_path)
    codebase.reset()
    assert_expected(codebase)


@pytest.mark.parametrize(
    "original, expected",
    [
        (
            {
                "src/main.py": "def main():\n    print('hello')",
                "src/utils/helpers.py": "def helper():\n    return True",
                "tests/test_main.py": "def test_main():\n    assert True",
            },
            {
                "src/main.py": "def main():\n    print('modified')",
                "src/utils/helpers.py": "def helper():\n    return True",
                "tests/test_main.py": "def test_main():\n    assert False",
            },
        ),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset_nested_directories(codebase: Codebase, assert_expected, tmp_path):
    """Test reset with nested directory structure."""
    # External changes should be preserved
    (tmp_path / "src/main.py").write_text("def main():\n    print('modified')")
    (tmp_path / "tests/test_main.py").write_text("def test_main():\n    assert False")
    # Programmatic changes should be reset
    codebase.get_file("src/utils/helpers.py").edit("def helper():\n    return False")
    codebase.reset()
    assert_expected(codebase)


@pytest.mark.parametrize(
    "original, expected",
    [
        (
            {
                "app.py": "import json\n\ndata = {\n    'name': 'test',\n    'value': 123\n}",
                "config.json": '{\n    "debug": true,\n    "port": 8080\n}',
                "README.md": "# Project\nThis is a test project.",
            },
            {
                "app.py": "import json\n\ndata = {\n    'name': 'test',\n    'value': 123\n}",
                "config.json": '{\n    "debug": false,\n    "env": "prod"\n}',
                "README.md": "# Modified Project\nUpdated documentation.",
            },
        ),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset_mixed_content(codebase: Codebase, assert_expected, tmp_path):
    """Test reset with different types of file content."""
    # External changes should be preserved
    (tmp_path / "config.json").write_text('{\n    "debug": false,\n    "env": "prod"\n}')
    (tmp_path / "README.md").write_text("# Modified Project\nUpdated documentation.")
    # Programmatic changes should be reset
    codebase.get_file("app.py").edit("import json\n\ndata = {'name': 'modified'}")
    codebase.commit()
    codebase.reset()
    assert_expected(codebase)


@pytest.mark.parametrize(
    "original, expected",
    [
        (
            {
                "module.py": """class ComplexClass:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1
        return self.value

    def decrement(self):
        self.value -= 1
        return self.value

    def reset(self):
        self.value = 0
        return self.value""",
            },
            {
                "module.py": """class ComplexClass:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1
        return self.value

    def decrement(self):
        self.value -= 1
        return self.value

    def reset(self):
        self.value = 0
        return self.value""",
            },
        ),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset_large_file(codebase: Codebase, assert_expected):
    """Test reset with a larger file containing multiple methods."""
    codebase.get_file("module.py").edit("""class ModifiedClass:
    def __init__(self):
        self.value = 100""")
    codebase.commit()
    codebase.reset()
    assert_expected(codebase)


@pytest.mark.parametrize(
    "original, expected",
    [
        ({"src/a.py": "# original content"}, {"src/a.py": "# modified content", "src/b.py": "# new file content"}),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset_preserves_external_changes(codebase: Codebase, assert_expected, tmp_path):
    # Make external changes to existing file
    src_dir = tmp_path / "src"
    src_dir.mkdir(exist_ok=True)
    (src_dir / "a.py").write_text("# modified content")

    # Add new file externally
    (src_dir / "b.py").write_text("# new file content")

    # Reset should detect and preserve these changes
    codebase.commit()
    codebase.reset()
    assert_expected(codebase)


@pytest.mark.parametrize(
    "original, expected",
    [
        (
            {"src/main.py": "def main():\n    pass", "src/utils.py": "def helper():\n    pass"},
            {"src/main.py": "def main():\n    return 42", "src/utils.py": "def helper():\n    pass", "src/new_module.py": "# New module"},
        ),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset_mixed_changes(codebase: Codebase, assert_expected, tmp_path):
    # Make programmatic change that should be reset
    codebase.get_file("src/utils.py").edit("def helper():\n    return None")

    # Make external changes that should be preserved
    src_dir = tmp_path / "src"
    (src_dir / "main.py").write_text("def main():\n    return 42")
    (src_dir / "new_module.py").write_text("# New module")

    codebase.commit()
    codebase.reset()
    assert_expected(codebase)


@pytest.mark.parametrize(
    "original, expected",
    [
        ({"config/settings.py": "DEBUG = False"}, {"config/settings.py": "DEBUG = True", "config/local.py": "# Local overrides"}),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset_nested_external_changes(codebase: Codebase, assert_expected, tmp_path):
    # Create nested directory structure with changes
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)

    # Modify existing file
    (config_dir / "settings.py").write_text("DEBUG = True")

    # Add new file in nested directory
    (config_dir / "local.py").write_text("# Local overrides")

    codebase.commit()
    codebase.reset()
    assert_expected(codebase)


@pytest.mark.xfail(reason="Needs CG-10484")
@pytest.mark.parametrize(
    "original, expected",
    [
        (
            {"file.py": "initial content"},
            {"file.py": "final external content"},
        ),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset_multiple_programmatic_edits(codebase: Codebase, assert_expected):
    """Test reset after multiple programmatic edits to the same file."""
    # Make multiple programmatic changes that should all be reset
    codebase.get_file("file.py").edit("first edit")
    codebase.get_file("file.py").edit("second edit")
    codebase.get_file("file.py").edit("third edit")

    # Make external change that should be preserved
    codebase.get_file("file.py").path.write_text("final external content")
    codebase.commit()
    codebase.reset()
    assert_expected(codebase)


@pytest.mark.xfail(reason="Needs CG-10484")
@pytest.mark.parametrize(
    "original, expected",
    [
        (
            {"file.py": "def main():\n    return 0"},
            {"file.py": "def main():\n    return 42"},
        ),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset_interleaved_changes(codebase: Codebase, assert_expected):
    """Test reset with interleaved programmatic and external changes."""
    # Interleave programmatic and external changes
    codebase.get_file("file.py").edit("def main():\n    return 1")
    codebase.get_file("file.py").path.write_text("def main():\n    return 42")
    codebase.get_file("file.py").edit("def main():\n    return 2")
    codebase.commit()
    codebase.reset()
    assert_expected(codebase)


@pytest.mark.parametrize(
    "original, expected",
    [
        (
            {
                "file.py": """
class Test:
    def method1(self):
        pass
"""
            },
            {
                "file.py": """
class Test:
    def method1(self):
        pass
"""
            },
        ),
    ],
    indirect=["original", "expected"],
)
def test_codebase_reset_complex_changes(codebase: Codebase, assert_expected):
    """Test reset with a mix of content additions, modifications, and external changes."""
    # Make several programmatic changes
    for i in range(5):
        codebase.get_file("file.py").insert_after(f"# comment {i}")
        codebase.commit()

    codebase.reset()
    assert_expected(codebase)
