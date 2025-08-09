"""Integrations command for the Codegen CLI."""

import requests
import typer
from rich.console import Console
from rich.table import Table

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token

console = Console()


def integrations():
    """List organization integrations from the Codegen API."""
    console.print("🔌 Fetching organization integrations...", style="bold blue")

    # Get the current token
    token = get_current_token()
    if not token:
        console.print("[red]Error:[/red] Not authenticated. Please run 'codegen login' first.")
        raise typer.Exit(1)

    try:
        # Make API request to list integrations
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/11/integrations"
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        response_data = response.json()

        # Extract integrations from the response structure
        integrations_data = response_data.get("integrations", [])
        organization_name = response_data.get("organization_name", "Unknown")
        total_active = response_data.get("total_active_integrations", 0)

        if not integrations_data:
            console.print("[yellow]No integrations found.[/yellow]")
            return

        # Create a table to display integrations
        table = Table(
            title=f"Integrations for {organization_name}",
            border_style="blue",
            show_header=True,
            title_justify="center",
        )
        table.add_column("Integration", style="cyan", no_wrap=True)
        table.add_column("Status", style="white", justify="center")
        table.add_column("Type", style="magenta")
        table.add_column("Details", style="dim")

        # Add integrations to table
        for integration in integrations_data:
            integration_type = integration.get("integration_type", "Unknown")
            active = integration.get("active", False)
            token_id = integration.get("token_id")
            installation_id = integration.get("installation_id")
            metadata = integration.get("metadata", {})

            # Status with emoji
            status = "✅ Active" if active else "❌ Inactive"

            # Determine integration category
            if integration_type.endswith("_user"):
                category = "User Token"
            elif integration_type.endswith("_app"):
                category = "App Install"
            elif integration_type in ["github", "slack_app", "linear_app"]:
                category = "App Install"
            else:
                category = "Token-based"

            # Build details string
            details = []
            if token_id:
                details.append(f"Token ID: {token_id}")
            if installation_id:
                details.append(f"Install ID: {installation_id}")
            if metadata and isinstance(metadata, dict):
                for key, value in metadata.items():
                    if key == "webhook_secret":
                        details.append(f"{key}: ***secret***")
                    else:
                        details.append(f"{key}: {value}")

            details_str = ", ".join(details) if details else "No details"
            if len(details_str) > 50:
                details_str = details_str[:47] + "..."

            table.add_row(integration_type.replace("_", " ").title(), status, category, details_str)

        console.print(table)
        console.print(f"\n[green]Total: {len(integrations_data)} integrations ({total_active} active)[/green]")

    except requests.RequestException as e:
        console.print(f"[red]Error fetching integrations:[/red] {e}", style="bold red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", style="bold red")
        raise typer.Exit(1)
