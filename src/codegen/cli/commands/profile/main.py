"""Profile command for the Codegen CLI."""

import requests
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
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

    try:
        # Make API request to get current user info with spinner
        spinner = create_spinner("Fetching user profile and organization info...")
        spinner.start()

        try:
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{API_ENDPOINT.rstrip('/')}/v1/users/me"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            user_data = response.json()
        finally:
            spinner.stop()

        # Extract user information
        user_id = user_data.get("id", "Unknown")
        full_name = user_data.get("full_name", "")
        email = user_data.get("email", "")
        github_username = user_data.get("github_username", "")
        github_user_id = user_data.get("github_user_id", "")
        avatar_url = user_data.get("avatar_url", "")
        role = user_data.get("role", "")

        # Get organization information
        org_id = resolve_org_id()
        org_name = None

        if org_id:
            try:
                # Fetch organizations to get the name
                orgs_url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations"
                orgs_response = requests.get(orgs_url, headers=headers)
                orgs_response.raise_for_status()
                orgs_data = orgs_response.json()

                # Find the matching organization
                organizations = orgs_data.get("items", [])
                for org in organizations:
                    if org.get("id") == org_id:
                        org_name = org.get("name", f"Organization {org_id}")
                        break

                if not org_name:
                    org_name = f"Organization {org_id}"  # Fallback if not found

            except Exception:
                # If we can't fetch org name, fall back to showing ID
                org_name = f"Organization {org_id}"

        # Create profile display
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

    except requests.RequestException as e:
        console.print(f"[red]Error fetching profile:[/red] {e}", style="bold red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", style="bold red")
        raise typer.Exit(1)
