"""Profile command for the Codegen CLI."""

import requests
import typer
from rich.console import Console

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import (
    get_cached_organizations,
    get_current_org_name,
    get_current_token,
    get_current_user_info,
    set_default_organization,
)
from codegen.cli.rich.spinners import create_spinner
from codegen.cli.utils.org import resolve_org_id
from codegen.cli.utils.simple_selector import simple_org_selector

console = Console()

# Create the profile Typer app
profile_app = typer.Typer(name="profile", help="Manage user profile and organization settings.")


def _get_profile_data() -> dict:
    """Get profile data (shared between commands)."""
    # Get the current token
    token = get_current_token()
    if not token:
        console.print("[red]Error:[/red] Not authenticated. Please run 'codegen login' first.")
        raise typer.Exit(1)

    # Try to get stored user and org info first (fast, no API calls)
    user_info = get_current_user_info()
    org_name = get_current_org_name()
    org_id = resolve_org_id()  # This now uses stored data first

    # If we have stored data, use it directly
    if user_info and user_info.get("id"):
        user_id = user_info.get("id", "Unknown")
        full_name = user_info.get("full_name", "")
        email = user_info.get("email", "")
        github_username = user_info.get("github_username", "")
        role = "Member"  # Default role for stored data
    else:
        # Fall back to API call if no stored data
        spinner = create_spinner("Fetching user profile info...")
        spinner.start()
        try:
            headers = {"Authorization": f"Bearer {token}"}
            user_response = requests.get(f"{API_ENDPOINT.rstrip('/')}/v1/users/me", headers=headers)
            user_response.raise_for_status()
            user_data = user_response.json()

            user_id = user_data.get("id", "Unknown")
            full_name = user_data.get("full_name", "")
            email = user_data.get("email", "")
            github_username = user_data.get("github_username", "")
            role = user_data.get("role", "Member")
        except requests.RequestException as e:
            spinner.stop()
            console.print(f"[red]Error:[/red] Failed to fetch profile information: {e}")
            raise typer.Exit(1)
        finally:
            spinner.stop()

    # If no stored org name but we have an org_id, try to fetch it
    if org_id and not org_name:
        spinner = create_spinner("Fetching organization info...")
        spinner.start()
        try:
            headers = {"Authorization": f"Bearer {token}"}
            orgs_response = requests.get(f"{API_ENDPOINT.rstrip('/')}/v1/organizations", headers=headers)
            orgs_response.raise_for_status()
            orgs_data = orgs_response.json()

            # Find the organization by ID
            orgs = orgs_data.get("items", [])
            for org in orgs:
                if org.get("id") == org_id:
                    org_name = org.get("name")
                    break
        except requests.RequestException:
            # Ignore errors for org name lookup - not critical
            pass
        finally:
            spinner.stop()

    return {
        "user_id": user_id,
        "full_name": full_name,
        "email": email,
        "github_username": github_username,
        "role": role,
        "org_name": org_name,
        "org_id": org_id,
    }


@profile_app.callback(invoke_without_command=True)
def profile_main(ctx: typer.Context):
    """Display organization selection dropdown or profile info."""
    if ctx.invoked_subcommand is None:
        # No subcommand - show organization selector
        _show_org_selector()


@profile_app.command("list")
def profile_list():
    """List all available organizations."""
    data = _get_profile_data()
    cached_orgs = get_cached_organizations()

    if not cached_orgs:
        console.print("[yellow]No organizations found. Please run 'codegen login' first.[/yellow]")
        return

    # Build profile information
    if data["user_id"] != "Unknown":
        console.print(f"[dim]User ID:[/dim]  [blue]{data['user_id']}[/blue]")
    if data["full_name"]:
        console.print(f"[dim]Name:[/dim]     [blue]{data['full_name']}[/blue]")
    if data["email"]:
        console.print(f"[dim]Email:[/dim]    [blue]{data['email']}[/blue]")
    if data["github_username"]:
        console.print(f"[dim]GitHub:[/dim]   [blue]{data['github_username']}[/blue]")
    if data["role"]:
        console.print(f"[dim]Role:[/dim]     [blue]{data['role']}[/blue]")

    # Current organization
    if data["org_name"]:
        console.print(f"[dim]Current Org:[/dim] [blue]{data['org_name']} ({data['org_id']})[/blue]")
    elif data["org_id"]:
        console.print(f"[dim]Current Org:[/dim] [blue]Organization {data['org_id']}[/blue]")
    else:
        console.print("[dim]Current Org:[/dim] [yellow]Not configured[/yellow]")

    console.print()
    console.print("[dim]Available Organizations:[/dim]")

    for org in cached_orgs:
        org_id = org.get("id")
        org_name = org.get("name")
        is_current = " [green](current)[/green]" if org_id == data["org_id"] else ""
        console.print(f"  • [blue]{org_name}[/blue] [dim](ID: {org_id})[/dim]{is_current}")


def _show_org_selector():
    """Show the organization selector."""
    cached_orgs = get_cached_organizations()

    if not cached_orgs:
        console.print("[red]Error:[/red] No organizations found. Please run 'codegen login' first.")
        raise typer.Exit(1)

    if len(cached_orgs) == 1:
        # Only one org, set it as default
        org = cached_orgs[0]
        org_id = org.get("id")
        org_name = org.get("name")
        try:
            set_default_organization(org_id, org_name)
            console.print(f"[green]✓[/green] Set default organization: {org_name} (ID: {org_id})")
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to set default organization: {e}")
            raise typer.Exit(1)
        return

    # Multiple orgs - show simple selector
    current_org_id = resolve_org_id()
    console.print("[blue]Select your default organization:[/blue]")

    selected_org = simple_org_selector(organizations=cached_orgs, current_org_id=current_org_id, title="👤 Select Default Organization")

    if selected_org:
        org_id = selected_org.get("id")
        org_name = selected_org.get("name")
        try:
            set_default_organization(org_id, org_name)
            console.print(f"\n[green]✓ Set default organization:[/green] {org_name} (ID: {org_id})")
            console.print("[green]✓ Updated ~/.codegen/auth.json[/green]")
        except Exception as e:
            console.print(f"\n[red]Error:[/red] Failed to set default organization: {e}")
            raise typer.Exit(1)
    else:
        console.print("\n[yellow]No organization selected.[/yellow]")


# For backward compatibility, export the profile function
def profile():
    """Display organization selector (legacy function)."""
    _show_org_selector()
