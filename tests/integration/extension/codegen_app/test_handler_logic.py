import asyncio
from contextlib import asynccontextmanager

import pytest
from slack_sdk import WebClient
from uvicorn.config import Config
from uvicorn.server import Server

from codegen.extensions.events.client import CodegenClient
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.events.slack import SlackEvent


@pytest.fixture
def app():
    """Create a test CodegenApp instance"""
    return CodegenApp(name="test-handlers")


@pytest.fixture
def app_with_handlers(app):
    """Create a CodegenApp instance with pre-registered handlers"""

    # Register an app mention handler
    @app.slack.event("app_mention")
    async def handle_mention(client: WebClient, event: SlackEvent):
        return {"message": "Mentioned", "received_text": event.text}

    return app


@asynccontextmanager
async def run_codegen_app(app: CodegenApp):
    """Run the CodegenApp server as a context manager"""
    # Configure uvicorn
    config = Config(app=app.app, host="127.0.0.1", port=8000, log_level="info")
    server = Server(config=config)

    # Start the server
    server_task = asyncio.create_task(server.serve())
    await asyncio.sleep(1)  # Give the server a moment to start

    try:
        yield server
    finally:
        # Shutdown the server
        server.should_exit = True
        await server_task


@pytest.mark.asyncio
async def test_server_slack_mention(app_with_handlers):
    """Test sending a Slack mention through the actual server"""
    async with run_codegen_app(app_with_handlers):
        # Create a test client
        client = CodegenClient()

        try:
            # Send test mention
            response = await client.send_slack_message(text="<@U123BOT> help me with this code", channel="C123TEST", event_type="app_mention")

            # Verify the response
            assert response is not None
            assert response["message"] == "Mentioned"
            assert response["received_text"] == "<@U123BOT> help me with this code"

        finally:
            await client.close()


@pytest.mark.asyncio
async def test_simulate_slack_mention(app_with_handlers):
    """Test simulating a Slack app_mention event"""
    # Create a test mention payload
    payload = {
        "token": "test_token",
        "team_id": "T123456",
        "api_app_id": "A123456",
        "event": {
            "type": "app_mention",
            "user": "U123456",
            "text": "<@U123BOT> help me with this code",
            "ts": "1234567890.123456",
            "channel": "C123456",
            "event_ts": "1234567890.123456",
        },
        "type": "event_callback",
        "event_id": "Ev123456",
        "event_time": 1234567890,
    }

    # Simulate the event
    response = await app_with_handlers.simulate_event(provider="slack", event_type="app_mention", payload=payload)

    # Verify the response
    assert response is not None
    assert response["message"] == "Mentioned"
    assert response["received_text"] == "<@U123BOT> help me with this code"


@pytest.mark.asyncio
async def test_simulate_unknown_provider(app_with_handlers):
    """Test simulating an event with an unknown provider"""
    with pytest.raises(ValueError) as exc_info:
        await app_with_handlers.simulate_event(provider="unknown", event_type="test", payload={})

    assert "Unknown provider" in str(exc_info.value)


@pytest.mark.asyncio
async def test_simulate_unregistered_event(app_with_handlers):
    """Test simulating an event type that has no registered handler"""
    payload = {"event": {"type": "unknown_event", "user": "U123456"}}

    response = await app_with_handlers.simulate_event(provider="slack", event_type="unknown_event", payload=payload)

    # Should return a default response for unhandled events
    assert response["message"] == "Event handled successfully"
