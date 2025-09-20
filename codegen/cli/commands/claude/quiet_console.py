"""Silent console utilities for Claude CLI.

This module provides a shared Rich console instance that is silent by default
to avoid interfering with Claude's terminal UI.
"""

from __future__ import annotations

import io
import os
from rich.console import Console


def _create_console() -> Console:
    """Create a console instance.

    If CODEGEN_CLAUDE_VERBOSE is set to a truthy value, return a normal
    Console for debugging; otherwise, return a Console that writes to an
    in-memory buffer so nothing is emitted to stdout/stderr.
    """
    verbose = os.environ.get("CODEGEN_CLAUDE_VERBOSE", "").strip().lower()
    is_verbose = verbose in ("1", "true", "yes", "on")

    if is_verbose:
        return Console()

    # Silent console: sink all output
    return Console(file=io.StringIO())


# Shared console used across Claude CLI modules
console = _create_console()

