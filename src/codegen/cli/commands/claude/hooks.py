"""Claude hooks management for session tracking."""

import json
import os
import time
from pathlib import Path

from rich.console import Console

console = Console()

CLAUDE_CONFIG_DIR = Path.home() / ".claude"
HOOKS_CONFIG_FILE = CLAUDE_CONFIG_DIR / "settings.json"
CODEGEN_DIR = Path.home() / ".codegen"
SESSION_FILE = CODEGEN_DIR / "claude-session.json"
SESSION_LOG_FILE = CODEGEN_DIR / "claude-sessions.log"


def ensure_claude_hook() -> bool:
    """Ensure the Claude hook is properly set up for session tracking.

    This function will:
    1. Create necessary directories
    2. Create the hooks file if it doesn't exist
    3. Always overwrite any existing startup hooks with our command

    Returns:
        bool: True if hook was set up successfully, False otherwise
    """
    try:
        # Create .codegen directory if it doesn't exist
        CODEGEN_DIR.mkdir(exist_ok=True)

        # Clean up old session file if it exists
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()

        # Ensure Claude config directory exists
        CLAUDE_CONFIG_DIR.mkdir(exist_ok=True)

        # Build the shell command that will write the session data
        # Simple approach: just write to the session file
        hook_command = f"mkdir -p {CODEGEN_DIR} && cat > {SESSION_FILE}"

        # Read existing hooks config or create new one
        hooks_config = {}
        if HOOKS_CONFIG_FILE.exists():
            try:
                with open(HOOKS_CONFIG_FILE) as f:
                    content = f.read().strip()
                    if content:
                        hooks_config = json.loads(content)
                    else:
                        console.print("⚠️  Hooks file is empty, creating new configuration", style="yellow")
            except (OSError, json.JSONDecodeError) as e:
                console.print(f"⚠️  Could not read existing hooks file: {e}, creating new one", style="yellow")

        # Ensure proper structure exists
        if "hooks" not in hooks_config:
            hooks_config["hooks"] = {}
        if "SessionStart" not in hooks_config["hooks"]:
            hooks_config["hooks"]["SessionStart"] = []

        # Get existing session start hooks
        session_start_hooks = hooks_config["hooks"]["SessionStart"]

        # Check if we're replacing an existing hook
        replaced_existing = len(session_start_hooks) > 0

        # Create the new hook structure (following Claude's format)
        new_hook_group = {"hooks": [{"type": "command", "command": hook_command}]}

        # Replace all existing SessionStart hooks with our single hook
        hooks_config["hooks"]["SessionStart"] = [new_hook_group]

        # Write updated config with nice formatting
        with open(HOOKS_CONFIG_FILE, "w") as f:
            json.dump(hooks_config, f, indent=2)
            f.write("\n")  # Add trailing newline for cleaner file

        if replaced_existing:
            console.print("✅ Replaced existing Claude startup hook", style="green")
        else:
            console.print("✅ Registered new Claude startup hook", style="green")
        console.print(f"   Hook command: {hook_command[:50]}...", style="dim")

        # Verify the hook was written correctly
        try:
            with open(HOOKS_CONFIG_FILE) as f:
                verify_config = json.load(f)

            # Check that our hook is in the config
            found_our_hook = False
            for hook_group in verify_config.get("hooks", {}).get("SessionStart", []):
                for hook in hook_group.get("hooks", []):
                    if SESSION_FILE.name in hook.get("command", ""):
                        found_our_hook = True
                        break

            if found_our_hook:
                console.print("✅ Hook configuration verified", style="dim")
            else:
                console.print("⚠️  Hook was written but verification failed", style="yellow")
                return False

        except Exception as e:
            console.print(f"⚠️  Could not verify hook configuration: {e}", style="yellow")
            return False

        return True

    except Exception as e:
        console.print(f"❌ Failed to set up Claude hook: {e}", style="red")
        return False


def wait_for_session_id(timeout: float = 10.0) -> str | None:
    """Wait for Claude to write the session ID to disk.

    Args:
        timeout: Maximum time to wait in seconds

    Returns:
        Session ID if found, None otherwise
    """
    start_time = time.time()
    checked_count = 0

    # Log where we're looking
    if checked_count == 0:
        console.print(f"📁 Looking for session file at: {SESSION_FILE}", style="dim")

    while time.time() - start_time < timeout:
        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE) as f:
                    content = f.read()
                    if content.strip():
                        data = json.loads(content)
                        session_id = data.get("session_id")
                        if session_id:
                            console.print(f"🔍 Found session ID: {session_id}", style="dim")
                            return session_id
            except (OSError, json.JSONDecodeError) as e:
                # File might be in the process of being written
                if checked_count % 10 == 0:  # Log every second
                    console.print(f"⏳ Waiting for valid session data... ({e.__class__.__name__})", style="dim")

        checked_count += 1
        time.sleep(0.1)  # Check every 100ms

    console.print(f"⏱️  Timeout waiting for session ID after {timeout}s", style="yellow")
    return None


def cleanup_claude_hook() -> None:
    """Remove the Codegen Claude hook from the hooks configuration."""
    try:
        if not HOOKS_CONFIG_FILE.exists():
            return

        with open(HOOKS_CONFIG_FILE) as f:
            hooks_config = json.load(f)

        if "hooks" not in hooks_config or "SessionStart" not in hooks_config["hooks"]:
            return

        session_start_hooks = hooks_config["hooks"]["SessionStart"]
        modified = False

        # Filter out any hook groups that contain our command
        new_session_hooks = []
        for hook_group in session_start_hooks:
            # Check if this group contains our hook
            contains_our_hook = False
            for hook in hook_group.get("hooks", []):
                if hook.get("command") and "claude-session.json" in hook.get("command", ""):
                    contains_our_hook = True
                    modified = True
                    break

            # Keep hook groups that don't contain our hook
            if not contains_our_hook:
                new_session_hooks.append(hook_group)

        # Update the hooks only if we removed something
        if modified:
            hooks_config["hooks"]["SessionStart"] = new_session_hooks

            # Write updated config
            with open(HOOKS_CONFIG_FILE, "w") as f:
                json.dump(hooks_config, f, indent=2)
                f.write("\n")  # Add trailing newline
            console.print("✅ Removed Claude hook", style="dim")

        # Clean up session files
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()

    except Exception as e:
        console.print(f"⚠️  Error cleaning up hook: {e}", style="yellow")


def get_codegen_url(session_id: str) -> str:
    """Get the Codegen URL for a session ID."""
    # You can customize this based on your environment
    base_url = os.environ.get("CODEGEN_BASE_URL", "https://codegen.com")
    # Use the format: codegen.com/claude-code/{session-id}
    return f"{base_url}/claude-code/{session_id}"
