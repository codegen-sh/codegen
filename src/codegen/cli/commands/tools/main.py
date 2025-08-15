"""Tools command for the Codegen CLI."""

import requests
import typer
from rich.console import Console
from rich.table import Table

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.rich.spinners import create_spinner
from codegen.cli.utils.org import resolve_org_id

console = Console()


def tools(org_id: int | None = typer.Option(None, help="Organization ID (defaults to CODEGEN_ORG_ID/REPOSITORY_ORG_ID or auto-detect)")):
    """List available tools from the Codegen API."""
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

        # Make API request to list tools with spinner
        spinner = create_spinner("Fetching available tools...")
        spinner.start()

        try:
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{resolved_org_id}/tools"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            response_data = response.json()
        finally:
            spinner.stop()

        # Extract tools from the response structure
        if isinstance(response_data, dict) and "tools" in response_data:
            tools_data = response_data["tools"]
            total_count = response_data.get("total_count", len(tools_data))
        else:
            tools_data = response_data
            total_count = len(tools_data) if isinstance(tools_data, list) else 1

        if not tools_data:
            console.print("[yellow]No tools found.[/yellow]")
            return

        # Handle case where response might be a list of strings vs list of objects
        if isinstance(tools_data, list) and len(tools_data) > 0:
            # Check if first item is a string or object
            if isinstance(tools_data[0], str):
                # Simple list of tool names
                console.print(f"[green]Found {len(tools_data)} tools:[/green]")
                for tool_name in tools_data:
                    console.print(f"  • {tool_name}")
                return

        # Create a table to display tools (for structured data)
        table = Table(
            title="Available Tools",
            border_style="blue",
            show_header=True,
            title_justify="center",
        )
        table.add_column("Tool Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Category", style="magenta")

        # Add tools to table
        for tool in tools_data:
            if isinstance(tool, dict):
                tool_name = tool.get("name", "Unknown")
                description = tool.get("description", "No description available")
                category = tool.get("category", "General")

                # Truncate long descriptions
                if len(description) > 80:
                    description = description[:77] + "..."

                table.add_row(tool_name, description, category)
            else:
                # Fallback for non-dict items
                table.add_row(str(tool), "Unknown", "General")

        console.print(table)
        console.print(f"\n[green]Found {total_count} tools available.[/green]")

    except requests.RequestException as e:
        console.print(f"[red]Error fetching tools:[/red] {e}", style="bold red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", style="bold red")
        raise typer.Exit(1)
