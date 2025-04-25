import os
import tempfile
from pathlib import Path

from codegen.sdk.codebase.config import ProjectConfig
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_explicit_language_respected():
    """Test that explicitly provided language is respected and not overridden by detection."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a temporary directory with more TypeScript files than Python files
        ts_dir = Path(tmp_dir) / "ts"
        py_dir = Path(tmp_dir) / "py"
        ts_dir.mkdir()
        py_dir.mkdir()

        # Create TypeScript files
        for i in range(5):
            with open(ts_dir / f"file{i}.ts", "w") as f:
                f.write(f"// TypeScript file {i}")

        # Create fewer Python files
        for i in range(2):
            with open(py_dir / f"file{i}.py", "w") as f:
                f.write(f"# Python file {i}")

        # Initialize git repo
        os.system(f"cd {tmp_dir} && git init && git config user.email 'test@example.com' && git config user.name 'Test User' && git add . && git commit -m 'Initial commit'")

        # Test with explicit Python language
        project_config = ProjectConfig.from_path(path=str(tmp_dir), programming_language=ProgrammingLanguage.PYTHON)

        # Verify that the language is Python, not TypeScript (which would be detected based on file count)
        assert project_config.programming_language == ProgrammingLanguage.PYTHON

        # Test with explicit TypeScript language
        project_config = ProjectConfig.from_path(
            path=str(py_dir),  # Use Python directory
            programming_language=ProgrammingLanguage.TYPESCRIPT,
        )

        # Verify that the language is TypeScript, not Python (which would be detected based on file count)
        assert project_config.programming_language == ProgrammingLanguage.TYPESCRIPT


def test_subfolder_language_detection():
    """Test that language detection respects the specified subfolder."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a temporary directory with TypeScript files in root and Python files in subfolder
        ts_dir = Path(tmp_dir)
        py_dir = Path(tmp_dir) / "python_only"
        py_dir.mkdir()

        # Create TypeScript files in root
        for i in range(5):
            with open(ts_dir / f"file{i}.ts", "w") as f:
                f.write(f"// TypeScript file {i}")

        # Create Python files in subfolder
        for i in range(3):
            with open(py_dir / f"file{i}.py", "w") as f:
                f.write(f"# Python file {i}")

        # Initialize git repo
        os.system(f"cd {tmp_dir} && git init && git config user.email 'test@example.com' && git config user.name 'Test User' && git add . && git commit -m 'Initial commit'")

        # Test with root path - should detect TypeScript
        project_config = ProjectConfig.from_path(path=str(tmp_dir))
        assert project_config.programming_language == ProgrammingLanguage.TYPESCRIPT

        # Test with Python subfolder path - should detect Python
        project_config = ProjectConfig.from_path(path=str(py_dir))
        assert project_config.programming_language == ProgrammingLanguage.PYTHON
