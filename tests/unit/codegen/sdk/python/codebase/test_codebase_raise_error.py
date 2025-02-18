import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_python_exports_not_supported(tmpdir):
    """Test that exports are not supported in Python codebases."""
    # language=python
    content = """
def hello():
    pass
    """
    # Create a Python codebase with a simple Python file
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        # Verify that accessing exports raises NotImplementedError
        with pytest.raises(NotImplementedError):
            _ = codebase.exports
