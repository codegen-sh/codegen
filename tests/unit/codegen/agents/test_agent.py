"""Unit tests for the Agent class."""

import os
from unittest.mock import MagicMock, patch

import pytest

from codegen.agents.agent import Agent, AgentTask


class TestAgentImport:
    """Test that we can properly import the Agent class."""

    def test_can_import_agent(self):
        """Test that we can import Agent from codegen.agents.agent."""
        from codegen.agents.agent import Agent

        assert Agent is not None

    def test_can_import_agent_task(self):
        """Test that we can import AgentTask from codegen.agents.agent."""
        from codegen.agents.agent import AgentTask

        assert AgentTask is not None


class TestAgentInitialization:
    """Test Agent initialization and configuration."""

    def test_agent_init_with_token_and_org_id(self):
        """Test Agent initialization with token and org_id."""
        agent = Agent(token="test_token", org_id=123)

        assert agent.token == "test_token"
        assert agent.org_id == 123
        assert agent.current_job is None
        assert agent.api_client is not None
        assert agent.agents_api is not None

    def test_agent_init_with_token_only(self):
        """Test Agent initialization with token only (should use default org_id)."""
        with patch.dict(os.environ, {"CODEGEN_ORG_ID": "456"}, clear=False):
            agent = Agent(token="test_token")

            assert agent.token == "test_token"
            assert agent.org_id == 456  # From environment
            assert agent.current_job is None

    def test_agent_init_with_token_no_env_org_id(self):
        """Test Agent initialization with token only and no env org_id (should use default)."""
        with patch.dict(os.environ, {}, clear=True):
            agent = Agent(token="test_token")

            assert agent.token == "test_token"
            assert agent.org_id == 1  # Default fallback
            assert agent.current_job is None

    def test_agent_init_with_custom_base_url(self):
        """Test Agent initialization with custom base_url."""
        custom_url = "https://custom.api.url"
        agent = Agent(token="test_token", org_id=123, base_url=custom_url)

        assert agent.token == "test_token"
        assert agent.org_id == 123
        # The API client should be configured with the custom URL
        assert agent.api_client.configuration.host == custom_url


class TestAgentErrorHandling:
    """Test error handling in Agent class."""

    def test_agent_init_requires_token(self):
        """Test that Agent initialization requires a token parameter."""
        # This should raise a TypeError because token is a required parameter
        with pytest.raises(TypeError, match="missing 1 required positional argument: 'token'"):
            Agent()  # Missing required token parameter

    def test_agent_init_with_none_token(self):
        """Test Agent initialization with None token."""
        # The Agent class should accept None but the API calls would fail
        agent = Agent(token=None, org_id=123)
        assert agent.token is None
        assert agent.org_id == 123

    def test_agent_init_with_empty_token(self):
        """Test Agent initialization with empty string token."""
        agent = Agent(token="", org_id=123)
        assert agent.token == ""
        assert agent.org_id == 123


class TestAgentTaskCreation:
    """Test AgentTask creation and functionality."""

    def test_agent_task_init(self):
        """Test AgentTask initialization."""
        # Mock the AgentRunResponse
        mock_response = MagicMock()
        mock_response.id = "task_123"
        mock_response.status = "pending"
        mock_response.result = None
        mock_response.web_url = "https://example.com/task/123"

        # Mock API client
        mock_api_client = MagicMock()

        # Create AgentTask
        task = AgentTask(mock_response, mock_api_client, org_id=123)

        assert task.id == "task_123"
        assert task.org_id == 123
        assert task.status == "pending"
        assert task.result is None
        assert task.web_url == "https://example.com/task/123"
        assert task._api_client == mock_api_client


class TestAgentUsageExample:
    """Test the example usage pattern from the user's requirements."""

    @patch("codegen.agents.agent.AgentsApi")
    @patch("codegen.agents.agent.ApiClient")
    @patch("codegen.agents.agent.Configuration")
    def test_basic_usage_pattern(self, mock_config, mock_api_client, mock_agents_api):
        """Test the basic usage pattern that should work."""
        # Setup mocks
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        mock_api_client_instance = MagicMock()
        mock_api_client.return_value = mock_api_client_instance

        mock_agents_api_instance = MagicMock()
        mock_agents_api.return_value = mock_agents_api_instance

        # Mock the API response
        mock_response = MagicMock()
        mock_response.id = "task_456"
        mock_response.status = "pending"
        mock_response.result = None
        mock_response.web_url = "https://example.com/task/456"

        mock_agents_api_instance.create_agent_run_v1_organizations_org_id_agent_run_post.return_value = mock_response

        # Test the usage pattern
        from codegen.agents.agent import Agent

        # Initialize the Agent
        agent = Agent(
            org_id=123,  # Pass as int
            token="test_api_token",
        )

        assert agent is not None
        assert agent.token == "test_api_token"
        assert agent.org_id == 123

        # Run an agent with a prompt
        task = agent.run(prompt="Implement a new feature to sort users by last login.")

        assert task is not None
        assert task.id == "task_456"
        assert task.status == "pending"

        # Verify the API was called correctly
        mock_agents_api_instance.create_agent_run_v1_organizations_org_id_agent_run_post.assert_called_once()
        call_args = mock_agents_api_instance.create_agent_run_v1_organizations_org_id_agent_run_post.call_args
        assert call_args[1]["org_id"] == 123
        assert call_args[1]["authorization"] == "Bearer test_api_token"


class TestAgentStatusCheck:
    """Test agent status checking functionality."""

    def test_get_status_no_current_job(self):
        """Test get_status when no job has been run."""
        agent = Agent(token="test_token", org_id=123)
        status = agent.get_status()
        assert status is None

    @patch("codegen.agents.agent.AgentsApi")
    @patch("codegen.agents.agent.ApiClient")
    @patch("codegen.agents.agent.Configuration")
    def test_get_status_with_current_job(self, mock_config, mock_api_client, mock_agents_api):
        """Test get_status when there is a current job."""
        # Setup mocks
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        mock_api_client_instance = MagicMock()
        mock_api_client.return_value = mock_api_client_instance

        mock_agents_api_instance = MagicMock()
        mock_agents_api.return_value = mock_agents_api_instance

        # Create agent
        agent = Agent(token="test_token", org_id=123)

        # Mock the task
        mock_task = MagicMock()
        mock_task.id = "task_789"
        mock_task.status = "completed"
        mock_task.result = "Task completed successfully"
        mock_task.web_url = "https://example.com/task/789"

        agent.current_job = mock_task

        # Test get_status
        status = agent.get_status()

        assert status is not None
        assert status["id"] == "task_789"
        assert status["status"] == "completed"
        assert status["result"] == "Task completed successfully"
        assert status["web_url"] == "https://example.com/task/789"

        # Verify refresh was called
        mock_task.refresh.assert_called_once()
