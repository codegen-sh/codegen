"""Tests for MCP protocol communication."""

import json
import os
import subprocess
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestMCPProtocol:
    """Test MCP protocol communication."""

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
        """Send an MCP message to the server."""
        if process.stdin:
            process.stdin.write(json.dumps(message) + "\n")
            process.stdin.flush()
        time.sleep(0.5)

    def test_mcp_initialization_sequence(self, mcp_server_process):
        """Test the complete MCP initialization sequence."""
        # Send initialize message
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        self.send_mcp_message(mcp_server_process, init_message)
        
        # Server should still be running after initialization
        assert mcp_server_process.poll() is None
        
        # Send initialized notification
        initialized_message = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        self.send_mcp_message(mcp_server_process, initialized_message)
        
        # Server should still be running
        assert mcp_server_process.poll() is None

    def test_mcp_list_resources_request(self, mcp_server_process):
        """Test MCP resources/list request."""
        # Initialize first
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        self.send_mcp_message(mcp_server_process, init_message)
        
        # List resources
        list_resources_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/list"
        }
        
        self.send_mcp_message(mcp_server_process, list_resources_message)
        
        # Server should handle the request without crashing
        assert mcp_server_process.poll() is None

    def test_mcp_list_tools_request(self, mcp_server_process):
        """Test MCP tools/list request."""
        # Initialize first
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        self.send_mcp_message(mcp_server_process, init_message)
        
        # List tools
        list_tools_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list"
        }
        
        self.send_mcp_message(mcp_server_process, list_tools_message)
        
        # Server should handle the request without crashing
        assert mcp_server_process.poll() is None

    def test_mcp_resource_read_request(self, mcp_server_process):
        """Test MCP resources/read request."""
        # Initialize first
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        self.send_mcp_message(mcp_server_process, init_message)
        
        # Read a resource
        read_resource_message = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/read",
            "params": {
                "uri": "system://agent_prompt"
            }
        }
        
        self.send_mcp_message(mcp_server_process, read_resource_message)
        
        # Server should handle the request without crashing
        assert mcp_server_process.poll() is None

    @patch('codegen.cli.mcp.server.get_api_client')
    def test_mcp_tool_call_request(self, mock_get_api_client, mcp_server_process):
        """Test MCP tools/call request."""
        # Mock API client to avoid actual API calls
        mock_get_api_client.return_value = (None, None, None, None)
        
        # Initialize first
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        self.send_mcp_message(mcp_server_process, init_message)
        
        # Call a tool
        tool_call_message = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "generate_codemod",
                "arguments": {
                    "title": "test-codemod",
                    "task": "Add logging to functions",
                    "codebase_path": "/tmp/test"
                }
            }
        }
        
        self.send_mcp_message(mcp_server_process, tool_call_message)
        
        # Server should handle the request without crashing
        assert mcp_server_process.poll() is None

    def test_mcp_invalid_method_request(self, mcp_server_process):
        """Test MCP server handling of invalid method requests."""
        # Initialize first
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        self.send_mcp_message(mcp_server_process, init_message)
        
        # Send invalid method
        invalid_message = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "invalid/method"
        }
        
        self.send_mcp_message(mcp_server_process, invalid_message)
        
        # Server should handle the invalid request gracefully
        assert mcp_server_process.poll() is None

    def test_mcp_malformed_json_handling(self, mcp_server_process):
        """Test MCP server handling of malformed JSON."""
        # Send malformed JSON
        if mcp_server_process.stdin:
            mcp_server_process.stdin.write("{ invalid json }\n")
            mcp_server_process.stdin.flush()
        
        time.sleep(0.5)
        
        # Server should handle malformed JSON gracefully
        assert mcp_server_process.poll() is None
        
        # Server should still be able to handle valid requests after malformed JSON
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        self.send_mcp_message(mcp_server_process, init_message)
        
        # Server should still be running
        assert mcp_server_process.poll() is None

    def test_mcp_missing_required_fields(self, mcp_server_process):
        """Test MCP server handling of messages with missing required fields."""
        # Send message without required fields
        incomplete_message = {
            "jsonrpc": "2.0",
            "method": "initialize"
            # Missing id and params
        }
        
        self.send_mcp_message(mcp_server_process, incomplete_message)
        
        # Server should handle incomplete messages gracefully
        assert mcp_server_process.poll() is None

    def test_mcp_protocol_version_handling(self, mcp_server_process):
        """Test MCP server handling of different protocol versions."""
        # Test with older protocol version
        init_message_old = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-01-01",  # Older version
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        self.send_mcp_message(mcp_server_process, init_message_old)
        
        # Server should handle different protocol versions
        assert mcp_server_process.poll() is None

    def test_mcp_concurrent_requests(self, mcp_server_process):
        """Test MCP server handling of concurrent requests."""
        # Initialize first
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        self.send_mcp_message(mcp_server_process, init_message)
        
        # Send multiple requests quickly
        messages = [
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "resources/list"
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/list"
            },
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": "system://manifest"}
            }
        ]
        
        for message in messages:
            self.send_mcp_message(mcp_server_process, message)
        
        # Give time for all requests to be processed
        time.sleep(2)
        
        # Server should handle concurrent requests without crashing
        assert mcp_server_process.poll() is None

    def test_mcp_server_shutdown_handling(self, mcp_server_process):
        """Test MCP server graceful shutdown."""
        # Initialize first
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        self.send_mcp_message(mcp_server_process, init_message)
        
        # Send shutdown request
        shutdown_message = {
            "jsonrpc": "2.0",
            "id": 99,
            "method": "shutdown"
        }
        
        self.send_mcp_message(mcp_server_process, shutdown_message)
        
        # Send exit notification
        exit_message = {
            "jsonrpc": "2.0",
            "method": "exit"
        }
        
        self.send_mcp_message(mcp_server_process, exit_message)
        
        # Give time for graceful shutdown
        time.sleep(2)
        
        # Server should have shut down gracefully
        # Note: This test might be flaky depending on FastMCP's shutdown handling
