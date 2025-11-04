import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from codegen.git.repo_operator.local_repo_operator import LocalRepoOperator
from codegen.git.schemas.enums import SetupOption
from codegen.git.schemas.repo_config import RepoConfig


@pytest.fixture
def mock_repo_model():
    repo_model = MagicMock()
    repo_config = RepoConfig(
        name="test-repo",
        full_name="test-org/test-repo",
        clone_url="https://github.com/test-org/test-repo.git",
    )
    repo_model.repo_config = repo_config
    return repo_model


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


def test_local_repo_operator_init(mock_repo_model, temp_dir):
    """Test that LocalRepoOperator initializes correctly."""
    # Patch the setup_repo_dir method to avoid actual Git operations
    with patch.object(LocalRepoOperator, "setup_repo_dir"):
        op = LocalRepoOperator(
            repo_model=mock_repo_model,
            base_dir=temp_dir,
            setup_option=SetupOption.SKIP,
        )

        assert op.repo_model == mock_repo_model
        assert op.base_dir == temp_dir
        assert op.repo_name == "test-repo"
        assert op.repo_path == os.path.join(temp_dir, "test-repo")


@patch("app.db.RepoModel")
def test_from_repo_id(mock_repo_model_class, mock_repo_model):
    """Test the from_repo_id class method."""
    mock_db = MagicMock()
    mock_repo_model_class.find_by_id.return_value = mock_repo_model

    # Patch the setup_repo_dir method to avoid actual Git operations
    with patch.object(LocalRepoOperator, "setup_repo_dir"):
        op = LocalRepoOperator.from_repo_id(
            db=mock_db,
            repo_id=123,
            setup_option=SetupOption.SKIP,
        )

        mock_repo_model_class.find_by_id.assert_called_once_with(mock_db, 123)
        assert op.repo_model == mock_repo_model


@patch("app.db.RepoModel")
def test_from_repo_id_not_found(mock_repo_model_class):
    """Test the from_repo_id class method when the repo is not found."""
    mock_db = MagicMock()
    mock_repo_model_class.find_by_id.return_value = None

    with pytest.raises(ValueError, match="Repository with ID 123 not found"):
        LocalRepoOperator.from_repo_id(
            db=mock_db,
            repo_id=123,
            setup_option=SetupOption.SKIP,
        )
