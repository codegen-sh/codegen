"""Debug command to visualize CLI styling components."""

import time

import typer

from codegen.cli.rich.spinners import create_spinner

# Create a Typer app for the style-debug command
style_debug_command = typer.Typer(help="Debug command to visualize CLI styling (spinners, etc).")

@style_debug_command.command()
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
