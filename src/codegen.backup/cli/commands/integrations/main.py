"""Integrations command for the Codegen CLI."""

import webbrowser

import requests
import typer
from rich.console import Console
from rich.table import Table

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.rich.spinners import create_spinner
from codegen.cli.utils.org import resolve_org_id
from codegen.cli.utils.url import generate_webapp_url

console = Console()

# Create the integrations app
integrations_app = typer.Typer(help="Manage Codegen integrations")


@integrations_app.command("list")
def list_integrations(org_id: int | None = typer.Option(None, help="Organization ID (defaults to CODEGEN_ORG_ID/REPOSITORY_ORG_ID or auto-detect)")):
    """List organization integrations from the Codegen API."""
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

        # Make API request to list integrations with spinner
        spinner = create_spinner("Fetching organization integrations...")
        spinner.start()

        try:
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{resolved_org_id}/integrations"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            response_data = response.json()
        finally:
            spinner.stop()

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


@integrations_app.command("add")
def add_integration():
    """Open the Codegen integrations page in your browser to add new integrations."""
    console.print("🌐 Opening Codegen integrations page...", style="bold blue")

    # Generate the web URL using the environment-aware utility
    web_url = generate_webapp_url("integrations")

    try:
        webbrowser.open(web_url)
        console.print(f"✅ Opened [link]{web_url}[/link] in your browser", style="green")
        console.print("💡 You can add new integrations from the web interface", style="dim")
    except Exception as e:
        console.print(f"❌ Failed to open browser: {e}", style="red")
        console.print(f"🔗 Please manually visit: {web_url}", style="yellow")


# Default callback for the integrations app
@integrations_app.callback(invoke_without_command=True)
def integrations_callback(ctx: typer.Context):
    """Manage Codegen integrations."""
    if ctx.invoked_subcommand is None:
        # If no subcommand is provided, run list by default
        list_integrations(org_id=None)
