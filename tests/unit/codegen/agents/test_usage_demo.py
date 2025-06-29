"""Demo test showing the exact usage pattern from the user's requirements."""

from unittest.mock import patch

import pytest

# This test demonstrates the exact usage pattern the user wanted to work


def test_usage_pattern_demo():
    """Test the exact usage pattern from the user's requirements."""
    with patch("codegen.agents.agent.AgentsApi"), patch("codegen.agents.agent.ApiClient"), patch("codegen.agents.agent.Configuration"):
        # Import works
        from codegen.agents.agent import Agent

        # Initialize the Agent with your organization ID and API token
        agent = Agent(
            org_id=123,  # Find this at codegen.com/developer
            token="YOUR_API_TOKEN",  # Get this from codegen.com/developer
            # base_url="https://codegen-sh-rest-api.modal.run",  # Optional - defaults to production
        )

        # Verify the agent was created successfully
        assert agent is not None
        assert agent.token == "YOUR_API_TOKEN"
        assert agent.org_id == 123

        # The API client should be initialized
        assert agent.api_client is not None
        assert agent.agents_api is not None

        # Current job should be None initially
        assert agent.current_job is None


def test_error_handling_no_token():
    """Test that proper errors are thrown when token is missing."""
    # Should raise TypeError when token is missing
    with pytest.raises(TypeError, match="missing 1 required positional argument: 'token'"):
        from codegen.agents.agent import Agent

        Agent()  # No token provided


def test_basic_initialization_variations():
    """Test different ways to initialize the Agent."""
    from codegen.agents.agent import Agent

    # With both token and org_id
    agent1 = Agent(token="test_token", org_id=123)
    assert agent1.token == "test_token"
    assert agent1.org_id == 123

    # With just token (will use default org_id)
    agent2 = Agent(token="test_token")
    assert agent2.token == "test_token"
    assert agent2.org_id == 1  # Default fallback

    # With custom base_url
    agent3 = Agent(token="test_token", org_id=123, base_url="https://custom.api.url")
    assert agent3.token == "test_token"
    assert agent3.org_id == 123
    assert agent3.api_client.configuration.host == "https://custom.api.url"


def test_import_statements():
    """Test that all the imports work as expected."""
    # Basic import
    from codegen.agents.agent import Agent

    assert Agent is not None

    # Import AgentTask too
    from codegen.agents.agent import Agent, AgentTask

    assert Agent is not None
    assert AgentTask is not None

    # Alternative import style
    import codegen.agents.agent

    assert hasattr(codegen.agents.agent, "Agent")
    assert hasattr(codegen.agents.agent, "AgentTask")
