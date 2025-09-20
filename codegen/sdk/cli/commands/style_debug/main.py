"""Debug command to visualize CLI styling components."""

import time

import rich_click as click

from codegen.sdk.cli.rich.spinners import create_spinner


@click.command(name="style-debug")
@click.option("--text", default="Loading...", help="Text to show in the spinner")
def style_debug_command(text: str):
    """Debug command to visualize CLI styling (spinners, etc)."""
    try:
        with create_spinner(text) as status:
            # Run indefinitely until Ctrl+C
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        # Exit gracefully on Ctrl+C
        pass
