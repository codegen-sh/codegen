"""Client used to abstract the weird stdin/stdout communication we have with the sandbox"""

import os
import subprocess
import time

from codegen.configs.models.secrets import SecretsConfig
from codegen.git.schemas.repo_config import RepoConfig
from codegen.runner.clients.client import Client
from codegen.runner.models.apis import SANDBOX_SERVER_PORT
from codegen.shared.logging.get_logger import get_logger

DEFAULT_SERVER_PORT = 4002
EPHEMERAL_SERVER_PATH = "codegen.runner.sandbox.ephemeral_server:app"
RUNNER_SERVER_PATH = "codegen.runner.sandbox.server:app"


logger = get_logger(__name__)


class CodebaseClient(Client):
    """Client for interacting with the locally hosted sandbox server."""

    repo_config: RepoConfig

    def __init__(self, repo_config: RepoConfig, host: str = "127.0.0.1", port: int = SANDBOX_SERVER_PORT, server_path: str = RUNNER_SERVER_PATH):
        super().__init__(host=host, port=port)
        self.repo_config = repo_config
        self._process = None
        self._start_server(server_path)

    def __del__(self):
        """Cleanup the subprocess when the client is destroyed"""
        if self._process is not None:
            self._process.terminate()
            self._process.wait()

    def _start_server(self, server_path: str) -> None:
        """Start the FastAPI server in a subprocess"""
        envs = self._get_envs()
        logger.info(f"Starting local server on {self.base_url} with envvars: {envs}")

        self._process = subprocess.Popen(
            [
                "uvicorn",
                server_path,
                "--host",
                self.host,
                "--port",
                str(self.port),
            ],
            env=envs,
        )
        self._wait_for_server()

    def _wait_for_server(self, timeout: int = 30, interval: float = 0.3) -> None:
        """Wait for the server to start by polling the health endpoint"""
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if self.is_running():
                return
            time.sleep(interval)
        msg = "Server failed to start within timeout period"
        raise TimeoutError(msg)

    def _get_envs(self) -> dict:
        envs = os.environ.copy()
        codebase_envs = {
            "REPOSITORY_PATH": str(self.repo_config.repo_path),
            "REPOSITORY_OWNER": self.repo_config.organization_name,
            "REPOSITORY_LANGUAGE": self.repo_config.language.value,
            "GITHUB_TOKEN": SecretsConfig().github_token,
        }

        envs.update(codebase_envs)
        return envs


if __name__ == "__main__":
    test_config = RepoConfig.from_repo_path("/Users/caroljung/git/codegen/codegen-agi")
    test_config.full_name = "codegen-sh/codegen-agi"
    client = CodebaseClient(test_config)
    print(client.is_running())
