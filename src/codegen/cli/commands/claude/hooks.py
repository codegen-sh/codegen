"""Claude hooks management for session tracking."""

import json
import os
import time
from pathlib import Path

from codegen.cli.commands.claude.quiet_console import console


CLAUDE_CONFIG_DIR = Path.home() / ".claude"
HOOKS_CONFIG_FILE = CLAUDE_CONFIG_DIR / "settings.json"
CODEGEN_DIR = Path.home() / ".codegen"
SESSION_FILE = CODEGEN_DIR / "claude-session.json"
SESSION_LOG_FILE = CODEGEN_DIR / "claude-sessions.log"


def ensure_claude_hook() -> bool:
    """Ensure the Claude hooks are properly set up for session tracking.

    This function will:
    1. Create necessary directories
    2. Create the hooks file if it doesn't exist
    3. Always overwrite any existing SessionStart and Stop hooks with our commands

    Returns:
        bool: True if hooks were set up successfully, False otherwise
    """
    try:
        # Create .codegen directory if it doesn't exist
        CODEGEN_DIR.mkdir(exist_ok=True)

        # Clean up old session file if it exists
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()

        # Ensure Claude config directory exists
        CLAUDE_CONFIG_DIR.mkdir(exist_ok=True)

        # Build the shell command that will create session via API and write session data
        start_hook_script_path = Path(__file__).parent / "config" / "claude_session_hook.py"
        start_hook_command = f"mkdir -p {CODEGEN_DIR} && python3 {start_hook_script_path} > {SESSION_FILE}"

        # Build the stop hook command to mark session COMPLETE
        stop_hook_script_path = Path(__file__).parent / "config" / "claude_session_stop_hook.py"
        stop_hook_command = f"python3 {stop_hook_script_path}"

        # Build the user prompt submit hook to set status ACTIVE
        active_hook_script_path = Path(__file__).parent / "config" / "claude_session_active_hook.py"
        active_hook_command = f"python3 {active_hook_script_path}"

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
        if "Stop" not in hooks_config["hooks"]:
            hooks_config["hooks"]["Stop"] = []
        if "UserPromptSubmit" not in hooks_config["hooks"]:
            hooks_config["hooks"]["UserPromptSubmit"] = []

        # Get existing hooks
        session_start_hooks = hooks_config["hooks"]["SessionStart"]
        stop_hooks = hooks_config["hooks"]["Stop"]
        active_hooks = hooks_config["hooks"]["UserPromptSubmit"]

        # Check if we're replacing existing hooks
        replaced_existing = (len(session_start_hooks) > 0) or (len(stop_hooks) > 0) or (len(active_hooks) > 0)

        # Create the new hook structures (following Claude's format)
        new_start_hook_group = {"hooks": [{"type": "command", "command": start_hook_command}]}
        new_stop_hook_group = {"hooks": [{"type": "command", "command": stop_hook_command}]}
        new_active_hook_group = {"hooks": [{"type": "command", "command": active_hook_command}]}

        # Replace all existing hooks with our single hook per event
        hooks_config["hooks"]["SessionStart"] = [new_start_hook_group]
        hooks_config["hooks"]["Stop"] = [new_stop_hook_group]
        hooks_config["hooks"]["UserPromptSubmit"] = [new_active_hook_group]

        # Write updated config with nice formatting
        with open(HOOKS_CONFIG_FILE, "w") as f:
            json.dump(hooks_config, f, indent=2)
            f.write("\n")  # Add trailing newline for cleaner file

        if replaced_existing:
            console.print("✅ Replaced existing Claude hooks (SessionStart, Stop)", style="green")
        else:
            console.print("✅ Registered new Claude hooks (SessionStart, Stop)", style="green")
        console.print(f"   Start hook: {start_hook_command[:50]}...", style="dim")
        console.print(f"   Stop hook:  {stop_hook_command}", style="dim")
        console.print(f"   Active hook:{' ' if len('Active hook:')<1 else ''} {active_hook_command}", style="dim")

        # Verify the hook was written correctly
        try:
            with open(HOOKS_CONFIG_FILE) as f:
                verify_config = json.load(f)

            # Check that our hooks are in the config
            found_start_hook = False
            for hook_group in verify_config.get("hooks", {}).get("SessionStart", []):
                for hook in hook_group.get("hooks", []):
                    if SESSION_FILE.name in hook.get("command", ""):
                        found_start_hook = True
                        break
            found_stop_hook = False
            for hook_group in verify_config.get("hooks", {}).get("Stop", []):
                for hook in hook_group.get("hooks", []):
                    if "claude_session_stop_hook.py" in hook.get("command", ""):
                        found_stop_hook = True
                        break
            found_active_hook = False
            for hook_group in verify_config.get("hooks", {}).get("UserPromptSubmit", []):
                for hook in hook_group.get("hooks", []):
                    if "claude_session_active_hook.py" in hook.get("command", ""):
                        found_active_hook = True
                        break

            if found_start_hook and found_stop_hook and found_active_hook:
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


def cleanup_claude_hook() -> None:
    """Remove the Codegen Claude hooks from the hooks configuration."""
    try:
        if not HOOKS_CONFIG_FILE.exists():
            return

        with open(HOOKS_CONFIG_FILE) as f:
            hooks_config = json.load(f)

        if "hooks" not in hooks_config:
            return

        session_start_hooks = hooks_config["hooks"].get("SessionStart", [])
        stop_hooks = hooks_config["hooks"].get("Stop", [])
        active_hooks = hooks_config["hooks"].get("UserPromptSubmit", [])
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

        # Update SessionStart hooks if we removed something
        if modified:
            hooks_config["hooks"]["SessionStart"] = new_session_hooks

        # Now also remove Stop hook referencing our stop script
        new_stop_hooks = []
        for hook_group in stop_hooks:
            contains_stop = False
            for hook in hook_group.get("hooks", []):
                if hook.get("command") and "claude_session_stop_hook.py" in hook.get("command", ""):
                    contains_stop = True
                    break
            if not contains_stop:
                new_stop_hooks.append(hook_group)
            else:
                modified = True

        if stop_hooks is not None:
            hooks_config["hooks"]["Stop"] = new_stop_hooks

        # Remove UserPromptSubmit hook referencing our active script
        new_active_hooks = []
        for hook_group in active_hooks:
            contains_active = False
            for hook in hook_group.get("hooks", []):
                if hook.get("command") and "claude_session_active_hook.py" in hook.get("command", ""):
                    contains_active = True
                    break
            if not contains_active:
                new_active_hooks.append(hook_group)
            else:
                modified = True

        if active_hooks is not None:
            hooks_config["hooks"]["UserPromptSubmit"] = new_active_hooks

        # Write updated config if anything changed
        if modified:
            with open(HOOKS_CONFIG_FILE, "w") as f:
                json.dump(hooks_config, f, indent=2)
                f.write("\n")  # Add trailing newline
            console.print("✅ Removed Claude hooks", style="dim")

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
