import rich
import typer

from codegen.cli.auth.token_manager import TokenManager

# Create a Typer app for the logout command
logout_command = typer.Typer(help="Clear stored authentication token.")

@logout_command.command()
def logout():
    """Clear stored authentication token."""
    token_manager = TokenManager()
    token_manager.clear_token()
    rich.print("Successfully logged out")
