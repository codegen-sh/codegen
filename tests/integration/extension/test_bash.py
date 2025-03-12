"""Tests for bash command tools."""

import time

from codegen.extensions.tools.bash import run_bash_command


def test_run_bash_command() -> None:
    """Test running a bash command."""
    # Test a simple echo command
    result = run_bash_command("echo 'Hello, World!'")
    assert result["status"] == "success"
    assert "Hello, World!" in result["stdout"]
    assert result["stderr"] == ""

    # Test ls with combined flags
    result = run_bash_command("ls -la")
    assert result["status"] == "success"

    # Test ls with separate flags
    result = run_bash_command("ls -l -a")
    assert result["status"] == "success"

    # Test ls with long option
    result = run_bash_command("ls --color")
    assert result["status"] == "success"

    # Test grep with allowed flags
    result = run_bash_command("grep -n test *.py")
    assert result["status"] == "success"


def test_command_validation() -> None:
    """Test command validation."""
    # Test disallowed command
    result = run_bash_command("rm -rf /")
    assert result["status"] == "error"
    assert "dangerous pattern: remove command" in result["error"]

    # Test command with disallowed flags
    result = run_bash_command("ls --invalid-flag")
    assert result["status"] == "error"
    assert "Flags" in result["error"]
    assert "not allowed" in result["error"]

    # Test command with invalid combined flags
    result = run_bash_command("ls -laz")  # -z is not allowed
    assert result["status"] == "error"
    assert "Flags {'-z'} are not allowed" in result["error"]

    # Test dangerous patterns
    dangerous_commands = [
        "ls | grep test",  # Pipe
        "ls; rm file",  # Command chaining
        "ls > output.txt",  # Redirection
        "sudo ls",  # Sudo
        "ls ../parent",  # Parent directory
        "mv file1 file2",  # Move
        "cp file1 file2",  # Copy
        "chmod +x file",  # Change permissions
    ]

    expected_patterns = [
        "shell operators",  # For pipe
        "shell operators",  # For command chaining
        "output redirection",  # For redirection
        "sudo command",  # For sudo
        "parent directory traversal",  # For parent directory
        "move command",  # For move
        "copy command",  # For copy
        "chmod command",  # For chmod
    ]

    for cmd, pattern in zip(dangerous_commands, expected_patterns):
        result = run_bash_command(cmd)
        assert result["status"] == "error", f"Command should be blocked: {cmd}"
        assert f"dangerous pattern: {pattern}" in result["error"], f"Expected '{pattern}' in error for command: {cmd}"


def test_background_command() -> None:
    """Test background command execution."""
    # Test a safe background command
    result = run_bash_command("tail -f /dev/null", is_background=True)
    assert result["status"] == "success"
    assert "started in background with PID" in result["message"]

    # Clean up by finding and killing the background process
    pid = int(result["message"].split()[-1])
    run_bash_command(f"ps -p {pid} || true")  # Check if process exists
    time.sleep(1)  # Give process time to start/stop
