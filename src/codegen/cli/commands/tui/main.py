# C:\Programs\codegen\src\codegen\cli\commands\tui\main.py
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Import compatibility module first
from codegen.compat import *

# Try to import the original TUI, fallback to Windows version
try:
    from codegen.cli.tui.app import run_tui
except (ImportError, ModuleNotFoundError):
    # Try to import the Windows TUI
    try:
        from codegen.cli.tui.windows_app import run_tui
    except (ImportError, ModuleNotFoundError):
        # If both fail, create a simple fallback
        def run_tui():
            print(
                "TUI is not available on this platform. Use 'codegen --help' for available commands."
            )


def tui():
    """Run the TUI interface."""
    run_tui()


def tui_command():
    """Run the TUI interface."""
    run_tui()
