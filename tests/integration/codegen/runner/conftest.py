from collections.abc import Generator
from unittest.mock import Mock

import pytest

from codegen.git.clients.git_repo_client import GitRepoClient
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.enums import SetupOption
from codegen.git.schemas.repo_config import RepoConfig
from codegen.runner.clients.codebase_client import CodebaseClient
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.network.port import get_free_port


@pytest.fixture()
def repo_config(tmpdir) -> Generator[RepoConfig, None, None]:
    yield RepoConfig(
        name="Kevin-s-Adventure-Game",
        full_name="codegen-sh/Kevin-s-Adventure-Game",
        language=ProgrammingLanguage.PYTHON,
        base_dir=str(tmpdir),
    )


@pytest.fixture
def op(repo_config: RepoConfig) -> Generator[RepoOperator, None, None]:
    yield RepoOperator(repo_config=repo_config, setup_option=SetupOption.PULL_OR_CLONE)


@pytest.fixture
def git_repo_client(op: RepoOperator, repo_config: RepoConfig) -> Generator[GitRepoClient, None, None]:
    yield GitRepoClient(repo_config=repo_config, access_token=op.access_token)


@pytest.fixture
def codebase_client(repo_config: RepoConfig) -> Generator[CodebaseClient, None, None]:
    sb_client = CodebaseClient(repo_config=repo_config, port=get_free_port())
    sb_client.runner = Mock()
    yield sb_client
