import typer

from codegen.cli.auth.login import login_routine
from codegen.cli.auth.token_manager import get_current_token


def login(token: str | None = typer.Option(None, help="API token for authentication")):
    """Store authentication token."""
    # Check if already authenticated
    if get_current_token():
        pass  # Just proceed silently with re-authentication

    login_routine(token)
