import webbrowser

import rich
import typer

from codegen.cli.api.webapp_routes import USER_SECRETS_ROUTE
from codegen.cli.auth.token_manager import TokenManager
from codegen.cli.errors import AuthError


def login_routine(token: str | None = None) -> str:
    """Guide user through login flow and return authenticated session.

    Args:
        token: Codegen user access token associated with github account

    Returns:
        str: The authenticated token

    Raises:
        typer.Exit: If login fails

    """
    # Always open the token page to encourage regenerating/retrieving a fresh token
    rich.print(f"Opening {USER_SECRETS_ROUTE} to get your authentication token...")
    webbrowser.open_new(USER_SECRETS_ROUTE)

    # If no token provided programmatically, prompt the user
    if token is None:
        token = typer.prompt(
            "Please enter your authentication token from the browser",
            hide_input=False,
        )

    if not token:
        rich.print("[red]Error:[/red] Token must be provided via CODEGEN_USER_ACCESS_TOKEN environment variable or manual input")
        raise typer.Exit(1)

    # Validate and store token
    try:
        token_manager = TokenManager()
        token_manager.authenticate_token(token)
        rich.print(f"[green]✓ Stored token to:[/green] {token_manager.token_file}")
        rich.print("[cyan]📊 Hey![/cyan] We collect anonymous usage data to improve your experience 🔒")
        rich.print("To opt out, set [green]telemetry_enabled = false[/green] in [cyan]~/.config/codegen-sh/analytics.json[/cyan] ✨")
        return token
    except AuthError as e:
        rich.print(f"[red]Error:[/red] {e!s}")
        raise typer.Exit(1)
