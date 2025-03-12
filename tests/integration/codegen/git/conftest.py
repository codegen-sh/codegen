from unittest.mock import MagicMock

import pytest

from codegen.git.schemas.repo_config import RepoConfig


@pytest.fixture()
def mock_config():
    """Mock Config instance to prevent actual environment variable access during tests."""
    mock_config = MagicMock()
    mock_config.GITHUB_TOKEN = "test-highside-token"

    yield mock_config


@pytest.fixture()
def repo_config(tmpdir):
    repo_config = RepoConfig(
        name="Kevin-s-Adventure-Game",
        full_name="codegen-sh/Kevin-s-Adventure-Game",
        base_dir=str(tmpdir),
    )
    yield repo_config
