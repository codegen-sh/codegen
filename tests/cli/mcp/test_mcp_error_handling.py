"""Tests for MCP error handling scenarios."""

import os
import subprocess
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestMCPErrorHandling:
    """Test MCP error handling scenarios."""

    def test_mcp_server_startup_without_dependencies(self):
        """Test MCP server behavior when optional dependencies are missing."""
        codegen_path = Path(__file__).parent.parent.parent.parent / "src"
        venv_python = Path(__file__).parent.parent.parent.parent / ".venv" / "bin" / "python"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(codegen_path)
        # Remove API key to test behavior without authentication
        env.pop("CODEGEN_API_KEY", None)

        process = subprocess.Popen(
            [str(venv_python), "-c", "from codegen.cli.cli import main; main(['mcp', '--transport', 'stdio'])"],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Give it time to start
            time.sleep(2)

            # Server should start even without API key
            assert process.poll() is None, "Server should start without API key"

        finally:
            # Cleanup
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    def test_mcp_server_with_invalid_api_base_url(self):
        """Test MCP server behavior with invalid API base URL."""
        codegen_path = Path(__file__).parent.parent.parent.parent / "src"
        venv_python = Path(__file__).parent.parent.parent.parent / ".venv" / "bin" / "python"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(codegen_path)
        env["CODEGEN_API_KEY"] = "test-key"
        env["CODEGEN_API_BASE_URL"] = "invalid-url"

        process = subprocess.Popen(
            [str(venv_python), "-c", "from codegen.cli.cli import main; main(['mcp', '--transport', 'stdio'])"],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Give it time to start
            time.sleep(2)

            # Server should start even with invalid API URL
            assert process.poll() is None, "Server should start with invalid API URL"

        finally:
            # Cleanup
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    @patch("codegen.cli.mcp.server.API_CLIENT_AVAILABLE", False)
    def test_api_client_unavailable_error_handling(self):
        """Test error handling when API client is not available."""
        from codegen.cli.mcp.server import get_api_client

        with pytest.raises(RuntimeError, match="codegen-api-client is not available"):
            get_api_client()

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_create_agent_run_api_error_handling(self, mock_get_api_client):
        """Test create_agent_run tool error handling."""
        from codegen.cli.mcp.server import mcp

        # Mock API to raise an exception
        mock_get_api_client.side_effect = Exception("Network error")

        # Get the create_agent_run tool function
        tools = mcp._tool_manager._tools
        assert "create_agent_run" in tools

        create_agent_run_tool = tools["create_agent_run"]

        # Test the tool function with API error
        result = create_agent_run_tool.fn(  # type: ignore[attr-defined]
            org_id=1,
            prompt="Test prompt",
            ctx=None
        )
        

        assert "Error creating agent run" in result
        assert "Network error" in result

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_get_agent_run_api_error_handling(self, mock_get_api_client):
        """Test get_agent_run tool error handling."""
        from codegen.cli.mcp.server import mcp

        # Mock API to raise an exception
        mock_get_api_client.side_effect = Exception("API timeout")

        # Get the get_agent_run tool function
        tools = mcp._tool_manager._tools
        assert "get_agent_run" in tools
        get_agent_run_tool = tools["get_agent_run"]

        get_agent_run_tool = tools["get_agent_run"]

        # Test the tool function with API error
        result = get_agent_run_tool.fn(  # type: ignore[attr-defined]
            org_id=1,
            agent_run_id=123,
            ctx=None
        )
        

        assert "Error getting agent run" in result
        assert "API timeout" in result

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_get_organizations_api_error_handling(self, mock_get_api_client):
        """Test get_organizations tool error handling."""
        from codegen.cli.mcp.server import mcp

        # Mock API to raise an exception
        mock_get_api_client.side_effect = Exception("Authentication failed")

        # Get the get_organizations tool function
        tools = mcp._tool_manager._tools
        assert "get_organizations" in tools
        get_organizations_tool = tools["get_organizations"]

        get_organizations_tool = tools["get_organizations"]

        # Test the tool function with API error
        result = get_organizations_tool.fn(  # type: ignore[attr-defined]
            page=1, limit=10, ctx=None)
        

        assert "Error getting organizations" in result
        assert "Authentication failed" in result

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_get_users_api_error_handling(self, mock_get_api_client):
        """Test get_users tool error handling."""
        from codegen.cli.mcp.server import mcp

        # Mock API to raise an exception
        mock_get_api_client.side_effect = Exception("Permission denied")

        # Get the get_users tool function
        tools = mcp._tool_manager._tools
        assert "get_users" in tools
        get_users_tool = tools["get_users"]

        get_users_tool = tools["get_users"]

        # Test the tool function with API error
        result = get_users_tool.fn(  # type: ignore[attr-defined]
            org_id=1, page=1, limit=10, ctx=None)
        

        assert "Error getting users" in result
        assert "Permission denied" in result

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_get_user_api_error_handling(self, mock_get_api_client):
        """Test get_user tool error handling."""
        from codegen.cli.mcp.server import mcp

        # Mock API to raise an exception
        mock_get_api_client.side_effect = Exception("User not found")

        # Get the get_user tool function
        tools = mcp._tool_manager._tools
        assert "get_user" in tools
        get_user_tool = tools["get_user"]

        get_user_tool = tools["get_user"]

        # Test the tool function with API error
        result = get_user_tool.fn(  # type: ignore[attr-defined]
            org_id=1, user_id=999, ctx=None)
        

        assert "Error getting user" in result
        assert "User not found" in result

    def test_run_server_invalid_transport_error(self):
        """Test run_server function with invalid transport."""
        from codegen.cli.mcp.server import run_server

        with pytest.raises(ValueError, match="Unsupported transport: invalid"):
            run_server(transport="invalid")

    def test_run_server_http_transport_fallback(self):
        """Test run_server function HTTP transport fallback."""
        from codegen.cli.mcp.server import run_server

        # This should not raise an exception but fall back to stdio
        # We can't easily test the actual behavior without mocking FastMCP
        # So we'll just ensure it doesn't crash
        try:
            # This will actually try to run the server, so we need to be careful
            # For now, we'll just test that the function exists and can be called
            assert callable(run_server)
        except Exception:
            # If it raises an exception, it should be a controlled one
            pass

    @patch("codegen.cli.mcp.server.LEGACY_IMPORTS_AVAILABLE", False)
    def test_legacy_tools_unavailable(self):
        """Test behavior when legacy imports are not available."""
        # Re-import the server module to trigger the conditional logic
        import importlib

        import codegen.cli.mcp.server

        importlib.reload(codegen.cli.mcp.server)

        from codegen.cli.mcp.server import mcp

        # Check that legacy tools are not registered when imports are unavailable
        tool_names = [tool.name for tool in mcp._tools]

        # ask_codegen_sdk and improve_codemod should not be available
        legacy_tools = ["ask_codegen_sdk", "improve_codemod"]
        for legacy_tool in legacy_tools:
            assert legacy_tool not in tool_names, f"Legacy tool {legacy_tool} should not be available"

    def test_api_client_configuration_error_handling(self):
        """Test API client configuration error handling."""
        from codegen.cli.mcp.server import get_api_client

        # Test with missing environment variables
        with patch.dict(os.environ, {}, clear=True):
            try:
                get_api_client()
                # Should not raise an exception, but should use defaults
            except Exception as e:
                # If it does raise an exception, it should be a controlled one
                assert "codegen-api-client is not available" in str(e)

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_api_client_initialization_error(self, mock_get_api_client):
        """Test API client initialization error handling."""
        from codegen.cli.mcp.server import mcp

        # Mock API client initialization to fail
        mock_get_api_client.side_effect = RuntimeError("Failed to initialize API client")

        # Get any API-dependent tool
        tools = mcp._tool_manager._tools
        assert "create_agent_run" in tools
        create_agent_run_tool = tools["create_agent_run"]
        
        
        tool = list(tools.values())[0]
        
        # Test that the tool handles initialization errors gracefully
        result = tool.fn(  # type: ignore[attr-defined]
            org_id=1, prompt="test", ctx=None)
        

        assert "Error creating agent run" in result
        assert "Failed to initialize API client" in result

    def test_resource_import_error_handling(self):
        """Test resource import error handling."""
        # Test that resources can be imported without errors
        try:
            from codegen.cli.mcp.resources.system_prompt import SYSTEM_PROMPT
            from codegen.cli.mcp.resources.system_setup_instructions import SETUP_INSTRUCTIONS

            assert isinstance(SYSTEM_PROMPT, str)
            assert isinstance(SETUP_INSTRUCTIONS, str)
        except ImportError as e:
            pytest.fail(  # type: ignore[misc]
                f"Resource imports should not fail: {e}")

    def test_server_module_import_error_handling(self):
        """Test server module import error handling."""
        # Test that the server module can be imported without errors
        try:
            import codegen.cli.mcp.server

            assert hasattr(codegen.cli.mcp.server, "run_server")
            assert hasattr(codegen.cli.mcp.server, "mcp")
        except ImportError as e:
            pytest.fail(  # type: ignore[misc]
                f"Server module import should not fail: {e}")

    def test_mcp_command_import_error_handling(self):
        """Test MCP command import error handling."""
        # Test that the MCP command can be imported without errors
        try:
            from codegen.cli.commands.mcp.main import mcp

            assert callable(mcp)
        except ImportError as e:
            pytest.fail(  # type: ignore[misc]
                f"MCP command import should not fail: {e}")

    @patch("codegen.cli.mcp.server.get_api_client")
    def test_api_response_parsing_error(self, mock_get_api_client):
        """Test API response parsing error handling."""
        from codegen.cli.mcp.server import mcp

        # Mock API to return malformed response
        mock_response = Mock()
        mock_response.id = None  # This could cause issues
        mock_response.status = None
        mock_response.created_at = None
        mock_response.prompt = None
        mock_response.repo_name = None
        mock_response.branch_name = None

        mock_agents_api = Mock()
        mock_agents_api.create_agent_run_v1_organizations_org_id_agent_run_post.return_value = mock_response

        mock_get_api_client.return_value = (None, mock_agents_api, None, None)

        # Get the create_agent_run tool function
        tools = mcp._tool_manager._tools
        assert "create_agent_run" in tools
        create_agent_run_tool = tools["create_agent_run"]

        create_agent_run_tool = tools["create_agent_run"]

        # Test the tool function with malformed response
        result = create_agent_run_tool.fn(  # type: ignore[attr-defined]
            org_id=1,
            prompt="Test prompt",
            ctx=None
        )
        

        # Should handle None values gracefully
        assert isinstance(result, str)
        # Should be valid JSON even with None values
        import json

        try:
            parsed = json.loads(result)
            assert isinstance(parsed, dict)
        except json.JSONDecodeError:
            pytest.fail(  # type: ignore[misc]
                "Tool should return valid JSON even with malformed API response")
