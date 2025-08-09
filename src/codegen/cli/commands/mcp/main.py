"""MCP server command for the Codegen CLI."""

from typing import Any

import requests
import typer
from rich.console import Console

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token

console = Console()


def fetch_tools_for_mcp() -> list[dict[str, Any]]:
    """Fetch available tools from the API for MCP server generation."""
    try:
        token = get_current_token()
        if not token:
            console.print("[red]Error:[/red] Not authenticated. Please run 'codegen login' first.")
            raise typer.Exit(1)

        console.print("🔧 Fetching available tools from API...", style="dim")
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/11/tools"
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        response_data = response.json()

        # Extract tools from the response structure
        if isinstance(response_data, dict) and "tools" in response_data:
            tools = response_data["tools"]
            console.print(f"✅ Found {len(tools)} tools", style="green")
            return tools

        return response_data if isinstance(response_data, list) else []

    except requests.RequestException as e:
        console.print(f"[red]Error fetching tools:[/red] {e}", style="bold red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", style="bold red")
        raise typer.Exit(1)


def mcp(
    host: str = typer.Option("localhost", help="Host to bind the MCP server to"),
    port: int | None = typer.Option(None, help="Port to bind the MCP server to (default: stdio transport)"),
    transport: str = typer.Option("stdio", help="Transport protocol to use (stdio or http)"),
):
    """Start the Codegen MCP server."""
    console.print("🚀 Starting Codegen MCP server...", style="bold green")

    if transport == "stdio":
        console.print("📡 Using stdio transport", style="dim")
    else:
        if port is None:
            port = 8000
        console.print(f"📡 Using HTTP transport on {host}:{port}", style="dim")

    # Validate transport
    if transport not in ["stdio", "http"]:
        console.print(
            f"❌ Invalid transport: {transport}. Must be 'stdio' or 'http'",
            style="bold red",
        )
        raise typer.Exit(1)

    # Fetch tools from API before starting server
    tools = fetch_tools_for_mcp()

    # Import here to avoid circular imports and ensure dependencies are available
    from codegen.cli.mcp.server import run_server

    try:
        run_server(transport=transport, host=host, port=port, available_tools=tools)
    except KeyboardInterrupt:
        console.print("\n👋 MCP server stopped", style="yellow")
    except Exception as e:
        console.print(f"❌ Error starting MCP server: {e}", style="bold red")
        raise typer.Exit(1)
