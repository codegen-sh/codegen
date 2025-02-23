"""Client used to abstract the weird stdin/stdout communication we have with the sandbox"""

import logging
import os
import subprocess
import time

import requests
from fastapi import params

logger = logging.getLogger(__name__)

DEFAULT_SERVER_PORT = 4002

EPHEMERAL_SERVER_PATH = "codegen.runner.sandbox.ephemeral_server:app"


class LocalServerClient:
    """Client for interacting with the sandbox server."""

    host: str
    port: int
    base_url: str
    _process: subprocess.Popen | None

    def __init__(self, server_path: str = EPHEMERAL_SERVER_PATH, host: str = "127.0.0.1", port: int = DEFAULT_SERVER_PORT):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._process = None
        self._start_server(server_path)

    def __del__(self):
        """Cleanup the subprocess when the client is destroyed"""
        if self._process is not None:
            self._process.terminate()
            self._process.wait()

    def _get_envs(self) -> dict:
        return os.environ.copy()

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
            if self.healthcheck(raise_on_error=False):
                return
            time.sleep(interval)
        msg = "Server failed to start within timeout period"
        raise TimeoutError(msg)

    def healthcheck(self, raise_on_error: bool = True) -> bool:
        try:
            self.get("/")
            return True
        except requests.exceptions.ConnectionError:
            if raise_on_error:
                raise
            return False

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
