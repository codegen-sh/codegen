"""TUI command for the Codegen CLI."""

from codegen.cli.tui.app import run_tui


def tui():
    """Launch the Codegen TUI interface."""
    run_tui()


if __name__ == "__main__":
    tui()
