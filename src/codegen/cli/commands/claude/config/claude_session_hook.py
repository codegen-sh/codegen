#!/usr/bin/env python3
"""Claude Code session hook script for API integration.

This script is called by Claude Code on SessionStart to:
1. Create a session in the backend API
2. Write session data to local file for tracking
"""

import json
import os
import sys
from pathlib import Path

# Add the codegen CLI to the path so we can import from it
script_dir = Path(__file__).parent
codegen_cli_dir = script_dir.parent.parent.parent
sys.path.insert(0, str(codegen_cli_dir))

try:
    from codegen.cli.commands.claude.claude_session_api import create_claude_session
    from codegen.cli.utils.org import resolve_org_id
except ImportError:
    # Fallback if imports fail - just write basic session data
    create_claude_session = None
    resolve_org_id = None


def main():
    """Main hook function called by Claude Code."""
    try:
        # Read hook input from stdin (Claude passes JSON data)
        input_data = {}
        try:
            if not sys.stdin.isatty():
                input_text = sys.stdin.read().strip()
                if input_text:
                    input_data = json.loads(input_text)
        except (json.JSONDecodeError, Exception):
            # If we can't read the input, continue with empty data
            pass

        # Get session ID from environment variable (set by main.py)
        session_id = os.environ.get("CODEGEN_CLAUDE_SESSION_ID")
        if not session_id:
            # Fallback: try to extract from input data
            session_id = input_data.get("session_id")
        
        if not session_id:
            # Generate a basic session ID if none available
            import uuid
            session_id = str(uuid.uuid4())

        # Get org_id from environment variable (set by main.py)
        org_id_str = os.environ.get("CODEGEN_CLAUDE_ORG_ID")
        org_id = None
        if org_id_str:
            try:
                org_id = int(org_id_str)
            except ValueError:
                pass

        # If we don't have org_id, try to resolve it
        if org_id is None and resolve_org_id:
            org_id = resolve_org_id(None)

        # Create session via API if available
        agent_run_id = None
        if create_claude_session and org_id:
            agent_run_id = create_claude_session(session_id, org_id)

        # Prepare session data
        session_data = {
            "session_id": session_id,
            "agent_run_id": agent_run_id,
            "org_id": org_id,
            "hook_event": input_data.get("hook_event_name"),
            "timestamp": input_data.get("timestamp")
        }

        # Output the session data (this gets written to the session file by the hook command)
        print(json.dumps(session_data, indent=2))

    except Exception as e:
        # If anything fails, at least output basic session data
        session_id = os.environ.get("CODEGEN_CLAUDE_SESSION_ID", "unknown")
        fallback_data = {
            "session_id": session_id,
            "error": str(e),
            "agent_run_id": None,
            "org_id": None
        }
        print(json.dumps(fallback_data, indent=2))


if __name__ == "__main__":
    main()