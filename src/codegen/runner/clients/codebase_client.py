"""Client used to abstract the weird stdin/stdout communication we have with the sandbox"""

import logging

from codegen.git.schemas.repo_config import RepoConfig
from codegen.runner.clients.server_client import LocalServerClient
from codegen.runner.models.apis import SANDBOX_SERVER_PORT

logger = logging.getLogger(__name__)

RUNNER_SERVER_PATH = "codegen.runner.sandbox.server:app"


class CodebaseClient(LocalServerClient):
    """Client for interacting with the locally hosted sandbox server."""

    repo_config: RepoConfig
    git_access_token: str | None

    def __init__(self, repo_config: RepoConfig, git_access_token: str | None, host: str = "127.0.0.1", port: int = SANDBOX_SERVER_PORT):
        self.repo_config = repo_config
        self.git_access_token = git_access_token
        super().__init__(server_path=RUNNER_SERVER_PATH, host=host, port=port)

    def _get_envs(self):
        envs = super()._get_envs()
        envs.update(
            {
                "CODEGEN_REPOSITORY__REPO_PATH": self.repo_config.repo_path,
                "CODEGEN_REPOSITORY__REPO_NAME": self.repo_config.name,
                "CODEGEN_REPOSITORY__FULL_NAME": self.repo_config.full_name,
                "CODEGEN_REPOSITORY__LANGUAGE": self.repo_config.language.value,
                "CODEGEN_SECRETS__GITHUB_TOKEN": self.git_access_token,
            }
        )
        return envs
