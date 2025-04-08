from unittest.mock import MagicMock, patch

import pytest

from codegen.agents.agent import Agent, AgentTask
from codegen.agents.client.openapi_client.api.agents_api import AgentsApi
from codegen.agents.client.openapi_client.configuration import Configuration
from codegen.agents.client.openapi_client.models.agent_run_response import AgentRunResponse
from codegen.agents.constants import CODEGEN_BASE_API_URL


class TestAgentTask:
    @pytest.fixture
    def agent_run_response(self):
        """Create a mock AgentRunResponse"""
        mock_response = MagicMock(spec=AgentRunResponse)
        mock_response.id = "123"  # Keep as string as this is likely the format from API
        mock_response.status = "running"
        mock_response.result = None
        mock_response.web_url = "https://example.com/run/123"
        return mock_response

    @pytest.fixture
    def api_client(self):
        """Create a mock ApiClient"""
        mock_client = MagicMock()  # Remove spec to allow dynamic attributes
        mock_client.configuration = MagicMock()  # Create configuration attribute
        mock_client.configuration.access_token = "test-token"
        return mock_client

    @pytest.fixture
    def mock_agents_api(self):
        """Create a proper mock for the AgentsApi"""
        # Create a proper mock with a get method
        mock_api = MagicMock(spec=AgentsApi)
        return mock_api

    @pytest.fixture
    def agent_task(self, agent_run_response, api_client, mock_agents_api):
        """Create an AgentTask instance with mock dependencies"""
        # Patch the AgentsApi constructor to return our mock
        with patch("codegen.agents.agent.AgentsApi", return_value=mock_agents_api):
            task = AgentTask(agent_run_response, api_client, org_id=42)
            return task

    def test_init(self, agent_task, agent_run_response, api_client, mock_agents_api):
        """Test initialization of AgentTask"""
        assert agent_task.id == "123"
        assert agent_task.org_id == 42
        assert agent_task.status == "running"
        assert agent_task.result is None
        assert agent_task.web_url == "https://example.com/run/123"
        assert agent_task._api_client == api_client
        assert agent_task._agents_api == mock_agents_api

    def test_refresh_without_id(self, agent_task, mock_agents_api):
        """Test refresh method when job ID is None"""
        agent_task.id = None
        # Should return early without making API call
        agent_task.refresh()
        mock_agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get.assert_not_called()

    def test_refresh_with_id(self, agent_task, mock_agents_api):
        """Test refresh method updates job status"""
        # Setup mock API response
        mock_updated_response = {"status": "completed", "result": {"output": "Success!"}}
        mock_agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get.return_value = mock_updated_response

        # Call refresh
        agent_task.refresh()

        # Verify API was called with correct params
        mock_agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get.assert_called_once_with(
            agent_run_id=123,  # Use string ID as stored in agent_task.id
            org_id=42,
            authorization="Bearer test-token",
        )

        # Verify status was updated
        assert agent_task.status == "completed"
        assert agent_task.result == {"output": "Success!"}

    def test_refresh_with_dict_response(self, agent_task, mock_agents_api):
        """Test refresh method when API returns dict instead of object"""
        # Setup mock API response as dict
        mock_updated_response = {"status": "failed", "result": {"error": "Something went wrong"}}
        mock_agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get.return_value = mock_updated_response

        # Call refresh
        agent_task.refresh()

        # Verify status was updated
        assert agent_task.status == "failed"
        assert agent_task.result == {"error": "Something went wrong"}


