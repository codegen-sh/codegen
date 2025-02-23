import pytest
from slack_sdk import WebClient

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
