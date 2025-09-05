"""Debug command to visualize CLI styling components."""

import time

import typer

from codegen.cli.rich.spinners import create_spinner


def style_debug(text: str = typer.Option("Loading...", help="Text to show in the spinner")):
    """Debug command to visualize CLI styling (spinners, etc)."""
    try:
        with create_spinner(text) as status:
            # Run indefinitely until Ctrl+C
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        # Exit gracefully on Ctrl+C
        pass
