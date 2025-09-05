"""Consistent spinner styles for the CLI."""

from dataclasses import dataclass

from rich.status import Status


@dataclass
class SpinnerConfig:
    """Configuration for a consistent spinner style."""

    text: str
    spinner: str = "dots"
    style: str = "bold"
    spinner_style: str = "blue"


def create_spinner(text: str) -> Status:
    """Create a spinner with consistent styling.

    Args:
        text: The text to show next to the spinner

    Returns:
        A rich Status object with consistent styling

    """
    config = SpinnerConfig(text)
    return Status(f"[{config.style}]{config.text}", spinner=config.spinner, spinner_style=config.spinner_style)
