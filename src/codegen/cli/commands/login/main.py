import rich
import typer

from codegen.cli.auth.login import login_routine
from codegen.cli.auth.token_manager import get_current_token


def login(token: str | None = typer.Option(None, help="API token for authentication")):
    """Log in and replace any existing token."""
    existing = get_current_token()
    if existing:
        rich.print("[yellow]Warning:[/yellow] You are currently authenticated. This will replace the existing token.")
    login_routine(token)
