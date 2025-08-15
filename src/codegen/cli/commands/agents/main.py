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
        # Resolve org id
        resolved_org_id = resolve_org_id(org_id)
        if resolved_org_id is None:
            console.print("[red]Error:[/red] Organization ID not provided. Pass --org-id, set CODEGEN_ORG_ID, or REPOSITORY_ORG_ID.")
            raise typer.Exit(1)

        # Make API request to list agent runs with spinner
        spinner = create_spinner("Fetching agent runs...")
        spinner.start()

        try:
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{resolved_org_id}/agent/runs"
            response = requests.get(url, headers=headers)
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
            console.print("[yellow]No agent runs found.[/yellow]")
            return

        # Create a table to display agent runs
        table = Table(
            title=f"Agent Runs (Page {page}, Total: {total})",
            border_style="blue",
            show_header=True,
            title_justify="center",
        )
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Status", style="white", justify="center")
        table.add_column("Source", style="magenta")
        table.add_column("Created", style="dim")
        table.add_column("Result", style="green")

        # Add agent runs to table
        for agent_run in agent_runs:
            run_id = str(agent_run.get("id", "Unknown"))
            status = agent_run.get("status", "Unknown")
            source_type = agent_run.get("source_type", "Unknown")
            created_at = agent_run.get("created_at", "Unknown")
            result = agent_run.get("result", "")

            # Status with emoji
            status_display = status
            if status == "COMPLETE":
                status_display = "✅ Complete"
            elif status == "RUNNING":
                status_display = "🏃 Running"
            elif status == "FAILED":
                status_display = "❌ Failed"
            elif status == "STOPPED":
                status_display = "⏹️ Stopped"
            elif status == "PENDING":
                status_display = "⏳ Pending"

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

            # Truncate result if too long
            result_display = result[:50] + "..." if result and len(result) > 50 else result or "No result"

            table.add_row(run_id, status_display, source_type, created_display, result_display)

        console.print(table)
        console.print(f"\n[green]Showing {len(agent_runs)} of {total} agent runs[/green]")

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
