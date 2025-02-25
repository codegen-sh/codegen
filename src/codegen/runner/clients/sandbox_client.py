"""Client used to abstract the weird stdin/stdout communication we have with the sandbox"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import requests
from modal.exception import SandboxTimeoutError
from urllib3.exceptions import NewConnectionError

from codegen.runner.models.apis import SANDBOX_SERVER_PORT, ServerInfo

if TYPE_CHECKING:
    from fastapi import params
    from modal import Sandbox, Tunnel

logger = logging.getLogger(__name__)


class RemoteSandboxClient:
    """Client for interacting with the remote sandbox server. To be used on the Modal web-app side."""

    sandbox: Sandbox
    _tunnel: Tunnel | None

    def __init__(self, sandbox: Sandbox) -> None:
        self.sandbox = sandbox
        self._tunnel = None

    @classmethod
    def from_sandbox(cls, sandbox: Sandbox) -> RemoteSandboxClient:
        return cls(db=None, sandbox=sandbox, runner=None)

    @property
    def tunnel(self):
        try:
            if not self._tunnel:
                self._tunnel = self.sandbox.tunnels()[SANDBOX_SERVER_PORT]
            return self._tunnel
        except SandboxTimeoutError:
            logger.exception(f"Timed out while trying to reach the sandbox server at {self.sandbox}")
            raise

    def status(self, raise_on_error: bool = True) -> ServerInfo:
        try:
            response = self.get("/")
            return ServerInfo.model_validate(response.json())
        except requests.exceptions.ConnectionError:
            if raise_on_error:
                raise
            return ServerInfo()

    def get(self, endpoint: str, data: dict | None = None) -> requests.Response:
        logger.info(f"> Requesting GET {endpoint} at {self.tunnel.url}")
        return requests.get(f"{self.tunnel.url}{endpoint}")

    def post(self, endpoint: str, data: dict | None = None, authorization: str | params.Header | None = None) -> requests.Response:
        logger.info(f"> Requesting POST {endpoint} at {self.tunnel.url}")
        try:
            res = requests.post(f"{self.tunnel.url}{endpoint}", json=data or {}, headers={"Authorization": str(authorization)} if authorization else {})
            logger.info(f" > Received {res.status_code} response: {res.json()}")

            return res

        except (requests.exceptions.ConnectionError, NewConnectionError) as e:
            logger.exception(f"Failed to connect to sandbox at {self.tunnel.url}: {e}")
            raise
