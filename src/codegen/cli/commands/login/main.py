from typing import Optional
import typer

from codegen.cli.auth.login import login_routine
from codegen.cli.auth.token_manager import get_current_token

# Create a Typer app for the login command
login_command = typer.Typer(help="Store authentication token.")

@login_command.command()
def login(token: Optional[str] = typer.Option(None, help="API token for authentication")):
    """Store authentication token."""
    # Check if already authenticated
    if get_current_token():
        msg = "Already authenticated. Use 'codegen logout' to clear the token."
        raise typer.Exit(msg)

    login_routine(token)
