"""MCP server command for the Codegen CLI."""

import rich_click as click
from rich.console import Console

console = Console()


@click.command(name="mcp")
@click.option(
    "--host",
    default="localhost",
    help="Host to bind the MCP server to (default: localhost)",
)
@click.option(
    "--port",
    default=None,
    type=int,
    help="Port to bind the MCP server to (default: stdio transport)",
)
@click.option(
    "--transport",
    default="stdio",
    type=click.Choice(["stdio", "http"]),
    help="Transport protocol to use (default: stdio)",
)
def mcp_command(host: str, port: int | None, transport: str):
    """Start the Codegen MCP server.
    
    The MCP server exposes Codegen API endpoints as MCP tools,
    allowing MCP clients to interact with the Codegen platform.
    """
    console.print("🚀 Starting Codegen MCP server...", style="bold green")
    
    if transport == "stdio":
        console.print("📡 Using stdio transport", style="dim")
    else:
        console.print(f"📡 Using HTTP transport on {host}:{port}", style="dim")
    
    # Import here to avoid circular imports and ensure dependencies are available
    from codegen.cli.mcp.server import run_server
    
    try:
        run_server(transport=transport, host=host, port=port)
    except KeyboardInterrupt:
        console.print("\n👋 MCP server stopped", style="yellow")
    except Exception as e:
        console.print(f"❌ Error starting MCP server: {e}", style="bold red")
        raise click.ClickException(str(e))
