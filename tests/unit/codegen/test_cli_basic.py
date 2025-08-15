"""Basic CLI tests to verify core functionality."""

import subprocess
import sys
from pathlib import Path


def test_cli_help_works():
    """Test that the CLI can show help without credentials."""
    # Run the CLI help command
    result = subprocess.run(
        [sys.executable, "-m", "codegen.cli.cli", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent.parent,  # Go to project root
    )

    # Should exit with code 0 (success)
    assert result.returncode == 0

    # Should contain basic help text
    assert "Commands" in result.stdout
    assert "init" in result.stdout
    assert "login" in result.stdout
    assert "profile" in result.stdout


def test_cli_version_works():
    """Test that the CLI can show version without credentials."""
    result = subprocess.run(
        [sys.executable, "-m", "codegen.cli.cli", "--version"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent.parent,  # Go to project root
    )

    # Should exit with code 0 (success)
    assert result.returncode == 0

    # Should show some version information
    assert len(result.stdout.strip()) > 0


def test_cli_command_help():
    """Test that individual commands can show help."""
    commands = ["init", "login", "logout", "profile", "config", "update"]

    for command in commands:
        result = subprocess.run(
            [sys.executable, "-m", "codegen.cli.cli", command, "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,  # Go to project root
        )

        # Should exit with code 0 (success) for help
        assert result.returncode == 0, f"Command '{command} --help' failed with code {result.returncode}"

        # Should contain usage information
        assert "Usage:" in result.stdout, f"Command '{command} --help' doesn't show usage"


def test_cli_imports_work():
    """Test that we can import the CLI module without errors."""
    # This test verifies that all imports in the CLI work
    try:
        from codegen.cli.cli import main

        assert main is not None

        # Test Agent import still works
        from codegen.agents.agent import Agent

        assert Agent is not None

    except ImportError as e:
        assert False, f"Failed to import CLI modules: {e}"
