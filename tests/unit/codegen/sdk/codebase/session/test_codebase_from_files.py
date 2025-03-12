import pytest

from codegen.sdk.core.codebase import Codebase


def test_from_files_python():
    """Test creating a Python codebase from multiple files"""
    files = {"main.py": "from utils import add\nprint(add(1, 2))", "utils.py": "def add(a, b):\n    return a + b"}
    # Language is optional, will be inferred
    codebase = Codebase.from_files(files)
    assert len(codebase.files) == 2
    assert any(f.filepath.endswith("main.py") for f in codebase.files)
    assert any(f.filepath.endswith("utils.py") for f in codebase.files)
    assert any("from utils import add" in f.source for f in codebase.files)


def test_from_files_typescript():
    """Test creating a TypeScript codebase from multiple files"""
    files = {"index.ts": "import { add } from './utils';\nconsole.log(add(1, 2));", "utils.ts": "export function add(a: number, b: number): number {\n    return a + b;\n}"}
    # Language is optional, will be inferred
    codebase = Codebase.from_files(files)
    assert len(codebase.files) == 2
    assert any(f.filepath.endswith("index.ts") for f in codebase.files)
    assert any(f.filepath.endswith("utils.ts") for f in codebase.files)
    assert any("import { add }" in f.source for f in codebase.files)


def test_from_files_empty():
    """Test creating a codebase with no files raises ValueError"""
    with pytest.raises(ValueError, match="No files provided"):
        Codebase.from_files({})


def test_from_files_mixed_extensions():
    """Test files with mixed extensions raises error"""
    files = {"main.py": "print('hello')", "test.ts": "console.log('world')"}
    with pytest.raises(ValueError, match="Cannot determine single language from extensions"):
        Codebase.from_files(files)


def test_from_files_typescript_multiple_extensions():
    """Test TypeScript codebase with various valid extensions"""
    files = {
        "index.ts": "console.log('hi')",
        "component.tsx": "export const App = () => <div>Hello</div>",
        "utils.js": "module.exports = { add: (a, b) => a + b }",
        "button.jsx": "export const Button = () => <button>Click</button>",
    }
    # Language is optional, will be inferred as TypeScript
    codebase = Codebase.from_files(files)
    assert len(codebase.files) == 4


def test_from_files_explicit_language_mismatch():
    """Test error when explicit language doesn't match extensions"""
    files = {"main.py": "print('hello')", "utils.py": "def add(a, b): return a + b"}
    with pytest.raises(ValueError, match="Provided language.*doesn't match inferred language"):
        Codebase.from_files(files, language="typescript")


def test_from_files_explicit_language_match():
    """Test explicit language matching file extensions works"""
    files = {"main.py": "print('hello')", "utils.py": "def add(a, b): return a + b"}
    codebase = Codebase.from_files(files, language="python")
    assert len(codebase.files) == 2
