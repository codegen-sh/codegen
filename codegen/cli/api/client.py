import json
from typing import ClassVar, TypeVar

import requests
from pydantic import BaseModel
from rich import print as rprint

from codegen.cli.env.global_env import global_env
from codegen.cli.errors import InvalidTokenError, ServerError

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class AuthContext(BaseModel):
    """Authentication context model."""

    status: str


class Identity(BaseModel):
    """User identity model."""

    auth_context: AuthContext


class RestAPI:
    """Handles auth + validation with the codegen API."""

    _session: ClassVar[requests.Session] = requests.Session()

    auth_token: str

    def __init__(self, auth_token: str):
        self.auth_token = auth_token

    def _get_headers(self) -> dict[str, str]:
        """Get headers with authentication token."""
        return {"Authorization": f"Bearer {self.auth_token}"}

    def _make_request(
        self,
        method: str,
        endpoint: str,
        input_data: InputT | None,
        output_model: type[OutputT],
    ) -> OutputT:
        """Make an API request with input validation and response handling."""
        if global_env.DEBUG:
            rprint(f"[purple]{method}[/purple] {endpoint}")
            if input_data:
                rprint(f"{json.dumps(input_data.model_dump(), indent=4)}")

        try:
            headers = self._get_headers()

            json_data = input_data.model_dump() if input_data else None

            response = self._session.request(
                method,
                endpoint,
                json=json_data,
                headers=headers,
            )

            if response.status_code == 200:
                try:
                    return output_model.model_validate(response.json())
                except ValueError as e:
                    msg = f"Invalid response format: {e}"
                    raise ServerError(msg)
            elif response.status_code == 401:
                msg = "Invalid or expired authentication token"
                raise InvalidTokenError(msg)
            elif response.status_code == 500:
                msg = "The server encountered an error while processing your request"
                raise ServerError(msg)
            else:
                try:
                    error_json = response.json()
                    error_msg = error_json.get("detail", error_json)
                except Exception:
                    error_msg = response.text
                msg = f"Error ({response.status_code}): {error_msg}"
                raise ServerError(msg)

        except requests.RequestException as e:
            msg = f"Network error: {e!s}"
            raise ServerError(msg)
