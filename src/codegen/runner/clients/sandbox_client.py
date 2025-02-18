"""Client used to abstract the weird stdin/stdout communication we have with the sandbox"""

import logging
import os
import subprocess
import time

import requests
from fastapi import params

from codegen.git.schemas.repo_config import RepoConfig
from codegen.runner.models.apis import SANDBOX_SERVER_PORT

logger = logging.getLogger(__name__)


class SandboxClient:
    """Client for interacting with the locally hosted sandbox server."""

    host: str
    port: int
    base_url: str
    _process: subprocess.Popen | None

    def __init__(self, repo_config: RepoConfig, git_access_token: str | None, host: str = "127.0.0.1", port: int = SANDBOX_SERVER_PORT):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._process = None
        self._start_server(repo_config, git_access_token)

    def _start_server(self, repo_config: RepoConfig, git_access_token: str | None) -> None:
        """Start the FastAPI server in a subprocess"""
        env = os.environ.copy()
        env.update(
            {
                "CODEGEN_REPOSITORY__REPO_PATH": repo_config.repo_path,
                "CODEGEN_REPOSITORY__REPO_NAME": repo_config.name,
                "CODEGEN_REPOSITORY__FULL_NAME": repo_config.full_name,
                "CODEGEN_REPOSITORY__LANGUAGE": repo_config.language.value,
                "CODEGEN_SECRETS__GITHUB_TOKEN": git_access_token,
            }
        )

        logger.info(f"Starting local sandbox server on {self.base_url} with repo setup in base_dir {repo_config.base_dir}")
        self._process = subprocess.Popen(
            [
                "uvicorn",
                "codegen.runner.sandbox.server:app",
                "--host",
                self.host,
                "--port",
                str(self.port),
            ],
            env=env,
        )
        self._wait_for_server()

    def _wait_for_server(self, timeout: int = 60, interval: float = 0.1) -> None:
        """Wait for the server to start by polling the health endpoint"""
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            try:
                self.get("/")
                return
            except requests.ConnectionError:
                time.sleep(interval)
        msg = "Server failed to start within timeout period"
        raise TimeoutError(msg)

    def __del__(self):
        """Cleanup the subprocess when the client is destroyed"""
        if self._process is not None:
            self._process.terminate()
            self._process.wait()

    def get(self, endpoint: str, data: dict | None = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, json=data)
        response.raise_for_status()
        return response

    def post(self, endpoint: str, data: dict | None = None, authorization: str | params.Header | None = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": str(authorization)} if authorization else None
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response
