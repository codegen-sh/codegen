"""Utility functions for Claude CLI integration."""

import os
from shutil import which


def resolve_claude_path() -> str | None:
    """Resolve the path to the Claude Code CLI.

    Tries PATH first, then common local install locations created by `claude /migrate`.

    Returns:
        Path to the claude executable if found, None otherwise.
    """
    # 1) Check system PATH first
    path_from_path = which("claude")
    if path_from_path:
        return path_from_path

    # 2) Check common local install locations
    home = os.path.expanduser("~")
    candidates = [
        # Local install created by `claude /migrate`
        os.path.join(home, ".claude", "local", "claude"),
        os.path.join(home, ".claude", "local", "node_modules", ".bin", "claude"),
        # Common global install locations
        "/usr/local/bin/claude",
        "/opt/homebrew/bin/claude",  # Homebrew on Apple Silicon
    ]

    for candidate in candidates:
        try:
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        except Exception:
            # Best-effort checks only; ignore filesystem errors
            pass

    return None
