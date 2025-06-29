"""Server startup tests for MCP functionality."""

import os
import subprocess
import time
from pathlib import Path


class TestMCPServerStartup:
    """Tests that actually start the MCP server briefly."""

    def test_server_startup_stdio(self):
        """Test that the server can start with stdio transport."""
        codegen_path = Path(__file__).parent.parent.parent.parent / "src"
        venv_python = Path(__file__).parent.parent.parent.parent / ".venv" / "bin" / "python"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(codegen_path)

        # Start the server process
        process = subprocess.Popen(
            [str(venv_python), "-c", "from codegen.cli.cli import main; main(['mcp', '--transport', 'stdio'])"],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Give it a moment to start
            time.sleep(2)

            # Check if process is still running (not crashed)
            assert process.poll() is None, "Server process should still be running"

            # Send a simple message to test stdio communication
            # This is a basic MCP initialization message
            init_message = (
                '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}\n'
            )

            if process.stdin:
                process.stdin.write(init_message)
                process.stdin.flush()

            # Give it a moment to process
            time.sleep(1)

            # Process should still be running
            assert process.poll() is None, "Server should handle initialization without crashing"

        finally:
            # Clean up: terminate the process
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    def test_server_startup_invalid_transport(self):
        """Test that the server fails gracefully with invalid transport."""
        codegen_path = Path(__file__).parent.parent.parent.parent / "src"
        venv_python = Path(__file__).parent.parent.parent.parent / ".venv" / "bin" / "python"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(codegen_path)

        process = subprocess.Popen(
            [str(venv_python), "-c", "from codegen.cli.cli import main; main(['mcp', '--transport', 'invalid'])"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        stdout, stderr = process.communicate(timeout=10)

        # Should exit with error code
        assert process.returncode != 0

        # Should contain error message about invalid transport
        error_output = stdout + stderr
        assert "invalid" in error_output.lower() or "transport" in error_output.lower()

    def test_server_help_contains_expected_info(self):
        """Test that server help contains expected information."""
        codegen_path = Path(__file__).parent.parent.parent.parent / "src"
        venv_python = Path(__file__).parent.parent.parent.parent / ".venv" / "bin" / "python"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(codegen_path)

        process = subprocess.Popen([str(venv_python), "-c", "from codegen.cli.cli import main; main(['mcp', '--help'])"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        stdout, stderr = process.communicate(timeout=10)

        assert process.returncode == 0

        # Check that help contains expected information
        help_text = stdout.lower()
        assert "mcp server" in help_text
        assert "codegen" in help_text
        assert "--host" in help_text
        assert "--port" in help_text
        assert "--transport" in help_text
        assert "stdio" in help_text
        assert "http" in help_text
