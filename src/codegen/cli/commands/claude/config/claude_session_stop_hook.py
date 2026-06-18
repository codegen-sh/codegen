#!/usr/bin/env python3
"""Claude Code stop hook script for API integration.

This script is called by Claude Code on Stop to:
1. Read the session context (session_id, org_id)
2. Send a COMPLETE status to the backend API
"""

import json
import os
import sys
from pathlib import Path

# Add the codegen CLI to the path so we can import from it
script_dir = Path(__file__).parent
codegen_cli_dir = script_dir.parent.parent.parent.parent
sys.path.insert(0, str(codegen_cli_dir))

try:
    from codegen.cli.commands.claude.claude_session_api import update_claude_session_status
except ImportError:
    update_claude_session_status = None


def read_session_file() -> dict:
    """Read session data written by the SessionStart hook, if available."""
    session_path = Path.home() / ".codegen" / "claude-session.json"
    if not session_path.exists():
        return {}
    try:
        with open(session_path) as f:
            return json.load(f)
    except Exception:
        return {}


def main():
    try:
        # Prefer environment variables set by the CLI wrapper
        session_id = os.environ.get("CODEGEN_CLAUDE_SESSION_ID")
        org_id = os.environ.get("CODEGEN_CLAUDE_ORG_ID")

        # Fallback to reading the session file
        if not session_id or not org_id:
            data = read_session_file()
            session_id = session_id or data.get("session_id")
            org_id = org_id or data.get("org_id")

        # Normalize org_id type
        if isinstance(org_id, str):
            try:
                org_id = int(org_id)
            except ValueError:
                org_id = None

        if update_claude_session_status and session_id:
            update_claude_session_status(session_id, "COMPLETE", org_id)

        # Stop hooks must stay silent on stdout unless they emit a valid decision object.
        # This hook only performs a backend side effect, so it should not print anything.
        return 0

    except Exception as e:
        # Ensure hook doesn't fail Claude if something goes wrong.
        # Log to stderr only so stdout remains a valid empty hook response.
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
