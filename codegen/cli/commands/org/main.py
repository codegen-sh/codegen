"""Organization management command for switching between organizations."""

import os

import typer
from rich.console import Console

from codegen.cli.auth.token_manager import get_cached_organizations, get_current_token
from codegen.cli.commands.org.tui import OrgSelectorApp

console = Console()


def org(
    set_default: int | None = typer.Option(None, "--set-default", "-s", help="Set default organization ID"),
    list_orgs: bool = typer.Option(False, "--list", "-l", help="List available organizations"),
):
    """Manage and switch between organizations."""
    # Check if user is authenticated
    token = get_current_token()
    if not token:
        console.print("[red]Error:[/red] Not authenticated. Please run 'codegen login' first.")
        raise typer.Exit(1)

    # Get cached organizations
    cached_orgs = get_cached_organizations()
    if not cached_orgs:
        console.print("[red]Error:[/red] No organizations found in cache. Please run 'codegen login' to refresh.")
        raise typer.Exit(1)

    # Handle list mode
    if list_orgs:
        _list_organizations(cached_orgs)
        return

    # Handle set default mode
    if set_default is not None:
        _set_default_organization(set_default, cached_orgs)
        return

    # No flags provided, launch TUI
    _run_org_selector_tui()


def _list_organizations(cached_orgs: list[dict]) -> None:
    """List all available organizations."""
    from rich.table import Table

    table = Table(title="Available Organizations")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")

    for org in cached_orgs:
        table.add_row(str(org["id"]), org["name"])

    console.print(table)


def _set_default_organization(org_id: int, cached_orgs: list[dict]) -> None:
    """Set the default organization via environment variable."""
    # Check if org ID exists in cache
    org_found = None
    for org in cached_orgs:
        if org["id"] == org_id:
            org_found = org
            break

    if not org_found:
        available_orgs = ", ".join([f"{org['name']} ({org['id']})" for org in cached_orgs])
        console.print(f"[red]Error:[/red] Organization ID {org_id} not found in your accessible organizations.")
        console.print(f"[yellow]Available organizations:[/yellow] {available_orgs}")
        raise typer.Exit(1)

    # Set the environment variable
    os.environ["CODEGEN_ORG_ID"] = str(org_id)
    
    # Try to update .env file if it exists
    env_file_path = ".env"
    if os.path.exists(env_file_path):
        _update_env_file(env_file_path, "CODEGEN_ORG_ID", str(org_id))
        console.print(f"[green]✓ Updated {env_file_path} with CODEGEN_ORG_ID={org_id}[/green]")
    else:
        console.print(f"[yellow]Info:[/yellow] No .env file found. Set environment variable manually:")
        console.print(f"[cyan]export CODEGEN_ORG_ID={org_id}[/cyan]")

    console.print(f"[green]✓ Default organization set to:[/green] {org_found['name']} ({org_id})")


def _update_env_file(file_path: str, key: str, value: str) -> None:
    """Update or add an environment variable in the .env file."""
    lines = []
    key_found = False

    # Read existing lines
    try:
        with open(file_path) as f:
            lines = f.readlines()
    except FileNotFoundError:
        pass

    # Ensure all lines end with newline
    for i, line in enumerate(lines):
        if not line.endswith('\n'):
            lines[i] = line + '\n'

    # Update existing key or note if we need to add it
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            key_found = True
            break

    # Add new key if not found
    if not key_found:
        lines.append(f"{key}={value}\n")

    # Write back to file
    with open(file_path, "w") as f:
        f.writelines(lines)


def _run_org_selector_tui() -> None:
    """Launch the organization selector TUI."""
    try:
        app = OrgSelectorApp()
        app.run()
    except Exception as e:
        console.print(f"[red]Error launching TUI:[/red] {e}")
        raise typer.Exit(1)