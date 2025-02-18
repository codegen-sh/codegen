import socket
from collections.abc import Generator
from contextlib import closing
from unittest.mock import Mock

import pytest

from codegen.git.clients.git_repo_client import GitRepoClient
from codegen.git.repo_operator.remote_repo_operator import RemoteRepoOperator
from codegen.git.schemas.repo_config import RepoConfig
from codegen.runner.clients.sandbox_client import SandboxClient
from codegen.shared.configs.session_configs import config
from codegen.shared.enums.programming_language import ProgrammingLanguage


@pytest.fixture
def get_free_port():
    """Find and return a free port on localhost"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port


@pytest.fixture()
def repo_config(tmpdir) -> Generator[RepoConfig, None, None]:
    yield RepoConfig(
        name="Kevin-s-Adventure-Game",
        full_name="codegen-sh/Kevin-s-Adventure-Game",
        organization_name="codegen-sh",
        language=ProgrammingLanguage.PYTHON,
        base_dir=str(tmpdir),
    )


@pytest.fixture
def op(repo_config: RepoConfig) -> Generator[RemoteRepoOperator, None, None]:
    yield RemoteRepoOperator(repo_config=repo_config, access_token=config.secrets.github_token)


@pytest.fixture
def git_repo_client(repo_config: RepoConfig) -> Generator[GitRepoClient, None, None]:
    yield GitRepoClient(repo_config=repo_config, access_token=config.secrets.github_token)


@pytest.fixture
def sandbox_client(repo_config: RepoConfig, get_free_port) -> Generator[SandboxClient, None, None]:
    sb_client = SandboxClient(repo_config=repo_config, port=get_free_port, git_access_token=config.secrets.github_token)
    sb_client.runner = Mock()
    yield sb_client
