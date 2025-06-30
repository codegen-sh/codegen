"""MCP server command for the Codegen CLI."""

import typer
from rich.console import Console

console = Console()


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
        console.print(f"📡 Using HTTP transport on {host}:{port}", style="dim")

    # Validate transport
    if transport not in ["stdio", "http"]:
        console.print(f"❌ Invalid transport: {transport}. Must be 'stdio' or 'http'", style="bold red")
        raise typer.Exit(1)

    # Import here to avoid circular imports and ensure dependencies are available
    from codegen.cli.mcp.server import run_server

    try:
        run_server(transport=transport, host=host, port=port)
    except KeyboardInterrupt:
        console.print("\n👋 MCP server stopped", style="yellow")
    except Exception as e:
        console.print(f"❌ Error starting MCP server: {e}", style="bold red")
        raise typer.Exit(1)
