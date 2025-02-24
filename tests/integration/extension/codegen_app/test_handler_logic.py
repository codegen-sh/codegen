import asyncio
from contextlib import asynccontextmanager

import pytest
from uvicorn.config import Config
from uvicorn.server import Server

from codegen.extensions.events.client import CodegenClient
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent
from codegen.extensions.linear.types import LinearEvent
from codegen.extensions.slack.types import SlackEvent


@pytest.fixture
def app():
    """Create a test CodegenApp instance"""
    return CodegenApp(name="test-handlers")


@pytest.fixture
def app_with_handlers(app):
    """Create a CodegenApp instance with pre-registered handlers"""

    # Register Slack handler
    @app.slack.event("app_mention")
    async def handle_mention(event: SlackEvent):
        return {"message": "Mentioned", "received_text": event.text}

    # Register GitHub handler
    @app.github.event("pull_request:labeled")
    def handle_labeled(event: PullRequestLabeledEvent):
        return {
            "message": "PR labeled",
            "pr_number": event.number,
            "label": event.label.name,
            "title": event.pull_request.title,
        }

    # Register Linear handler
    @app.linear.event("Issue")
    def handle_issue_created(event: LinearEvent):
        return {
            "message": "Issue created",
            "issue_id": event.data.id,
            "title": event.data.title,
        }

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


@pytest.mark.asyncio
async def test_simulate_github_pr_labeled(app_with_handlers):
    """Test simulating a GitHub PR labeled event"""
    # Create a test PR labeled payload
    payload = {
        "action": "labeled",
        "number": 123,
        "pull_request": {
            "id": 12345,
            "number": 123,
            "state": "open",
            "locked": False,
            "title": "Test PR",
            "user": {"id": 1, "login": "test-user"},
            "body": "Test PR body",
            "labels": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "draft": False,
        },
        "label": {"id": 1, "node_id": "123", "url": "https://api.github.com/repos/test/test/labels/bug", "name": "bug", "description": "Bug report", "color": "red", "default": False},
        "repository": {"id": 1, "name": "test"},
        "sender": {"id": 1, "login": "test-user"},
    }

    # Simulate the event
    response = await app_with_handlers.simulate_event(provider="github", event_type="pull_request:labeled", payload=payload)

    # Verify the response
    assert response is not None
    assert response["message"] == "PR labeled"
    assert response["pr_number"] == 123
    assert response["label"] == "bug"
    assert response["title"] == "Test PR"


@pytest.mark.asyncio
async def test_server_github_pr_labeled(app_with_handlers):
    """Test sending a GitHub PR labeled event through the actual server"""
    async with run_codegen_app(app_with_handlers):
        # Create a test client
        client = CodegenClient()

        try:
            # Create test PR labeled payload
            payload = {
                "action": "labeled",
                "number": 123,
                "pull_request": {
                    "id": 12345,
                    "number": 123,
                    "node_id": "PR_123",
                    "state": "open",
                    "locked": False,
                    "title": "Test PR",
                    "user": {"id": 1, "login": "test-user", "node_id": "U_123", "type": "User"},
                    "body": "Test PR body",
                    "labels": [],
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "draft": False,
                    "head": {
                        "label": "user:feature",
                        "ref": "feature",
                        "sha": "abc123",
                        "user": {"id": 1, "login": "test-user", "node_id": "U_123", "type": "User"},
                        "repo": {"id": 1, "name": "test", "node_id": "R_123", "full_name": "test/test", "private": False, "owner": {"id": 1, "login": "test-user", "node_id": "U_123", "type": "User"}},
                    },
                    "base": {
                        "label": "main",
                        "ref": "main",
                        "sha": "def456",
                        "user": {"id": 1, "login": "test-user", "node_id": "U_123", "type": "User"},
                        "repo": {"id": 1, "name": "test", "node_id": "R_123", "full_name": "test/test", "private": False, "owner": {"id": 1, "login": "test-user", "node_id": "U_123", "type": "User"}},
                    },
                },
                "label": {"id": 1, "node_id": "L_123", "url": "https://api.github.com/repos/test/test/labels/bug", "name": "bug", "description": "Bug report", "color": "red", "default": False},
                "repository": {"id": 1, "name": "test", "node_id": "R_123", "full_name": "test/test", "private": False, "owner": {"id": 1, "login": "test-user", "node_id": "U_123", "type": "User"}},
                "sender": {"id": 1, "login": "test-user", "node_id": "U_123", "type": "User"},
            }

            # Send test event
            response = await client.send_github_event(
                event_type="pull_request",
                action="labeled",
                payload=payload,
            )

            # Verify the response
            assert response is not None
            assert response["message"] == "PR labeled"
            assert response["pr_number"] == 123
            assert response["label"] == "bug"
            assert response["title"] == "Test PR"

        finally:
            await client.close()


@pytest.mark.asyncio
async def test_simulate_linear_issue_created(app_with_handlers):
    """Test simulating a Linear issue created event"""
    # Create a test issue created payload
    payload = {
        "action": "create",
        "type": "Issue",
        "data": {
            "id": "abc-123",
            "title": "Test Issue",
            "description": "This is a test issue",
            "priority": 1,
            "teamId": "team-123",
        },
        "url": "https://linear.app/company/issue/ABC-123",
    }

    # Simulate the event
    response = await app_with_handlers.simulate_event(provider="linear", event_type="Issue", payload=payload)

    # Verify the response
    assert response is not None
    assert response["message"] == "Issue created"
    assert response["issue_id"] == "abc-123"
    assert response["title"] == "Test Issue"


@pytest.mark.asyncio
async def test_server_linear_issue_created(app_with_handlers):
    """Test sending a Linear issue created event through the actual server"""
    async with run_codegen_app(app_with_handlers):
        # Create a test client
        client = CodegenClient()

        try:
            # Create test issue created payload
            payload = {
                "action": "create",
                "type": "Issue",
                "data": {
                    "id": "abc-123",
                    "title": "Test Issue",
                    "description": "This is a test issue",
                    "priority": 1,
                    "teamId": "team-123",
                },
                "url": "https://linear.app/company/issue/ABC-123",
            }

            # Send test event
            response = await client.send_linear_event(payload=payload)

            # Verify the response
            assert response is not None
            assert response["message"] == "Issue created"
            assert response["issue_id"] == "abc-123"
            assert response["title"] == "Test Issue"

        finally:
            await client.close()
