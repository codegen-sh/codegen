from typing import Optional
import typer
import rich

from codegen.cli.auth.login import login_routine
from codegen.cli.auth.token_manager import get_current_token

# Create a Typer app for the login command
login_command = typer.Typer(help="Store authentication token.")

@login_command.command()
def login(token: Optional[str] = typer.Option(None, help="API token for authentication")):
    """Store authentication token."""
    # Check if already authenticated
    if get_current_token():
        rich.print("[yellow]Warning:[/yellow] Already authenticated. Use 'codegen logout' to clear the token.")
        raise typer.Exit(1)

    login_routine(token)
