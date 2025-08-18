import webbrowser

import rich
import typer

from codegen.cli.api.webapp_routes import USER_SECRETS_ROUTE
from codegen.cli.auth.token_manager import TokenManager, get_cached_organizations, set_default_organization
from codegen.cli.env.global_env import global_env
from codegen.cli.errors import AuthError
from codegen.cli.utils.simple_selector import simple_org_selector


def login_routine(token: str | None = None) -> str:
    """Guide user through login flow and return authenticated session.

    Args:
        token: Codegen user access token associated with github account

    Returns:
        str: The authenticated token

    Raises:
        typer.Exit: If login fails

    """
    # Try environment variable first
    token = token or global_env.CODEGEN_USER_ACCESS_TOKEN

    # If no token provided, guide user through browser flow
    if not token:
        webbrowser.open_new(USER_SECRETS_ROUTE)
        token = typer.prompt(f"Enter your token from {USER_SECRETS_ROUTE}", hide_input=False)

    if not token:
        rich.print("[red]Error:[/red] Token must be provided via CODEGEN_USER_ACCESS_TOKEN environment variable or manual input")
        raise typer.Exit(1)

    # Validate and store token
    try:
        token_manager = TokenManager()
        token_manager.authenticate_token(token)
        rich.print(f"[green]✓ Stored token and profile to:[/green] {token_manager.token_file}")

        # Show organization selector if multiple organizations available
        organizations = get_cached_organizations()
        if organizations and len(organizations) > 1:
            rich.print("\n[blue]Multiple organizations found. Please select your default:[/blue]")
            selected_org = simple_org_selector(organizations, title="🏢 Select Default Organization")

            if selected_org:
                org_id = selected_org.get("id")
                org_name = selected_org.get("name")
                try:
                    set_default_organization(org_id, org_name)
                    rich.print(f"[green]✓ Set default organization:[/green] {org_name}")
                except Exception as e:
                    rich.print(f"[yellow]Warning: Could not set default organization: {e}[/yellow]")
                    rich.print("[yellow]You can set it later with 'codegen profile'[/yellow]")
            else:
                rich.print("[yellow]No organization selected. You can set it later with 'codegen profile'[/yellow]")
        elif organizations and len(organizations) == 1:
            # Single organization - set it automatically
            org = organizations[0]
            org_id = org.get("id")
            org_name = org.get("name")
            try:
                set_default_organization(org_id, org_name)
                rich.print(f"[green]✓ Set default organization:[/green] {org_name}")
            except Exception as e:
                rich.print(f"[yellow]Warning: Could not set default organization: {e}[/yellow]")

        return token
    except AuthError as e:
        rich.print(f"[red]Error:[/red] {e!s}")
        raise typer.Exit(1)