class TestAgent:
    @pytest.fixture
    def mock_api_client(self):
        """Create a mock ApiClient"""
        with patch("codegen.agents.agent.ApiClient") as mock_client_class:
            mock_client = MagicMock()  # Remove spec to allow dynamic attributes
            mock_client.configuration = MagicMock()  # Create configuration attribute
            mock_client.configuration.access_token = "test-token"
            mock_client_class.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def mock_agents_api(self):
        """Create a mock AgentsApi"""
        with patch("codegen.agents.agent.AgentsApi") as mock_api_class:
            mock_api = MagicMock(spec=AgentsApi)
            mock_api_class.return_value = mock_api
            yield mock_api

    @pytest.fixture
    def agent(self, mock_api_client, mock_agents_api):
        """Create an Agent instance with mock dependencies"""
        with patch.object(Configuration, "__init__", return_value=None) as mock_config:
            agent = Agent(token="test-token", org_id=42)
            # Verify config initialization
            mock_config.assert_called_once_with(host=CODEGEN_BASE_API_URL, access_token="test-token")
            return agent

    def test_init_with_explicit_org_id(self, mock_api_client, mock_agents_api):
        """Test initialization with explicitly provided org_id"""
        with patch.object(Configuration, "__init__", return_value=None):
            agent = Agent(token="test-token", org_id=42)
            assert agent.token == "test-token"
            assert agent.org_id == 42
            assert agent.api_client == mock_api_client
            assert agent.agents_api == mock_agents_api
            assert agent.current_job is None

    def test_init_with_default_org_id(self, mock_api_client, mock_agents_api):
        """Test initialization with default org_id"""
        with patch.object(Configuration, "__init__", return_value=None):
            with patch.dict("os.environ", {"CODEGEN_ORG_ID": "99"}):
                agent = Agent(token="test-token")
                assert agent.org_id == 99

    def test_init_with_custom_base_url(self, mock_api_client):
        """Test initialization with custom base URL"""
        with patch.object(Configuration, "__init__", return_value=None) as mock_config:
            custom_url = "https://custom-api.example.com"
            agent = Agent(token="test-token", org_id=42, base_url=custom_url)
            mock_config.assert_called_once_with(host=custom_url, access_token="test-token")

    def test_run(self, agent, mock_agents_api):
        """Test run method creates and returns job"""
        # Setup mock API response
        mock_run_response = MagicMock(spec=AgentRunResponse)
        mock_run_response.id = "123"
        mock_run_response.status = "running"
        mock_run_response.result = None
        mock_run_response.web_url = "https://example.com/run/123"
        mock_agents_api.create_agent_run_v1_organizations_org_id_agent_run_post.return_value = mock_run_response

        # Call run
        job = agent.run("Test prompt")

        # Verify API call
        mock_agents_api.create_agent_run_v1_organizations_org_id_agent_run_post.assert_called_once()
        call_args = mock_agents_api.create_agent_run_v1_organizations_org_id_agent_run_post.call_args
        assert call_args[1]["org_id"] == 42
        assert call_args[1]["authorization"] == "Bearer test-token"
        assert call_args[1]["_headers"] == {"Content-Type": "application/json"}
        assert call_args[1]["create_agent_run_input"].prompt == "Test prompt"

        # Verify job
        assert isinstance(job, AgentTask)
        assert job.id == "123"
        assert job.status == "running"
        assert agent.current_job == job

    def test_get_status_with_no_job(self, agent):
        """Test get_status when no job has been run"""
        assert agent.get_status() is None

    def test_get_status_with_job(self, agent):
        """Test get_status returns current job status"""
        # Setup mock job
        mock_job = MagicMock(spec=AgentTask)
        mock_job.id = "123"
        mock_job.status = "completed"
        mock_job.result = {"output": "Success!"}
        mock_job.web_url = "https://example.com/run/123"

        agent.current_job = mock_job

        # Call get_status
        status = agent.get_status()

        # Verify job was refreshed
        mock_job.refresh.assert_called_once()

        # Verify status
        assert status == {"id": "123", "status": "completed", "result": {"output": "Success!"}, "web_url": "https://example.com/run/123"}


# Integration-like tests
class TestAgentIntegration:
    @pytest.fixture
    def mock_response(self):
        """Create a mock response for API calls"""
        mock_response = MagicMock()  # Remove spec=AgentRunResponse
        mock_response.id = 987
        mock_response.status = "running"
        mock_response.result = None
        mock_response.web_url = "https://example.com/run/987"
        return mock_response

    @pytest.fixture
    def mock_updated_response(self):
        """Create a mock updated response for API calls"""
        mock_updated = {"id": 987, "status": "completed", "result": {"output": "Task completed successfully"}, "web_url": "https://example.com/run/987"}

        return mock_updated

    def test_full_workflow(self, mock_response, mock_updated_response):
        """Test a complete agent workflow from initialization to status check"""
        with (
            patch("codegen.agents.agent.ApiClient") as mock_api_client_class,
            patch("codegen.agents.agent.AgentsApi") as mock_agents_api_class,
            patch.object(Configuration, "__init__", return_value=None),
        ):
            # Setup mocks
            mock_api_client = MagicMock()  # Remove spec to allow dynamic attributes
            mock_api_client.configuration = MagicMock()  # Create configuration attribute
            mock_api_client.configuration.access_token = "test-token"
            mock_api_client_class.return_value = mock_api_client

            # Setup agents API mock
            mock_agents_api = MagicMock(spec=AgentsApi)
            mock_agents_api.create_agent_run_v1_organizations_org_id_agent_run_post.return_value = mock_response
            mock_agents_api_class.return_value = mock_agents_api

            # We're patching the same class for both the Agent and AgentTask
            mock_inner_agents_api = mock_agents_api
            mock_inner_agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get.return_value = mock_updated_response

            # Initialize agent
            agent = Agent(token="test-token", org_id=123)

            # Run agent
            job = agent.run("Execute this instruction")

            # Verify job properties
            assert job.id == 987
            assert job.status == "running"
            assert job.result is None

            # Check status
            status = agent.get_status()

            # Verify API calls
            mock_agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get.assert_called_once_with(agent_run_id=987, org_id=123, authorization="Bearer test-token")

            # Verify status
            assert isinstance(status, dict)
            assert status["id"] == 987
            assert status["status"] == "completed"
            assert status["result"] == {"output": "Task completed successfully"}
            assert status["web_url"] == "https://example.com/run/987"

    def test_exception_handling(self):
        """Test handling of API exceptions during agent run"""
        with patch("codegen.agents.agent.ApiClient"), patch("codegen.agents.agent.AgentsApi") as mock_agents_api_class, patch.object(Configuration, "__init__", return_value=None):
            # Setup API to raise exception
            mock_agents_api = MagicMock(spec=AgentsApi)
            mock_agents_api.create_agent_run_v1_organizations_org_id_agent_run_post.side_effect = Exception("API Error")
            mock_agents_api_class.return_value = mock_agents_api

            # Initialize agent
            agent = Agent(token="test-token", org_id=123)

            # Run agent and expect exception
            with pytest.raises(Exception) as excinfo:
                agent.run("Execute this instruction")

            assert "API Error" in str(excinfo.value)
