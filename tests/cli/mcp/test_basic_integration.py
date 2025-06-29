"""Basic integration tests for the MCP functionality."""

import os
import subprocess
from pathlib import Path


class TestMCPBasicIntegration:
    """Basic integration tests that don't require full server startup."""

    def test_mcp_command_help(self):
        """Test that the MCP command help works."""
        codegen_path = Path(__file__).parent.parent.parent.parent / "src"
        venv_python = Path(__file__).parent.parent.parent.parent / ".venv" / "bin" / "python"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(codegen_path)

        process = subprocess.Popen([str(venv_python), "-c", "from codegen.cli.cli import main; main(['mcp', '--help'])"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        stdout, stderr = process.communicate(timeout=10)

        assert process.returncode == 0
        assert "Start the Codegen MCP server" in stdout
        assert "--transport" in stdout
        assert "--host" in stdout
        assert "--port" in stdout

    def test_api_client_package_available(self):
        """Test that the API client package is available."""
        codegen_path = Path(__file__).parent.parent.parent.parent / "src"
        venv_python = Path(__file__).parent.parent.parent.parent / ".venv" / "bin" / "python"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(codegen_path)

        process = subprocess.Popen(
            [str(venv_python), "-c", "import codegen_api_client; print('API client package imported successfully')"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        stdout, stderr = process.communicate(timeout=10)

        assert process.returncode == 0
        assert "API client package imported successfully" in stdout
