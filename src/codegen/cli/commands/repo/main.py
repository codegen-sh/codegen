"""Repository management command for managing repository configuration."""

import typer
from rich.console import Console
from rich.table import Table

from codegen.cli.utils.repo import (
    get_current_repo_id, 
    get_repo_env_status, 
    set_repo_env_variable, 
    update_env_file_with_repo,
    clear_repo_env_variables,
    ensure_repositories_cached
)
from codegen.cli.auth.token_manager import get_current_token

console = Console()


def repo(
    set_default: int | None = typer.Option(None, "--set-default", "-s", help="Set default repository ID"),
    clear: bool = typer.Option(False, "--clear", "-c", help="Clear repository configuration"),
    list_config: bool = typer.Option(False, "--list", "-l", help="List current repository configuration"),
    list_repos: bool = typer.Option(False, "--list-repos", "-lr", help="List available repositories"),
):
    """Manage repository configuration and environment variables."""
    
    # Handle list repositories mode
    if list_repos:
        _list_repositories()
        return
    
    # Handle list config mode
    if list_config:
        _list_repo_config()
        return

    # Handle clear mode
    if clear:
        _clear_repo_config()
        return

    # Handle set default mode
    if set_default is not None:
        _set_default_repository(set_default)
        return

    # No flags provided, launch TUI
    _run_repo_selector_tui()


def _list_repo_config() -> None:
    """List current repository configuration."""
    table = Table(title="Repository Configuration")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_column("Status", style="yellow")

    # Current repository ID
    current_repo_id = get_current_repo_id()
    if current_repo_id:
        table.add_row("Current Repository ID", str(current_repo_id), "✅ Active")
    else:
        table.add_row("Current Repository ID", "Not configured", "❌ Inactive")
    
    # Environment variables
    env_status = get_repo_env_status()
    for var_name, value in env_status.items():
        status = "✅ Set" if value != "Not set" else "❌ Not set"
        table.add_row(var_name, value, status)

    console.print(table)


def _list_repositories() -> None:
    """List all available repositories."""
    # Check if user is authenticated
    token = get_current_token()
    if not token:
        console.print("[red]Error:[/red] Not authenticated. Please run 'codegen login' first.")
        raise typer.Exit(1)

    # Get cached or fetch repositories
    repositories = ensure_repositories_cached()
    if not repositories:
        console.print("[red]Error:[/red] No repositories found.")
        raise typer.Exit(1)

    table = Table(title="Available Repositories")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Description", style="dim")
    table.add_column("Current", style="yellow")

    current_repo_id = get_current_repo_id()
    
    for repo in repositories:
        repo_id = repo.get("id", "Unknown")
        repo_name = repo.get("name", "Unknown")
        repo_desc = repo.get("description", "")
        is_current = "●" if repo_id == current_repo_id else ""
        
        table.add_row(str(repo_id), repo_name, repo_desc, is_current)

    console.print(table)


def _set_default_repository(repo_id: int) -> None:
    """Set default repository ID."""
    try:
        # Set in environment
        success = set_repo_env_variable(repo_id, "CODEGEN_REPO_ID")
        if not success:
            console.print("[red]Error:[/red] Failed to set repository ID in environment.")
            raise typer.Exit(1)

        # Try to update .env file
        env_updated = update_env_file_with_repo(repo_id)
        
        if env_updated:
            console.print(f"[green]✓[/green] Set default repository ID to: [cyan]{repo_id}[/cyan]")
            console.print("[green]✓[/green] Updated .env file with CODEGEN_REPO_ID")
        else:
            console.print(f"[green]✓[/green] Set repository ID to: [cyan]{repo_id}[/cyan]")
            console.print("[yellow]ℹ[/yellow] Could not update .env file. Add 'export CODEGEN_REPO_ID={repo_id}' to your shell for persistence")

    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to set default repository: {e}")
        raise typer.Exit(1)


def _clear_repo_config() -> None:
    """Clear repository configuration."""
    try:
        clear_repo_env_variables()
        console.print("[green]✓[/green] Cleared repository configuration from environment variables")
        
        # Note: We don't automatically clear the .env file to avoid data loss
        console.print("[yellow]ℹ[/yellow] To permanently remove from .env file, manually delete the CODEGEN_REPO_ID line")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to clear repository configuration: {e}")
        raise typer.Exit(1)


def _run_repo_selector_tui() -> None:
    """Launch the repository selector TUI."""
    try:
        from codegen.cli.commands.repo.tui import RepoSelectorApp
        
        app = RepoSelectorApp()
        app.run()
        
    except ImportError:
        console.print("[red]Error:[/red] Repository selector TUI not available")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to launch repository selector: {e}")
        raise typer.Exit(1)