"""Tests for the MCP CLI command."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import typer

from codegen.cli.commands.mcp.main import mcp


class TestMCPCommand:
    """Test cases for the MCP command."""

    def test_mcp_command_basic_call(self):
        """Test that MCP command can be called with basic parameters."""
        with patch('subprocess.run') as mock_run, \
             patch('rich.print') as mock_print:
            
            # Mock successful subprocess run
            mock_run.return_value = Mock(returncode=0)
            
            # Call the function with explicit default values
            mcp(port=None, transport="stdio", verbose=False)
            
            # Verify subprocess was called
            mock_run.assert_called_once()
            
            # Verify the call arguments
            call_args = mock_run.call_args
            assert call_args[0][0][0] == sys.executable  # First arg should be python executable
            assert str(call_args[0][0][1]).endswith('server.py')  # Second arg should be server.py path
            
            # Verify environment variables
            env = call_args[1]['env']
            assert 'CODEGEN_MCP_TRANSPORT' in env
            assert env['CODEGEN_MCP_TRANSPORT'] == 'stdio'

    def test_mcp_command_with_port(self):
        """Test MCP command with port option."""
        with patch('subprocess.run') as mock_run, \
             patch('rich.print') as mock_print:
            
            mock_run.return_value = Mock(returncode=0)
            
            # Call with port
            mcp(port=8080, transport="stdio", verbose=False)
            
            # Verify environment variables include port
            call_args = mock_run.call_args
            env = call_args[1]['env']
            assert 'CODEGEN_MCP_PORT' in env
            assert env['CODEGEN_MCP_PORT'] == '8080'

    def test_mcp_command_with_transport(self):
        """Test MCP command with different transport types."""
        transports = ['stdio', 'http', 'sse']
        
        for transport in transports:
            with patch('subprocess.run') as mock_run, \
                 patch('rich.print') as mock_print:
                
                mock_run.return_value = Mock(returncode=0)
                
                # Call with transport
                mcp(port=None, transport=transport, verbose=False)
                
                # Verify environment variables include transport
                call_args = mock_run.call_args
                env = call_args[1]['env']
                assert env['CODEGEN_MCP_TRANSPORT'] == transport

    def test_mcp_command_with_verbose(self):
        """Test MCP command with verbose option."""
        with patch('subprocess.run') as mock_run, \
             patch('rich.print') as mock_print:
            
            mock_run.return_value = Mock(returncode=0)
            
            # Call with verbose
            mcp(port=None, transport="stdio", verbose=True)
            
            # Verify environment variables include verbose flag
            call_args = mock_run.call_args
            env = call_args[1]['env']
            assert 'CODEGEN_MCP_VERBOSE' in env
            assert env['CODEGEN_MCP_VERBOSE'] == '1'

    def test_mcp_command_all_options(self):
        """Test MCP command with all options."""
        with patch('subprocess.run') as mock_run, \
             patch('rich.print') as mock_print:
            
            mock_run.return_value = Mock(returncode=0)
            
            # Call with all options
            mcp(port=9000, transport='http', verbose=True)
            
            # Verify all environment variables are set
            call_args = mock_run.call_args
            env = call_args[1]['env']
            assert env['CODEGEN_MCP_PORT'] == '9000'
            assert env['CODEGEN_MCP_TRANSPORT'] == 'http'
            assert env['CODEGEN_MCP_VERBOSE'] == '1'

    def test_mcp_server_not_found(self):
        """Test behavior when MCP server file is not found."""
        with patch('pathlib.Path.exists', return_value=False), \
             patch('rich.print') as mock_print, \
             pytest.raises(typer.Exit) as exc_info:
            
            mcp(port=None, transport="stdio", verbose=False)
            
            # Should exit with code 1
            assert exc_info.value.exit_code == 1
            
            # Should print error message
            mock_print.assert_called_with("[red]Error:[/red] MCP server not found. Please ensure Codegen is properly installed.")

    def test_mcp_subprocess_failure(self):
        """Test behavior when subprocess fails."""
        with patch('subprocess.run') as mock_run, \
             patch('rich.print') as mock_print, \
             pytest.raises(typer.Exit) as exc_info:
            
            # Mock subprocess failure
            mock_run.return_value = Mock(returncode=1)
            
            mcp(port=None, transport="stdio", verbose=False)
            
            # Should exit with the same code as subprocess
            assert exc_info.value.exit_code == 1
            
            # Should print error message
            error_calls = [call for call in mock_print.call_args_list if 'Error:' in str(call)]
            assert len(error_calls) > 0

    def test_mcp_keyboard_interrupt(self):
        """Test behavior when user interrupts with Ctrl+C."""
        with patch('subprocess.run') as mock_run, \
             patch('rich.print') as mock_print, \
             pytest.raises(typer.Exit) as exc_info:
            
            # Mock KeyboardInterrupt
            mock_run.side_effect = KeyboardInterrupt()
            
            mcp(port=None, transport="stdio", verbose=False)
            
            # Should exit with code 0
            assert exc_info.value.exit_code == 0
            
            # Should print stop message
            stop_calls = [call for call in mock_print.call_args_list if 'stopped' in str(call)]
            assert len(stop_calls) > 0

    def test_mcp_general_exception(self):
        """Test behavior when general exception occurs."""
        with patch('subprocess.run') as mock_run, \
             patch('rich.print') as mock_print, \
             pytest.raises(typer.Exit) as exc_info:
            
            # Mock general exception
            mock_run.side_effect = Exception("Test error")
            
            mcp(port=None, transport="stdio", verbose=False)
            
            # Should exit with code 1
            assert exc_info.value.exit_code == 1
            
            # Should print error message
            error_calls = [call for call in mock_print.call_args_list if 'Error starting MCP server:' in str(call)]
            assert len(error_calls) > 0

    def test_mcp_server_path_resolution(self):
        """Test that MCP server path is resolved correctly."""
        with patch('subprocess.run') as mock_run, \
             patch('rich.print') as mock_print:
            
            mock_run.return_value = Mock(returncode=0)
            
            mcp(port=None, transport="stdio", verbose=False)
            
            # Verify the server path is constructed correctly
            call_args = mock_run.call_args
            server_path = call_args[0][0][1]
            assert server_path.endswith('server.py')
            assert 'mcp' in server_path

    def test_mcp_environment_preservation(self):
        """Test that existing environment variables are preserved."""
        original_env = {'EXISTING_VAR': 'existing_value'}
        
        with patch('os.environ.copy', return_value=original_env.copy()) as mock_env_copy, \
             patch('subprocess.run') as mock_run, \
             patch('rich.print') as mock_print:
            
            mock_run.return_value = Mock(returncode=0)
            
            mcp(port=None, transport="stdio", verbose=True)
            
            # Verify original environment is copied
            mock_env_copy.assert_called_once()
            
            # Verify both original and new env vars are present
            call_args = mock_run.call_args
            env = call_args[1]['env']
            assert 'EXISTING_VAR' in env
            assert env['EXISTING_VAR'] == 'existing_value'
            assert 'CODEGEN_MCP_VERBOSE' in env

    def test_mcp_rich_output_messages(self):
        """Test that appropriate rich messages are printed."""
        with patch('subprocess.run') as mock_run, \
             patch('rich.print') as mock_print:
            
            mock_run.return_value = Mock(returncode=0)
            
            mcp(port=8080, transport='http', verbose=True)
            
            # Check that startup messages are printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            
            # Should contain startup message
            startup_found = any('Starting Codegen MCP server' in call for call in print_calls)
            assert startup_found
            
            # Should contain transport info
            transport_found = any('Transport: http' in call for call in print_calls)
            assert transport_found
            
            # Should contain port info
            port_found = any('Port: 8080' in call for call in print_calls)
            assert port_found

    def test_mcp_working_directory(self):
        """Test that subprocess runs in correct working directory."""
        with patch('subprocess.run') as mock_run, \
             patch('rich.print') as mock_print:
            
            mock_run.return_value = Mock(returncode=0)
            
            mcp(port=None, transport="stdio", verbose=False)
            
            # Verify working directory is set to server parent directory
            call_args = mock_run.call_args
            cwd = call_args[1]['cwd']
            assert cwd is not None
            # The cwd should be the parent directory of server.py (i.e., the mcp directory)
            assert str(cwd).endswith('mcp')
