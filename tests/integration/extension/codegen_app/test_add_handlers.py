import pytest
from slack_sdk import WebClient

from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.events.slack import SlackEvent


@pytest.fixture
def app():
    """Create a test CodegenApp instance"""
    return CodegenApp(name="test-handlers")


def test_register_slack_handler(app):
    """Test registering a Slack event handler"""

    @app.slack.event("message")
    def handle_message(client: WebClient, event: SlackEvent):
        return {"message": "Handled slack message"}

    # Verify handler was registered
    assert "message" in app.slack.registered_handlers
    assert app.slack.registered_handlers["message"] is not None


def test_register_github_handler(app):
    """Test registering a GitHub event handler"""

    @app.github.event("pull_request:opened")
    def handle_pr(event: dict):
        return {"message": "Handled PR"}

    # Verify handler was registered
    assert "pull_request:opened" in app.github.registered_handlers
    assert app.github.registered_handlers["pull_request:opened"] is not None


def test_register_linear_handler(app):
    """Test registering a Linear event handler"""

    @app.linear.event("Issue")
    def handle_issue(event: dict):
        return {"message": "Handled issue"}

    # Verify handler was registered
    handler = app.linear.registered_handlers[handle_issue.__qualname__]
    assert handler.event_name == "Issue"
    assert handler.handler_func is not None


def test_register_multiple_handlers(app):
    """Test registering multiple handlers across different providers"""

    # Register Slack handler
    @app.slack.event("message")
    def handle_slack(client: WebClient, event: SlackEvent):
        return {"message": "Handled slack"}

    # Register GitHub handler
    @app.github.event("push")
    def handle_push(event: dict):
        return {"message": "Handled push"}

    # Register Linear handler
    @app.linear.event("Issue")
    def handle_linear(event: dict):
        return {"message": "Handled linear"}

    # Verify all handlers were registered
    assert "message" in app.slack.registered_handlers
    assert "push" in app.github.registered_handlers
    assert handle_linear.__qualname__ in app.linear.registered_handlers

    # Verify each handler is properly configured
    assert app.slack.registered_handlers["message"] is not None
    assert app.github.registered_handlers["push"] is not None
    assert app.linear.registered_handlers[handle_linear.__qualname__].event_name == "Issue"


def test_handler_registration_is_isolated(app):
    """Test that handlers are properly isolated between provider types"""

    @app.slack.event("message")
    def handle_slack(client: WebClient, event: SlackEvent):
        return {"message": "Handled slack"}

    # Verify handler is only in Slack registry
    assert "message" in app.slack.registered_handlers
    assert "message" not in app.github.registered_handlers
    assert not any(h.event_name == "message" for h in app.linear.registered_handlers.values())
