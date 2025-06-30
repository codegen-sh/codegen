"""Tests for MCP configuration scenarios."""

import os
import subprocess
import time
from pathlib import Path
from unittest.mock import patch


class TestMCPConfiguration:
    """Test MCP configuration scenarios."""

    def test_mcp_server_default_configuration(self):
        """Test MCP server with default configuration."""
        codegen_path = Path(__file__).parent.parent.parent.parent / "src"
        venv_python = Path(__file__).parent.parent.parent.parent / ".venv" / "bin" / "python"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(codegen_path)

        process = subprocess.Popen(
            [str(venv_python), "-c", "from codegen.cli.cli import main; main(['mcp'])"],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Give it time to start
            time.sleep(2)

            # Server should start with default configuration
            assert process.poll() is None, "Server should start with default configuration"

        finally:
            # Cleanup
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    def test_mcp_server_stdio_transport_explicit(self):
        """Test MCP server with explicit stdio transport."""
        codegen_path = Path(__file__).parent.parent.parent.parent / "src"
        venv_python = Path(__file__).parent.parent.parent.parent / ".venv" / "bin" / "python"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(codegen_path)

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

            # Server should start with stdio transport
            assert process.poll() is None, "Server should start with stdio transport"

        finally:
            # Cleanup
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    def test_mcp_server_http_transport_configuration(self):
        """Test MCP server with HTTP transport configuration."""
        codegen_path = Path(__file__).parent.parent.parent.parent / "src"
        venv_python = Path(__file__).parent.parent.parent.parent / ".venv" / "bin" / "python"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(codegen_path)

        # Test HTTP transport (should fall back to stdio for now)
        process = subprocess.Popen(
            [str(venv_python), "-c", "from codegen.cli.cli import main; main(['mcp', '--transport', 'http', '--host', '127.0.0.1', '--port', '8080'])"],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Give it time to start
            time.sleep(2)

            # Server should start (even if it falls back to stdio)
            assert process.poll() is None, "Server should start with HTTP transport configuration"

        finally:
            # Cleanup
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    def test_mcp_server_custom_host_port(self):
        """Test MCP server with custom host and port."""
        codegen_path = Path(__file__).parent.parent.parent.parent / "src"
        venv_python = Path(__file__).parent.parent.parent.parent / ".venv" / "bin" / "python"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(codegen_path)

        process = subprocess.Popen(
            [str(venv_python), "-c", "from codegen.cli.cli import main; main(['mcp', '--host', '0.0.0.0', '--port', '9000'])"],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Give it time to start
            time.sleep(2)

            # Server should start with custom host and port
            assert process.poll() is None, "Server should start with custom host and port"

        finally:
            # Cleanup
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    def test_mcp_server_environment_variables(self):
        """Test MCP server with various environment variables."""
        codegen_path = Path(__file__).parent.parent.parent.parent / "src"
        venv_python = Path(__file__).parent.parent.parent.parent / ".venv" / "bin" / "python"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(codegen_path)
        env["CODEGEN_API_KEY"] = "test-api-key-123"
        env["CODEGEN_API_BASE_URL"] = "https://custom.api.codegen.com"

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

            # Server should start with custom environment variables
            assert process.poll() is None, "Server should start with custom environment variables"

        finally:
            # Cleanup
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    def test_api_client_configuration_with_env_vars(self):
        """Test API client configuration with environment variables."""
        from codegen.cli.mcp.server import get_api_client

        with patch.dict(os.environ, {"CODEGEN_API_KEY": "test-key-456", "CODEGEN_API_BASE_URL": "https://test.api.codegen.com"}):
            try:
                api_client, agents_api, orgs_api, users_api = get_api_client()

                # Should return configured API clients
                assert api_client is not None
                assert agents_api is not None
                assert orgs_api is not None
                assert users_api is not None

                # Check that configuration was applied
                assert api_client.configuration.host == "https://test.api.codegen.com"

            except Exception as e:
                # If API client is not available, that's expected in test environment
                if "codegen-api-client is not available" not in str(e):
                    raise

    def test_api_client_configuration_defaults(self):
        """Test API client configuration with default values."""
        from codegen.cli.mcp.server import get_api_client

        # Clear environment variables to test defaults
        with patch.dict(os.environ, {}, clear=True):
            try:
                api_client, agents_api, orgs_api, users_api = get_api_client()

                # Should use default base URL
                assert api_client.configuration.host == "https://api.codegen.com"

            except Exception as e:
                # If API client is not available, that's expected in test environment
                if "codegen-api-client is not available" not in str(e):
                    raise

    def test_mcp_server_configuration_validation(self):
        """Test MCP server configuration validation."""
        # Test that the function has the expected parameters
        import inspect

        from codegen.cli.commands.mcp.main import mcp

        sig = inspect.signature(mcp)

        # Check that all expected parameters are present
        expected_params = ["host", "port", "transport"]
        for param in expected_params:
            assert param in sig.parameters, f"Parameter {param} not found in mcp function signature"

        # Check parameter defaults
        assert sig.parameters["host"].default == "localhost"
        assert sig.parameters["port"].default is None
        assert sig.parameters["transport"].default == "stdio"

    def test_transport_validation_in_command(self):
        """Test transport validation in the MCP command."""
        from codegen.cli.commands.mcp.main import mcp

        # This test would ideally call the function with invalid transport
        # but since it would try to actually run the server, we'll test the validation logic
        # by checking that the function exists and has the right structure

        # The function should exist and be callable
        assert callable(mcp)

        # The validation logic is in the function body, so we can't easily test it
        # without actually running the server, which we do in integration tests

    def test_server_configuration_object_creation(self):
        """Test server configuration object creation."""
        from codegen.cli.mcp.server import mcp

        # Check that the FastMCP server was created with correct configuration
        assert mcp.name == "codegen-mcp"
        assert mcp.instructions is not None
        assert "MCP server for the Codegen platform" in mcp.instructions

        # Check that tools and resources are registered
        assert len(mcp._tool_manager._tools) > 0, "Server should have tools registered"
        assert len(mcp._resource_manager._resources) > 0, "Server should have resources registered"

    def test_server_instructions_configuration(self):
        """Test server instructions configuration."""
        from codegen.cli.mcp.server import mcp

        instructions = mcp.instructions
        assert instructions is not None
        # Should contain key information about the server's purpose
        assert "MCP server" in instructions
        assert "Codegen" in instructions
        assert "tools" in instructions
        assert "resources" in instructions

    def test_global_api_client_singleton_behavior(self):
        """Test global API client singleton behavior."""
        # Reset global state
        import codegen.cli.mcp.server
        from codegen.cli.mcp.server import get_api_client

        codegen.cli.mcp.server._api_client = None
        codegen.cli.mcp.server._agents_api = None
        codegen.cli.mcp.server._organizations_api = None
        codegen.cli.mcp.server._users_api = None

        try:
            # First call should create the client
            client1 = get_api_client()

            # Second call should return the same client
            client2 = get_api_client()

            # Should be the same objects (singleton behavior)
            assert client1[0] is client2[0], "API client should be singleton"
            assert client1[1] is client2[1], "Agents API should be singleton"
            assert client1[2] is client2[2], "Organizations API should be singleton"
            assert client1[3] is client2[3], "Users API should be singleton"

        except Exception as e:
            # If API client is not available, that's expected in test environment
            if "codegen-api-client is not available" not in str(e):
                raise

    def test_conditional_tool_registration(self):
        """Test conditional tool registration based on available imports."""
        from codegen.cli.mcp.server import mcp, LEGACY_IMPORTS_AVAILABLE  # type: ignore[attr-defined]
        tool_names = list(mcp._tool_manager._tools.keys())

        if LEGACY_IMPORTS_AVAILABLE:
            # Legacy tools should be available
            assert "ask_codegen_sdk" in tool_names, "ask_codegen_sdk should be available when legacy imports are available"
            assert "improve_codemod" in tool_names, "improve_codemod should be available when legacy imports are available"
        else:
            # Legacy tools should not be available
            assert "ask_codegen_sdk" not in tool_names, "ask_codegen_sdk should not be available when legacy imports are unavailable"
            assert "improve_codemod" not in tool_names, "improve_codemod should not be available when legacy imports are unavailable"

        # Core tools should always be available
        core_tools = ["generate_codemod", "create_agent_run", "get_agent_run", "get_organizations", "get_users", "get_user"]
        for tool in core_tools:
            assert tool in tool_names, f"Core tool {tool} should always be available"

    def test_server_name_and_metadata(self):
        """Test server name and metadata configuration."""
        from codegen.cli.mcp.server import mcp

        # Check server metadata
        assert mcp.name == "codegen-mcp"

        # Check that the server has the expected structure
        assert hasattr(mcp, "_tool_manager")
        assert hasattr(mcp, "_resource_manager")
        assert hasattr(mcp, "instructions")

    def test_resource_configuration_consistency(self):
        """Test resource configuration consistency."""
        from codegen.cli.mcp.server import mcp

        # All resources should have URIs, descriptions, and MIME types
        resources = mcp._resource_manager._resources
        for uri, resource in resources.items():
            assert hasattr(resource, "description"), "Resource should have description"
            assert hasattr(resource, "mime_type"), "Resource should have MIME type"
            assert hasattr(resource, "fn"), "Resource should have function"

            # URI should be a string
            assert isinstance(uri, str), "Resource URI should be string"
            assert len(uri) > 0, "Resource URI should not be empty"

            # MIME type should be valid
            valid_mime_types = ["text/plain", "application/json", "text/html", "application/xml"]
            assert resource.mime_type in valid_mime_types, f"Resource MIME type should be valid: {resource.mime_type}"

    def test_tool_configuration_consistency(self):
        """Test tool configuration consistency."""
        from codegen.cli.mcp.server import mcp

        # All tools should have names and functions
        tools = mcp._tool_manager._tools
        for name, tool in tools.items():
            assert hasattr(tool, "fn"), "Tool should have function"

            # Name should be a string
            assert isinstance(name, str), "Tool name should be string"
            assert len(name) > 0, "Tool name should not be empty"

            # Function should be callable
            assert callable(tool.fn), "Tool function should be callable"
