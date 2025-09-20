# TODO: refactor this file out
import functools

import rich
import rich_click as click
from rich.panel import Panel


class AuthError(Exception):
    """Error raised if authed user cannot be established."""

    pass


class InvalidTokenError(AuthError):
    """Error raised if the token is invalid."""

    pass


class NoTokenError(AuthError):
    """Error raised if no token is provided."""

    pass


class CodegenError(Exception):
    """Base class for Codegen-specific errors."""

    pass


class ServerError(CodegenError):
    """Error raised when the server encounters an error."""

    pass


def format_error_message(error):
    """Format error message based on error type."""
    if isinstance(error, AuthError):
        return "[red]Authentication Error:[/red] Please run 'codegen login' first."
    elif isinstance(error, ServerError):
        return "[red]Server Error:[/red] The server encountered an error. Please try again later."
    else:
        return f"[red]Error:[/red] {error!s}"


def handle_auth_error(f):
    """Decorator to handle authentication errors gracefully."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AuthError:
            rich.print(Panel("[red]Authentication Error:[/red] Please run 'codegen login' first.", title="Graph-sitter Error", border_style="red"))
            raise click.Abort()

    return wrapper
