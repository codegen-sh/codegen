import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from codegen.git.repo_operator.remote_repo_operator import RemoteRepoOperator
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
def mock_db():
    return MagicMock()


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


def test_remote_repo_operator_init(mock_db, mock_repo_model, temp_dir):
    """Test that RemoteRepoOperator initializes correctly."""
    # Patch the setup_repo_dir method to avoid actual Git operations
    with patch.object(RemoteRepoOperator, "setup_repo_dir"):
        op = RemoteRepoOperator(
            db=mock_db,
            repo_model=mock_repo_model,
            base_dir=temp_dir,
            setup_option=SetupOption.SKIP,
            access_token="test-token",
        )

        assert op.db == mock_db
        assert op.repo_model == mock_repo_model
        assert op.base_dir == temp_dir
        assert op.repo_name == "test-repo"
        assert op.repo_path == os.path.join(temp_dir, "test-repo")
        assert op.access_token == "test-token"


def test_remote_git_repo_property(mock_db, mock_repo_model, temp_dir):
    """Test the remote_git_repo property."""
    # Patch the setup_repo_dir method to avoid actual Git operations
    with patch.object(RemoteRepoOperator, "setup_repo_dir"):
        # Patch the GitRepoClient constructor
        with patch("codegen.git.clients.git_repo_client.GitRepoClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            op = RemoteRepoOperator(
                db=mock_db,
                repo_model=mock_repo_model,
                base_dir=temp_dir,
                setup_option=SetupOption.SKIP,
                access_token="test-token",
            )

            # Access the property to trigger the lazy initialization
            remote_repo = op.remote_git_repo

            # Verify that the GitRepoClient was created with the correct arguments
            mock_client.assert_called_once_with(op.repo_config, access_token="test-token")
            assert remote_repo == mock_client_instance


def test_setup_repo_dir(mock_db, mock_repo_model, temp_dir):
    """Test the setup_repo_dir method."""
    # Patch the os.makedirs and os.chdir functions
    with (
        patch("os.makedirs") as mock_makedirs,
        patch("os.chdir") as mock_chdir,
        patch.object(RemoteRepoOperator, "clone_repo") as mock_clone_repo,
        patch.object(RemoteRepoOperator, "clone_or_pull_repo") as mock_clone_or_pull_repo,
        patch.object(RemoteRepoOperator, "repo_exists", return_value=False) as mock_repo_exists,
    ):
        op = RemoteRepoOperator(
            db=mock_db,
            repo_model=mock_repo_model,
            base_dir=temp_dir,
            setup_option=None,  # Don't call setup_repo_dir in __init__
        )

        # Test CLONE option
        op.setup_repo_dir(setup_option=SetupOption.CLONE, shallow=True)
        mock_makedirs.assert_called_with(temp_dir, exist_ok=True)
        mock_chdir.assert_any_call(temp_dir)
        mock_clone_repo.assert_called_once_with(shallow=True)
        mock_chdir.assert_called_with(op.repo_path)

        # Reset mocks
        mock_makedirs.reset_mock()
        mock_chdir.reset_mock()
        mock_clone_repo.reset_mock()

        # Test PULL_OR_CLONE option
        op.setup_repo_dir(setup_option=SetupOption.PULL_OR_CLONE, shallow=False)
        mock_makedirs.assert_called_with(temp_dir, exist_ok=True)
        mock_chdir.assert_any_call(temp_dir)
        mock_clone_or_pull_repo.assert_called_once_with(shallow=False)
        mock_chdir.assert_called_with(op.repo_path)

        # Reset mocks
        mock_makedirs.reset_mock()
        mock_chdir.reset_mock()
        mock_clone_or_pull_repo.reset_mock()

        # Test SKIP option
        with patch("codegen.shared.logging.get_logger.get_logger") as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance

            op.setup_repo_dir(setup_option=SetupOption.SKIP)
            mock_makedirs.assert_called_with(temp_dir, exist_ok=True)
            mock_chdir.assert_any_call(temp_dir)
            mock_repo_exists.assert_called_once()
            mock_logger_instance.warning.assert_called_once()
            mock_chdir.assert_called_with(op.repo_path)
