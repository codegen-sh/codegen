from typing import Any

import httpx
from pydantic import BaseModel


class SlackTestEvent(BaseModel):
    """Helper class to construct test Slack events"""

    user: str = "U123456"
    type: str = "message"
    ts: str = "1234567890.123456"
    client_msg_id: str = "test-msg-id"
    text: str = "Hello world"
    team: str = "T123456"
    channel: str = "C123456"
    event_ts: str = "1234567890.123456"
    blocks: list = []


class CodegenClient:
    """Client for testing CodegenApp endpoints"""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=timeout)

    async def send_slack_message(self, text: str, channel: str = "C123456", event_type: str = "message", **kwargs) -> dict[str, Any]:
        """Send a test Slack message event

        Args:
            text: The message text
            channel: The channel ID
            event_type: The type of event (e.g. 'message', 'app_mention')
            **kwargs: Additional fields to override in the event
        """
        event = SlackTestEvent(text=text, channel=channel, type=event_type, **kwargs)

        payload = {
            "token": "test_token",
            "team_id": "T123456",
            "api_app_id": "A123456",
            "event": event.model_dump(),
            "type": "event_callback",
            "event_id": "Ev123456",
            "event_time": 1234567890,
        }

        response = await self.client.post(f"{self.base_url}/slack/events", json=payload)
        return response.json()

    async def send_github_event(self, event_type: str, action: str | None = None, payload: dict | None = None) -> dict[str, Any]:
        """Send a test GitHub webhook event

        Args:
            event_type: The type of event (e.g. 'pull_request', 'push')
            action: The action for the event (e.g. 'labeled', 'opened')
            payload: The event payload
        """
        # Construct headers that GitHub would send
        headers = {
            "x-github-event": event_type,
            "x-github-delivery": "test-delivery-id",
            "x-github-hook-id": "test-hook-id",
            "x-github-hook-installation-target-id": "test-target-id",
            "x-github-hook-installation-target-type": "repository",
        }

        response = await self.client.post(
            f"{self.base_url}/github/events",
            json=payload,
            headers=headers,
        )
        return response.json()

    async def send_linear_event(self, payload: dict) -> dict[str, Any]:
        """Send a test Linear webhook event

        Args:
            payload: The event payload
        """
        response = await self.client.post(f"{self.base_url}/linear/events", json=payload)
        return response.json()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
