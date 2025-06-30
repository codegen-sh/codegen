"""Tests for the MCP CLI command."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import typer
from typer.testing import CliRunner

from codegen.cli.commands.mcp.main import mcp


class TestMCPCommand:
    """Test cases for the MCP command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_mcp_help_works(self):
        """Test that the MCP command can show help."""
        result = subprocess.run(
            [sys.executable, "-m", "codegen.cli.cli", "mcp", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,  # Go to project root
        )

        # Should exit with code 0 (success)
        assert result.returncode == 0

        # Should contain help text
        assert "Start the Codegen MCP server" in result.stdout
        assert "--port" in result.stdout
        assert "--transport" in result.stdout
        assert "--verbose" in result.stdout

    @patch('codegen.cli.commands.mcp.main.subprocess.run')
    @patch('codegen.cli.commands.mcp.main.rich.print')
    def test_mcp_default_options(self, mock_print, mock_subprocess):
        """Test MCP command with default options."""
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Create a typer app for testing
        app = typer.Typer()
        app.command()(mcp)
        
        result = self.runner.invoke(app, [])
        
        # Should exit successfully
        assert result.exit_code == 0
        
        # Check that subprocess was called correctly
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        
        # Verify the command structure
        assert call_args[0][0][0] == sys.executable  # Python executable
        assert "server.py" in call_args[0][0][1]  # MCP server path
        
        # Verify environment variables
        env = call_args[1]['env']
        assert env['CODEGEN_MCP_TRANSPORT'] == 'stdio'  # Default transport
        assert 'CODEGEN_MCP_VERBOSE' not in env  # Verbose not set by default
        assert 'CODEGEN_MCP_PORT' not in env  # Port not set by default

    @patch('codegen.cli.commands.mcp.main.subprocess.run')
    @patch('codegen.cli.commands.mcp.main.rich.print')
    def test_mcp_with_verbose_option(self, mock_print, mock_subprocess):
        """Test MCP command with verbose option."""
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Create a typer app for testing
        app = typer.Typer()
        app.command()(mcp)
        
        result = self.runner.invoke(app, ["--verbose"])
        
        # Should exit successfully
        assert result.exit_code == 0
        
        # Verify environment variables
        env = mock_subprocess.call_args[1]['env']
        assert env['CODEGEN_MCP_VERBOSE'] == '1'

    @patch('codegen.cli.commands.mcp.main.subprocess.run')
    @patch('codegen.cli.commands.mcp.main.rich.print')
    def test_mcp_with_port_option(self, mock_print, mock_subprocess):
        """Test MCP command with port option."""
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Create a typer app for testing
        app = typer.Typer()
        app.command()(mcp)
        
        result = self.runner.invoke(app, ["--port", "8080"])
        
        # Should exit successfully
        assert result.exit_code == 0
        
        # Verify environment variables
        env = mock_subprocess.call_args[1]['env']
        assert env['CODEGEN_MCP_PORT'] == '8080'

    @patch('codegen.cli.commands.mcp.main.subprocess.run')
    @patch('codegen.cli.commands.mcp.main.rich.print')
    def test_mcp_with_transport_option(self, mock_print, mock_subprocess):
        """Test MCP command with transport option."""
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Create a typer app for testing
        app = typer.Typer()
        app.command()(mcp)
        
        result = self.runner.invoke(app, ["--transport", "http"])
        
        # Should exit successfully
        assert result.exit_code == 0
        
        # Verify environment variables
        env = mock_subprocess.call_args[1]['env']
        assert env['CODEGEN_MCP_TRANSPORT'] == 'http'

    @patch('codegen.cli.commands.mcp.main.subprocess.run')
    @patch('codegen.cli.commands.mcp.main.rich.print')
    def test_mcp_with_all_options(self, mock_print, mock_subprocess):
        """Test MCP command with all options."""
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Create a typer app for testing
        app = typer.Typer()
        app.command()(mcp)
        
        result = self.runner.invoke(app, [
            "--verbose", 
            "--port", "9000", 
            "--transport", "sse"
        ])
        
        # Should exit successfully
        assert result.exit_code == 0
        
        # Verify environment variables
        env = mock_subprocess.call_args[1]['env']
        assert env['CODEGEN_MCP_VERBOSE'] == '1'
        assert env['CODEGEN_MCP_PORT'] == '9000'
        assert env['CODEGEN_MCP_TRANSPORT'] == 'sse'

    @patch('codegen.cli.commands.mcp.main.Path.exists')
    @patch('codegen.cli.commands.mcp.main.rich.print')
    def test_mcp_server_not_found(self, mock_print, mock_exists):
        """Test MCP command when server file is not found."""
        # Mock server file not existing
        mock_exists.return_value = False

        # Create a typer app for testing
        app = typer.Typer()
        app.command()(mcp)
        
        result = self.runner.invoke(app, [])
        
        # Should exit with error code 1
        assert result.exit_code == 1
        
        # Should print error message
        mock_print.assert_called_with("[red]Error:[/red] MCP server not found. Please ensure Codegen is properly installed.")

    @patch('codegen.cli.commands.mcp.main.subprocess.run')
    @patch('codegen.cli.commands.mcp.main.rich.print')
    def test_mcp_subprocess_failure(self, mock_print, mock_subprocess):
        """Test MCP command when subprocess fails."""
        # Mock failed subprocess run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result

        # Create a typer app for testing
        app = typer.Typer()
        app.command()(mcp)
        
        result = self.runner.invoke(app, [])
        
        # Should exit with error code 1
        assert result.exit_code == 1
        
        # Should print error message
        mock_print.assert_any_call("[red]Error:[/red] MCP server exited with code 1")

    @patch('codegen.cli.commands.mcp.main.subprocess.run')
    @patch('codegen.cli.commands.mcp.main.rich.print')
    def test_mcp_keyboard_interrupt(self, mock_print, mock_subprocess):
        """Test MCP command handling keyboard interrupt."""
        # Mock KeyboardInterrupt
        mock_subprocess.side_effect = KeyboardInterrupt()

        # Create a typer app for testing
        app = typer.Typer()
        app.command()(mcp)
        
        result = self.runner.invoke(app, [])
        
        # Should exit with code 0 (graceful shutdown)
        assert result.exit_code == 0
        
        # Should print shutdown message
        mock_print.assert_any_call("\n[yellow]MCP server stopped.[/yellow]")

    @patch('codegen.cli.commands.mcp.main.subprocess.run')
    @patch('codegen.cli.commands.mcp.main.rich.print')
    def test_mcp_general_exception(self, mock_print, mock_subprocess):
        """Test MCP command handling general exception."""
        # Mock general exception
        mock_subprocess.side_effect = Exception("Test error")

        # Create a typer app for testing
        app = typer.Typer()
        app.command()(mcp)
        
        result = self.runner.invoke(app, [])
        
        # Should exit with error code 1
        assert result.exit_code == 1
        
        # Should print error message
        mock_print.assert_any_call("[red]Error starting MCP server:[/red] Test error")

    @patch('codegen.cli.commands.mcp.main.subprocess.run')
    @patch('codegen.cli.commands.mcp.main.rich.print')
    def test_mcp_prints_startup_info(self, mock_print, mock_subprocess):
        """Test that MCP command prints startup information."""
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Create a typer app for testing
        app = typer.Typer()
        app.command()(mcp)
        
        result = self.runner.invoke(app, ["--port", "8080", "--transport", "http"])
        
        # Should exit successfully
        assert result.exit_code == 0
        
        # Verify startup messages were printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        
        # Check for startup messages
        assert any("[green]Starting Codegen MCP server...[/green]" in call for call in print_calls)
        assert any("Transport: http" in call for call in print_calls)
        assert any("Port: 8080" in call for call in print_calls)

    @patch('codegen.cli.commands.mcp.main.subprocess.run')
    @patch('codegen.cli.commands.mcp.main.rich.print')
    def test_mcp_no_port_message_when_not_specified(self, mock_print, mock_subprocess):
        """Test that port message is not printed when port is not specified."""
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Create a typer app for testing
        app = typer.Typer()
        app.command()(mcp)
        
        result = self.runner.invoke(app, [])
        
        # Should exit successfully
        assert result.exit_code == 0
        
        # Verify port message was not printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert not any("Port:" in call for call in print_calls)
