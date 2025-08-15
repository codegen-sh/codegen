"""Profile command for the Codegen CLI."""

import requests
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_org_name, get_current_token, get_current_user_info
from codegen.cli.rich.spinners import create_spinner
from codegen.cli.utils.org import resolve_org_id

console = Console()


def profile():
    """Display information about the currently authenticated user."""
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

    # Build profile information
    profile_info = []
    if user_id != "Unknown":
        profile_info.append(f"[cyan]User ID:[/cyan]  {user_id}")
    if full_name:
        profile_info.append(f"[cyan]Name:[/cyan]     {full_name}")
    if email:
        profile_info.append(f"[cyan]Email:[/cyan]    {email}")
    if github_username:
        profile_info.append(f"[cyan]GitHub:[/cyan]   {github_username}")
    if org_name:
        profile_info.append(f"[cyan]Organization:[/cyan] {org_name}")
    elif org_id:
        profile_info.append(f"[cyan]Organization:[/cyan] Organization {org_id}")
    else:
        profile_info.append("[cyan]Organization:[/cyan] [yellow]Not configured[/yellow] (set CODEGEN_ORG_ID or REPOSITORY_ORG_ID)")
    if role:
        profile_info.append(f"[cyan]Role:[/cyan]     {role}")

    profile_text = "\n".join(profile_info) if profile_info else "No profile information available"

    console.print(
        Panel(
            profile_text,
            title="👤 [bold]User Profile[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
