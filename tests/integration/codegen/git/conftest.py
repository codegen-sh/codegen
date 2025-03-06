from unittest.mock import MagicMock

import pytest

from codegen.configs.models.repository import RepositoryConfig
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.enums import SetupOption


@pytest.fixture()
def mock_config():
    """Mock Config instance to prevent actual environment variable access during tests."""
    mock_config = MagicMock()
    mock_config.GITHUB_TOKEN = "test-highside-token"

    yield mock_config


@pytest.fixture()
def repo_config(tmpdir):
    repo_config = RepositoryConfig(
        name="Kevin-s-Adventure-Game",
        owner="codegen-sh",
        base_dir=str(tmpdir),
    )
    yield repo_config


@pytest.fixture
def op(repo_config, request):
    op = RepoOperator(repo_config=repo_config, shallow=request.param if hasattr(request, "param") else True, bot_commit=False, setup_option=SetupOption.PULL_OR_CLONE)
    yield op
