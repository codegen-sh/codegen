import pytest

from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_from_string_python():
    """Test creating a Python codebase from string"""
    code = """
def hello():
    return "world"
    """
    codebase = Codebase.from_string(code, language="python")
    assert len(codebase.files) == 1
    assert codebase.files[0].filepath.endswith("test.py")
    assert "def hello" in codebase.files[0].source


def test_from_string_typescript():
    """Test creating a TypeScript codebase from string"""
    code = """
function hello(): string {
    return "world";
}
    """
    codebase = Codebase.from_string(code, language="typescript")
    assert len(codebase.files) == 1
    assert codebase.files[0].filepath.endswith("test.ts")
    assert "function hello" in codebase.files[0].source


def test_from_string_with_enum():
    """Test creating a codebase using ProgrammingLanguage enum"""
    code = "const x = 42;"
    codebase = Codebase.from_string(code, language=ProgrammingLanguage.TYPESCRIPT)
    assert len(codebase.files) == 1
    assert codebase.files[0].filepath.endswith("test.ts")


def test_from_string_invalid_syntax():
    """Test that invalid syntax is still accepted (parsing happens later)"""
    code = "this is not valid python"
    codebase = Codebase.from_string(code, language="python")
    assert len(codebase.files) == 1
    assert codebase.files[0].source == code


def test_from_string_empty():
    """Test creating a codebase from empty string"""
    codebase = Codebase.from_string("", language="python")
    assert len(codebase.files) == 1
    assert codebase.files[0].source == ""


def test_from_string_missing_language():
    """Test that language is required"""
    with pytest.raises(TypeError, match="missing.*required.*argument.*language"):
        Codebase.from_string("print('hello')")


def test_from_string_invalid_language():
    """Test that invalid language raises error"""
    with pytest.raises(ValueError):
        Codebase.from_string("print('hello')", language="invalid")


def test_from_string_multifile():
    """Test that multifile is not supported yet"""
    code = """
# file1.py
def hello(): pass

# file2.py
def world(): pass
    """
    # Still works, just puts everything in one file
    codebase = Codebase.from_string(code, language="python")
    assert len(codebase.files) == 1
