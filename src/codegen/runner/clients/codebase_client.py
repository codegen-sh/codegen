"""Client used to abstract the weird stdin/stdout communication we have with the sandbox"""

import logging

from codegen.git.schemas.repo_config import RepoConfig
from codegen.runner.clients.server_client import LocalServerClient
from codegen.runner.models.apis import SANDBOX_SERVER_PORT
from codegen.shared.configs.session_configs import config

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

    def _get_envs(self) -> dict:
        envs = super()._get_envs()
        codebase_envs = {
            "CODEGEN_REPOSITORY__REPO_PATH": self.repo_config.repo_path,
            "CODEGEN_REPOSITORY__REPO_NAME": self.repo_config.name,
            "CODEGEN_REPOSITORY__FULL_NAME": self.repo_config.full_name,
            "CODEGEN_REPOSITORY__LANGUAGE": self.repo_config.language.value,
        }
        if self.git_access_token is not None:
            codebase_envs["CODEGEN_SECRETS__GITHUB_TOKEN"] = self.git_access_token

        envs.update(codebase_envs)
        return envs


if __name__ == "__main__":
    test_config = RepoConfig.from_repo_path("/Users/caroljung/git/codegen/codegen-agi")
    test_config.full_name = "codegen-sh/codegen-agi"
    client = CodebaseClient(test_config, config.secrets.github_token)
    print(client.healthcheck())
