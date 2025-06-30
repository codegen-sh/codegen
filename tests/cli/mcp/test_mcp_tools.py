"""Comprehensive tests for MCP tools with mocked API calls."""

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestMCPTools:
    """Test MCP tools functionality with mocked API calls."""

    @pytest.fixture
    def mcp_server_process(self):
        """Start an MCP server process for testing."""
        codegen_path = Path(__file__).parent.parent.parent.parent / "src"
        venv_python = Path(__file__).parent.parent.parent.parent / ".venv" / "bin" / "python"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(codegen_path)
        # Set mock API key for testing
        env["CODEGEN_API_KEY"] = "test-api-key"
        env["CODEGEN_API_BASE_URL"] = "https://api.test.codegen.com"

        process = subprocess.Popen(
            [str(venv_python), "-c", "from codegen.cli.cli import main; main(['mcp', '--transport', 'stdio'])"],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Give it time to start
        time.sleep(2)

        yield process

        # Cleanup
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def send_mcp_message(self, process, message):
        """Send an MCP message to the server and get response."""
        if process.stdin:
            process.stdin.write(json.dumps(message) + "\n")
            process.stdin.flush()

        # Give time to process
        time.sleep(0.5)

        # Read response (this is simplified - real MCP would need proper parsing)
        return None  # For now, we'll test that the server doesn't crash

    def test_mcp_initialize(self, mcp_server_process):
        """Test MCP server initialization."""
        init_message = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}

        self.send_mcp_message(mcp_server_process, init_message)

        # Server should still be running after initialization
        assert mcp_server_process.poll() is None

    def test_mcp_list_resources(self, mcp_server_process):
        """Test listing MCP resources."""
        # First initialize
        init_message = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
        self.send_mcp_message(mcp_server_process, init_message)

        # List resources
        list_resources_message = {"jsonrpc": "2.0", "id": 2, "method": "resources/list"}

        self.send_mcp_message(mcp_server_process, list_resources_message)

        # Server should still be running
        assert mcp_server_process.poll() is None

    def test_mcp_list_tools(self, mcp_server_process):
        """Test listing MCP tools."""
        # First initialize
        init_message = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
        self.send_mcp_message(mcp_server_process, init_message)

        # List tools
        list_tools_message = {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}

        self.send_mcp_message(mcp_server_process, list_tools_message)

        # Server should still be running
        assert mcp_server_process.poll() is None

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_generate_codemod_tool(self, mock_get_api_client):
        """Test the generate_codemod tool."""
        from codegen.cli.mcp.server import mcp

        # Get the generate_codemod tool function
        tools = mcp._tool_manager._tools
        assert "generate_codemod" in tools

        generate_codemod_tool = tools["generate_codemod"]

        # Test the tool function
        result = generate_codemod_tool.fn(  # type: ignore[attr-defined]
            title="test-codemod",
            task="Add logging to all functions",
            codebase_path="/path/to/codebase",
            ctx=None
        )
        

        assert "codegen create test-codemod" in result
        assert "Add logging to all functions" in result

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_create_agent_run_tool_success(self, mock_get_api_client):
        """Test the create_agent_run tool with successful API response."""
        from codegen.cli.mcp.server import mcp

        # Mock the API response
        mock_response = Mock()
        mock_response.id = 123
        mock_response.status = "running"
        mock_response.created_at = datetime.now(timezone.utc)
        mock_response.prompt = "Test prompt"
        mock_response.repo_name = "test-repo"
        mock_response.branch_name = "test-branch"

        mock_agents_api = Mock()
        mock_agents_api.create_agent_run_v1_organizations_org_id_agent_run_post.return_value = mock_response

        mock_get_api_client.return_value = (None, mock_agents_api, None, None)

        # Get the create_agent_run tool function
        tools = mcp._tool_manager._tools
        assert "create_agent_run" in tools

        create_agent_run_tool = tools["create_agent_run"]

        # Test the tool function
        result = create_agent_run_tool.fn(  # type: ignore[attr-defined]
            org_id=1,
            prompt="Test prompt",
            repo_name="test-repo",
            branch_name="test-branch",
            ctx=None
        )
        

        # Parse the JSON response
        response_data = json.loads(result)
        assert response_data["id"] == 123
        assert response_data["status"] == "running"
        assert response_data["prompt"] == "Test prompt"
        assert response_data["repo_name"] == "test-repo"
        assert response_data["branch_name"] == "test-branch"

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_create_agent_run_tool_error(self, mock_get_api_client):
        """Test the create_agent_run tool with API error."""
        from codegen.cli.mcp.server import mcp

        # Mock API to raise an exception
        mock_get_api_client.side_effect = Exception("API connection failed")

        # Get the create_agent_run tool function
        tools = mcp._tool_manager._tools
        assert "create_agent_run" in tools
        create_agent_run_tool = tools["create_agent_run"]

        create_agent_run_tool = tools["create_agent_run"]

        # Test the tool function
        result = create_agent_run_tool.fn(  # type: ignore[attr-defined]
            org_id=1,
            prompt="Test prompt",
            ctx=None
        )
        

        assert "Error creating agent run" in result
        assert "API connection failed" in result

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_get_agent_run_tool_success(self, mock_get_api_client):
        """Test the get_agent_run tool with successful API response."""
        from codegen.cli.mcp.server import mcp

        # Mock the API response
        mock_response = Mock()
        mock_response.id = 123
        mock_response.status = "completed"
        mock_response.created_at = datetime.now(timezone.utc)
        mock_response.updated_at = datetime.now(timezone.utc)
        mock_response.prompt = "Test prompt"
        mock_response.repo_name = "test-repo"
        mock_response.branch_name = "test-branch"
        mock_response.result = "Task completed successfully"

        mock_agents_api = Mock()
        mock_agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get.return_value = mock_response

        mock_get_api_client.return_value = (None, mock_agents_api, None, None)

        # Get the get_agent_run tool function
        tools = mcp._tool_manager._tools
        assert "get_agent_run" in tools
        get_agent_run_tool = tools["get_agent_run"]

        get_agent_run_tool = tools["get_agent_run"]

        # Test the tool function
        result = get_agent_run_tool.fn(  # type: ignore[attr-defined]
            org_id=1,
            agent_run_id=123,
            ctx=None
        )
        

        # Parse the JSON response
        response_data = json.loads(result)
        assert response_data["id"] == 123
        assert response_data["status"] == "completed"
        assert response_data["result"] == "Task completed successfully"

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_get_organizations_tool_success(self, mock_get_api_client):
        """Test the get_organizations tool with successful API response."""
        from datetime import datetime

        from codegen.cli.mcp.server import mcp

        # Mock organization objects
        mock_org1 = Mock()
        mock_org1.id = 1
        mock_org1.name = "Test Org 1"
        mock_org1.slug = "test-org-1"
        mock_org1.created_at = datetime.now(timezone.utc)

        mock_org2 = Mock()
        mock_org2.id = 2
        mock_org2.name = "Test Org 2"
        mock_org2.slug = "test-org-2"
        mock_org2.created_at = datetime.now(timezone.utc)

        # Mock the API response
        mock_response = Mock()
        mock_response.items = [mock_org1, mock_org2]
        mock_response.total = 2
        mock_response.page = 1
        mock_response.limit = 10

        mock_organizations_api = Mock()
        mock_organizations_api.get_organizations_v1_organizations_get.return_value = mock_response

        mock_get_api_client.return_value = (None, None, mock_organizations_api, None)

        # Get the get_organizations tool function
        tools = mcp._tool_manager._tools
        assert "get_organizations" in tools
        get_organizations_tool = tools["get_organizations"]

        get_organizations_tool = tools["get_organizations"]

        # Test the tool function
        result = get_organizations_tool.fn(  # type: ignore[attr-defined]
            page=1, limit=10, ctx=None)
        

        # Parse the JSON response
        response_data = json.loads(result)
        assert response_data["total"] == 2
        assert len(response_data["organizations"]) == 2
        assert response_data["organizations"][0]["name"] == "Test Org 1"
        assert response_data["organizations"][1]["name"] == "Test Org 2"

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_get_users_tool_success(self, mock_get_api_client):
        """Test the get_users tool with successful API response."""
        from datetime import datetime

        from codegen.cli.mcp.server import mcp

        # Mock user objects
        mock_user1 = Mock()
        mock_user1.id = 1
        mock_user1.email = "user1@test.com"
        mock_user1.name = "User One"
        mock_user1.created_at = datetime.now(timezone.utc)

        mock_user2 = Mock()
        mock_user2.id = 2
        mock_user2.email = "user2@test.com"
        mock_user2.name = "User Two"
        mock_user2.created_at = datetime.now(timezone.utc)

        # Mock the API response
        mock_response = Mock()
        mock_response.items = [mock_user1, mock_user2]
        mock_response.total = 2
        mock_response.page = 1
        mock_response.limit = 10

        mock_users_api = Mock()
        mock_users_api.get_users_v1_organizations_org_id_users_get.return_value = mock_response

        mock_get_api_client.return_value = (None, None, None, mock_users_api)

        # Get the get_users tool function
        tools = mcp._tool_manager._tools
        assert "get_users" in tools
        get_users_tool = tools["get_users"]

        get_users_tool = tools["get_users"]

        # Test the tool function
        result = get_users_tool.fn(  # type: ignore[attr-defined]
            org_id=1, page=1, limit=10, ctx=None)
        

        # Parse the JSON response
        response_data = json.loads(result)
        assert response_data["total"] == 2
        assert len(response_data["users"]) == 2
        assert response_data["users"][0]["email"] == "user1@test.com"
        assert response_data["users"][1]["email"] == "user2@test.com"

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_get_user_tool_success(self, mock_get_api_client):
        """Test the get_user tool with successful API response."""
        from datetime import datetime

        from codegen.cli.mcp.server import mcp

        # Mock the API response
        mock_response = Mock()
        mock_response.id = 1
        mock_response.email = "user@test.com"
        mock_response.name = "Test User"
        mock_response.created_at = datetime.now(timezone.utc)
        mock_response.updated_at = datetime.now(timezone.utc)

        mock_users_api = Mock()
        mock_users_api.get_user_v1_organizations_org_id_users_user_id_get.return_value = mock_response

        mock_get_api_client.return_value = (None, None, None, mock_users_api)

        # Get the get_user tool function
        tools = mcp._tool_manager._tools
        assert "get_user" in tools
        get_user_tool = tools["get_user"]

        get_user_tool = tools["get_user"]

        # Test the tool function
        result = get_user_tool.fn(  # type: ignore[attr-defined]
            org_id=1, user_id=1, ctx=None)
        

        # Parse the JSON response
        response_data = json.loads(result)
        assert response_data["id"] == 1
        assert response_data["email"] == "user@test.com"
        assert response_data["name"] == "Test User"

    def test_mcp_tools_registration(self):
        """Test that all expected tools are registered."""
        from codegen.cli.mcp.server import mcp

        tool_names = list(mcp._tool_manager._tools.keys())

        # Check that all expected tools are registered
        expected_tools = ["generate_codemod", "create_agent_run", "get_agent_run", "get_organizations", "get_users", "get_user"]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Tool {expected_tool} not found in registered tools"

    def test_mcp_resources_registration(self):
        """Test that all expected resources are registered."""
        from codegen.cli.mcp.server import mcp

        resource_uris = list(mcp._resource_manager._resources.keys())

        # Check that all expected resources are registered
        expected_resources = ["system://agent_prompt", "system://setup_instructions", "system://manifest"]

        for expected_resource in expected_resources:
            assert expected_resource in resource_uris, f"Resource {expected_resource} not found in registered resources"
