from collections.abc import Generator
from unittest.mock import Mock

import pytest

from codegen.configs.models.repository import RepositoryConfig
from codegen.git.clients.git_repo_client import GitRepoClient
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.enums import SetupOption
from codegen.runner.clients.codebase_client import CodebaseClient
from codegen.shared.network.port import get_free_port


@pytest.fixture()
def repo_config(tmpdir) -> Generator[RepositoryConfig, None, None]:
    yield RepositoryConfig(
        path=str(tmpdir / "Kevin-s-Adventure-Game"),
        owner="codegen-sh",
        language="PYTHON",
    )


@pytest.fixture
def op(repo_config: RepositoryConfig) -> Generator[RepoOperator, None, None]:
    yield RepoOperator(repo_config=repo_config, setup_option=SetupOption.PULL_OR_CLONE)


@pytest.fixture
def git_repo_client(op: RepoOperator, repo_config: RepositoryConfig) -> Generator[GitRepoClient, None, None]:
    yield GitRepoClient(repo_full_name=repo_config.full_name, access_token=op.access_token)


@pytest.fixture
def codebase_client(repo_config: RepositoryConfig) -> Generator[CodebaseClient, None, None]:
    sb_client = CodebaseClient(repo_config=repo_config, port=get_free_port())
    sb_client.runner = Mock()
    yield sb_client
