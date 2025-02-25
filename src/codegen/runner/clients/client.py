"""Client used to abstract the weird stdin/stdout communication we have with the sandbox"""

import logging

import requests
from fastapi import params

logger = logging.getLogger(__name__)

DEFAULT_SERVER_PORT = 4002

EPHEMERAL_SERVER_PATH = "codegen.runner.sandbox.ephemeral_server:app"


class Client:
    """Client for interacting with the sandbox server."""

    host: str
    port: int
    base_url: str

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

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
