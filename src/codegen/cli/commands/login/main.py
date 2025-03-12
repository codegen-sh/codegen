import rich_click as click

from codegen.cli.auth.login import login_routine
from codegen.cli.auth.token_manager import get_current_token


@click.command(name="login")
@click.option("--token", required=False, help="API token for authentication")
def login_command(token: str):
    """Store authentication token."""
    # Check if already authenticated
    if get_current_token():
        msg = "Already authenticated. Use 'codegen logout' to clear the token."
        raise click.ClickException(msg)

    login_routine(token)
