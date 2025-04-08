"""Simplified test for the Agent class focusing on public interfaces.
This approach avoids the complexity of mocking internal implementations.
"""

from unittest.mock import MagicMock, patch

import pytest

from codegen.agents.agent import Agent
from codegen.agents.constants import CODEGEN_BASE_API_URL


class TestAgent:
    """Test the public interface of the Agent class."""

    @pytest.fixture
    def mock_agents_api(self):
        """Create a mock for the AgentsApi."""
        mock_api = MagicMock()
        # Set up response for create_agent_run
        mock_create_response = MagicMock()
        mock_create_response.id = 123
        mock_create_response.status = "running"
        mock_create_response.result = None
        mock_create_response.web_url = "https://example.com/agent/123"

        # Set up response for get_agent_run
        mock_get_response = MagicMock()
        mock_get_response.status = "completed"
        mock_get_response.result = {"output": "Task completed successfully"}

        # Configure the mock methods
        mock_api.create_agent_run_v1_organizations_org_id_agent_run_post.return_value = mock_create_response
        mock_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get.return_value = mock_get_response

        return mock_api

    @pytest.fixture
    def agent(self, mock_agents_api):
        """Create an Agent with mocked dependencies."""
        with patch("codegen.agents.agent.ApiClient"), patch("codegen.agents.agent.AgentsApi", return_value=mock_agents_api), patch("codegen.agents.agent.Configuration"):
            agent = Agent(token="test-token", org_id=42)
            return agent

    def test_initialization(self):
        """Test Agent initialization with different parameters."""
        # Test with explicit org_id
        with patch("codegen.agents.agent.ApiClient"), patch("codegen.agents.agent.AgentsApi"), patch("codegen.agents.agent.Configuration") as mock_config:
            agent = Agent(token="test-token", org_id=42)
            assert agent.token == "test-token"
            assert agent.org_id == 42
            assert agent.current_job is None

            # Verify Configuration was initialized correctly
            mock_config.assert_called_once_with(host=CODEGEN_BASE_API_URL, access_token="test-token")

            # Test with env var for org_id
            with patch.dict("os.environ", {"CODEGEN_ORG_ID": "99"}):
                agent = Agent(token="test-token")
                assert agent.org_id == 99

            # Test with custom base URL
            custom_url = "https://custom-api.example.com"
            agent = Agent(token="test-token", org_id=42, base_url=custom_url)
            mock_config.assert_called_with(host=custom_url, access_token="test-token")

    def test_run_agent(self, agent, mock_agents_api):
        """Test running an agent with a prompt."""
        # Run the agent
        job = agent.run("Test prompt")

        # Verify the API was called correctly
        mock_agents_api.create_agent_run_v1_organizations_org_id_agent_run_post.assert_called_once()
        call_args = mock_agents_api.create_agent_run_v1_organizations_org_id_agent_run_post.call_args[1]
        assert call_args["org_id"] == 42
        assert call_args["authorization"] == "Bearer test-token"
        assert call_args["_headers"] == {"Content-Type": "application/json"}
        assert call_args["create_agent_run_input"].prompt == "Test prompt"

        # Verify the job properties
        assert job.id == 123
        assert job.status == "running"
        assert job.result is None
        assert job.web_url == "https://example.com/agent/123"
        assert agent.current_job == job

    def test_get_status_no_job(self, agent):
        """Test get_status when no job has been run."""
        assert agent.get_status() is None

    def test_exception_handling(self):
        """Test handling of API exceptions during agent run."""
        with patch("codegen.agents.agent.ApiClient"), patch("codegen.agents.agent.AgentsApi") as mock_agents_api_class, patch("codegen.agents.agent.Configuration"):
            # Setup API to raise exception
            mock_agents_api = MagicMock()
            mock_agents_api.create_agent_run_v1_organizations_org_id_agent_run_post.side_effect = Exception("API Error")
            mock_agents_api_class.return_value = mock_agents_api

            # Initialize agent
            agent = Agent(token="test-token", org_id=123)

            # Run agent and expect exception
            with pytest.raises(Exception) as excinfo:
                agent.run("Execute this instruction")

            assert "API Error" in str(excinfo.value)
