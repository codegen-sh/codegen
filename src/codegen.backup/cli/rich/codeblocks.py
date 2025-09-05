def format_command(command: str) -> str:
    """Format a command in a consistent style.

    Args:
        command: The command to format

    Returns:
        The formatted command with consistent styling and spacing

    """
    return f"\n\t[cyan]{command}[/cyan]\n"


def format_codeblock(code: str) -> str:
    """Format a code block in a consistent style.

    Args:
        code: The code to format

    Returns:
        The formatted code with consistent styling

    """
    return f"\n\t[cyan]{code}[/cyan]\n"


def format_code(code: str) -> str:
    """Just blue for a span"""
    return f"[cyan]{code}[/cyan]"


def format_path(path: str) -> str:
    """Format a path in a consistent style.

    Args:
        path: The path to format

    Returns:
        The formatted path with consistent styling

    """
    return f"[cyan]{path}[/cyan]"
