"""Agents command for the Codegen CLI."""

import requests
import typer
from rich.console import Console
from rich.table import Table

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.rich.spinners import create_spinner
from codegen.cli.utils.org import resolve_org_id

console = Console()

# Create the agents app
agents_app = typer.Typer(help="Manage Codegen agents")


@agents_app.command("list")
def list_agents(org_id: int | None = typer.Option(None, help="Organization ID (defaults to CODEGEN_ORG_ID/REPOSITORY_ORG_ID or auto-detect)")):
    """List agent runs from the Codegen API."""
    # Get the current token
    token = get_current_token()
    if not token:
        console.print("[red]Error:[/red] Not authenticated. Please run 'codegen login' first.")
        raise typer.Exit(1)

    try:
        # Resolve org id (now fast, uses stored data)
        resolved_org_id = resolve_org_id(org_id)
        if resolved_org_id is None:
            console.print("[red]Error:[/red] Organization ID not provided. Pass --org-id, set CODEGEN_ORG_ID, or REPOSITORY_ORG_ID.")
            raise typer.Exit(1)

        # Start spinner for API calls only
        spinner = create_spinner("Fetching your recent API agent runs...")
        spinner.start()

        try:
            headers = {"Authorization": f"Bearer {token}"}

            # Filter to only API source type and current user's agent runs
            params = {
                "source_type": "API",
                # We'll get the user_id from the /users/me endpoint
            }

            # First get the current user ID
            user_response = requests.get(f"{API_ENDPOINT.rstrip('/')}/v1/users/me", headers=headers)
            user_response.raise_for_status()
            user_data = user_response.json()
            user_id = user_data.get("id")

            if user_id:
                params["user_id"] = user_id

            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{resolved_org_id}/agent/runs"
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            response_data = response.json()
        finally:
            spinner.stop()

        # Extract agent runs from the response structure
        agent_runs = response_data.get("items", [])
        total = response_data.get("total", 0)
        page = response_data.get("page", 1)
        page_size = response_data.get("page_size", 10)

        if not agent_runs:
            console.print("[yellow]No API agent runs found for your user.[/yellow]")
            return

        # Create a table to display agent runs
        table = Table(
            title=f"Your Recent API Agent Runs (Page {page}, Total: {total})",
            border_style="blue",
            show_header=True,
            title_justify="center",
        )
        table.add_column("Created", style="dim")
        table.add_column("Status", style="white", justify="center")
        table.add_column("Summary", style="green")
        table.add_column("Link", style="blue")

        # Add agent runs to table
        for agent_run in agent_runs:
            run_id = str(agent_run.get("id", "Unknown"))
            status = agent_run.get("status", "Unknown")
            source_type = agent_run.get("source_type", "Unknown")
            created_at = agent_run.get("created_at", "Unknown")

            # Use summary from API response (backend now handles extraction)
            summary = agent_run.get("summary", "") or "No summary"

            # Status with colored circles
            if status == "COMPLETE":
                status_display = "[green]●[/green] Complete"
            elif status == "ACTIVE":
                status_display = "[dim]●[/dim] Active"
            elif status == "RUNNING":
                status_display = "[dim]●[/dim] Running"
            elif status == "CANCELLED":
                status_display = "[yellow]●[/yellow] Cancelled"
            elif status == "ERROR":
                status_display = "[red]●[/red] Error"
            elif status == "FAILED":
                status_display = "[red]●[/red] Failed"
            elif status == "STOPPED":
                status_display = "[yellow]●[/yellow] Stopped"
            elif status == "PENDING":
                status_display = "[dim]●[/dim] Pending"
            else:
                status_display = "[dim]●[/dim] " + status

            # Format created date (just show date and time, not full timestamp)
            if created_at and created_at != "Unknown":
                try:
                    # Parse and format the timestamp to be more readable
                    from datetime import datetime

                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    created_display = dt.strftime("%m/%d %H:%M")
                except (ValueError, TypeError):
                    created_display = created_at[:16] if len(created_at) > 16 else created_at
            else:
                created_display = created_at

            # Truncate summary if too long
            summary_display = summary[:50] + "..." if summary and len(summary) > 50 else summary or "No summary"

            # Create web link for the agent run
            web_url = agent_run.get("web_url")
            if not web_url:
                # Construct URL if not provided
                web_url = f"https://codegen.com/traces/{run_id}"
            link_display = web_url

            table.add_row(created_display, status_display, summary_display, link_display)

        console.print(table)
        console.print(f"\n[green]Showing {len(agent_runs)} of {total} API agent runs[/green]")

    except requests.RequestException as e:
        console.print(f"[red]Error fetching agent runs:[/red] {e}", style="bold red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", style="bold red")
        raise typer.Exit(1)


# Default callback for the agents app
@agents_app.callback(invoke_without_command=True)
def agents_callback(ctx: typer.Context):
    """Manage Codegen agents."""
    if ctx.invoked_subcommand is None:
        # If no subcommand is provided, run list by default
        list_agents(org_id=None)
