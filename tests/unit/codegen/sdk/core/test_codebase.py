from unittest.mock import MagicMock, create_autospec, patch

import pytest

from codegen.configs.models.secrets import SecretsConfig
from codegen.sdk.codebase.codebase_context import CodebaseContext
from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.codebase import Codebase


@pytest.fixture(autouse=True)
def context_mock():
    mock_context = create_autospec(CodebaseContext, instance=True)
    for attr in CodebaseContext.__annotations__:
        if not hasattr(mock_context, attr):
            setattr(mock_context, attr, MagicMock(name=attr))
    with patch("codegen.sdk.core.codebase.CodebaseContext", return_value=mock_context):
        yield mock_context


@pytest.fixture
def codebase(context_mock, tmpdir):
    """Create a simple codebase for testing."""
    # language=python
    content = """
def hello():
    print("Hello, world!")

class Greeter:
    def greet(self):
        hello()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"src/main.py": content}, verify_output=False) as codebase:
        yield codebase


def test_codeowners_property(context_mock, codebase):
    context_mock.codeowners_parser.paths = [(..., ..., [("test", "test")], ..., ...)]
    codebase.files = MagicMock()
    assert isinstance(codebase.codeowners, list)
    assert len(codebase.codeowners) == 1
    assert callable(codebase.codeowners[0].files_source)
    assert codebase.codeowners[0].files_source() == codebase.files.return_value


def test_from_codebase_non_existent_repo(context_mock, tmpdir):
    with get_codebase_session(tmpdir=tmpdir, files={"src/main.py": "print('Hello, world!')"}, verify_output=False) as codebase:
        codebase = Codebase.from_repo("some-org/non-existent-repo", tmp_dir=tmpdir, secrets=SecretsConfig(github_token="some-token"))
        assert codebase is None
